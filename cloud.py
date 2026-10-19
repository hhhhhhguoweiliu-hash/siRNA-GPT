"""Single-owner WSGI entrypoint for Render; Gunicorn uses one process + threads.

The lightweight hosted edition imports verified scientific outputs. It never
claims that local heavy model/R workers were run on this service.
"""
import base64, binascii, io, json, os, secrets
from http import HTTPStatus
from types import SimpleNamespace
from urllib.parse import quote, urlsplit
import app as local
import core

local_cloud_base = core.config
def cloud_config():
    c=local_cloud_base()
    c.update(provider='doubao', api_mode='responses', base_url='https://ark.cn-beijing.volces.com/api/v3',
        api_key=os.environ.get('ARK_API_KEY',''), model=os.environ.get('ARK_MODEL','doubao-seed-2-1-pro-260915'),
        request_timeout=90, api_retries=1)
    return c
local.config=cloud_config
core.config=cloud_config
local.CONVERSATION.cfg_loader=cloud_config

class Wire:
    def __init__(self,raw): self.rfile=io.BytesIO(raw);self.output=bytearray()
    def makefile(self,*args):return self.rfile
    def sendall(self,data):self.output.extend(data)

def response(start,status,body,mime='application/json; charset=utf-8',extra=()):
    if not isinstance(body,bytes):
        body=(json.dumps(body,ensure_ascii=False) if not isinstance(body,str) else body).encode('utf-8')
    start(str(status)+' '+HTTPStatus(status).phrase,[('Content-Type',mime),('Content-Length',str(len(body))),
        ('Cache-Control','no-store'),('X-Content-Type-Options','nosniff'),('Referrer-Policy','same-origin'),*extra])
    return [body]

def allowed_host(host):
    configured=os.environ.get('RENDER_EXTERNAL_HOSTNAME','').lower()
    if not configured:configured=urlsplit(os.environ.get('RENDER_EXTERNAL_URL','')).netloc.lower()
    return host.lower() in ({configured} if configured else {'localhost','127.0.0.1','localhost:10000','127.0.0.1:10000'})

def authorized(value):
    expected=os.environ.get('WEB_PASSWORD','')
    if len(expected)<16:return False
    try:
        scheme,encoded=value.split(' ',1)
        user,password=base64.b64decode(encoded,validate=True).decode('utf-8').split(':',1)
        return scheme.lower()=='basic' and user=='research' and secrets.compare_digest(password.encode('utf-8'),expected.encode('utf-8'))
    except (ValueError,UnicodeError,binascii.Error):return False

def application(environ,start_response):
    path=environ.get('PATH_INFO','/');method=environ.get('REQUEST_METHOD','GET')
    if path=='/healthz' and method=='GET':return response(start_response,200,{'status':'ok','version':'0.4-cloud'})
    host=environ.get('HTTP_HOST','')
    if not allowed_host(host):return response(start_response,403,{'error':'Invalid host'})
    if len(os.environ.get('WEB_PASSWORD',''))<16:
        return response(start_response,503,{'error':'Set WEB_PASSWORD (at least 16 characters) in Render environment variables.'})
    if not authorized(environ.get('HTTP_AUTHORIZATION','')):
        return response(start_response,401,'Sign in with username research and your site password.',
            'text/plain; charset=utf-8',[('WWW-Authenticate','Basic realm="siRNA-GPT", charset="UTF-8"')])
    if method not in ('GET','POST'):return response(start_response,405,{'error':'Method not allowed'})
    body=b''
    if method=='POST':
        origin=environ.get('HTTP_ORIGIN')
        expected=os.environ.get('RENDER_EXTERNAL_URL','').rstrip('/') or environ.get('wsgi.url_scheme','http')+'://'+host
        if origin and origin!=expected:return response(start_response,403,{'error':'Invalid origin'})
        if environ.get('HTTP_X_RPE_LOCAL')!='1':return response(start_response,403,{'error':'Application request required'})
        if path=='/api/config':return response(start_response,409,{'error':'云端配置由Render环境变量管理；请在后台更新后重新部署。'})
        try:
            n=int(environ.get('CONTENT_LENGTH') or 0)
            if n<0 or n>50000:return response(start_response,413,{'error':'Input too large'})
            data=json.loads(environ['wsgi.input'].read(n).decode('utf-8'))
        except (ValueError,UnicodeError,KeyError):return response(start_response,400,{'error':'Invalid JSON request'})
        if not isinstance(data,dict):return response(start_response,400,{'error':'JSON object required'})
        if path in ('/api/run','/api/message'):
            if data.get('tool_mode','imported')!='imported':
                return response(start_response,409,{'error':'当前云端版本读取已验证的工具结果。重新运行OligoFormer/SeedMatchR需要另接计算后台。'})
            data['tool_mode']='imported'
        body=json.dumps(data,ensure_ascii=False).encode('utf-8')
    uri=environ.get('RAW_URI') or quote(path,safe='/%')+('?' + environ['QUERY_STRING'] if environ.get('QUERY_STRING') else '')
    if '\r' in uri or '\n' in uri:return response(start_response,400,{'error':'Invalid path'})
    raw=(method+' '+uri+' HTTP/1.0\r\nHost: 127.0.0.1:8765\r\nX-RPE-Local: 1\r\nContent-Type: application/json\r\nContent-Length: '+str(len(body))+'\r\n\r\n').encode()+body
    wire=Wire(raw)
    local.Handler(wire,('127.0.0.1',0),SimpleNamespace(server_port=8765))
    head,out=bytes(wire.output).split(b'\r\n\r\n',1);status=int(head.splitlines()[0].split()[1]);mime='application/octet-stream'
    for line in head.splitlines()[1:]:
        if line.lower().startswith(b'content-type:'):mime=line.split(b':',1)[1].decode().strip()
    return response(start_response,status,out,mime)

if __name__=='__main__':
    from wsgiref.simple_server import make_server
    with make_server('0.0.0.0',int(os.environ.get('PORT','10000')),application) as server:server.serve_forever()
