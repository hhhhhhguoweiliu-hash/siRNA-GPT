# 复现入口

在仓库根目录使用Python 3；以下脚本只用标准库。每个`--output`须是新目录。临时目录指定为仓库`_test_runs`，避免系统临时目录的写入限制。完整检查原始日志保留在本目录。

```powershell
$env:PYTHONIOENCODING='utf-8'
$env:TEMP=(Join-Path (Get-Location) '_test_runs')
$env:TMP=$env:TEMP
python research/2026-10-27_followup_execution/recompute_metrics.py --output audit_outputs/new_metrics
python research/2026-10-27_followup_execution/consistency_audit.py --output audit_outputs/new_consistency
python research/2026-10-27_followup_execution/independent_checks.py --analysis 'C:\Users\86182\.codex\.chatgpt-projects\g-p-6a82e08661e081919f3434650ae4f35c\analysis\ARPE19_candidates_20261016' --tpm 'C:\00000\ARPE RNA-seq\result\result\6_expression\expression\gene_tpm.xls' --mapping 'C:\Users\86182\.codex\.chatgpt-projects\g-p-6a82e08661e081919f3434650ae4f35c\analysis\ARPE19_agent_v2_20261018\deliverable\02_background\gene_expression_background.tsv' --output audit_outputs/new_independent_same_mapping
python -m unittest test_followup_integrity test_sequence_validation test_conversation test_optimization -v
```

独立脚本只读原TPM、同版FASTA/manifest、官方任务输入/计数/位点及静态映射。映射文件中的数值列不作为复算输入。原包装表的检出数仅在复算结束后作为比较对象。无需生产服务器、API凭证、联网或新模型调用。

省略`--mapping`会复现第一轮不同静态映射的差异，不能当成与原生产映射同口径的通过结果。输入指纹及样本列见两轮`run.json`。`build_addenda.py`重建原答回放/原件指纹/并列对照，不修改原件；它需本地Git历史。

不运行`run_confirmed_dialogue_once.py`，不恢复付费整批。新工具字段展示及缓存/子流程的测试替身不是真实模型成绩。已有评价默认冷会话，新Agent子流程策略需在未来运行前明确记录，不悄悄改变旧评价定义。
