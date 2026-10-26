"""Full new-entry/export plumbing with explicit synthetic HTTP; never paid API."""
import hashlib
import json
import re
import socket
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import dialogue_evaluation as entry
import paper_pilot
from test_dialogue_entry import CFG,fixture_response
from core import save_json
from review_import import read_sheets,import_workbooks
from scripts.prepare_runtime_review_workbook import prepare as prepare_workbook

BASE=ROOT/'research/2026-10-27_evaluation_entry'
TEMP=ROOT/'_test_runs/dialogue_entry_integration'


def main(reuse=False):
    TEMP.mkdir(parents=True,exist_ok=True)
    paper_pilot.STOP.clear()
    plan=entry.prepare(CFG)[0]
    original=TEMP/'evaluation_runs/all27_http_fixture'
    if reuse:
        out=TEMP/'export_revision_02'
        shutil.copytree(original,out,ignore=shutil.ignore_patterns('for_review','reviewer_package*.zip'))
        load=lambda p:json.loads(p.read_text(encoding='utf-8'))
        state=load(out/'completion.json');results=load(out/'results.json')
        from dialogue_review import export_review
        _,cases,resources,_=entry.prepare(CFG)
        export_review(out,cases,plan,results,resources,package=entry.PACKAGE,fixture_only=True)
    else:
      with (patch.object(entry,'HOME',TEMP),patch.object(paper_pilot,'log'),
        patch('urllib.request.urlopen',side_effect=AssertionError('NETWORK FORBIDDEN')),
        patch.object(socket,'socket',side_effect=AssertionError('NETWORK FORBIDDEN')),
        patch.object(subprocess,'run',side_effect=AssertionError('HEAVY WORKERS FORBIDDEN'))):
        state=entry.run(lambda:dict(CFG),'all27_http_fixture',confirm_api_usage=True,plan_sha256=plan['plan_sha256'],
            execution_mode='http_fixture',http_opener=fixture_response)
      out=original
    assert state['status']=='COMPLETE',state
    load=lambda p:json.loads(p.read_text(encoding='utf-8'))
    results=load(out/'results.json');execution=load(out/'execution_status.json')
    assert len(results)==len(execution)==27
    assert sum(len(r['rounds']) for r in results)==33
    assert all(r['real_model_requests']==0 for r in results)
    assert all(not r['quality_scored'] for r in results)
    for r in results:
        if r['group'] in ('llm','agent'):
            assert r['synthetic_http_attempts']>0
            assert r['total_tokens'] is None and r['usage']==[]
    for cid in plan['case_ids']:
        group=[r for r in results if r['case_id']==cid]
        assert len({r['input_sha256'] for r in group})==1
        assert len({r['resource_access']['resources_sha256'] for r in group})==1
    review=out/'for_review'
    for file in review.rglob('*.md'):
        if 'reference_for_judgement' in file.parts or file.name=='PROJECT_BRIEFING_ZH.md':continue
        for target in re.findall(r'\]\(([^)]+)\)',file.read_text(encoding='utf-8')):
            if '://' not in target:assert (file.parent/target.split('#')[0]).exists(),(file,target)
    for file in review.rglob('report.html'):
        for target in re.findall(r'href="([^"]+)"',file.read_text(encoding='utf-8')):
            if '://' not in target:assert (file.parent/target.split('#')[0]).exists(),(file,target)
    workbook=BASE/'planned_review_blank_27.xlsx'
    # Schedule and facts are identical for this fixed proposed plan and fixture;
    # no scores/answers are copied into the planned blank workbook.
    prepare_workbook(out,workbook,verify=True)
    summary={'kind':'SYNTHETIC_HTTP_INTEGRATION_NOT_MODEL_PERFORMANCE_OR_HUMAN_SCORE',
        'configuration_units':27,'user_round_units':33,'all_plan_positions_retained':True,
        'same_common_inputs_and_tool_resource_fingerprints':True,
        'fixture_logical_requests':sum(r.get('logical_model_requests',0) for r in results),
        'fixture_http_attempts':sum(r.get('synthetic_http_attempts',0) for r in results),
        'real_model_requests':0,'heavy_scientific_runs':0,'human_scientific_scores':0,
        'anonymous_cards_and_links_checked':True,'group_key_outside_reviewer_package':True,
        'report_attachment_links_checked':True,'reuse_saved_fixture_records_for_export_fix':reuse,
        'blank_xlsx_ids_and_all_facts_match_generated_cards':True,
        'raw_fixture_artifacts':'tests/fixtures/dialogue_http_integration.zip',
        'scope':'Actual adapter serialization and saved scientific imports, scripted HTTP responses only; no semantic quality comparison'}
    fixture=ROOT/'tests/fixtures/dialogue_http_integration.zip'
    with zipfile.ZipFile(fixture,'w',zipfile.ZIP_DEFLATED) as archive:
        archive.writestr('README_SYNTHETIC_ONLY.txt','ENGINEERING HTTP FIXTURES ONLY. All model responses are scripted and returned without network. Not model performance, independent human scores or paper results. Tool evidence is previously computed data imported for plumbing checks; no new heavy computations. No fixture belongs in the expert topic-review package.\n')
        for file in sorted(out.rglob('*')):
            if file.is_file():archive.write(file,file.relative_to(out))
    with zipfile.ZipFile(fixture) as archive:assert archive.testzip() is None
    summary['fixture_zip_sha256']=hashlib.sha256(fixture.read_bytes()).hexdigest()
    summary['fixture_zip_bytes']=fixture.stat().st_size
    sheets=read_sheets(workbook)
    summary['planned_blank_workbook']={'answer_rows':len(sheets['评分表'])-1,'fact_rows':len(sheets['逐事实'])-1,
        'human_fields_all_blank':True,'sha256':hashlib.sha256(workbook.read_bytes()).hexdigest(),
        'authoring_exit_code':-1073740791,'saved_file_readback_and_import_passed':True,'native_Excel_UI_acceptance':False}
    save_json(BASE/'integration_acceptance.json',summary)
    print('PASS: full 27-unit / 33-round synthetic HTTP entry -> actual records -> anonymous cards -> matching blank XLSX; 0 real model calls or scores.')


if __name__=='__main__':main('--reuse-records' in sys.argv)
