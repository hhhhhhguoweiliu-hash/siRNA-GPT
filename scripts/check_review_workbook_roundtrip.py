"""Read actual SYNTHETIC XLSX files; keep synthetic grades outside research data."""
import hashlib
import json
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from review_import import import_workbooks,read_sheets,parse_review_tables

BASE=ROOT/'research/2026-10-27_evaluation_fixes_v2'
TEMP=ROOT/'_test_runs/review_import_v2'


def main():
    load=lambda p:json.loads(Path(p).read_text(encoding='utf-8'))
    plan,execution=load(TEMP/'synthetic_plan.json'),load(TEMP/'synthetic_execution.json')
    files=[TEMP/'reviewer_A.xlsx',TEMP/'reviewer_B.xlsx']
    pending=import_workbooks(plan,execution,files)
    assert pending['analysis']['status']=='INCOMPLETE_OR_AWAITING_HUMAN_RATINGS'
    assert len(pending['reviews'])==6
    missing=next(r for r in pending['reviews'] if r['answer_id']=='agent1' and r['reviewer_id']=='SYNTHETIC_REVIEWER_B')
    assert missing['delivery_judgement'] is None and missing['severe_error'] is None
    assert missing['accuracy_0_2'] is None and missing['facts']['f1'] is None
    resolved=import_workbooks(plan,execution,files,TEMP/'adjudication.xlsx')
    assert resolved['analysis']['status']=='HUMAN_DELIVERY_RATINGS_AVAILABLE'
    assert all(u['complete'] is not None for u in resolved['analysis']['unit_records'])
    assert len(resolved['reviews'])==6 and len(resolved['adjudications'])==2
    try:import_workbooks(plan,execution,[files[0],files[0]])
    except ValueError as exc:assert '重复评审ID' in str(exc)
    else:raise AssertionError('duplicate independent reviewer not rejected')
    # The real review template remains wholly unfilled. Never grade test stubs.
    package=BASE/'package'
    actual_plan=load(package/'planning/analysis_plan.json')
    actual_execution=load(package/'planning/real_execution_NOT_STARTED.json')
    template=package/'review_only/review_form_blank.xlsx'
    blank=import_workbooks(actual_plan,actual_execution,[template])
    assert blank['reviews']==[]
    assert all(g['completion_rate_percent'] is None for g in blank['analysis']['category_summaries'])
    for name,content in [('synthetic_pending.json',pending),('synthetic_resolved.json',resolved)]:
        (TEMP/name).write_text(json.dumps(content,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    receipt={'kind':'SYNTHETIC_IMPORT_ALGORITHM_CHECK_NOT_MODEL_OR_PAPER_RESULTS',
        'two_independent_review_files_read':True,'raw_reviews_and_fact_rows_preserved':True,
        'unscorable_and_pending_flags_preserved_as_null':True,'duplicate_reviewer_id_rejected':True,
        'pending_then_attributed_human_adjudication_flow_checked':True,
        'synthetic_raw_files_location':'_test_runs/review_import_v2 (not paper results)',
        'real_template':{'path':'package/review_only/review_form_blank.xlsx','sha256':hashlib.sha256(template.read_bytes()).hexdigest(),
            'planned_answer_rows':33,'fact_rows':sum(len(p['required_fact_ids']) for p in actual_plan),
            'human_reviews_filled':0,'all_real_rates_and_differences_null':True},
        'native_Excel_UI_acceptance':False,'real_model_calls':0}
    (BASE/'review_import_acceptance.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('PASS: two synthetic review files -> import -> pending -> attributed adjudication; real template remains blank.')


if __name__=='__main__':main()
