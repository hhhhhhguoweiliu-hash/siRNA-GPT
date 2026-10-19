"""Cloud HTTP/auth and actual imported-tool workflow checks, without network sockets."""
import base64, io, json, os, time, unittest
from unittest.mock import patch
import cloud

def call(path='/',method='GET',body=None,auth=True,origin=None,host='sirna-test.onrender.com'):
    raw=json.dumps(body).encode() if body is not None else b''
    e={'PATH_INFO':path,'REQUEST_METHOD':method,'HTTP_HOST':host,'wsgi.input':io.BytesIO(raw),'wsgi.url_scheme':'https','CONTENT_LENGTH':str(len(raw)),'HTTP_X_RPE_LOCAL':'1'}
    if auth:e['HTTP_AUTHORIZATION']='Basic '+base64.b64encode(b'research:TEST_WEB_PASSWORD_123456789').decode()
    if origin:e['HTTP_ORIGIN']=origin
    status=[];out=b''.join(cloud.application(e,lambda s,h:status.append((int(s.split()[0]),dict(h)))))
    return status[0][0],out,status[0][1]

class CloudTests(unittest.TestCase):
 def setUp(self):
  self.env=patch.dict(os.environ,{'WEB_PASSWORD':'TEST_WEB_PASSWORD_123456789','ARK_API_KEY':'TEST_API_SECRET_ONLY','ARK_MODEL':'doubao-test-model','RENDER_EXTERNAL_HOSTNAME':'sirna-test.onrender.com','RENDER_EXTERNAL_URL':'https://sirna-test.onrender.com'})
  self.env.start()
 def tearDown(self):self.env.stop()
 def test_health_is_public_and_has_no_secrets(self):
  status,body,_=call('/healthz',auth=False);self.assertEqual(status,200);self.assertNotIn(b'SECRET',body)
 def test_page_needs_password(self):
  status,_,headers=call(auth=False);self.assertEqual(status,401);self.assertIn('WWW-Authenticate',headers)
 def test_wrong_password_does_not_pass(self):self.assertFalse(cloud.authorized('Basic '+base64.b64encode(b'research:wrong').decode()))
 def test_nonascii_password_does_not_crash(self):self.assertFalse(cloud.authorized('Basic '+base64.b64encode('research:测试'.encode()).decode()))
 def test_short_server_password_fails_closed(self):
  with patch.dict(os.environ,{'WEB_PASSWORD':'short'}):self.assertEqual(call()[0],503)
 def test_authenticated_home(self):self.assertEqual(call()[0],200)
 def test_wrong_host_rejected(self):self.assertEqual(call(host='foreign.example')[0],403)
 def test_foreign_origin_rejected(self):self.assertEqual(call('/api/message','POST',{},origin='https://foreign.example')[0],403)
 def test_live_tools_not_silently_substituted(self):self.assertEqual(call('/api/run','POST',{'tool_mode':'live','mode':'workflow'})[0],409)
 def test_cloud_config_environment_wins_and_no_secret_echo(self):
  self.assertEqual(cloud.cloud_config()['model'],'doubao-test-model')
  status,body,_=call('/api/status');self.assertEqual(status,200);self.assertNotIn(b'TEST_API_SECRET_ONLY',body);self.assertNotIn(b'TEST_WEB_PASSWORD',body)
 def test_website_cannot_rewrite_server_secrets(self):self.assertEqual(call('/api/config','POST',{'api_key':'overwrite'})[0],409)
 def test_authenticated_real_imported_workflow(self):
  payload={'mode':'workflow','tool_mode':'imported','candidate_ids':[x['candidate_id'] for x in cloud.local.default_candidates()],'state':'Hypoxia','top_n':2}
  status,_,_=call('/api/run','POST',payload,origin='https://sirna-test.onrender.com');self.assertEqual(status,202)
  deadline=time.monotonic()+20
  while cloud.local.public_state()['running'] and time.monotonic()<deadline:time.sleep(.05)
  s=cloud.local.public_state();self.assertEqual(s['last_result']['status'],'COMPLETE')
  status,body,_=call('/runs/'+s['run_id']+'/report.json');self.assertEqual(status,200)
  r=json.loads(body);self.assertEqual(r['tool_mode'],'imported');self.assertEqual(len(r['rows']),9)
 def test_path_escape_is_rejected(self):self.assertEqual(call('/runs/../../config.example.json')[0],404)

if __name__=='__main__':unittest.main(verbosity=2)
