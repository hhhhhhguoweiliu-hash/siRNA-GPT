# 新一位专家评分图件（第9题已按用户更正）

数据来自提交 `c68baaf2a47b91c9713fc1c046f2bbfa45b217c8` 的用户更正版。只使用本位真人专家的27份答复评分，不混入旧A/B/C表或AI预评审。第9题固定流程A011与Agent A025均为8分。旧原件及更正记录仍在原分析目录。

| 图 | 展示内容 | 本批结论 |
|---|---|---|
| Fig1 | 综合总分及四维评分柱图，点为每道任务 | Agent 7.78/8，LLM 5.78/8，Workflow 5.67/8；优势集中于证据支持和需求完成。 |
| Fig2 | 同一组四维均值的雷达图 | LLM事实准确略高于Agent；两者边界处理相同。不是Agent各维度都最高。 |
| Fig3 | 九题逐题总分 | Agent对LLM九题均高；对Workflow七题高，第4/9题持平。 |
| Fig4 | 标准、需求变化、可靠性分别展示 | 标准任务Agent 7.75、Workflow 6.75；可靠性7.75对4.50。需求变化只有一题。 |
| Fig5 | 三组全部108个维度原分的热图 | 保留每项评分，可定位第6/7题及各组差异；不从分数自动推导任务成功率。 |
| Fig6 | 同题Agent减另外两组的总分差 | 对Workflow的19个累计优势分中，第6/7题贡献11分，约57.9%。 |

每张均有600dpi PNG、矢量PDF、可编辑文本SVG。六页总PDF按上述顺序排列。真实Arial Bold已逐PDF核验嵌入，纵轴标题在左侧。图中数据点是任务评分，不是重复模型运行；无伪造误差线、p值或新分类Accuracy/Precision/Recall/F1。

完整ZIP包含全部单图PNG/PDF/SVG、汇总PDF、作图数据和更正版Excel。仓库单独保存SVG和汇总PDF；高清PNG与单图PDF可从ZIP取得。overview.png只用于六图预览，正式单图请使用figures目录中的600dpi文件。

`data/source_scores.csv`为27份逐答复原分，`data/group_summary.csv`为此前已核对汇总；`plot_data.csv`列出本次图的均值与差值。更正版工作簿和用户更正记录一并提供。A013主交付/原始模型文字的评价范围沿用分析报告边界，不因作图消除软件误拦截。

复现：先使用已有Windows Arial Bold字体，或运行`prepare_font.py`从仓库旧图PDF提取实际Arial Bold并恢复Unicode字符映射（不改字形），再运行`build_figures.py --font 字体路径`。临时字体本体不在结果包中另行分发。

```bash
python research/2026-10-28_authoritative_expert_figures/prepare_font.py --source-pdf research/2026-10-27_bar_radar/siRNA_GPT_bar_radar_existing_scores_REVIEW_PENDING.pdf --output tmp/Arial-Bold-project.ttf
python research/2026-10-28_authoritative_expert_figures/build_figures.py --font tmp/Arial-Bold-project.ttf
```

字体出处只用于复用字形，旧PDF的评分数据未参与本次作图。人工评分新增0、模型API调用0。当前只有一位专家和九个已见、部分相关任务，图件是本批开发评价的描述。
