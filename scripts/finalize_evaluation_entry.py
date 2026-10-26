"""Delivery checks and fingerprints; no models, grading or heavy science."""
import hashlib
import json
import re
import subprocess
import sys
import zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from core import save_json
from review_import import read_sheets
BASE=ROOT/'research/2026-10-27_evaluation_entry'
HANDOFF='6c9c02639872c97e0d2aad2d47ab8512bc52f129'


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    log=(BASE/'tests_full_03.txt').read_text(encoding='utf-8')
    assert re.search(r'Ran 214 tests.*\bOK\b',log,re.S)
    for name in ('test_browser_backup.cjs.txt','test_sequence_ui.cjs.txt','test_english_ui.cjs.txt','test_evaluation_ui_02.txt'):
        text=(BASE/name).read_text(encoding='utf-8');assert 'PASS' in text or 'passed' in text
    acceptance=json.loads((BASE/'integration_acceptance.json').read_text(encoding='utf-8'))
    assert acceptance['configuration_units']==27 and acceptance['user_round_units']==33
    assert acceptance['real_model_requests']==acceptance['heavy_scientific_runs']==acceptance['human_scientific_scores']==0
    fixture=ROOT/'tests/fixtures/dialogue_http_integration.zip'
    assert sha(fixture)==acceptance['fixture_zip_sha256']
    with zipfile.ZipFile(fixture) as z:
        assert z.testzip() is None and 'README_SYNTHETIC_ONLY.txt' in z.namelist()
    workbook=BASE/'planned_review_blank_27.xlsx';sheets=read_sheets(workbook)
    assert len(sheets['评分表'])==len(sheets['裁决'])==28 and len(sheets['逐事实'])==178
    for _,row in sheets['评分表'][1:]:assert not any(str(v).strip() for v in row[2:])
    for _,row in sheets['逐事实'][1:]:assert not str(row[2]).strip() and not any(str(v).strip() for v in row[5:])
    for _,row in sheets['裁决'][1:]:assert not any(str(v).strip() for v in row[2:])
    assert sha(workbook)==acceptance['planned_blank_workbook']['sha256']
    old=ROOT/'research/2026-10-24_nearfull_complete/live'
    practice=BASE/'expert_topic_review/practice'
    for name in ('conversation_export_original.json','actual_model_call_summary.json','ANSWER_CORRECTION_ZH.md','answer_sequence_discrepancy.json','actual_tool_export_original.zip'):
        assert sha(old/name)==sha(practice/name),name
    record=json.loads((old/'conversation_export_original.json').read_text(encoding='utf-8'))
    assert (practice/'actual_delivered_answer_UNCHANGED.txt').read_text(encoding='utf-8')==record['messages'][-1]['text']
    for copy in (practice/'actual_evidence').rglob('*'):
        if copy.is_file():assert sha(copy)==sha(old/'tool_export'/copy.relative_to(practice/'actual_evidence'))
    with zipfile.ZipFile(BASE/'expert_topic_review.zip') as z:
        assert z.testzip() is None
        assert not any('private_group' in n or 'synthetic' in n.lower() or 'http_attempt_' in n for n in z.namelist())
    protected=['data','references','evaluation_cases.example.json','evaluation_rubric.json',
        'research/2026-10-27_evaluation_fixes_v2','research/2026-10-27_evaluation_review_response',
        'research/2026-10-22_fairness','research/2026-10-24_candidate_v2','research/2026-10-24_nearfull_complete']
    changed=subprocess.check_output(['git','diff','--name-only',HANDOFF,'--',*protected],cwd=ROOT,text=True).strip()
    assert not changed,changed
    save_json(BASE/'delivery_checks.json',{'handoff_commit':HANDOFF,'Python_checks':214,'frontend_checks':4,
        'full_HTTP_fixture_units':27,'full_HTTP_fixture_rounds':33,'real_model_calls':0,
        'heavy_scientific_runs':0,'human_scores_filled':0,'old_protected_paths_changed':[],
        'old_practice_raw_answer_and_sources_unchanged':True,'blank_score_cells':108,'blank_fact_rows':177,
        'expert_pack_contains_synthetic_responses':False,'new_website_deployed':False,'merged_to_main':False,
        'native_browser_acceptance':False,'native_Excel_UI_acceptance':False,
        'workbook_authoring_exit_code':-1073740791,'saved_xlsx_readback_import_and_preview_verified':True,
        'new_tasks_independently_authored':False,'human_review_personnel_supplied_in_this_batch':False})
    names=['app.py','cloud.py','model_client.py','conversation.py','evaluation_dialogue.py','evaluation_protocol.py',
        'evaluation_transport.py','dialogue_evaluation.py','dialogue_review.py','evaluation_ui.js','runtime_info.py',
        'index.html','evaluate.py','test_dialogue_entry.py','test_evaluation_ui.cjs','scripts/build_expert_briefing_pack.py',
        'scripts/render_expert_reading_pages.py','scripts/check_dialogue_entry_integration.py',
        'scripts/prepare_runtime_review_workbook.py','scripts/build_review_workbooks.mjs','scripts/finalize_evaluation_entry.py']
    save_json(BASE/'FILE_MANIFEST.json',{'kind':'FILE_IDENTITY_AND_TEST_EVIDENCE_NOT_SCIENTIFIC_GRADING','handoff_commit':HANDOFF,
        'code_hash_policy':'Exact local bytes and normalized LF are both recorded for cross-platform checkout.',
        'code':[{'path':n,'sha256':sha(ROOT/n),'git_normalized_lf_sha256':hashlib.sha256((ROOT/n).read_bytes().replace(b'\r\n',b'\n')).hexdigest()} for n in names],
        'files':[{'path':p.relative_to(BASE).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(BASE.rglob('*'))
            if p.is_file() and p.name not in ('FILE_MANIFEST.json','DELIVERY.md','SYNC.json') and not p.name.startswith('finalize_')],
        'external_engineering_fixture':{'path':fixture.relative_to(ROOT).as_posix(),'bytes':fixture.stat().st_size,'sha256':sha(fixture)}})
    print('PASS: final logs, blank workbook, original practice bytes, separated expert/engineering packages and protected old assets verified.')


if __name__=='__main__':main()
