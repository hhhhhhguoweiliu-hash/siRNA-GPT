"""No API: review regressions, saved score provenance and explicit test failures."""
import copy
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from core import HOME, read_tsv
from evaluation_dialogue import run_dialogue
from evaluation_analysis import summarize
from evaluation_protocol import evaluation_settings
from test_conversation import message_response
from test_evaluation_analysis import synthetic_fixture
from test_evaluation_dialogue import test_stub
from review_import import parse_review_tables, SCORE_HEADERS, FACT_HEADERS

PACK=HOME/'research/2026-10-27_evaluation_fixes_v2/package'


def synthetic_tables(plan,person):
    """Matrix fixtures only, never exported as project grading data."""
    score=[(1,SCORE_HEADERS)]
    facts=[(1,FACT_HEADERS)]
    for row,p in enumerate(plan,2):
        score.append((row,[p['answer_id'],p['case_id'],person,1,1,1,1,'完成','否','','SYNTHETIC_ONLY']))
        for fid in p['required_fact_ids']:
            facts.append((len(facts)+1,[p['answer_id'],p['case_id'],person,fid,'SYNTHETIC_FACT','正确','SYNTHETIC_ONLY']))
    return {'评分表':score,'逐事实':facts}


class ReviewCorrections(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.root=Path(self.tmp.name)
        self.cases={c['id']:c for c in json.loads((PACK/'runtime/cases.json').read_text(encoding='utf-8'))['cases']}
        self.resources=json.loads((PACK/'runtime/resources.json').read_text(encoding='utf-8'))
        self.cfg={'model':'TEST_STUB_ONLY','max_tool_calls':18,'max_model_turns':12,'api_key':'TEST_HIDDEN_SECRET'}
    def tearDown(self):self.tmp.cleanup()
    def run_arm(self,cid,group,transport=None,cfg=None,tag=''):
        return run_dialogue(group,self.cases[cid],cfg or self.cfg,self.root/(cid+'_'+group+tag),transport,self.resources)

    def test_constructed_notes_neutral_and_truth_only_in_review_material(self):
        for cid in ('R2','R3','R4'):
            value=self.cases[cid]['rounds'][0]['user_input']['constructed_material']
            self.assertEqual(value,'Artificial development material, not an experimental observation')
        standards=json.loads((PACK/'review_only/criteria.json').read_text(encoding='utf-8'))
        self.assertIn('outside 3609nt',next(c for c in standards if c['case_id']=='R3')['construction_truth_REVIEW_ONLY'])
        result=self.run_arm('R3','agent',test_stub)
        for request in result['test_prepared_requests']:
            data=json.loads(request['payload']['messages'][1]['content'])['input']['task']['shared_user_input']
            self.assertNotIn('wrong',data['user_input']['constructed_material'])

    def test_each_reported_score_points_to_matching_actual_source_not_legacy_pointer(self):
        for cid in ('W1','W2b','W3','R4'):
            result=self.run_arm(cid,'workflow')
            rows=result['tool_results']['score_candidates']['rows']
            for row in rows:
                src=row['score_source'];path=HOME/src['path']
                self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(),src['sha256'])
                original=(next(r for r in read_tsv(path) if r['candidate_id']==row['candidate_id']) if path.suffix=='.tsv' else json.loads(path.read_text(encoding='utf-8')))
                for key in ('candidate_id','guide_core19_5to3','mRNA_context_57nt'):
                    self.assertEqual(original[key],row[key])
                self.assertEqual(float(original['oligoformer_scaled_score']),row['oligoformer_scaled_score'])
                self.assertIn(src['sha256'],result['answer'])
            if cid in ('W1','R4'):
                self.assertNotIn('ef91800094f711e5358c5bab3e5415fd60256056a7479b24b8be674c16e3d392',result['answer'])

    def test_mixed_score_sources_are_distinct_per_candidate(self):
        from core import Session,default_candidates
        from verified_imports import candidates
        s=Session(candidates=[next(r for r in default_candidates() if r['candidate_id']=='VEGFA_SD_3499'),*candidates()],
            task={'gene':'VEGFA','species':'Homo sapiens','state':'Hypoxia','top_n':2},tool_mode='imported',cfg=self.cfg,run_root=self.root/'mixed')
        for tool in ('inspect_candidates','verify_target','score_candidates'):self.assertNotEqual(s.call(tool,{})['status'],'ERROR')
        rows=s.state['score_candidates']['rows']
        self.assertEqual(len({r['score_source']['sha256'] for r in rows}),2)

    def test_transport_failures_all_stages_save_error_result_and_pending_round(self):
        for stage,group in (('ordinary_model','llm'),('planner','agent'),('executor','agent')):
            with self.subTest(stage=stage):
                count=[0]
                def fail(payload):
                    count[0]+=1
                    if stage=='executor' and (count[0]==1 or count[0]==2):return test_stub(payload)
                    raise RuntimeError('SYNTHETIC_FAILURE TEST_HIDDEN_SECRET')
                r=self.run_arm('U1',group,fail,tag=stage)
                self.assertEqual(r['attempted_rounds'],1)
                self.assertEqual(r['pending_rounds'],1)
                self.assertEqual(r['rounds'][1]['status'],'NOT_EXECUTED')
                self.assertEqual(r['rounds'][0]['error_record']['stage'],stage)
                folder=self.root/('U1_'+group+stage)
                self.assertTrue((folder/'result.json').exists())
                self.assertTrue((folder/'round_1/error.json').exists())
                self.assertTrue((folder/'round_2/turn_record.json').exists())
                self.assertNotIn('TEST_HIDDEN_SECRET',(folder/'result.json').read_text(encoding='utf-8'))
                if stage=='executor':self.assertIn('inspect_candidates',r['rounds'][0]['completed_tools'])

    def test_redundant_planner_updates_allowed_conflicting_updates_retained_and_stopped(self):
        def updated(state):
            def transport(payload):
                result=test_stub(payload)
                calls=result['choices'][0]['message'].get('tool_calls',[])
                if calls and calls[0]['function']['name']=='propose_plan':
                    args=json.loads(calls[0]['function']['arguments'])
                    args['task_updates']={'state':state}
                    calls[0]['function']['arguments']=json.dumps(args)
                return result
            return transport
        ok=self.run_arm('U1','agent',updated('Hypoxia'),tag='same')
        self.assertEqual(ok['pending_rounds'],0)
        self.assertIn('score_candidates',ok['completed_tools'])
        self.assertEqual(ok['rounds'][0]['planner_task_update_check']['unchanged'],{'state':'Hypoxia'})
        bad=self.run_arm('U1','agent',updated('Normoxia'),tag='conflict')
        self.assertEqual(bad['pending_rounds'],1)
        self.assertEqual(bad['rounds'][0]['planner_task_update_check']['conflicts'],{'state':'Normoxia'})
        self.assertEqual(bad['rounds'][0]['common_user_input'],self.cases['U1']['rounds'][0])

    def test_budget_record_matches_case_and_round_guards(self):
        settings=evaluation_settings(self.cfg,dialogue=True)
        self.assertEqual(settings['case_timeout_seconds'],720)
        self.assertEqual(settings['round_timeout_seconds'],360)
        clock=[0]
        def transport(payload):clock[0]=2;return message_response('SYNTHETIC_ONLY')
        cfg={**self.cfg,'dialogue_case_timeout_seconds':1,'dialogue_round_timeout_seconds':1}
        with patch('evaluation_dialogue.time.monotonic',side_effect=lambda:clock[0]):
            r=self.run_arm('U1','llm',transport,cfg=cfg,tag='deadline')
        self.assertEqual(r['pending_rounds'],1)
        self.assertIn('每题时限：1秒',r['rounds'][0]['error'])
        self.assertEqual(r['rounds'][0]['effective_settings']['case_timeout_seconds'],1)
        clock[0]=0
        cfg={**self.cfg,'dialogue_case_timeout_seconds':10,'dialogue_round_timeout_seconds':1}
        with patch('evaluation_dialogue.time.monotonic',side_effect=lambda:clock[0]):
            r=self.run_arm('U1','llm',transport,cfg=cfg,tag='round_deadline')
        self.assertIn('每轮时限：1秒',r['rounds'][0]['error'])
        self.assertEqual(r['rounds'][0]['effective_settings']['round_timeout_seconds'],1)

    def test_invalid_common_input_and_malformed_planner_also_retain_every_round(self):
        malformed=copy.deepcopy(self.cases['U1'])
        malformed['rounds'][0]['message']='X'*2001
        r=run_dialogue('llm',malformed,self.cfg,self.root/'bad_input',test_stub,self.resources)
        self.assertEqual(r['pending_rounds'],1)
        self.assertEqual(r['rounds'][0]['error_record']['stage'],'input_preparation')
        self.assertEqual(r['test_stub_requests'],0)
        r=self.run_arm('U1','agent',lambda p:{'choices':[]},tag='malformed')
        self.assertEqual(r['rounds'][0]['error_record']['stage'],'planner')
        self.assertEqual(r['pending_rounds'],1)
        self.assertTrue((self.root/'U1_agentmalformed/test_transport/001/stub_response.json').exists())

    def test_partial_error_payload_retained_and_redacted(self):
        from model_client import ModelError
        def partial(payload):
            error=ModelError('SYNTHETIC OUTPUT_TRUNCATED','OUTPUT_TRUNCATED')
            error.response_snapshot={'status':'incomplete','output':'TEST_HIDDEN_SECRET SYNTHETIC_PARTIAL','usage':{'total_tokens':7}}
            raise error
        result=self.run_arm('U1','llm',partial,tag='partial')
        saved=result['rounds'][0]['error_record']['partial_response']
        self.assertEqual(saved['status'],'incomplete')
        self.assertNotIn('TEST_HIDDEN_SECRET',saved['output'])
        self.assertIn('SYNTHETIC_PARTIAL',saved['output'])
        self.assertIsNone(result['total_tokens'])
        self.assertEqual(result['pending_rounds'],1)


class HumanReviewCorrections(unittest.TestCase):
    def test_complete_with_wrong_or_missing_necessary_facts_or_severe_error_is_pending(self):
        for fact,severe in (('wrong',False),('missing',False),('correct',True)):
            p,e,r=synthetic_fixture();original=copy.deepcopy(r)
            for row in r:
                if row['answer_id'].startswith('workflow'):
                    row['facts']['f1']=fact;row['severe_error']=severe
            original=copy.deepcopy(r)
            result=summarize(p,e,r)
            bad=next(row for row in result['unit_records'] if row['group']=='workflow')
            self.assertEqual(bad['delivery_judgement'],'完成')
            self.assertIsNone(bad['complete'])
            self.assertTrue(bad['pending_human_consistency_check'])
            self.assertEqual(r,original)
            self.assertIsNone(next(s for s in result['category_summaries'] if s['group']=='workflow')['completion_rate_percent'])

    def test_attributed_human_correction_resolves_without_deleting_facts_or_rewriting_scores(self):
        p,e,r=synthetic_fixture()
        aid=next(row['answer_id'] for row in p if row['group']=='workflow')
        for row in r:
            if row['answer_id']==aid:row['facts']['f1']='wrong';row['severe_error']=True
        out=summarize(p,e,r,[{'answer_id':aid,'adjudicator_id':'SYNTHETIC_HUMAN_C','reason':'SYNTHETIC_ONLY',
            'delivery_judgement':'部分完成'}])
        unit=next(v for v in out['unit_records'] if v['answer_id']==aid)
        self.assertEqual(unit['complete'],0)
        self.assertEqual(unit['facts'],{'f1':'wrong'})
        self.assertTrue(unit['original_rating_consistency_issues'][0]['issues'])
        self.assertTrue(unit['original_ratings'])
        unrun=copy.deepcopy(e)
        for record in unrun:record['execution']='NOT_EXECUTED'
        with self.assertRaisesRegex(ValueError,'未运行'):
            summarize(p,unrun,[],[{'answer_id':aid,'adjudicator_id':'SYNTHETIC_HUMAN_C',
                'reason':'SYNTHETIC_ONLY','delivery_judgement':'完成'}])
        for unit in p:unit['required_fact_ids']=[]
        with self.assertRaisesRegex(ValueError,'必要事实'):summarize(p,e,[])

    def test_excel_enum_mapping_missing_reasons_and_full_fact_rows(self):
        p,e,_=synthetic_fixture()
        sheets=synthetic_tables(p,'SYNTHETIC_REVIEWER_A')
        row=sheets['评分表'][1][1]
        row[3:7]=['','','',''];row[7]='不可评分';row[8]='待核对';row[9]='SYNTHETIC: no readable answer'
        for _,fact in sheets['逐事实'][1:]:
            if fact[0]==row[0]:fact[5]='未评分'
        out=parse_review_tables(p,sheets,{'kind':'SYNTHETIC_ONLY'})
        imported=next(r for r in out['reviews'] if r['answer_id']==row[0])
        self.assertIsNone(imported['delivery_judgement'])
        self.assertIsNone(imported['severe_error'])
        self.assertIsNone(imported['facts']['f1'])
        self.assertEqual(imported['raw_review_fields']['交付判定'],'不可评分')
        missing=copy.deepcopy(sheets);missing['逐事实'].pop()
        with self.assertRaisesRegex(ValueError,'缺行'):parse_review_tables(p,missing,{})
        row[9]=''
        with self.assertRaisesRegex(ValueError,'不可评分必须'):parse_review_tables(p,sheets,{})

    def test_strict_mean_missingness_explained_with_scorable_counts(self):
        p,e,r=synthetic_fixture()
        for row in r:
            if row['answer_id'].startswith('llm'):
                row['accuracy_0_2']=None;row['unscorable_reason']='SYNTHETIC: not scorable'
        result=summarize(p,e,r)
        group=next(s for s in result['category_summaries'] if s['group']=='llm')
        self.assertIsNone(group['quality']['accuracy_0_2'])
        self.assertEqual(group['quality_scoring_coverage']['accuracy_0_2'],{'scorable_task_count':0,'unscorable_task_count':1,'total_task_count':1})


if __name__=='__main__':unittest.main()
