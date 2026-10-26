# 人工填写Excel到汇总

这是录入人工判断的工具，不是自动判题。真实运行前先审核任务、事实标准和允许资源，固定后不看结果改规则。当前所有实际计划仍为未运行；导入器会拒绝为未运行单元填写分数、事实判定或裁决。不要给程序替身评分。

1. 从 `package/review_only/review_form_blank.xlsx` 各复制一份给两位独立评审，分别命名A.xlsx、B.xlsx。两人独立填写；不要互看评分或接收组别密钥。按答复编号对应匿名实际回答及证据。
2. `评分表` 填四维0/1/2、交付判定、严重错误、理由。`逐事实` 保留全部210行，逐一填写正确/错误/缺失/未评分及依据。不得删除未运行或难评行。事实标准草案仍需独立人员审核。
3. 每份文件必须填写一个明确、唯一的评审人编号。至少在一处填写，同文件空白身份格继承这一明确编号；两表不能有不同人名，不按文件名猜身份。两名独立评审不能共用编号。原始格值和身份继承规则一并保存。
4. 程序只转换明确枚举：严重错误“是/否”→true/false，“待核对”或空→null；事实“正确/错误/缺失”→correct/wrong/missing，“未评分”或空→null；交付“不可评分”→null并必须有理由，**不会自动改为未交付**。true/false/null分别是明确的是/否/尚无判断，不是新分数。
5. 四维任何一项留空须说明原因。已经真实尝试但完全无可读答案时，可由真人判“未交付”，四维留空并说明服务/技术原因；不能据此把生物学事实填“错误”。严重错误在本版专指会推翻本题完成结论的错误，一般问题写备注。

四维沿用仓库 `evaluation_rubric.json` 的量表：2=充分满足本题条件，1=部分满足或有明确缺漏，0=明确错误或未达到，空白=未评或不可评分且需理由。事实准确、证据支持、需求完成、边界处理分别判断，不能按文风、工具数或程序状态打分。诚实说明未知不自动算事实错误，但是否完成本题仍按本题要求判断；必要事实见本包草案，不能套用旧六题标准。

实际匿名回答到位后，执行端先据真实运行记录另外生成完整状态文件（ATTEMPTED=实际尝试、NOT_EXECUTED=未运行），不能将当前 `real_execution_NOT_STARTED.json` 改成虚假尝试。以下用 `actual_execution.json` 表示那份未来真实状态文件：

```powershell
python review_import.py --plan research/2026-10-27_evaluation_fixes_v2/package/planning/analysis_plan.json --execution actual_execution.json --workbooks A.xlsx B.xlsx --output review_imports/new_01
```

输出四个只读汇总文件：`reviews.json`（每人原分、事实、备注、原格值及来源）、`adjudications.json`、`source_workbooks.json`、`analysis.json`。必须选新输出目录，不能覆盖旧人工记录；公式代填、未知编号、重复身份/行号、删事实或删计划行均拒绝。保存A/B原文件，不用导出JSON替代原件。

两人分歧或“完成”与必要事实/严重错误矛盾时，正式完成率暂空，原标签和各人分仍保留。由真人先查证，必要时复制原空表另存C.xlsx，只填 `裁决`；每项有裁决人编号和依据。一个答案有多个事实要裁决时可追加行并重复答案编号、裁决人和依据，但事实ID不重复，其他必要事实仍保留。四维原分不由裁决器或LLM擅自改写。

```powershell
python review_import.py --plan research/2026-10-27_evaluation_fixes_v2/package/planning/analysis_plan.json --execution actual_execution.json --workbooks A.xlsx B.xlsx --adjudication-workbook C.xlsx --output review_imports/new_02
```

事实、交付或严重错误尚未判清的项目继续留空；真人裁决可修正两人一致但内部矛盾的标签，原始记录永远保留。不能靠删除必要事实让“完成”成立。严格质量均分仍要求全覆盖，另报可评分数、不可评分数、原始分布与原因；没有临时挑成功子集均分。

**本轮确实走通的范围：**实际读取两份明确标为合成检查的XLSX、导入为待裁决汇总、读第三份合成裁决后生成已裁决汇总，并实际运行命令行入口。测试原件/命令/输出仅在 `tests/fixtures/review_import_synthetic.zip`；所有人名和评分均为合成工程夹具，禁止用于论文。正式空表导入为0条人工记录、率/差值全null。原生Excel界面未操作验收，不能称真人评审完成。
