# 三列专家得分桑基图

日期：2026-10-28（北京时间）。按用户提供的模板，左列三个系统配置、中列九道题、右列四个评价维度；线宽使用真实分值，不再使用前一张结构草图的示意数据。

## 本图唯一评分来源

本轮读取并快进纳入 GitHub 最新任务分支提交 **c68baaf2a47b91c9713fc1c046f2bbfa45b217c8**：

- [本位专家原分及真实组别](../2026-10-28_authoritative_expert_analysis/scores_by_actual_group.csv)
- [用户更正后的原工作簿](../2026-10-28_authoritative_expert_analysis/source_workbook_user_corrected.xlsx)
- [Q9 录入更正收据](../2026-10-28_authoritative_expert_analysis/user_correction_receipt.json)
- [原评分解释及范围](../../docs/reviews/20261028_authoritative_expert_score_analysis.md)

用户已确认一位真人专家来源。本图不与较早的 A/C 等其他来源评分合并，不修改任何评分或原答。第九题固定流程 A011、Agent A025 均为四维 2/2/2/2、总分 8。表中甲乙丙不固定对应模型，本图使用逐答复的真实组别映射。

## 图形规则

- Agent 紫色、Fixed workflow 绿色、LLM 蓝色；颜色在中间题目节点后继续保留模型身份。
- 模型到题目：该模型该题四个维度之和（0-8），共 27 条连接。
- 题目到维度：对应模型、题目、维度的单项原分（0-2），共 108 条连接。
- 所有线宽均按同一个线性比例绘制，未分别归一化；每道题流入总分等于流出总分。
- 10 项零分对应零宽，不虚增细线；它们完整保留在来源及 `sankey_links.csv`，其余 98 条维度连接加 27 条总分连接共 125 条可见流带。
- 模型节点显示各自九题累计分/72：Agent 70、Fixed workflow 51、LLM 52。右侧显示三模型九题在该维度累计分/54：事实准确 46、证据支持 41、需求完成 36、边界处理 50。它们是原量表加分，不是分类准确率。
- Q1-Q4 标准任务、Q5 需求变化、Q6-Q9 可靠性，保持原题号顺序，不按高低分排序。英文短标题仅用于空间布局，完整问题仍见原44页总册与评分来源。
- 序数量表的加分仅用于本次描述性可视化，不将线宽差解释为生物学效果或测量尺度已被证明等距。图的左右方向表示评分分解，不是时间顺序或因果推断。

## 交付与核对

- `figures/siRNA_GPT_expert_score_sankey_20261028.png`：600 dpi（8400×5640）。
- `figures/siRNA_GPT_expert_score_sankey_20261028.svg`：可编辑 Arial 文本、纯矢量流带。
- `figures/siRNA_GPT_expert_score_sankey_20261028.pdf`：单页矢量，真实 Arial 常规体/粗体均嵌入。
- `sankey_links.csv`：135条含零分连接，带真实 A 编号、模型、维度、分值、线宽与端点。
- `validation.json`：108项工作簿单元格、27项公式缓存、九题流量守恒、线宽比例、组别合计、来源哈希、字体及导出检查。
- `preview.png` / `pdf_render_qa.png`：排版核对图。PDF 经 Poppler 实际渲染后查看；16个节点标签均在框内，无裁切或重叠。右侧保留98条非零维度连接，密度来自完整数据，不删选较有利记录。
- `FIGURE_LEGEND_EN.md`：英文图注。

复现：在具备 Matplotlib、Pillow、pypdf 与真实 Arial 的环境运行 `python research/2026-10-28_expert_score_sankey/build_sankey.py`。本环境使用此前已配置的独立绘图依赖，未修改系统环境。

本轮 0 新模型请求、0 新质量评分、0 科学预测或湿实验。原27答复/33轮、原405逐槽标签、全部旧评分和失败保持不变。本位专家评分针对已见开发任务；Q3 的主交付/原始文字/附件评价范围仍按来源说明保留，不能用本图证明误拦截不存在。单评审、未见任务与生物学验证边界不变。

本图上传原任务分支；不合 main，不部署网站。准确提交和远端核对见 `DELIVERY.md`。
