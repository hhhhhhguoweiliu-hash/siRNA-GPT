"""Reproducible three-arm execution recorder, not an automatic scientific quality judge."""
import argparse,csv,hashlib,json,random,time,uuid,sys
from pathlib import Path
# Windows embeddable Python may omit the script directory from sys.path.
sys.path.insert(0,str(Path(__file__).resolve().parent))
from core import config,save_json,TaskError,TOOLS
from conversation import Conversation,PlannedSession,prepare_inputs,PRESETS,SCOPE
from model_client import request_completion,ModelError,account_blocked
from runtime_info import manifest
from evaluation_protocol import evaluation_settings,settings_sha256

def safe_record(value,cfg):
    raw=json.dumps(value,ensure_ascii=False)
    if cfg.get('api_key'):raw=raw.replace(cfg['api_key'],'[REDACTED]')
    return json.loads(raw)

def write_execution_status(out,jobs,results,pending_reason):
    """One row per planned unit, including units never attempted after a stop."""
    actual={(r['case_id'],r['group'],r['repeat']):r for r in results}
    rows=[]
    for index,(case,group,rep) in enumerate(jobs):
        r=actual.get((case['id'],group,rep))
        rows.append({'schedule_index':index+1,'case_id':case['id'],'group':group,'repeat':rep,
            'answer_id':r.get('answer_id','') if r else '',
            'execution':'ATTEMPTED' if r else 'NOT_EXECUTED',
            'status':r['status'] if r else 'NOT_EXECUTED',
            'pending_reason':'' if r else pending_reason})
    write_rows(Path(out)/'execution_status.tsv',rows,
        ['schedule_index','case_id','group','repeat','answer_id','execution','status','pending_reason'])

def write_rows(path,rows,fields):
    with Path(path).open('w',encoding='utf-8-sig',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=fields,delimiter='\t');writer.writeheader();writer.writerows(rows)

def export_answers(out,cases,results):
    requests={c['id']:c['request'] for c in cases}
    fields=['answer_id','case_id','request','answer','reviewer_id','accuracy_0_2','evidence_0_2','task_fit_0_2','limits_0_2','notes']
    blind=[dict.fromkeys(fields,'')|{'answer_id':r['answer_id'],'case_id':r['case_id'],
        'request':requests[r['case_id']],'answer':r.get('answer','')} for r in results]
    keys=[{k:r[k] for k in ['answer_id','case_id','group','repeat','status']} for r in results]
    write_rows(Path(out)/'blind_answers.tsv',blind,fields)
    write_rows(Path(out)/'private_key.tsv',keys,['answer_id','case_id','group','repeat','status'])

def wait(c,seconds=360):
    deadline=time.monotonic()+seconds
    while c.snapshot()['busy'] and time.monotonic()<deadline:time.sleep(.1)
    if c.snapshot()['busy']:
        c.request_stop()
        raise TimeoutError('Evaluation timed out. Stop this batch; do not start concurrent follow-up cases.')

def _run_case(group,case,cfg,root,transport=None):
    if group not in ('llm','workflow','agent'):raise ValueError('Unknown evaluation arm')
    Path(root).mkdir(parents=True,exist_ok=True)
    start=time.monotonic();data={**case.get('input',{}),**case.get('task',{}),'message':case['request'],'tool_mode':'imported','web_enabled':False}
    result={'group':group,'case_id':case['id'],'status':'FAILED','tool_calls':0,'usage':[]}
    if group=='agent':
        c=Conversation(root=Path(root)/'conversations',cfg_loader=lambda:cfg,transport=transport,
            session_factory=lambda **kw:PlannedSession(run_root=Path(root)/'runs',**kw))
        c.submit({**data,'interaction_mode':'auto'});wait(c)
        if c.plan and c.phase=='awaiting_execution':c.action('execute',c.plan['id']);wait(c)
        result.update(status=(c.result or {}).get('status',c.phase),answer=c.messages[-1]['text'],
            tool_calls=(c.session.tool_calls if c.session else 0)+sum(len(r['observations']) for r in c.export_record()['evidence_records']),record=c.export_record(),
            usage=[e['usage'] for e in c.events if e.get('usage')],phase=c.phase,
            completed_tools=list(c.session.state) if c.session else [],tool_results=c.session.state if c.session else {},plan=c.plan,
            provider_error={k:c.result.get(k) for k in ['code','provider_code','http_status','request_id']} if c.result and c.result.get('code') else {})
    elif group=='workflow':
        inputs=prepare_inputs(data);inputs['task'].update(case.get('task',{}))
        preset=case.get('preset','full')
        if preset not in PRESETS:raise ValueError('Unknown fixed preset')
        s=PlannedSession(planned_tools=PRESETS[preset],mode='workflow',cfg=cfg,run_root=Path(root)/'runs',**inputs)
        for name in s.planned_tools:
            r=s.call(name,{})
            if r.get('status')=='ERROR':
                result.update(status='FAILED',answer=r['message']);break
        else:
            r=s.result_for_plan();result.update(status=r['status'],answer=json.dumps(r,ensure_ascii=False))
        result.update(tool_calls=s.tool_calls,run_id=s.id,tool_results=s.state,completed_tools=list(s.state))
    else:
        inputs=prepare_inputs(data);inputs['task'].update(case.get('task',{}))
        # Same supplied case input and declared capability boundary, without tools or retrieved outputs.
        payload={'model':cfg.get('model'),'messages':[{'role':'system','content':'你是siRNA研究助手。根据所给需求和输入回答，不能假装执行工具或编造实验/模型数值。当前系统能力边界：'+SCOPE},
            {'role':'user','content':json.dumps({'request':case['request'],'input':inputs,'tool_descriptions':TOOLS,'preset':case.get('preset','full')},ensure_ascii=False)}]}
        save_json(Path(root)/'model_request.json',safe_record(payload,cfg))
        r=transport(payload) if transport else request_completion(cfg,payload)
        save_json(Path(root)/'model_response.json',safe_record(r,cfg))
        result.update(status='ANSWERED_NO_TOOLS',answer=r['choices'][0]['message'].get('content') or '',usage=[r.get('usage',{})])
    result['seconds']=round(time.monotonic()-start,3)
    known=all(isinstance(u.get('total_tokens'),int) for u in result['usage'])
    result['total_tokens']=(sum(u['total_tokens'] for u in result['usage'])
        if result['usage'] and known and not result.get('provider_error') else 0 if group=='workflow' else None)
    result['usage_complete']=group=='workflow' or bool(result['usage']) and known and not result.get('provider_error')
    result['known_token_subtotal']=sum(u['total_tokens'] for u in result['usage'] if isinstance(u.get('total_tokens'),int)) if result['usage'] else 0 if group=='workflow' else None
    return result

def run_case(group,case,cfg,root,transport=None):
    started=time.monotonic()
    try:return _run_case(group,case,cfg,root,transport)
    except ModelError as e:
        partial=getattr(e,'response_snapshot',None)
        if partial is not None:save_json(Path(root)/'model_error_response.json',safe_record(partial,cfg))
        usage=partial.get('usage',{}) if isinstance(partial,dict) else {}
        return {'group':group,'case_id':case['id'],'status':'FAILED','answer':str(e),
            'provider_error':{k:v for k,v in e.diagnostics().items() if k!='provider_message'},
            'usage':[usage] if usage else [],'usage_complete':False,'partial_response_saved':partial is not None,
            'tool_calls':0,'total_tokens':None,'seconds':round(time.monotonic()-started,3)}

def main(argv=None):
    p=argparse.ArgumentParser();p.add_argument('--cases',required=True);p.add_argument('--output',required=True)
    p.add_argument('--group',choices=['llm','workflow','agent','all'],default='workflow');p.add_argument('--repeats',type=int,default=3)
    p.add_argument('--limit',type=int);p.add_argument('--seed',type=int,default=20261019);a=p.parse_args(argv)
    if not 1<=a.repeats<=10:p.error('repeats must be 1–10')
    if a.limit is not None and a.limit<1:p.error('limit must be positive')
    cases_file=Path(a.cases);source=json.loads(cases_file.read_text(encoding='utf-8'));cases=source['cases']
    if not cases or len({x['id'] for x in cases})!=len(cases):p.error('Cases require unique IDs')
    if a.limit is not None:cases=cases[:a.limit]
    out=Path(a.output)
    if out.exists() and any(out.iterdir()):p.error('Use a new empty output directory; existing results are never overwritten.')
    out.mkdir(parents=True,exist_ok=True);cfg=config()
    groups=['llm','workflow','agent'] if a.group=='all' else [a.group]
    protocol={'runtime':manifest(),'dataset_sha256':hashlib.sha256(cases_file.read_bytes()).hexdigest(),
        'dataset_review':source.get('review_status','UNKNOWN'),'model':cfg.get('model'),'provider':cfg.get('provider'),
        'groups':groups,'repeats':a.repeats,'seed':a.seed,'cases':[c['id'] for c in cases],
        'api_mode':cfg.get('api_mode'),'web_enabled':False,
        'scope':'execution cases; no automatic scientific quality score; imported scientific outputs only',
        'claim':'Development examples are not a frozen held-out expert test set.'}
    protocol['model_settings']=evaluation_settings(cfg)
    protocol['model_settings_sha256']=settings_sha256(protocol['model_settings'])
    jobs=[(case,group,rep) for case in cases for group in groups for rep in range(1,a.repeats+1)]
    rng=random.Random(a.seed);rng.shuffle(jobs)
    protocol.update(planned_observations=len(jobs),scheduled_order=[{'case_id':c['id'],'group':g,'repeat':n} for c,g,n in jobs])
    save_json(out/'protocol.json',protocol);save_json(out/'cases.json',{'review_status':source.get('review_status'),'cases':cases})
    results=[];status='COMPLETE';blocking_error=None
    write_execution_status(out,jobs,results,'RUNNING')
    for case,group,rep in jobs:
        answer_id=uuid.uuid4().hex[:12];folder=out/answer_id;folder.mkdir()
        try:r=run_case(group,case,cfg,folder)
        except TimeoutError as e:
            r={'group':group,'case_id':case['id'],'status':'TIMED_OUT','answer':str(e),'total_tokens':None}
            status='STOPPED_TIMEOUT'
        except Exception as e:r={'group':group,'case_id':case['id'],'status':'FAILED','answer':str(e)}
        r.update(repeat=rep,answer_id=answer_id);r=safe_record(r,cfg)
        save_json(folder/'result.json',r);results.append(r);save_json(out/'results.json',results)
        if account_blocked(r.get('provider_error',{})):
            blocking_error=r['provider_error'];status='BLOCKED_ACCOUNT'
        write_execution_status(out,jobs,results,status if status!='COMPLETE' else 'RUNNING')
        if status!='COMPLETE':break
    export_answers(out,cases,results)
    completion={'status':status,'completed':len(results),'pending':len(jobs)-len(results),
        'scientific_quality_scored':False,'blocking_error':blocking_error}
    save_json(out/'completion.json',completion);write_execution_status(out,jobs,results,status)
    print('Recorded '+str(len(results))+' answers; '+status+'; expert scoring has not been performed.')

if __name__=='__main__':main()
