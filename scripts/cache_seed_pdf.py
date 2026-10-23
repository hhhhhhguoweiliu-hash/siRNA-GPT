"""Rebuild a fingerprinted PDF page cache for the bundled, unchanged originals."""
import hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from literature import extract
out=ROOT/'references/sirna_library'
manifest=json.loads((out/'sources.json').read_text(encoding='utf-8'))
for source in manifest['sources']:
    if not source['file'].endswith('.pdf'):continue
    raw=(out/source['file']).read_bytes()
    assert hashlib.sha256(raw).hexdigest()==source['sha256']
    result=extract(raw,source['file'],use_cache=False)
    filename=source['file']+'.pages.json'
    content=json.dumps({'source_sha256':source['sha256'],
        'extraction_code_sha256':hashlib.sha256((ROOT/'pdf_text_worker.py').read_text(encoding='utf-8').replace('\r\n','\n').encode('utf-8')).hexdigest(),
        'result':result},ensure_ascii=False,indent=2).encode('utf-8')
    (out/filename).write_bytes(content)
    source.update(pages_file=filename,pages_sha256=hashlib.sha256(content).hexdigest())
    print(source['file'],len(result['pages']),'actual pages extracted, cache fingerprinted')
(out/'sources.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
