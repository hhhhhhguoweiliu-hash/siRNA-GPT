# 两个新对话的共同任务表

初始化：2026-10-20，北京时间。接手基线：`4dfca18c9117f29dda5bec7df83f0843cdc5305c`。该基线CI成功；本文件的提交会成为更晚的接手版本。请实际读取最新head，不把这个旧SHA当永远固定。

Codex统一维护本表，ChatGPT在docs/reviews/提交独立复核。已有详细事实见[STATUS](STATUS.md)，研究路线见[PAPER_MIGRATION_FAST_TRACK](PAPER_MIGRATION_FAST_TRACK.md)。本表状态不是自动任务调度，也不表示新对话已开始运行。

| ID | 负责人 | 当前状态 | 下一步与完成证据 |
|---|---|---|---|
| C01 | Codex | 已完成本地复现 | 接手e1f0443；37文件校验通过；新6题固定流程2完整/1局部/3输入停止；9候选表逐行一致；10图重绘。产物research/2026-10-20_takeover |
| R01 | ChatGPT | 已提交并读取 | e53bacb新增docs/reviews/20261020_1435_initial_review.md；两项必要修复已落实于bd41679，详见本轮验收 |
| C02 | Codex | 线上已有效；本地单独失败 | 本地一次403/AccessDenied已停；线上显示工具回传已验证并实际完成Auto，不混同两套凭证；未修改密钥/额度 |
| C03 | Codex | 已完成并校验归档 | 线上e53bacb，run 20261020_064921_2dae59，6科学工具；会话49801字节，29文件ZIP 434351字节，CRC通过；历史导入标识保留 |
| C04 | Codex；既有网页用量确认 | 新批次运行中，52/54已记录 | dev_20261020_070207_843de3，通过网页勾选确认启动；全部关闭外网。运行期间不部署/重启；结束后立即保存原包 |
| R02 | ChatGPT；独立评审另需真人 | 依赖C03/C04 | 复核证据与组间公平性，输出必要修正；ChatGPT复核不能代替独立专家评分 |
| C05 | Codex | 离线表图已交；等待新批次 | 已有audit_summary.json、workflow_summary.tsv及10幅重绘图；新三组结束后导出状态/延迟/usage/调用，不代填科学评分 |
| U01 | 用户提供，Codex导入 | 尚缺准确文献序列/来源 | 填inputs/literature_candidates.template.tsv；记录链方向/末端/来源，不用默认9条代替 |

## 当前可立即复用

- [10幅原型/背景图、3幅运行诊断图及底层数据](../research/README.md)。
- [原文可读文本、出处和读取边界](../references/CRISPR-GPT/README.md)。
- [现有三组开发预评估说明](../DEVELOPMENT_PILOT.md)。
- 旧54条批次：普通LLM18/Agent18为账号限额阻断，Agent科学工具调用0；固定流程6完整、3局部、9输入停止。旧批不承担三组优越性证据。

## 每批完成后补充

时间（北京时间）、负责人、实际commit/分支、完成ID、产物路径、真实执行与验证、未执行部分、阻断及用户只需做的一步。更新状态不覆盖历史原始数据；本表保持简短，详细过程落到新运行目录或复核文件。

### 2026-10-20 本批进度

Codex分支`codex/20261020-evidence-pilot`；接手`e1f044397ea60d4133d3b8e58a1501c6904d14c4`，已合入科研复核`e53bacb`。代码修复`bd41679`；124项Python检查、Node前端检查通过。Windows隔离Python的临时目录问题通过在工作区运行测试解决，原错误和纠正命令均保留。当前代码修复仍在任务分支，不宣称已部署。线上真实Auto及新批次使用e53bacb；不在批次中途改变模型或工具版本。

后续新增规划轮usage保留回归，最终125项Python及Node检查通过。线上e53bacb会清除ready计划的planner事件，故本批及Auto完整token总量可能未知，只交已知小计；本地已修复。完整Auto原文与工具包已校验，新批原包待结束后下载。详细命令、失败记录与范围见research/2026-10-20_takeover/README.md。
