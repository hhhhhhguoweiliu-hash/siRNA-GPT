"""Check saved real exports, not a test transport; retain all generated errors."""
import csv,hashlib,json,re,subprocess,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'research/2026-10-24_nearfull_complete/live';RUN=OUT/'tool_export'
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(name,v):(OUT/name).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
def main():
 conversation=load(OUT/'conversation_export_original.json');report=load(RUN/'report.json');config=load(RUN/'run_config.json')
 assert conversation['phase']=='complete' and not conversation['busy'] and conversation['export_status']=='COMPLETED_SNAPSHOT'
 assert report['agent_status']=='COMPLETED_WITH_REAL_API' and report['run_id']=='20261024_121627_1e50c9'
 inp=load(RUN/'input.json');assert len(inp['candidates'])==1 and inp['candidates'][0]['candidate_id']=='USER_PURCHASED_siVEGF'
 assert inp['candidates'][0]==load(ROOT/'data/purchased_sivegf_20261024_v1/candidate.json')
 tools=['inspect_candidates','verify_target','score_candidates','match_seed','query_expression','compile_report']
 results={n:load(RUN/(n+'.json')) for n in tools};assert all(r['status']!='ERROR' for r in results.values())
 assert results['score_candidates']['status']==results['match_seed']['status']=='IMPORTED_VERIFIED_LOCAL'
 assert results['verify_target']['rows'][0]['covered_transcripts']==18
 assert results['verify_target']['reference_sha256']==sha(ROOT/'data/VEGFA.fasta')
 assert results['query_expression']['candidate_summary'][0]['matched_genes']==2839
 e=results['query_expression']['candidate_summary'][0]
 assert e['baseline_mapped_genes']==2836 and e['hypoxia_detected_genes']==1595 and e['unmapped_genes']==3
 with (RUN/'seed_matches.tsv').open(encoding='utf-8-sig',newline='') as f:seed=list(csv.DictReader(f,delimiter='\t'))
 assert len(seed)==2840 and sum(int(r['seed_site_count']) for r in seed)==3540
 exchanges=[]
 for x in conversation['evidence_records']:
  if x['kind']=='model_exchange':exchanges.append({'phase':'planning','actual_request':x['request'],'raw_response':x['response'],'record':'conversation_export_original.json#'+x['id']})
 assert len(exchanges)==1
 for path in sorted((RUN/'attempts').glob('*_turn*_response.json')):
  v=load(path);exchanges.append({'phase':'execution','actual_request':v['_request'],'raw_response':v['_raw_response'],'record':path.relative_to(OUT).as_posix()})
 assert len(exchanges)==8 and len({x['raw_response']['id'] for x in exchanges})==8
 calls=[]
 for x in exchanges:
  req=x['actual_request'];res=x['raw_response']
  assert res['status']=='completed' and not res.get('incomplete_details')
  assert req['stream'] is False and req['thinking']=={'type':'disabled'} and req['max_output_tokens']==1800
  assert req['model']=='doubao-seed-2-1-pro-260915'
  calls.append({'phase':x['phase'],'response_id':res['id'],'model':res['model'],'created_at':res['created_at'],'response_status':res['status'],
   'incomplete_details':res.get('incomplete_details'),'actual_max_output_tokens':req['max_output_tokens'],'actual_thinking':req['thinking'],'actual_stream':req['stream'],'usage':res['usage'],'raw_record':x['record']})
 assert sum(x['usage']['total_tokens'] for x in calls)==39048
 save('actual_model_call_summary.json',{'case_only_excludes_startup_checks':True,'calls':calls,'total_requests':len(calls),
  'total_tokens':sum(x['usage']['total_tokens'] for x in calls),'input_tokens':sum(x['usage']['input_tokens'] for x in calls),'output_tokens':sum(x['usage']['output_tokens'] for x in calls),
  'full_actual_request_and_response_retained_in_original_exports':True})
 assets=[];commit='03092ef5fbc2af289aaa2b7bc8d57315c050964f'
 assert config['runtime']['commit']==conversation['runtime']['commit']==commit
 for name,digest in config['runtime']['assets'].items():
  blob=subprocess.check_output(['git','show',commit+':'+name]);actual=hashlib.sha256(blob).hexdigest();assert actual==digest,(name,actual,digest)
  assets.append({'path':name,'git_blob_sha256':actual,'exact_deployed_bytes_match':True})
 package=RUN/'verified_import/purchased_sivegf_20261024_v1';manifest=load(package/'manifest.json')
 for name,digest in manifest['files'].items():assert sha(package/name)==digest
 with zipfile.ZipFile(OUT/'actual_tool_export_original.zip') as z:
  assert z.testzip() is None
  assert len(z.namelist())==57 and len([n for n in z.namelist() if n.endswith('.gz')])==8
 correct='GAUAGAGCAAGACAAGAAA';incorrect='GAUAGAGCAAGACAAGACAAGAAA';summary=report['model_summary']
 assert incorrect in summary and inp['candidates'][0]['passenger_paired_core_19nt_5to3']==correct
 before=sha(RUN/'report.json')
 save('answer_sequence_discrepancy.json',{'observed_issue':'Generated final-answer passenger core is not the verified 19nt input','original_generated_text':incorrect,
  'original_generated_length':len(incorrect),'correct_from_original_input':correct,'correct_length':len(correct),'evidence':'tool_export/input.json; verified_import/purchased_sivegf_20261024_v1/candidate.json',
  'raw_answer_unchanged':True,'rerun_to_hide_error':False,'independent_human_quality_score':None})
 (OUT/'ANSWER_CORRECTION_ZH.md').write_text('# 真实案例原答的序列纠正\n\n运行20261024_121627_1e50c9，六工具完成，但模型最终表格把另一条链的19位核心写成了`'+incorrect+'`（'+str(len(incorrect))+'位）。这是生成文字错误，不能用于论文序列表或订购。\n\n原DOCX第1行、工具输入和已导入计算一致支持的19位核心是`'+correct+'`。原第1行完整文字`GAUAGAGCAAGACAAGAAATT-N3（叠氮基团，用于点击化学）`未改。角色仍按两行均5′→3′条件推导，未模拟N3实物。\n\n原回答、report.json、report.html、所有请求和响应均原样保留；不重跑消错、不声称回答全部正确。本说明是核对原始证据后的追加纠正，不是独立人工评分。论文必须同时报告这项错误，不能把工具完成状态当回答准确率。\n',encoding='utf-8',newline='\n')
 assert sha(RUN/'report.json')==before
 save('live_case_audit.json',{'evidence_integrity_status':'PASS','scientific_tool_workflow':'COMPLETE','final_answer_quality':'OBSERVED_SEQUENCE_TRANSCRIPTION_ERROR_PRESERVED',
  'run_id':report['run_id'],'runtime_commit':commit,'tool_count':6,'planned_cases':1,'real_model_requests':8,'tokens':39048,'export_files':57,
  'verified_import_raw_files':len(manifest['files']),'deployed_assets':assets,'expression_summary':e,'old_nine_and_54_not_run_as_case':True,
  'independent_human_quality_score':None,'supplemental_error_file':'answer_sequence_discrepancy.json','original_report_sha256':before})
 print(json.dumps({'workflow':'COMPLETE','model_requests':8,'tokens':39048,'assets_exact':len(assets),'answer_error_length':len(incorrect),'correction_added':True}))
if __name__=='__main__':main()
