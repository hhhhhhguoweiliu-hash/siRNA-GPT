"""Build a complete SEEN development pack, keeping answers outside runtime input."""
import copy
import csv
import hashlib
import io
import json
import random
import re
import shutil
import sys
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from core import save_json, read_tsv, fasta, revcomp
from evaluation_dialogue import common_round, effective_input, fixed_plan
from evaluation_contract import input_sha256
from verified_imports import calculation_candidate, DATASET

REVIEW = 'docs/reviews/20261027_evaluation_redesign_scientific_review.md'
BASE = ROOT / 'research/2026-10-27_evaluation_review_response'
ASSUMPTIONS = {'rows_written_5to3': True, 'guide_row': 2,
              'guide_core19_5to3': 'UUUCUUGUCUUGCUCUAUC',
              'passenger_core19_5to3': 'GAUAGAGCAAGACAAGAAA'}
TYPES = {'W1': ('work', 'purchased_complete'), 'W2': ('work', 'reference_score'),
         'W2b': ('work', 'reference_score'), 'W3': ('work', 'score_nearmatch_conflict'),
         'U1': ('change_request', 'reference_score'), 'R1': ('reliability', 'purchased_complete'),
         'R2': ('reliability', 'purchased_binding'), 'R3': ('reliability', 'coordinate_claim'),
         'R4': ('reliability', 'missing_expression'), 'Q1': ('literature_qa', 'score_seed_meaning'),
         'Q2': ('literature_qa', 'missing_experiment')}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def extract_order():
    path = ROOT / 'data/user_ordered_sequences/20261024/sequence_synthesis_original.docx'
    with zipfile.ZipFile(path) as archive:
        tree = ET.fromstring(archive.read('word/document.xml'))
    ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
    rows = [[''.join(t.text or '' for t in cell.findall('.//w:t', ns))
             for cell in row.findall('./w:tc', ns)] for row in tree.findall('.//w:tr', ns)]
    hits = [i for i, row in enumerate(rows) if row and row[0] == 'si-vegf']
    if len(hits) != 1:
        raise ValueError('原DOCX中的si-vegf名称不是唯一')
    i = hits[0]
    original = [rows[i][-1], rows[i + 1][-1]]
    return original, {'source': str(path.relative_to(ROOT)).replace('\\', '/'), 'sha256': sha(path),
        'method': 'word/document.xml table label EXACT si-vegf and following row; no sequence_records/README',
        'source_table_rows_1based': [i + 1, i + 2], 'extracted_text': original,
        'other_constructs_or_HIF_passed_to_runtime': False,
        'mapping_or_derivation_records_passed_to_runtime': False}


def conditions(**changes):
    value = {key: False for key in ('candidate_check', 'reference_check', 'score_check', 'seed_check',
        'expression_check', 'report_required', 'both_expression_states', 'compare_all_requested_candidates',
        'chain_assumption_provided')}
    value['allow_builtin_expression'] = True
    value.update(changes)
    return value


def build(out):
    out = Path(out)
    if out.exists() and any(out.iterdir()):
        raise ValueError('Use a new empty package directory, retaining prior builds')
    review = (ROOT / REVIEW).read_text(encoding='utf-8')
    sections = {m.group(1): m.group(0) for m in re.finditer(
        r'^### (W1|W2b|W2|W3|U1|R1|R2|R3|R4|Q1|Q2)：[^\n]+\n.*?(?=^### |^## |\Z)',
        review, flags=re.M | re.S)}
    assert set(sections) == set(TYPES)
    original, receipt = extract_order()
    candidates = read_tsv(ROOT / 'data/candidates.tsv')
    byid = {r['candidate_id']: r for r in candidates}
    one = [byid['VEGFA_SD_3499']]
    near = read_tsv(ROOT / 'data/historical_IRGM_review.tsv')
    purchased = {'original_order_lines': original, 'calculation_assumptions': ASSUMPTIONS}
    full = conditions(candidate_check=True, reference_check=True, score_check=True, seed_check=True,
                      expression_check=True, report_required=True, both_expression_states=True,
                      chain_assumption_provided=True)
    target = conditions(reference_check=True)
    score = conditions(score_check=True)
    changed = calculation_candidate(original, ASSUMPTIONS)
    changed['guide_core19_5to3'] = 'AUUCUUGUCUUGCUCUAUC'
    config = {
        'W1': [(purchased, full)],
        'W2': [({'candidate_rows': candidates}, target)],
        'W2b': [({'candidate_rows': one}, score)],
        'W3': [({'candidate_rows': [byid['VEGFA_SD_3535'], byid['VEGFA_SD_3499']],
                 'user_provided_evidence': {'near_match_review': near}},
                {**full, 'both_expression_states': False, 'chain_assumption_provided': False,
                 'compare_all_requested_candidates': True})],
        'U1': [({'candidate_rows': one}, target), ({'candidate_rows': one}, score)],
        'R1': [({'original_order_lines': original}, conditions()), (purchased, {**score, 'chain_assumption_provided': True})],
        'R2': [({'candidate_rows': [changed], 'original_order_lines': original,
                 'constructed_material': 'Artificial single-base mismatch, not an experimentally tested candidate'},
                conditions(candidate_check=True, chain_assumption_provided=True))],
        'R3': [({'candidate_rows': one, 'declared_core_coordinates': [{'candidate_id': 'VEGFA_SD_3499',
                 'reference': 'NM_003376.6', 'start_1based': 3610, 'end_1based': 3628}],
                 'constructed_material': 'Artificial wrong core-coordinate declaration; original candidate row preserved'}, target)],
        'R4': [({**purchased, 'constructed_material': 'User-required expression table intentionally absent; builtin fallback prohibited'},
                {**full, 'allow_builtin_expression': False})],
        'Q1': [({'candidate_rows': [], 'user_provided_evidence': {'software_context': {
            'OligoFormer_official_commit': 'e2f53ad63387bbe166bf123949151e2bc9bf6ec3',
            'SeedMatchR_version': '1.1.1', 'seed_label': 'mer7m8',
            'output_field_names': ['oligoformer_scaled_score', 'seed_site_count_nontarget', 'matched_genes'],
            'expression_input_type': 'untreated baseline TPM, not siRNA-treated RNA-seq'}}}, conditions())],
        'Q2': [(purchased, conditions(chain_assumption_provided=True))],
    }
    cases, standards = [], []
    for identity, (category, family) in TYPES.items():
        section = sections[identity]
        beginning = re.split(r'\*\*原始输入', section, maxsplit=1)[0]
        messages = re.findall('“([^”]+)”', beginning)
        assert len(messages) == len(config[identity]), (identity, len(messages))
        rounds = [{'message': text, 'user_input': copy.deepcopy(raw), 'conditions': dict(flags)}
                  for text, (raw, flags) in zip(messages, config[identity])]
        for value in rounds:
            effective_input(common_round(value))
        case = {'id': identity, 'request': messages[0], 'category': category, 'family': family,
                'seen_development': True, 'independent_heldout_case': False, 'rounds': rounds,
                'comparison_ready_offline': category != 'literature_qa'}
        cases.append(case)
        standards.append({'case_id': identity, 'category': category, 'family': family,
            'full_question_and_judgement_standard_from_uploaded_review': section,
            'necessary_evidence': '逐项按所附完整标准核对；保留实际交付附件与原答，不用底表替原答纠错',
            'allowed_answers': '按本题明确目的判断，允许有证据的不同建议；不强制匹配程序排名或单一工具顺序',
            'serious_errors': ['篡改序列或套用不一致版本', '编造实测值或把分数换成实测百分比',
                '把seed匹配或无警告当实验脱靶/安全认证', '引用不支持结论', '把缺失填零或未获许可回退内置表达'],
            'human_scores': {'accuracy_0_2': '', 'evidence_0_2': '', 'task_fit_0_2': '', 'limits_0_2': ''}})
    runtime = out / 'runtime'
    save_json(runtime / 'cases.json', {'schema': 'sirna-development-dialogue-v1',
        'review_status': 'SEEN_DEVELOPMENT_CASES_NOT_INDEPENDENT_TESTS_NO_NEW_MODEL_EXECUTION',
        'resource_manifest_file': 'resources.json', 'conditions_definition': {
            'candidate_check': '核对已给候选/绑定', 'reference_check': '核对靶参考',
            'score_check': '读取绑定分数', 'seed_check': '读取seed匹配', 'expression_check': '关联表达',
            'report_required': '输出完整报告', 'both_expression_states': '同份交付展示两状态',
            'compare_all_requested_candidates': '不隐藏被警告排除的指定比较对象',
            'allow_builtin_expression': '是否允许内置表达数据', 'chain_assumption_provided': '本轮已明确计算链假设'},
        'cases': cases})
    # Physically separate runtime inputs, scientific resources and grading answers.
    sources = ['data/candidates.tsv', 'data/VEGFA.fasta', 'data/historical_scores.tsv',
        'data/historical_seed_matches.tsv', 'data/historical_near_matches.tsv', 'data/historical_IRGM_review.tsv',
        'data/utr_gene_map.tsv', 'data/expression.tsv.gz', 'data/provenance.json']
    sources += [str(p.relative_to(ROOT)).replace('\\', '/') for p in sorted((ROOT / 'data' / DATASET).iterdir()) if p.is_file()]
    files = {}
    for rel in sources:
        source = ROOT / rel
        dest = out / 'tool_resources' / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, dest)
        files[rel] = {'sha256': sha(source), 'bytes': source.stat().st_size}
    lib = ROOT / 'research/2026-10-24_followup/offline/verification_02/expanded_library.zip'
    dest = out / 'tool_resources/library/expanded_library.zip'
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(lib, dest)
    files['library/expanded_library.zip'] = {'sha256': sha(lib), 'bytes': lib.stat().st_size,
        'source': str(lib.relative_to(ROOT)).replace('\\', '/'), 'qa_three_arm_access': 'NOT_YET_CONNECTED'}
    resources = {'policy': 'Same resource bytes and tool APIs for workflow/agent; no scientific tools for llm; no web',
                 'review_materials_are_not_tool_resources': True, 'files': files}
    save_json(runtime / 'resources.json', resources)
    save_json(out / 'review_only/criteria.json', standards)
    save_json(out / 'review_only/docx_extraction_receipt.json', receipt)
    p = out / 'review_only/source_originals/sequence_synthesis_original.docx'
    p.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(ROOT / receipt['source'], p)
    anchors = {'source_review_sha256': sha(ROOT / REVIEW), 'reference_sha256': sha(ROOT / 'data/VEGFA.fasta'),
        'coordinates_independently_found_from_fixed_FASTA': [], 'scores_original_rows': read_tsv(ROOT / 'data/historical_scores.tsv'),
        'supplied_IRGM_record_original': near}
    refs = fasta(ROOT / 'data/VEGFA.fasta')
    for row in candidates:
        guide = row['guide_paired_core_19nt_5to3']
        target_pattern = revcomp(guide)
        pos = refs['NM_003376.6'].find(target_pattern)
        assert pos >= 0
        anchors['coordinates_independently_found_from_fixed_FASTA'].append({'candidate_id': row['candidate_id'],
            'reference': 'NM_003376.6', 'start_1based': pos + 1, 'end_1based': pos + 19,
            'covered_transcripts': sum(target_pattern in r for r in refs.values()), 'reference_count': len(refs)})
    save_json(out / 'review_only/anchors.json', anchors)
    # These are existing records for reviewer lookup only, never request attachments.
    prefix = ROOT / 'research/2026-10-24_nearfull_complete/live/tool_export'
    for name in ('verify_target.json', 'score_candidates.json', 'match_seed.json', 'query_expression.json', 'expression_source.json'):
        dest = out / 'review_only/purchased_existing_evidence' / name
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(prefix / name, dest)
    units = [{'case_id': c['id'], 'group': group, 'repeat': 1} for c in cases for group in ('llm', 'workflow', 'agent')]
    random.Random(20261027).shuffle(units)
    for i, unit in enumerate(units, 1):
        unit['answer_id'] = 'D' + str(i).zfill(3)
        unit['execution'] = 'NOT_EXECUTED'
        unit['reason'] = 'OFFLINE_PACKAGE_ONLY; real paid evaluation not authorized' if unit['case_id'] not in ('Q1', 'Q2') else 'QA_INTERFACES_NOT_COMPARABLE'
    save_json(out / 'planning/private_group_key.json', units)
    blank = [{'answer_id': u['answer_id'], 'case_id': u['case_id'], 'reviewer_id': '',
        'accuracy_0_2': '', 'evidence_0_2': '', 'task_fit_0_2': '', 'limits_0_2': '',
        'delivery_judgement': '', 'severe_error': '', 'unscorable_reason': '', 'notes': ''} for u in units]
    save_json(out / 'review_only/blank_scores.json', blank)
    save_json(out / 'planning/budget_DRAFT_NOT_AUTHORIZATION.json', {
        'status': 'DRAFT_ONLY_NO_REAL_MODEL_RUNS', 'development_cases': len(cases),
        'offline_comparable_cases': 9, 'qa_separate_not_comparable': ['Q1', 'Q2'],
        'technical_repetitions_do_not_increase_independent_case_count': True,
        'future_real_entry': 'existing authenticated UI usage-confirmation mechanism; not yet connected for this new pack',
        'fixed_model_requests': 0, 'ordinary_model_requests_per_user_round': 1,
        'agent_model_requests_per_round_upper_bound': 13, 'agent_model_requests_per_case_upper_bound': 26,
        'tool_call_limit_per_round': 18, 'case_seconds_upper_bound_proposed': 720,
        'model_settings': {'model': 'same configured model for both model arms', 'thinking': 'disabled',
                           'max_output_tokens': 1800, 'request_timeout': 90, 'api_retries': 1},
        'money_cost': None, 'real_usage': None, 'human_scores': None,
        'stop_on_account_error_or_timeout': True, 'formal_unseen_12_case_set': 'NOT_CREATED; independent people required'})
    save_json(out / 'build_receipt.json', {'review_commit': '3a557d481c78843c988ba972ff06ceb117aac6f5',
        'source_review': REVIEW, 'source_review_sha256': sha(ROOT / REVIEW), 'case_count': len(cases),
        'round_counts': {c['id']: len(c['rounds']) for c in cases}, 'source_docx': receipt,
        'three_material_classes_physically_separate': True, 'runtime_contains_old_answers': False,
        'real_model_runs': 0, 'human_scores_filled': 0, 'scientific_heavy_recomputations': 0})
    (out / 'review_only/README.md').write_text(
        '# 评审材料，未评分\n\n先读完整题干与逐题判断标准criteria.json，再按anchors和已有证据核对实际交付。'
        'blank_scores.json及配套Excel所有评分栏留空。没有新的真实模型回答可评分；不得给测试替身填科研质量分。'
        '组别密钥在planning/private_group_key.json，不随匿名评审包发送。原文与失败不得改写。\n', encoding='utf-8')
    (runtime / 'README.md').write_text(
        '# 共同运行输入\n\ncases.json含11个已见开发模板的全文及两轮输入；Q1/Q2单列未具备对等入口。'
        '九条候选原始字段完整保留；订购输入只取原DOCX两行，计算链假设在明确提供的轮次加入。'
        'resources.json只列允许资源及指纹，实际表在另一个tool_resources目录。'
        'review_only、planning密钥和旧回答不能传入模型请求。固定流程按共同条件映射，不能按题号选路。\n', encoding='utf-8')
    for directory in ('runtime', 'tool_resources', 'review_only'):
        with zipfile.ZipFile(out / (directory + '.zip'), 'w', zipfile.ZIP_DEFLATED) as archive:
            for p in sorted((out / directory).rglob('*')):
                if p.is_file():
                    archive.write(p, p.relative_to(out / directory))
    print(json.dumps({'package': str(out), 'cases': len(cases), 'comparable_offline': 9,
                      'qa_not_comparable': 2, 'model_calls': 0}, ensure_ascii=False))
    return cases, resources


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, default=BASE / 'package')
    build(parser.parse_args().output)
