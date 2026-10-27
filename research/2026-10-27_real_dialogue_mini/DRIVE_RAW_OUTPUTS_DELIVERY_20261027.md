# 原始三组输出Drive交付：未经总册排版的原件

2026-10-27，北京时间。用户明确澄清需要普通模型、Agent、固定脚本当时直接产生的最原始完整回答，而非重新排版的PDF；此前只改PDF文件名没有满足该要求。

## 已上传并读回元数据

1. [完整原始运行ZIP](https://drive.google.com/file/d/1tTjWgpIvMrTyJt4vLAVmSPJyuPOkzB_6/view?usp=drivesdk)
   - model_and_tool_records_original.zip，9814625字节、1550文件。
   - 本地原件SHA256：512ab027fddd8c1ecabda20b7243a610c2f14a07a80130e832eebe083ed0c2c3。
   - 与本目录raw/内文件逐字节保持原样上传，含27位置的原始模型请求/响应、工具返回、程序结果及多轮过程。62次物理响应的原始文件均保留。

2. [原始结果JSON](https://drive.google.com/file/d/1cK16skh_7adRWGSxrnO1xdPeb-UX_hg5/view?usp=drivesdk)
   - results_original.json，3495823字节。
   - 本地原件SHA256：f443d6f358a3c63f45eeef0906ae968f74f231534eb3c5276207767a14c2b9a3。
   - 原27条任务记录，不改字段、文字或换行。

3. [便于直接阅读的逐字TXT包](https://drive.google.com/file/d/1rpfDSs3nZv5mjDlNk07UhrwWb89x28NN/view?usp=drivesdk)
   - answers_verbatim_txt.zip，50283字节。
   - 本地SHA256：c2737a445f9274574a3f208ebdc7a01ccc3d344d16a7b1abb9de544dd0071919。
   - 这是明确标注的逐字提取副本，不是替代上面两份原件。按普通模型、Agent、固定脚本分3目录；每轮实际交付33份TXT，另保留21份已保存的每轮最终模型文字。
   - 每个TXT只编码保存的answer或raw_model_answer字符串，不加标题、说明、分隔或末尾换行；原模型自己输出的Markdown照原样保留。逐文件重新读取并与JSON对应字段相等检查通过。
   - Agent的模型原文与实际交付分别放置，误拦截或程序错误不事后消除。21份最终文字不是实际模型请求数；完整62请求仍见第一份ZIP。
   - SOURCE_MANIFEST.json位于包中，记录每份来源字段、任务/轮次及文本哈希；解释不插入回答TXT。

Drive父目录仍为既有AI for biomedical discovery，ID为1wLVEtggMk_qtcnBqesMwxb90wyaCz83i。三个文件都经Drive元数据读回，名称、大小和父目录一致；未改变分享权限。没有取得远端SHA256回下载验证，不据元数据冒称远端字节核验。

原始材料均来自mini_real_20261027_061408、源码6c13c57，原结果提交4244ac0。没有新模型调用、重算、评分或原文改写；旧PDF仍保留，但不是本次用户所要求的原始记录。
