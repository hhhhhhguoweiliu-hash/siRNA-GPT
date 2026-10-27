# siRNA-GPT：两份专家原分的图件

本批图按用户提供的两份专家评分原样绘制。A为“专家评分表_最终版”，B为“专家评分-任务完成情况评分”。两份关系未说明，分开展示，未平均。若评审看了不同版本、PDF提取误读等导致事实性理由冲突，需由实际评审确认，不能由AI改分。详见[复核与具体原文对照](../../docs/reviews/20261027_two_expert_forms_and_figures_review.md)。

**状态：REVIEW_PENDING（原分展示，尚有理由与原答冲突）。不能把本目录称作正式独立测试优越性结果。**

| 图 | 展示问题 | 当前可说的结论 |
|---|---|---|
| fig1_standard_quality | 四项标准工作的事实、证据、完成、边界，A/B分别展示 | 按当前原分，固定流程表现较稳；没有Agent全面领先 |
| fig2_completion_as_submitted | 完成题数占比；W4、U1、R4分别呈现 | 两表对部分任务完成的判断有分歧，不能任取有利结果 |
| figS1_reliability_quality | 四个可靠性题的四维分 | 不同维度和表之间有高低与分歧 |
| figS2_requirement_change_quality | U1两轮案例的四维分 | 单个案例，不能代表一般变化处理能力 |

每图有PNG（600 dpi）、PDF、SVG。PDF已嵌入Arial Bold；SVG文本指定Arial Bold，编辑电脑需有Arial。轴标题位于纵轴左侧。图内为英文，原数据与说明保留中文。

- `siRNA_GPT_expert_figures_REVIEW_PENDING.pdf`：四页汇总。
- `expert_plot_data.xlsx`：216行逐维原分、72行均分、18行完成计数、18行百分点差及说明；没有代填分数。
- `scores_long.csv`、`dimension_means.csv`、`completion_as_submitted.csv`、`completion_differences_pp.csv`：对应作图源数据。
- `source_form_A_original.xlsx`、`source_completion_scores_original.xlsx`：两份原件，字节未变。
- `make_expert_figures.py`：可复现作图；参数为本批`results_original.json`绝对路径。依赖openpyxl、ReportLab、Pillow、pypdf。脚本只读原始评分和运行，输出新图，不联网或调用模型。
- `FIGURE_LEGENDS_EN.md`：英文图注及参考图依据。

四维量表为0–2，非原论文1–5分；柱为任务均分，点是全部题目评分。没有冒称三个独立试验，没有误差线或显著性星号。W/U/R分开，不将9个已见模板称27道独立题。完成百分比只复述原标签，n=1明确注明。分数、seed、表达证据均不能解释成湿实验效力。
