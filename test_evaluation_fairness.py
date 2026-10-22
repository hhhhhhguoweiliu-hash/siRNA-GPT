"""Actual local tool evidence + explicitly fake model; no API and no scientific scores."""
import csv,json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from core import config,default_candidates
from evaluate import run_case,export_answers
from test_conversation import message_response
from evaluation_contract import FINAL_ANSWER_STYLE,input_sha256

class FairnessTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
        self.cases=json.loads(Path('evaluation_cases.example.json').read_text(encoding='utf-8'))['cases']
        self.cfg=config();self.cfg['api_key']='TEST_SECRET'
    def tearDown(self):self.tmp.cleanup()
    def test_same_complete_raw_candidates_and_conditions_reach_all_three_arms(self):
        for case in self.cases:
            inputs=[];model_inputs=[]
            for group in ('llm','workflow','agent'):
                folder=self.root/(case['id']+'_'+group)
                def fake(payload):
                    model_inputs.append((group,payload))
                    if group=='agent':return message_response(name='propose_plan',args={'decision':'clarify','summary':'TEST_ONLY','tools':[],'question':''})
                    return message_response('TEST_ONLY')
                run_case(group,case,self.cfg,folder,fake)
                inputs.append(json.loads((folder/'case_input.json').read_text(encoding='utf-8')))
            self.assertEqual(inputs[0],inputs[1]);self.assertEqual(inputs[1],inputs[2])
            for group,payload in model_inputs:
                supplied=json.loads(payload['messages'][1]['content'])['input']
                self.assertEqual(supplied,inputs[0]['input'])
                self.assertIn(FINAL_ANSWER_STYLE,payload['messages'][0]['content'])
                if group=='llm':
                    self.assertNotIn('tools',payload)
                    self.assertNotIn('oligoformer_scaled_score',payload['messages'][1]['content'])
                if case['id']=='invalid_sequence':self.assertEqual(supplied['candidates'][0]['guide_core19_5to3'],'AAA')
                if case['id']=='ambiguous_direction':self.assertEqual(supplied['candidates'][0]['guide_21nt_RNA_5to3'],'A'*21)
                if case['id']=='unsupported_target':self.assertEqual(supplied['task']['gene'],'KRAS')
    def test_real_full_workflow_fields_match_review_anchors_and_units(self):
        for case,state_counts in [(self.cases[0],[463,811]),(self.cases[1],[480,858,1155])]:
            r=run_case('workflow',case,self.cfg,self.root/case['id'])
            byid={x['candidate_id']:x for x in r['tool_results']['query_expression']['candidate_summary']}
            for suffix,expected in [('3499',[778,777,728,726]),('3500',[1548,1547,1333,1330]),('1157',[2197,2197,1876,1874])]:
                row=byid['VEGFA_SD_'+suffix]
                self.assertEqual([row[k] for k in ['seed_site_count_all','seed_site_count_nontarget','matched_genes','baseline_mapped_genes']],expected)
            ids=r['tool_results']['compile_report']['selected_for_review']
            self.assertEqual([byid[c]['state_detected_genes'] for c in ids],state_counts)
            self.assertIn('seed位点(含VEGFA)',r['answer']);self.assertIn('可映射基因',r['answer'])
            rows={x['candidate_id']:x for x in r['tool_results']['verify_target']['rows']}
            self.assertEqual(rows['VEGFA_SD_3499']['design_window_start_1based'],'3499')
            self.assertEqual(rows['VEGFA_SD_3499']['core_start_1based'],3501)
            self.assertEqual(rows['VEGFA_SD_3499']['core_end_1based'],3519)
    def test_target_only_contains_all_nine_actual_core_coordinates_and_no_extra_tools(self):
        r=run_case('workflow',self.cases[2],self.cfg,self.root/'target')
        self.assertEqual(r['completed_tools'],['inspect_candidates','verify_target'])
        self.assertEqual(r['status'],'PARTIAL_COMPLETE')
        for row in default_candidates():self.assertIn(row['candidate_id'],r['answer'])
        self.assertIn('3501–3519',r['answer']);self.assertIn('未评分',r['answer'])
    def test_invalid_inputs_stop_before_scoring_and_echo_actual_provided_sequence(self):
        for case in self.cases[3:]:
            r=run_case('workflow',case,self.cfg,self.root/case['id'])
            self.assertEqual(r['completed_tools'],[])
            self.assertNotIn('score_candidates',r['tool_results'])
            for heading in ['判定','关键结果','证据','限制或下一步']:self.assertIn(heading,r['answer'])
            if case['id']=='invalid_sequence':self.assertIn('AAA',r['answer'])
            if case['id']=='ambiguous_direction':self.assertIn('A'*21,r['answer'])
    def test_complete_review_context_preserves_answers_has_blank_scores_and_separate_key(self):
        case=self.cases[3];out=self.root/'export';out.mkdir()
        r=run_case('workflow',case,self.cfg,out/'A001');r.update(answer_id='A001',repeat=1)
        export_answers(out,[case],[r])
        review=out/'for_review';task=json.loads((review/'complete_tasks.json').read_text(encoding='utf-8'))[0]
        self.assertEqual(task['resolved_input']['candidates'][0]['guide_core19_5to3'],'AAA')
        self.assertTrue(task['requirements']);self.assertTrue((out/'private_key.tsv').is_file())
        self.assertEqual(list(review.rglob('private_key*')),[])
        self.assertEqual((review/'answers/A001/answer.txt').read_text(encoding='utf-8'),r['answer'])
        with (review/'blank_scores.tsv').open(encoding='utf-8-sig') as f:row=next(csv.DictReader(f,delimiter='\t'))
        for k in ['reviewer_id','accuracy_0_2','evidence_0_2','task_fit_0_2','limits_0_2']:self.assertEqual(row[k],'')
        evidence=json.loads((review/'answers/A001/evidence.json').read_text(encoding='utf-8'))
        self.assertNotIn('group',evidence)
    def test_raw_complete_provider_response_and_effective_request_are_saved(self):
        from model_client import request_completion
        from test_model_client import Response
        raw={'status':'completed','model':'TEST','usage':{'total_tokens':9},'output':[{'type':'message','content':[{'type':'output_text','text':'TEST_ONLY'}]}]}
        cfg={**self.cfg,'model':'TEST','max_output_tokens':91}
        r=request_completion(cfg,{'messages':[]},lambda req,timeout:Response(raw))
        self.assertEqual(r['_raw_response'],raw);self.assertEqual(r['_request']['max_output_tokens'],91)
    def test_manual_diagnostic_runs_exactly_one_case_and_retains_settings(self):
        import paper_pilot
        suite={'review_status':'TEST_ONLY','cases':self.cases}
        (self.root/'evaluation_cases.example.json').write_text(json.dumps(suite),encoding='utf-8')
        def fake(group,case,cfg,folder):return {'group':group,'case_id':case['id'],'status':'TEST_ONLY','answer':'TEST_ONLY'}
        with patch.object(paper_pilot,'HOME',self.root),patch.object(paper_pilot,'log'),patch('evaluate.run_case',side_effect=fake) as run:
            paper_pilot.run(lambda:self.cfg,'diag_test',mode='diagnostic')
        self.assertEqual(run.call_count,1);self.assertEqual(run.call_args.args[:2],('llm',self.cases[0]))
        p=json.loads((self.root/'evaluation_runs/diag_test/protocol.json').read_text(encoding='utf-8'))
        self.assertEqual(p['planned_observations'],1);self.assertEqual(p['model_settings']['max_output_tokens'],1800)
    def test_planner_cannot_replace_explicit_unsupported_raw_target_with_vegfa(self):
        case=self.cases[4]
        def fake(payload):return message_response(name='propose_plan',args={'decision':'ready','summary':'TEST_ONLY','tools':['compile_report'],'question':'','task_updates':{'gene':'VEGFA'}})
        r=run_case('agent',case,self.cfg,self.root/'scope',fake)
        self.assertEqual(r['status'],'FAILED');self.assertEqual(r['tool_calls'],0)
        self.assertIn('KRAS',r['record']['result']['message'])
    def test_http_diagnostic_preserves_manual_usage_ack_and_has_one_planned_record(self):
        import os,cloud
        from test_cloud import call
        with patch.dict(os.environ,{'WEB_PASSWORD':'TEST_WEB_PASSWORD_123456789','RENDER_EXTERNAL_HOSTNAME':'sirna-test.onrender.com','RENDER_EXTERNAL_URL':'https://sirna-test.onrender.com'}),patch.dict(cloud.local.STATE,{'running':False,'checking_connection':False}),patch.object(cloud.local.CONVERSATION,'busy',False),patch.dict(__import__('paper_pilot').STATE,{'status':'NOT_STARTED'}):
            self.assertEqual(call('/api/development-evaluation-start','POST',{'mode':'diagnostic','confirm_api_usage':False})[0],400)
            with patch.object(cloud.local.threading,'Thread'):
                code,body,_=call('/api/development-evaluation-start','POST',{'mode':'diagnostic','confirm_api_usage':True})
            self.assertEqual(code,202);self.assertEqual(json.loads(body)['expected_records'],1)

if __name__=='__main__':unittest.main()
