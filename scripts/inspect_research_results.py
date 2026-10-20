"""Read-only inspection of the checked-in research handoff; no API calls."""
from pathlib import Path
import collections,gzip,hashlib,json,sys
ROOT=Path(__file__).resolve().parents[1]
manifest=ROOT/'research/manifest.json'
if not manifest.is_file():raise SystemExit('Missing research/manifest.json')
m=json.loads(manifest.read_text(encoding='utf-8'))
for entry in m['files']:
    p=(ROOT/entry['path']).resolve()
    if ROOT not in p.parents:raise SystemExit('Invalid manifest path')
    if not p.is_file() or hashlib.sha256(p.read_bytes()).hexdigest()!=entry['sha256']:
        raise SystemExit('File missing or changed: '+entry['path'])
path=ROOT/'research/2026-10-19_evaluation/raw/results.json.gz'
with gzip.open(path,'rt',encoding='utf-8') as f:results=json.load(f)
print('Verified files:',len(m['files']))
print('Recorded scheduled entries:',len(results))
print('Raw statuses:',dict(collections.Counter((r['group']+':'+r['status']) for r in results)))
blocked=0
for r in results:
    error=(r.get('record',{}).get('result') or {})
    blocked+=error.get('provider_code')=='SetLimitExceeded' or 'SetLimitExceeded' in r.get('answer','')
print('Account-limit blocked entries:',blocked)
print('This batch does NOT establish three-arm scientific accuracy or superiority.')
