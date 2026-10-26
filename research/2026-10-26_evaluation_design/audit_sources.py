"""Read existing evidence; count cases and preserve source fingerprints. No API."""
import csv
import gzip
import hashlib
import json
import subprocess
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
REVIEWED_MAIN = '14b1958b58b416a7322edb76f187aa4584408f4c'
SOURCES = [
    'AGENTS.md', 'docs/USER_REQUIREMENTS.md',
    'references/CRISPR-GPT/README.md',
    'references/CRISPR-GPT/paper_extracted_text.txt',
    'evaluation_cases.example.json', 'evaluation_rubric.json', 'evaluate.py',
    'research/2026-10-22_fairness/three_arm/cases.json',
    'research/2026-10-22_fairness/three_arm/results.json.gz',
    'docs/reviews/20261022_1501_full_batch_review.md',
    'docs/reviews/20261023_2116_fast_paper_scope_and_codex_tasks.md',
    'data/candidates.tsv', 'data/VEGFA.fasta', 'data/historical_scores.tsv',
    'data/historical_near_matches.tsv', 'data/historical_IRGM_review.tsv',
    'data/user_ordered_sequences/20261024/sequence_synthesis_original.docx',
    'data/user_ordered_sequences/20261024/README.md',
    'data/user_ordered_sequences/20261024/sequence_records.json',
    'research/2026-10-24_candidate_v2/METHODS_EN.md',
    'research/2026-10-24_nearfull_complete/README.md',
    'research/2026-10-24_nearfull_complete/live/tool_export/input.json',
    'research/2026-10-24_nearfull_complete/live/tool_export/inspect_candidates.json',
    'research/2026-10-24_nearfull_complete/live/tool_export/verify_target.json',
    'research/2026-10-24_nearfull_complete/live/tool_export/score_candidates.json',
    'research/2026-10-24_nearfull_complete/live/tool_export/match_seed.json',
    'research/2026-10-24_nearfull_complete/live/tool_export/query_expression.json',
    'research/2026-10-24_nearfull_complete/live/tool_export/expression_source.json',
    'research/2026-10-24_nearfull_complete/live/tool_export/compile_report.json',
    'research/2026-10-24_nearfull_complete/live/ANSWER_CORRECTION_ZH.md',
    'research/2026-10-23_literature/development_protocol.json',
    'research/2026-10-24_followup/live/README.md',
]


def read_json(rel):
    raw = (ROOT / rel).read_bytes()
    if rel.endswith('.gz'):
        raw = gzip.decompress(raw)
    return json.loads(raw.decode('utf-8-sig'))


def read_tsv(rel):
    with (ROOT / rel).open(encoding='utf-8-sig', newline='') as stream:
        return list(csv.DictReader(stream, delimiter='\t'))


def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT, text=True).strip()


def main():
    current = read_json('evaluation_cases.example.json')['cases']
    previous = read_json('research/2026-10-22_fairness/three_arm/cases.json')['cases']
    records = read_json('research/2026-10-22_fairness/three_arm/results.json.gz')
    ids = [x['id'] for x in previous]
    actual = [(x['case_id'], x['group'], x['repeat']) for x in records]
    expected = {(case, arm, rep) for case in ids
                for arm in ('llm', 'workflow', 'agent') for rep in (1, 2, 3)}
    assert len(ids) == len(set(ids)) == 6
    assert [x['id'] for x in current] == ids
    assert len(records) == len(set(actual)) == 54 and set(actual) == expected
    assert len({x['answer_id'] for x in records}) == 54

    candidates = read_tsv('data/candidates.tsv')
    scores = read_tsv('data/historical_scores.tsv')
    assert len(candidates) == len({x['candidate_id'] for x in candidates}) == 9
    assert {x['candidate_id'] for x in scores} == {x['candidate_id'] for x in candidates}
    highest = max(scores, key=lambda x: float(x['oligoformer_scaled_score']))
    flag = read_tsv('data/historical_IRGM_review.tsv')
    assert highest['candidate_id'] == 'VEGFA_SD_3535'
    assert len(flag) == 1 and flag[0]['candidate_id'] == highest['candidate_id']
    assert flag[0]['query_definition'] == 'AUTHOR_G2_G20_19NT'
    assert flag[0]['mapped_gene'] == 'IRGM' and flag[0]['actual_mismatches'] == '1'

    prefix = 'research/2026-10-24_nearfull_complete/live/tool_export/'
    target = read_json(prefix + 'verify_target.json')['rows'][0]
    purchased_score = read_json(prefix + 'score_candidates.json')['rows'][0]
    expression = read_json(prefix + 'query_expression.json')
    counts = expression['candidate_summary'][0]
    assert target['candidate_id'] == purchased_score['candidate_id'] == counts['candidate_id']
    assert target['guide_core19_5to3'] == purchased_score['guide_core19_5to3']
    assert len(target['guide_core19_5to3']) == 19
    assert target['covered_transcripts'] == 18 and target['reference_transcript_count'] == 20
    assert purchased_score['not_N3_construct_simulation'] is True
    assert expression['source']['ranking_changed'] is False
    assert len(expression['source']['samples']) == 8

    files = []
    for rel in SOURCES:
        raw = (ROOT / rel).read_bytes()
        files.append({'path': rel, 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()})

    protected = ['data', 'evaluation_cases.example.json', 'evaluation_rubric.json',
                 'research/2026-10-22_fairness', 'research/2026-10-24_candidate_v2',
                 'research/2026-10-24_nearfull_complete', 'references/CRISPR-GPT',
                 'research/2026-10-23_literature', 'research/2026-10-24_followup']
    changed = git('diff', '--name-only', REVIEWED_MAIN, '--', *protected)
    assert not changed, f'Protected evidence differs from reviewed main: {changed}'

    result = {
        'kind': 'READ_ONLY_EXISTING_EVIDENCE_AUDIT_NOT_QUALITY_GRADING',
        'reviewed_main': REVIEWED_MAIN,
        'task_branch': git('branch', '--show-current'),
        'audited_working_head': git('rev-parse', 'HEAD'),
        'old_distinct_development_task_count': len(ids),
        'old_case_ids': ids, 'old_planned_and_recorded_cells': len(records),
        'old_complete_unique_6_by_3_by_3_coverage': True,
        'old_groups': dict(Counter(x['group'] for x in records)),
        'old_status_counts_NOT_quality_scores': dict(Counter(x['group'] + ':' + x['status'] for x in records)),
        'nine_refers_to_legacy_candidate_count': len(candidates),
        'legacy_highest_score_and_review_flag_same_candidate': {
            'candidate_id': highest['candidate_id'],
            'scaled_score_NOT_knockdown_percent': highest['oligoformer_scaled_score'],
            'query_definition': flag[0]['query_definition'],
            'mapped_gene': flag[0]['mapped_gene'],
            'mismatches': int(flag[0]['actual_mismatches']),
            'not_experimentally_demonstrated_off_target': True,
        },
        'purchased_case_existing_evidence': {
            'candidate_id': target['candidate_id'],
            'guide_core19_5to3': target['guide_core19_5to3'],
            'reference_transcript': target['reference_transcript'],
            'fixed_reference_coverage': [target['covered_transcripts'], target['reference_transcript_count']],
            'expression_counts': counts,
            'expression_changes_ranking': expression['source']['ranking_changed'],
            'sample_expressed_isoform_or_target_read_coverage_checked_by_this_audit': False,
            'physical_N3_construct_simulated': False,
        },
        'new_design_status': 'DISCUSSION_DRAFT_ONLY_NOT_RUNNABLE_FINAL_CASESET',
        'new_problem_type_count_NOT_independent_test_sample_size': 9,
        'new_model_calls': 0, 'new_scientific_computation_runs': 0,
        'new_evaluation_runs': 0, 'human_quality_scores_filled': 0,
        'deployment_attempted': False,
        'protected_evidence_changed_from_reviewed_main': [],
        'source_files': files,
    }
    (OUT / 'audit.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print('PASS: 6 seen cases; 54 unique planned cells; 9 legacy candidates; existing sources unchanged.')
    print('No new model execution, scientific computation, human scores or deployment.')


if __name__ == '__main__':
    main()
