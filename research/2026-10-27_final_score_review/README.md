# 最终版专家评分文件及只读汇总

原件来自用户明确说明已经专家复核的最终版。原分一项未由本次分析修改；本目录不是新增人工评分。先读[科研复核](../../docs/reviews/20261027_final_expert_score_workbook_review.md)。

- `source_workbook_original.xlsx`：原始25410字节，SHA256见`source_manifest.json`。
- `score_rows_by_actual_group.csv`：27份答复的原四维分，按真实运行编号映射组别；8分和仅供核对。
- `scores_and_descriptive_summary.json`：四维原分、原理由、W/U/R分别的均分及差值、相较上版的真实变更。正式主指标仍留空，原因在复核中说明。
- `workbook_checks.json`：108分一致性、加总核对和三处漏列并列者。
- `remaining_issues_NOT_NEW_RATINGS.json`：证据问题，不是新的评分、人工裁决或新真值。
- `reproduce_score_summary.py`：只读读取原件和本次真实运行JSON。运行示例：`python reproduce_score_summary.py ../2026-10-27_real_dialogue_mini/raw/results_original.json ../2026-10-27_score_file_review/source_workbook_UNVERIFIED.xlsx`。依赖openpyxl，不联网，不调用模型。可选第二参数仅用于比较上版提交。

用户确认了专家复核，文件未注明评审人数及独立性；不能冒称双人独立评分。所有9个模板均为已见开发材料，27为配置答复数。完整原始模型/脚本/工具记录见[原始交付收据](../2026-10-27_real_dialogue_mini/DRIVE_RAW_OUTPUTS_DELIVERY_20261027.md)。
