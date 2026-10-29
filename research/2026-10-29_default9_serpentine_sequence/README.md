# VEGFA完整序列S形排列与九条siRNA对齐

按用户要求，**同一张图、同一页**展示固定参考NM_003376.6的全部3609个mRNA碱基，九条当前默认siRNA的guide直接对齐在靶序列下方。所有图形由原生R/ggplot2生成，未在图片上后期加字。

- [单页矢量PDF](figures/default9_VEGFA_serpentine_full_sequence.pdf)
- [完整PNG](figures/default9_VEGFA_serpentine_full_sequence.png)／[矢量SVG](figures/default9_VEGFA_serpentine_full_sequence.svg)
- [重叠位点局部预览（同图裁切，仅供检查）](preview/row28_detail.png)
- [逐碱基mRNA位置表](tables/mRNA_bases.tsv)／[逐碱基guide对齐表](tables/guide_bases.tsv)
- [来源和互补核验](logs/coordinate_sequence_audit.json)／[实际PDF字形与方向核验](logs/output_audit.json)

## 读图

每行126个碱基，共29行；最后一行81个。第一行由左向右，第二行由右向左，沿两端箭头不断折返。**偶数行的字母按阅读方向反排，不是把参考序列取反向互补。**两端数字表示该行左右位置上的成熟mRNA坐标，全部从1开始。末端5′、3′与每条guide方向明确标出；mRNA由原固定DNA字母记录T→U显示。

橙色是既有19nt配对核心在mRNA上的位置；下方显示原始**完整21nt guide**，其中19nt核心蓝色、其余3′端2nt灰色。每个蓝色左标签为“候选编号 | 19nt核心区间”。**灰色2nt是相对于原始passenger双链的末端突出，不表示与mRNA不匹配**：本批全21nt guide均与固定mRNA的相应区间精确反向互补。完整guide对应的mRNA区间和19nt核心区间分别记录，不能混用。

guide与mRNA反向平行，因此guide在纸面上可能是5′→3′或3′→5′；请按每条guide两端标记阅读。所有guide碱基的横坐标都等于其互补mRNA碱基横坐标。重叠候选分别占用下方多行，不叠字、不表示它们会同时结合。

## 版式与来源

为保留3609个碱基和16pt Arial Bold，这是一张约73×61cm的大画布（28.89×23.87英寸）。PDF/SVG可放大查看；PNG为5200×4296像素。不是适合缩到普通论文单栏后逐字阅读的图；这里只按用户要求先把完整S形方案画清楚。标题32pt、说明16–20pt，纯白底，无背景网格。

来源复用[上一版位置图](../2026-10-29_default9_target_sites/README.md)已核验的固定GenBank、原九条候选和核心位置表，输入副本在`inputs/`。未更换转录本版本，没有RNA-seq读段覆盖、结构预测、新siRNA筛选、效力推理或真实结合证据；仅为序列与互补位置展示。

复现：`python prepare_sequence.py` → `Rscript --vanilla render_sequence.R <本目录>` → `python verify_sequence.py`。核验包括3609个参考碱基、189个guide碱基、9条完整guide原序列、链端方向、每一列互补关系，以及实际PDF核苷酸字形。同步状态见`SYNC.json`。
