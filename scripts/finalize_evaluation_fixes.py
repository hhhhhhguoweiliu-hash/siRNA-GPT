"""Read back actual v2 artifacts; never touch the prior reviewed package."""
import csv
import hashlib
import io
import json
import re
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from review_import import read_sheets, import_workbooks

BASE = ROOT / 'research/2026-10-27_evaluation_fixes_v2'
REVIEW = 'f665696dd844a97d21270198f12f5bf234710f90'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path):
    return json.loads(path.read_text(encoding='utf-8'))


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def main():
    package = BASE / 'package'
    suite = load(package / 'runtime/cases.json')
    criteria = load(package / 'review_only/criteria.json')
    assert len(suite['cases']) == len(criteria) == 11
    expected_label = 'Artificial development material, not an experimental observation'
    for case in suite['cases']:
        for turn in case['rounds']:
            note = turn['user_input'].get('constructed_material')
            assert note is None or note == expected_label
    assert next(c for c in criteria if c['case_id'] == 'R3')['construction_truth_REVIEW_ONLY']
    (package / 'review_only/TASKS_AND_STANDARDS.md').write_text(
        '# 完整开发题及逐题标准（仅评审使用）\n\n全部11题均已见，不能称独立未见测试；没有真实新回答或人工分。\n\n' +
        '\n\n'.join(c['full_question_and_judgement_standard_from_uploaded_review'] +
          ('\n\n构造真值（仅评审）：' + c['construction_truth_REVIEW_ONLY'] if c.get('construction_truth_REVIEW_ONLY') else '')
          for c in criteria), encoding='utf-8')
    text = '# 三组共同运行输入全文\n\n已见开发题，不含评审真值。Q1/Q2对等入口未接通。\n\n'
    for case in suite['cases']:
        text += '## ' + case['id'] + '\n\n类别：' + case['category'] + '；母题：' + case['family'] + '\n\n'
        for i, turn in enumerate(case['rounds'], 1):
            text += '### 第' + str(i) + '轮\n\n' + turn['message'] + '\n\n```json\n' + json.dumps(
                {'user_input': turn['user_input'], 'conditions': turn['conditions']}, ensure_ascii=False, indent=2) + '\n```\n\n'
        text += '允许资源见resources.json；普通模型没有科学工具/外网，固定流程和Agent读取相同绑定科学数据。不得传入评审材料。\n\n'
    (package / 'runtime/TASKS_AND_INPUTS.md').write_text(text, encoding='utf-8')
    shutil.copyfile(BASE / 'REVIEW_IMPORT.md', package / 'review_only/REVIEWER_INSTRUCTIONS.md')
    (package / 'review_only/README.md').write_text(
        '# 仅评审材料，当前没有真实新回答\n\n先读TASKS_AND_STANDARDS.md、criteria.json、anchors.json及fact_items_DRAFT.json。'
        '实际填写使用review_form_blank.xlsx（评分、逐事实、裁决三表），操作与导入规则见REVIEWER_INSTRUCTIONS.md。'
        '旧JSON空表仅作结构对照，不要求真人手工拼JSON。事实标准仍需独立人员审核。'
        '所有人工字段空白，不能给测试替身填科学分；组别对应只在planning/private_group_key.json，禁止随评审包发送。\n', encoding='utf-8')

    workbook = package / 'review_only/review_form_blank.xlsx'
    sheets = read_sheets(workbook)
    assert set(sheets) == {'评分表', '逐事实', '裁决'}
    assert len(sheets['评分表']) == len(sheets['裁决']) == 34
    assert len(sheets['逐事实']) == 211
    for _, row in sheets['评分表'][1:]:
        assert not any(str(v).strip() for v in row[2:])
    for _, row in sheets['逐事实'][1:]:
        assert not str(row[2]).strip() and not any(str(v).strip() for v in row[5:])
    for _, row in sheets['裁决'][1:]:
        assert not any(str(v).strip() for v in row[2:])
    ns = {'m': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
    with zipfile.ZipFile(workbook) as archive:
        assert archive.testzip() is None
        for name in archive.namelist():
            if name.startswith('xl/worksheets/sheet') and name.endswith('.xml'):
                tree = ET.fromstring(archive.read(name))
                assert tree.find('.//m:f', ns) is None
                assert tree.find('.//m:sheetProtection', ns) is None
    actual = import_workbooks(load(package / 'planning/analysis_plan.json'),
        load(package / 'planning/real_execution_NOT_STARTED.json'), [workbook])
    assert not actual['reviews']
    assert all(g['completion_rate_percent'] is None for g in actual['analysis']['category_summaries'])
    for path in (BASE / 'outputs').rglob('preview_*.png'):
        assert path.stat().st_size > 1000
    save(BASE / 'blank_workbook_check.json', {'path': str(workbook.relative_to(BASE)).replace('\\','/'),
        'sha256': digest(workbook), 'bytes': workbook.stat().st_size, 'crc': 'PASS',
        'answer_rows': 33, 'empty_four_dimension_cells': 132, 'fact_rows': 210,
        'all_human_score_fact_adjudication_fields_blank': True, 'formulas': 0, 'sheet_protection': False,
        'imported_real_reviews': 0, 'native_Excel_UI_acceptance': False,
        'actual_three_sheet_previews_reviewed': True,
        'authoring_exit': {'code': -1073740791, 'all_four_exports_saved_before_failure': True,
            'saved_files_independently_read_and_imported': True, 'log': 'workbook_build_01.txt'}})

    source_checks = []
    with zipfile.ZipFile(BASE / 'offline_raw_records.zip') as archive:
        assert archive.testzip() is None
        for case in ('W1', 'W2b', 'W3', 'R4'):
            paths = [name for name in archive.namelist() if name.startswith(case + '/workflow/') and name.endswith('/score_candidates.json')]
            assert paths
            for name in paths:
                data = json.loads(archive.read(name))
                for row in data['rows']:
                    src = row['score_source']
                    assert digest(ROOT / src['path']) == src['sha256']
                    if src['path'].endswith('.tsv'):
                        table = list(csv.DictReader(io.StringIO((ROOT/src['path']).read_text(encoding='utf-8')), delimiter='\t'))
                        original = next(r for r in table if r['candidate_id'] == row['candidate_id'])
                    else:
                        original = load(ROOT / src['path'])
                        assert digest(ROOT / src['manifest_path']) == src['manifest_sha256']
                    for field in ('candidate_id', 'guide_core19_5to3', 'mRNA_context_57nt'):
                        assert original[field] == row[field]
                    assert float(original['oligoformer_scaled_score']) == row['oligoformer_scaled_score']
                    answer = (BASE / 'fixed_workflow_examples' / (case+'.md')).read_text(encoding='utf-8')
                    assert src['path'] in answer and src['sha256'] in answer
                    source_checks.append({'case_id': case, 'candidate_id': row['candidate_id'],
                        'guide_core19_5to3': row['guide_core19_5to3'], 'mRNA_context_57nt': row['mRNA_context_57nt'],
                        'oligoformer_scaled_score': row['oligoformer_scaled_score'], 'score_source': src,
                        'saved_tool_record': 'offline_raw_records.zip!/' + name,
                        'exact_id_sequence_context_value_match': True, 'short_answer_actual_source_visible': True})
    save(BASE / 'source_correction/score_source_checks.json', {'kind': 'PRESENTATION_PROVENANCE_CHECK_NOT_RECOMPUTATION', 'rows': source_checks})

    # Read the actual XLSX fixtures through the CLI too. Numeric synthetic outputs
    # are shipped only as tests/fixtures, never as research performance results.
    temp = ROOT / '_test_runs/review_import_v2'
    cli_root = Path(tempfile.mkdtemp(prefix='cli_saved_', dir=temp))
    commands = []
    for label, adjud in [('pending', False), ('resolved', True)]:
        command = [sys.executable, 'review_import.py', '--plan', str(temp/'synthetic_plan.json'),
            '--execution', str(temp/'synthetic_execution.json'), '--workbooks', str(temp/'reviewer_A.xlsx'), str(temp/'reviewer_B.xlsx')]
        if adjud:command += ['--adjudication-workbook', str(temp/'adjudication.xlsx')]
        command += ['--output', str(cli_root/label)]
        completed = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, encoding='utf-8')
        assert completed.returncode == 0, completed.stderr
        result = load(cli_root/label/'analysis.json')
        expected = 'HUMAN_DELIVERY_RATINGS_AVAILABLE' if adjud else 'INCOMPLETE_OR_AWAITING_HUMAN_RATINGS'
        assert result['status'] == expected
        commands.append({'label': label, 'command': command, 'exit_code': completed.returncode,
            'stdout': completed.stdout, 'stderr': completed.stderr, 'expected_state_verified': True})
    fixture = ROOT / 'tests/fixtures/review_import_synthetic.zip'
    fixture.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(fixture, 'w', zipfile.ZIP_DEFLATED) as archive:
        archive.writestr('README.txt', 'SYNTHETIC ENGINEERING FIXTURES ONLY. All identities, scores and adjudications are constructed. NOT real model answers, human judgements or paper results. Reproduce with review_import.py; source plan and execution are synthetic. CLI result files are preserved, never mixed into research summaries.\n')
        for name in ('synthetic_plan.json','synthetic_execution.json','reviewer_A.xlsx','reviewer_B.xlsx','adjudication.xlsx'):
            archive.write(temp/name, name)
        for path in sorted(cli_root.rglob('*.json')):
            archive.write(path, 'cli_output/' + path.relative_to(cli_root).as_posix())
        archive.writestr('cli_commands.json', json.dumps(commands, ensure_ascii=False, indent=2))
    with zipfile.ZipFile(fixture) as archive:assert archive.testzip() is None
    save(BASE / 'review_import_cli_acceptance.json', {'kind': 'SYNTHETIC_CHECK_NOT_PAPER_DATA',
        'actual_CLI_exit_codes': [c['exit_code'] for c in commands],
        'pending_and_resolved_states_verified': True, 'real_template_scores_filled': 0,
        'fixture_path': fixture.relative_to(ROOT).as_posix(), 'fixture_sha256': digest(fixture),
        'synthetic_values_stored_only_in_test_fixtures': True})

    protected = ['data', 'references', 'evaluation_cases.example.json','evaluation_rubric.json',
        'research/2026-10-27_evaluation_review_response', 'research/2026-10-22_fairness',
        'research/2026-10-24_candidate_v2','research/2026-10-24_nearfull_complete']
    changed = subprocess.check_output(['git','diff','--name-only',REVIEW,'--',*protected], cwd=ROOT, text=True).strip()
    assert not changed, changed
    for case in ('W1','R4'):
        old = ROOT / 'research/2026-10-27_evaluation_review_response/fixed_workflow_examples' / (case+'.md')
        assert old.read_bytes() == (BASE / 'source_correction' / ('old_'+case+'_unchanged_copy.md')).read_bytes()
    full = (BASE / 'tests_full_02.txt').read_text(encoding='utf-8')
    assert re.search(r'Ran 204 tests.*\bOK\b', full, re.S)
    for name in ('test_browser_backup.cjs','test_sequence_ui.cjs','test_english_ui.cjs'):
        content = (BASE/(name+'.txt')).read_text(encoding='utf-8')
        assert 'PASS' in content or 'passed' in content
    acceptance = load(BASE/'offline_acceptance.json')
    assert acceptance['review_commit'] == REVIEW
    assert acceptance['real_model_requests'] == acceptance['human_scores_filled'] == 0
    assert acceptance['offline_case_configuration_units'] == 27
    assert acceptance['offline_round_configuration_units'] == 33
    assert len(acceptance['planned_unit_statuses']) == 33
    archive_info = []
    for directory in ('runtime','tool_resources','review_only'):
        path = package / (directory+'.zip')
        with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED) as archive:
            for source in sorted((package/directory).rglob('*')):
                if source.is_file():archive.write(source, source.relative_to(package/directory))
        with zipfile.ZipFile(path) as archive:
            assert archive.testzip() is None
            assert not any('private_group_key' in n for n in archive.namelist())
            if directory == 'runtime':
                assert not any(any(s in n for s in ('criteria','anchors','answer.txt','review_only')) for n in archive.namelist())
            if directory == 'review_only':assert 'review_form_blank.xlsx' in archive.namelist()
            archive_info.append({'path': path.relative_to(BASE).as_posix(),'bytes': path.stat().st_size,
                'sha256': digest(path),'entries': len(archive.namelist()),'crc':'PASS'})
    save(BASE/'package_checks.json', {'review_commit': REVIEW, 'archives': archive_info,
        'old_protected_paths': protected, 'old_protected_paths_changed': [], 'old_error_copies_byte_identical': True,
        'test_count': 204,'frontend_checks': 3,'real_model_requests':0,'heavy_scientific_runs':0,
        'human_scores_filled':0,'deployment_started':False,'runtime_answer_truth_separate':True})
    code = ['core.py','evaluation_contract.py','evaluation_dialogue.py','evaluation_protocol.py','evaluation_analysis.py',
        'review_import.py','test_evaluation_review_fixes.py','scripts/build_evaluation_development_pack.py',
        'scripts/check_evaluation_development_pack.py','scripts/prepare_evaluation_analysis.py',
        'scripts/check_evaluation_boundary_records.py','scripts/prepare_review_workbook_payloads.py',
        'scripts/build_review_workbooks.mjs','scripts/check_review_workbook_roundtrip.py','scripts/finalize_evaluation_fixes.py']
    save(BASE/'FILE_MANIFEST.json', {'kind':'FILE_IDENTITY_NOT_SCIENTIFIC_GRADING','review_commit':REVIEW,
        'code_hash_policy':'sha256 is exact local bytes; git_normalized_lf_sha256 allows Git checkout line-ending differences',
        'code':[{'path':p,'sha256':digest(ROOT/p),
            'git_normalized_lf_sha256':hashlib.sha256((ROOT/p).read_bytes().replace(b'\r\n',b'\n')).hexdigest()} for p in code],
        'files':[{'path':p.relative_to(BASE).as_posix(),'bytes':p.stat().st_size,'sha256':digest(p)}
            for p in sorted(BASE.rglob('*')) if p.is_file() and not p.name.startswith('finalize_')
            and p.name not in ('FILE_MANIFEST.json','SYNC.json','DELIVERY.md')]})
    print('PASS: v2 separated ZIPs, actual source rows, blank XLSX, two CLI imports, old evidence and 204/3 check logs verified.')


if __name__ == '__main__':main()
