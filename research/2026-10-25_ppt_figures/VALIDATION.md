# 本批实际核对记录

本批只排版已有证据，不调用模型、搜索、评分、seed或近全长计算，也不更新生产服务。

- 实际执行：`python scripts/build_ppt_evidence_figures_20261025.py`，退出码0；标准输出/错误见build_stdout.txt和build_stderr.txt。Python为Codex捆绑的3.12运行环境，ReportLab生成PDF，Poppler pdftoppm从最终PDF渲染3840×2160 PNG。
- 生成两张图的PDF、可编辑SVG、PNG及元素位置/来源JSON。PDF每张一页1280×720点，比例16:9；全部图中文字在提取文本中核对存在。
- Arial来自本机`C:/Windows/Fonts/arial.ttf`、`arialbd.ttf`，文件指纹保存在evidence_checks.json。PDF两字体均为嵌入TrueType；逐个文字显示操作核对所用字体，没有用默认Helvetica绘制文字。SVG各text均声明Arial、常规/粗体分开。见font_and_format_checks.json。
- 实际查看了由最终PDF渲染的两张PNG，检查标题、引用、两列间距和页边，无文字遮挡或截断。初版到终版将执行区标题补为真实UTC时间段，并把seed/表达只作注释的边界放在同图，再重新渲染查看。没有把生成图当网页截图。
- A核对：8次模型请求逐条分工、六工具顺序与status、39048词元、三段实际时间、19位正确核心与24位原错、靶参考/覆盖/坐标、分数、位点/基因/表达字段、导入状态。确认点击和规划器时长缺失明确保留。
- B核对：B02问答与实际模型请求中的6个来源编号和片段文字逐字一致；图上原文/代码是片段内的真实子串。library.zip内原文/源码的字节指纹与检索声明一致，源码行号和文章字符位置实际查得，未猜PDF页码。英文回答为有标记的中文原答译文，原答保存不改。
- 39份原件与Git `927910c`核对。首次核对发现两个复核文档因Windows换行与Git原字节不同，正文经换行统一一致；首查记录source_integrity_first_check.json保留。随后只把新交付目录中的这两份副本改为直接读取Git原字节，未改原文档或科学原件；最终检查见source_integrity_checks.json。其他37份原记录直接逐字相同。
- 旧九条、原54条、候选科学计算、既购原答、旧文库问答和防错历史目录均检查无差异。没有用本批工程检查数当研究样本量或科学准确率。

最终上传与核对见SYNC.json；本文件不提前声称上传或部署成功。
