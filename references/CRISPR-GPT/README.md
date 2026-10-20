# 本课题的主参考：CRISPR-GPT

Qu et al. **CRISPR-GPT for agentic automation of gene-editing experiments**. *Nature Biomedical Engineering*. Published online 30 July 2025. DOI: **10.1038/s41551-025-01463-z**.

- [期刊原文与原始PDF入口](https://www.nature.com/articles/s41551-025-01463-z)
- [作者公开代码](https://github.com/cong-lab/crispr-gpt-pub)（轻量公开版本，不能当成完整系统源码）
- [用户所提供原文的可读取文本](paper_extracted_text.txt)
- **[先按这份迁移路线出结果](../../docs/PAPER_MIGRATION_FAST_TRACK.md)**
- [逐项机制与实现边界](../../REFERENCE_ALIGNMENT.md)

## 原文文件状态与读取边界

原文件名为 `s41551-025-01463-z.pdf`，17,033,615字节。2026-10-20尝试取得原PDF字节时，文件下载失败，因此**当前Git仓库没有原PDF二进制文件**，不能把本目录说成已经收齐原始PDF及补充材料。

本目录文本直接来自用户提供论文的文档读取结果，不是模型改写摘要。读取接口共返回1,578个索引行，分两次连续读取1–1000和1001–1578，无剩余文本。保留了页面标记、Methods、Data availability、Code availability及扩展图说明。接口把文件标记为24页，但可提取文本中的页标记只有1–19；另外请求20–24页文本未返回可读内容。双栏顺序、公式及图内信息可能失真，细节须回看期刊原PDF，不能把文本抽取当成全部24页图像已核对。

文本校验值和读取范围见[source_manifest.json](source_manifest.json)。这里不提交临时下载签名、账号凭据或原文件访问令牌。

## 迁移时先抓住什么

1. 沿用Meta / Auto / Q&A三个交互模式，把CRISPR任务换为siRNA候选核对与筛选辅助。
2. 沿用规划器、任务状态机、工具接口和用户澄清反馈；先完成一条可导出、可复查的链路。
3. 沿用工具证据与可信资料支撑回答的方式；清楚区分历史官方结果导入与新序列现场计算。
4. 沿用任务评价、人工评价与实验案例三种证据的分工，缩小规模先做开发预评估。

原文还有288题基准、专门微调的8B Llama3及多种湿实验。本课题当前不把这些全部复现作为拿到第一批结果的前置条件。三组中的“固定流程”是本课题为区分同工具条件下适配能力而增加的对照，不要写成原文已做过完全相同的三组设计。
