"""Read original labels and apply the separately recorded project adjudication.

No new answer, quality label, model request or biological calculation is made.
"""
import collections,csv,hashlib,json,statistics,subprocess
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
SOURCE_HEAD='a09e9a89f55b28ae761fbbdb64d1c53ccf1be058'
REVIEW=ROOT/'research/2026-10-27_ai_simulated_review_audit_v3'
OVERLAY=ROOT/'research/2026-10-27_final_adjudication'
GROUPS=('llm','workflow','agent')
CATEGORIES=('STANDARD_TASK','REQUIREMENT_CHANGE','RELIABILITY')
DIMS=('factual_accuracy','evidence_support','requirement_completion','boundary_handling')

def read(path):
    with path.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))

def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def slot_metrics(rows):
    counts=collections.Counter(r['review_status'] for r in rows)
    if set(counts)-{'CORRECT','WRONG','MISSING','NOT_APPLICABLE'}:raise ValueError('Unjudged/unknown labels cannot become zero')
    c,w,m=(counts[k] for k in ('CORRECT','WRONG','MISSING'))
    n=c+w+m
    if not n:raise ValueError('No applicable required slots')
    return dict(C=c,W=w,M=m,TP=c,FP=w,FN=w+m,required_slots=n,
        precision=c/(c+w) if c+w else 0.0,precision_undefined=c+w==0,
        recall=c/n,f1=2*c/(2*c+2*w+m),label_source='AI_PROVISIONAL_UNCHANGED_SLOT_LABELS')

def load_data():
    slots=read(REVIEW/'slot_reviews.csv');tasks=read(REVIEW/'task_reviews.csv');standards=read(REVIEW/'required_slots.csv')
    decisions=read(OVERLAY/'decision_overlay.csv');declared=json.loads((OVERLAY/'metrics_before_after.json').read_text('utf-8'))
    raw=json.loads((ROOT/'research/2026-10-27_real_dialogue_mini/raw/results_original.json').read_text('utf-8'))
    byid={r['answer_id']:dict(r) for r in tasks};std={r['slot_id']:r for r in standards}
    assert len(byid)==len(tasks)==27 and len(std)==len(standards)==135 and len(slots)==405 and len(decisions)==13
    assert {r['answer_id']:r['group'] for r in raw}=={k:r['group'] for k,r in byid.items()}
    expected={(aid,sid) for aid,t in byid.items() for sid,s in std.items() if s['case_id']==t['case_id']}
    observed=[(r['answer_id'],r['slot_id']) for r in slots]
    assert set(observed)==expected and len(set(observed))==len(observed)
    for r in slots:
        t=byid[r['answer_id']];s=std[r['slot_id']]
        assert (r['group'],r['category'],r['case_id'],r['round_id'])==(t['group'],t['category'],t['case_id'],s['round_id'])
    for r in byid.values():
        assert r['task_verdict'] in ('PASS','FAIL')
        r['original_verdict']=r['task_verdict'];r['final_verdict']=r['task_verdict']
    updated=set()
    for d in decisions:
        if d['affected_answer_ids']=='ALL':continue
        ids=d['affected_answer_ids'].split(';');before=d['original_task_verdict'].split(';');after=d['adjudicated_task_verdict'].split(';')
        assert len(ids)==len(before)==len(after)
        for aid,old,new in zip(ids,before,after):
            assert aid not in updated and aid in byid and byid[aid]['original_verdict']==old and new in ('PASS','FAIL')
            updated.add(aid);byid[aid]['final_verdict']=new;byid[aid]['decision_id']=d['decision_id']
    changed={k for k,r in byid.items() if r['final_verdict']!=r['original_verdict']}
    assert changed=={'A002','A008','A013','A014'}
    assert {r['answer_id']:r['final_verdict'] for r in byid.values()}=={r['answer_id']:r['adjudicated_verdict'] for r in declared['all_task_labels']}
    per=[]
    for aid,t in byid.items():
        rr=[r for r in slots if r['answer_id']==aid]
        per.append(dict(answer_id=aid,case_id=t['case_id'],category=t['category'],group=t['group'],
            original_verdict=t['original_verdict'],final_verdict=t['final_verdict'],**slot_metrics(rr)))
    summaries=[]
    for group in GROUPS:
        for category in (*CATEGORIES,'OVERALL'):
            pp=[r for r in per if r['group']==group and (category=='OVERALL' or r['category']==category)]
            ids={r['answer_id'] for r in pp};ss=[r for r in slots if r['answer_id'] in ids];m=slot_metrics(ss)
            row=dict(group=group,category=category,n_tasks=len(pp),pass_before=sum(r['original_verdict']=='PASS' for r in pp),pass_after=sum(r['final_verdict']=='PASS' for r in pp),**m)
            row.update({f'macro_{key}':statistics.mean(r[key] for r in pp) for key in ('precision','recall','f1')})
            summaries.append(row)
            if category=='OVERALL':
                assert (row['pass_before'],row['pass_after'])==(declared['group_task_verdicts'][group]['before']['PASS'],declared['group_task_verdicts'][group]['after']['PASS'])
    ratings={};means=[]
    for form,path,col in [('A',ROOT/'research/2026-10-27_final_score_review/score_rows_by_actual_group.csv','actual_group'),('C',ROOT/'research/2026-10-27_third_expert_review/score_rows_by_actual_group.csv','group')]:
        rr=read(path);assert len(rr)==27 and {r['answer_id'] for r in rr}==set(byid)
        ratings[form]=[]
        for r in rr:
            t=byid[r['answer_id']];assert r[col]==t['group'] and r['case_id']==t['case_id']
            scores={d:int(r[d]) for d in DIMS};assert all(v in (0,1,2) for v in scores.values())
            assert sum(scores.values())==int(r['sum8_audit_only'])
            ratings[form].append(dict(answer_id=r['answer_id'],case_id=t['case_id'],group=t['group'],category=t['category'],**scores))
        for group in GROUPS:
            for category in CATEGORIES:
                selected=[r for r in ratings[form] if r['group']==group and r['category']==category]
                means.append(dict(form=form,group=group,category=category,n_tasks=len(selected),**{d:statistics.mean(r[d] for r in selected) for d in DIMS}))
    sources=[REVIEW/n for n in ('slot_reviews.csv','task_reviews.csv','required_slots.csv','group_map.csv','review_metadata.json')]
    sources+=[OVERLAY/'decision_overlay.csv',OVERLAY/'metrics_before_after.json',ROOT/'research/2026-10-27_final_score_review/score_rows_by_actual_group.csv',ROOT/'research/2026-10-27_third_expert_review/score_rows_by_actual_group.csv']
    return dict(per_task=per,summaries=summaries,ratings=ratings,dimension_means=means,
        changed_answers=sorted(changed),source_head=SOURCE_HEAD,
        source_manifest={str(p.relative_to(ROOT)).replace('\\','/'):dict(bytes=p.stat().st_size,sha256=digest(p)) for p in sources},
        scope=dict(task_labels='PROJECT_CONFIRMED_RETROSPECTIVE_ADJUDICATION_OVERLAY',slot_labels='AI_PROVISIONAL_UNCHANGED',
            rating_sheets='Existing A and C kept separate; rater independence not inferred',new_model_requests=0,new_human_ratings=0,source_labels_modified=False,unseen_test=False,C1_planning='NOT_READY'))

def protected_integrity():
    entries=subprocess.check_output(['git','ls-tree','-r',SOURCE_HEAD],cwd=ROOT,encoding='utf-8').splitlines();checked=[]
    for line in entries:
        meta,path=line.split('\t',1)
        selected=path.startswith('research/2026-10-27_real_dialogue_mini/raw/') or path.startswith('research/2026-10-27_final_adjudication/') and path.endswith(('.svg','.csv','.json'))
        selected|=path.startswith('research/2026-10-27_ai_simulated_review_audit_v3/') and path.endswith('.csv')
        selected|=path in ('research/2026-10-27_final_score_review/source_workbook_original.xlsx','research/2026-10-27_third_expert_review/source_expert_scores_original.xlsx')
        if selected:
            blob=meta.split()[2];b=(ROOT/path).read_bytes();actual=hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()
            assert blob==actual,path
            checked.append(dict(path=path,git_blob=blob,sha256=hashlib.sha256(b).hexdigest()))
    return dict(source_head=SOURCE_HEAD,n_files=len(checked),all_unchanged=True,files=checked)

def write_analysis(data):
    for name,value in [('metrics_corrected.json',data),('protected_source_integrity.json',protected_integrity())]:
        (HERE/name).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    rows=[]
    for r in data['summaries']:
        for phase in ('before','after'):
            rows.append(dict(layer='TASK',form='',category=r['category'],group=r['group'],metric='pass_'+phase,numerator=r['pass_'+phase],denominator=r['n_tasks'],value=r['pass_'+phase]/r['n_tasks'],label_source='AI_INITIAL' if phase=='before' else 'PROJECT_ADJUDICATION_OVERLAY'))
        for key in ('precision','recall','f1','macro_precision','macro_recall','macro_f1'):
            rows.append(dict(layer='SLOT',form='',category=r['category'],group=r['group'],metric=key,numerator='',denominator=r['n_tasks'] if key.startswith('macro') else r['required_slots'],value=r[key],label_source='AI_PROVISIONAL_UNCHANGED'))
    for r in data['dimension_means']:
        for d in DIMS:rows.append(dict(layer='ORDINAL_SCORE',form=r['form'],category=r['category'],group=r['group'],metric=d,numerator='',denominator=r['n_tasks'],value=r[d],label_source='ORIGINAL_SCORE_SHEET_'+r['form']))
    with (HERE/'figure_data_corrected.csv').open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)

if __name__=='__main__':
    data=load_data();write_analysis(data)
    print(json.dumps([r for r in data['summaries'] if r['category']=='OVERALL'],ensure_ascii=True))
