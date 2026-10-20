"""Protocol reproducibility and secret exclusion; no API."""
import json, tempfile, unittest
from pathlib import Path
from unittest.mock import patch
import evaluate, paper_pilot
from evaluation_protocol import evaluation_settings, settings_sha256

class ProtocolTests(unittest.TestCase):
    def test_planner_partial_response_is_exported_without_scientific_calls_or_fake_total(self):
        from model_client import request_completion
        from test_model_client import Response
        cfg={'provider':'doubao','api_mode':'responses','model':'TEST','api_key':'TEST_SECRET',
             'base_url':'https://ark.cn-beijing.volces.com/api/v3','max_output_tokens':37}
        partial={'status':'incomplete','incomplete_details':{'reason':'max_output_tokens'},
            'usage':{'total_tokens':41},'output':[{'type':'message','content':[{'type':'output_text','text':'TEST_SECRET partial'}]}]}
        def transport(payload):return request_completion(cfg,payload,lambda req,timeout:Response(partial))
        with tempfile.TemporaryDirectory() as tmp:
            r=evaluate.run_case('agent',{'id':'x','request':'TEST'},cfg,tmp,transport)
            self.assertEqual((r['status'],r['tool_calls']),('FAILED',0))
            self.assertIsNone(r['total_tokens']);self.assertFalse(r['usage_complete'])
            self.assertEqual(r['known_token_subtotal'],41)
            record=r['record']['evidence_records'][0]
            self.assertEqual(record['response']['incomplete_details']['reason'],'max_output_tokens')
            self.assertEqual(record['request']['max_output_tokens'],37)
            self.assertNotIn('TEST_SECRET',json.dumps(r))

    def test_executor_partial_payload_and_prior_usage_survive_in_run_archive(self):
        from model_client import request_completion
        from test_model_client import Response
        from test_conversation import message_response
        cfg={'provider':'doubao','api_mode':'responses','model':'TEST','api_key':'TEST_SECRET',
             'base_url':'https://ark.cn-beijing.volces.com/api/v3','max_output_tokens':37}
        partial={'status':'incomplete','incomplete_details':{'reason':'max_output_tokens'},
                 'usage':{'total_tokens':41},'output':[]}
        calls=[]
        def transport(payload):
            calls.append(payload)
            if len(calls)==1:return message_response(name='propose_plan',args={'decision':'ready','summary':'TEST','tools':['verify_target'],'question':''})
            return request_completion(cfg,payload,lambda req,timeout:Response(partial))
        with tempfile.TemporaryDirectory() as tmp:
            r=evaluate.run_case('agent',{'id':'x','request':'TEST'},cfg,tmp,transport)
            self.assertEqual((r['status'],r['tool_calls']),('FAILED',0))
            self.assertIsNone(r['total_tokens']);self.assertEqual(r['known_token_subtotal'],44)
            self.assertEqual(len(calls),2)
            files=list(Path(tmp).rglob('*_error.json'));self.assertEqual(len(files),1)
            saved=json.loads(files[0].read_text(encoding='utf-8'))
            self.assertEqual(saved['response'],partial)
            self.assertEqual(saved['request']['max_output_tokens'],37)
            self.assertNotIn('TEST_SECRET',files[0].read_text(encoding='utf-8'))

    def test_chat_length_failure_keeps_actual_payload_and_request_identity(self):
        from model_client import request_completion,ModelError
        from test_model_client import Response
        cfg={'provider':'doubao','api_mode':'chat','model':'TEST','api_key':'TEST_SECRET',
             'base_url':'https://ark.cn-beijing.volces.com/api/v3','max_output_tokens':37}
        partial={'choices':[{'finish_reason':'length','message':{'content':'partial'}}], 'usage':{'total_tokens':41}}
        with self.assertRaises(ModelError) as caught:
            request_completion(cfg,{'messages':[]},lambda req,timeout:Response(partial))
        self.assertEqual(caught.exception.response_snapshot,partial)
        self.assertEqual(caught.exception.request_snapshot['max_tokens'],37)
        self.assertEqual(caught.exception.request_id,'test-request')

    def test_effective_settings_exclude_secrets_and_capture_nondefault_controls(self):
        cfg = {'api_key':'TEST_SECRET','base_url':'https://private.invalid',
            'max_output_tokens':2048,'thinking':'disabled','request_timeout':73,
            'api_retries':0,'max_model_turns':9,'max_tool_calls':14}
        s = evaluation_settings(cfg)
        self.assertEqual([s[k] for k in ['max_output_tokens','request_timeout_seconds','api_retries',
            'max_model_turns','max_tool_calls']], [2048,73,0,9,14])
        self.assertNotIn('TEST_SECRET',json.dumps(s))
        self.assertNotIn('private.invalid',json.dumps(s))
        self.assertEqual(settings_sha256(s),settings_sha256(dict(reversed(list(s.items())))))
        self.assertNotEqual(settings_sha256(s),settings_sha256(evaluation_settings({})))

    def test_both_launchers_export_same_effective_settings_before_first_case(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);source=root/'evaluation_cases.example.json'
            source.write_text(json.dumps({'review_status':'TEST_ONLY','cases':[{'id':'x','request':'TEST'}]}))
            cfg={'model':'TEST','max_output_tokens':2048,'api_key':'TEST_SECRET'}
            def run(group,case,cfg,folder):
                protocol=json.loads((Path(folder).parent/'protocol.json').read_text())
                self.assertEqual(protocol['model_settings'],evaluation_settings(cfg))
                self.assertEqual(protocol['model_settings_sha256'],settings_sha256(evaluation_settings(cfg)))
                return {'case_id':case['id'],'group':group,'status':'TEST','answer':'TEST'}
            with patch.object(evaluate,'config',return_value=cfg),patch.object(evaluate,'run_case',side_effect=run):
                evaluate.main(['--cases',str(source),'--output',str(root/'cli'),'--repeats','1'])
            with patch.object(paper_pilot,'HOME',root),patch.object(paper_pilot,'log'),patch.object(evaluate,'run_case',side_effect=run):
                paper_pilot.run(lambda:cfg,'protocol_test')
            web=json.loads((root/'evaluation_runs/protocol_test/protocol.json').read_text())
            cli=json.loads((root/'cli/protocol.json').read_text())
            self.assertEqual(cli['model_settings'],web['model_settings'])
            self.assertNotIn('TEST_SECRET',json.dumps(web))

if __name__=='__main__':unittest.main()
