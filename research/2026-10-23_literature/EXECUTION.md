# 执行与失败保留

接手main1e4fe57，先记录04241c2的10项开发问题，再实现检索。所有程序检查均使用模拟模型或不调用模型；真实模型演示另存，不混入这些记录。

1. 首次取全文的旧PMC OA接口返回404；NCBI当前公告确认已经停用。改用官方efetch取得3篇全文XML并保存原字节。siDirect出版商PDF两条公开入口取得相同SHA256的8页原PDF；SeedMatchR出版商PDF403，未伪造PDF。
2. PDF检查器最初设置的解压上限拒绝siDirect正常绘图页，扩大到有界16MB解压/8MB页内容后，发现预检查重复解析复杂绘图导致25秒超时。读取原始内容流作大小预检查后，全8页实际提取成功；第6页原始解码内容5895666字节，未跳过。本地首次完整提取和缓存由`scripts/cache_seed_pdf.py`完成，缓存同时核对PDF、文字缓存及提取代码指纹，保留解析警告。
3. 初期SQLite连接未显式关闭，Windows临时检查目录清理报文件占用；已显式关闭连接。未删除或改变任何历史科研文件。
4. 首轮文库16项检查中“SeedMatchR旧版定义被中文问题检出”失败；按明确工具名优先相应资料后16项通过，未改预定问题或补造定义。随后增加HTTP导入及账号阻断保留两个计划题的检查；首次全套159项检查通过，日志和真实命令边界已保留。
5. 10个开发检查通过，包括实际HTTP导入9份材料、中文找英文、原页/片段对应、无证据不调用模型、损坏/图片PDF拒绝，以及完整文库重新导入/重建。它们不是人工判分，也不证明模型回答的科学质量。
6. 浏览器原标签已不存在，新打开的网站在唤醒后读取空白/超时；使用同一Edge的已记录浏览器接口和截图核对后，已请用户自己新开并登录。没有读取或请求其网站密码、模型密钥，没有改额度或绕过登录。

本地实际命令（Python为桌面提供的依赖环境，pypdf6.10.0；前端使用Node）：

```powershell
& 'C:\Users\86182\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' scripts/prepare_small_library.py
& 'C:\Users\86182\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' scripts/cache_seed_pdf.py
& 'C:\Users\86182\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' scripts/check_small_library.py
node --check library_ui.js
node test_browser_backup.cjs
```

初次全文获取脚本禁止覆盖本批已取得的原件；PDF出版商入口的补取收据单独保留。`cache_seed_pdf.py`是派生文字缓存重建，不是重新设计siRNA或执行科学模型。`check_small_library.py`不会运行真实模型。完整软件检查为`unittest discover -p 'test_*.py'`，Windows临时目录指定到工作区；逐次日志放offline。

## 最终复验与浏览器实测

代码修正后保留首轮记录，另跑第二轮：`unit_checks_02.txt/json`为159项检查，32.46秒，无错误/失败。`scripts/check_small_library.py verification_02`通过预定10项，输出另放`offline/verification_02/`，没有覆盖第一次记录。前端语法及浏览器备份检查通过。测试中的模型响应均明确模拟，没有本轮真实API问答。

本地先在受限进程启动测试服务，浏览器和本机连接受阻（WinError10013/连接超时）；改在经授权的正常进程运行同一现有应用，端口8895可访问，未改防火墙/登录/配额。Edge实际输入中文SeedMatchR问题，显示英文论文和1.1.1官方定义；打开真实片段text-c002可见g2-g8和reverseComplement源码。截图仅记录界面操作，不是论文科研图。生产网站仍为旧部署1f155cf，浏览器访问空白/超时，已请求用户自行新开并登录；没有绕过登录或手动用量确认。

旧54条原包再次核对SHA256仍为55664e58cea8181046ddc73c3740b73960589380d02b95719f3c6c0e1334e505。本轮没有修改其答案、失败、评分或工具结果。
