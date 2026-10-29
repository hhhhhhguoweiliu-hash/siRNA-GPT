"""Reconcile plot inputs to the 405 final slot labels and 27 retained task labels."""
import csv,json,math,statistics
from collections import Counter
from pathlib import Path
P=Path(__file__).resolve().parent/'data'
def read(n):
 with (P/n).open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
slots=read('resolved_slots.csv');tasks=read('task_verdicts_reconciled.csv');byid={r['answer_id']:r for r in tasks}
assert len(slots)==405 and len(tasks)==len(byid)==27
assert len({(r['answer_id'],r['source_slot_id']) for r in slots})==405
assert Counter(r['final_status'] for r in slots)==Counter(CORRECT=312,WRONG=12,MISSING=81)
assert sum(r['final_status_source']=='USER_RELAYED_ADJUDICATION_20261029' for r in slots)==9
def calc(rs):
 co=Counter(r['final_status'] for r in rs);c,w,m=[co[k] for k in ['CORRECT','WRONG','MISSING']]
 assert c+w>0 and c+w+m>0
 return {'precision':c/(c+w),'recall':c/(c+w+m),'f1':2*c/(2*c+2*w+m)}
cats={'STANDARD':['W1','W2','W2b','W3'],'REQUIREMENT_CHANGE':['U1'],'RELIABILITY':['R1','R2','R3','R4'],'OVERALL':['W1','W2','W2b','W3','U1','R1','R2','R3','R4']}
for a in byid:
 assert sum(r['answer_id']==a for r in slots)==sum(1 for r in slots if r['case_id']==byid[a]['case_id'])//3
for row in read('metrics_by_group_category.csv'):
 ids={a for a,t in byid.items() if t['group']==row['group'] and t['case_id'] in cats[row['category']]}
 rr=[r for r in slots if r['answer_id'] in ids];micro=calc(rr)
 for k in ['precision','recall','f1']:
  macro=statistics.mean(calc([r for r in rr if r['answer_id']==a])[k] for a in ids)
  assert math.isclose(micro[k],float(row['micro_'+k]),rel_tol=0,abs_tol=1e-12)
  assert math.isclose(macro,float(row['macro_'+k]),rel_tol=0,abs_tol=1e-12)
for row in read('task_pass_rates.csv'):
 rr=[r for r in tasks if r['group']==row['group'] and r['case_id'] in cats[row['category']]]
 assert len(rr)==int(row['n_tasks']) and sum(r['task_verdict']=='PASS' for r in rr)==int(row['passed'])
 assert math.isclose(int(row['passed'])/len(rr),float(row['pass_rate']),abs_tol=1e-12)
print(json.dumps({'slots':405,'tasks':27,'group_category_summaries':12,'all_aggregates_match_label_tables':True,'scientific_or_model_calls':0}))
