# siRNA-GPT

面向缺氧RPE / VEGFA的siRNA候选核对与筛选辅助Agent。当前使用豆包API、受控工具流程、已有官方科学计算结果和本项目ARPE-19常氧/缺氧表达背景。

**Codex接手先读：[CODEX_HANDOFF.md](CODEX_HANDOFF.md)**。当前首要路线是**[仿照主参考文献，先出结果](docs/PAPER_MIGRATION_FAST_TRACK.md)**；[原文可读文本与出处](references/CRISPR-GPT/README.md)已补入，再按[任务清单](docs/TASKS.md)处理细节。

| 内容 | 入口 |
|---|---|
| 课题定位、证据链、完成标准 | [docs/PROJECT.md](docs/PROJECT.md) |
| 当前完成与未完成状态 | [docs/STATUS.md](docs/STATUS.md) |
| 数据、候选、工具和参考来源 | [docs/DATA_PROVENANCE.md](docs/DATA_PROVENANCE.md) |
| 参考文献对齐 | [REFERENCE_ALIGNMENT.md](REFERENCE_ALIGNMENT.md) |
| 图、表、原始评价与复现 | [research/README.md](research/README.md) |
| 三组开发评价使用方式 | [DEVELOPMENT_PILOT.md](DEVELOPMENT_PILOT.md) |
| 科学边界与TPM用法 | [SCIENTIFIC_SCOPE.md](SCIENTIFIC_SCOPE.md) |

网站：https://sirna-gpt.onrender.com 。仓库为用户私有仓库；保持现有可见性与服务。

## 当前事实

- 自动规划、逐步引导、问答；PubMed、网页检索/读取、本地说明；工具记录、来源与导出。
- 固定9条候选来自siDirect计算池，未导入用户有效文献siRNA；不是订购单。
- 云端OligoFormer和SeedMatchR读取序列核验后的历史结果。序列/转录本核查、表达关联和报告实际执行；任意新序列的重型现场计算后台尚未接入。
- 自有TPM已用于两状态表达注释，不进入OligoFormer、不改变默认候选排名。
- 2026-10-19的54条开发记录中，36条模型依赖案例受SetLimitExceeded阻断，不能用于三组优劣结论。随后修复账号阻断即停和用量缺失处理。当前账号状态需要重新检测，不自动提高限额。
- 10幅原型/背景图、3幅诊断图及真实数据在research/。未完成正式独立盲评、专用模型微调或新的湿实验。

## 不调用API的检查与复现

```powershell
python -m unittest discover -v
node test_browser_backup.cjs
python scripts/inspect_research_results.py
python scripts/rebuild_candidate_report.py --output evaluation_runs/new_report
```

最近软件基线有121项Python检查及前端检查通过；这是工程验证，不是研究bench样本量。研究图重绘另需numpy、pandas、matplotlib：`python scripts/plot_research_results.py --output figures_rebuilt`。

## 本地与云端

本地轻量界面：`python app.py --port 8765`。配置由ARK_API_KEY、ARK_MODEL等环境变量读取；不要提交config.local.json或真实.env。Render已配置ARK_API_KEY、ARK_MODEL、WEB_PASSWORD。网站Basic登录用户名research，密码由用户单独保管，不在仓库中。

Render当前是免费Python服务；build命令`pip install -r requirements.txt`；start命令`gunicorn cloud:application --bind 0.0.0.0:$PORT --workers 1 --threads 4 --timeout 180 --access-logfile -`。健康端点`/healthz`不表示平台已配置HTTP检查（既有服务可能用默认TCP）。保持单worker；当前内存会话和免费实例文件不保证永久保留。

账号/费用/权限变更由用户明确决定。批量评价需要登录后手动确认API用量，不随部署自动运行。重部署前应保存未导出结果；重跑用新批次，保留历史失败。
