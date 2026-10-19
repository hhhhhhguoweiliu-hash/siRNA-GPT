import unittest,json,io,urllib.error
from model_client import extract_model,responses_payload,normalize_responses,request_completion,test_connection,ModelError,endpoint,readiness,redact

class Response(io.BytesIO):
 def __init__(self,data):super().__init__(json.dumps(data).encode());self.headers={'x-request-id':'test-request'}
class ModelTests(unittest.TestCase):
 def setUp(self):self.cfg={'provider':'doubao','api_mode':'responses','model':'doubao-seed-2-1-pro-260915','base_url':'https://ark.cn-beijing.volces.com/api/v3','api_key':'TEST_SECRET_ONLY','api_retries':0}
 def response(self):return {'id':'resp_test','status':'completed','output':[{'type':'function_call','call_id':'call_1','name':'inspect_candidates','arguments':'{}'}],'usage':{'input_tokens':10,'output_tokens':3,'total_tokens':13}}
 def test_extract_python_model(self):self.assertEqual(extract_model('model="ep-test"'),'ep-test')
 def test_extract_json_model(self):self.assertEqual(extract_model('{"model":"doubao-test"}'),'doubao-test')
 def test_numeric_rejected(self):
  with self.assertRaises(ModelError):extract_model('2133169827')
 def test_endpoint(self):self.assertTrue(endpoint(self.cfg).endswith('/responses'))
 def test_full_endpoint_normalized(self):
  self.cfg['base_url']+='/responses';self.assertTrue(endpoint(self.cfg).endswith('/v3/responses'))
 def test_wrong_host_rejected_for_ark_key(self):
  self.cfg['base_url']='https://foreign.example/api/v3'
  with self.assertRaises(ModelError):endpoint(self.cfg)
 def test_history_conversion(self):
  p=responses_payload({'messages':[{'role':'system','content':'rules'},{'role':'user','content':'task'},{'role':'assistant','content':None,'tool_calls':[{'id':'call_1','function':{'name':'inspect_candidates','arguments':'{}'}}]},{'role':'tool','tool_call_id':'call_1','content':'{"status":"OK"}'}],'tools':[{'type':'function','function':{'name':'inspect_candidates','parameters':{'type':'object','properties':{}}}}],'tool_choice':'auto','thinking':{'type':'disabled'}})
  self.assertEqual(p['instructions'],'rules');self.assertEqual([x.get('type') for x in p['input']],[None,'function_call','function_call_output']);self.assertEqual(p['tools'][0]['name'],'inspect_candidates')
 def test_forced_tool_conversion(self):
  r=responses_payload({'tool_choice':{'type':'function','function':{'name':'connection_probe'}}});self.assertEqual(r['tool_choice'],{'type':'function','name':'connection_probe'})
 def test_response_tool_call_conversion(self):self.assertEqual(normalize_responses(self.response())['choices'][0]['message']['tool_calls'][0]['id'],'call_1')
 def test_response_text_conversion(self):
  r=normalize_responses({'status':'completed','output':[{'type':'message','content':[{'type':'output_text','text':'done'}]}]});self.assertEqual(r['choices'][0]['message']['content'],'done')
 def test_truncated_rejected(self):
  with self.assertRaises(ModelError):normalize_responses({'status':'incomplete','output':[]})
 def test_real_request_shape_with_explicit_fake_opener(self):
  def fake(req,timeout):
   body=json.loads(req.data);self.assertTrue(req.full_url.endswith('/responses'));self.assertIn('input',body);self.assertNotIn('messages',body);self.assertEqual(req.get_header('Authorization'),'Bearer TEST_SECRET_ONLY');return Response(self.response())
  r=request_completion(self.cfg,{'messages':[{'role':'user','content':'hello'}]},opener=fake);self.assertEqual(r['_request_id'],'test-request')
 def test_http_401_classified_and_key_not_echoed(self):
  def fake(req,timeout):raise urllib.error.HTTPError(req.full_url,401,'bad',{},io.BytesIO(json.dumps({'error':{'code':'TEST_SECRET_ONLY'}}).encode()))
  with self.assertRaises(ModelError) as caught:request_completion(self.cfg,{'messages':[]},opener=fake)
  self.assertEqual(caught.exception.code,'HTTP_401');self.assertNotIn('TEST_SECRET_ONLY',str(caught.exception))
 def test_network_block_classified(self):
  def fake(req,timeout):
   e=OSError('blocked');e.winerror=10013;raise urllib.error.URLError(e)
  with self.assertRaises(ModelError) as caught:request_completion(self.cfg,{'messages':[]},opener=fake)
  self.assertEqual(caught.exception.code,'NETWORK_BLOCKED')
 def test_probe_requires_function_call(self):
  with self.assertRaises(ModelError):test_connection(self.cfg,transport=lambda p:{'choices':[{'message':{'role':'assistant','content':'hello'}}]})
 def test_probe_accepts_correct_call_only(self):
  r=test_connection(self.cfg,transport=lambda p:{'choices':[{'message':{'tool_calls':[{'function':{'name':'connection_probe','arguments':'{}'}}]}}]});self.assertEqual(r['status'],'CONNECTED_TOOL_CALL_VERIFIED')
 def test_empty_key_not_ready(self):self.cfg['api_key']='';self.assertFalse(readiness(self.cfg)['ready'])

if __name__=='__main__':unittest.main(verbosity=2)
