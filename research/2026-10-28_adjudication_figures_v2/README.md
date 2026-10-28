# 裁决接续、指标修正与正式图包

2026-10-28，北京时间。源任务分支`14f11f8eb649ce923271ba65bf8a5c8a08d9e72e`；完整裁决/旧图分支`a09e9a89f55b28ae761fbbdb64d1c53ccf1be058`已正常快进接入原任务分支，未覆盖任何并行提交。本目录完成三项收尾：修正新图的指标口径、生成真实Arial正式图包、接续裁决与共同方法/状态。

## 直接打开

- [8页完整PDF](output/pdf/siRNA_GPT_corrected_adjudication_figures_20261028.pdf)：每页为矢量图，嵌入Arial常规体/粗体。
- [逐图PNG/PDF/SVG](figures/)：8图，每图3种格式；PNG为600 dpi。
- [图注](FIGURE_LEGENDS_EN.md)与[方法/结果说明](METHODS_RESULTS_UPDATE_EN.md)：整题裁决、逐槽AI指标与两份原评分分别说明。
- [完整计算数据](metrics_corrected.json)、[绘图数据](figure_data_corrected.csv)、[导出检查](export_checks.json)、[视觉核查](VISUAL_QA.md)。

## 1. 已修正的具体错误

原图脚本用`Recall=C/(C+M)`，漏掉了错误值对应的FN。按已记录的共同协议，CORRECT计TP；WRONG同时计FP和FN；MISSING计FN。因此：

`TP=C, FP=W, FN=W+M; P=C/(C+W), R=C/(C+W+M), F1=2C/(2C+2W+M)`。

| 配置 | C/W/M | 原图R/F1 | 修正后micro R/F1 |
|---|---|---|---|
| 普通模型 | 55/12/68 | 44.72% / 57.89% | 40.74% / 54.46% |
| 固定流程 | 130/0/5 | 96.30% / 98.11% | 96.30% / 98.11% |
| Agent | 128/1/6 | 95.52% / 97.34% | 94.81% / 96.97% |

Precision未变。这里是全部135槽位的micro汇总，仅作为补充描述。主图按标准工作4题、需求变化1题、可靠性4题分别呈现，槽位主图报告先逐题计算再取均值的macro值。没有构造TN，也不是严格C1规划成绩。

## 2. 裁决与原始记录分层

已有13项项目方裁决由`decision_overlay.csv`读取，未硬编码Agent必须获胜。四个整题标签变化：A002/A013/A014 FAIL→PASS；A008 PASS→FAIL。其余23个整题标签不变，405项原逐槽标签和A/C原评分全部不变。

当前整题裁决通过数是普通模型0/9、固定流程8/9、Agent9/9。**这不是逐槽准确率，更不代表Agent在所有维度或一般科研能力上胜出。**原槽位微观F1仍是54.46%、98.11%、96.97%；A/C评分仍分别展示，不将两文件自动当作两个独立盲评者。项目方回顾性裁决不等于运行前批准标准或未见测试。

新旧图与代码均可追溯：旧SVG、旧绘图CSV保留原字节，旧脚本原文另存`legacy_source/`。旧生成入口已改为转到本目录，避免再次生成错误口径或覆盖旧图。源答复27份、33轮、逐槽标签405项、13项裁决、旧图和原评分共32个受保护文件与a09e9a8 Git对象精确一致，见[原件核对](protected_source_integrity.json)。

## 3. 字体与验收

实际读取`C:\Windows\Fonts\arial.ttf`和`arialbd.ttf`；找不到或解析成替代字体即失败，不允许Arimo/Liberation/DejaVu回退。PDF导出为嵌入TrueType的矢量文本，SVG保持可编辑Arial文本和矢量图形；Arial字体文件本身不上传。

已验证8张单页PDF、8张600 dpi PNG、8张SVG与8页总PDF，检查页数、字体名称与嵌入、常规/粗体、分类面板、原件不变及原协议公式。PDF必须渲染后逐页检查；最终结果见VISUAL_QA。首次检测到热图SVG栅格图层，已改为矢量网格；首次视觉检查发现横版页脚相距过近，已增加间距。原失败日志保留。外部MiKTeX的pdffonts命令因本机配置访问失败，未据其宣布通过；字体嵌入以直接读取PDF FontDescriptor/FontFile2的独立检查为准。

## 4. 复现

Python需Matplotlib 3.10.0、NumPy、Pillow和pypdf。使用Codex随附Python；本机缺少兼容绘图库，已在聊天工作目录隔离安装，未改系统Python、旧科学环境或数据。实际依赖/字体版本和SHA见`font_and_environment.json`。

```powershell
python research/2026-10-28_adjudication_figures_v2/audit_data.py
python research/2026-10-28_adjudication_figures_v2/build_figures.py
python research/2026-10-28_adjudication_figures_v2/verify_figures.py
python -m unittest discover -s research/2026-10-28_adjudication_figures_v2 -p test_metrics.py -v
```

上述脚本不调用真实模型或科学预测。新环境须先准备实际Arial，缺字体必须明确失败，不自动换字体。本轮没有重跑27/54、新增付费调用或真人评分；没有合main、部署或新网页验收。严格规划、独立未见验证及生物学真值仍是后续证据缺口，不通过改名或本轮作图补齐。上传提交与远端核对另见DELIVERY。
