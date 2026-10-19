"""In-memory HTTP boundary tests, requiring no network permission."""
import unittest,io,json,time
from types import SimpleNamespace
import app

class Wire:
 def __init__(self,request):self.request=io.BytesIO(request);self.output=bytearray()
 def makefile(self,*args):return self.request
 def sendall(self,data):self.output.extend(data)
def request(method,path,body=None,headers=None):
 data=json.dumps(body).encode('utf-8') if body is not None else b''
 h={'Host':'127.0.0.1:8765','Content-Length':str(len(data)),'X-RPE-Local':'1',**(headers or {})}
 raw=(method+' '+path+' HTTP/1.0\r\n'+''.join(k+': '+v+'\r\n' for k,v in h.items())+'\r\n').encode()+data
 wire=Wire(raw);app.Handler(wire,('127.0.0.1',12345),SimpleNamespace(server_port=8765))
 head,out=bytes(wire.output).split(b'\r\n\r\n',1)
 return int(head.split()[1]),out
class HTTPTests(unittest.TestCase):
 def test_home(self):
  status,body=request('GET','/');self.assertEqual(status,200);self.assertIn(b'Auto',body)
 def test_status_hides_secrets(self):
  status,body=request('GET','/api/status');r=json.loads(body);self.assertEqual(len(r['candidates']),9);self.assertNotIn('api_key',r)
 def test_foreign_origin_rejected(self):self.assertEqual(request('POST','/api/run',{},headers={'Origin':'https://foreign.example'})[0],403)
 def test_foreign_host_rejected(self):self.assertEqual(request('GET','/api/status',headers={'Host':'foreign.example'})[0],403)
 def test_path_escape_rejected(self):self.assertEqual(request('GET','/runs/../../config.example.json')[0],404)
 def test_run_through_http_boundary(self):
  status,_=request('POST','/api/run',{'mode':'workflow','tool_mode':'imported','candidate_ids':[x['candidate_id'] for x in app.default_candidates()],'state':'Hypoxia','top_n':2})
  self.assertEqual(status,202)
  deadline=time.monotonic()+20
  while app.public_state()['running'] and time.monotonic()<deadline:time.sleep(.1)
  s=app.public_state();self.assertEqual(s['last_result']['status'],'COMPLETE')
  status,body=request('GET','/runs/'+s['run_id']+'/report.html');self.assertEqual(status,200);self.assertIn('未调用大模型'.encode(),body)
if __name__=='__main__':unittest.main(verbosity=2)
