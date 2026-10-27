"""Verify concurrent v3 audit against unchanged raw records and our computation."""
import collections,csv,hashlib,json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent
def read(p):
    with p.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def main():
    original=ROOT/'research/2026-10-27_ai_simulated_review';latest=ROOT/'research/2026-10-27_ai_simulated_review_audit_v3'
    same={n:read(original/n)==read(latest/n) for n in ('required_slots.csv','slot_reviews.csv','task_reviews.csv','group_map.csv')};assert all(same.values())
    own={(r['group'],r['category']):r for r in read(HERE/'metrics/metrics_summary.csv')};comparison=[]
    for r in read(latest/'metrics_summary.csv'):
        q=own[r['group'],r['category']]
        names={'task_pass':'task_pass','task_total':'task_total','required_slots_n':'required_slots_n','TP':'TP','FP':'FP','FN':'FN',
            'micro_required_slot_precision':'precision','micro_required_slot_recall':'recall','micro_required_slot_f1':'f1',
            'macro_required_slot_precision':'macro_precision','macro_required_slot_recall':'macro_recall','macro_required_slot_f1':'macro_f1'}
        checks={k:abs(float(r[k])-float(q[v]))<1e-9 for k,v in names.items()};assert all(checks.values())
        comparison.append(dict(group=r['group'],category=r['category'],checks=checks))
    raw=json.loads((ROOT/'research/2026-10-27_real_dialogue_mini/raw/results_original.json').read_text('utf-8'));source=[]
    for x in raw:
        for q in x['rounds']:
            text=q.get('raw_model_answer');present=text is not None and text!=''
            source.append(dict(answer_id=x['answer_id'],round=q['round'],raw_present=present,
                comparison=('EQUAL' if text==q['answer'] else 'DIFFERENT') if present else 'NOT_COMPARABLE',
                answer_source=q['answer_source'],real_model_requests=q['real_model_requests']))
    counts=dict(collections.Counter(r['comparison'] for r in source));assert counts==dict(EQUAL=20,NOT_COMPARABLE=12,DIFFERENT=1),counts
    result=dict(concurrent_commit='f92adcdbaf89a34010e1ad00d31c2954a77355a7',merge_commit='601431d008106b8f11d75fa02f244d147c2d2a43',
        primary_implementation_commit='e02708125b91dd8cdcb63f64f0a0c80725689db7',same_primary_labels=same,summary_rows_checked=comparison,
        raw_comparison_counts=counts,raw_difference_ids=sorted({r['answer_id'] for r in source if r['comparison']=='DIFFERENT'}),
        standard_reconciliation='v3 documents 126 original-draft slots + 8 prompt-common + 1 prompt-delivery = 135; no slot label was changed',
        new_quality_labels=0,new_model_calls=0,source_hashes={n:hashlib.sha256((latest/n).read_bytes()).hexdigest() for n in same})
    (HERE/'latest_v3_alignment.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    with (HERE/'raw_comparison_status_v3.csv').open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(source[0]));w.writeheader();w.writerows(source)
    print(json.dumps(dict(primary_labels_identical=True,summary_rows_identical=len(comparison),raw_comparison_counts=counts)))
if __name__=='__main__':main()
