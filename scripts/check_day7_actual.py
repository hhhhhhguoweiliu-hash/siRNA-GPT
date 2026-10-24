"""Audit the separately preserved real single-question record; no new API calls."""
import hashlib,json,re,subprocess,sys,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from literature import Library
from knowledge import CARDS
OUT=ROOT/'research/2026-10-24_followup/live';R=OUT/'actual_demo'
def main():
 record=json.loads((R/'conversation_record.json').read_text(encoding='utf-8'))
 results=json.loads((R/'results.json').read_text(encoding='utf-8'))
 audit=next(a for a in record['evidence_records'] if a['kind']=='library_qa')
 exchange=next(a for a in record['evidence_records'] if a['kind']=='model_exchange')
 req=exchange['request'];res=exchange['response']
 payload=json.loads(req['input'][-1]['content'][0]['text'])
 answer=''.join(c['text'] for o in res['output'] for c in o.get('content',[]) if c.get('type')=='output_text')
 checks={'one_planned_unit':len(results)==1 and results[0]['id']=='B11_day7',
  'one_actual_model_exchange':sum(a['kind']=='model_exchange' for a in record['evidence_records'])==1,
  'actual_retrieval_executed':audit['retrieval_executed'] is True,
  'actual_request_has_question':payload['question']==results[0]['question'],
  'actual_request_has_all_excerpts':payload['retrieved_excerpts']==audit['retrieved_excerpts'],
  'actual_library_version_aligned':payload['library_version']==audit['library_version'],
  'response_complete':res['status']=='completed' and not res.get('incomplete_details'),
  'original_response_matches_exported_answer':answer==audit['raw_model_answer']==results[0]['answer'],
  'explicit_missing_day7_statement':'证据不足，无法给出' in answer and '第7天' in answer,
  'no_model_score_presented_as_knockdown':'不能用模型分数' in answer and '0.9915' not in answer,
  'no_unknown_citation_ids':not audit['citation_check']['unknown_ids']}
 citations=[]
 with tempfile.TemporaryDirectory(dir=ROOT/'.test_tmp') as td:
  lib=Library(Path(td)/'restored');receipt=lib.import_bundle((R/'library.zip').read_bytes());lib.db.unlink();lib.rebuild()
  checks['actual_library_restore_rebuild']=receipt['same_version'] and lib.version()==audit['library_version']
  checks['actual_library_twelve_materials']=len(lib.catalogue()['documents'])==12
  for e in audit['retrieved_excerpts']:
   if e.get('document_id'):
    doc,original_path,stored_chunks=lib.document(e['document_id'])
    page=next(p for p in doc['pages'] if p['page']==e['page'])
    exact=page['text'][e['start']:e['end']]==e['text'] and hashlib.sha256(e['text'].encode()).hexdigest()==e['chunk_sha256']
   else:exact=next(c for c in CARDS if c['id']==e['knowledge_id'])['text']==e['text']
   citations.append({'citation_id':e['citation_id'],'source_kind':e['source_kind'],'title':e['title'],
    'url':e['url'],'locator':e.get('locator'),'exact_excerpt_verified':exact})
  checks['all_eight_actual_excerpts_exact']=len(citations)==8 and all(x['exact_excerpt_verified'] for x in citations)
 runtime=record['runtime'];commit=runtime['commit']
 comparisons={}
 for name,expected in runtime['assets'].items():
  raw=subprocess.check_output(['git','show',commit+':'+name],cwd=ROOT)
  comparisons[name]=hashlib.sha256(raw).hexdigest()==expected
 checks['actual_runtime_assets_match_deployed_commit']=all(comparisons.values())
 value={'checks':checks,'all_pass':all(checks.values()),'run_id':'library_demo_20261024_052657_5a7974',
  'actual_commit':commit,'library_version':audit['library_version'],'model':req['model'],
  'request_settings':{k:req[k] for k in ('stream','thinking','max_output_tokens')},
  'response_status':res['status'],'incomplete_details':res.get('incomplete_details'),
  'usage':res['usage'],'citations':citations,'runtime_asset_comparisons':comparisons,
  'verification_scope':'Record completeness, source transmission and targeted missing-measurement regression; not independent scientific scoring or unseen-question accuracy',
  'independent_human_scores':None,'new_model_calls_in_this_audit':0}
 (OUT/'actual_record_checks.json').write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
 lines=['# 本次真实原回答（逐字保留）','',answer,'','## 引用定位（追加导航，不修改回答）','']
 lines+=['- ['+c['citation_id']+'] '+c['title']+'；'+(c['locator'] or '项目说明卡')+'；'+c['url'] for c in citations]
 (OUT/'ACTUAL_ANSWER.md').write_text('\n'.join(lines)+'\n',encoding='utf-8',newline='\n')
 print(json.dumps({'all_pass':value['all_pass'],'checks':checks,'model':req['model'],'usage':res['usage']},ensure_ascii=False))
 if not value['all_pass']:raise SystemExit(1)
if __name__=='__main__':main()
