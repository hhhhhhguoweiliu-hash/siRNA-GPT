# 已有结果、图表与原始评价记录

2026-10-23新增：[任务A：默认九条来源核查](2026-10-23_candidate_provenance/README.md)，含原始104条设计响应、真实104→9筛选、九条序列/方向/坐标、OligoFormer/SeedMatchR旧运行及完整计数核对、原始成功/失败日志和缺项。本轮无新模型推理或新54条。用户已放弃状态相关风险重排序；旧图和旧路线保留为历史，不追溯改成当前新成果。

本目录为真实产物的Git交接版，未运行的模型结果没有补造。全部文件校验见[manifest.json](manifest.json)，可运行`python scripts/inspect_research_results.py`检查。

## 2026-10-19原型与表达背景

[说明](2026-10-19_scientific/README.md) · [数据](2026-10-19_scientific/data) · [10幅SVG](2026-10-19_scientific/figures) · [中文图注](2026-10-19_scientific/figure_captions.json)

1. 系统结构与实时/历史结果边界。
2. 9条计算候选的OligoFormer分数（非敲低率）。
3. 19nt guide与seed位置。
4. 固定VEGFA参考转录本覆盖。
5. 非靶seed匹配基因的两状态表达与未映射数。
6. 自有8样本VEGFA基线TPM。
7. 预先列出背景基因的表达图。
8. 本地固定流程18次开发记录（全部保留）。
9. 本地固定流程耗时，非重型推理耗时。
10. TPM描述性检测阈值的敏感性。

图2–5不证明实际效力或脱靶；图6–7是未转染基线；图8–9不是三组对照；图10不产生新的融合风险分数。

## 用户下载的真实三组开发批次

[核查说明](2026-10-19_evaluation/README.md) · [54条审计表](2026-10-19_evaluation/all_54_records_audited.tsv) · [原始汇总JSON.gz](2026-10-19_evaluation/raw/results.json.gz) · [协议](2026-10-19_evaluation/raw/protocol.json)

记录时间：2026-10-19 22:19:29–22:20:58（北京时间）。54条完整记录，但36条模型依赖案例均为账号用量上限阻断。不能说三组评价成功完成、Agent劣于固定流程，或把错误响应耗时当正常模型效率。3幅Audit图只呈现基础设施结果和固定流程耗时。

`raw/results.json.gz`保留全部54条原始汇总，包括Agent对话/诊断、固定流程工具证据。完整下载ZIP约2.6MB的重复中间表未展开重复提交；原包SHA256见manifest，可从用户电脑取得。完整逐基因seed/TPM明细可由现有仓库data重新生成。

## 人工评审准备

[20项待审核任务草案](expert_review/task_review_draft.tsv) · [空白评分表](expert_review/blind_scoring_template.tsv) · [说明](expert_review/review_instructions.md)

这些不是专家已审核题库，不是独立冻结测试集，没有代填专家分数。原失败批次不得混入新的成功批次。

## 复现

```powershell
python scripts/inspect_research_results.py
python scripts/rebuild_candidate_report.py --output evaluation_runs/new_candidate_report
# 绘图另需numpy/pandas/matplotlib，轻量云端服务不需要安装这些依赖
python scripts/plot_research_results.py --output figures_rebuilt
```

原始测序、重型权重和历史本地计算环境的位置见[数据来源](../docs/DATA_PROVENANCE.md)。Git内已提供绘制交接图所需的汇总表；要重做从原始逐样本矩阵到阈值敏感性的全部分析，需回到原始矩阵和映射记录。
