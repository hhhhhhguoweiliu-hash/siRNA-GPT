"""Audit immutable handoff records and a newly rebuilt offline batch. No API."""
import argparse,collections,csv,gzip,hashlib,json,platform,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from core import read_tsv,save_json

def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def table(path,rows):
    with path.open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]),delimiter='\t');w.writeheader();w.writerows(rows)

def main():
    p=argparse.ArgumentParser();p.add_argument('--batch',required=True);a=p.parse_args()
    batch=Path(a.batch).resolve()
    m=json.loads((ROOT/'research/manifest.json').read_text(encoding='utf-8'))
    for row in m['files']:
        path=(ROOT/row['path']).resolve()
        assert ROOT in path.parents and path.is_file() and digest(path)==row['sha256'],row['path']
    old=ROOT/'research/2026-10-19_evaluation/raw'
    with gzip.open(old/'results.json.gz','rt',encoding='utf-8') as f:records=json.load(f)
    protocol=json.loads((old/'protocol.json').read_text(encoding='utf-8'))
    keys=lambda r:(r['case_id'],r['group'],r['repeat'])
    assert len(records)==54 and len({keys(r) for r in records})==54
    assert len({r['answer_id'] for r in records})==54
    assert [keys(r) for r in records]==[keys(r) for r in protocol['scheduled_order']]
    assert all(sum(r['case_id']==c['id'] and r['group']==g for r in records)==3
        for c in json.loads((ROOT/'evaluation_cases.example.json').read_text(encoding='utf-8'))['cases']
        for g in ['llm','workflow','agent'])
    blocked=[r for r in records if 'SetLimitExceeded' in json.dumps(r)]
    assert len(blocked)==36 and all(r.get('tool_calls',0)==0 for r in blocked if r['group']=='agent')
    data_assets={n:digest(ROOT/n)==sha for n,sha in protocol['runtime']['assets'].items() if n.startswith('data/')}
    assert all(data_assets.values())
    counts=collections.Counter((r['group'],r['status']) for r in records)
    table(batch/'historical_status.tsv',[{'group':g,'status':s,'records':n} for (g,s),n in sorted(counts.items())])
    new=json.loads((batch/'workflow_check/results.json').read_text(encoding='utf-8'))
    assert len(new)==6 and len({r['case_id'] for r in new})==6
    assert all(r['group']=='workflow' and not r.get('usage') for r in new)
    for r in new:
        saved=json.loads((batch/'workflow_check'/r['answer_id']/'result.json').read_text(encoding='utf-8'))
        assert saved==r
    table(batch/'workflow_summary.tsv',[{k:r.get(k) for k in ['answer_id','case_id','status','tool_calls','seconds','total_tokens']} for r in new])
    reports=list((batch/'candidate_report').glob('*/candidates_ranked.tsv'))
    assert len(reports)==1
    current=read_tsv(reports[0]);previous=read_tsv(ROOT/'research/2026-10-19_scientific/data/candidate_evidence.tsv')
    assert current==previous,'Candidate evidence changed'
    raw_tpm=read_tsv(ROOT/'research/2026-10-19_scientific/data/VEGFA_eight_samples_TPM.tsv')
    tpm_means={state:sum(float(r['TPM']) for r in raw_tpm if r['state']==state)/4 for state in ['Normoxia','Hypoxia']}
    report=json.loads(reports[0].with_name('report.json').read_text(encoding='utf-8'))
    probe=json.loads((batch/'model_connection.json').read_text(encoding='utf-8'))
    summary={'checked_in_manifest_files_verified':len(m['files']),'historical_entries':len(records),
        'unique_answer_ids':54,'historical_schedule_and_6x3x3_coverage_verified':True,
        'historical_account_limit_entries':len(blocked),'historical_blocked_agent_scientific_calls':0,
        'scientific_data_assets_equal_to_historical_batch':data_assets,
        'new_workflow_entries':len(new),'new_workflow_statuses':dict(collections.Counter(r['status'] for r in new)),
        'candidate_evidence_all_9_rows_equal_to_handoff':True,
        'selected_for_review':report['selected_for_review'],'baseline_VEGFA_TPM_means':tpm_means,
        'model_probe':{'status':probe['status'],'provider_code':probe.get('provider_code'),'http_status':probe.get('http_status')},
        'production_model_state':'NOT_TESTED_AUTH_REQUIRED','true_auto_case_run':False,'new_three_arm_batch_run':False,
        'scientific_accuracy_scored':False,'scientific_mode':'verified historical imports; no heavy inference',
        'environment':{'python':platform.python_version(),'platform':platform.platform()},
        'source_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        'branch':subprocess.check_output(['git','branch','--show-current'],cwd=ROOT,text=True).strip()}
    save_json(batch/'audit_summary.json',summary)
    print(json.dumps(summary,ensure_ascii=True))

if __name__=='__main__':main()
