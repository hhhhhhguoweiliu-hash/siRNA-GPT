# 图件交付记录（2026-10-27，UTC）

本目录为已有评分数据的柱状图与雷达图重绘，审查基点为 `05b46d1a1ac453392c239891acd002f9e09435e3`。数据直接取自提交 `748a71bec7043fdd9b031731c237f687009f015b` 的旧图数据；72个均值全部逐项复核，与旧数据及本次两种图形一致。未新增评分、模型调用或科学计算。

## 可下载文件

- 三页完整PDF已保存：[siRNA_GPT_bar_radar_REVIEW_PENDING.pdf](https://chatgpt.com/library?file_id=libfile_1a6e0e0a55608191bde229d7d6cb003b&account_id=personal)。
- 复现数据：`bar_radar_plot_data.csv`、`bar_radar_plot_data.xlsx`。
- 可编辑矢量图：`figures/*.svg`；PDF中已嵌入实际Arial Bold字体。
- 图件ZIP保存在本地 `deliverables/siRNA_GPT_bar_radar_figures_only_20261027.zip`，1,076,612字节，SHA256为 `af3dc69daaa1aa65878db9c88e77e1e5dd1a5e6d46299ace603785f840eeeec4`。仅含本次图件与图注，不含原始答复或专家原表。

## 交付状态与解释

本次新PDF和ZIP向Google Drive的上传均被自动审批拒绝，理由是新生成的私有研究材料尚无单独外传授权。没有重试或绕过，该两项文件**未上传Drive**。上述PDF保存成功；Windows本地元数据附加脚本因平台不支持 `os.setxattr` 未完成，这不改变已成功创建的PDF记录。

A、B两份评分分别展示；不混入C表、重复评分文件或后续粘贴评分。不把这些表的数量视为已确认的独立评审人数。标准任务4题、可靠性4题、需求变化1题分别展示。评分理由中已有待核对项，因此全部图保留 `REVIEW_PENDING`，不宣称已完成裁决或独立统计验证。

现有四维评分无法直接转换为分类Accuracy/Precision/Recall/F1；相关字段保留空值，不绘制虚构指标。详见本次科研复核文档和 `metric_availability.json`。
