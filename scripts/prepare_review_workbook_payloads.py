"""Prepare blank real templates and explicit SYNTHETIC workbook-only fixtures."""
import copy
import json
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from review_import import SCORE_HEADERS,FACT_HEADERS,ADJ_HEADERS
from test_evaluation_analysis import synthetic_fixture

BASE=ROOT/'research/2026-10-27_evaluation_fixes_v2'
TEMP=ROOT/'_test_runs/review_import_v2'
THREAD='01a15800-7529-7ee0-b82c-8428c7746a68'


def sheets_for(plan,labels=None,person=''):
    scores=[SCORE_HEADERS];facts=[FACT_HEADERS];adj=[ADJ_HEADERS]
    labels=labels or {}
    for p in plan:
        scores.append([p['answer_id'],p['case_id'],person,*([None]*8)])
        for fid in p['required_fact_ids']:
            facts.append([p['answer_id'],p['case_id'],None,fid,labels.get(fid,'SYNTHETIC_FACT'),None,None])
        adj.append([p['answer_id'],p['case_id'],*([None]*6)])
    return {'评分表':scores,'逐事实':facts,'裁决':adj}


def main():
    TEMP.mkdir(parents=True,exist_ok=True)
    package=BASE/'package'
    plan=json.loads((package/'planning/analysis_plan.json').read_text(encoding='utf-8'))
    facts=json.loads((package/'review_only/fact_items_DRAFT.json').read_text(encoding='utf-8'))
    labels={r['fact_id']:r['required_fact'] for items in facts.values() for r in items}
    actual=BASE/'outputs'/THREAD/'review_form_blank.xlsx'
    artifacts=[{'path':str(actual),'copy_to':str(package/'review_only/review_form_blank.xlsx'),
        'kind':'REAL_TEMPLATE_ALL_HUMAN_FIELDS_BLANK','sheets':sheets_for(plan,labels),
        'preview_dir':str(actual.parent)}]
    synthetic,execution,_=synthetic_fixture()
    (TEMP/'synthetic_plan.json').write_text(json.dumps(synthetic,indent=2)+'\n',encoding='utf-8')
    (TEMP/'synthetic_execution.json').write_text(json.dumps(execution,indent=2)+'\n',encoding='utf-8')
    a=sheets_for(synthetic,person='SYNTHETIC_REVIEWER_A')
    b=sheets_for(synthetic,person='SYNTHETIC_REVIEWER_B')
    for sheets in (a,b):
        for row in sheets['评分表'][1:]:row[3:]=[1,1,1,1,'完成','否','','SYNTHETIC_ONLY_NOT_PAPER_DATA']
        for row in sheets['逐事实'][1:]:row[5:]=['正确','SYNTHETIC_ONLY_NOT_PAPER_DATA']
    for row in b['评分表'][1:]:
        if row[0].startswith('llm'):row[7]='未交付'
        if row[0].startswith('agent'):
            row[3:7]=[None]*4;row[7]='不可评分';row[8]='待核对';row[9]='SYNTHETIC: no readable answer'
    for row in b['逐事实'][1:]:
        if row[0].startswith('llm'):row[5]='缺失'
        if row[0].startswith('agent'):row[5]='未评分'
    adjud=sheets_for(synthetic)
    for row in adjud['裁决'][1:]:
        if row[0].startswith(('llm','agent')):
            row[2:]=['SYNTHETIC_HUMAN_C','SYNTHETIC_ONLY_NOT_PAPER_DATA','未交付','否','f1','缺失']
    for name,sheets in [('reviewer_A',a),('reviewer_B',b),('adjudication',adjud)]:
        artifacts.append({'path':str(TEMP/(name+'.xlsx')),'kind':'SYNTHETIC_CHECK_ONLY_NOT_PAPER_DATA',
            'sheets':sheets,'preview_dir':str(TEMP/name)})
    path=TEMP/'authoring_payloads.json'
    path.write_text(json.dumps({'artifacts':artifacts},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('Prepared 1 blank review workbook and 3 SYNTHETIC fixtures. No real scores filled.')


if __name__=='__main__':main()
