"""Prepare blank HUMAN fields and an explicitly pending analysis, never grades."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from evaluation_analysis import summarize

BASE = ROOT / 'research/2026-10-27_evaluation_review_response'
FACTS = {
    'W1': ['原序列与条件性链角色', '参考坐标', '固定参考覆盖', '绑定scaled分数', '分数含义', '非靶seed位点',
           '去重非靶基因', '表达可映射基因', '两状态检出计数', '未映射基因', '未转染基线范围', '修饰实物限制'],
    'W2': ['逐条核对' + str(i) + '的序列/参考/核心坐标/覆盖与证据' for i in (1157, 2739, 3119, 3193, 3429, 3499, 3500, 3502, 3535)],
    'W2b': ['候选版本绑定', 'scaled原值及显示舍入', '分数来源', '预测与实测区别'],
    'W3': ['两候选分数', '分数高低关系', '查询窗口定义', '查询序列', 'IRGM参考坐标与错配', '科学局限', '建议目的及依据'],
    'U1': ['首轮序列/坐标/覆盖', '首轮范围', '次轮新增分数', '分数含义', '保留各自历史', '证据版本与新增/重做说明', '次轮范围'],
    'R1': ['首轮原始TT/N3保留', '链角色未供应商确认', '补齐明确假设后继续', '次轮参考/分数绑定', '化学实物限制'],
    'R2': ['新旧核心原样', '不迁移旧分数', '不据错误字段判生物学无效', '原订购来源保留', '需要的新核对'],
    'R3': ['声明越界', '实际序列匹配坐标', '元数据与序列区分', '不改原碱基'],
    'R4': ['禁止内置回退', '保留已有局部证据', 'seed实际进展', '表达明确缺失', '完整报告未完成', '所需表与来源'],
    'Q1': ['实际可定位官方引文', '分数定义', 'seed位点与基因数及局限', '版本适用范围', 'N3未模拟', '基线与处理后测量区别'],
    'Q2': ['指定测量缺口', '不编数或替换本项目测量', '所需对应条件测量', '不宣称全球均无研究', '检索/范围状态区分'],
}


def main():
    package = BASE / 'package'
    cases = {c['id']: c for c in json.loads((package / 'runtime/cases.json').read_text(encoding='utf-8'))['cases']}
    units = json.loads((package / 'planning/private_group_key.json').read_text(encoding='utf-8'))
    specs = {cid: [{'fact_id': cid + '_F' + str(i).zfill(2), 'required_fact': label,
        'answer_material': 'criteria.json and anchors.json; not runtime input',
        'tolerance': '序列与计数精确；scaled可显示四位小数但须保留原始数值及字段名；含义/建议由真人判断',
        'human_approved_before_real_run': ''} for i, label in enumerate(labels, 1)] for cid, labels in FACTS.items()}
    plan, execution, blanks = [], [], []
    for unit in units:
        cid = unit['case_id']
        ids = [f['fact_id'] for f in specs[cid]]
        plan.append({k: unit[k] for k in ('answer_id', 'case_id', 'group', 'repeat')} |
                    {'category': cases[cid]['category'], 'family': cases[cid]['family'], 'required_fact_ids': ids})
        execution.append({'answer_id': unit['answer_id'], 'execution': 'NOT_EXECUTED',
            'reason': 'NO_REAL_MODEL_BATCH; offline stubs are not model results',
            'seconds': None, 'model_requests': None, 'real_total_tokens': None})
        blanks.append({'answer_id': unit['answer_id'], 'case_id': cid, 'reviewer_id': '',
            'accuracy_0_2': '', 'evidence_0_2': '', 'task_fit_0_2': '', 'limits_0_2': '',
            'delivery_judgement': '', 'severe_error': '', 'facts': dict.fromkeys(ids, ''),
            'unscorable_reason': '', 'notes': ''})
    files = {'planning/analysis_plan.json': plan, 'planning/real_execution_NOT_STARTED.json': execution,
        'review_only/fact_items_DRAFT.json': specs, 'review_only/human_reviews_blank.json': blanks,
        'planning/analysis_pending_NOT_RESULTS.json': summarize(plan, execution, blanks)}
    for rel, content in files.items():
        path = package / rel
        if path.exists() and json.loads(path.read_text(encoding='utf-8')) != content:
            raise ValueError('已有分析/人工记录内容不同，停止覆盖；请使用新的题包目录：' + rel)
        path.write_text(json.dumps(content, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    assert all(v['completion_rate_percent'] is None for v in files['planning/analysis_pending_NOT_RESULTS.json']['category_summaries'])
    print('PASS: human ratings/facts/decisions blank; all real-performance summaries null, not zero.')


if __name__ == '__main__':
    main()
