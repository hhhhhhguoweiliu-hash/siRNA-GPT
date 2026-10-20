"""Export/stop regressions with explicit test transports; no model API use."""
import csv,io,json,tempfile,unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch
import evaluate,paper_pilot

class EvaluationExportTests(unittest.TestCase):
    def test_ready_plan_preserves_planner_usage_before_execution(self):
        from test_conversation import message_response
        from conversation import Conversation
        import time
        with tempfile.TemporaryDirectory() as tmp:
            def transport(payload):
                r=message_response(name='propose_plan',args={'decision':'ready','summary':'TEST','tools':['verify_target'],'question':''})
                r['usage']={'total_tokens':37};return r
            c=Conversation(root=Path(tmp),cfg_loader=lambda:{},transport=transport)
            c.submit({'interaction_mode':'auto','message':'TEST','web_enabled':False})
            deadline=time.monotonic()+5
            while c.snapshot()['busy'] and time.monotonic()<deadline:time.sleep(.01)
            self.assertEqual(c.phase,'awaiting_execution')
            planner=[e for e in c.events if e['kind']=='planner_finished']
            self.assertEqual([e['usage']['total_tokens'] for e in planner],[37])

    def suite(self,root):
        source=root/'cases.json'
        source.write_text(json.dumps({'review_status':'TEST_ONLY','cases':[
            {'id':str(i),'request':'TEST_ONLY'} for i in range(6)]}),encoding='utf-8')
        return source

    def test_cli_stops_after_access_denied_and_exports_all_54_units(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);source=self.suite(root);out=root/'out';calls=[]
            def blocked(group,case,cfg,folder):
                calls.append(group)
                return {'group':group,'case_id':case['id'],'status':'FAILED','answer':'TEST_SECRET',
                    'provider_error':{'provider_code':'AccessDenied','http_status':403},'total_tokens':None}
            with patch.object(evaluate,'config',lambda:{'api_key':'TEST_SECRET'}),patch.object(evaluate,'run_case',blocked),redirect_stdout(io.StringIO()):
                evaluate.main(['--cases',str(source),'--output',str(out),'--group','all','--repeats','3'])
            self.assertEqual(len(calls),1)
            completion=json.loads((out/'completion.json').read_text())
            self.assertEqual((completion['status'],completion['pending']),('BLOCKED_ACCOUNT',53))
            rows=list(csv.DictReader((out/'execution_status.tsv').open(encoding='utf-8-sig'),delimiter='\t'))
            self.assertEqual(len(rows),54)
            self.assertEqual(sum(r['execution']=='NOT_EXECUTED' for r in rows),53)
            self.assertNotIn('TEST_SECRET',(out/'results.json').read_text())
            self.assertEqual(len(json.loads((out/'protocol.json').read_text())['scheduled_order']),54)

    def test_missing_model_usage_remains_unknown_and_raw_answer_is_saved(self):
        with tempfile.TemporaryDirectory() as tmp:
            for usage,expected in [(None,None),({'input_tokens':7},None),({'total_tokens':11},11)]:
                response={'choices':[{'message':{'content':'TEST_ONLY'}}]}
                if usage is not None:response['usage']=usage
                r=evaluate.run_case('llm',{'id':'x','request':'TEST_ONLY'},
                    {'model':'TEST','api_key':'TEST_SECRET'},tmp,lambda p:response)
                self.assertEqual(r['total_tokens'],expected)
                self.assertEqual(r['usage_complete'],expected is not None)
            self.assertTrue((Path(tmp)/'model_request.json').is_file())
            self.assertIn('TEST_ONLY',(Path(tmp)/'model_response.json').read_text())

    def test_timeout_preserves_partial_pilot_and_no_further_case_starts(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);self.suite(root).rename(root/'evaluation_cases.example.json')
            with patch.object(paper_pilot,'HOME',root),patch.object(paper_pilot,'log'),patch('evaluate.run_case',side_effect=TimeoutError('TEST timeout')) as run:
                paper_pilot.run(lambda:{},'timeout_test')
            out=root/'evaluation_runs/timeout_test'
            self.assertEqual(run.call_count,1)
            completion=json.loads((out/'completion.json').read_text())
            self.assertEqual((completion['status'],completion['pending']),('STOPPED_TIMEOUT',53))
            self.assertEqual(json.loads((out/'results.json').read_text())[0]['status'],'TIMED_OUT')
            self.assertTrue((out/'blind_answers.tsv').is_file())

if __name__=='__main__':unittest.main()
