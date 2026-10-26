# 2026-10-27复核落实：完整开发题包与无模型验收

实际读取复核 `3a557d481c78843c988ba972ff06ceb117aac6f5` 和最新main `2623c8601bd4b19b472fafc520b95c0cfd0a0fdb`，在原分支保留合入，未推main或部署。下列是开发材料及程序验收，不是新模型科学表现、独立测试或人工评分。

上传前发现科研对话追加`9676a37`定量说明，已保留合入；另补[分析协议](ANALYSIS_PROTOCOL.md)、空白逐事实记录和[evaluation_analysis.py](../../evaluation_analysis.py)真人评分汇总入口。当前所有真实质量比例、分数与差值为null，不能当作0分或真实比较结果。

## 先看这些

- [逐项复核响应及准确缺项](REVIEW_RESPONSE.md)。
- [完整共同输入ZIP](package/runtime.zip)：11个已见模板的完整题干、原始行、按轮消息、共同条件和资源清单。
- [工具资源ZIP](package/tool_resources.zip)：同一固定参考、真实已存分数/seed/近匹配/表达及既购独立版本；还有单列问答用的原12材料文库备份。
- [评审材料ZIP](package/review_only.zip)：完整逐题标准、原始来源、核对底表和空白评分表。与运行输入物理分开。
- [完整逐题标准](package/review_only/TASKS_AND_STANDARDS.md)、[原始输入全文](package/runtime/cases.json)、[空白评分表](package/review_only/blank_scores.xlsx)。组别对应关系单独放在`package/planning/`，不在上述评审ZIP内。
- [无模型验收与每个计划单元状态](offline_acceptance.json)、[全部原始检查记录ZIP](offline_raw_records.zip)、[逐文件校验](offline_archive_receipt.json)。
- [固定流程可读示例](fixed_workflow_examples/)：W1两状态，W2九条坐标，W2b真实精度分数，W3两候选和警告，U1/R1两轮，以及R2–R4可靠性材料。

## 实际完成范围

| 类型 | 已整理模板 | 本轮执行 |
|---|---|---|
| 实际工作 | W1、W2、W2b、W3 | 已用真实已存工具数据作无模型验收 |
| 需求追加 | U1 | 三组同一两轮，各留自己的历史；科学工具每轮重新核对，未跨组共享缓存 |
| 可靠性/澄清 | R1、R2、R3、R4 | R1两轮先原文后显式假设；其余为明确标注的构造错误/缺项 |
| 文献问答 | Q1、Q2 | 题干、输入、允许资源、标准已齐；三组检索入口仍不对等，6个计划单元标未运行 |

9个可作入口验收的开发模板 × 3配置 = **27个离线检查单元**；U1和R1各有两轮，累计**33个用户轮次**。另有Q1/Q2的6个配置单元未运行；完整33个题×配置计划状态都保留。不是27道独立题，也不是旧54条的新成绩。

固定流程按三组共同可见的需求条件，通过同一个通用映射选择工具；没有按题号或评分底表选路。普通模型的替身收到相同原始文字/候选和轮次，但没有科学工具；这是预先声明的系统差异。两个工具配置可用资源字节和接口相同，不宣称三组计算证据访问完全相同。

程序保存并检查了**准备给模型替身的请求全文**、每轮消息、各自历史和资源清单，未发生真实API传输，不能据此声称线上模型已实际接收或通过。真实工具部分是轻量序列/参考核对及已有结果导入，没有重跑OligoFormer、SeedMatchR或近全长扫描。

## 检查与失败

- 新增8项针对公平输入、两轮历史、绑定与证据展示的检查和4项定量算法合成测试通过；最终全部192项Python检查通过，三项前端检查通过。它们是程序检查，不是科研样本数或准确率。合成单元只在根目录测试代码中，没有导出为论文数据。
- [首次新检查失败](tests_dialogue_01.txt)保留：新适配器的修饰说明误多写一个英文词，严格绑定正确停止；已准确恢复新说明文字，不放宽碱基、原修饰或参考绑定。旧数据未改。见[first_attempt](first_attempt/CORRECTION.md)。
- 空白Excel包含33行、132个评分单元，评审人及判定栏全部空；有0–2分和交付判定的输入限制。已检查保存文件CRC/XML和实际渲染。**Windows表格生成库在完成写出后退出报错，重试仍发生；日志保留，未把进程退出说成通过。**已写出的Excel文件独立复读通过，但未在本机Excel界面验收。详见`blank_scores_saved_file_check.json`及`blank_scores_build_*.txt`。

## 复现方式

在仓库根，用项目Python运行：

```text
python scripts/build_evaluation_development_pack.py --output _test_runs/new_development_package
python scripts/check_evaluation_development_pack.py --package _test_runs/new_development_package --output _test_runs/new_offline_records --summary _test_runs/new_offline_acceptance.json
python -m unittest test_evaluation_dialogue -v
```

必须使用新的空目录，旧输出不覆盖。新两轮入口复用现有规划、依赖与科学工具，当前只允许明确传入的测试替身；旧评价命令若接到新题包会明确停止，不会自动启动付费模型。空白Excel另用本目录表格生成器，需官方表格运行库；JSON空表和标准始终保留，不依赖生成库才可核对。

下一步：请科研对话复核本题包和无模型证据。真实付费运行、未见题与真实独立评分另需安排；本轮无需用户操作网页。
