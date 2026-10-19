"""Reproducible three-arm execution recorder, not an automatic scientific quality judge."""
import argparse,csv,hashlib,json,random,time,uuid
from pathlib import Path
from core import config,save_json,TaskError,TOOLS
from conversation import Conversation,PlannedSession,prepare_inputs,PRESETS,SCOPE
from model_client import request_completion
from runtime_info import manifest

def wait(c,seconds=360):
    deadline=time.monotonic()+seconds
    while c.snapshot()['busy'] and time.monotonic()<deadline:time.sleep(.1)
    if c.snapshot()['busy']:
        c.request_stop()
        raise TimeoutError('Evaluation timed out. Stop this batch; do not start concurrent follow-up cases.')

def run_case(group,case,cfg,root,transport=None):
    if group not in ('llm','workflow','agent'):raise ValueError('Unknown evaluation arm')
    Path(root).mkdir(parents=True,exist_ok=True)
    start=time.monotonic();data={**case.get('input',{}),'message':case['request'],'tool_mode':'imported'}
    result={'group':group,'case_id':case['id'],'status':'FAILED','tool_calls':0,'usage':[]}
    if group=='agent':
        c=Conversation(root=Path(root)/'conversations',cfg_loader=lambda:cfg,transport=transport,
            session_factory=lambda **kw:PlannedSession(run_root=Path(root)/'runs',**kw))
        c.submit({**data,'interaction_mode':'auto'});wait(c)
        if c.plan and c.phase=='awaiting_execution':c.action('execute',c.plan['id']);wait(c)
        result.update(status=(c.result or {}).get('status',c.phase),answer=c.messages[-1]['text'],
            tool_calls=(c.session.tool_calls if c.session else 0)+sum(len(r['observations']) for r in c.export_record()['evidence_records']),record=c.export_record(),
            usage=[e['usage'] for e in c.events if e.get('usage')])
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
        result.update(tool_calls=s.tool_calls,run_id=s.id,tool_results=s.state)
    else:
        inputs=prepare_inputs(data);inputs['task'].update(case.get('task',{}))
        # Same supplied case input and declared capability boundary, without tools or retrieved outputs.
        payload={'messages':[{'role':'system','content':'你是siRNA研究助手。根据所给需求和输入回答，不能假装执行工具或编造实验/模型数值。当前系统能力边界：'+SCOPE},
            {'role':'user','content':json.dumps({'request':case['request'],'input':inputs,'tool_descriptions':TOOLS,'preset':case.get('preset','full')},ensure_ascii=False)}]}
        r=transport(payload) if transport else request_completion(cfg,payload)
        result.update(status='ANSWERED_NO_TOOLS',answer=r['choices'][0]['message'].get('content') or '',usage=[r.get('usage',{})])
    result['seconds']=round(time.monotonic()-start,3)
    result['total_tokens']=sum(int(u.get('total_tokens',0)) for u in result['usage'])
    return result

def main():
    p=argparse.ArgumentParser();p.add_argument('--cases',required=True);p.add_argument('--output',required=True)
    p.add_argument('--group',choices=['llm','workflow','agent','all'],default='workflow');p.add_argument('--repeats',type=int,default=3)
    p.add_argument('--limit',type=int);p.add_argument('--seed',type=int,default=20261019);a=p.parse_args()
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
        'scope':'execution cases; no automatic scientific quality score; imported scientific outputs only',
        'claim':'Development examples are not a frozen held-out expert test set.'}
    save_json(out/'protocol.json',protocol)
    jobs=[(case,group,rep) for case in cases for group in groups for rep in range(1,a.repeats+1)]
    rng=random.Random(a.seed);rng.shuffle(jobs);blind=[];keys=[]
    for case,group,rep in jobs:
        answer_id=uuid.uuid4().hex[:12];folder=out/answer_id;folder.mkdir()
        try:r=run_case(group,case,cfg,folder)
        except TimeoutError:raise
        except Exception as e:r={'group':group,'case_id':case['id'],'status':'FAILED','answer':str(e)}
        r['repeat']=rep;save_json(folder/'result.json',r)
        blind.append({'answer_id':answer_id,'case_id':case['id'],'request':case['request'],'answer':r.get('answer','')})
        keys.append({'answer_id':answer_id,'group':group,'repeat':rep,'status':r['status']})
    for name,rows in [('blind_answers.tsv',blind),('private_key.tsv',keys)]:
        with (out/name).open('w',encoding='utf-8-sig',newline='') as f:
            writer=csv.DictWriter(f,fieldnames=list(rows[0]),delimiter='\t');writer.writeheader();writer.writerows(rows)
    print('Recorded '+str(len(keys))+' answers; expert scoring has not been performed.')

if __name__=='__main__':main()
