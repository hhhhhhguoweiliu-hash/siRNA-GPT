"""Manual-gated library demonstrations, separate from old evaluations."""
import io
import json
import zipfile
import base64,hashlib
from pathlib import Path
from core import HOME,save_json,now
from conversation import Conversation
from model_client import ModelError,account_blocked
from literature import get_library

STATE={'status':'IDLE','run_id':None,'completed':0,'total':2}
QUESTIONS=[('B02','OligoFormer分数超过1可以解释为超过100%的敲低率吗？'),
           ('B08','请给出本项目已经测得的人类患者视力改善百分比和临床给药剂量。')]
DAY7_REGRESSION=[('B11_day7','VEGFA_SD_3499在ARPE-19转染后第7天实测敲低率是多少？')]


def run(cfg_loader,identity,mode='two_question'):
    if mode not in ('two_question','day7_regression'):raise ValueError('Invalid library demo mode')
    questions=DAY7_REGRESSION if mode=='day7_regression' else QUESTIONS
    STATE['total']=len(questions)
    cfg=cfg_loader();secret=cfg.get('api_key','')
    def clean(value):
        text=json.dumps(value,ensure_ascii=False)
        return json.loads(text.replace(secret,'[REDACTED]') if secret else text)
    path=HOME/'literature_runs'/identity
    path.mkdir(parents=True,exist_ok=False)
    records=[{'id':key,'question':q,'status':'NOT_STARTED'} for key,q in questions]
    protocol={'kind':'MANUALLY_CONFIRMED_MINIMAL_LIBRARY_DEMO','started_at':now(),
        'questions':records,'mode':mode,'library_version':get_library().version(),'external_search':False,
        'not_old_54_evaluation':True,'no_independent_scores':True,
        'no_evidence_question_may_stop_without_model_call':True}
    save_json(path/'protocol.json',protocol)
    (path/'library.zip').write_bytes(get_library().export_bundle())
    c=Conversation(cfg_loader=cfg_loader,root=path/'conversation')
    status='COMPLETE'
    try:
        for record in records:
            record.update(status='RUNNING',started_at=now())
            save_json(path/'results.json',records)
            c.add('user',record['question'],mode='qa')
            try:
                c.answer(record['question'],web_enabled=False,literature_only=True)
                record.update(status='COMPLETED',answer=clean(c.messages[-1]['text']),audit_id=c.current_audit['id'],
                    answer_status=c.current_audit.get('status'),citation_check=c.current_audit.get('citation_check'),
                    model_calls=c.current_audit.get('model_call_count',len(c.current_audit.get('model_calls',[]))),
                    usage=[call.get('usage',{}) for call in c.current_audit.get('model_calls',[])],finished_at=now())
            except Exception as error:
                message=clean(str(error))
                record.update(status='FAILED',error=message,finished_at=now())
                if isinstance(error,ModelError):record['diagnostics']=clean(error.diagnostics())
                if c.current_audit:
                    c.current_audit.update(status='failed',error=message);c.save_audit()
                status='BLOCKED_ACCOUNT' if isinstance(error,ModelError) and account_blocked(error.diagnostics()) else 'FAILED'
                break  # No account retries, no next question after a failed API exchange.
            finally:
                save_json(path/'results.json',records)
                save_json(path/'conversation_record.json',clean(c.export_record()))
            STATE['completed']+=1
    except Exception as error:
        status='FAILED';save_json(path/'failure.json',{'error':clean(str(error)),'time':now()})
    finally:
        if status=='COMPLETE' and any(r.get('answer_status')=='citation_warning' for r in records):status='COMPLETE_WITH_WARNINGS'
        STATE.update(status=status,run_id=identity,records=records,finished_at=now())
        save_json(path/'status.json',STATE)
        # Small chunked export, using the same service-log receipt mechanism as C06.
        raw=export_zip();encoded=base64.b64encode(raw).decode('ascii')
        parts=[encoded[i:i+6000] for i in range(0,len(encoded),6000)]
        print('LIBRARY_DEMO_ARCHIVE '+json.dumps({'run_id':identity,'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),'chunks':len(parts)}),flush=True)
        for i,value in enumerate(parts):print('LIBRARY_DEMO_CHUNK '+json.dumps({'run_id':identity,'i':i,'data':value}),flush=True)


def export_zip():
    identity=STATE.get('run_id')
    if not identity or STATE.get('status') in ('IDLE','RUNNING'):
        raise ValueError('文库演示尚未结束。')
    path=HOME/'literature_runs'/identity
    memory=io.BytesIO()
    with zipfile.ZipFile(memory,'w',zipfile.ZIP_DEFLATED) as z:
        for p in sorted(path.rglob('*')):
            if p.is_file():z.write(p,p.relative_to(path))
    return memory.getvalue()
