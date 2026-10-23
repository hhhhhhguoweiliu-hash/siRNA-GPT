"""Generate a non-circular file manifest after evidence and docs are final."""
import hashlib
import json
from pathlib import Path

root = Path(__file__).resolve().parent
files = []
for p in sorted(root.rglob('*')):
    if p.is_file() and p.name != 'manifest.json' and '__pycache__' not in p.parts:
        h = hashlib.sha256()
        with p.open('rb') as f:
            for chunk in iter(lambda: f.read(4*1024*1024), b''):
                h.update(chunk)
        files.append({'path': p.relative_to(root).as_posix(), 'bytes': p.stat().st_size, 'sha256': h.hexdigest()})
audit = json.loads((root / 'audit_result.json').read_text(encoding='utf-8'))
assert audit['failures'] == [] and audit['raw_candidates'] == 104 and len(audit['retained']) == 9
assert audit['seed_raw_rows'] == 1397880
sources = json.loads((root / 'official_reference_check/receipt.json').read_text(encoding='utf-8'))
assert all(r['status'] == 'FETCHED' for r in sources)
assert all(r.get('matches_recovered_bytes', True) for r in sources)
assert all(all(r.get('release_source_comparison', {}).values()) for r in sources)
result = {'takeover_main': audit['takeover_main'], 'kind': 'provenance_audit_not_new_scientific_inference',
          'historical_54_raw_sha256': '55664e58cea8181046ddc73c3740b73960589380d02b95719f3c6c0e1334e505',
          'files': files, 'manifest_self_excluded': True}
(root / 'manifest.json').write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
print('Manifest:', len(files), 'files. Audit failures:', len(audit['failures']))
