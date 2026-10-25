# 来源与用途

所用main：`7de40bd5e03c313d3cc387cbfdbb417e3646c439`。源文件均与Git blob核对；PNG原截图未改像素。

图01/02是保存记录的英文精简重排，图03/04/05从完整底表绘图；没有新增模型请求或科学工具运行。
图01的正确序列取自工具字段，原模型24位错误保留说明。图02是原中文问答的译文摘录，S1项目说明不冒充外部论文。
图03只复用旧表中已完成的分数与seed字段，不沿用旧表NOT_RUN近全长状态；全量近全长结果以图04所用新表为准。
图03不再沿用旧图注中的“只有24项近全长完成”这一历史状态。
图04保留固定参考与条件；四种查询互相重叠，23条是候选并集。原始末端18位边缘匹配保留在历史证据，不影响本图两面板。
图05来自八个原TPM点，仅画均值、不增加显著性检验。图08为旧版案例，不与新案例混算用量或候选。

## 图册逐页说明

### 图01：01_agent_case_compact.pdf
- 这是什么：一条既购双链的真实运行，按确认计划完成六步核查。
- 要说明什么：Agent 能否把序列、已有计算结果和表达背景接起来？
- 得到什么结论：流程跑通并保存报告；8次模型请求对应1个案例。
- 边界：分数和 seed 为本地结果导入；原答有19位错写24位，不能称回答全对。

### 图02：02_literature_evidence_compact.pdf
- 这是什么：B02 的真实问题、实际传入的原文/源码和回答摘录。
- 要说明什么：模型是否真正取得来源，并按来源解释专业概念？
- 得到什么结论：这一次问答正确区分模型分数与实测敲低率，引用可核对。
- 边界：单题演示不代表总体准确率；项目说明不是外部论文结果。

### 图03：03_candidate_results.pdf
- 这是什么：全部65条设计的模型/seed结果，既购序列单列。
- 要说明什么：候选有无来源？是否只挑了少数高分结果展示？
- 得到什么结论：完整池均有计算结果；各候选的分数与匹配注释存在差异。
- 边界：9条是历史子集；高分不等于高实测效力；seed匹配不等于实验脱靶。

### 图04：04_nearfull_results.pdf
- 这是什么：两条链各按1–19、2–20位比对，共264项查询。
- 要说明什么：所有候选是否都检查？是否有接近全长的非靶匹配？
- 得到什么结论：264项查询完成；65条中23条有0/1错配非靶匹配。
- 边界：10、7、10、9不可相加成独立候选数；其余42条不能据此称安全。

### 图05：05_vegfa_baseline.pdf
- 这是什么：同批ARPE-19常氧/缺氧各4皿，均未转染。
- 要说明什么：自己的RNA-seq能为课题提供什么直接背景证据？
- 得到什么结论：该批次VEGFA均值为20.10与102.39 TPM，比值约5.09。
- 边界：仅描述这批样本；不是4轮独立培养、siRNA敲低效果或状态风险重排序。

### 图06：06_real_website.png
- 这是什么：真实网站完成既购序列核查后的截图。
- 要说明什么：系统是否具有实际可操作的网页入口与结果界面？
- 得到什么结论：该案例确实在原网站完成；界面可展示运行记录和结果。
- 边界：完成状态不等于回答全部正确；原序列错误仍需同时说明。

### 图07：07_local_retrieval.png
- 这是什么：本地小型文献库检索后显示来源片段的截图。
- 要说明什么：用户能否检索资料，并看到命中的来源内容？
- 得到什么结论：本地检索和来源片段展示已有实际入口。
- 边界：此截图不能单独证明模型读过来源；真实模型问答证据请用图02。

### 图08：08_historical_auto.png
- 这是什么：旧版Agent执行记录与原九条候选结果的组合图。
- 要说明什么：项目早期是否已有完整运行？前后版本如何区分？
- 得到什么结论：旧版曾完成六工具案例，但使用的是另一批输入。
- 边界：旧候选优先级不代表最新65条最佳；当时完整规划用量缺失，不能拿来比成本。

### 图09：09_original_agent.pdf
- 这是什么：Codex交付的未精简版既购案例证据图。
- 要说明什么：精简图中的细节能否回到完整记录？
- 得到什么结论：版本、时间、结果与错误均有完整说明。
- 边界：与图01是同一个案例，不作为新增样本或新模型回答。

### 图10：10_original_literature.pdf
- 这是什么：Codex交付的未精简版B02证据图。
- 要说明什么：图02省略的文字与来源说明能否查到？
- 得到什么结论：全文摘录、代码、项目说明和回答引用均可追溯。
- 边界：与图02是同一道题，不增加独立题数，也不是专家评分。

## 精确原件路径

- `research/2026-10-24_nearfull_complete/live/conversation_export_original.json`
- `research/2026-10-24_nearfull_complete/live/tool_export/score_candidates.json`
- `research/2026-10-24_nearfull_complete/live/tool_export/query_expression.json`
- `research/2026-10-24_nearfull_complete/live/tool_export/inspect_candidates.json`
- `research/2026-10-24_nearfull_complete/live/tool_export/plan.json`
- `research/2026-10-24_nearfull_complete/live/tool_export/report.json`
- `research/2026-10-24_nearfull_complete/live/actual_model_call_summary.json`
- `research/2026-10-23_literature/live_20261024/actual_demo/conversation/evidence/ef511585f2734fe999f4f28c.json`
- `research/2026-10-23_literature/live_20261024/actual_demo/conversation/evidence/8adf373e980643189b6f0479.json`
- `research/2026-10-24_candidate_v2/new_65_complete_table.tsv`
- `research/2026-10-24_candidate_v2/purchased_siVEGF_separate.tsv`
- `research/2026-10-24_candidate_v2/all_104_decisions.tsv`
- `research/2026-10-24_nearfull_complete/all_264_summary.tsv`
- `research/2026-10-24_nearfull_complete/figures/source_data.tsv`
- `research/2026-10-20_integrity_arial/paper/data/VEGFA_eight_samples_TPM.tsv`
- `research/2026-10-24_nearfull_complete/live/case_completed.png`
- `research/2026-10-23_literature/offline/local_ui_search.png`
- `research/2026-10-20_integrity_arial/paper/figures/Figure2_real_Auto_case.png`
- `research/2026-10-25_ppt_figures/figures/A_purchased_Agent_case.pdf`
- `research/2026-10-25_ppt_figures/figures/B_literature_answer_evidence.pdf`
