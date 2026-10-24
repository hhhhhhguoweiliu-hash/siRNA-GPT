# 新候选批交付：实际运行和仍缺项

从main f60add9继续，先完成科学方案、官方示例及少量测时，再进行明确范围的真实本地计算。全部65条新版本设计候选与既购1条的预测、双链种子计数已完成；近全长完整核对的是5条编码区设计＋既购1条，共24查询。另240个非编码区查询因事先限时未执行，逐项保留，不填零。

结果从[完整入口](https://github.com/hhhhhhguoweiliu-hash/siRNA-GPT/tree/main/research/2026-10-24_candidate_v2)查看，重点是完整65条表、既购独立结果、原始输出/日志、SMALL_TRIAL_REVIEW.md、METHODS_EN.md、图和完成核验。文献参考另列，未计算值留空，原21字符与TT/N3不改。

可交科研对话讨论的新设计为1555、1157，既购单列；它们均未做本项目效力实验。1555仅14/20固定参考匹配，仍需决定真正靶转录本范围；不能说泛VEGFA通用。1552的1错配匹配及其他序列标记全保留，不能以分高替代核对。最终链/末端/修饰、N3连接实物、质检和小试条件仍需确认；没有自动下单或实验。

上一批三篇实验论文及第7天1次真实问答已只读核验复用，不另跑，不把它们算成本批新增问答。没有人工评分、HIF扩展或状态风险重排序。旧九条和旧54条不变。

新图是完整数据的描述图，英文、真实Arial/Arial Bold及PDF字体嵌入已核对；不是准确率、效力或安全性图。本批不修改网站默认池、不部署重型后台，上传提交将使用[skip render]。最终GitHub提交与Drive文件、大小/父目录核对见SYNC.json；参考数据另包，避免与结果混为新实验。大权重只按已核对来源/指纹复用，不重复上传。

## 已上传并核对

实际结果提交：**9dd8831ebc28a42584ba57f288a314ccb5042b2c**，main及原任务分支均已推送，GitHub两项程序检查成功。本批没有触发网站部署。

- [完整结果包，436文件、19690699字节](https://drive.google.com/file/d/1-KV60yR81gWsCM5BqWBRNyI0QT-tvHYu/view)。包含全部65＋1结果、含零计数/位点/日志、原始输入、官方使用源码、三篇原件和既有真实补测原ZIP。
- 完整参考数据原件230823493字节，连接工具单文件上限100MiB，整包上传在动作前被拒绝，未生成整文件。按原字节分为3份：[001](https://drive.google.com/file/d/1N-3o47Kz6JAjWfNazXOCpSmXUDOSTsPA/view)、[002](https://drive.google.com/file/d/1aQIQ2xTDkRsfRv1GJ0GRqiC_gnHTyQM-/view)、[003](https://drive.google.com/file/d/154I8X_jVGFo2W03wpMDKktLAH3I8KYQx/view)。它们包括保存的完整NCBI RNA/GFF原下载及完整代表UTR/映射/历史转录本TPM表，不是新实验观测。原下载文件指纹与旧收据一致。
- 分卷必须依001→003原字节合并再解压，不能分别当完整ZIP打开。每卷及合并后的指纹见reference_package_parts.json；[恢复/检查程序](../../scripts/restore_candidate_v2_reference.py)默认核对指纹，输出已存在且不同则拒绝覆盖。无需用户现在操作，日后复现时使用。

远端文件名、大小与原项目父目录均已实际读取核对；连接工具没有给出远端SHA256，不能声称已比较远端字节指纹。结果包是上传前完整内容，后补同步收据和说明以GitHub最新main为准。

初版汇总method字段的英文“Preregistered”另作[文字纠正](WORDING_CORRECTION.md)：这里只在本地运行前写明规则，没有正式公开预注册。原始数据及初版记录保留，不把标签当作注册认证。
