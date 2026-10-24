"""Check or join the three reference-file parts. Never overwrite a different existing file."""
import argparse,hashlib,json,zipfile
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--parts-dir',type=Path,required=True);p.add_argument('--check-only',action='store_true');a=p.parse_args()
meta=json.loads((Path(__file__).resolve().parents[1]/'research/2026-10-24_candidate_v2/reference_package_parts.json').read_text(encoding='utf-8'))
joined=hashlib.sha256();size=0
for part in meta['parts_in_order']:
 assert Path(part['filename']).name==part['filename']
 path=a.parts_dir/part['filename'];h=hashlib.sha256();n=0
 with path.open('rb') as f:
  for b in iter(lambda:f.read(4*1024*1024),b''):h.update(b);joined.update(b);n+=len(b)
 assert n==part['bytes'] and h.hexdigest()==part['sha256'],part['filename'];size+=n
assert size==meta['full_bytes'] and joined.hexdigest()==meta['full_sha256']
if not a.check_only:
 assert Path(meta['full_filename']).name==meta['full_filename']
 dest=a.parts_dir/meta['full_filename']
 if dest.exists():
  with dest.open('rb') as f:
   h=hashlib.sha256()
   for b in iter(lambda:f.read(4*1024*1024),b''):h.update(b)
  assert h.hexdigest()==meta['full_sha256'],'Existing output differs; refusing overwrite'
 else:
  with dest.open('xb') as f:
   for part in meta['parts_in_order']:
    with (a.parts_dir/part['filename']).open('rb') as source:
     for b in iter(lambda:source.read(4*1024*1024),b''):f.write(b)
 with zipfile.ZipFile(dest) as z:assert z.testzip() is None
print(json.dumps({'all_parts_sha256_verified':True,'concatenated_sha256':joined.hexdigest(),'bytes':size,'check_only':a.check_only}))
