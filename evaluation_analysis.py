"""Read HUMAN ratings; preserve missing values and paired task denominators.

No model calls, automatic semantic grading, plotting or alteration of raw runs.
Synthetic algorithm checks live only in test_evaluation_analysis.py.
"""
import argparse
import json
from collections import defaultdict
from pathlib import Path

DIMENSIONS = ('accuracy_0_2', 'evidence_0_2', 'task_fit_0_2', 'limits_0_2')
GROUPS = ('llm', 'workflow', 'agent')
DELIVERY = ('完成', '部分完成', '未交付')


def mean(values):
    return sum(values) / len(values) if values else None


def completion_conflicts(delivery, facts, severe):
    """Flag contradictions; never replace a human's label or scores."""
    if delivery != '完成':return []
    issues=[]
    for fact, value in facts.items():
        if value in ('wrong','missing'):issues.append({'code':'NECESSARY_FACT_NOT_CORRECT','fact_id':fact,'value':value})
        elif value not in ('correct',):issues.append({'code':'NECESSARY_FACT_UNSCORED','fact_id':fact})
    if severe is True:issues.append({'code':'BLOCKING_SEVERE_ERROR_WITH_COMPLETE_LABEL'})
    elif severe is None or severe == '':issues.append({'code':'SEVERE_ERROR_JUDGEMENT_PENDING'})
    return issues


def summarize(plan, execution, reviews, adjudications=(), minimum_reviewers=2):
    units = {p['answer_id']: p for p in plan}
    if not plan or len(units) != len(plan):
        raise ValueError('计划单元ID重复或为空')
    seen = set()
    case_groups = defaultdict(set)
    families = {}
    for p in plan:
        facts=p['required_fact_ids']
        if not facts or len(facts)!=len(set(facts)) or any(not isinstance(f,str) or not f for f in facts):
            raise ValueError('预定必要事实不能为空、重复或删除；按运行前审核的计划核对')
        key = (p['case_id'], p['group'], p['repeat'])
        if key in seen or p['group'] not in GROUPS:
            raise ValueError('题/组/重复重复或组别未知')
        seen.add(key)
        case_groups[p['case_id']].add(p['group'])
        signature = (p['category'], p['family'], tuple(p['required_fact_ids']))
        if p['case_id'] in families and families[p['case_id']] != signature:
            raise ValueError('同题三组的类别/母题/所需事实不一致')
        families[p['case_id']] = signature
    if any(g != set(GROUPS) for g in case_groups.values()):
        raise ValueError('三组计划题目分母不一致')
    actual = {e['answer_id']: e for e in execution}
    if len(actual) != len(execution) or set(actual) != set(units):
        raise ValueError('实际状态必须覆盖全部计划单元，不得漏掉失败或未运行')
    if any(e.get('execution') not in ('ATTEMPTED', 'NOT_EXECUTED') for e in execution):
        raise ValueError('执行状态无效；程序状态不是人工完成判定')
    grades = defaultdict(list)
    grade_ids = set()
    unfilled = 0
    for r in reviews:
        aid = r.get('answer_id')
        if aid not in units:
            raise ValueError('评分包含未知计划ID')
        values = [r.get(k) for k in DIMENSIONS] + [r.get('delivery_judgement'), r.get('severe_error')]
        facts = r.get('facts', {})
        if not r.get('reviewer_id') and all(x in (None, '') for x in values) and all(v in (None, '') for v in facts.values()):
            unfilled += 1
            continue
        if not r.get('reviewer_id'):
            raise ValueError('有评分但没有真人评审编号')
        key = (aid, r['reviewer_id'])
        if key in grade_ids:
            raise ValueError('同评审对同单元重复评分')
        grade_ids.add(key)
        if actual[aid]['execution'] != 'ATTEMPTED':
            raise ValueError('不能为未运行单元填写质量分或完成判定')
        for k in DIMENSIONS:
            v = r.get(k)
            if v not in (None, '') and (type(v) is not int or v not in (0, 1, 2)):
                raise ValueError('人工分必须是0/1/2或空白，不能自动填零')
        if r.get('delivery_judgement') not in (None, '', *DELIVERY):
            raise ValueError('完成判定无效')
        if r.get('severe_error') not in (None, '') and type(r.get('severe_error')) is not bool:
            raise ValueError('严重错误需真人判定布尔值或留空')
        required = set(units[aid]['required_fact_ids'])
        if set(facts) != required or any(v not in (None, '', 'correct', 'wrong', 'missing') for v in facts.values()):
            raise ValueError('必须逐项保留全部预定事实；正确/错误/缺失与未评分空白分开')
        if any(r.get(k) in (None, '') for k in DIMENSIONS) and not r.get('unscorable_reason'):
            raise ValueError('人工分空白需给不可评分原因')
        grades[aid].append(r)
    decisions = {r['answer_id']: r for r in adjudications}
    if len(decisions) != len(adjudications) or set(decisions) - set(units):
        raise ValueError('裁决ID重复或不属于计划')
    if any(not d.get('adjudicator_id') or not d.get('reason') for d in decisions.values()):
        raise ValueError('分歧裁决需真人编号和依据')
    for aid,d in decisions.items():
        if actual[aid]['execution'] != 'ATTEMPTED':raise ValueError('不能为未运行单元填写真人裁决')
        if d.get('delivery_judgement') not in (None,'',*DELIVERY):raise ValueError('真人裁决交付标签无效')
        if d.get('severe_error') not in (None,'') and type(d['severe_error']) is not bool:raise ValueError('真人裁决严重错误需为布尔值')
        if set(d.get('facts',{}))-set(units[aid]['required_fact_ids']):raise ValueError('裁决不能删除或替换预定必要事实')
        if any(v not in (None,'','correct','wrong','missing') for v in d.get('facts',{}).values()):raise ValueError('真人事实裁决标签无效')
    rows = []
    for aid, p in units.items():
        ratings = grades[aid]
        eligible = len(ratings) >= minimum_reviewers
        def consensus(key, allowed):
            values = [r.get(key) for r in ratings if r.get(key) not in (None, '')]
            if not eligible:return None
            # Explicit, attributed human correction may also fix unanimous but
            # internally contradictory ratings. Original ratings remain intact.
            decided=decisions.get(aid,{}).get(key)
            if decided in allowed:return decided
            if len(values)!=len(ratings):return None
            if len(set(values)) == 1:
                return values[0]
            value = decisions.get(aid, {}).get(key)
            if value not in allowed:
                return None
            return value
        delivery = consensus('delivery_judgement', DELIVERY)
        severe = consensus('severe_error', (True, False))
        fact_status = {}
        for fact in p['required_fact_ids']:
            values = [r['facts'][fact] for r in ratings]
            decided=decisions.get(aid,{}).get('facts',{}).get(fact)
            if eligible and decided in ('correct','wrong','missing'):
                fact_status[fact]=decided
            elif eligible and all(v not in (None, '') for v in values):
                if len(set(values)) == 1:
                    fact_status[fact] = values[0]
                else:
                    decided = decisions.get(aid, {}).get('facts', {}).get(fact)
                    fact_status[fact] = decided if decided in ('correct', 'wrong', 'missing') else None
            else:
                fact_status[fact] = None
        quality = {k: mean([r[k] for r in ratings]) if eligible and all(r.get(k) not in (None, '') for r in ratings) else None for k in DIMENSIONS}
        fraction = (sum(v == 'correct' for v in fact_status.values()) / len(fact_status)
                    if fact_status and all(v is not None for v in fact_status.values()) else None)
        issues=completion_conflicts(delivery,fact_status,severe)
        rows.append({**p, 'execution': actual[aid]['execution'], 'human_raters': len(ratings),
            'delivery_judgement': delivery, 'complete': None if delivery is None or issues else int(delivery == '完成'),
            'pending_human_consistency_check':bool(issues),'consistency_issues':issues,
            'original_rating_consistency_issues':[{'reviewer_id':r['reviewer_id'],
                'issues':completion_conflicts(r.get('delivery_judgement'),r['facts'],r.get('severe_error'))} for r in ratings],
            'severe_error': severe, 'facts': fact_status, 'fact_delivery_correct_fraction': fraction,
            'quality': quality, 'original_ratings': ratings, 'adjudication': decisions.get(aid),
            'seconds': actual[aid].get('seconds'), 'model_requests': actual[aid].get('model_requests'),
            'real_total_tokens': actual[aid].get('real_total_tokens')})
    tasks = []
    for cid in case_groups:
        for group in GROUPS:
            selected = [r for r in rows if r['case_id'] == cid and r['group'] == group]
            def task_mean(key):
                values = [r[key] for r in selected]
                return mean(values) if all(v is not None for v in values) else None
            quality = {k: mean([r['quality'][k] for r in selected]) if all(r['quality'][k] is not None and not r['pending_human_consistency_check'] for r in selected) else None for k in DIMENSIONS}
            tasks.append({'case_id': cid, 'group': group, 'category': selected[0]['category'],
                'family': selected[0]['family'], 'planned_repeats': len(selected),
                'completion_fraction': task_mean('complete'), 'fact_delivery_correct_fraction': task_mean('fact_delivery_correct_fraction'),
                'severe_error_fraction': task_mean('severe_error'), 'quality': quality})
    incomplete_run = any(e['execution'] != 'ATTEMPTED' for e in execution)
    summaries = []
    for category in sorted({p['category'] for p in plan}):
        category_incomplete = any(e['execution'] != 'ATTEMPTED' for aid, e in actual.items() if units[aid]['category'] == category)
        for group in GROUPS:
            selected = [t for t in tasks if t['category'] == category and t['group'] == group]
            def group_mean(key):
                values = [t[key] for t in selected]
                return mean(values) if not category_incomplete and all(v is not None for v in values) else None
            summaries.append({'category': category, 'group': group, 'task_count': len(selected),
                'category_run_complete': not category_incomplete,
                'metric_label': '可靠性检查通过比例' if category == 'reliability' else '规定任务完成比例',
                'family_count_NOT_independent_biological_samples': len({t['family'] for t in selected}),
                'completion_rate_percent': None if group_mean('completion_fraction') is None else 100 * group_mean('completion_fraction'),
                'fact_delivery_correct_percent': None if group_mean('fact_delivery_correct_fraction') is None else 100 * group_mean('fact_delivery_correct_fraction'),
                'severe_error_percent': None if group_mean('severe_error_fraction') is None else 100 * group_mean('severe_error_fraction'),
                'quality': {k: mean([t['quality'][k] for t in selected]) if not category_incomplete and all(t['quality'][k] is not None for t in selected) else None for k in DIMENSIONS},
                'quality_task_distributions': {k: [{'case_id': t['case_id'], 'score': t['quality'][k]} for t in selected] for k in DIMENSIONS},
                'quality_scoring_coverage':{k:{'scorable_task_count':sum(t['quality'][k] is not None for t in selected),
                    'unscorable_task_count':sum(t['quality'][k] is None for t in selected),
                    'total_task_count':len(selected)} for k in DIMENSIONS},
                'completion_case_fractions': [{'case_id': t['case_id'], 'fraction': t['completion_fraction']} for t in selected]})
    paired = []
    for category in sorted({p['category'] for p in plan}):
        lookup = {s['group']: s for s in summaries if s['category'] == category}
        for treatment, baseline in (('agent', 'llm'), ('workflow', 'llm'), ('agent', 'workflow')):
            a, b = lookup[treatment], lookup[baseline]
            av, bv = a['completion_rate_percent'], b['completion_rate_percent']
            def wins(dimension=None):
                counts = {'win': 0, 'tie': 0, 'loss': 0, 'unknown': 0}
                for cid in {t['case_id'] for t in tasks if t['category'] == category}:
                    pair = {t['group']: t for t in tasks if t['case_id'] == cid}
                    x = pair[treatment]['quality'][dimension] if dimension else pair[treatment]['completion_fraction']
                    y = pair[baseline]['quality'][dimension] if dimension else pair[baseline]['completion_fraction']
                    key = 'unknown' if x is None or y is None else 'win' if x > y else 'loss' if x < y else 'tie'
                    counts[key] += 1
                return counts
            paired.append({'category': category, 'configuration': treatment, 'baseline': baseline,
                'completion_percentage_point_difference': None if av is None or bv is None else av - bv,
                'completion_relative_change_percent': None if av is None or bv in (None, 0) else 100 * (av - bv) / bv,
                'quality_raw_scale_differences': {k: None if a['quality'][k] is None or b['quality'][k] is None else a['quality'][k] - b['quality'][k] for k in DIMENSIONS},
                'completion_task_win_tie_loss': wins(), 'quality_task_win_tie_loss': {k: wins(k) for k in DIMENSIONS}})
    return {'status': 'INCOMPLETE_OR_AWAITING_HUMAN_RATINGS' if incomplete_run or any(r['complete'] is None for r in rows) else 'HUMAN_DELIVERY_RATINGS_AVAILABLE',
        'minimum_human_reviewers_for_consensus': minimum_reviewers,
        'planned_units': len(plan), 'attempted_units': sum(e['execution'] == 'ATTEMPTED' for e in execution),
        'unfilled_rating_rows_ignored_not_zero': unfilled, 'unit_records': rows, 'task_equal_weight_records': tasks,
        'pending_human_consistency_units':[r['answer_id'] for r in rows if r['pending_human_consistency_check']],
        'category_summaries': summaries, 'paired_differences': paired,
        'human_ratings_are_not_created_by_this_program': True,
        'notes': ['No aggregation across work/change/reliability/QA categories', 'Family variants and technical repeats are not independent tasks',
                  'Missing ratings/usage remain null; zero-baseline relative change undefined', 'Completion and semantic severe-error consensus require real people',
                  'Original reviewer scores, disagreements and timing/usage remain in unit_records; no automatic scientific grading']}


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    for name in ('plan', 'execution', 'reviews', 'output'):
        p.add_argument('--' + name, type=Path, required=True)
    p.add_argument('--adjudications', type=Path)
    args = p.parse_args()
    if args.output.exists():
        p.error('Use a new output file, retaining earlier summaries')
    load = lambda path: json.loads(path.read_text(encoding='utf-8'))
    result = summarize(load(args.plan), load(args.execution), load(args.reviews), load(args.adjudications) if args.adjudications else [])
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
