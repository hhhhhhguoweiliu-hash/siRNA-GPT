"""Recompute checkpoint classification metrics; retain abstentions as errors.

Requires Python 3, numpy, scikit-learn. Run in this directory. No model calls.
An optional --source-root verifies the earlier review against the local original
data. All normal computations use the published CSV files only.
"""
import argparse,csv,hashlib,json,math,statistics
from collections import Counter
from pathlib import Path
import numpy as np
from sklearn.metrics import accuracy_score,confusion_matrix,precision_recall_fscore_support

HERE=Path(__file__).resolve().parent
GROUPS=['llm','workflow','agent']
CASES=['W1','W2','W2b','W3','U1','R1','R2','R3','R4']
METRICS=['accuracy','precision','recall','f1']
def read(name):
    with (HERE/'data'/name).open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def write_csv(name,rows):
    with (HERE/'data'/name).open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def ratio(a,b):return a/b if b else None
def calculate(rows):
    c=Counter(r['outcome'] for r in rows)
    tp,tn,fp,fn,ap,an=[c[k] for k in ['TP','TN','FP','FN_EXPLICIT','A_POS','A_NEG']]
    n=len(rows);assert n==tp+tn+fp+fn+ap+an
    yt=[int(r['gold_label']) for r in rows]
    yp=[-1 if r['prediction']=='ABSTAIN' else int(r['prediction']) for r in rows]
    # ABSTAIN is a separate prediction label (-1), absent from the gold labels.
    # Thus it is never correct and is never silently mapped to class 0 / TN.
    acc=ratio(tp+tn,n);p=ratio(tp,tp+fp);rec=ratio(tp,tp+fn+ap)
    f1=ratio(2*tp,2*tp+fp+fn+ap)
    assert math.isclose(acc,accuracy_score(yt,yp),abs_tol=1e-14)
    sp,sr,sf,_=precision_recall_fscore_support(yt,yp,labels=[1],average=None,zero_division=np.nan)
    for ours,theirs in [(p,sp[0]),(rec,sr[0]),(f1,sf[0])]:
        assert (ours is None and np.isnan(theirs)) or (ours is not None and math.isclose(ours,theirs,abs_tol=1e-14))
    mat=confusion_matrix(yt,yp,labels=[1,0,-1])
    assert mat.tolist()==[[tp,fn,ap],[fp,tn,an],[0,0,0]]
    return {'n':n,'n_positive':tp+fn+ap,'n_negative':tn+fp+an,
        'TP':tp,'TN':tn,'FP':fp,'FN_explicit':fn,'abstain_positive':ap,'abstain_negative':an,
        'FN_positive_class_including_abstentions':fn+ap,
        'accuracy':acc,'precision':p,'recall':rec,'f1':f1,
        'coverage':ratio(n-ap-an,n),'answered_only_accuracy':ratio(tp+tn,n-ap-an),
        'negative_class_recall':ratio(tn,tn+fp+an)}
def main(source_root=None):
    defs=read('checkpoint_definitions.csv');rows=read('judgments.csv');neg=read('negative_evidence_review.csv')
    ids={r['checkpoint_id']:r for r in defs}
    assert len(ids)==len(defs)==135 and Counter(int(d['gold_label']) for d in defs)=={1:108,0:27}
    assert len(rows)==405 and len(neg)==81
    assert len({(r['answer_id'],r['checkpoint_id']) for r in rows})==405
    for g in GROUPS:
        rr=[r for r in rows if r['group']==g]
        assert len(rr)==135 and {r['checkpoint_id'] for r in rr}==set(ids)
        assert len({r['answer_id'] for r in rr})==9
    for r in rows:
        d=ids[r['checkpoint_id']];gt=int(r['gold_label'])
        assert r['gold_label']==d['gold_label'] and r['case_id']==d['case_id']
        expected=str(gt) if r['original_status']=='CORRECT' else str(1-gt) if r['original_status']=='WRONG' else 'ABSTAIN'
        assert r['prediction']==expected
        assert not (r['outcome']=='TN' and r['original_status']!='CORRECT')
        assert not (r['prediction']=='ABSTAIN' and r['outcome']=='TN')
        assert r['evidence_locator'] and r['full_evidence_quote_sha256']
    if source_root:
        src=Path(source_root)
        with (src/'outputs/ai_item_audit/resolved_slots.csv').open(encoding='utf-8-sig') as f:old=list(csv.DictReader(f))
        old_by={(r['answer_id'],r['source_slot_id']):r for r in old}
        for r in rows:
            o=old_by[(r['answer_id'],r['checkpoint_id'])]
            assert r['original_status']==o['final_status']
            assert r['full_evidence_quote_sha256']==hashlib.sha256(o['evidence_quote'].encode()).hexdigest()
            assert r['evidence_locator']==o['evidence_locator']
    micro=[];per_task=[];macro=[];matrix=[]
    for g in GROUPS:
        rr=[r for r in rows if r['group']==g];res=calculate(rr)
        micro.append({'group':g,'aggregation':'micro',**res})
        task_values=[]
        for case in CASES:
            values=calculate([r for r in rr if r['case_id']==case]);task_values.append(values)
            per_task.append({'group':g,'case_id':case,**values})
        macro.append({'group':g,'aggregation':'macro_9_tasks','n_tasks':9,
            **{k:statistics.mean(v[k] for v in task_values if v[k] is not None) for k in METRICS+['coverage']},
            **{k+'_defined_tasks':sum(v[k] is not None for v in task_values) for k in METRICS}})
        for gold,pred,k in [(1,1,'TP'),(1,0,'FN_explicit'),(1,'ABSTAIN','abstain_positive'),
                            (0,1,'FP'),(0,0,'TN'),(0,'ABSTAIN','abstain_negative')]:
            matrix.append({'group':g,'gold':gold,'prediction':pred,'count':res[k]})
    write_csv('metrics_micro.csv',micro);write_csv('metrics_macro.csv',macro)
    write_csv('metrics_by_task.csv',per_task);write_csv('confusion_matrix_2x3.csv',matrix)
    checks={'n_judgments':405,'n_original_checkpoints':135,'positive':108,'negative':27,
        'n_groups':3,'same_checkpoint_set_in_all_groups':True,'original_C_W_M_retained':True,
        'abstentions_never_counted_as_TN':True,'TN_evidence_records':sum(r['outcome']=='TN' for r in neg),
        'independent_sklearn_accuracy_precision_recall_f1_check':'passed',
        'sklearn_2x3_confusion_matrix_check':'passed','source_hash_join_check':bool(source_root),
        'new_runs':0,'new_expert_scores':0}
    (HERE/'verification.json').write_text(json.dumps(checks,indent=2)+'\n')
    (HERE/'metrics.json').write_text(json.dumps({'micro':micro,'macro':macro,'by_task':per_task},indent=2)+'\n')
    print(json.dumps({'verification':checks,'micro':micro,'macro':macro},ensure_ascii=False,indent=2))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--source-root',type=Path)
    main(p.parse_args().source_root)
