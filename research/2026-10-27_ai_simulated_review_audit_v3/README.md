# siRNA-GPT：27份真实答复的 AI 模拟科研预评审（第三版一致性审计）

- 评审者：ChatGPT
- 日期：2026-10-27
- 性质：**AI预评审，不是独立真人评分；所有标准和标签均待真人确认。**
- 目录版本：`AUDIT_V3_2026-10-27`
- 任务分支：`codex/20261020-evidence-pilot`
- 本次重新核对的源分支 HEAD（写入本目录前）：`ab54de166d77cf2c34ee7d9a5219e8ff3e6d834b`
- 最新 main HEAD（读取时）：`2623c8601bd4b19b472fafc520b95c0cfd0a0fdb`
- 用户指定交接提交：`c30473d3168ccf5ce6522722f0cea857c2065037`
- GitHub compare：任务分支相对交接提交前进43个提交；相对main前进82个提交、落后0个。没有把旧交接状态覆盖远端较新内容。
- 原始运行：`mini_real_20261027_061408`；运行源码提交：`6c13c5788405e8ecf1aaf77144accd8108701d48`；原始结果提交：`4244ac0d9b9f0b1e01fe46f6871fd664825a4c24`。
- 不启动新模型问答批次，不微调，不恢复状态风险重排序，不扩大湿实验。

## 1. 实际读取的材料、版本与缺失

### 协作和任务范围
- 任务分支的 `START_CHATGPT.md`（blob `836cda6faf4e209e4541c613030b82ef6a793009`）、`docs/USER_REQUIREMENTS.md`（`28082469008aadedb415dfa468df7cfd3b8cc48f`）。
- main 的 `AGENTS.md`（`2bf320c842b56bdea06c81780019565201c4f884`）、`COLLABORATION.md`（`196fb6d1b67c0cee34b2fc8f8eae8f32f5a4af68`）、`docs/WORKBOARD.md`（`5f206579f519426a291846244ee54ef79847302b`）、`docs/STATUS.md`（`665f6fff822f36abd7203e8738a49528c4c357c3`）。
- `docs/reviews/20261027_agent_improvement_and_metric_handoff.md`（`d6ad6f194a02c9799ad9d91c19053d8a0b111e54`）。
- `research/2026-10-27_agent_improvement_handoff/metric_protocol.md`（`6ad8365caa3f4a8e5fa8c5b66721b45459909742`）。
- 既有科研复核：`docs/reviews/20261027_three_evaluation_objections_evidence_review.md`、`docs/reviews/20261027_final_expert_score_workbook_review.md`、`docs/reviews/20261027_pasted_score_reason_consistency_review.md`、`docs/reviews/20261027_evidence_fidelity_and_independent_checks_tasks.md`。

### 原始答复、输入和科学证据
- `research/2026-10-27_real_dialogue_mini/raw/results_original.json`：Git blob `f0b334c3d5b1c44d4a164a1752d32df38043e480`；3495823字节。原记录SHA256见同目录 `SHA256SUMS.json`：`f443d6f358a3c63f45eeef0906ae968f74f231534eb3c5276207767a14c2b9a3`。
- `raw/cases_original.json`（blob `d29d70793d520d7247f324f8be2de302c7475a0d`）、`raw/protocol_original.json`（`f24ee8ca7b00724dfce9d8b5b0f7a6bea7c96240`）、`raw/execution_status_original.json`（`f4ccbf032f19e827e54287a0d1c9a5740cc9df82`）。
- `fact_items_DRAFT.json`（`496e5d3cab205fbcedf803538174faccd4134ccc`）、`anchors.json`（`18449a9bb4dede2c344fbcd2def7adba3c1af5fa`）、`criteria.json`（`410fd88eb75c260edf94b7e100b901bdee44cb49`）。
- 原始工具/轮次归档 `raw/model_and_tool_records_original.zip`（blob `6f413bc8dfc660d81160d3bc957e8364e7b85547`，9814625字节；历史清单记录SHA256 `512ab027fddd8c1ecabda20b7243a610c2f14a07a80130e832eebe083ed0c2c3`）。本次重新审计直接解析了完整原始JSON中的27份答复、全部33轮、各轮输入与嵌入工具结果，并核对原有附件定位清单；**本次没有在本地再次解包这份1550成员的二进制ZIP**。该归档仍在仓库中，先前复核记录说明其附件审计。没有原始客户端UI截图，因此不能独立证明每个附件当时在UI中如何呈现/点击。
- 原始答复JSON的普通inline读取返回空；通过Git blob读取成功。该接口现象不是源文件缺失。

### 评审输入快照与缺失
- 初版AI逐项评审源快照：`bfa1a0d19f5e207fc0ef4804b14c89ae7834a965`；其后43个提交包含原子槽位细化、A002证据披露修订、计算更新和审计副本。
- 27份原答、原专家评分、历史失败、原图均未覆盖。
- 缺少：原运行前真人批准标准的证据；独立真人逐槽裁决；独立盲评；三组可比的原始结构化计划；湿实验敲低/脱靶真值。Q1/Q2两道文献题不在本批运行内。
- R4明确不能回退内置表达表，用户本轮未提供允许使用的表达表；因此拒绝回退是正确边界，但完整表达关联报告仍未完成。

## 2. 评价对象与标准拆分

本轮评价构念限定为 **工具证据检索与报告保真度**（Tool-evidence retrieval and report fidelity）：在给定资源与任务范围内，是否正确取得、绑定版本、限定含义并交付可追溯的已有计算证据。它不等同于生物学效力、实际敲低率、脱靶安全性或一般科研判断力。

- 原草案共70条：实际运行的W1/W2/W2b/W3/U1/R1/R2/R3/R4共59条；Q1/Q2共11条未运行，不进本批分母。
- 原59条复合草案拆分为126个独立槽位；从原始题干补充的通用范围/证据约束为8个；W1原题另有“提供可定位的报告与候选表附件”1项，原草案未覆盖。**本版共135个必答槽位，已全部映射**：126+8+1=135。
- 135个槽位各自有：题号、轮次、槽位编号、具体要求、可接受值/表述、容差、参考转录本/版本、链角色假设、条件、证据文件/字段/原文定位、禁止事项、判断规则、真人批准栏。详见 [required_slots.csv](required_slots.csv)。
- [draft_reconciliation.csv](draft_reconciliation.csv) 映射59条原始活跃草案、未运行的Q1/Q2、8个PROMPT_COMMON槽位和1个PROMPT_DELIVERY槽位；不把新增槽位伪称为原始59条之一。
- 固定参考涉及人VEGFA `NM_003376.6`及固定FASTA SHA256 `30059fb1290f94692a1b0eeef85a7d992d6e34b8940395d390202bcf71d9c706`。19nt核心坐标与23nt设计窗口分开；链角色若只来自用户的计算假设，就明确标注为假设而非供应商确认。表达数据是未转染基线背景，不是敲低真值。模型分数不是敲低百分比；seed命中不是实测脱靶。
- 允许合理的证据支持型替代解释；不以程序当前排名定义生物学最佳答案。没有湿实验数据时，不指定某条siRNA必须最有效。
- 135条标准都是回顾性AI草案，`human_approved_before_real_run`为空。不能声称真人在原运行前批准。

## 3. 统一的评价范围

**主评价对象**：每一轮实际交付的最终 `answer` 正文 + 原始运行清单明确列出的可访问业务报告/数据附件。附件可以补足正文没有展开的精确字段，但不能消除正文与附件之间的实质矛盾。

**仅作诊断、不代替主答复**：内部 `raw_model_answer`、模型请求/响应、计划、工具日志。不得用内部原文覆盖用户收到的错误或被拦截答复。无独立raw模型文字的轮次标为不可比较，而不是“与交付不同”。

- 33轮：21轮有独立内部模型文字；其中20轮与交付一致，1轮不同（A013）；12轮没有独立内部模型文字，raw一致性不适用。
- A013：用户交付正文说“模型序列检查未通过”；内部模型原文有正确的0.9915144175887107分数，但不能代替主答复。原始交付清单列有该轮 `score_candidates.json` 与 `verify_target.json`，因此对应槽位可由可访问附件支持；主答复与附件冲突仍使整题FAIL。
- A014：分数附件存在且候选/序列绑定正确；“2025年X月X日”不是有效日期。问题是日期占位符，不是说分数来源文件凭空不存在。
- A002：IRGM来源字段及 `independent_check=PASS`确实存在；答复缺少精确查询定义/序列/坐标/错配数和PASS含义，属于交付披露不足，不是凭空编造来源。
- A023：停止新计算是正确的；但没有回答旧分数是否可迁移、哪些字段可保留、哪些必须重核，因此整题不通过。
- A005/A009/A011/A012/A019/A021/A023/A026/A027等固定流程轮次没有独立raw模型文字；不能据此称其原答“与raw不同”，也不能凭空填充普通模型的规划。
- A011/A025最终文本为共用错误呈现模板；A011模型请求0次、A025模型请求6次。R4系统交付可以按任务要求通过，但不能把该模板解释归功于模型自主推理。

逐轮范围见 [raw_delivery_scope.csv](raw_delivery_scope.csv)；三组映射单独保存于 [group_map.csv](group_map.csv)，本轮知道组别，**不称独立盲评**。

## 4. 27份答复和405条槽位判断

- 原始答复：27份；实际轮次：33；每组9个任务单元。U1/R1的多轮分别逐轮检查，但每组仍按一个任务单元计算，不把轮次当独立题。
- 每个答复的任务结论、必答槽位计数和证据位置见 [task_reviews.csv](task_reviews.csv) 与 [metrics_by_task.csv](metrics_by_task.csv)。
- 逐槽原句/附件字段、提供值、状态、理由、证据位置、是否使用内部raw替代、真人确认状态见 [slot_reviews.csv](slot_reviews.csv)，共405行（135槽位×3组）。
- 状态计数：CORRECT=313；WRONG=13；MISSING=79；UNJUDGED=0；NOT_APPLICABLE=0。**这是AI已逐项判定的数量，不是已获真人确认的数量。** 405条的真人确认时间和裁决者仍为空。
- 逐题必答槽位规则：CORRECT→TP+1；WRONG→FP+1且FN+1；MISSING→FN+1；UNJUDGED不自动填零；NOT_APPLICABLE仅在有依据且三组一致时排除。重复正确内容不重复计数。额外错误另列，并根据其是否使任务结论失效决定整题FAIL，不能只看槽位F1。
- Task accuracy按整题计算：全部必答槽位正确交付、禁止事项未发生、必要证据可定位且无使结论失效的错误才PASS；正确停止是否完成要回到原题干逐题判断。

## 5. 可支持的指标（全部为AI预评审结果）

后三项是必答槽位指标，不是CRISPR-GPT Supplementary Note C1规划指标。Micro按同组全部槽位汇总；Macro为每个任务先计算P/R/F1后再对9个任务取算术平均。

| 组别 | AI预评审Task accuracy | TP | FP | FN | 必答槽位Micro P | Micro R | Micro F1 | Macro P | Macro R | Macro F1 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 普通LLM | 1/9 (11.11%) | 55 | 12 | 80 | 82.09% | 40.74% | 54.46% | 92.22% | 46.67% | 59.78% |
| 固定流程 | 8/9 (88.89%) | 130 | 0 | 5 | 100.00% | 96.30% | 98.11% | 100.00% | 93.06% | 94.95% |
| Agent | 6/9 (66.67%) | 128 | 1 | 7 | 99.22% | 94.81% | 96.97% | 99.07% | 93.52% | 95.37% |

公式：Precision=TP/(TP+FP)；Recall=TP/(TP+FN)；F1=2TP/(2TP+FP+FN)。这里的TP/FP/FN来自必答槽位值交付：错误值同时算FP和FN。整题Task accuracy的分母是每组9个任务，不是135槽位，也不是33轮。

### 按任务类别拆分（AI预评审，Macro必答槽位指标）

| 组别 | 类别 | Task accuracy | Macro P | Macro R | Macro F1 |
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

可复现脚本：[metrics_calculation.py](metrics_calculation.py)。本次重新解析405条逐槽表、27条任务表及组别映射，并重算12行“组别×类别”汇总；所有12行与 `metrics_summary.csv` 数值在1e-9容差内一致。见 [integrity_checks.json](integrity_checks.json)。

### 严格规划四指标为什么未计算

[planning_metrics_status.json](planning_metrics_status.json) 状态为 `NOT_READY`。缺少有限动作全集、真人批准的gold-selected标签和普通LLM的对等原始结构化计划。固定流程按预先条件选出的工具清单不是模型生成计划；普通LLM没有工具调用也不能填成“计划全错”。不能用事后补写的计划伪造CRISPR-GPT C1的Accuracy/Precision/Recall/F1。

## 6. 关键错误、停止与缺口

- **A013**：最终主答复的误拦截提示与可访问附件冲突；不能用内部正确模型原文替换用户实际收到的结果。任务FAIL，但附件支持的槽位可记正确。
- **A014**：占位日期使来源追溯不合格；分数本身与序列绑定正确。
- **A020**：把23nt设计窗口起点当成19nt核心起点；正确核心坐标应按固定参考核对（例如3499窗口对应3501–3519核心）。
- **A006**：输入中确有 `independent_check=PASS`；错误是将序列核查标记解释为“无脱靶证据/风险”，忽略其“未证明脱靶”的限定。
- **A002**：来源字段存在，不是编造；但关键近匹配细节没有在实际交付中展开。
- **A023**：停止无效计算正确，但没有回答旧分数不可迁移及可保留/需重核的证据清单，故整题FAIL。
- **A003/A015/A016/A018/A024**：分别存在边界正确但未交付可做的局部核查，或必答信息缺失；不因没有工具调用自动称为胡编。
- **A022**：主结论“声明坐标越过3609nt参考末端”正确；附加解释把19nt闭区间说成长度不足是错误，另列为不影响主结论的额外错误。
- **A008**：不能沿用旧分数的主结论正确，来源归因有误。
- **A010**：多问了一句是否启动新评分，但实际没有启动，不当作已执行的越界操作。
- **A011/A025**：共用模板的系统交付保留了局部证据与缺项；不能把模板解释归功于Agent自主推理。

完整额外错误与证据缺口见 [extra_errors_and_gaps.csv](extra_errors_and_gaps.csv)；需真人优先裁决的项目见 [pending_adjudications.csv](pending_adjudications.csv)。

## 7. 审计v3之后的远端提交：已读取并对齐，不覆盖

本次审计目录写入后，远端又出现三个提交，按提交顺序已读取：
- `e02708125b91dd8cdcb63f64f0a0c80725689db7`：后续实现、独立复核与证据；
- `601431d008106b8f11d75fa02f244d147c2d2a43`：合并远端v3审计与实现提交，保留双方父提交；
- `fe5b43c0d7f2c759b3a2e324f2b9589d81f7cb9e`：记录最新证据读回与v3对齐。

已读取后续执行README/交付收据、`latest_v3_alignment.json`、`raw_comparison_status_v3.csv`、`original_integrity.json`、`independent_matched_mapping/run.json`及逐候选表、seed对照、`consistency/summary.json`、官方分数来源检查、评审范围附页、给原评分者的短核对单，以及最新WORKBOARD/STATUS。对齐记录明确135标准、405标签、27个任务结论和12行汇总没有被后续实现改变。

已完成但不能过度解读的工程/独立代码路径检查：
- **Seed精确匹配复核**：保存的运行记录为10条guide、固定代表性UTR集合19,415条，位点/转录本/基因计数与原官方明细差异均为0。默认九条按原任务guide输入核对，既购候选按原19nt核心；方向、重叠和边界控制有单独记录。这是同定义下的计数实现复核，不是实测脱靶真值。
- **原始TPM逐样本复算**：从公司原始8列TPM、固定阈值TPM≥1且至少2/4皿及指定静态映射重新计算，10条候选的逐基因和检出集合与同版基线表差异为0。首次使用不同静态映射的运行曾出现35条候选-基因差异和100条集合成员差异，已完整保留；同版映射复算的一致性不证明该映射是独立生物学真值。
- **来源与计数一致性**：工具记录层34 PASS/266 UNCHECKABLE，交付正文层12 PASS/288 UNCHECKABLE；不完整/非标准化文本标UNCHECKABLE，不当成错答。构造正负控制与真实27答复分开。
- **OligoFormer来源**：原始批次确有新旧候选绑定的历史分数记录，但该批实际调用评分的候选仅为既购siVEGF、VEGFA_SD_3499和VEGFA_SD_3535；10条来源表的其他分数不是本次运行新推断。后续未做OligoFormer独立推断。
- **A013**：新代码离线回放从旧误拦FAIL变为新显示PASS；这是后续工程回归，不替换原始A013用户交付，也不回填原任务成绩。

后续提交记录为0新真实模型调用、0新真人评分、0新OligoFormer推断；未合main、未部署生产网站。它们不补足原运行前真人批准、独立盲评、严格C1所需对等计划、独立未见测试或湿实验真值。

## 8. 结论与边界

在这9个已见开发任务上，固定流程整题通过数最高（8/9），Agent为6/9，普通LLM为1/9。固定流程的必答槽位Micro F1为98.11%，Agent为96.97%；Agent Macro F1为95.37%，略高于固定流程的94.95%。不同汇总口径的次序不同，**不能宣称Agent全面胜出**。工具组相对无工具LLM的差别不能单独归因于模型本体；固定流程同样胜出且应保留。A013误拦截、A014占位日期、A002证据披露不足是Agent侧明确问题，A020坐标混淆是普通LLM侧明确问题。

这些是9个已见开发任务的回顾性AI预评审，不是未见测试、独立盲评、一般科研判断力证明，也不是生物学效力/安全性证明。原0–2专家分数未作为真假标签，未被修改；真人批准/裁决仍待完成。

## 文件索引

- [required_slots.csv](required_slots.csv)：135条完整原子标准和证据。
- [slot_reviews.csv](slot_reviews.csv)：405条逐槽核对。
- [task_reviews.csv](task_reviews.csv)：27份答复的整题AI预评审。
- [metrics_by_task.csv](metrics_by_task.csv)：逐题TP/FP/FN和P/R/F1。
- [metrics_summary.csv](metrics_summary.csv)：整体与分类指标。
- [metrics_status.json](metrics_status.json)：机器可读指标状态及分母。
- [planning_metrics_status.json](planning_metrics_status.json)：严格规划指标缺口。
- [raw_delivery_scope.csv](raw_delivery_scope.csv)：33轮正文、内部原文、附件范围与原文一致性。
- [group_map.csv](group_map.csv)：组别映射，明确非盲评。
- [draft_reconciliation.csv](draft_reconciliation.csv)：草案复合项拆分与额外题干要求映射。
- [extra_errors_and_gaps.csv](extra_errors_and_gaps.csv)：额外错误与证据缺口。
- [pending_adjudications.csv](pending_adjudications.csv)：真人需优先裁决项目。
- [POST_REVIEW_INTEGRITY_AUDIT.md](POST_REVIEW_INTEGRITY_AUDIT.md)：本次审计发现与修订日志。
