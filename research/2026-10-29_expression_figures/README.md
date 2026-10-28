# 当前候选 × RNA-seq 表达背景：Agent R 作图功能

已实现并用当前九条跑通本地网页处理链：选择候选 → 已有适用seed结果 → 本次表达关联 → 原生R出图 → PDF/PNG/SVG和完整记录下载。没有更改候选排序、删除Hyp2、训练模型或重新比对FASTQ。本次实际验证是引导模式/固定流程，**没有新LLM调用或新siRNA设计/预测**；已有分数与seed结果仍记录为历史导入。自然语言规划器已注册新工具，真实模型自主调用本工具尚未做付费演示。

- [示例PDF：5页图＋2页方法](example/candidate_expression.pdf)
- [图与方法网页](example/report.html)
- [完整运行记录ZIP](candidate_expression_records.zip)
- [实际HTTP处理链与下载核对](http_e2e_receipt.json)
- [独立表格、字体与导出核对](audit.json)
- [版本、输入与文件指纹](example/manifest.json)

## 使用

现有本地服务重启后，在 **Guided mode → Plot candidate expression background (R)** 选择本次候选和表达表。旧九条用 **Saved-result import**，逐步执行即可，不需调用大模型。若同时需要原有排序报告，选 **Complete review with expression figures (R)**。Autonomous mode也可提出“为当前候选作表达背景韦恩图和TPM热图并导出PDF”，由已有规划/确认机制选择`render_expression_figures`；不绕过启动检查或用量确认。

本地复现：`python scripts/run_expression_figures_example.py`（原六工具＋作图）；HTTP处理链验证：`python scripts/verify_expression_figures_http.py`（4步表达作图，不评分/排序）；源表对照：`python scripts/audit_expression_figure_example.py`。后者需要原工作区v3核验表，以及pdfplumber/pypdf/Pillow；这些不是线上服务必装依赖。

服务器须安装R及ggplot2、ggforce、patchwork、systemfonts、ragg、svglite、jsonlite和**合法可用的Arial Bold**；具体已运行版本见[sessionInfo](example/sessionInfo.txt)。Rscript从服务器`RPE_PLOT_RSCRIPT`、PATH或本机已知R4.5.1位置读取；不能通过HTTP指定可执行文件。不分发Arial字体。缺R/字体/包会报错、保留来源表并返回未完成，不用其他字体或静态旧图代替。**代码上传不等于线上部署**；现有线上Python服务尚未配置/验收此R功能，未开新付费设施。

## 数据与规则

新内置表`data/expression.tsv.gz`为43,418条核验的唯一Entrez—公司参考条目，保留全部8列原TPM。其来源、原文件SHA256和映射规则见`data/expression_provenance.json`及`scripts/sync_expression_baseline.py`。原43,385条摘要表保存在`data/expression_legacy_20261016.tsv.gz`；原`data/provenance.json`和历史题包不改。冻结的旧评价入口显式用旧表，并校验题包原指纹；当前新作图用新版。已有27/54答复、专家评分及裁决未修改、未重跑。

每次冻结当前候选、序列匹配、逐样本TPM和来源：不直接套用九条的静态图。接口最多20条；本次真实R/逐页验收覆盖当前九条，候选子集和上传值改变另有单元检查；更大池和长候选名的论文排版仍需具体验收。

1. 排除靶基因VEGFA（Entrez7422）；正seed匹配按唯一基因计数，位点数与基因数分开。
2. 各状态TPM≥1且至少2/4皿为“检测到”。分别列常氧、缺氧、交集、各自独有、两状态均未达到检测规则、未映射；未映射不填零。
3. 从本次全部匹配基因的可映射并集按全8样本平均TPM递减取前20展示；符号、数值Entrez顺序打破并列。没有按DE/FDR/方向挑选；完整匹配及表达仍可下载。
4. 热图为log2(TPM+1)，共用基因顺序/色阶，非逐行z分数。韦恩数字精确，圆面积为示意。TPM不作风险权重，不改变排名；未转染数据不证明真实脱靶、敲低、安全或Agent优越。
5. 原生ggplot2/ggforce/patchwork绘图，R cairo导出PDF；ragg PNG和svglite SVG。10×7英寸、纯白背景、Arial Bold，标题24pt、主体18pt、密集标签/方法16pt；没有图片生成模型或后期手绘数据。

## 实际检查及修复记录

最终完整Python检查228项通过；随后新增冻结版本/作图审计检查后，相关37项通过。4项既有Node检查通过。实际R图逐页渲染检查；9条计数、前20基因顺序和均值均与独立保存的v3表一致；PDF嵌入Arial-BoldMT、无页面外文字；5张2400×1680PNG、5张SVG（无栅格图层）核对通过。

初轮发现并修复：展示元数据误混入全表达导出列；测试临时目录的沙箱权限问题（改用工作区测试目录）；旧评价未锁定旧表达版本；一个旧接口测试仍查找已经更名的报告标题；方法页行数过多和韦恩表头裁切。旧运行及失败日志保留在本地`runs/`和本目录`.log`，旧PDF预览亦保留；交付以`example/`、`http_e2e_receipt.json`与`audit.json`为准。未改科学原始数据以迎合检查结果。

本次没有重新核实counts计数软件/命令、完整FASTA/GTF来源，也没有新增实验记录；它们仍是论文方法定稿待补信息，不阻断已核验TPM的描述性作图。
