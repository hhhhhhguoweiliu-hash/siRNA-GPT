"""Offline acceptance with saved tables and model STUBS; not performance scores."""
import hashlib
import json
import socket
import subprocess
import sys
import urllib.request
import zipfile
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import core
from evaluation_dialogue import run_dialogue, common_round, effective_input
from evaluation_contract import input_sha256
from test_evaluation_dialogue import test_stub

BASE = ROOT / 'research/2026-10-27_evaluation_fixes_v2'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check(package, out, summary):
    if out.exists() and any(out.iterdir()):
        raise ValueError('Use a fresh output directory; first failures are retained')
    suite = json.loads((package / 'runtime/cases.json').read_text(encoding='utf-8'))
    resources = json.loads((package / 'runtime/resources.json').read_text(encoding='utf-8'))
    cfg = {'model': 'TEST_MODEL_STUB_NOT_REAL_PROVIDER', 'provider': 'TEST_ONLY', 'thinking': 'disabled',
           'max_output_tokens': 1800, 'request_timeout': 90, 'api_retries': 1,
           'max_model_turns': 12, 'max_tool_calls': 18}
    for rel, record in resources['files'].items():
        assert sha(package / 'tool_resources' / rel) == record['sha256'], rel
        if rel.startswith('data/'):
            assert sha(ROOT / rel) == record['sha256'], ('actual core resource differs', rel)
    runtime_members = set(zipfile.ZipFile(package / 'runtime.zip').namelist())
    assert all(not any(x in p for x in ('review_only', 'anchors', 'private_group_key', 'criteria', 'answer.txt')) for p in runtime_members)
    extraction = json.loads((package / 'review_only/docx_extraction_receipt.json').read_text(encoding='utf-8'))
    assert extraction['extracted_text'] == ['GAUAGAGCAAGACAAGAAATT-N3（叠氮基团，用于点击化学）', 'UUUCUUGUCUUGCUCUAUCTT']
    assert not extraction['mapping_or_derivation_records_passed_to_runtime']
    review = json.loads((package / 'review_only/criteria.json').read_text(encoding='utf-8'))
    assert len(review) == len(suite['cases']) == 11
    assert all(c['full_question_and_judgement_standard_from_uploaded_review'] for c in review)
    blank = json.loads((package / 'review_only/blank_scores.json').read_text(encoding='utf-8'))
    assert len(blank) == 33
    for row in blank:
        assert all(row[key] == '' for key in row if key not in ('answer_id', 'case_id'))
    results, cells, common_proofs, request_proofs, reads = [], [], [], [], []
    original_read = core.read_tsv
    def tracked_read(path):
        reads.append(str(Path(path).relative_to(ROOT)).replace('\\', '/') if Path(path).is_relative_to(ROOT) else str(path))
        return original_read(path)
    def denied(*args, **kwargs):
        raise AssertionError('OFFLINE_ACCEPTANCE: network/heavy scientific worker forbidden')
    # These guards fail closed if future refactoring accidentally adds a real call.
    with patch.object(socket, 'create_connection', side_effect=denied), \
         patch.object(urllib.request, 'urlopen', side_effect=denied), \
         patch.object(core.Session, 'worker', side_effect=denied), \
         patch.object(core, 'read_tsv', side_effect=tracked_read):
        for case in suite['cases']:
            per_case = []
            if case['category'] == 'literature_qa':
                for group in ('llm', 'workflow', 'agent'):
                    cells.append({'case_id': case['id'], 'group': group, 'execution': 'NOT_EXECUTED',
                                  'reason': 'QA_RESOURCES_AND_INTERFACES_NOT_YET_COMPARABLE'})
                continue
            for group in ('llm', 'workflow', 'agent'):
                reads_start = len(reads)
                result = run_dialogue(group, case, cfg, out / case['id'] / group,
                    None if group == 'workflow' else test_stub, resources)
                actual_reads = reads[reads_start:]
                if case['id'] == 'R4':
                    assert 'data/expression.tsv.gz' not in actual_reads
                for request in result['test_prepared_requests']:
                    data = json.loads(request['payload']['messages'][1]['content'])
                    inp = data['input']
                    number = request['round'] - 1
                    expected = common_round(case['rounds'][number])
                    assert inp['task']['shared_user_input'] == expected
                    assert inp['task']['own_history'] == result['rounds'][number]['history_before']
                    user_text = json.dumps(inp, ensure_ascii=False)
                    for forbidden in ('sequence_checks', 'review_only', 'ANSWER_CORRECTION', 'full_question_and_judgement_standard', 'coordinates_independently_found'):
                        assert forbidden not in user_text, forbidden
                    if group == 'llm':
                        assert 'tools' not in request['payload']
                        if case['id'] != 'R2':
                            assert 'oligoformer_scaled_score' not in user_text
                            assert '1.121934400320053' not in user_text
                            assert '0.9915144175887107' not in user_text
                    request_proofs.append({'case_id': case['id'], 'group': group, 'round': request['round'],
                        'record_kind': 'PREPARED_TEST_STUB_REQUEST_NOT_SENT_TO_PROVIDER',
                        'shared_user_input_sha256': input_sha256(expected),
                        'own_history_sha256': input_sha256(inp['task']['own_history']),
                        'payload_sha256': input_sha256(request['payload']),
                        'same_effective_model_settings': request['effective_settings'],
                        'ordinary_model_has_no_tools': group != 'llm' or 'tools' not in request['payload']})
                if case['id'] == 'U1':
                    assert result['rounds'][1]['history_before'] == result['rounds'][0]['history_after']
                if group == 'workflow' and case['id'] == 'W2b':
                    assert '0.9915144175887107' in result['answer'] and '未评分' not in result['answer']
                if group == 'workflow' and case['id'] == 'W3':
                    for value in ('VEGFA_SD_3535', 'VEGFA_SD_3499', 'AUTHOR_G2_G20_19NT', 'NR_170598.1:1724–1742', 'IRGM'):
                        assert value in result['answer']
                if case['id'] == 'R2' and group != 'llm':
                    assert 'score_candidates' not in result['completed_tools']
                if case['id'] == 'R4' and group != 'llm':
                    assert 'score_candidates' in result['completed_tools'] and 'match_seed' in result['completed_tools']
                    assert 'query_expression' not in result['completed_tools']
                result['actual_tsv_reads'] = actual_reads
                results.append(result)
                per_case.append(result)
                cells.append({'case_id': case['id'], 'group': group, 'execution': 'OFFLINE_ACCEPTANCE_ONLY',
                              'status_NOT_quality': result['status'], 'rounds': len(result['rounds']),
                              'real_model_requests': 0, 'test_stub_requests': result['test_stub_requests']})
            assert len({r['input_sha256'] for r in per_case}) == 1
            assert len({r['resource_access']['resources_sha256'] for r in per_case}) == 1
            for number in range(len(case['rounds'])):
                hashes = {r['rounds'][number]['common_input_sha256'] for r in per_case}
                assert len(hashes) == 1
                common_proofs.append({'case_id': case['id'], 'round': number + 1,
                    'identical_complete_common_input_in_all_three_arms': True,
                    'sha256': hashes.pop(), 'ordinary_model_tool_access': False,
                    'workflow_agent_resource_availability_identical': True,
                    'both_tool_arms_expression_policy': case['rounds'][number]['conditions']['allow_builtin_expression']})
    unchanged = subprocess.check_output(['git', 'diff', '--name-only', '2623c8601bd4b19b472fafc520b95c0cfd0a0fdb', '--',
        'data', 'references', 'evaluation_cases.example.json', 'evaluation_rubric.json',
        'research/2026-10-22_fairness', 'research/2026-10-24_candidate_v2', 'research/2026-10-24_nearfull_complete'], cwd=ROOT, text=True).strip()
    assert not unchanged, unchanged
    summary.parent.mkdir(parents=True, exist_ok=True)
    payload = {'kind': 'OFFLINE_ACCEPTANCE_NOT_AGENT_PERFORMANCE_OR_HUMAN_SCORE',
        'review_commit': 'f665696dd844a97d21270198f12f5bf234710f90',
        'original_task_review_commit': '3a557d481c78843c988ba972ff06ceb117aac6f5',
        'latest_main_read': '2623c8601bd4b19b472fafc520b95c0cfd0a0fdb',
        'development_templates': 11, 'offline_case_configuration_units': len(results),
        'offline_round_configuration_units': sum(len(r['rounds']) for r in results),
        'qa_units_explicitly_not_executed': 6, 'all_33_planned_units_retained': len(cells) == 33,
        'real_model_requests': 0, 'heavy_scientific_runs': 0, 'human_scores_filled': 0,
        'network_and_scientific_worker_guard': 'ENFORCED', 'protected_old_inputs_and_evidence_changed': [],
        'same_inputs_and_resources': common_proofs, 'prepared_request_checks': request_proofs,
        'planned_unit_statuses': cells,
        'unsupported': ['Q1/Q2 equal retrieval in fixed workflow and Agent evaluation',
            'new pack not connected to authenticated website usage-confirmation and paid model launch',
            'independently authored unseen tasks and real human scoring',
            'arbitrary new sequences or 65-candidate cloud heavy computation'],
        'scope': 'Actual sequence/reference checks and imports of saved tables; scripted models only; no scientific quality comparisons'}
    summary.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    with zipfile.ZipFile(summary.parent / 'offline_raw_records.zip', 'w', zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(out.rglob('*')):
            if path.is_file():
                archive.write(path, path.relative_to(out))
    archive_path = summary.parent / 'offline_raw_records.zip'
    with zipfile.ZipFile(archive_path) as archive:
        assert archive.testzip() is None
        archive_info = {'path': archive_path.name, 'bytes': archive_path.stat().st_size, 'sha256': sha(archive_path),
            'entries': len(archive.namelist()), 'crc': 'PASS',
            'files': [{'path': p.filename, 'bytes': p.file_size, 'sha256': hashlib.sha256(archive.read(p)).hexdigest()} for p in archive.infolist()]}
    (summary.parent / 'offline_archive_receipt.json').write_text(json.dumps(archive_info, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    # Readable deterministic examples, never promoted to model answers.
    for result in results:
        if result['group'] == 'workflow':
            dest = summary.parent / 'fixed_workflow_examples' / (result['case_id'] + '.md')
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text('# 固定流程的本轮离线交付，不是模型回答\n\n' + '\n\n'.join(
                '## 第' + str(r['round']) + '轮\n\n' + r['answer'] for r in result['rounds']), encoding='utf-8')
    print('PASS: 27 offline configuration units / 33 user-round units; 6 QA units explicitly unsupported; 0 real model calls.')
    return payload


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--package', type=Path, default=BASE / 'package')
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--summary', type=Path, default=BASE / 'offline_acceptance.json')
    args = parser.parse_args()
    check(args.package, args.output, args.summary)
