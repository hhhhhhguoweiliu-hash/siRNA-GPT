# 用户确认的一位权威专家：原分只读分析

2026-10-28（北京时间）。用户确认本次对原44页总册的评分来自一位权威真人专家。按此登记，不重新由AI评分。用户随后明确更正第9题：A011、A025均为8分，原A011的6分属于录入失误。先读[结果解释](../../docs/reviews/20261028_authoritative_expert_score_analysis.md)。

- `source_workbook_original.xlsx`：上传原件的逐字节副本，未通过Excel或Python重新保存。
- `source_workbook_user_corrected.xlsx`：按用户更正D27、E27为2，G27保留公式并为8；其余内容与样式不变。
- `user_correction_receipt.json`：用户更正说明、原值与现值，不是新增专家评分。
- `scores_by_actual_group.csv`：27份答复按用户更正后的四维分和对应单元格，按已核对真实组别映射。
- `group_summary.csv`：总体及W/U/R分组均分，各题权重相同。
- `analysis.json`：原分描述、逐题差值、相对总评分差和两项评价范围说明。
- `workbook_checks.json`：108项原分、27个公式/缓存与分组键核对。
- `analyze_scores.py`：只读重现，不联网、不改分、不调用模型。

在完整仓库中复现：

```bash
python research/2026-10-28_authoritative_expert_analysis/analyze_scores.py \
  --source research/2026-10-28_authoritative_expert_analysis/source_workbook_user_corrected.xlsx \
  --original-source research/2026-10-28_authoritative_expert_analysis/source_workbook_original.xlsx \
  --mapping research/2026-10-27_real_dialogue_mini/outputs/01a15800-7529-7ee0-b82c-8428c7746a68/private_display_key_DO_NOT_SEND_REVIEWERS.json \
  --origin-audit research/2026-10-27_three_objections_audit/audit.json \
  --output analysis_outputs/new_authoritative_expert
```

这里含实际组别，属于研究者分析材料，不是新的盲评包。第9题均8分的用户录入更正已解决差异，不再列为专家分歧。第3题仍应明确模型原文/附件与主交付的评价范围；不据此由AI改分。不同来源旧评分不合并或覆盖。本轮没有新模型运行，没有新独立测试，也未生成分类Accuracy/Precision/Recall/F1。
