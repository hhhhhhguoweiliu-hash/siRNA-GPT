# 首版小型文库：原件与来源

范围只含工具使用、分数解释、链方向、seed匹配局限及项目证据。不是全部siRNA文献库，也没有微调或向量模型训练。

[sources.json](sources.json)记录9份导入材料的题名、DOI或来源、版本、类别和SHA256。**9份材料不等于9篇论文**：3篇工具原文的提取文字、其中siDirect另有1份原始PDF、4份固定版本官方文档/源码、1份本项目来源核查记录。另外保留现有6张项目说明卡，作为单独的“项目设置”来源。

| 原文 | 实际取得的材料 |
|---|---|
| [OligoFormer](https://doi.org/10.1093/bioinformatics/btae577) | NCBI全文XML及提取文字；没有取得原始PDF，不提供虚构PDF页码 |
| [SeedMatchR](https://doi.org/10.1093/bioinformatics/btae011) | NCBI全文XML及提取文字；出版商PDF请求403，失败保留 |
| [siDirect 2.0](https://doi.org/10.1186/1471-2105-10-392) | NCBI全文XML、提取文字，以及出版商原始8页文字PDF |

原始XML在[acquisition](acquisition/)，实际请求及失败在[全文收据](acquisition_receipt.json)与[PDF收据](publisher_pdf_attempts.json)。最初调用的旧PMC OA API返回404；随后核实该接口已于2026-08-25停用，见[NCBI公告](https://pmc.ncbi.nlm.nih.gov/tools/oa-service/)。全文由仍可访问的NCBI efetch接口取得，没有绕过登录或付费限制。`prepare_small_library.py`保留首次获取过程，禁止覆盖现有材料；重新获取必须另存新目录，不能把新文件冒充本批原件。

XML原件完整保留；生成供检索的文本时提取了摘要和正文（含其中的文字图注），没有把文后参考文献表加入该文本，也没有识别原图或表格结构。siDirect另有完整8页PDF的文字索引。单次问答只读取实际检出的片段，不能因为保存了全文原件就声称模型读完了所有页面。

OligoFormer文档与源码固定为`e2f53ad63387bbe166bf123949151e2bc9bf6ec3`。SeedMatchR定义文档/源码固定为历史1.1.1（`b462d4a00520172622f9d8a5a8842d34442c2e68`）；没有把现行新版混入旧工具说明。原字节复用任务A已经核对的证据，仍分别标为官方文档或源码，不能说成实验结果。

siDirect的`*.pdf.pages.json`是pypdf6.10.0对全部8页实际提取的文字缓存，包含PDF指纹和提取代码指纹。服务器仅在原件和缓存均吻合时复用，避免免费实例反复解析复杂绘图。图像和表格结构没有识别，缓存不冒充另一份原PDF。原件、文字页和片段都随文库导出。

来源类别是明确标注的声明；文件一致性、DOI存在和引用编号合法均不能自动证明每句话得到原文支持。正式论文表述仍须逐条复核文意。本项目的来源核查记录不是外部论文，项目TPM设置不是文献中的实验结论。
