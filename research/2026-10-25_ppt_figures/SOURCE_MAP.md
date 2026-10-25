# 两图的来源、译文和数字对应

所有相对路径以仓库根为起点。`raw_evidence/`中按相同路径保留实际输入原件及附加复核原件；数量以source_manifest.json为准。指纹是原字节SHA256，不用指纹代替科学复核。

## A：既购si-VEGF案例

原目录：`research/2026-10-24_nearfull_complete/live/`；运行号`20261024_121627_1e50c9`；运行代码`03092ef5fbc2af289aaa2b7bc8d57315c050964f`。

| 图中内容 | 原文件和字段 | 处理方式 |
|---|---|---|
| 英文需求摘录 | `conversation_export_original.json`的messages中第一条用户text | 由中文原句节选翻译，译文明确标注；原句要求只核查既购si-VEGF、保留TT/N3、不重跑重型计算 |
| 确认计划 | 同文件`plan.tools`、`plan.completed`和`tool_export/plan.json` | 保留六步及次序；不增加步骤 |
| 8请求、1规划+7执行、39048词元 | `actual_model_call_summary.json`的calls及total_requests/total_tokens | 逐条检查phase和总数；不把请求数称工具数或题数 |
| 模型与参数 | 同summary及原`attempts/*request.json`；规划原请求在conversation的evidence_records | doubao-seed-2-1-pro-260915；thinking disabled、stream false、max_output_tokens 1800；原请求/响应一并保留 |
| M1-M6工具名/状态/耗时 | `conversation_export_original.json`的events，逐个tool_finished；同`tool_export/events.jsonl` | 工具函数名逐字保留；运行方式转为简短英文；耗时取日志seconds，单位秒，并非重型计算耗时 |
| M7为最终回答，没有第7工具 | 同events第7个model_started/model_finished；`attempts/7a372161375c_turn7_request.json`和response.json | 实际时间差21.870299秒，图中显示21.870；最终响应原文保留 |
| 执行时间 | 第1个model_started `12:16:27.220214+00:00`到第7个model_finished `12:17:03.259801+00:00` | UTC，36.039587秒；图中36.040秒，不当作完整人工交互总时长 |
| 计划到执行间隔 | planner_finished `12:14:43.863259+00:00`到上述第1个model_started | 103.356955秒，包含人工确认等待；没有点击时间，不伪称精确人工等待或模型耗时。没有规划器模型起始日志，不补其耗时 |
| 正确19位链核心、原始21位/修饰 | `tool_export/inspect_candidates.json` rows[0]，`tool_export/plan.json` candidates[0] | guide `UUUCUUGUCUUGCUCUAUC`；另一链`GAUAGAGCAAGACAAGAAA`，互补性核对；两行5'→3'只是条件性假设，未获供应商实物链角色确认 |
| 原始TT/N3 | 上述row1/row2字段及`verified_import/.../input_assets.json` | 全部原文在图注和原件中，英文图内只摘要；不猜N3连接位置、完整化学或质检 |
| NM_003376.6、1439–1457、18/20 | `tool_export/verify_target.json`的reference_sha256和rows[0] | 19位核心、1-based闭区间；FASTA SHA256 `30059fb1290f94692a1b0eeef85a7d992d6e34b8940395d390202bcf71d9c706` |
| 1.121934 | `tool_export/score_candidates.json` rows[0].oligoformer_scaled_score=1.121934400320053 | 显示6位小数，非敲低百分比；status=IMPORTED_VERIFIED_LOCAL |
| 3539位点、2839基因 | `tool_export/match_seed.json`和`query_expression.json` candidate_summary[0] | guide、排除VEGFA；位点与去重基因不混用。全部含靶位点3540另在原件 |
| 1595检出、3未映射 | `tool_export/query_expression.json` candidate_summary[0] | 2836可映射基因中的1595符合缺氧至少2/4皿TPM≥1；3个未映射不等于不表达；不作风险重排序 |
| 原答24位错误 | `tool_export/report.json` model_summary和`ANSWER_CORRECTION_ZH.md` | 错串`GAUAGAGCAAGACAAGACAAGAAA`，24位；正确串19位，分别保留；图红字警示，无新模型回答替代 |

OligoFormer/seed所绑定的数据版本为`purchased_sivegf_20261024_v1`，来源提交`9dd8831ebc28a42584ba57f288a314ccb5042b2c`，原DOCX指纹`7ce4e3cffbe91c62c81926edcc52f53f97fc57c8941085367166068f9b9c3db6`。包内manifest列出原计算文件指纹，seed原sessionInfo为R 4.3.1、Biostrings 2.70.1。本批未运行这些科学工具。完整历史科学计算原件仍在原目录，不把图表排版算成复算。

## B：文献问答

原目录：`research/2026-10-23_literature/live_20261024/actual_demo/`。真实运行、代码、文库完整版本见evidence_checks.json和英文图注。

- 问题/回答：`results.json`中id=B02；问答证据：`conversation/evidence/ef511585f2734fe999f4f28c.json`。
- 实际模型请求/响应：`conversation/evidence/8adf373e980643189b6f0479.json`；解析`request.input[0].content[0].text`内JSON，逐一核对6份retrieved_excerpts的citation_id和text均与问答证据一致。
- 完整原件在`library.zip`；原代码及文章字节SHA256与检索来源声明一致。保留全部S1-S6，不只保存图上成功引用。

| 编号 | 实际来源类别/定位 | 本图使用 |
|---|---|---|
| S1 | project_setting；knowledge#score，无PDF页 | 项目设置原句“模型分数不是实验敲低百分比”的英文翻译；不是论文结论 |
| S2 | official_source_code；text-c007；原文本字符9354–11035 | `Y_PRED = [i*1.341 for i in Y_PRED]`与`RESULT['efficacy'] = Y_PRED`逐字摘录 |
| S3 | article_full_text；text-c020；原文本字符28983–30781 | 原句“The output of the model represents a prediction score for each siRNA, reflecting its potential effectiveness in inducing gene knockdown.”，在保存全文字符30046–30182，0起点、右开区间 |
| S4 | article_full_text；text-c001；字符0–1693 | 未单独摘录于图，随全部原件保留；不将其摘要性能数值用作本系统结果 |
| S5 | official_source_code；text-c011；字符15538–17304 | 原回答的缩放说明引用S2/S5；两片段均含同一缩放语句；保留完整来源 |
| S6 | official_documentation；text-c001；字符0–1761 | 未摘录于图，保留完整官方README片段 |

源码：`https://github.com/lulab/OligoFormer/blob/e2f53ad63387bbe166bf123949151e2bc9bf6ec3/scripts/infer.py`；导出文库原件`originals/ec77cffdc9e76e478068430f.txt`，缩放语句在第252及385行。文章：[OligoFormer原文文字](https://pmc.ncbi.nlm.nih.gov/articles/PMC11494384/)，DOI 10.1093/bioinformatics/btae577；导出文库`originals/e2cea21b6712b85250758e8b.txt`。这些是文字片段，不能添加PDF页码；源文件指纹和定位见B02_original_source_locators.json。

图中回答翻译的三处分别对应原答：

1. “分数超过1不能解释为超过100%敲低率”，引用S1/S3 → “A score above 1 cannot mean more than 100% knockdown. [S1, S3]”。
2. “官方推理源码还显示输出经过线性缩放”，引用S2/S5 → “The output is linearly scaled by 1.341. [S2, S5]”。
3. “不能据此反推出某一具体分数对应的实际敲低百分比” → “These snippets do not establish a measured knockdown percentage for a specific score.”。

这不是逐字重写全部回答，而是有标记的译文摘录。原文和raw_model_answer均未改；原问答1次模型调用、6232词元，仅指B02，不是服务启动或部署总用量。引用编号正确不等于自动完成全部语义质量评分，仍待科研复核。

## 元素级索引

两个`figures/*_elements.json`逐项记录图上文字、坐标、字体和来源；完整原句、数值及检查断言见脚本和evidence_checks.json。显示的四舍五入有明确原值，不补缺失时间、实验值或人工评分。
