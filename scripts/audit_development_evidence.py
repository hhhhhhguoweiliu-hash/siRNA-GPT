"""Availability and tool-evidence audit of a real batch; no semantic scoring."""
import argparse,csv,gzip,json,collections
from pathlib import Path

def write(path,rows,fields):
    with path.open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields,delimiter='\t');w.writeheader();w.writerows(rows)

def main():
    p=argparse.ArgumentParser();p.add_argument('--batch',required=True);a=p.parse_args();base=Path(a.batch)
    with gzip.open(base/'results.json.gz','rt',encoding='utf-8') as f:results=json.load(f)
    metrics=list(csv.DictReader((base/'records.tsv').open(encoding='utf-8-sig'),delimiter='\t'))
    lookup={(r['case_id'],r['group'],r['repeat']):r for r in results};infra={r['answer_id']:r['infrastructure_error']=='True' for r in metrics}
    pairs=[]
    for cid in sorted({r['case_id'] for r in results}):
        for n in [1,2,3]:
            sub=[lookup.get((cid,g,n)) for g in ['llm','workflow','agent']]
            pairs.append({'case_id':cid,'repeat':n,'all_three_attempted':all(sub),
                'all_three_without_infrastructure_error':all(r and not infra[r['answer_id']] for r in sub),
                'missing_or_infrastructure_arms':';'.join(g for g,r in zip(['llm','workflow','agent'],sub) if not r or infra[r['answer_id']]),
                'scientific_quality_scored':False})
    write(base/'paired_availability.tsv',pairs,list(pairs[0]))
    errors=[];checks=[]
    for r in results:
        error=r.get('provider_error') or r.get('record',{}).get('result') or {}
        if r['status']=='FAILED':errors.append({'answer_id':r['answer_id'],'case_id':r['case_id'],'group':r['group'],'repeat':r['repeat'],
            'infrastructure_error':infra[r['answer_id']],'code':error.get('code',''),'provider_code':error.get('provider_code',''),
            'message':error.get('message') or r.get('answer',''),'semantic_grade':'NOT_SCORED'})
        tools=r.get('completed_tools',[]);plan=r.get('plan') or {}
        if r['group']=='agent' and r['status'] in ('COMPLETE','PARTIAL_COMPLETE'):
            expected=['inspect_candidates','verify_target'] if r['case_id']=='target_only' else ['inspect_candidates','verify_target','score_candidates','match_seed','query_expression','compile_report']
            # Scoring and seed matching are independent after target checks;
            # the model may legally swap them. Check coverage, not an invented order.
            assert set(tools)==set(expected) and len(tools)==len(expected),(r['answer_id'],tools)
            if r['case_id']!='target_only':
                state='Hypoxia' if r['case_id']=='normal_hypoxia' else 'Normoxia';top=2 if state=='Hypoxia' else 3
                assert plan['state']==state and plan['top_n']==top
                assert len(r['tool_results']['compile_report']['selected_for_review'])==top
            checks.append({'answer_id':r['answer_id'],'case_id':r['case_id'],'status':r['status'],'completed_tools':';'.join(tools),'plan_scope_and_evidence':'PASS','semantic_grade':'NOT_SCORED'})
    ids=[r['record']['id'] for r in results if r['group']=='agent'];assert len(ids)==len(set(ids))==18
    write(base/'failure_diagnostics.tsv',errors,list(errors[0]))
    write(base/'completed_agent_evidence_checks.tsv',checks,list(checks[0]))
    summary={'planned_units':54,'recorded_units':len(results),'independent_development_tasks':6,
        'technical_repeats':3,'unique_agent_conversations':len(ids),
        'infrastructure_error_records':sum(infra.values()),
        'three_arm_repeat_units_without_infrastructure_error':sum(r['all_three_without_infrastructure_error'] for r in pairs),
        'per_case_available_repeats':{cid:sum(r['all_three_without_infrastructure_error'] for r in pairs if r['case_id']==cid) for cid in sorted({r['case_id'] for r in pairs})},
        'completed_agent_scope_checks':len(checks),'scientific_quality_scored':False,
        'full_six_task_paired_quality_comparison_ready':False,
        'limitation':'Availability is not correctness. Clarifications and program failures still need independent scoring. The hypoxia task has no complete plain-LLM response in this batch.'}
    (base/'evidence_audit.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(summary,ensure_ascii=True))

if __name__=='__main__':main()
