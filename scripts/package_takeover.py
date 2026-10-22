"""Bundle code and audited results with hashes and a verified ZIP CRC."""
import argparse,hashlib,json,subprocess,sys,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from core import config

def main():
    p=argparse.ArgumentParser();p.add_argument('--batch',required=True);p.add_argument('--output',required=True);a=p.parse_args()
    batch=Path(a.batch).resolve();out=Path(a.output).resolve()
    assert ROOT in batch.parents and ROOT in out.parents and not out.exists()
    local_exclusions=('historical_export_check','plot-install.txt','render_attempt_')
    files={ROOT/n for n in subprocess.check_output(['git','ls-files'],cwd=ROOT,text=True).splitlines()}
    files.update(path for path in batch.rglob('*') if path.is_file())
    files={path for path in files if path.is_file() and not (batch in path.parents and
        any(part.startswith(local_exclusions) for part in path.relative_to(batch).parts))}
    files.discard(batch/'manifest.json')
    secret=config().get('api_key','').encode()
    entries=[]
    for path in sorted(files):
        assert ROOT in path.resolve().parents
        raw=path.read_bytes()
        if len(secret)>=8 and secret in raw:raise SystemExit('Secret detected; package not written')
        entries.append({'path':path.relative_to(ROOT).as_posix(),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()})
    manifest={'code_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        'batch':batch.relative_to(ROOT).as_posix(),'files':entries,'excluded_local_trials':'historical_export_check*, render_attempt_* and installation log remain local; real failed research batches retained'}
    (batch/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    files.add(batch/'manifest.json');out.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(out,'x',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for path in sorted(files):z.write(path,path.relative_to(ROOT))
    with zipfile.ZipFile(out) as z:assert z.testzip() is None
    receipt={'archive':out.name,'bytes':out.stat().st_size,'sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'zip_crc':'PASS','files':len(files)}
    out.with_suffix('.receipt.json').write_text(json.dumps(receipt,indent=2),encoding='utf-8')
    print(json.dumps(receipt))

if __name__=='__main__':main()
