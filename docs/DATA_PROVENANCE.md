# 数据、模型与原始材料来源

## 自有基线RNA-seq

原始本地位置：`C:\00000\ARPE RNA-seq\result\result.zip`。此前分析提取公司结果中的`6_expression/expression/gene_tpm.xls`等表；研究基线包位于本地`deliverables/ARPE19_baseline_20261016_v0.1`。

样本：Nor1–4与Hyp1–4，用户确认同一培养批次、8个不同培养皿、每皿分别提RNA、未混样、未加siRNA/转染试剂；缺氧1% O2连续24h，常氧同期培养。不能按编号推断配对，也不能写成4轮独立培养。

2026-10-29同步后的`data/expression.tsv.gz`包含43,418条核验的唯一Entrez-参考条目，保留feature_id、approved_symbol、ENTREZID、Nor1–4/Hyp1–4逐样本TPM、两状态均值和TPM≥1样本数。当前来源/校验与映射规则见`data/expression_provenance.json`、`data/expression_mapping_evidence/`，复现入口为`scripts/sync_expression_baseline.py`。没有按后缀删行、加总或挑最小P值。旧43,385条仅摘要版本保存在`expression_legacy_20261016.tsv.gz`，历史来源仍可查。它不是原始FASTQ、不是siRNA处理后RNA-seq；基因表达不能证明实际3′UTR异构体/APA或seed位点可及性。

网页表达检测规则为每状态TPM≥1且至少2/4样本，仅作描述性标记。TPM不进入效力模型，不改变排序。上传模板需要基因级未取对数TPM、唯一人Entrez ID；格式校验不能证明单位/物种/实验声明真实。

## 默认9候选

2026-10-23已从原本地目录和旧交付包找回并核对：[完整来源核查](../research/2026-10-23_candidate_provenance/README.md)、[九条追溯表](../research/2026-10-23_candidate_provenance/candidate_trace.tsv)、[104条保留/排除表](../research/2026-10-23_candidate_provenance/selection_104_audit.tsv)。原siDirect2.0请求、104条HTML、逐条理由和筛选代码均保留；104→9按旧规则一致。20条固定转录本用于核心覆盖检查，不用状态TPM值筛选。旧OligoFormer输入/分数和完整SeedMatchR1.1.1输出1397880行与当前导入表一致。最初完整shell命令和siDirect旧数据库具体发布日期未找到；当前审核不冒充第三方原始运行认证。三条官方回文序列警告、适配差异及打包日志差异在报告中披露，旧数据不改。

2026-10-16用人VEGFA参考NM_003376.6的siDirect 2.0结果，104条原始候选中整理出9条工作池；10月18日核对并用于Agent原型。来源字段、原始21nt双链、19nt配对核心、末端、参考覆盖保留在`data/candidates.tsv`。

候选ID：VEGFA_SD_1157、2739、3119、3193、3429、3499、3500、3502、3535。不是用户有效文献siRNA；修饰未冻结、不作订购单。优先复核3499/3500来自当前程序规则，不代表新发现或验证效力。

## 官方工具与参考

- OligoFormer：https://github.com/lulab/OligoFormer ，论文doi:10.1093/bioinformatics/btae577；历史上游commit e2f53ad63387bbe166bf123949151e2bc9bf6ec3。使用官方权重、RNA-FM与IO适配，不训练新模型。适配器显式CPU/eval/no_grad、固定随机性、保留官方层12表征切片，差异需如实记录。
- RNA-FM：https://github.com/ml4bio/RNA-FM 。历史权重约1.194GB；不入Git。路径与SHA256见provenance。源码/依赖和词表也要固定。
- SeedMatchR：https://github.com/tacazares/SeedMatchR ，历史版本1.1.1；论文doi:10.1093/bioinformatics/btae011。本项目目前用guide mer7m8精确匹配代表性参考3′UTR，不等于运行了全部seed/链/差异表达效应统计。
- 参考：固定20条VEGFA转录本FASTA；基因级代表性3′UTR。UTR序列、manifest、映射和版本必须一起核验；当前参考覆盖不等于实际异构体使用。
- `data/historical_scores.tsv`与`historical_seed_matches.tsv`为历史输出。score/sequence/context一致才允许复用。
- `data/historical_near_matches.tsv`为已有Biostrings固定Hamming匹配（无indel）的补充记录，不是新发明的脱靶预测算法；仅原guide一致时使用。

原文完整OligoFormer还含PITA/TargetScan/其他筛选模块；本项目未完成这些模块和全面毒性检测。官方scaled score可大于1；不要当概率或敲低比例。

## 文件位置与交接范围

Git中提供当前应用、已有计算输入/输出、13幅SVG、绘图数据、压缩54条原始汇总（含对话/错误）、批次协议和复现脚本。大型模型权重、完整FASTQ、重复生成的巨大逐次中间表不进入Git。逐基因seed/TPM明细可用仓库现有data重新生成。

原始完整下载包及本地成果仍在用户电脑：
- `C:\Users\86182\Downloads\development_evaluation.zip`
- 项目目录下`deliverables/siRNA_GPT_results_20261019_v1.zip`与`deliverables/evaluation_audit_20261019.zip`
- 历史计算环境`analysis/ARPE19_candidates_20261016`，含oligo_env、官方工具、prepared参考与risk_raw。

完整原始包的SHA256和Git交接文件校验见research/manifest；关键压缩记录可用仓库脚本展开查看。历史本地路径只是查找线索，不能在云端声称它存在；缺失时从官方来源重建并校验。
