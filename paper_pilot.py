"""Explicit one-off development pilot. Never runs at startup or on a schedule.

Exports a compressed, checksummed archive to owner-only deployment logs so the
authorized researcher can recover complete records from ephemeral hosting.
No keys/configuration values are archived. Not a frozen or blinded study.
"""
import base64,hashlib,io,json,os,random,re,threading,time,uuid,zipfile
from pathlib import Path
from core import HOME,save_json,now
from runtime_info import manifest
from model_client import account_blocked
from evaluation_protocol import evaluation_settings,settings_sha256

LOCK=threading.Lock()
STATE={'status':'NOT_STARTED'}
STOP=threading.Event()

def log(kind,value):
    print('PAPER_PILOT '+kind+' '+json.dumps(value,ensure_ascii=True,separators=(',',':')),flush=True)

def run(cfg_loader,run_id):
    from evaluate import run_case,write_execution_status,export_answers
    if not re.fullmatch(r'[a-zA-Z0-9_-]{1,50}',run_id):raise ValueError('Invalid run ID')
    if not LOCK.acquire(blocking=False):return
    out=HOME/'evaluation_runs'/run_id
    try:
        if out.exists():return
        out.mkdir(parents=True);cfg=cfg_loader()
        # Same model, scientific imports and metadata; no external search in any arm.
        source=HOME/'evaluation_cases.example.json';suite=json.loads(source.read_text(encoding='utf-8'))
        cases=suite['cases'];jobs=[(c,g,n) for c in cases for g in ['llm','workflow','agent'] for n in range(1,4)]
        random.Random(20261019).shuffle(jobs)
        protocol={'id':run_id,'started_at':now(),'runtime':manifest(),'cases_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
            'model':cfg.get('model'),'provider':cfg.get('provider'),'api_mode':cfg.get('api_mode'),
            'seed':20261019,'repeats':3,'groups':['llm','workflow','agent'],'review_status':suite['review_status'],
            'web_enabled':False,'planned_observations':len(jobs),'scheduled_order':[{'case_id':c['id'],'group':g,'repeat':n} for c,g,n in jobs],
            'limitations':['Development cases; not held out or expert reviewed','No automatic semantic quality score','Repeated tasks are not independent biological replicates','Scientific results imported, not heavy model/R reruns','Fixed arm receives preset and structured task; not asked to parse unrestricted language','Cost in currency unavailable; usage is provider-returned token count']}
        protocol['model_settings']=evaluation_settings(cfg)
        protocol['model_settings_sha256']=settings_sha256(protocol['model_settings'])
        save_json(out/'protocol.json',protocol);save_json(out/'cases.json',suite)
        STOP.clear();STATE.clear();STATE.update(status='RUNNING',run_id=run_id,completed=0,total=len(jobs));log('BEGIN',protocol)
        results=[]
        blocking_error=None
        timed_out=False
        write_execution_status(out,jobs,results,'RUNNING')
        for index,(case,group,rep) in enumerate(jobs):
            if STOP.is_set():break
            answer_id='A'+str(index+1).zfill(3);folder=out/answer_id
            try:r=run_case(group,case,cfg,folder)
            except TimeoutError as e:
                # Do not overlap with a timed-out running conversation.
                timed_out=True
                r={'group':group,'case_id':case['id'],'status':'TIMED_OUT','answer':str(e),
                    'usage':[],'tool_calls':0,'seconds':None,'total_tokens':None}
            except Exception as e:r={'group':group,'case_id':case['id'],'status':'FAILED','answer':str(e),'usage':[],'tool_calls':0,'seconds':None}
            r.update(answer_id=answer_id,repeat=rep,recorded_at=now())
            # Strip the actual secret if a provider were to echo it in an error/text.
            raw=json.dumps(r,ensure_ascii=False);secret=cfg.get('api_key','')
            if secret:raw=raw.replace(secret,'[REDACTED]')
            r=json.loads(raw);folder.mkdir(parents=True,exist_ok=True);save_json(folder/'result.json',r);results.append(r)
            save_json(out/'results.json',results);write_execution_status(out,jobs,results,'RUNNING')
            STATE.update(completed=index+1);log('CASE',{'answer_id':answer_id,'case_id':case['id'],'group':group,'repeat':rep,'status':r['status'],'seconds':r.get('seconds'),'tool_calls':r.get('tool_calls',0),'tokens':r.get('total_tokens')})
            if account_blocked(r.get('provider_error',{})):
                blocking_error=r['provider_error'];STATE.update(blocking_error=blocking_error)
                log('ACCOUNT_BLOCK',blocking_error);break
            if timed_out:break
        save_json(out/'results.json',results)
        export_answers(out,cases,results)
        STATE.update(status='BLOCKED_ACCOUNT' if blocking_error else 'STOPPED_TIMEOUT' if timed_out else 'STOPPED' if STOP.is_set() else 'COMPLETE',
            finished_at=now(),pending=len(jobs)-len(results),scientific_quality_scored=False)
        save_json(out/'completion.json',STATE)
        write_execution_status(out,jobs,results,STATE['status'])
        # Includes raw conversation/model attempts and scientific tables, not just summaries.
        buffer=io.BytesIO()
        with zipfile.ZipFile(buffer,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
            for p in sorted(out.rglob('*')):
                # Repeated deterministic, large scientific TSVs are supplied once
                # in the separately generated candidate data package.
                if p.is_file() and p.name not in ('seed_matches.tsv','seed_expression_details.tsv'):
                    z.write(p,p.relative_to(out))
        archive=buffer.getvalue();encoded=base64.b64encode(archive).decode();chunks=[encoded[i:i+6500] for i in range(0,len(encoded),6500)]
        log('ARCHIVE',{'run_id':run_id,'bytes':len(archive),'sha256':hashlib.sha256(archive).hexdigest(),'chunks':len(chunks)})
        for index,chunk in enumerate(chunks):log('CHUNK',{'run_id':run_id,'i':index,'data':chunk})
        log('DONE',STATE)
    except Exception as e:
        error=str(e);secret=locals().get('cfg',{}).get('api_key','')
        if secret:error=error.replace(secret,'[REDACTED]')
        STATE.update(status='FAILED',error=error);log('ERROR',STATE)
    finally:LOCK.release()

if __name__=='__main__':
    import argparse
    from core import config
    parser=argparse.ArgumentParser();parser.add_argument('--run-id',required=True)
    args=parser.parse_args();run(config,args.run_id)
