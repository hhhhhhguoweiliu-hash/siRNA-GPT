import json,tempfile,unittest,zipfile,io,base64
from pathlib import Path
from unittest.mock import patch
import paper_pilot
from evaluate import run_case
from core import config

class PilotTests(unittest.TestCase):
 def test_evaluation_web_endpoints_require_auth_and_explicit_usage_ack(self):
  import os,cloud
  from test_cloud import call
  with patch.dict(os.environ,{'WEB_PASSWORD':'TEST_WEB_PASSWORD_123456789','RENDER_EXTERNAL_HOSTNAME':'sirna-test.onrender.com','RENDER_EXTERNAL_URL':'https://sirna-test.onrender.com'}),patch.dict(cloud.local.STATE,{'running':False,'checking_connection':False}),patch.object(cloud.local.CONVERSATION,'busy',False):
   self.assertEqual(call('/api/development-evaluation',auth=False)[0],401)
   self.assertEqual(call('/api/development-evaluation')[0],200)
   self.assertEqual(call('/api/development-evaluation-start','POST',{'confirm_api_usage':False})[0],400)
   self.assertEqual(call('/api/development-evaluation-start','POST',{'confirm_api_usage':True},origin='https://foreign.example')[0],403)
   with patch.object(cloud.local.threading,'Thread') as thread:
    code,body,_=call('/api/development-evaluation-start','POST',{'confirm_api_usage':True})
    self.assertEqual(code,202);self.assertEqual(json.loads(body)['expected_records'],54)
    thread.return_value.start.assert_called_once()
 def test_common_structured_target_passes_to_all_preparation(self):
  cfg=config();seen=[]
  case={'id':'unsupported','request':'KRAS only','task':{'gene':'KRAS'},'preset':'full'}
  run_case('llm',case,cfg,Path(tempfile.gettempdir())/'pilot_input_test',lambda p:(seen.append(p),{'choices':[{'message':{'content':'TEST ONLY'}}]})[1])
  self.assertEqual(json.loads(seen[0]['messages'][1]['content'])['input']['task']['gene'],'KRAS')
 def test_explicit_pilot_archives_all_answers_and_runs_once(self):
  with tempfile.TemporaryDirectory() as root:
   root=Path(root);(root/'evaluation_cases.example.json').write_text(json.dumps({'review_status':'TEST ONLY','cases':[{'id':'x','request':'test'}]}),encoding='utf-8')
   logs=[]
   def fake(group,case,cfg,path):
    return {'group':group,'case_id':case['id'],'status':'TEST','answer':'secret_fake','usage':[],'tool_calls':0,'seconds':0}
   with patch.object(paper_pilot,'HOME',root),patch.object(paper_pilot,'log',lambda k,v:logs.append((k,v))),patch('evaluate.run_case',fake):
    paper_pilot.run(lambda:{'api_key':'secret_fake','model':'TEST'},'test');paper_pilot.run(lambda:{},'test')
   self.assertEqual(len([x for x in logs if x[0]=='BEGIN']),1)
   chunks=[x[1]['data'] for x in logs if x[0]=='CHUNK'];raw=base64.b64decode(''.join(chunks))
   with zipfile.ZipFile(io.BytesIO(raw)) as archive:
    results=json.loads(archive.read('results.json'));self.assertEqual(len(results),9)
    self.assertNotIn('secret_fake',json.dumps(results));self.assertIn('blind_answers.tsv',archive.namelist())
 def test_invalid_run_id_rejected(self):
  with self.assertRaises(ValueError):paper_pilot.run(lambda:{},'../escape')

if __name__=='__main__':unittest.main()
