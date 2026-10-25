"""Full loop with an explicitly fake Responses endpoint; never evidence of a real API run."""
import unittest,json,io,uuid
from unittest.mock import patch
from core import HOME,Session,config,TOOLS

class Response(io.BytesIO):
 def __init__(self,obj):super().__init__(json.dumps(obj).encode('utf-8'));self.headers={'x-request-id':'TEST_ONLY'}
class IntegrationTests(unittest.TestCase):
 def test_responses_adapter_full_tool_loop(self):
  cfg=config();cfg.update(api_key='TEST_SECRET_ONLY',model='doubao-seed-2-1-pro-260915',api_mode='responses',provider='doubao')
  root=HOME/'_test_runs'/uuid.uuid4().hex;calls=[]
  def fake(req,timeout):
   body=json.loads(req.data);calls.append(body)
   self.assertTrue(req.full_url.endswith('/responses'));self.assertNotIn('messages',body)
   # Regression: Ark rejects a mixed multi-turn input list if type is omitted.
   self.assertTrue(all(x.get('type') in ('message','function_call','function_call_output') for x in body['input']))
   outputs=[x for x in body['input'] if x.get('type')=='function_call_output']
   n=len(outputs)
   if n<6:
    name=TOOLS[n][0]
    out=[{'type':'function_call','call_id':'call_'+str(n),'name':name,'arguments':'{}'}]
   else:out=[{'type':'message','role':'assistant','content':[{'type':'output_text','text':'TEST_ONLY：报告已按工具证据生成。'}]}]
   return Response({'id':'response_'+str(n),'status':'completed','output':out,'usage':{'input_tokens':3,'output_tokens':2,'total_tokens':5}})
  with patch('model_client.urllib.request.urlopen',side_effect=fake):
   session=Session(mode='agent',tool_mode='imported',cfg=cfg,run_root=root);result=session.run()
  self.assertEqual(result['status'],'COMPLETE');self.assertEqual(len(calls),7)
  self.assertEqual(len([x for x in calls[-1]['input'] if x.get('type')=='function_call_output']),6)
  report=json.loads((session.path/'report.json').read_text(encoding='utf-8'))
  self.assertTrue(report['model_summary'].startswith('TEST_ONLY'))
  self.assertIn('Model interpretation',(session.path/'report.html').read_text(encoding='utf-8'))
  self.assertNotIn('TEST_SECRET_ONLY',(session.path/'model_transcript.json').read_text(encoding='utf-8'))
if __name__=='__main__':unittest.main(verbosity=2)
