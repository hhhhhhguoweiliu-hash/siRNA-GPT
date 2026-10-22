# 2026-10-20 接手、复现与真实运行

接手main：`e1f044397ea60d4133d3b8e58a1501c6904d14c4`。线上Auto及本批三组的实际版本：`e53bacba981a9082fad4df57c600eb93de159dc8`。本地修复在`codex/20261020-evidence-pilot`，不把分支提交说成已部署。

## 已完成

- `audit_summary.json`：37项历史文件SHA256、旧54唯一ID/完整6×3×3/协议顺序、6项科学数据资产一致性验证。旧36条模型账号阻断保持原样。
- `candidate_report/`：本次无API固定流程报告，9条候选表逐行与交接底表一致，优先复核3499/3500。不是文献候选或订购单。
- `workflow_check/`：新6任务各1次，2完整/1局部/3异常输入停止。原始结果、逐条记录、协议、空白评审表及独立的组别密钥均保留。不是三组批次的一部分。
- `figures/`：10幅既有背景/工程图重新生成PNG/SVG/PDF；3幅旧审计SVG为原件复制。图8–9仍描述10月19日18次本地运行，不能冒充今天的新批次。图注见`figure_captions.json`，原始底表在`../2026-10-19_scientific/data/`。
- `model_connection.json`：本地一次403/AccessDenied后停止；不能据此断言线上服务失败。
- `model_connection_online.json`：线上真实两轮工具回传检测已通过，2026-10-20 14:45:25（北京时间），PubMed和网页搜索检测成功。本轮案例及三组关闭外部联网；检测工具可用不等于本轮调用了检索。
- `auto_case/`：真实模型规划与执行，run `20261020_064921_2dae59`。会话原文、6项工具返回、29文件工具ZIP、7轮执行器请求/对话/usage、候选表及报告均已导出。两个重型工具为历史导入，表达关联为实时基线连接；未执行新的重型模型/R推理。

## 用量和评价边界

Auto执行器返回7轮usage，共59,767 tokens，是已知小计。线上版本在新计划建立时清掉规划轮事件，完整总量未知；不补0，不估货币费用。该缺口已在本地修复，本批运行期间不部署修改版本。三组汇总也应识别此类遗漏，不把导出中残留的数字当完整总成本。

Auto原文的seed匹配数778/1548是匹配记录数，候选表中的728/1333是去重非靶基因数，不能混同。原始模型回答保留不重写，独立科研复核另行进行。没有人工科学准确率或独立评分。

`development_anchors.json`转录批次开始前已存在于e53bacb科研复核中的6题锚点。正常两题的top_n分别为2和3，名单长度差不是状态改变排名。3次是技术重复，只有6道开发题。

## 修复与软件验证

已修复CLI遇账号阻断继续请求、成功响应缺usage误填0、超时记录丢失、普通LLM缺原始请求/响应、规划轮usage被清除；两入口增加全部计划单元状态导出。生产启动检查、手动确认、密钥、额度均未改变。

首轮默认临时目录存在沙箱写权限错误；将测试临时目录置于工作区后121项基线检查通过。后续新增针对性回归检查，最终检查日志见`tests-final-125.txt`；这些检查数不是科研样本量。`tests-targeted.txt`记录隔离Python未加入当前路径的导入错误，纠正后`tests-targeted-corrected.txt`通过；失败日志未删。

## 实际命令

在仓库根目录：

```powershell
python scripts/inspect_research_results.py
python scripts/rebuild_candidate_report.py --output research/2026-10-20_takeover/candidate_report
python evaluate.py --cases evaluation_cases.example.json --output research/2026-10-20_takeover/workflow_check --group workflow --repeats 1
python scripts/audit_takeover_results.py --batch research/2026-10-20_takeover
```

以上为实际使用目录，复跑生成命令时须换成新的空目录。当前Windows embeddable Python可用以下检查命令（不改生产环境变量）：

```powershell
python -c "import tempfile,pathlib,unittest,sys; tempfile.tempdir=str(pathlib.Path('.test_tmp').resolve()); r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.discover('.')); sys.exit(not r.wasSuccessful())"
node test_browser_backup.cjs
```

绘图依赖仅安装在本地`.plot_deps`；直接依赖见`requirements-research.txt`，实际全量版本见`plot-dependencies.txt`。复现命令：

```powershell
python -m pip install --target .plot_deps --only-binary=:all: -r requirements-research.txt
python -c "import sys,runpy; sys.path.insert(0,'.plot_deps'); runpy.run_path('scripts/plot_research_results.py',run_name='__main__')" --output research/new_rebuilt_figures
```

真实Auto经现有网页输入需求→模型计划→按计划开始执行；三组经现有网页勾选用量确认→启动本次预评估。没有通过启动脚本或环境变量自动起批。

## 新三组真实批次：已运行，仍不足完整质量比较

批次`dev_20261020_070207_843de3`，北京时间15:02:07–15:20:50；`three_arm_original.zip`为逐字节原包，5,028,649字节、459个文件，SHA256及CRC见下载收据。54条唯一ID、协议顺序、6题×3组×3次和逐条/汇总一致性通过，Agent18个会话ID独立；协议关闭外部联网。未把昨日失败或本地固定流程拼进本批。

| 组 | 本批实际状态 |
|---|---|
| 普通LLM | 12条ANSWERED_NO_TOOLS；6条OUTPUT_TRUNCATED，没有完整可用回答 |
| 固定流程 | 6完整、3局部核对、9异常输入停止 |
| Agent | 4完整、3局部、8 idle；3失败含2网络与1计划格式失败 |

这不是54条全有效配对：18个题目重复单元中12个无API异常；`normal_hypoxia`为0/3，`normal_normoxia`为1/3、`target_only`为2/3。其余异常任务各3/3仍需人工评其停止/澄清是否正确。只有6道已见开发题，不是18道独立题，不能作泛化或显著性结论。完整Agent的4份正常报告和3份target_only证据范围检查通过；这是工具覆盖/条件核查，不是科学准确率。

`three_arm/`提供原始results.json.gz、54行records.tsv、execution_status.tsv、配对可用性、failure_diagnostics.tsv、7份完成Agent的证据范围核查、group_summary.tsv和2幅PNG/SVG/PDF诊断图。原始答案与空白评分栏在`for_review/`；`private_key.tsv`单独保存。只给评审for_review及已冻结评分说明，不给原始ZIP/密钥。去掉组名不能保证风格盲法。

已知返回用量小计：普通LLM54,129、Agent241,107 tokens；失败调用缺usage、部分Agent缺规划轮，因此都不是全组总量，不推算货币费用。独立科学分数未填。6次OUTPUT_TRUNCATED没有保留服务端incomplete_details，不能断言确切原因一定为1800输出上限；本地已补充错误原文留存，下一轮先诊断，再冻结统一参数，不自动提高账号额度或覆盖失败。

线上该版本未给普通LLM单独保存请求/响应JSON；12份原始回答和返回usage仍在原包，输入由cases/protocol与当次源码追溯。不能将此包称为所有HTTP字节均已留存。新代码已为后续调用保存请求、正常响应与不完整响应，但不能补造本批丢失内容。

复现本批审计（新空目录）：

```powershell
python -c "import sys,runpy; sys.path.insert(0,'.plot_deps'); runpy.run_path('scripts/summarize_development_batch.py',run_name='__main__')" --archive research/2026-10-20_takeover/three_arm_original.zip --output research/new_batch_audit --plot
python scripts/audit_development_evidence.py --batch research/new_batch_audit
```

审计时修正了两项验收脚本自身的问题：效力与seed步骤可合法交换，按工具集合与依赖检查；原research/README.md受历史manifest固定，已按接手blob逐字节恢复，入口链接只写WORKBOARD/STATUS。原始research证据37项最终再次通过。

126项最终软件检查记录见`tests-final-126.txt`。本批诊断图只展示执行状态/分任务耗时，API异常不混作正常推理耗时；无准确率、优越性或显著性图。
