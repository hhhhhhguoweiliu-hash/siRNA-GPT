# 任务B线上部署与两题真实演示

2026-10-24，北京时间。实际部署提交`179a7af6bf74620c31b23bbd5d7bfccaa1303ba0`；新增功能代码来自ba94bb4。线上`/api/runtime`已实际读取并核对，Render部署`dep-dbe1uqd9fdbs73925gt0`于11:01:45完成。没有改登录、费用、权限、启动检查或科学候选排序。

## 本轮真正运行了什么

先保存更新前当前会话、浏览器原有历史，以及旧服务报告20261024_025019_83e11e的完整34文件包；包CRC校验通过，原模型请求/响应及工具结果保留。10月24日这份报告由原有启动检查生成，不能记为本轮新增文库评价或旧54条之一。备份先以179a7af上传私有GitHub，再通过官方Render连接更新同一服务。

上线后，网页再次导入真实siDirect原PDF，返回“原文件已经在文库中”，保留首次来源声明；没有冒充新增论文。中文SeedMatchR问题检出英文论文与1.1.1官方源码。9份资料、siDirect全部8页/28片段及文库版本与本地开发检查一致。新文件首次导入和异常PDF此前通过同一HTTP入口检查；本轮线上PDF操作是重复导入检查。

执行端在原网页勾选用量确认，**只点一次“运行两题文库演示”**，没有点三组评价。实际运行`library_demo_20261024_032210_21c28f`，11:22:10–11:22:20：

| 预定单元 | 实际状态 | 实际模型调用 | 本轮作用 |
|---|---|---:|---|
| B02：分数超过1能否当成超过100%敲低 | COMPLETED / complete | 1 | 使用本轮检出的6个片段，保留原始请求、响应、引用、用量 |
| B08：本项目患者视力改善与临床剂量 | COMPLETED / no_evidence | 0 | 程序判断范围/资料不足，明确拒绝提供未测数值；不是一次模型拒答能力测试 |

## 实际请求和用量

- 模型：`doubao-seed-2-1-pro-260915`，请求/响应型号一致。
- `thinking.type=disabled`，`stream=false`，`max_output_tokens=1800`；原始最终请求采用现有客户端的Responses格式，未把温度等未发送字段补写成实际参数。
- 原始响应状态`completed`，没有返回`incomplete_details`字段；没有截断或账号错误，没有重跑消错。
- 本次文库问答实际用量：输入5927、输出305、合计6232词元（模型接口的用量单位）。缓存命中0、思考词元0均为接口实际返回。
- **6232仅是这次文库问答用量，不是部署期间账号总用量。**保留的启动检查另有真实API调用；启动日志没有完整总用量，未填零费用或合计部署成本。

## 原件取回和可复核性

通过原服务日志取回159个传输片段，组合为711727字节原始ZIP，SHA256为`fe223ce2d3a174a3968b6a8594d9cded04b7861d58917f3b39608df8c17e2d83`，与服务收据一致，CRC通过。日志接口每次最多100条，分两页取回全部159条；第一次请求250条被接口拒绝，仅修正日志取回分页，没有重跑问答。

原包[actual_demo_original.zip](actual_demo_original.zip)、[完整原始回答](actual_demo/results.json)、[全部请求/响应和片段](actual_demo/conversation/evidence/)、[取回校验](actual_demo_recovery_receipt.json)、[实际片段核对](actual_demo_integrity_checks.json)、[可重新导入的线上文库](actual_demo/library.zip)。所有2个计划单元都保留。

已把真实服务导出的文库重新导入本地空库，再删除派生索引并重建：版本仍为`b4d516450903cd7df6087b965f28225ee1a411689824f2b4e94301744aaf44c3`；6份实际引用片段逐字一致，3个明确短引文确实存在。没有把编号有效当成每句话科学正确。线上原文页标题实际打开；后续片段自动截图被其他浏览器扩展界面阻止，未伪造截图或绕过该限制。导入/检索/引用/恢复的程序核对与人工科学评分分开。

## 可用于论文的边界

目前可以说明实现了小范围文献导入、中文检索英文、按实际片段问答、来源定位、无证据处理和文库导出恢复，并提供这一个真实问答和一个程序无证据处理示例。10项开发核查是预先确定的工程检查，159项是程序检查；**均不是独立科研准确率**。本轮不宣称Agent优于对照，不画优越性图，不代填人工分数，不把新功能追溯计入旧54条。

只有siDirect具有本轮取得的原PDF；另外两篇为原始全文XML及其中摘要/正文提取文字，没有PDF页码或图片识别。免费实例的用户上传与运行记录仍需下载，不保证永久保存。

下一步可请科研对话核对这两题原始回答及方法描述；不需要重跑54条或扩大课题。以下逐字保留两题原回答。

## B02 原始问题与回答

问题：OligoFormer分数超过1可以解释为超过100%的敲低率吗？

**判定：不可以。**

**关键结果：**
- OligoFormer 的输出是用于反映诱导基因敲低潜在有效性的**预测分数**，不是实测敲低百分比；分数超过 1 不能解释为“超过100%敲低率”。项目设置明确说明“模型分数不是实验敲低百分比”[S1]；论文也称输出是“prediction score … reflecting its potential effectiveness”[S3]。
- 官方推理源码还显示输出经过线性缩放：`Y_PRED = [i*1.341 for i in Y_PRED]`，随后写入 `efficacy` 列[S2][S5]。因此该数值可能超过 1，但源码片段本身没有把这个缩放后数值定义成百分比，也没有给出 0–100% 的边界保证。
- 若需知道实际敲低率，只能通过相应实验体系中的敲低/沉默实验测量；本项目模型分数只用于候选排序与复核，不等同实验结果[S1]。

**证据：**“模型分数不是实验敲低百分比”[S1]；“prediction score for each siRNA”[S3]；“i*1.341”[S2]。

**限制：**以上是项目设置说明、官方源码和论文文字片段；不能据此反推出某一具体分数对应的实际敲低百分比。

## B08 原始问题与回答

问题：请给出本项目已经测得的人类患者视力改善百分比和临床给药剂量。

判定：当前文库证据不足。
关键结果：没有找到支持这项结论的资料，不能提供本项目未测得的数值。
证据：本轮本地检索没有可引用片段，未进行联网补查。
限制或下一步：请提供与问题相关的原文；导入后再核对。

## 本次B02实际引用对照

| 编号 | 类别 | 实际来源与定位 |
|---|---|---|
| S1 | project_setting | [模型分数和实验敲低率 · 项目说明卡；无PDF页码](https://sirna-gpt.onrender.com/knowledge#score) |
| S2 | official_source_code | [OligoFormer official inference source, including score scaling and input context · 文本，片段text-c007](https://sirna-gpt.onrender.com/library/ec77cffdc9e76e478068430f#text-c007) |
| S3 | article_full_text | [OligoFormer: an accurate and robust prediction method for siRNA design · 文本，片段text-c020](https://sirna-gpt.onrender.com/library/e2cea21b6712b85250758e8b#text-c020) |
| S4 | article_full_text | [OligoFormer: an accurate and robust prediction method for siRNA design · 文本，片段text-c001](https://sirna-gpt.onrender.com/library/e2cea21b6712b85250758e8b#text-c001) |
| S5 | official_source_code | [OligoFormer official inference source, including score scaling and input context · 文本，片段text-c011](https://sirna-gpt.onrender.com/library/ec77cffdc9e76e478068430f#text-c011) |
| S6 | official_documentation | [OligoFormer official README (pinned historical version) · 文本，片段text-c001](https://sirna-gpt.onrender.com/library/fce74ce24f4c5275cdea80d0#text-c001) |

页面分类来自保存的来源声明，不等于已通过专家审核。
