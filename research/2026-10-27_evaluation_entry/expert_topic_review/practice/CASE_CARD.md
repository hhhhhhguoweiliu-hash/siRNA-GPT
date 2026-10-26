# 旧真实开发练习例：只理解材料，不纳入正式评分

原运行20261024_121627_1e50c9，代码03092ef；是一例实际Agent流程，没有另外两组同题新回答。不能与新W1的两状态题干混配，也不是未见题。

## 当时完整需求

请只对当前已选择的既购si-VEGF完成一次完整核查并生成最终报告：核对原始双链与链方向假设、固定靶参考、读取绑定版本的真实OligoFormer分数和seed结果、关联表达背景，再生成报告。保留TT和N3原文，说明模型没有模拟N3连接实物。不要混入旧九条或重新运行重型计算。

[当时实际输入](actual_evidence/input.json)；[用户当时收到的完整答复](actual_delivered_answer_UNCHANGED.txt)；[实际报告](actual_evidence/report.html)。**必须同读[原答错误与纠正](ANSWER_CORRECTION_ZH.md)**：模型把另一链19位核心复述成24位，原答保留；后加纠正不算模型当时说对。

## 实际过程与证据导航

| 核对项 | 实际原件定位 | 这份证据不能证明什么 |
|---|---|---|
| 原始两行、TT/N3与条件性链分配 | [input.json](actual_evidence/input.json)、[候选检查](actual_evidence/inspect_candidates.json) | 不是供应商确认或N3实物模拟 |
| 参考核心坐标和公共参考覆盖 | [verify_target.json](actual_evidence/verify_target.json)：rows[0].core_start_1based/core_end_1based、covered_transcripts | 不是本细胞实测异构体覆盖 |
| 预测分数 | [score_candidates.json](actual_evidence/score_candidates.json)：rows[0].oligoformer_scaled_score、evidence_dataset_id | 不是实测敲低率；旧全局legacy指纹不是既购数值的来源 |
| seed位点/基因 | [match_seed.json](actual_evidence/match_seed.json)：seed_site_counts_nontarget、counts、supplemental_both_strand_seed_summaries | 匹配不是实测脱靶，位点不是基因 |
| 表达映射与检出 | [query_expression.json](actual_evidence/query_expression.json)：candidate_summary、expression_comparison；[来源](actual_evidence/expression_source.json) | 未转染基线仅注释，不能证明第7天敲低或安全 |

实际6项工具均执行；当时模型请求8次，合计39048词元，详见[真实调用与用量](actual_model_call_summary.json)。工具执行完整不等于回答无错。完整会话原件另附，不要求评审通读模型提示词或源码；不涉及隐藏思维链。

没有生成新的完整三组回答，没有练习评分，也不把新软件防错回填旧原答。正式评分包另行从实际运行生成，练习例与本册不随正式匿名回答一起发出，以减少先入判断。

既购数值可继续回查[独立结果](actual_evidence/verified_import/purchased_sivegf_20261024_v1/verified_local_result.json)及[绑定清单](actual_evidence/verified_import/purchased_sivegf_20261024_v1/manifest.json)。[当时完整工具导出原包](actual_tool_export_original.zip)原样保留，后加说明不算模型原答。
