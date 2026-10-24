import hashlib,json,tempfile,sys,re
from pathlib import Path
from unittest.mock import patch
root=Path.cwd();sys.path.insert(0,str(root))
from literature import Library
from knowledge import search
base=root/'research/2026-10-23_literature/live_20261024'
actual=base/'actual_demo'
records=json.loads((actual/'results.json').read_text(encoding='utf-8'))
evidence=actual/'conversation/evidence'
audits=[json.loads(p.read_text(encoding='utf-8')) for p in evidence.glob('*.json')]
exchange=next(x for x in audits if x.get('kind')=='model_exchange')
supported=next(x for x in audits if x.get('kind')=='library_qa' and x['status']=='complete')
unsupported=next(x for x in audits if x.get('kind')=='library_qa' and x['status']=='no_evidence')
scratch=root/'.test_tmp';scratch.mkdir(exist_ok=True)
with tempfile.TemporaryDirectory(dir=scratch) as td:
 restored=Library(Path(td)/'restored_actual_server_library')
 restore=restored.import_bundle((actual/'library.zip').read_bytes())
 restored.db.unlink();restored.rebuild()
 with patch('literature.get_library',return_value=restored):
  again=search(supported['question'],limit=3)
 old=supported['retrieved_excerpts'];by_url={x['url']:x for x in again['excerpts']}
 checks=[]
 for item in old:
  recomputed=by_url.get(item['url'])
  checks.append({'citation_id':item['citation_id'],'url':item['url'],'source_kind':item.get('source_kind'),
   'locator':item.get('locator'),'sha256':item.get('sha256'),
   'exact_text_matches_restored_source':recomputed is not None and recomputed['text']==item['text']})
 if not all(c['exact_text_matches_restored_source'] for c in checks):raise ValueError('Retrieved source mismatch')
 quotes=[('S1','模型分数不是实验敲低百分比'),('S2','i*1.341'),('S3','prediction score for each siRNA')]
 quote_checks=[{'citation_id':identity,'quote':quote,'present_in_actual_excerpt':any(x['citation_id']==identity and quote in x['text'] for x in old)} for identity,quote in quotes]
 response=exchange['response'];request=exchange['request']
 check={'kind':'EXECUTION_AND_SOURCE_INTEGRITY_CHECK_NOT_INDEPENDENT_QUALITY_SCORING',
  'planned_units':len(records),'actual_model_exchange_records':sum(x.get('kind')=='model_exchange' for x in audits),
  'all_two_completed':all(x['status']=='COMPLETED' for x in records),
  'actual_request':{k:request[k] for k in ['model','stream','thinking','max_output_tokens'] if k in request},
  'actual_response_model':response.get('model'),'actual_response_status':response.get('status'),
  'incomplete_details_returned':'incomplete_details' in response,'incomplete_details':response.get('incomplete_details'),
  'actual_usage':response.get('usage'),'request_id':supported['model_calls'][0]['request_id'],
  'actual_server_library_restored':restore,'same_library_version':restored.version()==supported['library_version'],
  'rebuilt_after_removing_derived_index':True,'retrieved_sources':checks,'short_quote_checks':quote_checks,
  'unsupported_case':{'model_call_count':unsupported['model_call_count'],'retrieved_excerpts':len(unsupported['retrieved_excerpts']),
   'note':'Program scope/no-evidence refusal, not a measurement of model refusal ability'},
  'independent_human_scores':None}
 if not check['same_library_version'] or not all(x['present_in_actual_excerpt'] for x in quote_checks):raise ValueError('Integrity check failed')
 (base/'actual_demo_integrity_checks.json').write_text(json.dumps(check,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 print(json.dumps({k:v for k,v in check.items() if k not in ['retrieved_sources','short_quote_checks','actual_server_library_restored']},ensure_ascii=False))
