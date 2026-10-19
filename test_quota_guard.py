import unittest,io,json,urllib.error,tempfile
from unittest.mock import patch
from pathlib import Path
from model_client import request_completion,ModelError,account_blocked
from test_model_client import Response
from evaluate import run_case
import paper_pilot

class QuotaTests(unittest.TestCase):
 def cfg(self):return {'provider':'doubao','api_mode':'responses','model':'test-model','base_url':'https://ark.cn-beijing.volces.com/api/v3','api_key':'TEST_ONLY','api_retries':1}
 def test_usage_limit_does_not_retry(self):
  calls=[]
  def opener(req,timeout):
   calls.append(req)
   raise urllib.error.HTTPError(req.full_url,429,'limit',{},io.BytesIO(json.dumps({'error':{'code':'SetLimitExceeded','message':'test quota'}}).encode()))
  with self.assertRaises(ModelError) as error:request_completion(self.cfg(),{'messages':[]},opener)
  self.assertEqual(len(calls),1);self.assertTrue(account_blocked(error.exception.diagnostics()))
 def test_transient_429_still_has_bounded_retry(self):
  calls=[]
  def opener(req,timeout):
   calls.append(req)
   if len(calls)==1:raise urllib.error.HTTPError(req.full_url,429,'rate',{},io.BytesIO(b'{"error":{"code":"RateLimitExceeded"}}'))
   return Response({'status':'completed','output':[{'type':'message','content':[{'type':'output_text','text':'TEST ONLY'}]}]})
  with patch('model_client.time.sleep'):
   request_completion(self.cfg(),{'messages':[]},opener)
  self.assertEqual(len(calls),2)
 def test_failed_model_case_has_elapsed_time_and_unknown_tokens(self):
  def fail(payload):raise ModelError('test limit',code='HTTP_429',provider_code='SetLimitExceeded',http_status=429)
  with tempfile.TemporaryDirectory() as root:
   r=run_case('llm',{'id':'test','request':'test'},self.cfg(),root,fail)
  self.assertTrue(account_blocked(r['provider_error']));self.assertIsNone(r['total_tokens']);self.assertIsNotNone(r['seconds'])
 def test_agent_preserves_structured_provider_code(self):
  def fail(payload):raise ModelError('test limit',code='HTTP_429',provider_code='SetLimitExceeded',http_status=429)
  with tempfile.TemporaryDirectory() as root:r=run_case('agent',{'id':'test','request':'test'},self.cfg(),root,fail)
  self.assertEqual(r['provider_error']['provider_code'],'SetLimitExceeded');self.assertIsNone(r['total_tokens'])
 def test_batch_stops_and_exports_after_first_account_block(self):
  with tempfile.TemporaryDirectory() as temp:
   root=Path(temp);(root/'evaluation_cases.example.json').write_text(json.dumps({'review_status':'TEST','cases':[{'id':'x','request':'test'}]}),encoding='utf-8');calls=[]
   def fail(group,case,cfg,folder):
    calls.append(group);return {'group':group,'case_id':case['id'],'status':'FAILED','answer':'test limit','usage':[],'seconds':.01,'provider_error':{'provider_code':'SetLimitExceeded','http_status':429}}
   with patch.object(paper_pilot,'HOME',root),patch.object(paper_pilot,'log'),patch('evaluate.run_case',fail):paper_pilot.run(lambda:{},'quota_test')
   self.assertEqual(len(calls),1);completion=json.loads((root/'evaluation_runs/quota_test/completion.json').read_text())
   self.assertEqual(completion['status'],'BLOCKED_ACCOUNT');self.assertEqual(completion['pending'],8)
   self.assertTrue((root/'evaluation_runs/quota_test/results.json').is_file())

if __name__=='__main__':unittest.main()
