"""Recover one actual manual library demo; verify transport and preserve originals."""
import argparse
import base64
import hashlib
import io
import json
import zipfile
from pathlib import Path, PurePosixPath


def recover(transport, output, expected_ids=('B02','B08')):
    data=json.loads(transport.read_text(encoding='utf-8'))
    receipts=data['archive_receipt']['logs']
    if len(receipts)!=1:raise ValueError('Expected one archive receipt')
    meta=json.loads(receipts[0]['message'].split(' ',1)[1])
    parts={}
    for page in data['chunk_pages']:
        for row in page['logs']:
            chunk=json.loads(row['message'].split(' ',1)[1])
            if chunk['run_id']!=meta['run_id']:raise ValueError('Mixed runs')
            index=chunk['i']
            if index in parts and parts[index]!=chunk['data']:raise ValueError('Conflicting chunks')
            parts[index]=chunk['data']
    if set(parts)!=set(range(meta['chunks'])):raise ValueError('Missing transport chunks')
    raw=base64.b64decode(''.join(parts[i] for i in range(meta['chunks'])),validate=True)
    if len(raw)!=meta['bytes'] or hashlib.sha256(raw).hexdigest()!=meta['sha256']:
        raise ValueError('Archive bytes do not match service receipt')
    output.mkdir(parents=True,exist_ok=True)
    original=output/'actual_demo_original.zip'
    if original.exists() and original.read_bytes()!=raw:raise ValueError('Refusing to replace a different original')
    original.write_bytes(raw)
    extracted=output/'actual_demo';extracted.mkdir(exist_ok=True)
    files=[]
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        if z.testzip() is not None:raise ValueError('ZIP CRC failed')
        if sum(i.file_size for i in z.infolist())>30_000_000:raise ValueError('Unexpectedly large archive')
        for item in z.infolist():
            part=PurePosixPath(item.filename)
            if part.is_absolute() or '..' in part.parts or '\\' in item.filename or ':' in item.filename:
                raise ValueError('Unsafe archive path')
            if item.is_dir():continue
            target=extracted.joinpath(*part.parts);target.parent.mkdir(parents=True,exist_ok=True)
            value=z.read(item)
            if target.exists() and target.read_bytes()!=value:raise ValueError('Refusing to overwrite original record')
            target.write_bytes(value)
            files.append({'path':item.filename,'bytes':len(value),'sha256':hashlib.sha256(value).hexdigest()})
    results=json.loads((extracted/'results.json').read_text(encoding='utf-8'))
    protocol=json.loads((extracted/'protocol.json').read_text(encoding='utf-8'))
    status=json.loads((extracted/'status.json').read_text(encoding='utf-8'))
    if [r['id'] for r in results]!=list(expected_ids) or len(protocol['questions'])!=len(expected_ids):
        raise ValueError('Unexpected planned question units')
    receipt={'run_id':meta['run_id'],'source':'Authorized Render service log transport from manual UI demo',
        'archive_sha256':meta['sha256'],'archive_bytes':len(raw),'chunks_verified':len(parts),'zip_crc_valid':True,
        'all_planned_units_retained':True,'planned_units':len(expected_ids),'status':status['status'],'library_version':protocol['library_version'],
        'results':[{'id':r['id'],'status':r['status'],'answer_status':r.get('answer_status'),
                    'model_calls':r.get('model_calls'),'usage':r.get('usage'),'citation_check':r.get('citation_check')} for r in results],
        'independent_human_scores':None,'files':files}
    (output/'actual_demo_recovery_receipt.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    return receipt


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--transport',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--day7',action='store_true',help='Validate the separately planned single regression question')
    args=parser.parse_args()
    result=recover(args.transport,args.output,('B11_day7',) if args.day7 else ('B02','B08'))
    print(json.dumps({k:v for k,v in result.items() if k!='files'},ensure_ascii=False))
