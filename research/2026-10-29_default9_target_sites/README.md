# 默认九条siRNA在VEGFA上的位置

已先查现有本地图：找到[20条参考匹配数图](../2026-10-20_takeover/figures/Fig04_transcript_coverage.png)，以及65条新候选的“位置—模型分数”图；没有找到专门展示当前默认九条19nt配对核心区间的图。本次用原生R/ggplot2新画，未改已有图、候选、分数或统计结果。

- [两页PDF：全长图＋末端放大图](figures/default9_VEGFA_target_sites.pdf)
- [全长PNG](figures/default9_VEGFA_full_reference.png)／[SVG](figures/default9_VEGFA_full_reference.svg)
- [末端放大PNG](figures/default9_VEGFA_3UTR_zoom.png)／[SVG](figures/default9_VEGFA_3UTR_zoom.svg)
- [九条在原设计参考上的具体位置与序列](tables/default9_primary_positions.tsv)
- [九条×20个固定参考转录本的位置表](tables/default9_all20_transcript_positions.tsv)
- [序列与坐标核验](logs/sequence_coordinate_audit.json)／[字体及导出核验](logs/output_audit.json)

## 图怎么读

主图采用历史原设计转录本 **NM_003376.6，3609nt** 的成熟mRNA坐标，从5′端向3′端递增；坐标从1开始、包含两端。顶端是该版本GenBank注释的5′UTR（1–496）、CDS（497–1684）及3′UTR（1685–3609）。蓝色为CDS，灰色为UTR，橙色为19nt配对核心。它不是基因组DNA坐标或RNA-seq读段覆盖图。

| 候选ID | 配对核心位置 | 在本参考上的区域 |
|---|---|---|
| VEGFA_SD_1157 | 1159–1177 | CDS |
| VEGFA_SD_2739 | 2741–2759 | 3′UTR |
| VEGFA_SD_3119 | 3121–3139 | 3′UTR |
| VEGFA_SD_3193 | 3195–3213 | 3′UTR |
| VEGFA_SD_3429 | 3431–3449 | 3′UTR |
| VEGFA_SD_3499 | 3501–3519 | 3′UTR |
| VEGFA_SD_3500 | 3502–3520 | 3′UTR |
| VEGFA_SD_3502 | 3504–3522 | 3′UTR |
| VEGFA_SD_3535 | 3537–3555 | 3′UTR |

**候选后缀不是核心起点。**它来自siDirect的23nt设计窗口起点；配对核心是窗口起点+2至+20。原始21nt双链和两碱基末端保留在输入及表中，不把19nt核心当完整订购双链。3499、3500、3502在这一参考上分别只移动1或3nt，因此高度重叠；第二页另放大3485–3565nt，包含邻近的3535。

九条在固定20条参考转录本中各有一个完整19nt匹配，180组已逐一用实际参考序列核验。**不同转录本的数值坐标可能不同**，不能把本图的NM_003376.6坐标直接套用到其他版本。参考匹配不证明ARPE-19实际使用全部20种异构体、各异构体表达比例、位点可及性或siRNA敲低效果。本图没有使用TPM加权或重新排序。

## 来源与复现

优先复用现有`data/candidates.tsv`、10月23日核验的`candidate_trace.tsv`、固定20序列FASTA和历史GenBank原件。输入副本在`inputs/`，每个原文件的路径和SHA256在序列核验JSON。历史原件位于原本地ChatGPT项目`analysis/ARPE19_candidates_20261016/public_sources/`。本次NCBI网页检查遇到验证页，未以其代替已核验的固定版本原件，没有重新下载大数据或声称使用最新注释。

`prepare_sites.py --source-dir <历史public_sources目录>`校验23nt窗口、19nt反向互补、原追溯表和180个匹配；`Rscript --vanilla render_sites.R <本目录>`原生出图；`python verify_outputs.py`核验坐标标签、Arial Bold、字号、页边界及导出。Arial Bold标题24pt、坐标18–20pt、区间和说明16pt，10×7英寸，白底无网格。图及PDF由R直接生成。

只增本图和位置表，不重跑siDirect/OligoFormer/SeedMatchR，不改默认池，不改原RNA-seq图册或原27/54答复/评分。原任务分支同步情况见`SYNC.json`。
