# 本轮：输入公平性修复、一次诊断与完整54条真实开发运行

按20261022_1310科研复核继续现有任务分支与现有服务。先读[运行前说明](PRE_RUN_PROTOCOL.md)；[旧回答纠正说明](OLD_BATCH_CORRECTIONS.md)另写，历史原文不改。

已完成代码：三组保存同一完整原始候选/任务副本，规划器和执行器都能看到真实序列；普通模型无科学工具/外网。最终答复共用简短四部分；固定流程用确定性模板，不新增模型润色。位点/去重基因/映射/检出与23nt窗口/19nt核心明确分列。保存成功及失败的实际模型请求、原始响应和用量。

新运行导出完整for_review/材料与独立private_key.tsv；四项分数全部留空。本轮未新增算法、融合权重或科学范围。

无模型检查140项通过，前端检查通过，日志见checks/。这证明输入传递、字段和记录机制，不是140道研究题或科学准确率。独立评分与上游重型复跑/湿实验不冒称完成。

[一次真实诊断](DIAGNOSTIC_RESULT.md)已完成并保存原包、实际请求/响应/用量，38510字节/23文件CRC及SHA256通过；没有截断。随后用户在既有手动入口启动新54条`dev_20261022_054717_79c2d3`；北京时间13:47:17–14:00:47完成，全部54计划单元有实际记录、未执行0条。三组同原始输入、实际模型/思考/1800上限及工具数据版本核查通过，外网关闭；固定流程预选路径与Agent多轮调用的差异保留。

| 题目（每组3次） | 普通模型 | 固定流程 | Agent |
|---|---|---|---|
| 缺氧完整题 | 3次有回答，无科学工具 | 3次完整 | 3次完整 |
| 常氧完整题 | 3次有回答，无科学工具 | 3次完整 | 3次完整 |
| 仅候选/转录本核对 | 3次有回答，无科学工具 | 3次所需局部流程完成 | 3次所需局部流程完成 |
| AAA | 3次有回答 | 3次输入拦截 | 2次暂停/澄清，1次拦截后笼统失败答复 |
| KRAS | 3次有回答 | 3次范围拦截 | 3次暂停/说明 |
| 21nt链身份不明确 | 3次有回答 | 3次输入拦截 | 2次暂停/澄清，1次拦截后笼统失败答复 |

这是实际运行状态，不是科学正确性。80次模型请求（普通模型18、规划18、执行44）均返回completed，无不完整原因、账号或网络错误；返回用量完整：普通模型109570、Agent878820，固定流程无模型调用为0。Agent多轮导致总用量不同，不推算货币费用。六道已见开发题、每题3次技术重复，不能当18道独立题或生物学重复。

A037/A040的最终答复过于笼统，其他可定位措辞问题及后续修补详见[新批批注](NEW_BATCH_NOTES.md)；原始回答、错误与FAILED状态不改、不替换重跑。未来错误提示和评审错误附件已另修代码，141项软件检查及两项GitHub检查通过；PR #2已合入main `1f155cf`，原服务14:15:36上线，健康HTTP 200，详见[后续部署收据](post_batch_deployment.json)。本批实际版本仍为9daff5d，不把后续修补追溯成本批已具备。

## 实际文件与评审交付

- [完整原包](archives/dev_20261022_054717_79c2d3.zip)：2441770字节、815文件；CRC通过、SHA256 `ac580c48aa7769cd114c5895903eb2c49bcaf72b0718004fb928c1b30e6e5ef2`与[服务端收据](batch_receipt.json)一致。原始请求/响应及各调用用量在内。
- [全部逐条结果](three_arm/results.json.gz)、[54行记录表](three_arm/records.tsv)、[全部计划状态](three_arm/execution_status.tsv)、[80次请求/响应摘要](three_arm/model_calls.tsv)、[核查JSON](three_arm/audit.json)、[完整技术汇总](three_arm/technical_summary.json)。这些管理文件含组别，不能交盲评。
- **给独立评审只发[完整评审包](three_arm/for_review_complete.zip)**：含完整题目输入/逐题要求、允许资源、54份匿名原文与证据、字段说明及空白评分表、补充原始工具错误和完整同版科学底表。不发[组别密钥](three_arm/private_key.tsv)或完整运行原包。原始[服务端评审包](three_arm/for_review.zip)另留未改；补充包逐字节核查原回答和原证据未改、54份评分全空、无组别密钥。风格可能暴露配置，不称完全盲法。
- [同版完整科学底表](shared_scientific_references.zip)与[来源/哈希](shared_scientific_references.receipt.json)：本批六项数据资产与运行前指纹一致，另含两份报告补充注释。云端原包有意省去每次重复的大型seed/逐基因表达TSV，此处一次提供完整源表；不是新做重型推理，也不是普通模型当时收到的事后结果。
- [本轮科研复核落实](../../docs/REVIEW_RESPONSE_20261022.md)、[原始实际协议](three_arm/protocol.json)、[运行前说明](PRE_RUN_PROTOCOL.md)、[部署收据](deployment.json)与软件检查在checks/。

没有代填独立分数，也没有画优越性图。本批可交独立人员做完整开发评价；答案是否科学准确、异常处理是否满足题意仍待评分。重型复跑、真正文献siRNA接入及湿实验仍未完成，不能用本批替代这些证据。

## 可复现的无模型整理

从仓库根目录执行，输出换成新的空目录或新文件；不覆盖原包：

```powershell
python -X utf8 scripts/audit_fairness_batch.py --archive research/2026-10-22_fairness/archives/dev_20261022_054717_79c2d3.zip --output research/new_audit/three_arm
python -X utf8 scripts/package_review_references.py --protocol research/new_audit/three_arm/protocol.json --output research/new_audit/shared_scientific_references.zip
python -X utf8 scripts/finalize_fairness_delivery.py --root research/new_audit
```

修复1698169已通过两次GitHub检查，PR #1合入main 9daff5d；原服务新部署live，HTTP健康与既有模型/六工具启动检查通过。详见deployment.json。启动检查不是本批诊断或54条评价记录。浏览器控制读取持续超时，用户在现有页面手动确认启动后，已从原服务日志取回完整原包并核对。
