"""Regression checks for the user's 403 case; all network responses are explicit fakes."""
import unittest, io, json, urllib.error
from model_client import request_completion, ModelError

class DiagnosticTests(unittest.TestCase):
 def setUp(self):
  self.cfg={'provider':'doubao','api_mode':'responses','base_url':'https://ark.cn-beijing.volces.com/api/v3','model':'doubao-test','api_key':'TEST_SECRET_ONLY','api_retries':0}
 def error(self,code='AccessDenied',message='No permission for project alpha',headers=None,body=None):
  def fake(req,timeout):
   value={'error':{'code':code,'message':message}} if body is None else body
   raise urllib.error.HTTPError(req.full_url,403,'Forbidden',headers or {},io.BytesIO(json.dumps(value).encode()))
  with self.assertRaises(ModelError) as caught:request_completion(self.cfg,{'messages':[]},opener=fake)
  return caught.exception
 def test_access_denied_keeps_explanation_and_request_id(self):
  e=self.error(headers={'x-request-id':'req_diag_403'})
  self.assertEqual(e.provider_code,'AccessDenied');self.assertEqual(e.request_id,'req_diag_403')
  self.assertIn('project alpha',str(e));self.assertEqual(e.diagnostics()['http_status'],403)
 def test_error_fields_are_redacted(self):
  e=self.error(message='Rejected Bearer TEST_SECRET_ONLY',headers={'x-request-id':'TEST_SECRET_ONLY'})
  self.assertNotIn('TEST_SECRET_ONLY',str(e));self.assertNotIn('TEST_SECRET_ONLY',json.dumps(e.diagnostics()))
 def test_no_cause_invented_without_server_message(self):
  e=self.error(body={})
  self.assertEqual(e.provider_message,'');self.assertIn('不能仅凭HTTP',str(e))
 def test_provider_overdue_and_service_not_open_distinct(self):
  overdue=self.error(code='AccountOverdueError',message='account overdue')
  unopened=self.error(code='OperationDenied.ServiceNotOpen',message='model not activated')
  self.assertNotEqual(str(overdue),str(unopened));self.assertIn('账户欠费',str(overdue));self.assertIn('尚未开通',str(unopened))

if __name__=='__main__':unittest.main(verbosity=2)
