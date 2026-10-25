"""Presentation labels. Stored scientific fields and model/source text stay unchanged."""
SEQUENCE_LABELS={
    'PASS':'Sequence check passed',
    'FAIL':'Sequence check failed - original answer conflicts with verified fields',
    'NO_SEQUENCE_CLAIMS':'No sequence claims to check',
    'NOT_CHECKED_NO_VERIFIED_SEQUENCE':'Sequence check unavailable: no verified sequence evidence',
    'NO_MODEL_ANSWER':'No model answer to check',
}
LABELS={
    '文献全文（文字部分）':'Article full text (text only)',
    '文献全文':'Article full text','仅摘要':'Abstract only',
    '官方工具文档':'Official tool documentation','官方工具源码':'Official source code',
    '官方源码文本':'Official source code','项目设置说明（待外部审核）':'Project setting (not independently reviewed)',
    '项目设置说明':'Project setting','本地计算记录':'Local computation record',
    '本项目2026-10-16整理的ARPE-19基线表达表':'Project ARPE-19 baseline expression prepared on 16 October 2026',
    '同一培养批次，每状态4皿；未转染；缺氧1% O2 24h':'One culture batch, four dishes per state; untransfected; hypoxia at 1% O2 for 24 h',
    '先列出无已知复核提示的候选，组内按OligoFormer分数降序；提示候选单列待核对。表达注释不进入排名。':'Candidates without existing review flags are listed first and sorted by OligoFormer score. Flagged candidates are listed for separate review. Expression annotation does not affect ranking.',
    '仅人VEGFA及当前参考':'Human VEGFA and the fixed reference only',
    '既有候选来自siDirect，尚非用户的文献候选清单':'Existing designs come from siDirect, not a user literature-derived siRNA list',
    '仅guide mer7m8匹配，不是全面脱靶或毒性检测':'Guide mer7m8 matches only; not a comprehensive off-target or toxicity assessment',
    '近似匹配使用经序列核对的历史结果':'Approximate matches use sequence-verified saved results',
    '模型分数不是敲低百分比':'Model scores are not measured knockdown percentages',
    '待确认化学形式与成熟SOP；不作为订购单':'Chemistry and the experimental protocol remain to be confirmed; not an order sheet',
    '当前推荐规则用于流程原型，尚未经生物学效力验证':'The current recommendation rules support a workflow prototype and have not been validated for biological efficacy',
}
def ui_label(value):
    return LABELS.get(str(value),str(value))
def sequence_label(check):
    return SEQUENCE_LABELS.get(check['status'],check['status'])
