# siRNA-GPT 0.5：联网科研助手

## 实际工作方式

1. 接收自然语言需求，保留当前对话和已有科学工具结果。
2. 根据任务选择直接解释、查文献/网页、澄清，或生成本地计算计划。
3. 检索问题进入有界工具循环：模型选择工具和参数 → 程序执行 → 返回原始证据 → 模型判断是否继续查证 → 带来源回答。
4. 文献检索优先使用 NCBI PubMed ESearch + EFetch，获得 PMID、题名、期刊、年份、DOI 和摘要；摘要不等于全文。
5. 普通网页与软件文档使用豆包 Responses API 原生 web_search。仅服务端返回的已完成搜索和 url_citation 标注可作为已联网的证据；纯模型文本不算。
6. 需要看来源时可以读取可信科研/官方站点的公开 HTML；不绕过付费墙、登录、验证码，不支持 PDF 解析。
7. 筛选计算沿用原有官方工具与已核对的输出，不让语言模型改变分数或凭文献编造候选序列。计算计划仍有确认步骤，查文献不逐步要求用户点击。

## 可追溯性和停止条件

- 每轮最多 6 次实际检索/读取、7 轮模型调用。重复相同工具和参数会返回错误，要求换词或总结已有结果。
- 搜索失败、无结果、未返回引用、正文未读取成功分别记录；可以换工具继续，不静默伪装成成功。
- 回答中的 [S1] 等编号对应真实工具元数据，来源链接由程序生成。未知编号标注为“未核实引用”。有链接不代表该来源自动支持所有结论，仍须人工核对。
- 网页和摘要作为不可信数据，不执行其中的命令。读取器限制 HTTPS、科研/官方域名、每次重定向、超时与响应大小。
- 每条回答保存自己的来源；研究步骤及当前资料可随对话 JSON 导出。当前服务为单用户共享会话，免费实例重建后记录可能丢失，请及时下载。
- 联网开关默认开启，仅代表允许使用；简单解释不必搜索。关闭后不提供联网工具。
- 当前云端仅整合已核对的 9 条 VEGFA 候选结果；OligoFormer 和 SeedMatchR 的新计算仍需要计算后台。其他靶点可查文献，不能宣称已运行本地筛选。

## 修复与检查

- 页面区分 PubMed 和普通网页搜索的实际连接状态。豆包返回 ToolNotOpen 时，禁用该工具供模型选择，但保留 PubMed 和可信网页读取；页面提供服务端提示的官方开通入口。开通后的“检测模型与联网”会重新检查三项连接。
- 在云端用独立会话检查完整路径：自然语言提问 → 模型选择 PubMed → 真实检索 → 工具结果回传 → 生成带来源的回答。该测试不替换用户正在使用的会话，结果单独写入 STARTUP_CHECK research_conversation 日志。

- 所有 Responses input 元素都显式包含 type（message / function_call / function_call_output），避免混合工具历史报 MissingParameter input.type。
- “检测连接”实际执行两次模型请求：请求函数调用、回传测试函数结果并取得最终回答。第一轮可调用不再被当作多轮已验证。
- Gunicorn 启动时在后台执行轻量检查：真实两轮模型调用、公开关键词 PubMed 检索、官方网页搜索。结果保存在服务器记录并以不含密钥的摘要写入 Render 日志；同一运行目录、同一 commit 只测一次。STARTUP_CHECKS=0 可关闭。
- 自动化测试使用明确标注的模拟外部服务，只证明程序契约与错误处理；线上真实检查单独记录，不混淆。

## 官方参考

- Anthropic, Building effective agents：https://www.anthropic.com/engineering/building-effective-agents 。参考简单组合、工具循环、环境反馈、明确停止条件。
- 火山方舟 Responses API：https://console.volcengine.com/ark/region:cn-beijing/docs/create-model-responses-api 。核对 input.type、function_call_output、原生 web_search、引用标注参数。
- NCBI E-utilities：https://www.ncbi.nlm.nih.gov/books/NBK25501/ 。使用官方检索和摘要接口；无 API key 时限制在每秒 3 次请求以内。

本版本沿用已部署的 Python/豆包架构，没有迁移模型供应商、训练 Transformer 或声称复现文献中的完整系统。
