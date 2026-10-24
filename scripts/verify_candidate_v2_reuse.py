"""Read-only verification of already completed literature/import/day7 work, saving new audit only."""
import hashlib,io,json,sys,tempfile,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from literature import Library
OUT=ROOT/'research/2026-10-24_candidate_v2'
def sha(raw):return hashlib.sha256(raw).hexdigest()
def main():
 old=ROOT/'research/2026-10-24_followup'
 raw=(old/'live/actual_demo_original.zip').read_bytes()
 with zipfile.ZipFile(io.BytesIO(raw)) as z:
  assert z.testzip() is None
  results=json.loads(z.read('results.json'));protocol=json.loads(z.read('protocol.json'));record=json.loads(z.read('conversation_record.json'))
  calls=[e for e in record['evidence_records'] if e['kind']=='model_exchange'];assert len(calls)==1
  audit=next(e for e in record['evidence_records'] if e['kind']=='library_qa')
  request=json.loads(calls[0]['request']['input'][-1]['content'][0]['text'])
  assert protocol['mode']=='day7_regression' and len(protocol['questions'])==len(results)==1
  assert calls[0]['response']['status']=='completed' and calls[0]['response']['usage']['total_tokens']==6816
  assert request['retrieved_excerpts']==audit['retrieved_excerpts'] and audit['retrieval_executed']
  assert '证据不足，无法给出' in results[0]['answer'] and '0.9915' not in results[0]['answer']
  with tempfile.TemporaryDirectory(dir=ROOT/'.test_tmp') as td:
   lib=Library(Path(td)/'restore');r=lib.import_bundle(z.read('library.zip'));lib.db.unlink();lib.rebuild()
   assert r['same_version'] and lib.version()==audit['library_version'] and len(lib.catalogue()['documents'])==12
   checks=[]
   for e in audit['retrieved_excerpts']:
    if not e.get('document_id'):continue
    doc,path,cs=lib.document(e['document_id']);page=next(p for p in doc['pages'] if p['page']==e['page'])
    assert page['text'][e['start']:e['end']]==e['text'] and sha(e['text'].encode())==e['chunk_sha256']
    checks.append(e['citation_id'])
   papers=json.loads((ROOT/'references/vegfa_experiments_20261024/sources.json').read_text(encoding='utf-8'))['sources']
   for source in papers:
    raw_source=(ROOT/'references/vegfa_experiments_20261024'/source['file']).read_bytes();assert sha(raw_source)==source['sha256']
    assert any(d['sha256']==source['sha256'] for d in lib.catalogue()['documents'])
 value={'status':'VERIFIED_REUSE_NO_NEW_API','prior_source_commit':'f60add9','prior_deployed_code':'fa62c7d','actual_original_day7_run':'library_demo_20261024_052657_5a7974',
  'actual_original_day7_zip_sha256':sha(raw),'new_API_calls':0,'original_model_calls':1,'original_usage_tokens':6816,
  'question_and_response_preserved':True,'actual_request_excerpts_preserved':len(audit['retrieved_excerpts']),
  'document_excerpts_rechecked':checks,'three_experimental_originals_verified':True,'library_restore_rebuild_same_version':True,
  'library_version':audit['library_version'],'independent_human_scores':None,'not_counted_as_new_demo':True}
 (OUT/'completed_CD_reuse_audit.json').write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
 print(json.dumps(value,ensure_ascii=False))
if __name__=='__main__':main()
