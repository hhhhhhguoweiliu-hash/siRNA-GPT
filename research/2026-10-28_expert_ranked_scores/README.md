# 三配置组内降序专家分柱状图

2026-10-28，北京时间。用户要求参考其附件的“每组内由高到低排列的细柱”样式。本图使用最新确认专家分；每组9题，共27柱，不伪造大量候选或重复样本。

## 来源与图形规则

- 评分源为提交 `c68baaf2a47b91c9713fc1c046f2bbfa45b217c8` 的[更正版原分](../2026-10-28_authoritative_expert_analysis/scores_by_actual_group.csv)，第九题两工具组均8分。绘图前实际读取GitHub并fetch核对，任务分支头为 `32f5da88a4974435ef5cc79cbad974c05a18ff21`，无更新评分。
- 一位用户确认真人专家，四维各0-2分、总分0-8。继续使用既有桑基图的只读源核对函数：原CSV与Git提交逐字节一致，108项单元格和27个原工作簿总分缓存逐项一致。无改分、新模型调用或新质量判断。
- 每组按原总分降序，同分按原题号升序。柱下保留Q1-Q9，明确三组排序后的横坐标位置不代表相同题目。每题每组恰好出现一次，不删零/低分、不挑选成功记录。
- 颜色连续编码原0-8分，色标全范围固定。没有预先确定的高/低质量或噪声阈值，因此不按示例虚构这三类标签。
- 虚线为全部27份答复的描述性平均分 `173/27=6.407407`，不是合格阈值。三组均分分别为Agent7.78、固定流程5.67、LLM5.78。均为原量表分，不称Accuracy或成功概率。
- 不增加误差线、显著性或独立重复。原评分的单专家、已见任务及Q3评价范围限制沿用[原解释](../../docs/reviews/20261028_authoritative_expert_score_analysis.md)。

## 文件

- `figures/siRNA_GPT_ranked_expert_scores_20261028.png`：600dpi（7200×4020）。
- 同名 `.pdf`：单页矢量、实际Arial常规/粗体嵌入；同名 `.svg`：可编辑Arial、含色标的纯矢量。
- `ranked_plot_data.csv`：27项原分、排序名次、题号、真实A编号及原工作簿位置。
- `validation.json`：来源哈希、每组9题完整性、降序、柱高、总分、字体和导出检查。
- `preview.png` / `pdf_render_qa.png`：本次排版核对。PDF经Poppler真实渲染查看，无标签裁切或重叠。
- `build_ranked_scores.py`：复现入口，复用同仓桑基图的只读评分/字体核对。依赖已配置独立Matplotlib环境、Pillow、pypdf及真实Arial。

保留生成期间的两次检查失败说明：首次SVG核对发现默认色标被栅格化，已将色标设为矢量后重导出；第二次核对结果写JSON时遇到NumPy整数类型，已显式转为Python整数。两者均为绘图/核对导出问题，不是原答复或评分变化。最终全部核对通过后才交付。

本轮新增此图及数据，不覆盖桑基图、此前六图包或任何评分/原答/失败；仅上传原任务分支，不合main、不部署网站。

## Figure legend

**Expert scores ranked within each model configuration.** Each bar represents the original total score for one of nine seen development questions, assigned by one user-confirmed human expert using four 0-2 dimensions (maximum total 8). Bars are sorted independently within Agent, fixed workflow and LLM groups in descending score order, with original question number as the tie breaker. Question IDs retain the paired-task identity; aligned bar positions across groups do not imply identical questions. Color continuously represents the original score on a fixed 0-8 scale, without inferred high-quality, low-quality or noise categories. The dashed line denotes the descriptive overall mean across all 27 responses, not a quality threshold. All questions are included once per group. Scores incorporate the documented user correction for Q9. These are ordinal rubric totals for seen tasks, not classification accuracy, independent-test performance or biological efficacy; the documented Q3 rating-scope distinction remains.
