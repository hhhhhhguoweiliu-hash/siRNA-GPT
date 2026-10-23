"""Fetch small pinned public sources, never models or private account settings."""
import concurrent.futures
import hashlib
import io
import json
import tarfile
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from zipfile import ZipFile

HERE = Path(__file__).resolve().parent
OUT = HERE / 'official_reference_check'
OUT.mkdir(exist_ok=True)
O = 'e2f53ad63387bbe166bf123949151e2bc9bf6ec3'
R = '348951516e0963d22bbb33b3c9fc18c89081d38e'
S = 'b462d4a00520172622f9d8a5a8842d34442c2e68'
ITEMS = [(f'https://raw.githubusercontent.com/lulab/OligoFormer/{O}/scripts/{n}', f'official_tools/OligoFormer/scripts/{n}')
         for n in ['infer.py', 'model.py', 'loader.py', 'loader_infer.py']]
ITEMS += [(f'https://raw.githubusercontent.com/ml4bio/RNA-FM/{R}/fm/pretrained.py', 'official_tools/RNA-FM/source/fm/pretrained.py')]
ITEMS += [(f'https://raw.githubusercontent.com/cran/SeedMatchR/{S}/R/{n}', f'official_tools/SeedMatchR_1.1.1/R/{n}') for n in ['SeedMatchR.R', 'get_seed.R']]
ITEMS += [('https://cran.r-project.org/src/contrib/Archive/SeedMatchR/SeedMatchR_1.1.1.tar.gz', None)]


def fetch(item):
    url, original = item
    row = {'url': url, 'historical_source': original, 'requested_at_utc': datetime.now(timezone.utc).isoformat()}
    try:
        with urllib.request.urlopen(url, timeout=25) as f:
            data = f.read()
            row.update(http_status=f.status, final_url=f.url)
        filename = (original.replace('/', '__') if original else 'SeedMatchR_1.1.1.tar.gz')
        (OUT / filename).write_bytes(data)
        row.update(status='FETCHED', bytes=len(data), sha256=hashlib.sha256(data).hexdigest(), saved_file=filename)
        with ZipFile(HERE / 'historical_evidence.zip') as z:
            if original:
                row['matches_recovered_bytes'] = data == z.read(original)
            else:
                with tarfile.open(fileobj=io.BytesIO(data), mode='r:gz') as tar:
                    row['release_source_comparison'] = {n: tar.extractfile('SeedMatchR/'+n).read() == z.read('official_tools/SeedMatchR_1.1.1/'+n)
                                                       for n in ['DESCRIPTION', 'R/get_seed.R', 'R/SeedMatchR.R']}
    except Exception as e:
        row.update(status='FAILED', error=f'{type(e).__name__}: {e}')
    return row


with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
    results = list(pool.map(fetch, ITEMS))
(OUT / 'receipt.json').write_text(json.dumps(results, indent=2)+'\n', encoding='utf-8')
for r in results:
    print(r['status'], r['url'], r.get('matches_recovered_bytes', r.get('release_source_comparison', r.get('error'))))
