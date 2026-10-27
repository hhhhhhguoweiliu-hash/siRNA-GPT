"""Read immutable retrospective AI labels; never create or confirm quality labels."""
import argparse, collections, csv, hashlib, json, statistics
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
SOURCE=ROOT/'research/2026-10-27_ai_simulated_review'

def read(path):
    with path.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))

def write(path,rows):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)

def calculate(rows):
    counts=collections.Counter(r['review_status'] for r in rows)
    if set(counts)-{'CORRECT','WRONG','MISSING','UNJUDGED','NOT_APPLICABLE'}:raise ValueError('Unknown review status')
    tp,fp=counts['CORRECT'],counts['WRONG'];fn=fp+counts['MISSING']
    n=len(rows)-counts['NOT_APPLICABLE'];ready=n>0 and counts['UNJUDGED']==0
    return dict(required_slots_n=n,TP=tp,FP=fp,FN=fn,unjudged=counts['UNJUDGED'],
        precision=tp/(tp+fp) if ready and tp+fp else (0.0 if ready else None),
        precision_undefined=tp+fp==0,recall=tp/(tp+fn) if ready else None,
        f1=2*tp/(2*tp+fp+fn) if ready else None,
        status='AI_PRE_REVIEW_ONLY' if ready else 'NOT_READY')

def validate(standards,reviews,tasks,mapping):
    sm={s['slot_id']:s for s in standards};tm={t['answer_id']:t for t in tasks};gm={r['answer_id']:r['group'] for r in mapping}
    if len(sm)!=len(standards) or len(tm)!=len(tasks) or len(gm)!=len(mapping):raise ValueError('Duplicate ID')
    if set(tm)!=set(gm):raise ValueError('Task/group mapping mismatch')
    expected={(aid,sid) for aid,t in tm.items() for sid,s in sm.items() if s['case_id']==t['case_id']}
    actual=[(r['answer_id'],r['slot_id']) for r in reviews]
    if len(set(actual))!=len(actual) or set(actual)!=expected:raise ValueError('Missing/duplicate/unexpected slot review')
    for r in reviews:
        t=tm[r['answer_id']];s=sm[r['slot_id']]
        if r['case_id']!=s['case_id'] or r['group']!=gm[r['answer_id']] or r['category']!=t['category']:raise ValueError('Cross-case/group binding')
        if r['round_id']!=s['round_id']:raise ValueError('Round binding mismatch')
    for t in tasks:
        if t['task_verdict'] not in ('PASS','FAIL','UNJUDGED'):raise ValueError('Unknown task verdict')
    # Applicability must be the same for all groups on the same task/slot.
    for sid in sm:
        na=[r['review_status']=='NOT_APPLICABLE' for r in reviews if r['slot_id']==sid]
        if any(na) and not all(na):raise ValueError('Asymmetric applicability')
    return gm

def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    standards,reviews,tasks,mapping=[read(SOURCE/n) for n in ('required_slots.csv','slot_reviews.csv','task_reviews.csv','group_map.csv')]
    gm=validate(standards,reviews,tasks,mapping)
    original=json.loads((ROOT/'research/2026-10-27_real_dialogue_mini/raw/results_original.json').read_text('utf-8'))
    assert {x['answer_id']:x['group'] for x in original}==gm
    per=[]
    for t in tasks:
        rr=[r for r in reviews if r['answer_id']==t['answer_id']];m=calculate(rr)
        counts=collections.Counter(r['review_status'] for r in rr)
        for field,status in [('required_slots_total',None),('required_slots_correct','CORRECT'),('required_slots_wrong','WRONG'),('required_slots_missing','MISSING')]:
            assert int(t[field])==(len(rr) if status is None else counts[status]),(t['answer_id'],field)
        per.append(dict(answer_id=t['answer_id'],case_id=t['case_id'],category=t['category'],group=gm[t['answer_id']],task_verdict=t['task_verdict'],**m))
    summaries=[]
    for g in ('llm','workflow','agent'):
        for cat in ('STANDARD_TASK','RELIABILITY','REQUIREMENT_CHANGE','OVERALL'):
            pp=[r for r in per if r['group']==g and (cat=='OVERALL' or r['category']==cat)]
            ids={r['answer_id'] for r in pp};m=calculate([r for r in reviews if r['answer_id'] in ids])
            task_ready=bool(pp) and all(r['task_verdict']!='UNJUDGED' for r in pp)
            result=dict(group=g,category=cat,task_pass=sum(r['task_verdict']=='PASS' for r in pp),task_total=len(pp),
                task_accuracy=sum(r['task_verdict']=='PASS' for r in pp)/len(pp) if task_ready else None,**m)
            for k in ('precision','recall','f1'):
                result['macro_'+k]=statistics.mean(r[k] for r in pp) if pp and all(r[k] is not None for r in pp) else None
            summaries.append(result)
    a.output.mkdir(parents=True,exist_ok=False)
    write(a.output/'metrics_by_task.csv',per);write(a.output/'metrics_summary.csv',summaries)
    human_ready=all(s.get('human_approved_by') and s.get('human_approved_at_utc') for s in standards) and all(r.get('human_confirmed_at_utc') for r in reviews+tasks)
    status=dict(source_commit='33cd2283a951ee71e8788c348ce8ea2e617b7ceb',n_standards=len(standards),n_judgments=len(reviews),n_answers=len(tasks),
        slot_status_counts=dict(collections.Counter(r['review_status'] for r in reviews)),
        human_metrics_status='NOT_READY' if not human_ready else 'REQUIRES_IDENTITY_AND_ADJUDICATION_VALIDATION',
        formal_human_metrics=None,planning_metrics_status='NOT_READY',new_quality_labels=0,new_model_calls=0,
        source_hashes={n:hashlib.sha256((SOURCE/n).read_bytes()).hexdigest() for n in ('required_slots.csv','slot_reviews.csv','task_reviews.csv','group_map.csv')},
        overall=[r for r in summaries if r['category']=='OVERALL'])
    (a.output/'status.json').write_text(json.dumps(status,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    # Blank confirmation tables retain no new semantic judgment or fabricated identity.
    write(a.output/'human_standard_confirmation_blank.csv',[dict(slot_id=s['slot_id'],case_id=s['case_id'],standard_locator='../../2026-10-27_ai_simulated_review/required_slots.csv#'+s['slot_id'],human_approved_by='',human_approved_at_utc='',decision='',reason='') for s in standards])
    write(a.output/'human_slot_reviews_blank.csv',[dict(answer_id=r['answer_id'],case_id=r['case_id'],round_id=r['round_id'],slot_id=r['slot_id'],review_status='',source_locator='',reason='',reviewer_id='',human_confirmed_at_utc='',adjudication_status='') for r in reviews])
    print(json.dumps(status,ensure_ascii=True))

if __name__=='__main__':main()
