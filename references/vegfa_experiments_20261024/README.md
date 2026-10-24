# 三篇指定实验文献的原件与读取范围

本目录只增加12:15复核指定的三篇，不是全siRNA文献库。当前sources.json导入3份材料，与原9份合计12份；对应6篇不同论文，不把重复格式或官方源码算独立论文。

| 原文 | 实际得到的材料 | 定位与限制 |
|---|---|---|
| Chen 2013，10.2147/IJN.S39622 | 官方PMC完整XML，109162字节；提取正文文字、表格文字和图注 | chen2013_locators.json的xml-block编号/XPath/节名；纯文本没有PDF页码；未将图像读数转换成新数据 |
| Osipova 2020，10.3390/pharmaceutics12010039 | 官方PMC完整XML，118222字节；提取正文文字、表格文字和图注 | osipova2020_locators.json；原文27bp双链按原方向保存，不擅自截成19nt；第7天稳定性不是敲低读数 |
| Kleinman 2008，10.1038/nature06765 | 公开机构库作者稿PDF，513529字节、15页，含Online Methods | PDF实际页码，不是出版方定稿。第1页明确不含补充材料；第14页方法已视觉核对。没有补充序列表，不补造具体双链 |

每份导入原件SHA256在sources.json；XML原件指纹、访问时间在acquisition_receipt.json；PDF下载来源/重定向及字节数在kleinman_author_pdf_receipt.json。PDF取得时间采用实际下载文件的最后写入时间另记来源，初始下载收据没有时间字段。

保留真实失败及纠正：PMC网页曾返回验证页，未交互验证码；Nature读取失败、Europe PMC全文接口失败见kleinman_fulltext_attempt.json。起初PMC efetch只有Kleinman摘要，最初收据过早标为全文；初始收据和sources_initial_abstract_only.json保留，修正收据明确无body。随后从UNCG机构库取得真实作者稿，最终导入改用PDF，原摘要XML/文字仍保留，不冒称补充表已取得。

PDF页文字缓存由现有pdf_text_worker.py对原PDF冷提取，保存原件及提取器代码指纹；不是人工编辑过的正文。最终文库导出/导入检查见[本轮离线记录](../../research/2026-10-24_followup/offline/verification_02/focused_checks.json)。服务器新上传仍是临时实例文件，应导出；不宣称永久保存。

实验条件和1–3条范围内的2条序列参考：[证据表](../../research/2026-10-24_followup/experimental_literature_evidence.json)、[序列](../../research/2026-10-24_followup/literature_reference_sequences.json)。文献实验结果与本项目历史计算/尚未进行的实验分开。
