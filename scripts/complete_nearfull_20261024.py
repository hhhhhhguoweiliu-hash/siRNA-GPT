"""Append the exact uncompleted 240 queries; never overwrite earlier computation."""
import csv, datetime, gzip, hashlib, json, os, subprocess, time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PRIOR = ROOT / 'research/2026-10-24_candidate_v2'
OUT = ROOT / 'research/2026-10-24_nearfull_complete'
LEGACY = Path(r'C:\Users\86182\.codex\.chatgpt-projects\g-p-6a82e08661e081919f3434650ae4f35c\analysis\ARPE19_candidates_20261016')
KEY = ('candidate_id', 'strand_role', 'query_kind')

def read(path):
    with (gzip.open if str(path).endswith('.gz') else open)(path, 'rt', encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f, delimiter='\t'))

def key(row): return tuple(row[k] for k in KEY)
def sha(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for block in iter(lambda: f.read(4*1024*1024), b''): h.update(block)
    return h.hexdigest()
def save(name, value):
    (OUT/name).write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n', encoding='utf-8', newline='\n')
def write(name, rows):
    with (OUT/name).open('w', encoding='utf-8-sig', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]), delimiter='\t'); w.writeheader(); w.writerows(rows)

def main():
    OUT.mkdir(exist_ok=True)
    if (OUT/'execution.json').exists(): raise SystemExit('Existing execution must be preserved')
    plan = read(PRIOR/'inputs/nearfull_all_264.tsv')
    assert len(plan) == len({key(r) for r in plan}) == 264
    completed = {}
    for phase in ['nearfull_pilot', 'nearfull_CDS_remaining']:
        rows = read(PRIOR/phase/'summary.tsv')
        for k in {key(r) for r in rows}:
            ss = [r for r in rows if key(r) == k]
            assert len(ss) == 3 and {int(r['max_mismatches']) for r in ss} == {0,1,2}
            assert all(r['status'] == 'COMPLETED' for r in ss)
            raw = PRIOR/phase/('__'.join(k)+'__hits.tsv.gz')
            assert raw.exists() and k not in completed
            read(raw)  # gzip CRC/read and header validation, including zero-hit files
            completed[k] = {'source_phase': phase, 'raw_sha256': sha(raw)}
    assert len(completed) == 24 and set(completed).issubset({key(r) for r in plan})
    remaining = [r for r in plan if key(r) not in completed]
    assert len(remaining) == len({key(r) for r in remaining}) == 240
    obsolete = {key(r) for r in read(PRIOR/'inputs/nearfull_remaining_256.tsv')}
    assert len(obsolete & set(completed)) == 16
    write('remaining_240.tsv', remaining)
    write('plan_264_initial_states.tsv', [{**r, 'actual_status': 'COMPLETED_PRIOR' if key(r) in completed else 'NOT_RUN', 'source_phase': completed.get(key(r),{}).get('source_phase','new_240')} for r in plan])
    assets = json.loads((PRIOR/'input_assets.json').read_text(encoding='utf-8'))
    evidence = []
    for a in assets:
        if a['path'].endswith(('refseq_all_transcripts.fasta','refseq_all_transcript_gene_loci.tsv','get_seed.R','SeedMatchR.R')):
            p=Path(a['path']); actual=sha(p)
            assert actual == a['sha256']
            evidence.append({'path':str(p),'bytes':p.stat().st_size,'sha256':actual,'matches_prior':True})
    worker=ROOT/'scripts/candidate_v2_match.R'
    evidence.append({'path':str(worker),'sha256':sha(worker),'role':'unchanged IO adapter'})
    save('input_and_reference_manifest.json', evidence)
    save('plan_reconciliation.json', {'started_from_commit':'dbb8a2d','planned':264,'previously_completed_unique':24,'remaining_unique':240,'obsolete_256_already_completed':16,'same_query_parameters':{'max_mismatch':2,'with_indels':False,'fixed':True,'windows':['paired_core19','sidirect_g2g20'],'strands':['guide','passenger']},'new_model_or_seed_runs':0,'previous_completed':[{'key':list(k),**v} for k,v in completed.items()]})
    cmd=[r'C:\Program Files\R\R-4.3.1\bin\Rscript.exe',str(worker),str(LEGACY),str(OUT/'remaining_240.tsv'),str(OUT/'new_240'),'nearfull']
    start=datetime.datetime.now(datetime.timezone.utc).isoformat(); clock=time.perf_counter()
    receipt={'status':'RUNNING','started_utc':start,'command':cmd,'cwd':str(ROOT),'timeout_seconds':7200,'scope':'Exactly remaining 240; old 24 reused, no OligoFormer/seed/API execution'}
    save('execution.json',receipt)
    env=os.environ.copy();env['PYTHONDONTWRITEBYTECODE']='1'
    code=None;status='RETURNED'
    with (OUT/'execution.log').open('wb') as log:
        try: code=subprocess.run(cmd,cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=7200).returncode
        except subprocess.TimeoutExpired: status='TIMED_OUT_PROCESS_STOPPED'
    receipt.update(status=status,exit_code=code,finished_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),wall_seconds=time.perf_counter()-clock)
    save('execution.json',receipt)
    print(json.dumps(receipt,ensure_ascii=False))
    raise SystemExit(0 if code == 0 else 1)

if __name__ == '__main__': main()
