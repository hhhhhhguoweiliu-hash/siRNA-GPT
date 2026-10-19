"""Doubao/Ark adapter. Credentials remain local; no silent model or workflow fallback."""
import json,os,re,time,socket,urllib.request,urllib.error,hashlib,datetime
from pathlib import Path

ARK_BASE_URL='https://ark.cn-beijing.volces.com/api/v3'
DOC_URL='https://docs.volcengine.com/docs/ark/function-calling?lang=zh'
class ModelError(Exception):
 def __init__(self,message,code='MODEL_ERROR',provider_code='',provider_message='',request_id='',http_status=None):
  super().__init__(message);self.code=code;self.provider_code=provider_code
  self.provider_message=provider_message;self.request_id=request_id;self.http_status=http_status
 def diagnostics(self):
  return {'code':self.code,'provider_code':self.provider_code,'provider_message':self.provider_message,'request_id':self.request_id,'http_status':self.http_status}

def account_blocked(diagnostics):
 """Terminal account/billing/auth errors are not transient request throttling."""
 code=str(diagnostics.get('provider_code',''))
 return diagnostics.get('http_status') in (401,402) or code in {
  'SetLimitExceeded','AccountOverdueError','OperationDenied.ServiceOverdue',
  'OperationDenied.ServiceNotOpen','ModelNotOpen','InvalidAccountStatus','AuthenticationError'}

def extract_model(value):
 text=str(value or '').strip()
 if not text:return ''
 # Paste either the exact ID, JSON/Curl body or Python call example. Never log the pasted example.
 for pattern in [r'["\']model["\']\s*:\s*["\']([^"\']+)["\']',r'\bmodel\s*=\s*["\']([^"\']+)["\']']:
  m=re.search(pattern,text)
  if m:text=m.group(1).strip();break
 if len(text)>180 or re.search(r'[\s\x00-\x1f"\'<>]',text):raise ModelError('请填写调用示例中model字段的值，不要填写整段不含model字段的代码。','MODEL_ID_INVALID')
 if text.isdigit():raise ModelError('这是纯数字ID，尚不能识别为方舟模型ID。请复制控制台调用示例中的model值，通常以doubao-或ep-开头。','MODEL_ID_INVALID')
 if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._:/-]*',text):raise ModelError('模型ID含不支持的字符。','MODEL_ID_INVALID')
 return text

def apply_environment(cfg):
 c=dict(cfg);provider=c.get('provider','doubao')
 names=[('ARK_API_KEY','api_key'),('DOUBAO_API_KEY','api_key'),('ARK_BASE_URL','base_url'),('ARK_MODEL','model'),('ARK_ENDPOINT_ID','model'),('DOUBAO_MODEL','model')]
 if provider!='doubao':names=[('OPENAI_API_KEY','api_key'),('OPENAI_BASE_URL','base_url'),('OPENAI_MODEL','model')]
 # Explicit local config wins; the environment fills missing fields.
 for env,key in names:
  if not c.get(key) and os.environ.get(env):c[key]=os.environ[env]
 if provider=='doubao' and not c.get('base_url'):c['base_url']=ARK_BASE_URL
 c['provider']=provider
 return c

def endpoint(cfg):
 base=str(cfg.get('base_url','')).strip().rstrip('/')
 if base.endswith('/chat/completions'):base=base[:-len('/chat/completions')]
 if base.endswith('/responses'):base=base[:-len('/responses')]
 if not base.startswith('https://') and not base.startswith(('http://127.0.0.1:','http://localhost:')):raise ModelError('远程API地址需使用HTTPS。','CONFIG_INVALID')
 if cfg.get('provider')=='doubao' and not base.startswith(ARK_BASE_URL):raise ModelError('豆包标准API模式使用方舟官方地址；其他兼容接口请明确切换服务商。','CONFIG_INVALID')
 return base+('/responses' if cfg.get('api_mode')=='responses' else '/chat/completions')

def responses_payload(payload):
 out={k:v for k,v in payload.items() if k not in ('messages','tools','tool_choice','max_tokens')}
 out['max_output_tokens']=payload.get('max_tokens',1800)
 out['input']=[];instructions=[]
 for message in payload.get('messages',[]):
  role=message.get('role')
  if role=='system':instructions.append(message.get('content') or '')
  elif role=='tool':out['input'].append({'type':'function_call_output','call_id':message['tool_call_id'],'output':message.get('content') or ''})
  else:
   if message.get('content'):
    out['input'].append({'type':'message','role':role,'content':[{'type':'output_text' if role=='assistant' else 'input_text','text':message['content']}]})
   for call in message.get('tool_calls') or []:
    out['input'].append({'type':'function_call','call_id':call['id'],'name':call['function']['name'],'arguments':call['function']['arguments']})
 if instructions:out['instructions']='\n'.join(instructions)
 if payload.get('tools'):out['tools']=[{'type':'function',**tool['function']} if tool.get('type')=='function' else dict(tool) for tool in payload['tools']]
 if 'tool_choice' in payload:
  choice=payload['tool_choice']
  out['tool_choice']=({'type':'function','name':choice['function']['name']} if choice.get('type')=='function' and 'function' in choice else choice) if isinstance(choice,dict) else choice
 # v0.2 uses stateless history and disabled thinking; no hidden reasoning state is omitted.
 if out.get('thinking',{}).get('type')=='enabled':raise ModelError('当前Responses适配仅验证关闭深度思考的无状态历史传递。','CONFIG_INVALID')
 return out

def normalize_responses(data):
 if data.get('status')=='incomplete':raise ModelError('Responses输出不完整，本轮未执行工具指令。','OUTPUT_TRUNCATED')
 if data.get('status') in ('failed','cancelled'):raise ModelError('Responses任务失败或取消。','RESPONSE_INVALID')
 calls=[];text=[];sources=[];searches=[]
 for item in data.get('output',[]):
  if item.get('type')=='function_call':
   calls.append({'id':item.get('call_id') or item.get('id'),'type':'function','function':{'name':item.get('name'),'arguments':item.get('arguments','{}')}})
  elif item.get('type')=='web_search_call':searches.append({'status':item.get('status'),'action':item.get('action',{})})
  elif item.get('type')=='message':
   for c in item.get('content',[]):
    if c.get('type')=='output_text':
     text.append(c.get('text',''))
     for a in c.get('annotations',[]):
      if a.get('type')=='url_citation' and isinstance(a.get('url'),str):
       from urllib.parse import urlsplit
       u=urlsplit(a['url'])
       if u.scheme=='https' and u.hostname and not u.username and not u.password and a['url'] not in [s['url'] for s in sources]:
        sources.append({'title':a.get('title') or u.hostname,'url':a['url'],'summary':a.get('summary','')[:1500]})
 if not calls and not text:raise ModelError('Responses未返回文本或函数调用。','RESPONSE_INVALID')
 usage=data.get('usage',{})
 return {'id':data.get('id'),'model':data.get('model'),'choices':[{'finish_reason':'tool_calls' if calls else 'stop','message':{'role':'assistant','content':'\n'.join(text) or None,**({'tool_calls':calls} if calls else {})}}],'usage':usage,'sources':sources,'web_search_calls':searches}

def readiness(cfg):
 result={'key_present':bool(cfg.get('api_key')),'model_present':bool(cfg.get('model')),'model_valid':False,'ready':False,'message':'请先填写模型ID'}
 try:
  m=extract_model(cfg.get('model'));result['model_valid']=bool(m)
  if not result['key_present']:result['message']='未检测到密钥：设置ARK_API_KEY或在本机填写'
  elif not m:result['message']='已检测到密钥，还需模型ID或ep-接入点ID'
  else:endpoint(cfg);result.update(ready=True,message='配置齐全，尚需连接检查')
 except ModelError as e:result['message']=str(e)
 return result

def client_fingerprint(cfg):
 # The key hash is used only in memory to invalidate stale connection results, never returned or saved.
 return (cfg.get('base_url'),cfg.get('model'),hashlib.sha256(str(cfg.get('api_key','')).encode()).hexdigest())

def redact(text,key=''):
 s=str(text)
 if key:s=s.replace(key,'[REDACTED]')
 s=re.sub(r'(?i)(Bearer\s+)[^\s"\']+',r'\1[REDACTED]',s)
 return s[:500]

def provider_http_error(error,key):
 """Keep the provider's actual explanation and request ID; never infer an exact cause from 403 alone."""
 try:body=json.loads(error.read(12000).decode('utf-8','replace'))
 except (ValueError,OSError):body={}
 if not isinstance(body,dict):body={}
 detail=body.get('error',{})
 if not isinstance(detail,dict):detail={}
 code=redact(detail.get('code') or body.get('code') or str(error.code),key)
 message=redact(detail.get('message') or body.get('message') or '',key)
 headers=error.headers or {}
 rid=redact(headers.get('x-request-id') or headers.get('X-Request-Id') or headers.get('x-tt-logid') or body.get('request_id') or detail.get('request_id') or '',key)
 hints={400:'请求参数未被接受',401:'鉴权失败，请核对密钥',403:'请求被拒绝，具体原因需看服务端说明',404:'资源不存在或不可访问',429:'请求限流或配额受限',402:'计费状态异常'}
 if code=='AccessDenied':hint='当前凭证无权访问所请求的资源，请核对账号、项目授权和白名单'
 elif code in ('OperationDenied.ServiceNotOpen','ModelNotOpen'):hint='对应模型服务尚未开通，请在方舟控制台确认'
 elif code in ('AccountOverdueError','OperationDenied.ServiceOverdue'):hint='服务端报告账户欠费，请核对计费状态'
 elif code=='SetLimitExceeded':hint='模型累计用量已达到账号设置上限，服务暂停；请在开通管理核对限额，程序不会自动提高限额'
 else:hint=hints.get(error.code,'服务端返回错误')
 parts=['豆包 API HTTP '+str(error.code)+' / '+code+'：'+hint]
 parts.append('服务端说明：'+message if message else '服务端未提供具体说明；不能仅凭HTTP状态码确定原因。')
 if rid:parts.append('请求ID：'+rid)
 return ModelError('\n'.join(parts),'HTTP_'+str(error.code),provider_code=code,provider_message=message,request_id=rid,http_status=error.code)

def request_completion(cfg,payload,opener=None):
 if not cfg.get('api_key'):raise ModelError('本机尚未检测到API密钥。','KEY_MISSING')
 model=extract_model(cfg.get('model'))
 if not model:raise ModelError('请填写方舟模型ID或推理接入点ID。','MODEL_MISSING')
 url=endpoint(cfg);body=dict(payload);body['model']=model;body.setdefault('stream',False)
 body.setdefault('max_tokens',int(cfg.get('max_output_tokens',1800)))
 if cfg.get('provider')=='doubao':body.setdefault('thinking',{'type':cfg.get('thinking','disabled')})
 if cfg.get('api_mode')=='responses':body=responses_payload(body)
 req=urllib.request.Request(url,data=json.dumps(body,ensure_ascii=False).encode('utf-8'),headers={'Authorization':'Bearer '+cfg['api_key'],'Content-Type':'application/json'},method='POST')
 open_fn=opener or urllib.request.urlopen;retries=max(0,min(int(cfg.get('api_retries',1)),2))
 for attempt in range(retries+1):
  try:
   with open_fn(req,timeout=int(cfg.get('request_timeout',90))) as response:
    data=json.load(response);rid=response.headers.get('x-request-id','')
   if isinstance(data,dict) and cfg.get('api_mode')=='responses':data=normalize_responses(data)
   if not isinstance(data,dict) or not data.get('choices'):raise ModelError('API未返回可用消息，可能是接口类型或模型不兼容。','RESPONSE_INVALID')
   choice=data['choices'][0]
   if choice.get('finish_reason')=='length':raise ModelError('模型输出达到长度上限，本轮未执行不完整的工具指令；请调整输出上限后重试。','OUTPUT_TRUNCATED')
   if choice.get('finish_reason') in ('content_filter','sensitive'):raise ModelError('本轮响应被服务端过滤，未宣称任务完成。','CONTENT_FILTERED')
   if not isinstance(choice.get('message'),dict):raise ModelError('模型返回消息格式无效。','RESPONSE_INVALID')
   data['_request_id']=rid
   return data
  except urllib.error.HTTPError as e:
   error=provider_http_error(e,cfg['api_key'])
   if e.code in (429,502,503,504) and not account_blocked(error.diagnostics()) and attempt<retries:time.sleep(.5*(attempt+1));continue
   raise error from None
  except (socket.timeout,TimeoutError):raise ModelError('模型请求超时，未自动重发以避免重复调用；可查看日志后手动重试。','NETWORK_TIMEOUT') from None
  except urllib.error.URLError as e:
   reason=getattr(e,'reason',e)
   if isinstance(reason,OSError) and getattr(reason,'winerror',None)==10013:raise ModelError('当前运行环境禁止网络连接（WinError 10013）。请在本机正常启动程序后连接豆包。','NETWORK_BLOCKED') from None
   raise ModelError('无法连接豆包API，请检查网络、代理或证书；本轮未降级为演示。','NETWORK_UNAVAILABLE') from None
  except (ValueError,KeyError,IndexError):raise ModelError('API返回内容不是预期的JSON消息。','RESPONSE_INVALID') from None

def test_connection(cfg,transport=None):
 # A real, small tool call verifies more than a text-only hello.
 tools=[{'type':'function','function':{'name':'connection_probe','description':'连接测试，请调用此工具，参数为空对象。','parameters':{'type':'object','properties':{},'additionalProperties':False}}}]
 payload={'messages':[{'role':'user','content':'只调用connection_probe工具，参数为空对象。不要输出其他文字。'}],'tools':tools,'tool_choice':{'type':'function','function':{'name':'connection_probe'}},'max_tokens':256}
 start=time.monotonic();response=transport(payload) if transport else request_completion(cfg,payload)
 calls=response['choices'][0]['message'].get('tool_calls') or []
 if len(calls)!=1 or calls[0].get('function',{}).get('name')!='connection_probe':raise ModelError('API可响应，但未按要求返回函数调用；尚未通过Agent连接检查。','TOOLS_NOT_CONFIRMED')
 try:args=json.loads(calls[0]['function'].get('arguments','{}'))
 except Exception:raise ModelError('模型工具参数不是有效JSON。','TOOLS_NOT_CONFIRMED') from None
 if args!={}:raise ModelError('模型工具参数不符合要求。','TOOLS_NOT_CONFIRMED')
 # Verify tool-result replay as well as first-turn function selection.
 call=calls[0]
 if not call.get('id'):raise ModelError('工具调用缺少关联ID','TOOLS_NOT_CONFIRMED')
 history=list(payload['messages'])+[{'role':'assistant','content':None,'tool_calls':calls},
  {'role':'tool','tool_call_id':call['id'],'content':'{"status":"OK","probe":"connection"}'},
  {'role':'user','content':'工具返回成功，请只回答 CONNECTION_OK，不要再调用工具。'}]
 final=transport({'messages':history,'max_tokens':256}) if transport else request_completion(cfg,{'messages':history,'max_tokens':256})
 if not (final['choices'][0]['message'].get('content') or '').strip():raise ModelError('工具回传后没有最终回答','TOOLS_NOT_CONFIRMED')
 return {'status':'CONNECTED_TOOL_CALL_VERIFIED','provider':cfg.get('provider'),'model':extract_model(cfg.get('model')),'seconds':round(time.monotonic()-start,3),'usage':response.get('usage',{}),'request_id':response.get('_request_id',''),'checked_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'probe_tools_executed':True,'multi_turn_verified':True,'note':'真实API返回正确的工具指令；完整任务仍需运行验证'}
