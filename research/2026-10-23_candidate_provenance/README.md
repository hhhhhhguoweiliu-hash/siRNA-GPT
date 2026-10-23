# 默认九条候选的来源核查（任务A）

2026-10-23。实际从main `3831cb555a7e8e3ab572e26193e41b33eb0498df`接手；按[21:16科研复核](../../docs/reviews/20261023_2116_fast_paper_scope_and_codex_tasks.md)执行。本轮只核查来源，不改变候选、分数、排序、网站或旧54条回答。

从Drive单独阅读本文件时，配套文件请打开[GitHub完整材料目录](https://github.com/hhhhhhguoweiliu-hash/siRNA-GPT/tree/main/research/2026-10-23_candidate_provenance)；另有[Drive原始证据ZIP](https://drive.google.com/file/d/1zl729Uq-uRikrazwAx7x_ionBiYy7Ju3/view)。正文的相对文件链接以GitHub目录为准。

**结论：找回了siDirect提交文件、104条网页原始输出、当时的逐条筛选记录和两个科学工具的输入/源码/输出/日志。104→9按旧脚本复算一致，九条序列、方向、坐标和网站导入表对得上。它们可以作为有来源的固定开发候选，不能因此称为实验有效或安全的siRNA。**

## 文件怎么用

- [逐候选追溯表](candidate_trace.tsv)：九条全列，含原始21碱基双链、19碱基配对核心、23碱基窗口与核心坐标、模型分数、seed位点数和去重基因数。另有[JSON版](candidate_trace.json)。所有序列按5′→3′书写，坐标从1开始并包含两端。
- [104条筛选核对表](selection_104_audit.tsv)：旧排除原因与本次按旧规则算出的原因并列。原表不改。
- [原始证据包](historical_evidence.zip)：149份历史文件，含完整原始输入/输出、固定参考、源码、成功与失败日志。[每份文件的原位置、大小和SHA256](source_files.tsv)用于检查文件是否相同，不能单独证明最初执行时间或科学有效性。
- [旧交付包补取材料](prior_package_records.zip)：保留当时的环境版本、工具运行概要、分析配置与旧复现说明原文。旧复现说明含损坏中文字，保留原件；本次可读命令另见[COMMANDS.md](COMMANDS.md)。
- [本次逐项检查](audit_result.json)、[两个本地旧副本的核对](local_archive_crosscheck.json)、[权重及参考文件核对](external_assets_check.json)、[重新从官方取得源码的收据](official_reference_check/receipt.json)。
- [仍有的证据缺项](evidence_gaps.json)、[本次操作与失败记录](EXECUTION.md)、[上传记录](SYNC.md)。

## 已核实：siDirect怎样得到九条

找回位置：本地旧ChatGPT项目的`analysis/ARPE19_candidates_20261016`，以及旧交付压缩包`ARPE19_candidates_20261016_v0.1.zip`。两者是本地历史副本，不冒充独立第三方的真实性认证。ChatGPT资料库保存收据也找回了；它不是Google Drive收据。

原请求是siDirect **2.0** 的`/v2.0/design.cgi`，提交人VEGFA **NM_003376.6，3609碱基完整序列**。请求JSON、GenBank原件、固定FASTA三者序列一致。记录的提交时间为2026-10-16 08:08:31–08:08:41北京时间；HTTP状态200，原HTML为124302字节。旧清单中的“收到响应、尚待校验”状态原样保留，本次核查另写结果。

实际请求参数：Ui-Tei规则开启；seed Tm筛选开启、上限21.5°C；物种hs；全序列起止；`consGCmax=4`、`consATmax=4`、`percentGCMin=0`、`percentGCMax=100`、`customPattern=NNGNNNNNNNNNNNNNNNNNNNN`，排除模式为空。含义以原表单及请求为准，不把没有记录的服务端默认值补出来。没有用今天的网页版本重新设计并覆盖旧记录。

旧`parse_sidirect.py`对104条逐条核对23/21/19碱基配对关系，然后采用以下工作规则：

| 旧规则导致的排除 | 触发候选数 |
|---|---:|
| 任一条链的siDirect旧数据库最小错配数小于2 | 39 |
| 19碱基配对核心GC含量不在30–65% | 81 |
| 任一配对核心有至少4个连续相同碱基 | 57 |
| 核心没有同时匹配固定的20条VEGFA转录本 | 19 |

同一条可触发多个条件，**不能相加**。共同排除95条，保留9条；随后按guide核心去重，本次确认没有额外去掉重复核心。104条保存的理由与本次核对一致，保留ID和顺序也完全一致。20条转录本编号来自公司转录本注释中的VEGFA列表，实际序列从NCBI取得；这一步没有用常氧/缺氧TPM数值筛选。20/20参考匹配不代表细胞实际表达这20种转录本。

这些是恢复出来的**历史工作规则**，没有证据证明阈值已独立验证或在设计前预先注册；不能把它们写成新算法或公认安全标准。OligoFormer分数、seed计数和Agent没有参与这一次104→9的产生。

链方向按原始网页核实：guide21是23碱基靶窗口前21位的反向互补；passenger21是该窗口第3–23位的RNA形式。实际配对的19碱基位于正义靶窗口第3–21位，所以核心坐标为“窗口起点+2”至“窗口起点+20”。例如3499：设计窗口3499–3521，核心3501–3519。保留两条链原来的3′端两碱基，不能把19碱基模型输入说成完整订购双链。

## 已核实：旧OligoFormer结果来自哪里

上游固定提交`e2f53ad63387bbe166bf123949151e2bc9bf6ec3`，RNA-FM源码提交`348951516e0963d22bbb33b3c9fc18c89081d38e`。实际本地权重的SHA256与旧记录一致；OligoFormer权重5804894字节，RNA-FM权重1194424423字节。本次重新从官方固定提交取得模型/特征/数据装载源码，均与找回文件逐字节一致。RNA-FM的24份已收录源码文件也与旧固定提交源码压缩包一致。

旧运行是`run_oligo_cpu.py`适配器调用官方模型、热力学特征、数据装载器和权重：Python3.8环境，torch2.2.1+cpu、numpy1.24.4、pandas2.0.3；CPU两线程、随机种子42，显式设置推理模式和不计算梯度。RNA-FM取第12层，去掉首尾特殊标记。**它不是原Unix命令行完整流程**；显式推理模式是已记录的适配差异。原始57碱基mRNA上下文逐条由参考序列核对，九条各有一个核心匹配位置。

已有日志显示先通过官方示例的两个匹配输入，再计算九条；保存了重复结果一致及官方数据装载器一致性检查。完整成功日志、先前缺依赖失败日志均保留。九条原始class1分数、乘1.341后的分数、序列标记，与成功日志和当前网站导入表一致。缩放分数可以大于1，**不是敲低百分比或概率**。

特别说明：3119、3193、3502的官方`func_filter`标记是**4，触发官方代码中的回文序列检查**；另六条为0。这些标记在旧输出中本来就存在，本次也用未改动的官方函数核对一致。它们在先前siDirect工作池中被保留，不意味着通过了OligoFormer全部序列筛选；本轮不据此事后删除、重排或重跑。没有完成PITA、TargetScan、毒性和错配模型，不写成复现了所有模块。

## 已核实：旧SeedMatchR结果来自哪里

历史版本**1.1.1**，CRAN源码镜像提交`b462d4a00520172622f9d8a5a8842d34442c2e68`。本次从CRAN官方旧版压缩包重新取得DESCRIPTION、`get_seed.R`、`SeedMatchR.R`，与本地旧文件完全相同。旧环境没有完整安装SeedMatchR包，而是直接加载这两个未修改的官方函数；R4.3.1、Biostrings2.70.1、dplyr1.1.3、data.table1.14.8等见原`sessionInfo.txt`。保留S4Vectors、GenomeInfoDb在R4.3.2下构建的原警告。

原脚本先执行官方文档中`get_seed`示例，然后对九条的原始guide21和passenger21分别计算mer7m8、mer8、mer7A1、mer6，允许错配0、不允许插入缺失。使用GRCh38.p14、RefSeq RS_2025_08整理的**19415个基因各一条代表性3′UTR**；按优先NM、最长UTR、再按编号选择。它是参考选择，不是ARPE-19实测的主要异构体。

完整旧计数表**1397880行＝9×2条链×4种seed×19415个基因**，包含零计数。本次核实所有72块的候选/链/seed/基因均完整；网站使用的**14524行**是其中guide、mer7m8、正计数的明确子集，逐条一致，**不是漏跑后只拿成功部分作图**。旧mer7m8位点表中全部正反链位点均核对到固定FASTA，按基因合计与计数表相符。其他seed类型本次只核对旧表完整性及定义，没有重新扫描参考。

追溯表分别列出“位点数”和“去重匹配基因数”，并同时给出包含/排除VEGFA（Entrez7422）两种口径。一个基因可以有多个位点；这里没有把它们叫作状态检出基因数，也没有把多个seed类型相加。网站当前只使用guide mer7m8；历史上多算过passenger和其他seed不代表这些模块已接入网站。没有siRNA处理后RNA-seq，未做SeedMatchR的扰动表达效应统计。

## 仍缺什么，以及本次没有冒称完成什么

1. **最初启动各脚本的完整命令行、外层工作目录及逐进程退出码没有找回。**已找回执行脚本、环境版本、时间清单、实际输入/输出、标准输出和失败日志；旧`tool_runs.csv`是运行概要，不是逐命令捕获。可复现命令按脚本重建并另标，不能假装是当时的终端录屏或原始命令日志。
2. **siDirect服务端旧数据库的准确发布日期/版本没有公开在这些文件中。**它返回的错配数仅按旧网页记录解释，不声称已核实对今日全人转录组的安全性。
3. **工作阈值的独立科学验证、实验敲低及全面脱靶证据仍没有。**九条不是用户文献siRNA，修饰与最终订购形式未确定。文件一致性和模型分数都不能替代实验。
4. 原资料库收据和旧ZIP支持历史保存的连续性，但不是第三方认证的执行证明。旧ZIP与现存源目录有一份**打包日志**不同：ZIP内为空，源目录多出“打包完成，166文件”的一行；两份原件均保留，原因未独立证实。关键提交、筛选脚本、科学输出、计算日志等结构对应文件一致。没有把整个旧包称为全字节相同。

由于关键原始输入、全量输出、固定源码/权重和成功/失败日志均已找回且相互吻合，本次按用户要求**没有重复执行OligoFormer、SeedMatchR或siDirect远端设计**。只做文件、序列、计数核对，按旧规则复算104→9及官方轻量序列标记检查；没有新模型预测、新54条、新排序或新论文优越性图。检查数只是文件/程序检查数，不是科研样本量。

## 论文可以怎样写

下段仅供科研对话核对后的Methods文字，不是新实验结果：

> We used a fixed development pool of nine VEGFA siRNA candidates retained from 104 outputs of siDirect 2.0 for NM_003376.6. Recovered historical scripts applied working filters for the recorded siDirect mismatch counts, paired-core GC content, homopolymers, and exact core coverage across 20 versioned VEGFA reference transcripts. The original 21-nt guide and passenger strands and their 19-bp paired cores were retained separately. Historical OligoFormer scores were obtained using the pinned official model and weights through a documented CPU inference adapter, with 19-nt guides and 57-nt mRNA contexts. Seed counts were generated using the unmodified core functions of SeedMatchR 1.1.1 against 19,415 representative reference 3′UTRs; the application imports the guide mer7m8 subset after input matching. Provenance auditing recovered the original design responses, per-candidate selection records, outputs and logs and reproduced their internal consistency. These computational candidates and sequence matches do not establish experimental knockdown efficacy or off-target safety.

同时在补充方法保留阈值、版本、适配差异、三条序列警告、参考限制和上面列出的命令记录缺项。现有网页读取历史结果，不写成每次实时执行重型模型。本文已经放弃状态相关风险重排序；表达数据只作背景注释，不再把没有这种新排序当成本文欠缺的成果。
