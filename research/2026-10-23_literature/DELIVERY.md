# 上传、本地验证、部署与真实演示分别记录

- 接手main：`1e4fe57a059fbf19cf32b4685cc249a3d297e98c`。
- 10题开发检查协议先行提交：`04241c2`。
- 本地验证：最终文库10项自动核查、159项软件检查和前端检查通过；前次日志另存。不代表独立科研评分。
- GitHub源码与本批材料：**已上传主分支与原任务分支**，代码提交`ba94bb4da1b3794d5ea29984a5d8577660806c26`，实际读取远端两分支一致。[完整材料](https://github.com/hhhhhhguoweiliu-hash/siRNA-GPT/tree/main/research/2026-10-23_literature)、[来源清单](https://github.com/hhhhhhguoweiliu-hash/siRNA-GPT/blob/main/references/sirna_library/sources.json)。[main自动检查](https://github.com/hhhhhhguoweiliu-hash/siRNA-GPT/actions/runs/39979868750)及[任务分支检查](https://github.com/hhhhhhguoweiliu-hash/siRNA-GPT/actions/runs/39979869502)均已成功。
- 原网站部署：**尚未更新为本轮版本**。本次提交含`[skip render]`，Render实际查询仍为旧`1f155cf2ed051f85a440f8162488989a462f2b14`。需要恢复网页登录并先保存已有记录，不能把旧服务可访问当新功能已部署。
- 真实两题演示：尚未运行；没有用模拟模型结果替代。
- 当前具体人工步骤：已请求在Edge手动打开原站并用原账号登录，暂不启动任务。其余工作持续。

后续每项只按实际收据更新；保留旧54条及其失败。没有新科学分数、风险重排序、微调或湿实验扩张。

## Google Drive同步

沿用[已有项目目录](https://drive.google.com/drive/folders/1wLVEtggMk_qtcnBqesMwxb90wyaCz83i)，未改变共享权限：

- [文库、原件、来源与开发检查完整包](https://drive.google.com/file/d/1tHrQRfe3k-zIJR07qqWaz7YEa4ASa8Qv/view)，2296409字节；上传后重新取得文件名、大小和父目录，均一致。本地ZIP SHA256为`b687b442e26f24ff1c55e9ced222bab9215087bfd42cee495e830dd3e7bbba78`。连接工具没有返回远端SHA256，未声称已核对远端全部字节。
- [可读功能与检查说明](https://drive.google.com/file/d/1aDTHRK_J22luN-Pku3vAIti25APJmLTe/view)。原来源和10项逐题片段也已随GitHub和ZIP提供；未把模拟响应作为真实演示上传。
- [上传及未完成事项说明](https://drive.google.com/file/d/1OwS8jpBrwo2NtkVQZAaWNVPNYv3iqd0O/view)。功能说明正文已从Drive重新读取，确认确有导入、检索、检查及未运行边界。

`FILE_MANIFEST.json`记录本机及Drive ZIP的文件字节；[COMMITTED_FILE_MANIFEST.json](COMMITTED_FILE_MANIFEST.json)另外记录ba94bb4实际Git文件对象。50份文件逐一核对，7份源代码只存在Windows与Git的换行差异，无其他内容差异；文献原件、实际片段和开发记录字节一致。没有把不同换行的文件声称为同一字节哈希。

下一步只需在Edge新开原网站，用research与原密码登录，暂不启动任务。随后执行端先保存旧记录，再更新原服务，并通过“确认用量→运行两题文库演示”完成真实记录。不要点“三组开发预评估”的启动按钮。无需发送密码或密钥。
