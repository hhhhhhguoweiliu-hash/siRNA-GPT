"""Loopback-only local UI; no framework, no public deployment."""
from http.server import ThreadingHTTPServer,BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlparse,unquote
import html
import json,threading,mimetypes,webbrowser,argparse,os,io,csv,zipfile,datetime
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
 s.update({'api_ready':r['ready'],'api_connected':connected,'readiness':r,'model':c.get('model',''),'base_url':c.get('base_url',''),'version':'0.7-cloud','history':history(),'candidates':[{'candidate_id':r['candidate_id'],'guide':canonical(r),'source':r.get('source_tool')} for r in default_candidates()]})
 s['conversation']=CONVERSATION.snapshot()
 return s
def progress(event):
 with LOCK:STATE['events'].append(event)
def execute(payload):
 try:
  if payload.get('candidate_dataset_id'):
   from conversation import prepare_inputs
   candidates=prepare_inputs(payload)['candidates']
  elif payload.get('candidate_text','').strip():
   text=payload['candidate_text'].strip()
   if text.startswith('['):candidates=json.loads(text)
   else:candidates=list(csv.DictReader(io.StringIO(text),delimiter='\t' if '\t' in text.splitlines()[0] else ','))
   if not isinstance(candidates,list) or not 1<=len(candidates)<=20:raise ValueError('请提供1至20条候选记录')
  else:
   ids=payload.get('candidate_ids',[])
   available={r['candidate_id']:r for r in default_candidates()}
   if not ids or any(i not in available for i in ids):raise ValueError('请选择有效候选')
   candidates=[available[i] for i in ids]
  task={'gene':payload.get('gene','VEGFA'),'species':'Homo sapiens','state':payload.get('state','Hypoxia'),'top_n':payload.get('top_n',2),'request':str(payload.get('request',''))[:2000],'expression_dataset_id':payload.get('expression_dataset_id','builtin')}
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
  if path=='/api/data-source':
   from expression_data import builtin_receipt
   return self.send({'expression':builtin_receipt(),'candidates':{'source':'siDirect 2.0, computed 2026-10-16','count':9,'user_literature_candidates':False},'model_inference':'historical outputs; sequence checked before reuse','expression_changes_ranking':False})
  if path=='/api/expression-template':
   return self.send('ENTREZID\tapproved_symbol\tNor1\tNor2\tNor3\tNor4\tHyp1\tHyp2\tHyp3\tHyp4\n',kind='text/tab-separated-values; charset=utf-8')
  if path=='/api/status':return self.send(public_state())
  if path=='/api/development-evaluation':
   import paper_pilot
   return self.send(dict(paper_pilot.STATE))
  if path=='/api/development-evaluation-download':
   import paper_pilot
   identity=paper_pilot.STATE.get('run_id','')
   if not identity or paper_pilot.STATE.get('status') not in ('COMPLETE','STOPPED','FAILED','STOPPED_TIMEOUT','BLOCKED_ACCOUNT'):return self.send({'error':'评价未完成或本次服务中尚无结果'},409)
   directory=HOME/'evaluation_runs'/identity;memory=io.BytesIO()
   with zipfile.ZipFile(memory,'w',zipfile.ZIP_DEFLATED) as z:
    for p in directory.rglob('*'):
     if p.is_file():z.write(p,p.relative_to(directory))
   return self.send(memory.getvalue(),kind='application/zip')
  if path=='/api/conversation-record':return self.send(CONVERSATION.export_record())
  if path=='/api/runtime':
   from runtime_info import manifest
   return self.send(manifest())
  if path=='/library_ui.js':return self.send((HOME/'library_ui.js').read_bytes(),kind='application/javascript; charset=utf-8')
  if path in ('/api/library','/api/library-export') or path.startswith(('/library/','/api/library/original/')):
   from literature import get_library,chunks
   library=get_library()
   try:
    if path=='/api/library':return self.send(library.catalogue())
    if path=='/api/library-export':return self.send(library.export_bundle(),kind='application/zip')
    identity=path.rsplit('/',1)[-1];doc,original,parts=library.document(identity)
    if path.startswith('/api/library/original/'):
     return self.send(original.read_bytes(),kind='application/pdf' if original.suffix=='.pdf' else 'text/plain; charset=utf-8')
    esc=lambda value:html.escape(str(value),quote=True)
    body='<meta charset="utf-8"><title>'+esc(doc['title'])+'</title><style>body{max-width:900px;margin:30px auto;padding:0 20px;font:16px/1.7 system-ui}article{border-top:1px solid #ddd;padding:20px 0}pre{white-space:pre-wrap;overflow-wrap:anywhere;font:15px/1.7 system-ui}small{color:#536}article:target{background:#fff6da}</style>'
    body+='<h1>'+esc(doc['title'])+'</h1><p>'+esc(doc['source_label'])+'；来源类别按声明记录，不代表已通过科学审核。</p><p>文件SHA256：<code>'+esc(doc['sha256'])+'</code></p>'
    body+='<p><a href="/api/library/original/'+identity+'">打开原始文件</a>'
    if doc['source_url']:body+=' · <a href="'+esc(doc['source_url'])+'" rel="noopener noreferrer">原始来源入口</a>'
    body+='</p><p>'+esc(doc['source_note'])+'</p><p>仅提取文字，没有识别图片或图表。文本文件没有PDF页码。</p>'
    if doc['pages_without_text']:body+='<p>以下页没有可提取文字，未建立文字索引：'+esc(doc['pages_without_text'])+'</p>'
    for c in parts:
     label=('PDF第'+str(c['page'])+'页；' if c['page'] else '文本；')+'片段'+c['chunk_id']
     body+='<article id="'+esc(c['chunk_id'])+'"><h2>'+esc(label)+'</h2>'
     if c['page']:body+='<a href="/api/library/original/'+identity+'#page='+str(c['page'])+'">定位原PDF该页</a>'
     body+='<pre>'+html.escape(c['text'])+'</pre><small>片段SHA256：'+esc(c['sha256'])+'</small></article>'
    return self.send(body,kind='text/html; charset=utf-8')
   except ValueError as e:return self.send({'error':str(e)},400)
  if path in ('/api/library-demo','/api/library-demo-download'):
   import library_demo
   if path=='/api/library-demo':return self.send(dict(library_demo.STATE))
   try:return self.send(library_demo.export_zip(),kind='application/zip')
   except ValueError as e:return self.send({'error':str(e)},409)
  if path in ('/knowledge','/api/knowledge'):
   from knowledge import catalogue
   data=catalogue()
   if path=='/api/knowledge':return self.send(data)
   body='<meta charset="utf-8"><title>siRNA-GPT 项目资料</title><style>body{max-width:800px;margin:40px auto;padding:0 20px;font:16px/1.8 system-ui}article{padding:20px 0;border-bottom:1px solid #ddd}small{color:#666}</style><h1>本地项目说明卡</h1><p>版本 '+html.escape(data['version'])+'；待外部专家审核。它们说明当前实现，不替代原始论文或实验验证。</p>'
   for card in data['cards']:
    body+='<article id="'+html.escape(card['id'])+'"><h2>'+html.escape(card['title'])+'</h2><p>'+html.escape(card['text'])+'</p><small>依据：'+html.escape(card['basis'])+'</small>'
    if card.get('original_url'):body+='<p><a href="'+html.escape(card['original_url'],quote=True)+'">原始文献入口</a></p>'
    body+='</article>'
   return self.send(body,kind='text/html; charset=utf-8')
  if path=='/api/candidate-template':return self.send('candidate_id\tguide_core19_5to3\tsource\n',kind='text/tab-separated-values; charset=utf-8')
  if path in ('/','/index.html'):return self.send((HOME/'index.html').read_bytes(),kind='text/html; charset=utf-8')
  if path.startswith('/runs/'):
   target=(HOME/path.lstrip('/')).resolve();allowed=(HOME/'runs').resolve()
   if target.name=='download.zip' and allowed in target.parent.parents and (target.parent/'result.json').is_file():
    memory=io.BytesIO()
    with zipfile.ZipFile(memory,'w',zipfile.ZIP_DEFLATED) as z:
     for p in target.parent.rglob('*'):
      if p.is_file() and p.suffix in ('.json','.jsonl','.tsv','.html','.txt','.log','.gz'):z.write(p,p.relative_to(target.parent))
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
   maximum=34000000 if self.path in ('/api/library-upload','/api/library-import') else 16000000 if self.path=='/api/expression-upload' else 50000
   if n<0 or n>maximum:return self.send({'error':'Input too large'},413)
   data=json.loads(self.rfile.read(n).decode('utf-8'))
   if not isinstance(data,dict):return self.send({'error':'Request must be a JSON object'},400)
   if self.path in ('/api/library-upload','/api/library-import','/api/library-search','/api/library-rebuild'):
    from literature import get_library,decode_upload
    try:
     library=get_library()
     if self.path=='/api/library-search':return self.send(library.search(data.get('query','')))
     with LOCK:
      if STATE['running'] or STATE['checking_connection'] or CONVERSATION.busy:return self.send({'error':'请等待当前任务结束，再更改文库。'},409)
      STATE['running']=True
     try:
      if self.path=='/api/library-upload':result=library.import_document(decode_upload(data.get('content_base64')),data.get('filename',''),data)
      elif self.path=='/api/library-import':result=library.import_bundle(decode_upload(data.get('content_base64'),24000000))
      else:result={'version':library.rebuild(),'status':'REBUILT'}
      return self.send(result)
     finally:
      with LOCK:STATE['running']=False
    except ValueError as e:return self.send({'error':str(e)},400)
   if self.path=='/api/library-demo-start':
    import library_demo
    with LOCK:
     if STATE['running'] or STATE['checking_connection'] or CONVERSATION.busy:return self.send({'error':'请等待当前任务结束。'},409)
     if data.get('confirm_api_usage') is not True:return self.send({'error':'请先确认本次最多2题演示会调用模型并产生用量。'},400)
     demo_mode=data.get('mode','two_question')
     if demo_mode not in ('two_question','day7_regression'):return self.send({'error':'文库演示模式无效。'},400)
     if library_demo.STATE.get('status')=='RUNNING':return self.send({'error':'文库演示正在运行。'},409)
     identity='library_demo_'+datetime.datetime.now().strftime('%Y%m%d_%H%M%S')+'_'+__import__('uuid').uuid4().hex[:6]
     expected_questions=1 if demo_mode=='day7_regression' else 2
     STATE['running']=True;library_demo.STATE.update(status='RUNNING',run_id=identity,completed=0,total=expected_questions)
    def demonstrate_once():
     try:library_demo.run(config,identity,demo_mode)
     except Exception:
      # A setup error must release both gates; details may contain config secrets.
      library_demo.STATE.update(status='FAILED_SETUP',run_id=identity,error='演示初始化未完成，请检查服务记录；未自动重试。')
     finally:
      with LOCK:STATE['running']=False
    threading.Thread(target=demonstrate_once,daemon=True).start()
    return self.send({'started':True,'run_id':identity,'expected_questions':expected_questions},202)
   if self.path=='/api/expression-upload':
    from expression_data import upload
    try:return self.send(upload(data.get('text'),data.get('label',''),data.get('confirmed')))
    except ValueError as e:return self.send({'error':str(e)},400)
   if self.path=='/api/stop':return self.send(CONVERSATION.request_stop())
   if self.path=='/api/development-evaluation-stop':
    import paper_pilot
    paper_pilot.STOP.set();return self.send({'message':'当前案例结束后停止，不再启动下一案例'})
   if self.path=='/api/development-evaluation-start':
    import paper_pilot
    with LOCK:
     if STATE['running'] or STATE['checking_connection'] or CONVERSATION.busy:return self.send({'error':'请等待当前任务结束'},409)
     if paper_pilot.STATE.get('status')=='RUNNING':return self.send({'error':'评价已经运行中'},409)
     if data.get('confirm_api_usage') is not True:return self.send({'error':'需先确认本次诊断或开发评价会调用模型并产生用量'},400)
     evaluation_mode=data.get('mode','batch')
     if evaluation_mode not in ('batch','diagnostic'):return self.send({'error':'评价模式无效'},400)
     expected_records=1 if evaluation_mode=='diagnostic' else 54
     identity=('diag_' if evaluation_mode=='diagnostic' else 'dev_')+datetime.datetime.now().strftime('%Y%m%d_%H%M%S')+'_'+__import__('uuid').uuid4().hex[:6]
     STATE['running']=True
     paper_pilot.STATE.update(status='RUNNING',run_id=identity,completed=0,total=expected_records)
    def evaluate_once():
     try:paper_pilot.run(config,identity,mode=evaluation_mode)
     finally:
      with LOCK:STATE['running']=False
    threading.Thread(target=evaluate_once,daemon=True).start()
    return self.send({'started':True,'run_id':identity,'expected_records':expected_records},202)
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
 save_json(HOME/'server.local.json',{'url':url,'pid':os.getpid(),'version':'0.7-cloud'})
 print('RPE siRNA Agent v0.3.2: '+url,flush=True)
 if args.open:webbrowser.open(url)
 try:server.serve_forever()
 except KeyboardInterrupt:pass
 finally:server.server_close()
