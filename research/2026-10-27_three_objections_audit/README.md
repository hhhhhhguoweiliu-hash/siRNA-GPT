# 三项评价质疑的原件审计

2026-10-27（北京时间）。审查分支提交 `c30473d3168ccf5ce6522722f0cea857c2065037`。先读[科研复核](../../docs/reviews/20261027_three_evaluation_objections_evidence_review.md)。

- `audit.json`：原JSON与匿名ZIP指纹、R4字节相等/过程差异、A013原文与主答复分离、逐组来源计数。
- `answer_origin_by_round.csv`：全部27答复共33轮的真实来源；不等于新增33道题或质量分。
- `audit_evaluation_claims.py`：只读原件，不调用API，不填人工分数，不改原文件。

复现（使用新输出目录）：

```powershell
python research/2026-10-27_three_objections_audit/audit_evaluation_claims.py --results research/2026-10-27_real_dialogue_mini/raw/results_original.json --reviewer-zip research/2026-10-27_real_dialogue_mini/raw/anonymous_reviewer_package_original.zip --output audit_outputs/new_three_objections
```

脚本要求原JSON SHA256完全匹配既有原件，避免拿修复版代替。确认R4两份导出文本均1900字节且完全相同，process仅错误阶段不同；A025此前有6次模型请求。A013的分数存在于模型原文，不存在于主答复。上述为来源与相等性检查，不是独立真人评分，不代判分差4分，也不证明模型生物学预测正确。

主交付与内部模型草稿、字段来源一致性与生物学有效性、共用规则与模型解释贡献，应分别评价。旧原答、评分和图保留，不新增付费批次。
