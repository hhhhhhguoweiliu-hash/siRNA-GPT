# 已有评分的柱图＋雷达图

沿用此前已绘图的A/B两份评分，72个均值原样使用；没有加入C表、重复文件或最新满分表。每页左为柱图，右为同数据雷达图。详见[方法复核](../../docs/reviews/20261027_metric_availability_and_bar_radar_review.md)。

1. `fig1_standard_bar_radar`：标准科研任务W1/W2/W2b/W3，n=4。
2. `figS1_reliability_bar_radar`：可靠性R1–R4，n=4。
3. `figS2_change_bar_radar`：需求变化U1完整两轮，n=1。

图轴为事实准确、证据支持、需求完成、边界处理，每项0–2分。Arial Bold，PDF嵌入字体；PNG 600 dpi，另有SVG可编辑文本。SVG编辑环境需安装Arial。评分理由尚有待核对项，图只描述原分，不证明普遍优越性或真实用户体验。

- `siRNA_GPT_bar_radar_existing_scores_REVIEW_PENDING.pdf`：三页汇总。
- `bar_radar_plot_data.csv`、`bar_radar_plot_data.xlsx`：72个相同的柱图/雷达均值。
- `figure_checks.json`：源文件指纹、原分复算、同值核对及嵌入字体检查。
- `metric_availability.json`：分类指标仍缺的评价条件，空值不是0分。
- `make_bar_radar.py`：复现脚本。默认读取相邻`2026-10-27_expert_figures`中的原绘图数据与渲染类；不会重跑旧分析或调用模型。

左侧没有冒称为Accuracy/Precision/Recall/F1；它是现有四维专家评分的分组柱图。原论文左图是规划列表与专家标准的逐项指标，不能由本表均分换算。本次没有计算或编造这四个新指标。
