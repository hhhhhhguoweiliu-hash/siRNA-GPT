# 固定流程的本轮离线交付，不是模型回答

## 第1轮

判定：停止后续计算；已有局部证据保留。
关键结果：
本题指定的用户表达表尚未提供，且禁止回退内置表达表；已有序列、参考、分数和seed结果保留，表达与完整报告未完成；原始输入：[{"candidate_id": "USER_PURCHASED_siVEGF", "guide_core19_5to3": "UUUCUUGUCUUGCUCUAUC", "guide_21nt_RNA_5to3": "UUUCUUGUCUUGCUCUAUCTT"}]

已完成工具：inspect_candidates、verify_target、score_candidates、match_seed；以下只展示实际已取得的证据。

候选 | 参考 | 19nt核心起止(1-based) | 参考转录本覆盖
--- | --- | --- | ---
USER_PURCHASED_siVEGF | NM_003376.6 | 1439–1457 | 18/20

候选 | 模型分数(scaled，原始精度) | raw_class1 | 来源状态
--- | --- | --- | ---
USER_PURCHASED_siVEGF | 1.121934400320053 | 0.8366401195526123 | IMPORTED_VERIFIED_LOCAL

已取得guide seed位点（含VEGFA）：{"USER_PURCHASED_siVEGF": 3540}；未取得表达关联，不填零。
证据：本轮实际完成：inspect_candidates、verify_target、score_candidates、match_seed。核心坐标来自verify_target，不用23nt设计窗口坐标代替。分数导入来源指纹：ef91800094f711e5358c5bab3e5415fd60256056a7479b24b8be674c16e3d392。
限制或下一步：未做表达关联；未选top候选；分数不是敲低率；参考覆盖不等于细胞内异构体表达；两行链角色仅按用户明确计算假设使用，不是供应商确认；原始TT/N3保留，模型未模拟N3连接实物；未完成部分不当作结果；确认支持的目标、链身份及19nt核心，不自动截短21nt或回退缺失数据。