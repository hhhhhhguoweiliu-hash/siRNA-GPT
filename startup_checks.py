"""Public-keyword smoke checks in the actual deployed runtime; no user data in probes."""
import json, os, time
from core import HOME, save_json
from model_client import redact, ModelError

def log(name,data,cfg):
    safe={'status':data.get('status'),'source_count':data.get('source_count',len(data.get('sources',[]))),
        'message':redact(data.get('message',''),cfg.get('api_key','')),
        'provider_code':data.get('provider_code',''),'request_id':data.get('request_id',''),
        'multi_turn_verified':data.get('multi_turn_verified',False)}
    for key in ('tools','source_titles','answer_preview'):
        if key in data:safe[key]=data[key]
    print('STARTUP_CHECK '+name+' '+json.dumps(safe,ensure_ascii=True),flush=True)

def research_checks(cfg,model_connected):
    from research import search_pubmed,search_web
    results={}
    for name,fn in [('pubmed',lambda:search_pubmed('OligoFormer',1)),
        ('web',lambda:search_web('OligoFormer siRNA original paper',cfg))]:
        if name=='web' and not model_connected:
            r={'status':'SKIPPED','message':'Model connection failed; no web search request sent.'}
        else:
            try:r=fn()
            except Exception as e:
                r={'status':'ERROR','message':redact(str(e),cfg.get('api_key',''))}
                if isinstance(e,ModelError):r.update(e.diagnostics())
        results[name]={k:r[k] for k in ('status','message','request_id','provider_code') if k in r}
        results[name]['source_count']=len(r.get('sources',[]));log(name,r,cfg)
    return results

def verify_research_conversation(cfg_loader):
    """An isolated real conversation; never replaces the user's active conversation."""
    from conversation import Conversation
    c=Conversation(cfg_loader=cfg_loader,root=HOME/'_startup_checks')
    c.submit({'message':'请通过 PubMed 联网检索 OligoFormer 原始论文，告诉我真实题名以及它评估什么，给出引用编号；只依据查到的文献，不要编造。',
        'interaction_mode':'auto','tool_mode':'imported','web_enabled':True})
    deadline=time.monotonic()+180
    while c.snapshot()['busy'] and time.monotonic()<deadline:time.sleep(.3)
    state=c.snapshot();answer=c.messages[-1] if c.messages else {};sources=answer.get('sources',[])
    tools=[s['tool'] for s in state.get('research',{}).get('steps',[]) if s.get('status')=='OK']
    ok=not state['busy'] and answer.get('kind')=='qa' and bool(sources) and 'search_pubmed' in tools
    return {'status':'VERIFIED' if ok else 'FAILED','source_count':len(sources),'tools':tools,
        'source_titles':[s['title'] for s in sources[:3]],
        'answer_preview':redact(answer.get('text',''),cfg_loader().get('api_key','')),
        'message':'' if ok else 'Isolated live conversation did not complete with retrieved sources.'}

def verify_scientific_conversation(cfg_loader):
    from conversation import Conversation
    c=Conversation(cfg_loader=cfg_loader,root=HOME/'_startup_checks')
    c.submit({'message':'请对默认9条人VEGFA候选做完整核对，读取已有官方分数和seed结果，关联缺氧表达背景，最后生成2条优先核查候选的报告。不查文献。',
        'interaction_mode':'auto','tool_mode':'imported','web_enabled':False})
    def wait():
        deadline=time.monotonic()+240
        while c.snapshot()['busy'] and time.monotonic()<deadline:time.sleep(.3)
    wait()
    if c.plan and c.phase=='awaiting_execution':c.action('execute',c.plan['id']);wait()
    state=c.snapshot();result=c.result or {};tools=list(c.session.state) if c.session else []
    ok=not state['busy'] and result.get('status')=='COMPLETE' and len(tools)==6
    return {'status':'VERIFIED' if ok else 'FAILED','tools':tools,'source_count':0,
        'message':'Full six-tool workflow with imported scientific outputs; no heavy cloud model/R rerun.' if ok else c.messages[-1].get('text',''),
        'answer_preview':redact(c.messages[-1].get('text',''),cfg_loader().get('api_key',''))}

def run():
    if not os.environ.get('RENDER_SERVICE_ID') or os.environ.get('STARTUP_CHECKS','1')!='1':return
    import app
    marker=HOME/'connection.startup.json';commit=os.environ.get('RENDER_GIT_COMMIT','unknown')
    if marker.exists():
        try:
            old=json.loads(marker.read_text(encoding='utf-8'))
            if old.get('commit')==commit:
                with app.LOCK:
                    app.STATE['connection']=old.get('model',{'status':'NOT_TESTED'})
                    app.STATE['research_connection']={k:old[k] for k in ('pubmed','web') if k in old}
                    if app.STATE['connection'].get('status')=='CONNECTED_TOOL_CALL_VERIFIED':
                        from model_client import client_fingerprint
                        app.CONNECTION_FINGERPRINT=client_fingerprint(app.config())
                return
        except (ValueError,OSError):pass
    cfg=app.config();result={'commit':commit,'version':'0.6-cloud'}
    with app.LOCK:app.STATE['checking_connection']=True
    app.check_connection(check_research=True)
    with app.LOCK:
        result['model']=dict(app.STATE['connection']);result.update(app.STATE.get('research_connection',{}))
    log('model',result['model'],cfg)
    if result['model'].get('status')=='CONNECTED_TOOL_CALL_VERIFIED' and result.get('pubmed',{}).get('status')=='OK':
        try:result['research_conversation']=verify_research_conversation(app.config)
        except Exception as e:result['research_conversation']={'status':'FAILED','message':redact(str(e),cfg.get('api_key',''))}
        log('research_conversation',result['research_conversation'],cfg)
    if result['model'].get('status')=='CONNECTED_TOOL_CALL_VERIFIED':
        try:result['scientific_conversation']=verify_scientific_conversation(app.config)
        except Exception as e:result['scientific_conversation']={'status':'FAILED','message':redact(str(e),cfg.get('api_key',''))}
        log('scientific_conversation',result['scientific_conversation'],cfg)
    save_json(marker,result)
