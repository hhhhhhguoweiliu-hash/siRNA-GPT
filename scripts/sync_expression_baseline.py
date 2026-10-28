"""Package verified gene representatives + original per-vessel TPM; never sum features."""
import argparse, csv, gzip, hashlib, io, json, shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SAMPLES = ['Nor1','Nor2','Nor3','Nor4','Hyp1','Hyp2','Hyp3','Hyp4']

def digest(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):
    with p.open(encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f, delimiter='\t'))

def main(workspace):
    background=workspace/'analysis_redraw_20261028_v3/tables/expression_background_v3.tsv'
    original=workspace/'analysis_stage1_20261017/inputs/tpm_all_features.tsv'
    mapping=read(background); tpm={r['feature_id']:r for r in read(original)}
    assert len({r['ENTREZID'] for r in mapping})==len(mapping), 'Nonunique Entrez mapping'
    rows=[]
    for r in mapping:
        values={s:float(tpm[r['feature_id']][s]) for s in SAMPLES}
        for state,prefix in [('Normoxia','Nor'),('Hypoxia','Hyp')]:
            v=[values[prefix+str(i)] for i in range(1,5)]
            assert abs(sum(v)/4-float(r['TPM_'+state+'_mean']))<1e-5
            assert sum(x>=1 for x in v)==int(r[state+'_n_TPM_ge1'])
        rows.append({**r,**values})
    target=ROOT/'data/expression.tsv.gz'
    legacy=ROOT/'data/expression_legacy_20261016.tsv.gz'
    if target.exists() and not legacy.exists():shutil.copy2(target,legacy)
    buf=io.StringIO(newline='');writer=csv.DictWriter(buf,fieldnames=list(rows[0]),delimiter='\t',lineterminator='\n')
    writer.writeheader();writer.writerows(rows)
    with target.open('wb') as f:
        with gzip.GzipFile(filename='',mode='wb',fileobj=f,mtime=0) as z:z.write(buf.getvalue().encode('utf-8'))
    provenance={'version':'ARPE19_TPM_verified_v3_20261028','label':'ARPE-19逐样本TPM与2026-10-28核验映射',
        'source':'PACKAGED_PROJECT_DATA','rows':len(rows),'sha256':digest(target),'samples':SAMPLES,
        'scope':'同一培养批次，每状态4皿；未转染；缺氧1% O2 24h；全部8样本保留',
        'per_sample_tpm_available_in_packaged_table':True,'ranking_changed':False,
        'sources':[{'path':str(p),'sha256':digest(p)} for p in (background,original)],
        'mapping_rules':'Retain verified unique Entrez-to-feature representatives from v3; no suffix stripping, summing or minimum-p selection; exact-coordinate alias corrections retained.',
        'mapping_evidence':'expression_mapping_evidence/','legacy_sha256':digest(legacy),
        'limitations':['Counts software/command and complete reference FASTA/GTF provenance remain unconfirmed.',
                      'TPM is baseline annotation only, not siRNA response, risk weights or reranking.']}
    evidence=ROOT/'data/expression_mapping_evidence';evidence.mkdir(exist_ok=True)
    for rel in ['tables/annotation_overrides_evidence.tsv','references/NCBI_gene_summary_mapping_overrides.json']:
        p=workspace/'analysis_redraw_20261028_v3'/rel
        if p.is_file():shutil.copy2(p,evidence/p.name)
    (ROOT/'data/expression_provenance.json').write_text(json.dumps(provenance,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'rows':len(rows),'sha256':digest(target),'bytes':target.stat().st_size}))

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--workspace',type=Path,required=True)
    main(parser.parse_args().workspace)
