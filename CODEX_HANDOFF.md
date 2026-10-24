# Codex 接手入口

**2026-10-23更新：**用户已放弃状态相关风险重排序，当前是小而完整的siRNA辅助Agent工具/应用文章；不做微调、不扩大湿实验，TPM只注释。先读[最新范围与A/B任务](docs/reviews/20261023_2116_fast_paper_scope_and_codex_tasks.md)。A的[候选来源核查已交](research/2026-10-23_candidate_provenance/README.md)，含真实104→9、版本、全量旧结果与缺项；B文献库已实现、部署并完成最小两题演示（未独立科学评分），[上传、部署、真实演示状态单独记录](research/2026-10-23_literature/DELIVERY.md)。旧54条已保存，不按下面历史说明再启批消错，联系评审稍后讨论。下面是历史背景，不把旧风险路线或湿实验扩张当成当前必做项。

新对话协作先看[COLLABORATION.md](COLLABORATION.md)和[共同任务表](docs/WORKBOARD.md)。两个新对话共用GitHub事实记录；Codex维护代码与状态，ChatGPT在docs/reviews/写独立复核。

更新：2026-10-20，北京时间。用户希望得到可用、可评价、可毕业的最小完整课题，先跑通真实流程，再逐步补强。用简单中文沟通，优先执行已经授权的可逆工作，遇到真实账号/资源/实验障碍再明确列出用户要做什么。

## 先读这些

**当前优先：[按CRISPR-GPT迁移并取得首批结果](docs/PAPER_MIGRATION_FAST_TRACK.md)**，先读[原文资料](references/CRISPR-GPT/README.md)。不把专用微调、全工具复现或扩大湿实验作为第一批结果的门槛。当前Git含原文可提取文本；PDF字节下载失败，未提交原PDF，详见来源说明。

1. [AGENTS.md](AGENTS.md)：执行约束。
2. [课题全貌](docs/PROJECT.md)：研究目的、证据链、完成标准。
3. [当前状态](docs/STATUS.md)：已完成与尚未完成的事实。
4. [任务清单](docs/TASKS.md)：按优先级推进，含验收方式。
5. [数据来源](docs/DATA_PROVENANCE.md)：默认9候选、真实RNA-seq、模型与参考的来源。
6. [已有结果目录](research/README.md)：10幅原型/背景图、3幅运行诊断图、54条评价原始结果与核查。
7. [参考文献对齐](REFERENCE_ALIGNMENT.md)、[科学边界](SCIENTIFIC_SCOPE.md)、[三组评价](DEVELOPMENT_PILOT.md)。

## 30秒理解当前项目

这是“缺氧RPE / VEGFA siRNA候选核对与筛选辅助Agent”。CNV作为背景，不声称已经验证疾病治疗效果。使用豆包API理解需求、规划并调用工具；确定性程序核对序列、读取已有官方模型结果、关联自有常氧/缺氧表达数据并输出证据。三种交互为自动规划、逐步引导和问答。当前不训练Transformer，也没有完成专用模型微调。

网页：https://sirna-gpt.onrender.com 。仓库为用户私有仓库 hhhhhhguoweiliu-hash/siRNA-GPT。

## 最近最关键的情况

- 当前云端评分和seed分析读取10月16日已有结果；先核对候选ID/序列/模型上下文一致性。不是对任意新序列重新推理。
- 默认9条是siDirect计算候选，不是用户实际有效的文献siRNA，不是订购清单。用户已经做过实验并信任其文献siRNA；需要取得准确序列/来源后接入，不能用默认池代替。
- 自有ARPE-19基线确实包含TPM。网页使用此前整理后打包的数据，不会自动读取用户电脑。TPM用于表达注释，不进入OligoFormer、不改变默认排名。
- 2026-10-19真实三组开发批次有54条记录，但普通LLM和Agent的36条全部受SetLimitExceeded账号用量上限阻断；没有科学工具执行，不能解释为模型能力差。固定流程6完整、3局部、9输入停止。
- 已修复账号级限额不重试、首次阻断后停止批次并导出、错误耗时与结构化诊断保留、缺失token不当0。相关代码基线提交：790c0b48bdba6330f487e473f5e7094afcee587c，121项Python检查和CI通过。此次交接提交会增加文档、现有适配器和研究产物。
- 最近成功检测过网页搜索与PubMed，但账号限额后来影响模型。接手时重新查当前状态；不要断言10月20日仍处于同一状态，也不要循环消耗API来探测。

## 立即开始

在仓库根目录运行（不调用模型API）：

```powershell
python -m unittest discover -v
node test_browser_backup.cjs
python evaluate.py --cases evaluation_cases.example.json --output evaluation_runs/new_workflow_check --group workflow --repeats 1
```

首次可先运行 `python scripts/inspect_research_results.py` 查看交接产物校验和真实状态。然后按TASKS推进。不要启动一个全新的重复网站、换框架、重写脱靶算法或先大规模跑付费任务。

密钥配置用环境变量；现有Render环境已配置，仓库无真实密钥和网站密码。需要本地配置时由用户在本地提供，不让用户把密钥再贴进聊天/提交记录。启动本地网页：`python app.py --port 8765`；云端使用 `cloud:application`，单worker。

## 团队分工与反馈

Codex负责代码、环境、官方工具接入、运行与可复查导出；当前科研讨论负责研究设计和解释；用户负责真实实验、文献候选、账号与费用决定、联系导师/评审。软件自测不能替代独立专家或湿实验。

每次交付说明：改了什么、真实运行了什么、未运行什么、结果在哪里、下一步用户只需做什么。把长期事实更新进docs/STATUS.md和docs/DECISIONS.md。保留失败批次，不悄悄重写历史、挑成功记录或把开发例子包装成独立测试。
