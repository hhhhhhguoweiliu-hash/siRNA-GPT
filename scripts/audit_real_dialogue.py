"""Read actual provider records and package them; never assign semantic scores."""
import collections
import hashlib
import json
import re
import shutil
import sys
import zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from core import save_json
from review_import import import_workbooks

BASE=ROOT/'research/2026-10-27_real_dialogue_mini'


def load(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    authorization=load(BASE/'authorization.json');run=ROOT/'evaluation_runs'/authorization['run_ids']['batch']
    rows=load(run/'results.json');protocol=load(run/'protocol.json');plan=protocol['plan'];status=load(run/'execution_status.json')
    assert len(rows)==len(status)==len(plan['schedule'])==27
    assert all(r['execution']=='ATTEMPTED' for r in status)
    assert all(r['execution_mode']=='provider' and r['record_kind']=='REAL_EVALUATION_ATTEMPT_NOT_HUMAN_SCORED' for r in rows)
    actual={r['answer_id']:r for r in rows}
    for item in plan['schedule']:
        r=actual[item['answer_id']]
        assert (r['case_id'],r['group'],r['repeat'])==(item['case_id'],item['group'],item['repeat'])
    common=[];requests=[];usages=[]
    for cid in plan['case_ids']:
        same=[r for r in rows if r['case_id']==cid]
        assert len(same)==3 and len({r['input_sha256'] for r in same})==1
        assert len({r['resource_access']['resources_sha256'] for r in same})==1
        for n in range(len(same[0]['rounds'])):assert len({r['rounds'][n]['common_input_sha256'] for r in same})==1
        common.append({'case_id':cid,'same_complete_common_input':True,'same_tool_resource_version':True,'user_rounds':len(same[0]['rounds'])})
    expected_model='doubao-seed-2-0-mini-260428'
    for r in rows:
        assert not r['quality_scored']
        if r['group']=='workflow':assert r['real_model_requests']==0;continue
        for path in sorted((run/r['answer_id']/'model_transport').glob('*/http_attempt_*.json')):
            record=load(path);events=record['events'];start=next(e for e in events if e['event']=='attempt_started')
            response=next(e for e in events if e['event']=='response_received')
            req=start['request'];raw=response['response']
            assert req['model']==expected_model and req['max_output_tokens']==1800 and req['thinking']=={'type':'disabled'}
            assert raw['model']==expected_model and raw['status']=='completed' and raw.get('incomplete_details') in (None,{})
            assert record['status']=='SUCCEEDED'
            if r['group']=='llm':assert not req.get('tools')
            usages.append(raw['usage']['total_tokens'])
            requests.append({'answer_id':r['answer_id'],'case_id':r['case_id'],'group':r['group'],
                'record':path.relative_to(run).as_posix(),'request_id':response.get('request_id'),
                'returned_model':raw['model'],'usage':raw['usage'],'seconds':response.get('seconds')})
    assert len(requests)==sum(r['real_model_requests'] for r in rows)==62
    assert sum(usages)==sum(r['total_tokens'] for r in rows)==505264
    assert sum(len(r['rounds']) for r in rows)==33
    sourcebook=ROOT/'research/2026-10-27_evaluation_entry/planned_review_blank_27.xlsx'
    imported=import_workbooks(load(run/'analysis_plan.json'),load(run/'actual_execution.json'),[sourcebook])
    assert imported['reviews']==[]
    with zipfile.ZipFile(run/'reviewer_package.zip') as z:
        assert z.testzip() is None
        assert not any('private_group' in n or 'http_attempt_' in n for n in z.namelist())
    raw=BASE/'raw';raw.mkdir(exist_ok=True)
    copies={raw/'model_and_tool_records_original.zip':run.parent/(run.name+'.zip'),
        raw/'anonymous_reviewer_package_original.zip':run/'reviewer_package.zip',
        raw/'results_original.json':run/'results.json',raw/'protocol_original.json':run/'protocol.json',
        raw/'execution_status_original.json':run/'execution_status.json',raw/'cases_original.json':run/'cases.json',
        raw/'analysis_plan_original.json':run/'analysis_plan.json',raw/'actual_execution_original.json':run/'actual_execution.json',
        raw/'private_group_key_DO_NOT_SEND_REVIEWERS.json':run/'private_group_key.json',
        raw/'review_form_blank_matched.xlsx':sourcebook}
    receipts=[]
    for target,source in copies.items():
        if target.exists():assert target.read_bytes()==source.read_bytes()
        else:shutil.copyfile(source,target)
        receipts.append({'saved':target.relative_to(BASE).as_posix(),'source':source.relative_to(ROOT).as_posix(),'bytes':target.stat().st_size,'sha256':sha(target)})
    # A concrete credential pattern scan, not a claim that hashes prove scientific correctness.
    patterns=[re.compile(rb'ark-[a-zA-Z0-9-]{30,}'),re.compile(rb'Bearer\s+(?!\[REDACTED\])[A-Za-z0-9._-]{20,}')]
    checked=0
    for path in [*run.rglob('*.json'),*run.rglob('*.txt'),*BASE.glob('*.json')]:
        content=path.read_bytes();assert not any(p.search(content) for p in patterns),'Credential pattern found in '+str(path)
        checked+=1
    for path in (raw/'model_and_tool_records_original.zip',raw/'anonymous_reviewer_package_original.zip'):
        with zipfile.ZipFile(path) as z:
            assert z.testzip() is None
            for member in z.infolist():
                if member.filename.endswith(('.json','.txt','.jsonl')):
                    assert not any(p.search(z.read(member)) for p in patterns),'Credential pattern found in archive member'
                    checked+=1
    connection=load(BASE/'connection_result.json')
    report={'kind':'REAL_PROVIDER_EXECUTION_EVIDENCE_NOT_HUMAN_GRADING','model':expected_model,'run_id':run.name,
        'planned_units':27,'attempted_units':27,'pending_units':0,'user_round_units':33,
        'model_requests_in_batch':len(requests),'provider_reported_total_tokens_in_batch':sum(usages),
        'http_retries_in_batch':sum(r.get('http_retries',0) for r in rows),
        'separate_connection_check_requests':connection['transport_summary']['real_model_requests'],
        'separate_connection_check_tokens':connection['transport_summary']['total_tokens'],
        'currency_cost':None,'currency_note':'Provider-returned token counts retained; no unverified pricing conversion',
        'software_status_counts_NOT_accuracy':dict(collections.Counter(r['status'] for r in rows)),
        'common_input_and_resources':common,'requests':requests,'raw_file_copies':receipts,
        'human_scientific_scores_filled':0,'independent_unseen_tasks':False,'production_website_updated':False,
        'heavy_scientific_recomputation':False,'credential_pattern_scan_files':checked,'credential_pattern_matches':0}
    save_json(BASE/'actual_run_audit.json',report)
    print('PASS: 27 actual units / 33 user rounds; 62 real provider requests and 505264 tokens verified against raw responses; all grades remain blank; complete evidence saved.')


if __name__=='__main__':main()
