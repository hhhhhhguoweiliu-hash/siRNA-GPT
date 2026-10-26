"""HTTP/website integration fixtures. No network, paid models or human grades."""
import copy
import io
import json
import os
import tempfile
import unittest
import urllib.error
import zipfile
from pathlib import Path
from unittest.mock import patch
import dialogue_evaluation as entry
import paper_pilot
from evaluation_dialogue import run_dialogue
from evaluation_transport import RecordedTransport
from model_client import ModelError,request_completion
from test_evaluation_dialogue import test_stub


CFG={'provider':'doubao','model':'SYNTHETIC_HTTP_MODEL','api_mode':'responses',
    'base_url':'https://ark.cn-beijing.volces.com/api/v3','api_key':'SYNTHETIC_TEST_SECRET',
    'thinking':'disabled','max_output_tokens':1800,'request_timeout':90,'api_retries':1,
    'max_model_turns':12,'max_tool_calls':18}


class HTTPResponse(io.BytesIO):
    def __init__(self,value):
        super().__init__(json.dumps(value,ensure_ascii=False).encode())
        self.headers={'x-request-id':'SYNTHETIC_HTTP_REQUEST_ID'}


def fixture_response(req,timeout):
    body=json.loads(req.data)
    if 'input' in body:
        messages=[{'role':'system','content':body.get('instructions','')}]
        for item in body['input']:
            if item.get('type')=='message':messages.append({'role':item['role'],'content':'\n'.join(c.get('text','') for c in item.get('content',[]))})
        tools=[{'type':'function','function':{k:v for k,v in t.items() if k!='type'}} for t in body.get('tools',[])]
        answer=test_stub({'messages':messages,'tools':tools})['choices'][0]['message']
        output=[]
        for call in answer.get('tool_calls',[]):output.append({'type':'function_call','call_id':call['id'],**call['function']})
        if answer.get('content'):output.append({'type':'message','role':'assistant','content':[{'type':'output_text','text':answer['content']}]})
        return HTTPResponse({'id':'SYNTHETIC_RESPONSE','model':'SYNTHETIC_RETURNED_VERSION','status':'completed',
            'output':output,'usage':{'input_tokens':10,'output_tokens':5,'total_tokens':15}})
    response=test_stub(body);response.update(id='SYNTHETIC_CHAT',model='SYNTHETIC_RETURNED_VERSION',usage={'total_tokens':15})
    return HTTPResponse(response)


class DialogueEntryTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)
        self.cfg=copy.deepcopy(CFG)
        suite,self.resources=entry.load_package();self.cases={c['id']:c for c in suite['cases']}
        paper_pilot.STOP.clear()
    def tearDown(self):
        paper_pilot.STOP.clear();self.temp.cleanup()

    def test_web_auth_confirmation_and_current_plan_hash_required(self):
        import cloud
        from test_cloud import call
        env={'WEB_PASSWORD':'TEST_WEB_PASSWORD_123456789','RENDER_EXTERNAL_HOSTNAME':'sirna-test.onrender.com','RENDER_EXTERNAL_URL':'https://sirna-test.onrender.com'}
        with patch.dict(os.environ,env),patch.object(cloud.local,'config',lambda:self.cfg),patch.dict(cloud.local.STATE,{'running':False,'checking_connection':False}),patch.object(cloud.local.CONVERSATION,'busy',False),patch.dict(paper_pilot.STATE,{'status':'NOT_STARTED'},clear=True),patch.object(cloud.local.threading,'Thread') as thread,patch('urllib.request.urlopen',side_effect=AssertionError('NO NETWORK')):
            self.assertEqual(call('/api/development-evaluation-plan',auth=False)[0],401)
            code,body,_=call('/api/development-evaluation-plan');self.assertEqual(code,200)
            plan=json.loads(body)['batch'];self.assertEqual(plan['planned_units'],27)
            self.assertNotIn('SYNTHETIC_TEST_SECRET',body.decode())
            data={'protocol':'dialogue-v3','mode':'batch','plan_sha256':plan['plan_sha256']}
            self.assertEqual(call('/api/development-evaluation-start','POST',data)[0],400)
            self.assertEqual(call('/api/development-evaluation-start','POST',{**data,'confirm_api_usage':True,'plan_sha256':'stale'})[0],409)
            self.assertEqual(call('/api/development-evaluation-start','POST',{**data,'confirm_api_usage':True},origin='https://foreign.example')[0],403)
            code,body,_=call('/api/development-evaluation-start','POST',{**data,'confirm_api_usage':True})
            self.assertEqual(code,202);self.assertEqual(json.loads(body)['expected_records'],27)
            thread.return_value.start.assert_called_once()

    def test_provider_requires_confirmation_and_forbids_unlabelled_fixture(self):
        with self.assertRaises(ValueError):run_dialogue('llm',self.cases['U1'],self.cfg,self.root/'no',execution_mode='provider')
        with self.assertRaises(ValueError):run_dialogue('llm',self.cases['U1'],self.cfg,self.root/'no',test_stub,execution_mode='provider',confirm_api_usage=True)
        self.assertFalse((self.root/'no').exists())

    def test_responses_adapter_agent_planner_executor_usage_and_versions_recorded(self):
        r=run_dialogue('agent',self.cases['W2b'],self.cfg,self.root/'agent',resources=self.resources,
            execution_mode='http_fixture',http_opener=fixture_response)
        self.assertIn('score_candidates',r['completed_tools'])
        self.assertGreater(r['synthetic_http_attempts'],1);self.assertEqual(r['real_model_requests'],0)
        self.assertEqual(r['provider_model_versions'],['SYNTHETIC_RETURNED_VERSION'])
        self.assertIsNone(r['total_tokens']);self.assertFalse(r['usage_complete'])
        folder=self.root/'agent/model_transport/001'
        physical=json.loads((folder/'http_attempt_01.json').read_text(encoding='utf-8'))
        actual=physical['events'][0]['request']
        self.assertIn('at_utc',physical['events'][0])
        self.assertIn('input',actual);self.assertNotIn('messages',actual)
        self.assertEqual(actual['max_output_tokens'],1800)
        self.assertIn('thinking',actual)
        raw=''.join(p.read_text(encoding='utf-8') for p in (self.root/'agent').rglob('*.json'))
        self.assertNotIn(self.cfg['api_key'],raw)

    def test_provider_accounting_branch_uses_nonzero_counters_under_patched_network_only(self):
        # Counter logic test only. No actual API occurred; never export as evidence.
        with patch('urllib.request.urlopen',fixture_response):
            r=run_dialogue('llm',self.cases['U1'],self.cfg,self.root/'provider_counter_test',resources=self.resources,
                execution_mode='provider',confirm_api_usage=True)
        self.assertEqual(r['real_model_requests'],2)
        self.assertEqual(r['total_tokens'],30)
        self.assertEqual(r['record_kind'],'REAL_EVALUATION_ATTEMPT_NOT_HUMAN_SCORED')
        self.assertNotIn('OFFLINE_MODEL_STUB',r['rounds'][0]['answer_source'])
        self.assertIsNone(r['rounds'][0]['raw_model_answer_TEST_ONLY'])

    def test_chat_adapter_is_also_audited(self):
        cfg={**self.cfg,'api_mode':'chat'}
        t=RecordedTransport(cfg,self.root/'chat',mode='http_fixture',opener=fixture_response)
        t({'messages':[{'role':'user','content':'SYNTHETIC_ONLY'}]})
        saved=json.loads((self.root/'chat/001/http_attempt_01.json').read_text(encoding='utf-8'))
        self.assertIn('messages',saved['events'][0]['request'])
        self.assertEqual(t.summary()['http_attempts'],1)
        def empty(req,timeout):return HTTPResponse({'choices':[{'finish_reason':'stop','message':{'role':'assistant','content':''}}],'usage':{'total_tokens':3}})
        r=run_dialogue('llm',self.cases['U1'],cfg,self.root/'empty',execution_mode='http_fixture',http_opener=empty)
        self.assertEqual(r['pending_rounds'],1)
        self.assertIn('没有返回可读回答',r['rounds'][0]['error'])

    def test_retry_records_every_attempt_and_never_guesses_missing_usage(self):
        calls=[]
        def opener(req,timeout):
            calls.append(1)
            if len(calls)==1:raise urllib.error.HTTPError(req.full_url,429,'fixture',{},io.BytesIO(b'{"error":{"code":"Throttling"},"usage":{"total_tokens":4}}'))
            return fixture_response(req,timeout)
        t=RecordedTransport(self.cfg,self.root/'retry',mode='http_fixture',opener=opener)
        with patch('model_client.time.sleep'):t({'messages':[{'role':'user','content':'SYNTHETIC_ONLY'}]})
        self.assertEqual(t.summary()['http_retries'],1);self.assertEqual(t.summary()['http_attempts'],2)
        self.assertEqual([u['total_tokens'] for u in t.summary()['synthetic_usage']],[4,15])
        self.assertTrue((self.root/'retry/001/http_attempt_02.json').exists())
        self.assertFalse(t.summary()['usage_complete'])

    def test_incomplete_response_preserves_actual_payload_usage_and_pending_round(self):
        def incomplete(req,timeout):return HTTPResponse({'status':'incomplete','model':'SYNTHETIC_RETURNED_VERSION',
            'incomplete_details':{'reason':'max_output_tokens'},'output':[{'type':'message','content':[{'type':'output_text','text':'SYNTHETIC_PARTIAL'}]}],'usage':{'total_tokens':7}})
        r=run_dialogue('llm',self.cases['U1'],self.cfg,self.root/'partial',execution_mode='http_fixture',http_opener=incomplete)
        self.assertEqual(r['pending_rounds'],1);self.assertEqual(r['provider_error']['code'],'OUTPUT_TRUNCATED')
        saved=json.loads((self.root/'partial/model_transport/001/error.json').read_text(encoding='utf-8'))
        self.assertEqual(saved['response']['incomplete_details']['reason'],'max_output_tokens')
        self.assertEqual(saved['response']['usage']['total_tokens'],7)
        self.assertEqual(r['real_model_requests'],0)

    def test_request_timeout_clamped_to_remaining_budget_and_no_timeout_retry(self):
        seen=[]
        def opener(req,timeout):seen.append(timeout);raise TimeoutError('SYNTHETIC_TIMEOUT')
        with self.assertRaises(ModelError):request_completion(self.cfg,{'messages':[]},opener=opener,remaining_seconds=lambda:0.25)
        self.assertEqual(seen,[0.25])

    def test_account_block_preserves_all_plan_units_and_does_not_retry(self):
        count=[]
        def blocked(req,timeout):
            count.append(1)
            raise urllib.error.HTTPError(req.full_url,429,'fixture',{},io.BytesIO(b'{"error":{"code":"SetLimitExceeded","message":"SYNTHETIC ONLY"}}'))
        plan=entry.prepare(self.cfg)[0]
        with patch.object(entry,'HOME',self.root),patch.object(paper_pilot,'log'):
            state=entry.run(lambda:self.cfg,'blocked_fixture',confirm_api_usage=True,plan_sha256=plan['plan_sha256'],execution_mode='http_fixture',http_opener=blocked)
        self.assertEqual(state['status'],'BLOCKED_ACCOUNT');self.assertEqual(len(count),1)
        rows=json.loads((self.root/'evaluation_runs/blocked_fixture/execution_status.json').read_text(encoding='utf-8'))
        self.assertEqual(len(rows),27)
        self.assertTrue(any(r['execution']=='NOT_EXECUTED' for r in rows))
        out=self.root/'evaluation_runs/blocked_fixture'
        with zipfile.ZipFile(out/'reviewer_package.zip') as z:
            self.assertFalse(any('private_group' in n or 'http_attempt' in n for n in z.namelist()))
            self.assertIn('程序HTTP替身检查专用',z.read('README.md').decode())
            payload=json.loads(z.read('score_workbook_payload.json'))
            self.assertEqual(len(payload['sheets']['评分表']),28)
            self.assertTrue(all(all(x is None for x in row[2:]) for row in payload['sheets']['评分表'][1:]))
        before=(out/'execution_status.json').read_bytes()
        with patch.object(entry,'HOME',self.root):
            with self.assertRaises(ValueError):entry.run(lambda:self.cfg,'blocked_fixture',confirm_api_usage=True,plan_sha256=plan['plan_sha256'],execution_mode='http_fixture',http_opener=blocked)
        self.assertEqual((out/'execution_status.json').read_bytes(),before)
        self.assertFalse(paper_pilot.LOCK.locked())

    def test_plan_budget_and_review_versions_bind_before_manual_confirmation(self):
        from dialogue_review import remove_identity
        self.assertEqual(remove_identity({'mode':'agent','scientific_model':{'mode':'eval'},'group':'Normoxia'}),
            {'scientific_model':{'mode':'eval'},'group':'Normoxia'})
        p,_,_,_=entry.prepare(self.cfg)
        self.assertEqual(p['planned_units'],27);self.assertEqual(p['planned_user_round_units'],33)
        self.assertEqual(p['max_logical_model_requests'],154);self.assertEqual(p['max_http_attempts'],308)
        self.assertEqual(p['qa_excluded_before_run'],['Q1','Q2'])
        self.assertEqual(p['max_output_tokens_across_requests'],277200)
        changed=entry.prepare({**self.cfg,'max_output_tokens':900})[0]
        self.assertNotEqual(p['plan_sha256'],changed['plan_sha256'])
        self.assertIn('fact_standards_sha256',p)


if __name__=='__main__':unittest.main()
