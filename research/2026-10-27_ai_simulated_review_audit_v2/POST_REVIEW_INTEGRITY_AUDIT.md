# siRNA-GPT 27份答复 AI预评审：一致性审计与修订记录

- 评审者：ChatGPT；日期：2026-10-27
- 性质：AI模拟科研预评审；本文件审计既有完整逐项预评审的原件范围与计算一致性，不是独立真人专家评审
- 分支：`codex/20261020-evidence-pilot`
- 本次读取时源分支HEAD：`33cd2283a951ee71e8788c348ce8ea2e617b7ceb`
- 用户指定交接提交：`c30473d3168ccf5ce6522722f0cea857c2065037`；GitHub compare确认当前HEAD比其前进42个提交，交接提交是共同祖先
- 原评审输入快照：`bfa1a0d19f5e207fc0ef4804b14c89ae7834a965`
- 本目录为新建审计副本，不覆盖原目录 `research/2026-10-27_ai_simulated_review/`。

## 1. 实际读取的材料与原件验证

实际读取：`START_CHATGPT.md`、`docs/USER_REQUIREMENTS.md`、`AGENTS.md`、`COLLABORATION.md`、`docs/WORKBOARD.md`、`docs/STATUS.md`；`docs/reviews/20261027_agent_improvement_and_metric_handoff.md`；`research/2026-10-27_agent_improvement_handoff/metric_protocol.md`；原运行README、`raw/results_original.json`、`cases_original.json`、`analysis_plan_original.json`、`execution_status_original.json`；`fact_items_DRAFT.json`、`anchors.json`、`criteria.json`、`TASKS_AND_STANDARDS.md`；既有科研复核文件；以及原始运行ZIP `model_and_tool_records_original.zip`。重点核对了A013、A014、A020、A006、A002、A022、A008、A010、A023的各轮正文、附件和内部原始模型文字。

- `results_original.json`：3,495,823字节；本地SHA256 `f443d6f358a3c63f45eeef0906ae968f74f231534eb3c5276207767a14c2b9a3`；Git blob SHA `f0b334c3d5b1c44d4a164a1752d32df38043e480`。两种SHA用途不同。
- `model_and_tool_records_original.zip`：9,814,625字节；SHA256 `512ab027fddd8c1ecabda20b7243a610c2f14a07a80130e832eebe083ed0c2c3`；1,550个成员、33份轮次记录、62个模型响应记录。
- 原始JSON记录27份答复、33轮；本次不启动新的问答批次。

## 2. 范围与缺失材料

主评分采用每轮实际交付的 `answer` 正文，以及原始记录明确列出的可访问业务报告/数据附件。内部 `raw_model_answer`、请求/响应、计划、工具日志只作诊断，不替代实际交付。附件定位依据 `raw_delivery_scope.csv` 与原始运行包的 `answers/Axxx/attachments/`。没有原始客户端UI截图，因此不能独立复原当时界面上的每个附件点击呈现。

仍缺、不能冒充已完成：
1. 独立真人批准的必答标准、批准人及批准时间；135条标准均是回顾性AI草案。
2. 独立真人逐槽裁决及独立盲评；三组映射已知，本轮不称盲评。
3. 严格规划四指标所需的有限动作全集、三组对等原始计划、逐步gold_selected/predicted_selected和批准记录。
4. Q1/Q2两道文献任务未在本批27份答复中运行，不计入分母。
5. 本候选/本条件的湿实验敲低与脱靶真值。
6. R4明确禁止回退内置表达表且用户表缺失，因此表达关联和完整表达报告未完成。

## 3. 原子标准、完整性与公式

原草案共70条：实际运行的W1/W2/W2b/W3/U1/R1/R2/R3/R4共59条；Q1/Q2共11条未运行。复合草案拆分并加入原题干要求后形成135个独立必答槽位。405条判断=135槽位×3组，状态：CORRECT 313、WRONG 13、MISSING 79、UNJUDGED 0、NOT_APPLICABLE 0。U1/R1的多轮逐轮检查，但每组仍是9个任务单元。

按metric_protocol：CORRECT→TP+1；WRONG→FP+1且FN+1；MISSING→FN+1；UNJUDGED不能填零。独立重算显示所有12个组别/类别汇总行的TP/FP/FN、micro及macro值与槽位明细一致。

## 4. 本审计副本修正的两处不一致

1. 旧README汇总表仍写Agent 7/9、130槽位、TP=129，并称Agent的P/R/F1整体较高；与最新任务结论、405槽位明细和metrics_status.json不一致。本副本已改为Agent 6/9、135槽位、TP=128、FP=1、FN=7，并重写比较文字。
2. 旧metrics_by_task.csv中A002为task_verdict=FAIL但task_pass_indicator=1；逐题状态表判A002失败。本副本已将该指示改为0。

两项是评审产物的汇总/版本错误；未改变任何原始答复、原专家评分或历史失败记录。

## 5. AI预评审指标

| 组别 | Task accuracy | 必答槽位n | TP | FP | FN | Micro P | Micro R | Micro F1 | Macro P | Macro R | Macro F1 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 普通LLM | 1/9 (11.11%) | 135 | 55 | 12 | 80 | 82.09% | 40.74% | 54.46% | 92.22% | 46.67% | 59.78% |
| 固定流程 | 8/9 (88.89%) | 135 | 130 | 0 | 5 | 100.00% | 96.30% | 98.11% | 100.00% | 93.06% | 94.95% |
| Agent | 6/9 (66.67%) | 135 | 128 | 1 | 7 | 99.22% | 94.81% | 96.97% | 99.07% | 93.52% | 95.37% |

Task accuracy为通过整题数/9；其余P/R/F1为必答槽位指标。Micro合并槽位计数；Macro先按题计算再取均值。严格CRISPR-GPT C1规划Accuracy/Precision/Recall/F1为NOT_READY，不能用本表替代。

## 6. 关键案例

- A013：正文显示“模型序列检查未通过”，可访问附件有正确0.9915144175887107分数及57nt上下文；内部raw也正确但不能替代正文。附件槽位可计正确，正文/附件矛盾仍使整题FAIL。
- A014：分数附件的来源字段存在且数值正确；“2025年X月X日”是无效占位日期，不代表整个来源凭空编造。
- A020：九条都把23nt窗口起点误当19nt核心起点，九个核心坐标均错。
- A006：`independent_check=PASS`确实存在；错误是把序列审核状态解释为“无脱靶证据”，忽略`SEQUENCE_REVIEW_FLAG_NOT_DEMONSTRATED_OFF_TARGET`。
- A002：IRGM来源记录存在，但正文/附件未展开查询定义、精确查询序列、坐标、精确错配数及PASS解释；属于证据披露缺失，不是来源不存在或凭空编造。
- A023：停止计算是合理的，但未回答旧分数不可迁移、可保留字段和需重核字段，故任务未完成。
- A022：主坐标结论正确；但3610–3628闭区间本身是19nt，只是越过3609nt参考末端。错误解释另列，不推翻主结论。
- A008：旧分数不能迁移的结论正确，但把来源归于用户计算假设不准确；它实际是绑定旧核心/上下文的导入结果。
- A010：末尾询问是否启动新评分与用户限制不协调，但没有实际启动新评分。
- A011/A025：共用错误呈现模板；A011为0次模型请求，A025为6次，不能将模板说明归为Agent自主推理。

## 7. 保留原则

没有改写原始27份答复、33轮原答、内部模型原文、附件、工具记录、原专家0–2评分或历史失败；没有启动新的模型/API问答、微调、状态风险重排序或湿实验。原始评审目录保持不变。
