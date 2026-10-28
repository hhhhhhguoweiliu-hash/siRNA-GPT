"""Manual, development-only dialogue pilot. Importing never launches a model."""
import hashlib
import io
import json
import random
import re
import zipfile
from pathlib import Path
from core import HOME,save_json,sha,now
from evaluation_protocol import evaluation_settings
from evaluation_contract import input_sha256
from evaluation_dialogue import run_dialogue,common_round
from evaluation_transport import sanitized
from model_client import account_blocked,readiness
from runtime_info import manifest

PACKAGE=HOME/'research/2026-10-27_evaluation_fixes_v2/package'
RESOURCE_ROOT=HOME
PROTOCOL='dialogue-v3'
SEED=20261027


def load_package(package=None):
    package=Path(package or PACKAGE)
    suite=json.loads((package/'runtime/cases.json').read_text(encoding='utf-8'))
    resources=json.loads((package/'runtime/resources.json').read_text(encoding='utf-8'))
    for case in suite['cases']:
        for turn in case['rounds']:common_round(turn)
    # The live tools read the fixed project resources, not an arbitrary upload.
    for rel,record in resources['files'].items():
        actual=RESOURCE_ROOT/record.get('source',rel)
        if rel=='data/expression.tsv.gz' and (not actual.is_file() or sha(actual)!=record['sha256']):
            # Frozen protocol keeps the exact old bytes; never rewrite its manifest/answers.
            actual=RESOURCE_ROOT/'data/expression_legacy_20261016.tsv.gz'
        if not actual.is_file() or sha(actual)!=record['sha256']:
            raise ValueError('工具资源版本与已审核题包不一致：'+rel)
    return suite,resources


def prepare(cfg,mode='batch',*,package=None):
    if mode not in ('batch','diagnostic'):raise ValueError('Invalid dialogue evaluation mode')
    suite,resources=load_package(package)
    cases=[c for c in suite['cases'] if c['category']!='literature_qa']
    if mode=='diagnostic':
        cases=[next(c for c in cases if c['id']=='W2b')]
        jobs=[(cases[0],'llm',1)]
    else:
        jobs=[(c,g,1) for c in cases for g in ('llm','workflow','agent')]
        random.Random(SEED).shuffle(jobs)
    schedule=[{'answer_id':'A'+str(i+1).zfill(3),'case_id':c['id'],'group':g,'repeat':n}
        for i,(c,g,n) in enumerate(jobs)]
    limits=evaluation_settings(cfg,dialogue=True)
    model_rounds={g:sum(len(c['rounds']) for c,arm,_ in jobs if arm==g) for g in ('llm','workflow','agent')}
    logical=model_rounds['llm']+model_rounds['agent']*limits['max_model_requests_per_round']
    plan={'protocol':PROTOCOL,'mode':mode,'review_status':'SEEN_DEVELOPMENT_NOT_INDEPENDENT_TEST',
        'case_ids':[c['id'] for c in cases],'qa_excluded_before_run':['Q1','Q2'],
        'planned_units':len(jobs),'planned_user_round_units':sum(len(c['rounds']) for c,_,_ in jobs),
        'technical_repeats':1,'seed':SEED,'schedule':schedule,
        'common_cases_sha256':input_sha256(cases),'resources_sha256':input_sha256(resources),
        'fact_standards_sha256':sha(Path(package or PACKAGE)/'review_only/fact_items_DRAFT.json'),
        'criteria_sha256':sha(Path(package or PACKAGE)/'review_only/criteria.json'),
        'model':cfg.get('model'),'provider':cfg.get('provider'),'api_mode':cfg.get('api_mode'),
        'effective_settings':limits,'max_logical_model_requests':logical,
        'max_http_attempts':logical*(1+limits['api_retries']),
        'max_output_tokens_across_requests':logical*limits['max_output_tokens'],
        'max_output_token_parameter_sum_all_http_attempts':logical*(1+limits['api_retries'])*limits['max_output_tokens'],
        'max_sequential_round_seconds':sum(len(c['rounds']) for c,_,_ in jobs)*limits['round_timeout_seconds'],
        'currency_cost':None,'input_token_budget':None,'actual_usage':None,
        'budget_note':'Upper bounds, not expected usage or a price quotation; output caps are per request, input varies.',
        'group_differences':['ordinary model: no scientific tools or web','fixed workflow: common conditions select a prespecified path, no model','Agent: plans and may call the same tools over multiple requests'],
        'stop_policy':'Stop the batch on account block, timeout or explicit user stop; other failed cases retained. First execution failure stops later rounds of that case.',
        'formal_unseen_task_upload_supported':False,'human_quality_scored':False}
    plan['plan_sha256']=input_sha256(plan)
    return plan,cases,resources,jobs


def preview(cfg_loader):
    cfg=cfg_loader()
    return {mode:prepare(cfg,mode)[0] for mode in ('diagnostic','batch')}


def run(cfg_loader,run_id,mode='batch',*,confirm_api_usage=False,plan_sha256='',
        execution_mode='provider',http_opener=None,package=None):
    import paper_pilot
    if confirm_api_usage is not True:raise ValueError('先确认本次实际模型用量')
    if not re.fullmatch(r'[A-Za-z0-9_-]{1,50}',run_id):raise ValueError('Invalid run ID')
    if execution_mode not in ('provider','http_fixture'):raise ValueError('Use provider or explicit HTTP fixture mode')
    cfg=cfg_loader();plan,cases,resources,jobs=prepare(cfg,mode,package=package)
    if plan_sha256!=plan['plan_sha256']:raise ValueError('待运行方案或设置已变化，请重新查看并确认用量')
    if execution_mode=='provider' and not readiness(cfg)['ready']:raise ValueError('模型配置未齐全；没有发起请求')
    out=HOME/'evaluation_runs'/run_id
    if out.exists():raise ValueError('使用新的运行目录，禁止覆盖历史记录')
    if not paper_pilot.LOCK.acquire(blocking=False):raise ValueError('另一项评价正在运行')
    created=False
    results=[];completion='FAILED';pending_reason='RUNNING'
    actual={}
    def save_status():
        rows=[]
        for item in plan['schedule']:
            r=actual.get(item['answer_id'])
            rows.append({**item,'execution':'ATTEMPTED' if r else 'NOT_EXECUTED',
                'status':r['status'] if r else 'NOT_EXECUTED','reason':None if r else pending_reason,
                'seconds':r.get('seconds') if r else None,'model_requests':r.get('real_model_requests') if r else None,
                'real_total_tokens':r.get('total_tokens') if r else None})
        save_json(out/'execution_status.json',rows)
        save_json(out/'results.json',results)
    try:
        out.mkdir(parents=True);created=True
        save_json(out/'protocol.json',{'plan':plan,'runtime':manifest(),'started_at':now(),
            'execution_mode':execution_mode,'kind':'REAL_MODEL_RUN' if execution_mode=='provider' else 'SYNTHETIC_HTTP_CHECK_NOT_MODEL_RESULT'})
        save_json(out/'cases.json',cases);save_json(out/'resources.json',resources)
        save_json(out/'private_group_key.json',plan['schedule'])
        paper_pilot.STATE.clear()
        paper_pilot.STATE.update(status='RUNNING',run_id=run_id,total=len(jobs),completed=0,protocol=PROTOCOL)
        save_status()
        completion='COMPLETE'
        for (case,group,rep),item in zip(jobs,plan['schedule']):
            if paper_pilot.STOP.is_set():completion='STOPPED';break
            r=run_dialogue(group,case,cfg,out/item['answer_id'],resources=resources,
                execution_mode=execution_mode,confirm_api_usage=True,http_opener=http_opener,
                stop_requested=paper_pilot.STOP.is_set)
            r=sanitized({**r,'answer_id':item['answer_id'],'repeat':rep,'recorded_at':now()},cfg)
            save_json(out/item['answer_id']/'result.json',r)
            actual[item['answer_id']]=r;results.append(r)
            paper_pilot.STATE.update(completed=len(results))
            diagnostics=r.get('provider_error',{})
            if account_blocked(diagnostics):completion='BLOCKED_ACCOUNT'
            elif diagnostics.get('code')=='NETWORK_TIMEOUT' or any('时限' in (x.get('error') or '') for x in r['rounds']):completion='STOPPED_TIMEOUT'
            if paper_pilot.STOP.is_set():completion='STOPPED'
            pending_reason=completion if completion!='COMPLETE' else 'RUNNING'
            save_status()
            if completion!='COMPLETE':break
    except Exception as exc:
        if not created:raise
        completion='FAILED';pending_reason='BATCH_ERROR'
        if out.exists():save_json(out/'batch_error.json',sanitized({'type':type(exc).__name__,'message':str(exc)},cfg))
    finally:
        try:
            if created:
                pending_reason=completion;save_status()
                paper_pilot.STATE.update(status=completion,run_id=run_id,completed=len(results),total=len(jobs),
                    pending=len(jobs)-len(results),finished_at=now(),scientific_quality_scored=False,protocol=PROTOCOL)
                save_json(out/'completion.json',paper_pilot.STATE)
                try:
                    if mode=='batch':
                        from dialogue_review import export_review
                        export_review(out,cases,plan,results,resources,package=package or PACKAGE,
                            fixture_only=execution_mode=='http_fixture')
                    else:save_json(out/'diagnostic_NOT_FOR_SCORING.json',{'scoring':False,'reason':'Single ordinary-model transport diagnostic, not a three-arm task comparison'})
                except Exception as exc:
                    save_json(out/'review_export_error.json',sanitized({'message':str(exc)},cfg))
                    paper_pilot.STATE.update(status='FAILED',review_export_failed=True)
                    save_json(out/'completion.json',paper_pilot.STATE)
                # Full owner archive; the reviewer ZIP has its own smaller surface.
                memory=io.BytesIO()
                with zipfile.ZipFile(memory,'w',zipfile.ZIP_DEFLATED) as z:
                    for p in sorted(out.rglob('*')):
                        if p.is_file():z.write(p,p.relative_to(out))
                archive=memory.getvalue();(out.parent/(run_id+'.zip')).write_bytes(archive)
                paper_pilot.log('ARCHIVE',{'run_id':run_id,'bytes':len(archive),'sha256':hashlib.sha256(archive).hexdigest()})
                # Reuse the established private-log recovery convention for temporary hosting.
                import base64
                encoded=base64.b64encode(archive).decode()
                for i in range(0,len(encoded),6500):paper_pilot.log('CHUNK',{'run_id':run_id,'i':i//6500,'data':encoded[i:i+6500]})
                paper_pilot.log('DONE',paper_pilot.STATE)
        finally:
            paper_pilot.LOCK.release()
    return dict(paper_pilot.STATE)
