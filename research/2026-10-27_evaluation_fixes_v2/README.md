# 10月27日第二次复核修正：开发准备，不是模型成绩

接手提交：`f665696dd844a97d21270198f12f5bf234710f90`，原任务分支 `codex/20261020-evidence-pilot`。本轮依据 [b2dd233验收复核](../../docs/reviews/20261027_b2dd233_evaluation_acceptance.md)，不新增题型或科研计算。原main读取版本为 `2623c8601bd4b19b472fafc520b95c0cfd0a0fdb`；上传、合main、部署分开记录。

- [逐项修正与证据](REVIEW_RESPONSE.md)：A提示泄露、B逐候选来源、C人工评分导入与矛盾检查、第5节失败/预算边界。
- [共同运行题目和完整原始输入](package/runtime/TASKS_AND_INPUTS.md)、[允许资源与指纹](package/runtime/resources.json)：只包含运行可见内容。
- [评审全文和逐题标准](package/review_only/TASKS_AND_STANDARDS.md)、[事实项目草案](package/review_only/fact_items_DRAFT.json)、[填写说明](package/review_only/REVIEWER_INSTRUCTIONS.md)。标准仍须独立人员在真实运行前审核。
- **[可直接填写的空白Excel](package/review_only/review_form_blank.xlsx)**：33个答复位置、132个四维分数字段、210条逐事实位置，另有人工裁决表；所有人工填写字段仍空。当前没有真实新回答，不能给测试替身打科学质量分。
- [人工评分到汇总的操作说明](REVIEW_IMPORT.md)、[实际XLSX导入检查](review_import_acceptance.json)。合成检查原件在仓库 `tests/fixtures/review_import_synthetic.zip`，不是论文结果。
- [离线完整检查](offline_acceptance.json)、[全部离线原始记录](offline_raw_records.zip)、[失败边界记录](boundary_test_records.zip)、[边界核对](boundary_acceptance.json)、[分数逐行追溯](source_correction/score_source_checks.json)。
- [付费入口接入前的明确缺项](API_READINESS.md)、[交付状态](DELIVERY.md)、[文件指纹](FILE_MANIFEST.json)。

三个独立压缩包：[共同运行输入](package/runtime.zip)、[工具数据](package/tool_resources.zip)、[仅评审材料](package/review_only.zip)。组别对应表只在 `package/planning/private_group_key.json`，不放入评审包。不要把评审包当作模型输入。

本轮实际完成204项Python检查、3项前端检查、27个配置单元/33个用户轮次的本地检查；文献问答Q1/Q2的6个配置单元仍不支持对等检索，明确未执行。普通模型/Agent使用明确的程序替身，科学工具只核对序列/参考并读取已有真实结果，**0真实模型请求、0重型重算、0人工科学评分、0新部署**。这不是完成率、准确率或Agent提升幅度。

旧题包、旧错误示例、九条/54条和原科研数据不变；纠正另存本目录。`source_correction/old_*_unchanged_copy.md`为旧错误短答的原样副本，应与新来源说明同读。

Excel已保存并独立读回、检查结构、实际导入及预览。生成库在全部四份文件写出后出现Windows退出异常，原日志保留；不把该进程说成正常退出，也没有原生Excel界面验收。文件检查与实际导入通过的范围见 `blank_workbook_check.json`。
