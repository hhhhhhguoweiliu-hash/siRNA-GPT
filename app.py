"""Loopback-only local UI; no framework, no public deployment."""
from http.server import ThreadingHTTPServer,BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlparse,unquote
import json,threading,mimetypes,webbrowser,argparse,os,io,csv,zipfile
from core import HOME,Session,config,default_candidates,canonical,save_json
from model_client import readiness,extract_model,test_connection,client_fingerprint,ModelError,ARK_BASE_URL
from conversation import Conversation

LOCK=threading.Lock();STATE={'running':False,'events':[],'last_result':None,'run_id':None,'checking_connection':False,'connection':{'status':'NOT_TESTED'}}
CONNECTION_FINGERPRINT=None
CONVERSATION=Conversation()
def history():
 out=[]
 for p in sorted((HOME/'runs').glob('*/report.json'),reverse=True)[:12]:
  try:
   r=json.loads(p.read_text(encoding='utf-8'))
   out.append({'run_id':p.parent.name,'mode':r.get('mode'),'selected':r.get('selected_for_review',[]),'agent_status':r.get('agent_status',''),'tool_mode':r.get('tool_mode')})
  except (OSError,ValueError):pass
 return out
def public_state():
 c=config()
 with LOCK:s=dict(STATE);s['events']=list(STATE['events'])
 r=readiness(c)
 connected=s['connection'].get('status')=='CONNECTED_TOOL_CALL_VERIFIED' and CONNECTION_FINGERPRINT==client_fingerprint(c)
 s.update({'api_ready':r['ready'],'api_connected':connected,'readiness':r,'model':c.get('model',''),'base_url':c.get('base_url',''),'version':'0.3.2','history':history(),'candidates':[{'candidate_id':r['candidate_id'],'guide':canonical(r),'source':r.get('source_tool')} for r in default_candidates()]})
 s['conversation']=CONVERSATION.snapshot()
 return s
def progress(event):
 with LOCK:STATE['events'].append(event)
def execute(payload):
 try:
  if payload.get('candidate_text','').strip():
   text=payload['candidate_text'].strip()
   if text.startswith('['):candidates=json.loads(text)
   else:candidates=list(csv.DictReader(io.StringIO(text),delimiter='\t' if '\t' in text.splitlines()[0] else ','))
   if not isinstance(candidates,list) or not 1<=len(candidates)<=20:raise ValueError('请提供1至20条候选记录')
  else:
   ids=payload.get('candidate_ids',[])
   available={r['candidate_id']:r for r in default_candidates()}
   if not ids or any(i not in available for i in ids):raise ValueError('请选择有效候选')
   candidates=[available[i] for i in ids]
  task={'gene':payload.get('gene','VEGFA'),'species':'Homo sapiens','state':payload.get('state','Hypoxia'),'top_n':payload.get('top_n',2),'request':str(payload.get('request',''))[:2000]}
  s=Session(candidates=candidates,task=task,mode=payload.get('mode','agent'),tool_mode=payload.get('tool_mode','live'),event=progress)
  with LOCK:STATE['run_id']=s.id
  result=s.run()
  with LOCK:STATE['last_result']=result
 except Exception as e:
  with LOCK:STATE['last_result']={'status':'FAILED','message':str(e)}
 finally:
  with LOCK:STATE['running']=False

def check_connection(check_research=False):
 global CONNECTION_FINGERPRINT
 c=config()
 try:
  result=test_connection(c);CONNECTION_FINGERPRINT=client_fingerprint(c)
 except Exception as e:result={'status':'FAILED','message':str(e),**(e.diagnostics() if isinstance(e,ModelError) else {'code':'MODEL_ERROR'})}
 save_json(HOME/'connection.last.json',result)
 if check_research:
  from startup_checks import research_checks
  checks=research_checks(c,result.get('status')=='CONNECTED_TOOL_CALL_VERIFIED')
  with LOCK:STATE['research_connection']=checks
 with LOCK:STATE.update(checking_connection=False,connection=result)

class Handler(BaseHTTPRequestHandler):
 def log_message(self,*args):pass
 def send(self,body,status=200,kind='application/json; charset=utf-8'):
  if isinstance(body,(dict,list)):body=json.dumps(body,ensure_ascii=False).encode('utf-8')
  elif isinstance(body,str):body=body.encode('utf-8')
  self.send_response(status);self.send_header('Content-Type',kind);self.send_header('Content-Length',str(len(body)))
  self.send_header('Cache-Control','no-store');self.send_header('X-Content-Type-Options','nosniff');self.end_headers();self.wfile.write(body)
 def valid_host(self):
  return self.headers.get('Host') in ('127.0.0.1:'+str(self.server.server_port),'localhost:'+str(self.server.server_port))
 def do_GET(self):
  if not self.valid_host():return self.send({'error':'Invalid host'},403)
  path=unquote(urlparse(self.path).path)
  if path=='/api/status':return self.send(public_state())
  if path=='/api/conversation-record':return self.send(CONVERSATION.snapshot())
  if path=='/api/candidate-template':return self.send('candidate_id\tguide_core19_5to3\tsource\n',kind='text/tab-separated-values; charset=utf-8')
  if path in ('/','/index.html'):return self.send((HOME/'index.html').read_bytes(),kind='text/html; charset=utf-8')
  if path.startswith('/runs/'):
   target=(HOME/path.lstrip('/')).resolve();allowed=(HOME/'runs').resolve()
   if target.name=='download.zip' and allowed in target.parent.parents and (target.parent/'result.json').is_file():
    memory=io.BytesIO()
    with zipfile.ZipFile(memory,'w',zipfile.ZIP_DEFLATED) as z:
     for p in target.parent.iterdir():
      if p.is_file() and p.suffix in ('.json','.jsonl','.tsv','.html','.txt','.log'):z.write(p,p.name)
    return self.send(memory.getvalue(),kind='application/zip')
   if allowed not in target.parents or not target.is_file():return self.send({'error':'Not found'},404)
   types={'.tsv':'text/tab-separated-values; charset=utf-8','.json':'application/json; charset=utf-8','.jsonl':'text/plain; charset=utf-8','.html':'text/html; charset=utf-8','.txt':'text/plain; charset=utf-8'}
   return self.send(target.read_bytes(),kind=types.get(target.suffix,'application/octet-stream'))
  return self.send({'error':'Not found'},404)
 def do_POST(self):
  if not self.valid_host() or self.headers.get('X-RPE-Local')!='1':return self.send({'error':'Local request required'},403)
  origin=self.headers.get('Origin')
  if origin and origin not in ('http://127.0.0.1:'+str(self.server.server_port),'http://localhost:'+str(self.server.server_port)):return self.send({'error':'Invalid origin'},403)
  try:
   n=int(self.headers.get('Content-Length','0'))
   if n>50000:return self.send({'error':'Input too large'},413)
   data=json.loads(self.rfile.read(n).decode('utf-8'))
   if not isinstance(data,dict):return self.send({'error':'Request must be a JSON object'},400)
   if self.path in ('/api/message','/api/action'):
    with LOCK:
     if STATE['running'] or STATE['checking_connection'] or CONVERSATION.busy:return self.send({'error':'已有任务或连接检查正在运行'},409)
     try:
      if self.path=='/api/message':CONVERSATION.submit(data)
      else:CONVERSATION.action(data.get('action'),data.get('plan_id'))
     except Exception as e:return self.send({'error':str(e)},400)
    return self.send({'accepted':True},202)
   if self.path=='/api/config':
    with LOCK:
     if STATE['running'] or STATE['checking_connection'] or CONVERSATION.busy:return self.send({'error':'任务或连接检查运行中，暂不能改配置'},409)
    c={'provider':'doubao','base_url':ARK_BASE_URL,'model':extract_model(data.get('model',''))}
    if not c['model']:return self.send({'error':'请填写模型ID或粘贴包含model字段的调用示例'},400)
    local=HOME/'config.local.json'
    existing=json.loads(local.read_text(encoding='utf-8-sig')) if local.exists() else {}
    existing.update(c)
    if str(data.get('api_key','')).strip():existing['api_key']=str(data['api_key']).strip()
    save_json(local,existing)
    with LOCK:STATE['connection']={'status':'NOT_TESTED'}
    return self.send({'saved':True,'api_key_returned':False})
   if self.path=='/api/test-connection':
    with LOCK:
     if STATE['running'] or STATE['checking_connection'] or CONVERSATION.busy:return self.send({'error':'已有任务运行中'},409)
     STATE.update(checking_connection=True,connection={'status':'CHECKING'})
    threading.Thread(target=check_connection,kwargs={'check_research':True},daemon=True).start()
    return self.send({'started':True},202)
   if self.path=='/api/run':
    if data.get('mode') not in ('agent','workflow') or data.get('tool_mode') not in ('live','imported'):return self.send({'error':'不支持的运行模式'},400)
    with LOCK:
     if STATE['running'] or STATE['checking_connection'] or CONVERSATION.busy:return self.send({'error':'已有任务或连接检查运行中'},409)
     STATE.update({'running':True,'events':[],'last_result':None,'run_id':None})
    threading.Thread(target=execute,args=(data,),daemon=True).start()
    return self.send({'started':True},202)
   return self.send({'error':'Not found'},404)
  except ModelError as e:return self.send({'error':str(e),'code':e.code},400)
  except Exception:return self.send({'error':'请求无法处理，请检查输入格式'},400)

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--port',type=int,default=8765);p.add_argument('--open',action='store_true');args=p.parse_args()
 server=None
 for port in range(args.port,args.port+20):
  try:server=ThreadingHTTPServer(('127.0.0.1',port),Handler);break
  except OSError:continue
 if server is None:raise SystemExit('No available localhost port. See README.')
 url='http://127.0.0.1:'+str(server.server_port)
 save_json(HOME/'server.local.json',{'url':url,'pid':os.getpid(),'version':'0.3.2'})
 print('RPE siRNA Agent v0.3.2: '+url,flush=True)
 if args.open:webbrowser.open(url)
 try:server.serve_forever()
 except KeyboardInterrupt:pass
 finally:server.server_close()
