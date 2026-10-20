"""Verify primary publisher metadata; retain no credentials or full article text."""
import datetime, hashlib, json, re, sys, urllib.request
from pathlib import Path

out = Path(sys.argv[1])
if out.exists():
    raise SystemExit('Use a new output path')
rows = []
for url in ['https://www.nature.com/articles/s41551-025-01463-z',
            'https://www.nature.com/articles/s41551-025-01589-0']:
    row = {'url': url, 'checked_at': datetime.datetime.now(datetime.timezone.utc).isoformat()}
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=25) as response:
            raw = response.read()
            row.update(http_status=response.status, bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())
        html = raw.decode('utf-8', 'replace')
        tags = re.findall(r'<meta\b[^>]+>', html)
        row['citation_meta'] = [t for t in tags if 'citation_' in t]
        row['verification_status'] = 'METADATA_FOUND' if row['citation_meta'] else 'UNVERIFIED_NO_CITATION_METADATA'
        # Presence flags are navigation aids, not semantic verification.
        row['figure4_text_present'] = bool(re.search(r'Fig\.?\s*4', html))
        row['correction_terms_present'] = {t: t.lower() in html.lower()
            for t in ['legend', 'colour', 'color', '8 December 2025']}
    except Exception as error:
        row['error'] = str(error)
        row['verification_status'] = 'UNVERIFIED_REQUEST_FAILED'
    rows.append(row)
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps([{k: r[k] for k in ('url', 'http_status', 'error') if k in r} for r in rows]))
