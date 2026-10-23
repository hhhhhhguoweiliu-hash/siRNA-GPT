# 命令、环境与记录边界

## 历史上实际留下的证据

原脚本、输入、输出、标准输出、失败日志与版本表均在`historical_evidence.zip`，旧环境列表另在`prior_package_records.zip`。最初调用脚本的完整终端命令、外层工作目录、进程退出码没有找到；不把下面按脚本重建的命令冒充历史捕获。`00_admin/tool_runs.csv`是工具执行概要，不含完整命令。

- siDirect：`run_sidirect_public.py`、`sidirect_raw/*request.json`和`*response.html`、`sidirect_run.log`、`sidirect.log`、`sidirect_retry.log`。后两份是早期缺bs4的失败，保留。
- 筛选：`parse_sidirect.py`、`parse_sidirect.log`、`prepared/candidates_all.tsv`、`candidates_working_pool.tsv`。
- OligoFormer：`run_oligo_cpu.py`、`oligo_raw/run_manifest.json`、`oligo_cpu_validated.log`、`oligo_cpu_retry.log`和失败的`oligo_cpu.log`；旧pip版本表含Python3.8环境依赖。官方RNA-FM主要下载端返回403，随后使用OligoFormer原README列出的作者压缩包获取权重；两段收据均保存，不把第一次下载失败删掉。
- SeedMatchR：`run_seed_and_search.R`、`risk_scan.log`、`risk_raw/sessionInfo.txt`和两份status；官方核心函数直接source，完整包未安装。

## 仅用于以后重建的命令示意（本轮没有执行）

在新的副本中保留原目录关系，Python脚本按自身位置定位文件；R脚本的`analysis/ARPE19_candidates_20261016`相对于旧项目根目录。不要在历史源目录执行会覆盖输出的脚本。先另建复算副本、把写入目录改为新目录，并记录这种路径适配，之后才可考虑：

```powershell
# 以下是重建示意；省略号代表须核验的环境路径，不能直接当成已执行命令。
& '...\Python_with_bs4_Biopython\python.exe' '...\run_sidirect_public.py'
& '...\Python_with_pandas_bs4_Biopython\python.exe' '...\parse_sidirect.py'
& '...\oligo_env\Scripts\python.exe' '...\run_oligo_cpu.py'
& '...\R-4.3.1\bin\Rscript.exe' '...\run_seed_and_search.R'
```

其中原R脚本在seed计算之后还执行全RefSeq近似互补补充扫描；它不是最小seed复算入口。未来需要复算时应单独保存路径适配及执行范围，不能为了得到seed表而未经说明重跑额外模块。当前关键证据已足够互相核对，本轮没有运行以上重型脚本，也没有重新提交siDirect设计请求。

## 本轮实际运行的检查

工作目录：`C:\00000\ARPE RNA-seq\sirna-gpt`。实际检查用Python3.10.11（`C:\Users\86182\Documents\Codex\python310\python.exe`），不是旧模型环境。工具调用和结果见[EXECUTION.md](EXECUTION.md)。便携复核只需Python标准库：

```powershell
python research/2026-10-23_candidate_provenance/audit_candidates.py
```

该命令从本次证据ZIP核对文件、104→9规则、所有九条输入、保存分数、72块seed计数及46867个位点；使用未修改的官方轻量序列标记函数，不加载模型、不联网、不写历史数据。默认更新本目录审计表和审计JSON，其时间属于本次核查。

首次打包和本地第二副本核查的实际命令：

```powershell
python research/2026-10-23_candidate_provenance/audit_candidates.py --source-root C:\Users\86182\.codex\.chatgpt-projects\g-p-6a82e08661e081919f3434650ae4f35c\analysis\ARPE19_candidates_20261016
python research/2026-10-23_candidate_provenance/crosscheck_local_sources.py --project-root C:\Users\86182\.codex\.chatgpt-projects\g-p-6a82e08661e081919f3434650ae4f35c
python research/2026-10-23_candidate_provenance/check_official_sources.py
```

最后一条只从固定官方公开地址下载小型源码/旧版CRAN压缩包。不会下载大模型、安装包、调用模型API或改变网站配置。权重已经在本地核对SHA256，不重复下载；字节校验结果保存在`external_assets_check.json`。
