# siRNA-GPT：27份真实答复的AI模拟科研预评审

- 评审者：ChatGPT
- 日期：2026-10-27
- 评审版本：AI_PRE_REVIEW_2026-10-27_v1（本目录为一致性审计副本 AUDIT_V2_2026-10-27）
- 任务分支：`codex/20261020-evidence-pilot`
- 评审输入快照的分支头（本轮写入前）：`bfa1a0d19f5e207fc0ef4804b14c89ae7834a965`
- 原运行：`mini_real_20261027_061408`
- 原结果提交：`4244ac0d9b9f0b1e01fe46f6871fd664825a4c24`
- 运行源码提交：`6c13c5788405e8ecf1aaf77144accd8108701d48`
- 交接提交：`c30473d3168ccf5ce6522722f0cea857c2065037`
- 本次审计时源分支HEAD：`33cd2283a951ee71e8788c348ce8ea2e617b7ceb`（比交接提交前进42个提交；原评审输入快照仍为 `bfa1a0d19f5e207fc0ef4804b14c89ae7834a965`）
- 性质：**AI预评审，不是独立真人评分；标准为回顾性AI草案，未证明在原运行前获真人批准。**

## 1. 实际读取的原件与版本

已读取并核对：

- `START_CHATGPT.md`（blob `836cda6faf4e209e4541c613030b82ef6a793009`）、`docs/USER_REQUIREMENTS.md`（`28082469008aadedb415dfa468df7cfd3b8cc48f`）、`AGENTS.md`（`2bf320c842b56bdea06c81780019565201c4f884`）、`COLLABORATION.md`（`196fb6d1b67c0cee34b2fc8f8eae8f32f5a4af68`）、`docs/WORKBOARD.md`（`2016112d3ffc3306db8fe6bcfc73653603c36792`）、`docs/STATUS.md`（`9db6eeba60b1668ebc788547fc088cc31dc6fa98`）。
- `docs/reviews/20261027_agent_improvement_and_metric_handoff.md`（`d6ad6f194a02c9799ad9d91c19053d8a0b111e54`）。
- `research/2026-10-27_agent_improvement_handoff/metric_protocol.md`（`6ad8365caa3f4a8e5fa8c5b66721b45459909742`）。
- `research/2026-10-27_real_dialogue_mini/raw/results_original.json`：通过Git blob读取并解析，blob SHA `f0b334c3d5b1c44d4a164a1752d32df38043e480`；该文件的普通inline fetch不返回内容，但blob读取成功，不是材料缺失。
- `fact_items_DRAFT.json`（`496e5d3cab205fbcedf803538174faccd4134ccc`）、`anchors.json`（`18449a9bb4dede2c344fbcd2def7adba3c1af5fa`）、`criteria.json`（`410fd88eb75c260edf94b7e100b901bdee44cb49`）。
- 既有复核：`20261027_final_expert_score_workbook_review.md`、`20261027_pasted_score_reason_consistency_review.md`、`20261027_three_evaluation_objections_evidence_review.md`；以及 `answer_origin_by_round.csv`（`0aabb0ba04955221f5ddeb8322415a4305325222`）。
- 已读取评审总册及其中嵌入的原件包；按A编号检查 `answer.txt`、各轮 `process.json`/原始JSON、可访问附件与内部 `raw_model_answer.txt` 的差别。

## 2. 评价对象和原件范围

**主评价范围**：本次实际交付的每轮最终答复 + 本答复明确随附、可访问的报告/数据附件。附件字段可补足正文未展开的精确值，但不能抹去正文与附件之间的实质矛盾。

**仅作诊断、不代替主答复**：内部 `raw_model_answer.txt`、内部请求/响应、计划、工具日志。A013内部模型原文的正确数值不会替代实际主答复；其附件另按实际可访问范围独立检查。

**归因限制**：A011/A025共用错误展示模板；最终文本同一并不代表两组整个过程相同，也不等于该说明由模型自主撰写。A025有6次模型请求，A011为0。此类共用规则功劳归系统/实现，不独归Agent。

## 3. 标准拆分

原始草案文件共70条：九个实际运行任务W1/W2/W2b/W3/U1/R1/R2/R3/R4合计59条；Q1/Q2另有11条，但本次27份运行未执行，明确排除出本批指标分母。

把59条复合草案结合原始题干、输入与固定证据拆分后，本轮形成 **135个独立必答槽位**，覆盖27份答复；U1/R1的两轮均检查，但每组仍只有9个任务单元。另加入从原始题干提取、原草案未覆盖的范围/来源约束，并在 `draft_reconciliation.csv` 逐条说明。

所有标准均标记 `NOT_APPROVED_AI_DRAFT`。没有把当前工具排名作为生物学最佳标准；没有把OligoFormer分数当敲低率、seed计数当实测脱靶或任何计算当湿实验真值。

## 4. AI预评审指标

### 4.1 每组整体

| 组别 | Task accuracy | 必答槽位数 | TP | FP | FN | Micro precision | Micro recall | Micro F1 | Macro precision | Macro recall | Macro F1 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 普通LLM | 1/9 | 135 | 55 | 12 | 80 | 82.09% | 40.74% | 54.46% | 92.22% | 46.67% | 59.78% |
| 固定流程 | 8/9 | 135 | 130 | 0 | 5 | 100.00% | 96.30% | 98.11% | 100.00% | 93.06% | 94.95% |
| Agent | 6/9 | 135 | 128 | 1 | 7 | 99.22% | 94.81% | 96.97% | 99.07% | 93.52% | 95.37% |

- Task accuracy = 达到预先写明的整题通过条件数 / 9；U1/R1各自的两轮合为一个任务单元。
- 必答槽位计数：CORRECT→TP+1；WRONG→FP+1且FN+1；MISSING→FN+1。UNJUDGED不自动记零；本轮AI预评审已对全部槽位作出临时判断，真人仍待复核。
- Micro是汇总全部槽位计数后计算；Macro是先逐题计算P/R/F1再在同类任务中取算术均值。主结果为AI预评审，不是正式专家指标。

### 4.2 按任务类别分别报告

| 组别 | 类别 | Task accuracy | Macro precision | Macro recall | Macro F1 |
|---|---|---:|---:|---:|---:|
| 普通LLM | 标准任务 | 0/4 | 82.50% | 32.83% | 45.78% |
| 普通LLM | 可靠性任务 | 1/4 | 100.00% | 57.59% | 70.30% |
| 普通LLM | 需求变化任务 | 0/1 | 100.00% | 58.33% | 73.68% |
| 固定流程 | 标准任务 | 4/4 | 100.00% | 100.00% | 100.00% |
| 固定流程 | 可靠性任务 | 3/4 | 100.00% | 84.38% | 88.64% |
| 固定流程 | 需求变化任务 | 1/1 | 100.00% | 100.00% | 100.00% |
| Agent | 标准任务 | 2/4 | 100.00% | 87.50% | 91.67% |
| Agent | 可靠性任务 | 4/4 | 100.00% | 100.00% | 100.00% |
| Agent | 需求变化任务 | 0/1 | 91.67% | 91.67% | 91.67% |

详细每题TP/FP/FN、分母、每题P/R/F1与PASS/FAIL见 `metrics_by_task.csv`；每组/类别的任务数、micro和macro汇总见 `metrics_summary.csv`。

## 5. 严格规划指标：NOT_READY

严格的CRISPR-GPT C1规划Accuracy/Precision/Recall/F1没有计算。缺少：

1. 版本固定、有限的可选动作全集与适用性标记；
2. 三组对等的实际原始计划列表（普通LLM没有可比结构化计划；固定流程工具清单不是自然语言自主计划）；
3. 逐步骤的真人批准标准 `gold_selected`、实际计划选择 `predicted_selected` 与可追溯计划原文；
4. 标准批准人、批准日期和版本。

不把普通LLM没有工具调用填成“规划全错”，不把工具执行结果冒充计划，也不从无限未选内容凑TN。详细缺口见 `planning_metrics_status.json`。

## 6. 主要结果与局限

- 固定流程整题通过率为8/9，Agent为6/9。按必答槽位汇总，固定流程micro P/R/F1为100.00%/96.30%/98.11%，Agent为99.22%/94.81%/96.97%；macro F1分别为94.95%和95.37%，macro recall分别为93.06%和93.52%，macro precision分别为100.00%和99.07%。这些是AI预评审结果，不能据此宣称Agent整体优于固定流程。
- A013说明：附件数值正确与最终主答复错误可以同时成立。槽位指标会计入明确可访问附件，整题指标会捕捉主答复/附件矛盾。A002则相反：输入中有完整IRGM记录，但答复和附件未展开查询定义、查询序列、坐标、精确错配数和PASS解释，属于证据披露缺失而不是来源编造，整题不通过。
- A014的占位日期是实际交付中的来源问题。
- A020把23nt窗口坐标当19nt核心坐标，是关键事实错误。
- A023正确停止了无效核查，但没有回答旧分数是否可复用、哪些证据可保留/需重核，因此整题仍失败。
- A006的 `independent_check=PASS` 字段确实存在；问题是解释边界，不是该字段凭空编造。
- A011/A025同文是共用错误处理模板；不能把模板说明归为Agent独立推理。
- W1/W2/W2b等数字核对证明的是结果获取、版本绑定和交付可追溯性，不证明工具预测真实敲低效力。当前无湿实验效力真值，未评哪条siRNA生物学最佳。

## 7. 待真人裁决与缺失材料

- 所有135个独立必答槽位、27个整题结论都是AI临时判断，尚无真人确认；未进行独立盲评。
- 需要独立领域人员确认可接受答案、容差、严重错误是否使整题失败，重点复核A013/A014/A020/A006/A022/A008/A010/A023。
- Q1/Q2文献任务未运行，未计入本批。
- 严格规划指标的有限动作全集和对等计划缺失。
- 没有湿实验敲低/脱靶真值；不支持生物学有效性结论。
- 原0–2专家评分没有用作本轮真假标签，没有被修改；不把本次AI预评分冒充原专家确认。

## 8. 文件目录

- `required_slots.csv`：135条原子必答标准及证据/条件/限制。
- `slot_reviews.csv`：405条逐槽AI判断，含原答/附件位置、提供值、状态与理由。
- `task_reviews.csv`：27份整题PASS/FAIL及通过理由。
- `metrics_by_task.csv`：逐题TP/FP/FN、P/R/F1、分母与整题结论。
- `metrics_summary.csv`：整体和分类别的Task accuracy、micro与macro必答槽位指标。
- `raw_delivery_scope.csv`：33轮主答复/内部原文/工具来源/附件范围，raw只作诊断。
- `group_map.csv`：独立保存的三组映射；本轮不是盲评。
- `extra_errors_and_gaps.csv`：严重错误、额外错误、来源与范围缺口。
- `draft_reconciliation.csv`：原草案条目到原子槽位映射，标记未运行Q1/Q2。
- `planning_metrics_status.json`：严格规划四指标的NOT_READY状态及缺口。
- `metrics_calculation.py`：只读CSV、可复现计算Task accuracy与槽位P/R/F1。

本评审没有启动新的模型问答批次、付费API批次、微调或湿实验，也没有修改原始答复、原专家评分、旧失败记录、main或线上网站。
