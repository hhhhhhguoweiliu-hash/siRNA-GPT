# 本轮交付与验证

实现/证据提交：`e02708125b91dd8cdcb63f64f0a0c80725689db7`（71文件变更，[完整清单](CHANGED_FILES.md)）。第一次普通推送因远端新增`f92adcdbaf89a34010e1ad00d31c2954a77355a7`被拒绝；读取其v3完整审计后，正常合并为`601431d008106b8f11d75fa02f244d147c2d2a43`，普通推送成功，保留双方父提交，未强推。v3标准/逐项标签/任务判断与复算输入一致，全部12行汇总逐字段1e-9内一致。raw比较修正与原始JSON相符，见latest_v3_alignment与raw_comparison_status_v3，原v1/v2不改。

GitHub连接从601431d读回并与本地Git对象一致：`metrics/status.json` blob `ad0bbb299a8e26582d2522e385aa13f898fa5468`；`independent_matched_mapping/run.json` blob `7dcd4a055dd275e380ce3d80a7bf38dd5d7ef04f`；`original_integrity.json` blob `733ec9eac2d920a262caf3681624d2402d7b4d1c`。本段为实际读回收据，不表示对所有内容作独立科学验证。

分支`codex/20261020-evidence-pilot`。初始33cd228，完整保留并纳入并行ab54de1；main仍2623c86。实现、全部新复算与失败/差异、评审范围/方法和原件核对在本目录；代码变更为`sequence_validation.py`、`delivery.py`、`bound_reuse.py`、`conversation.py`、`core.py`、`evaluation_dialogue.py`及新回归检查。共同WORKBOARD/STATUS只追加最新入口，保留历史正文。

- 本地软件验证：71个不同的定向检查通过（47项实现/对话/取消/复用检查＋24项原核心/导入/科学边界检查）；最后涉及展示/绑定/子流程的19项再验通过。原始输出见`final_implementation_checks.txt`、`scientific_boundary_checks.txt`、`final_changed_path_checks.txt`。未执行真实问答整批或把替身当新模型表现。
- A013保存原答回放：旧检查FAIL、新检查PASS；旧24位、单碱基错和角色错仍FAIL。原raw10文件与4244ac0的Git blob精确一致。
- 科学计算复核：10条guide，19,415条固定代表性UTR，独立位点/转录本/基因seed差异0；同版映射的原TPM逐基因和检出集合差异0。首轮异版映射35条候选×基因差异、100条集合差异全部保留。两次实际运行时间/退出状态/指纹见对应`run.json`。
- 指标：135原子标准、405已有AI判断、27整题，原件标签未改；复算与ab54de1一致。正式人工指标、C1为NOT_READY，不生成优越性图。
- 失败记录：首轮测试临时目录权限错误保留，切换项目内临时目录后通过；官方分数源核对曾错误要求10条都在旧mini批评分，断言失败另记，后按实际3条批内评分与10条源表分别核对，没有补跑或改旧结果。

本轮真实模型调用0、人工质量标签新增0、OligoFormer新推断0。实现/证据及并行审计已实际上传原任务分支并读回；收尾对齐说明另追加提交。未合main、未部署，未做新线上浏览器验收，没有改账号/用量设置。现阶段无需用户重新提供原表或启动网页，需真实人员确认现有标准/争议及独立性后再做正式人工汇总。
