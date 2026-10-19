"""Public-keyword startup probes; no candidate data or secrets in logs."""
import json, os
from core import HOME, save_json
from model_client import redact

def run():
    if not os.environ.get('RENDER_SERVICE_ID') or os.environ.get('STARTUP_CHECKS','1')!='1':return
    import app
    from research import search_pubmed, search_web
    marker=HOME/'connection.startup.json'
    commit=os.environ.get('RENDER_GIT_COMMIT','unknown')
    if marker.exists():
        try:
            old=json.loads(marker.read_text(encoding='utf-8'))
            if old.get('commit')==commit:return
        except (ValueError,OSError):pass
    cfg=app.config(); result={'commit':commit,'version':'0.5-cloud'}
    # No WSGI request is blocked while the deployment runs these small checks.
    with app.LOCK:app.STATE['checking_connection']=True
    app.check_connection()
    with app.LOCK:result['model']=dict(app.STATE['connection'])
    def log(name,data):
        safe={'status':data.get('status'),'source_count':len(data.get('sources',[])),
            'message':redact(data.get('message',''),cfg.get('api_key','')),
            'request_id':data.get('request_id',''),'multi_turn_verified':data.get('multi_turn_verified',False)}
        print('STARTUP_CHECK '+name+' '+json.dumps(safe,ensure_ascii=True),flush=True)
    log('model',result['model'])
    for name,fn in [('pubmed',lambda:search_pubmed('OligoFormer',1)),
        ('web',lambda:search_web('OligoFormer siRNA original paper',cfg))]:
        if name=='web' and result['model'].get('status')!='CONNECTED_TOOL_CALL_VERIFIED':
            r={'status':'SKIPPED','message':'Model connection failed; no search request sent.'}
        else:
            try:r=fn()
            except Exception as e:r={'status':'ERROR','message':redact(str(e),cfg.get('api_key',''))}
        result[name]={k:r[k] for k in ('status','message','request_id') if k in r}
        result[name]['source_count']=len(r.get('sources',[]));log(name,r)
    save_json(marker,result)
    with app.LOCK:app.STATE['research_connection']={k:result[k] for k in ('pubmed','web')}
