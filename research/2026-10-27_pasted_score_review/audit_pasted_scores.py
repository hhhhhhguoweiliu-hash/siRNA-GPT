from pathlib import Path
from collections import Counter
import json,csv,hashlib
r=Path('research/2026-10-27_pasted_score_review')
source=r/'user_pasted_score_transcription.txt'
records=json.loads((r/'parsed_score_transcription.json').read_text(encoding='utf-8'))
raw=Path(r'C:\00000\ARPE RNA-seq\sirna-gpt\research\2026-10-27_real_dialogue_mini\raw\results_original.json')
b=raw.read_bytes();assert hashlib.sha256(b).hexdigest()=='f443d6f358a3c63f45eeef0906ae968f74f231534eb3c5276207767a14c2b9a3'
results=json.loads(b);ids={x['answer_id']:x for x in results}
assert len(records)==len({x['answer_id'] for x in records})==27 and {x['answer_id'] for x in records}==set(ids)
for x in records:
 x['group']=ids[x['answer_id']]['group'];x['case_id']=ids[x['answer_id']]['case_id']
 assert len(x['scores'])==4 and all(type(v) is int and 0<=v<=2 for v in x['scores'])
 assert sum(x['scores'])==x['sum8_audit_only']
 x['completion_label_as_pasted']=x['source_reason_segment'].split('：',1)[0]
dims=['factual_accuracy','evidence_support','requirement_completion','boundary_handling']
summary={}
for name,cases in {'W_standard':['W1','W2','W2b','W3'],'U_change':['U1'],'R_reliability':['R1','R2','R3','R4']}.items():
 summary[name]={}
 for group in ['llm','workflow','agent']:
  rr=[x for x in records if x['group']==group and x['case_id'] in cases];assert len(rr)==len(cases)
  summary[name][group]={'n_task_episodes':len(rr),'dimension_means_0_to_2':{d:sum(x['scores'][i] for x in rr)/len(rr) for i,d in enumerate(dims)}}
counts={g:{'n':sum(x['group']==g for x in records),'n_full_score_as_pasted':sum(x['group']==g and x['sum8_audit_only']==8 for x in records)} for g in ['llm','workflow','agent']}
evidence=[]
for aid in ['A001','A014','A023','A013','A010','A022','A002']:
 x=ids[aid]
 ev={'answer_id':aid,'case_id':x['case_id'],'group':x['group'],'original_round_answers':[{'round':z['round'],'answer':z['answer'],'raw_model_answer':z.get('raw_model_answer')} for z in x['rounds']],'round_question_texts':[z['message'] for z in x['case_input']],'completed_tools':x.get('completed_tools',[]),'software_status_not_human_rating':x['status']}
 evidence.append(ev)
a=ids['A001']['rounds'][0]['answer'];assert '23nt设计窗口对应NM_003376.6的坐标' in a
a=ids['A014']['rounds'][1]['answer'];assert '2025年X月X日' in a
a=ids['A023'];assert not a.get('completed_tools')
o={'source_kind':'Transcription of user-pasted scores, not an original XLSX or signed expert form','saved_transcription_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'reviewer_identity_and_relationship_to_prior_forms':'Not supplied in this message; no inference of an additional independent rater','new_ratings_added_or_changed_by_assistant':0,'records':records,'full_score_counts_as_pasted':counts,'stratified_descriptive_summary':summary,'accepted_primary_completion_rates':None,'scientific_accuracy_percentages':None,'pooled_human_metrics':None,'status':'PRESERVED_SUBMITTED_OPINION_PENDING_REASON_AND_SCOPE_REVIEW'}
(r/'parsed_scores_and_descriptive_check.json').write_text(json.dumps(o,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
(r/'original_answer_evidence_NOT_NEW_RATINGS.json').write_text(json.dumps({'is_new_rating':False,'run_results_sha256':hashlib.sha256(b).hexdigest(),'evidence':evidence},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
with (r/'score_rows_by_actual_group.csv').open('w',encoding='utf-8-sig',newline='') as f:
 w=csv.writer(f);w.writerow(['answer_id','case_id','group',*dims,'sum8_audit_only','completion_label_as_pasted'])
 for x in sorted(records,key=lambda x:(x['case_id'],x['group'])):w.writerow([x['answer_id'],x['case_id'],x['group'],*x['scores'],x['sum8_audit_only'],x['completion_label_as_pasted']])
checks={'records':27,'valid_score_cells':108,'all_totals_match':True,'all_answer_ids_match_real_run':True,'full_score_counts_as_pasted':counts,'source_transcription_hash':hashlib.sha256(source.read_bytes()).hexdigest(),'new_model_calls':0,'new_or_changed_human_scores':0,'source_text_is_user_message_transcription_not_original_file':True}
(r/'mechanical_checks.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(checks,ensure_ascii=True))

