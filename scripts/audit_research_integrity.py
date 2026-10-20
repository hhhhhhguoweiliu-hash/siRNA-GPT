"""Recheck original evidence and coverage without replacing missing data or assigning quality scores."""
import argparse, collections, csv, hashlib, io, json, zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
    return h.hexdigest()
def read(path):return json.loads(path.read_text(encoding='utf-8-sig'))
def table(path):
    with path.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f,delimiter='\t'))

def main():
    p=argparse.ArgumentParser();p.add_argument('--vendor-tpm',required=True);p.add_argument('--output',required=True);a=p.parse_args()
    out=Path(a.output)
    if out.exists():raise SystemExit('Use a new output path')
    pinned=read(ROOT/'research/manifest.json')['files']
    for item in pinned:assert sha(ROOT/item['path'])==item['sha256'],item['path']
    vendor=Path(a.vendor_tpm);matches=[]
    with vendor.open(encoding='utf-8-sig',newline='') as f:
        reader=csv.DictReader(f,delimiter='\t');gene_column=reader.fieldnames[0]
        for row in reader:
            if row[gene_column]=='VEGFA':matches.append(row)
    assert len(matches)==1
    expected={r['sample']:float(r['TPM']) for r in table(ROOT/'research/2026-10-19_scientific/data/VEGFA_eight_samples_TPM.tsv')}
    assert set(expected)=={'Nor1','Nor2','Nor3','Nor4','Hyp1','Hyp2','Hyp3','Hyp4'}
    assert all(float(matches[0][name])==value for name,value in expected.items())
    means={s:sum(v for n,v in expected.items() if n.startswith(s))/4 for s in ['Nor','Hyp']}
    score={r['candidate_id']:r for r in table(ROOT/'data/historical_scores.tsv')}
    ranked=table(ROOT/'research/2026-10-19_scientific/data/candidate_evidence.tsv')
    assert len(ranked)==len(score)==9
    assert all(r['guide_core19_5to3']==score[r['candidate_id']]['guide_core19_5to3'] and
        float(r['score'])==float(score[r['candidate_id']]['oligoformer_scaled_score']) for r in ranked)
    base=ROOT/'research/2026-10-20_takeover'
    checks=[]
    for name in ['auto_case/tools.zip','three_arm_original.zip']:
        with zipfile.ZipFile(base/name) as z:assert z.testzip() is None
        checks.append({'path':str((base/name).relative_to(ROOT)),'sha256':sha(base/name),'CRC':'PASS'})
    with zipfile.ZipFile(base/'three_arm_original.zip') as z:
        records=json.loads(z.read('results.json'));protocol=json.loads(z.read('protocol.json'))
        key=lambda r:(r['case_id'],r['group'],r['repeat'])
        assert len(records)==54 and len({key(r) for r in records})==54
        assert [key(r) for r in records]==[key(r) for r in protocol['scheduled_order']]
        assert all(r==json.loads(z.read(r['answer_id']+'/result.json')) for r in records)
    auto=read(base/'auto_case/conversation.json')
    assert auto['result']['status']=='COMPLETE'
    assert set(auto['scientific_run']['tool_results'])=={'inspect_candidates','verify_target','score_candidates','match_seed','query_expression','compile_report'}
    assert auto['scientific_run']['tool_results']['score_candidates']['status']=='IMPORTED_HISTORICAL'
    assert auto['scientific_run']['tool_results']['match_seed']['status']=='IMPORTED_HISTORICAL'
    availability=read(base/'three_arm/evidence_audit.json')
    summary={'pinned_history_files_verified':len(pinned),'vendor_TPM_file':str(vendor),'vendor_TPM_sha256':sha(vendor),
        'VEGFA_original_vendor_row':matches[0],'sample_values_verified':8,'baseline_means_TPM':means,
        'baseline_scope':'one culture run, four separate dishes per oxygen state, untreated; not paired',
        'candidate_rows_present_and_consistent':9,'heavy_tool_rerun_this_session':False,
        'historical_model_execution_independently_replayed':False,
        'historical_output_limit':'Archive consistency verified, not independent replay of upstream weights/reference execution',
        'Auto_full_six_tool_case_verified':True,'Auto_semantic_quality_independently_scored':False,
        'new_pilot_records_and_per_case_exports_verified':54,'independent_development_tasks':6,
        'per_case_available_repeats':availability['per_case_available_repeats'],
        'full_quality_comparison_ready':False,'independent_expert_scoring_done':False,'new_wet_lab_done':False,
        'archives':checks,'truth_boundary':'File integrity and reproduced arithmetic do not by themselves authenticate physical laboratory work or prove model interpretation correct.'}
    out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in summary.items() if k not in ['VEGFA_original_vendor_row','archives']},ensure_ascii=True))

if __name__=='__main__':main()
