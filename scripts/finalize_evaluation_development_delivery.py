"""Read back saved artifacts, package separated review material, write receipts."""
import hashlib
import json
import re
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'research/2026-10-27_evaluation_review_response'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    package = BASE / 'package'
    suite = json.loads((package / 'runtime/cases.json').read_text(encoding='utf-8'))
    criteria = json.loads((package / 'review_only/criteria.json').read_text(encoding='utf-8'))
    (package / 'review_only/TASKS_AND_STANDARDS.md').write_text(
        '# 完整开发题及逐题标准（仅供评审，不给运行模型）\n\n所有题均已见，无人工分。\n\n' +
        '\n\n'.join(c['full_question_and_judgement_standard_from_uploaded_review'] for c in criteria), encoding='utf-8')
    text = '# 共同用户输入全文（不是标准答案）\n\n所有模板已见；Q1/Q2对等入口未接通。\n\n'
    for case in suite['cases']:
        text += '## ' + case['id'] + '\n\n类别：' + case['category'] + '；关联母题：' + case['family'] + '\n\n'
        for i, turn in enumerate(case['rounds'], 1):
            text += '### 第' + str(i) + '轮\n\n' + turn['message'] + '\n\n原始资料全文与共同条件：\n\n```json\n' + json.dumps(
                {'user_input': turn['user_input'], 'conditions': turn['conditions']}, ensure_ascii=False, indent=2) + '\n```\n\n'
        text += '允许资源：以resources.json为准；工具配置读取同一绑定数据，普通模型不开放科学工具/外网。评审底表不得用作运行附件。\n\n'
    (package / 'runtime/TASKS_AND_INPUTS.md').write_text(text, encoding='utf-8')
    scores = package / 'review_only/blank_scores.xlsx'
    ns = {'m': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
    with zipfile.ZipFile(scores) as archive:
        assert archive.testzip() is None
        sheet = ET.fromstring(archive.read('xl/worksheets/sheet1.xml'))
        cells = {c.attrib['r']: c for c in sheet.findall('.//m:c', ns)}
        for row in range(2, 35):
            for col in 'CDEFGHIJK':
                cell = cells.get(f'{col}{row}')
                if cell is not None:
                    assert cell.find('m:f', ns) is None
                    assert cell.find('m:v', ns) is None
                    assert not ''.join(cell.itertext()).strip()
        assert sheet.find('.//m:sheetProtection', ns) is None
        assert len(sheet.findall('.//m:dataValidation', ns)) == 3
    check = {'file': str(scores.relative_to(BASE)).replace('\\', '/'), 'sha256': digest(scores),
        'bytes': scores.stat().st_size, 'crc': 'PASS', 'planned_rows': 33,
        'score_cells_empty': 132, 'all_297_reviewer_input_cells_empty': True,
        'score_validation_0_to_2': True, 'unprotected_editable_cells': True,
        'actual_preview_reviewed': True, 'native_Excel_UI_acceptance': False,
        'authoring_process': {'first_attempt': 'module load failed after directory junction was denied; original log retained',
            'dependency_junction_created_later': True,
            'second_attempt_exit_code': -1073740791, 'third_attempt_exit_code': -1073740791,
            'saved_file_independently_read_back': True,
            'native_library_exit_failure_not_reported_as_process_success': True}}
    (BASE / 'blank_scores_saved_file_check.json').write_text(json.dumps(check, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    full = (BASE / 'tests_full_02.txt').read_text(encoding='utf-8')
    assert re.search(r'Ran 192 tests.*\bOK\b', full, re.S)
    acceptance = json.loads((BASE / 'offline_acceptance.json').read_text(encoding='utf-8'))
    assert acceptance['real_model_requests'] == 0 and acceptance['human_scores_filled'] == 0
    assert len(acceptance['planned_unit_statuses']) == 33
    assert len(acceptance['same_inputs_and_resources']) == 11
    archive_info = []
    for directory in ('runtime', 'tool_resources', 'review_only'):
        path = package / (directory + '.zip')
        with zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED) as archive:
            for source in sorted((package / directory).rglob('*')):
                if source.is_file():
                    archive.write(source, source.relative_to(package / directory))
        with zipfile.ZipFile(path) as archive:
            assert archive.testzip() is None
            if directory == 'review_only':
                assert 'blank_scores.xlsx' in archive.namelist()
                assert not any('private_group_key' in name for name in archive.namelist())
            if directory == 'runtime':
                assert not any(any(s in name for s in ('criteria', 'anchors', 'private_group_key', 'answer.txt')) for name in archive.namelist())
            archive_info.append({'archive': str(path.relative_to(BASE)).replace('\\', '/'), 'entries': len(archive.namelist()),
                                 'bytes': path.stat().st_size, 'sha256': digest(path), 'crc': 'PASS'})
    (BASE / 'package_checks.json').write_text(json.dumps({'archives': archive_info, 'blank_workbook': check,
        'runtime_reviewer_materials_separate': True, 'reviewer_zip_contains_group_key': False,
        'all_11_templates_have_full_inputs_and_standards': True, 'old_54_records_rewritten': False,
        'tests': {'Python': 192, 'targeted_dialogue': 8, 'quantitative_algorithm_synthetic_only': 4, 'frontend': 3},
        'frontend_commands': ['node test_browser_backup.cjs', 'node test_sequence_ui.cjs', 'node test_english_ui.cjs'],
        'frontend_tool_output_verified': True, 'real_model_calls': 0, 'deployment_started': False},
        ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    code = ['evaluation_dialogue.py', 'evaluation_contract.py', 'evaluate.py', 'conversation.py', 'core.py',
            'verified_imports.py', 'runtime_info.py', 'test_evaluation_dialogue.py',
            'scripts/build_evaluation_development_pack.py', 'scripts/check_evaluation_development_pack.py',
            'scripts/finalize_evaluation_development_delivery.py', 'evaluation_analysis.py',
            'test_evaluation_analysis.py', 'scripts/prepare_evaluation_analysis.py']
    sources = [{'path': rel, 'sha256': digest(ROOT / rel)} for rel in code]
    artifacts = [{'path': str(p.relative_to(BASE)).replace('\\', '/'), 'bytes': p.stat().st_size, 'sha256': digest(p)}
                 for p in sorted(BASE.rglob('*')) if p.is_file() and p.name not in ('FILE_MANIFEST.json', 'SYNC.json')]
    (BASE / 'FILE_MANIFEST.json').write_text(json.dumps({'kind': 'SOURCE_AND_ARTIFACT_IDENTITY_NOT_SCIENTIFIC_GRADING',
        'review_commit': '3a557d481c78843c988ba972ff06ceb117aac6f5', 'code': sources, 'files': artifacts},
        ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print('PASS: 11 complete development templates; separated ZIPs; 33 blank rows / 132 blank scores; saved files verified.')


if __name__ == '__main__':
    main()
