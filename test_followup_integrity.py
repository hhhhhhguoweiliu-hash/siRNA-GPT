"""Targeted real-record regression and explicit synthetic controls; no API."""
import copy, importlib.util, json, tempfile, unittest
from pathlib import Path
from unittest.mock import patch
from core import HOME,TaskError
from conversation import PlannedSession
from evaluation_dialogue import effective_input
from sequence_validation import answer_evidence
from delivery import present_delivery, requirement_audit
from bound_reuse import remember, reuse

OUT=HOME/'research/2026-10-27_followup_execution'
def module(name):
    spec=importlib.util.spec_from_file_location(name,OUT/(name+'.py'));m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

class FollowupIntegrityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.records=json.loads((HOME/'research/2026-10-27_real_dialogue_mini/raw/results_original.json').read_text('utf-8'))
        cls.a13=next(x for x in cls.records if x['answer_id']=='A013')
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(dir=HOME/'_test_runs');self.addCleanup(self.temp.cleanup)
    def test_saved_A013_local_labels_and_mutated_core(self):
        q=self.a13['rounds'][0];inputs=effective_input(q['common_user_input']);raw=q['raw_model_answer']
        result=answer_evidence(raw,inputs['candidates'],q['tool_results'])
        self.assertEqual(result['answer_validation']['status'],'PASS')
        self.assertEqual({c['length'] for c in result['answer_validation']['claims']},{19,57})
        bad=raw.replace('UGUACUACGGAAUAUCUCG','UGUACUACGGAAUAUCUCC')
        self.assertEqual(answer_evidence(bad,inputs['candidates'],q['tool_results'])['answer_validation']['status'],'FAIL')
        state=q['tool_results'];row=state['verify_target']['rows'][0]
        full=inputs['candidates'][0]['guide_21nt_RNA_5to3'];window=inputs['candidates'][0]['target_window_23nt']
        text='guide 19nt核心：'+row['guide_core19_5to3']+'；guide 21nt完整：'+full+'；设计窗口23nt：'+window+'；上下文57nt：'+row['mRNA_context_57nt']
        self.assertEqual(answer_evidence(text,inputs['candidates'],state)['answer_validation']['status'],'PASS')
    def test_two_arms_share_fields_placeholder_is_only_raw_diagnostic(self):
        q=self.a13['rounds'][0];inputs=effective_input(q['common_user_input']);state=q['tool_results']
        shared=present_delivery(inputs,state,['score_candidates'])
        session=PlannedSession(['score_candidates'],cfg={},run_root=self.temp.name,**inputs)
        session.state=copy.deepcopy(state)
        raw=q['raw_model_answer']+'\n来源2025年X月X日'
        result=session.result_for_plan(raw,test_only=True)
        self.assertEqual(shared['model_summary_display'],result['model_summary_display'])
        self.assertNotIn('2025年X月X日',result['model_summary_display'])
        self.assertIn('2025年X月X日',result['model_summary_raw'])
        self.assertIn('0.9915144175887107',result['model_summary_display'])
        self.assertNotIn('match_seed',result['delivery_audit']['completed_steps'])
    def test_missing_requested_evidence_is_not_software_success(self):
        q=self.a13['rounds'][0];inputs=effective_input(q['common_user_input'])
        inputs['task']['evaluation_conditions']['expression_check']=True
        audit=requirement_audit(inputs,q['tool_results'])
        self.assertIn('query_expression',audit['missing_steps'])
        self.assertEqual(audit['status'],'MISSING_REQUIRED_EVIDENCE')
    def test_incremental_reuse_exact_binding_then_changed_sequence_version_parameter(self):
        q=self.a13['rounds'][0];inputs=effective_input(q['common_user_input'])
        first=PlannedSession(['verify_target'],cfg={},run_root=self.temp.name,**inputs)
        for n in first.planned_tools:self.assertNotEqual(first.call(n,{})['status'],'ERROR')
        first.result_for_plan()
        second=PlannedSession(['score_candidates'],cfg={},run_root=self.temp.name,**inputs)
        audit=reuse(second,first)
        self.assertEqual(audit['reused_steps'],['inspect_candidates','verify_target'])
        self.assertNotEqual(second.call('score_candidates',{})['status'],'ERROR');self.assertEqual(second.tool_calls,1)
        for kind in ('sequence','version','parameter','reference','role'):
            changed=copy.deepcopy(inputs);cfg={}
            if kind=='sequence':changed['candidates'][0]['guide_paired_core_19nt_5to3']='A'*19
            elif kind=='version':changed['candidates'][0]['evidence_dataset_id']='SYNTHETIC_TEST_ONLY_v2'
            elif kind=='parameter':cfg['scientific_parameter_version']='SYNTHETIC_TEST_ONLY_v2'
            elif kind=='reference':changed['task']['reference_version']='SYNTHETIC_TEST_ONLY_v2'
            else:changed['candidates'][0]['strand_assignment_basis']='SYNTHETIC_TEST_ONLY_CHANGED_ROLE'
            with self.subTest(kind=kind):
                s=PlannedSession(['score_candidates'],cfg=cfg,run_root=self.temp.name,**changed)
                self.assertEqual(reuse(s,first)['reused_steps'],[])
        first.state['verify_target']['rows'][0]['core_start_1based']=1
        s=PlannedSession(['score_candidates'],cfg={},run_root=self.temp.name,**inputs)
        self.assertEqual(reuse(s,first)['reused_steps'],[])
    def test_metrics_missing_duplicate_unknown_and_applicability_guards(self):
        m=module('recompute_metrics');base=HOME/'research/2026-10-27_ai_simulated_review'
        standards,reviews,tasks,mapping=[m.read(base/n) for n in ('required_slots.csv','slot_reviews.csv','task_reviews.csv','group_map.csv')]
        m.validate(standards,reviews,tasks,mapping)
        for altered in (reviews[:-1],reviews+[reviews[0]]):
            with self.assertRaises(ValueError):m.validate(standards,altered,tasks,mapping)
        self.assertIsNone(m.calculate([{'review_status':'UNJUDGED'}])['precision'])
        with self.assertRaises(ValueError):m.calculate([{'review_status':'TYPO'}])
        changed=copy.deepcopy(reviews);changed[0]['review_status']='NOT_APPLICABLE'
        with self.assertRaises(ValueError):m.validate(standards,changed,tasks,mapping)
    def test_confirmed_subflow_runs_only_requested_checks_and_stops_on_failure(self):
        q=self.a13['rounds'][0];inputs=effective_input(q['common_user_input'])
        s=PlannedSession(['score_candidates'],cfg={'use_confirmed_subflow':True},run_root=self.temp.name,**inputs)
        requests=[]
        from test_conversation import message_response
        def stub(payload):
            requests.append(payload)
            return message_response('SYNTHETIC_TEST_ONLY interpretation')
        result=s.run_agent(stub,test_only=True)
        self.assertEqual(list(s.state),['inspect_candidates','verify_target','score_candidates'])
        self.assertEqual(s.tool_calls,3);self.assertEqual(len(requests),1);self.assertNotIn('tools',requests[0])
        self.assertIn('0.9915144175887107',result['model_summary_display'])
        bad=copy.deepcopy(inputs);bad['candidates'][0]['guide_paired_core_19nt_5to3']='AAA'
        failed=PlannedSession(['score_candidates'],cfg={},run_root=self.temp.name,**bad)
        with self.assertRaises(TaskError):failed.execute_confirmed_subflow()
        self.assertEqual(failed.state,{})
    def test_synthetic_direction_overlap_boundary_and_coordinate_length(self):
        m=module('independent_checks');self.assertTrue(all(x['passed'] for x in m.controls()))
        guide='UUUCUUGUCUUGCUCUAUC'
        self.assertEqual(m.motif(guide),'ACAAGAA')
        self.assertEqual(list(m.positions('TTACAAGAACC',m.motif(guide))),[3])
        self.assertEqual(m.motif('GAUAGAGCAAGACAAGAAATT'),'GCTCTAT')
        self.assertEqual(3628-3610+1,19);self.assertGreater(3610,3609)
        c=module('consistency_audit')
        good=dict(all=10,non=10,target=0,genes=4,mapped=3,unmapped=1,N=3,H=3)
        self.assertTrue(all(x['status']=='PASS' for x in c.relations(good)))
        self.assertEqual(next(x for x in c.relations({**good,'genes':5}) if x['rule']=='GENE_PARTITION')['status'],'FAIL')

if __name__=='__main__':unittest.main(verbosity=2)
