"""Copy version-checked scientific reference files for independent reviewers."""
import argparse,hashlib,json,zipfile
from pathlib import Path

def package(protocol_path,output):
    protocol=json.loads(Path(protocol_path).read_text(encoding='utf-8'))
    files={name:Path(name).read_bytes() for name in protocol['runtime']['assets'] if name.startswith('data/')}
    for name,raw in files.items():
        assert hashlib.sha256(raw).hexdigest()==protocol['runtime']['assets'][name],name+' differs from runtime'
    # Optional report annotations are also source data, not newly measured evidence.
    for name in ('data/historical_near_matches.tsv','data/utr_gene_map.tsv'):
        files[name]=Path(name).read_bytes()
    manifest={name:{'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),
        'runtime_hash_verified':name in protocol['runtime']['assets']} for name,raw in files.items()}
    explanation='''# Scientific references for the unscored review

These are complete shared source tables, not newly measured experimental results.
The six scientific assets recorded in the batch protocol are byte-checked against that runtime manifest.
The two supplementary report-annotation tables are copied from the matching source checkout; their hashes are recorded separately.
OligoFormer scores and seed matches are imported historical official outputs; no new heavy inference is claimed.
The expression table is untreated ARPE-19 baseline (one culture run; four vessels per oxygen state), not siRNA perturbation evidence.

The cloud archive excludes repeated seed_matches.tsv and seed_expression_details.tsv to avoid many duplicate large tables.
The complete underlying seed and expression source tables are supplied here once, with provenance and hashes.
Actual tool summaries, inputs and original answers for each answer_id remain in that answer's evidence.json.
These reference files are for checking evidence; they were NOT supplied as computed results to the no-tool model.
This package contains no group key, configuration, credentials, reviewer identity or filled scores.
'''
    target=Path(output);assert not target.exists(),'Use a new output file'
    target.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED) as z:
        for name,raw in files.items():z.writestr(name,raw)
        z.writestr('manifest.json',json.dumps(manifest,indent=2))
        z.writestr('README.md',explanation)
    with zipfile.ZipFile(target) as z:assert z.testzip() is None
    receipt={'bytes':target.stat().st_size,'sha256':hashlib.sha256(target.read_bytes()).hexdigest(),
        'source_runtime_commit':protocol['runtime']['commit'],'files':manifest,'contains_group_key':False}
    target.with_suffix('.receipt.json').write_text(json.dumps(receipt,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in receipt.items() if k!='files'}))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--protocol',required=True);p.add_argument('--output',required=True)
    a=p.parse_args();package(a.protocol,a.output)
