# CRISPR-GPT → 缺氧RPE / VEGFA siRNA课题：第二批可用图和数据

2026-10-20。接手分支 `codex/20261020-evidence-pilot`，起点 `3230670c657036e6fdbbb83adbc9080c82a5cea9`；实际拉取的最新main仍为 `e53bacba981a9082fad4df57c600eb93de159dc8`。`docs/reviews/`只有首轮科研复核，PR #1 的普通和行内评论均为0。本轮没有声称收到尚不存在的新复核。

本批把分散图整理成可用于论文结果组织的4张组合图（10个panel），每张均有PNG、SVG、PDF、中文图注及底表。不是4项新增独立实验；没有新API批次、重型模型推理、评分或湿实验。

## 直接查看

- [下载本轮完整成果包（代码、两批原始证据和最终图表）](delivery/siRNA_GPT_migration_20261020.zip)；[ZIP校验回执](delivery/siRNA_GPT_migration_20261020.receipt.json)。
- [四图及中文图注](paper/index.html)（下载后本地打开）；[GitHub可直接查看的总览](paper/contact_sheet.jpg)。
- [Figure 1：课题系统迁移](paper/figures/Figure1_system_migration.png)：原文交互和工具机制如何落到本课题。
- [Figure 2：真实Auto案例](paper/figures/Figure2_real_Auto_case.png)：7轮执行器API、6个工具的真实时间轴与候选输出。
- [Figure 3：候选与细胞背景](paper/figures/Figure3_candidate_and_cell_context.png)：8皿VEGFA TPM、9候选分数、seed表达注释与两状态对应。
- [Figure 4：开发评价证据](paper/figures/Figure4_development_evidence.png)：54条逐题状态、配对缺口、规划失败和API错误分开显示。
- [底表](paper/data)、[中文图注](paper/figure_captions.json)、[来源及SHA256](paper/provenance.json)、[文件清单](paper/manifest.json)。
- [按原文各图组织的证据对照与当前结果文字](PAPER_RESULTS.md)；[下一批诊断门槛](NEXT_EVALUATION.md)。

## 真实结论

真实Auto的6项工具均留有证据，优先复核3499/3500；这里的重型分数与seed仍为历史官方输出导入。VEGFA基线均值TPM为20.09929925与102.390068，均值比5.09421，限于同批次4+4皿未转染背景，未作配对推断或敲低效应推断。TPM不改变候选排序。

新开发批次54条完整归档，但只有12/18个题目重复单元无基础设施错误，缺氧完整题0/3。另1条规划格式失败是系统失败，不能算正确拒绝。本轮未代替独立评审填分，未生成科学准确率或优越性图。

## 复现与验证

隔离绘图依赖仍为仓库 `requirements-research.txt`；本机已经安装到 `.plot_deps`。Windows embeddable Python需显式将依赖路径加入sys.path：

```powershell
python -c "import sys,runpy; sys.path.insert(0,'.plot_deps'); sys.argv=['scripts/build_migration_figures.py','--output','research/new_migration_figures']; runpy.run_path('scripts/build_migration_figures.py',run_name='__main__')"
python scripts/inspect_research_results.py
node test_browser_backup.cjs
python -c "import sys,tempfile,pathlib,unittest; sys.path.insert(0,'.'); tempfile.tempdir=str(pathlib.Path('.test_tmp').resolve()); r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.discover('.')); sys.exit(not r.wasSuccessful())"
```

绘图程序执行数据断言：54唯一记录及唯一题×组×重复、6项Auto工具、59,767执行器已返回token小计、12个无基础设施错误配对及缺氧0配对。不改写2026-10-19/首批原始数据。`paper/provenance.json`记录绘图脚本SHA256，不能把工作树基点当成所有新代码已经在该commit中。

131项Python检查通过，详见[tests.txt](tests.txt)。新增5项检查覆盖两个入口的参数冻结、密钥排除、Agent规划/执行不完整响应留存、Chat格式截断诊断。初次新增回归因测试读文件使用Windows默认GBK失败，改为显式UTF-8后通过；没有降低产品的文件写入标准。渲染排版/路径问题已修正，本地保留中间渲染，不作为最终图交付。

## 原文读取边界

本次从出版方页面请求原文/勘误，两者HTTP 200均只返回相同的3038字节页面，没有citation metadata或可用正文。见[原始请求诊断](reference_metadata.json)。HTTP 200不等于内容核验通过；本轮原文对照依据已归档抽取文本和e53bacb科研复核，没有声称新取得PDF/补充材料或独立重验勘误。新图全部为本项目重画，不用原Fig.4颜色识别组别。

## 同步与运行状态

本批代码、图、底表、图注与共同任务表同步GitHub PR #1任务分支。无需重复要求“上传”。目前未合入main或部署；线上真实运行证据仍对应e53bacb。下一批实际诊断要用已包含留存修复的版本，不能以本地模拟检查冒充线上诊断成功。
