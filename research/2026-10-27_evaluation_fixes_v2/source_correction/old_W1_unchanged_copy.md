# 固定流程的本轮离线交付，不是模型回答

## 第1轮

判定：本题报告流程完成；以下仅为优先复核证据。
关键结果：
候选 | 参考 | 19nt核心起止(1-based) | 参考转录本覆盖
--- | --- | --- | ---
USER_PURCHASED_siVEGF | NM_003376.6 | 1439–1457 | 18/20

候选 | 模型分数(scaled，原始精度) | raw_class1 | 来源状态
--- | --- | --- | ---
USER_PURCHASED_siVEGF | 1.121934400320053 | 0.8366401195526123 | IMPORTED_VERIFIED_LOCAL

候选 | 复核警告 | 近匹配窗口/转录本 | 当前规则列为优先核查
--- | --- | --- | ---
USER_PURCHASED_siVEGF | 未见当前规则的已知提示，不代表安全 | 见绑定记录；未见提示不代表全范围无匹配 | True

候选 | seed位点(含VEGFA) | 非靶seed位点 | 去重非靶匹配基因 | 可映射基因 | 常氧检出基因 | 缺氧检出基因 | 未映射基因
--- | --- | --- | --- | --- | --- | --- | ---
USER_PURCHASED_siVEGF | 3540 | 3539 | 2839 | 2836 | 1695 | 1595 | 3

当前工作规则的优先核查名单：USER_PURCHASED_siVEGF；不是生物学最佳答案。
证据：本轮实际完成：inspect_candidates、verify_target、score_candidates、match_seed、query_expression、compile_report。核心坐标来自verify_target，不用23nt设计窗口坐标代替。分数导入来源指纹：ef91800094f711e5358c5bab3e5415fd60256056a7479b24b8be674c16e3d392。交付报告：report.html；全部候选底表：candidates_ranked.tsv。
限制或下一步：分数不是敲低率；seed不是实测脱靶；表达仅作注释、不改变排序；警告不是实测脱靶，无提示不是安全认证；两行链角色仅按用户明确计算假设使用，不是供应商确认；原始TT/N3保留，模型未模拟N3连接实物；同一培养批次、每状态4皿、未转染；缺氧1% O2 24h；检出为至少2/4皿TPM≥1，不是实际敲低效果。