# 第三份专家评分：C表

用户明确确认“真人已逐项确认”。登记为真人逐项复核、AI辅助整理；不是本次LLM新增人工评分。原件不改、分数不改、不自动与A/B平均。详见[复核](../../docs/reviews/20261027_third_human_confirmed_expert_score_review.md)。

- `source_expert_scores_original.xlsx`：用户D盘提供的原件，18287字节，SHA256见检查JSON。
- `score_rows_by_actual_group.csv`：27份原分按真实组别回连，保留“基本完成/部分完成/未完成”原标签。
- `scores_and_comparison.json`：W/U/R分开的四维均分、分差、27条原分评语及与A/B的逐条对照；没有合并均分或人工裁决。
- `evidence_questions_NOT_NEW_RATINGS.json`：A002来源/解释、A006 PASS语义、A013误报等证据，不是新评分。
- `workbook_checks.json`：27编号、108分、总分与题目汇总检查。
- `audit_third_expert.py`：复算脚本。示例：`python audit_third_expert.py ../2026-10-27_real_dialogue_mini/raw/results_original.json ../2026-10-27_expert_figures/plot_data.json`。依赖openpyxl；只读原件，无模型或网络调用。

不将三份文件数量自动当作三位独立盲评者；用户确认的这一位真人判断予以保留。9模板均为已见开发任务，题目与轮次不重复计数。完成标签尚未转换成正式完成率，逐事实评价不代填。A/B图原样保留，未用C覆盖较低或较高分。
