# 10月24日小批：检索修正、三篇实验文献与九条候选论文材料

实际从main **7bf22d3** 接手，读取12:15任务、11:56 A/B复核及其JSON，另读取12:49后续规则复核。后者关于“工作阈值不等于已验证规则、先确定靶转录本”的意见一并落实，不扩大本轮运行。

上传前再次同步到科研对话刚提交的 **ba13edd**，读取13:16交接；其中已有订购原件与本次复制件SHA256一致。新增候选实际评分/扫描作为后续批次，此处全104行只是旧规则的轻量比较，未完成新候选计算就不声称完成。

## 已在本地完成

- 文库范围停止与实际空检索分开；不再由“患者”一词屏蔽证据边界问题。首次离线发现数字21误命中项目卡，也已修正；[首次失败](offline/focused_checks.json)保留，[修正后检查](offline/verification_02/focused_checks.json)另存。161项程序检查通过；这些不是161道科研题或科学正确率。
- 指定三篇实验论文原件、来源和定位已补入：[来源与读取范围](../../references/vegfa_experiments_20261024/README.md)，[逐论文实验条件表](experimental_literature_evidence.json)、[TSV](experimental_literature_evidence.tsv)。Chen、Osipova为完整XML文字，Kleinman为15页作者稿PDF，不含补充序列表。
- [两条独立文献参考序列](literature_reference_sequences.tsv)：Chen的target2只是19碱基靶序列；Osipova保留原文27bp双链及方向。没有猜缺失末端/修饰、不混入原九条。
- [完整九条可读表](FIXED_NINE_TABLE.md)、[全字段TSV](fixed_nine_complete_table.tsv)、[英文论文Methods](PAPER_METHODS_EN.md)。保留原顺序、原预测分数、全部警告，区别23nt窗口/19nt核心、位点/基因/可映射/状态检出。无本项目实验敲低率。
- [已有订购文档原件](originals/purchased_sequence_spec_original.docx)、[逐段提取](purchase_document_extraction.json)、[有假设说明的序列比对](purchased_siVEGF_sequence_check.json)。已找到两条si-VEGF书写序列；不是要求重新购买。[小试真正缺项](SMALL_TRIAL_CHECKLIST_ZH.md)供科研对话判断。
- [旧B08追加纠正](OLD_B08_CORRECTION.md)；原B08、九条、54条和失败不改。本轮无重型重算、湿实验或状态风险重排序。

## 本次实际检查和运行边界

离线以实际HTTP导入路径导入三份、核对中文检索/来源定位、相关片段传递、导出重导及删除派生索引后重建，最终12份材料版本 **ac6d351a2e992bc86dfb87db6527861752c1ec6bab07adb7e33b667052576a54**。模拟传输只作程序检查，文件名含TEST_ONLY。旧开发题受扩库影响的检索变化另存，不回写旧10题。

更新前工具报告已由用户保存，34文件ZIP完整校验见[备份收据](predeploy/backup_receipt.json)；它是旧版本自动启动检查产生的报告，不能算指定的新问答。自动启动的连接/工具检查继续保留，不能混入文库新题或旧54条。

**实际完成：**代码fa62c7d已上传main和现有任务分支，GitHub两项检查成功；现有网站dep-dbe428ei0phs73bn25m0已live，并核对实际运行代码及12份文库版本。通过现有网页用量复选框，只点新增单题入口，完成[第7天真实问答及全部原始记录](live/README.md)。实际1次模型调用、用量6816词元；回答明确没有所问实测数据，不能拿模型分数或别篇论文比例填空。8个片段及实际请求/原始响应均已核对。不是未见题准确率，没有代填人工评分；[最终上传及部署说明](DELIVERY.md)单独列出。

## 交科研对话复核

重点检查：英文方法是否准确表述历史工作选择；两条文献参考的原始形式与实验条件是否充分；已有si-VEGF最终供应商链/化学标注及真实靶转录本范围还缺什么。不要把试验提议或别人的文献结果写成本项目实测，也不要把一次针对性补测写成未见题准确率。
