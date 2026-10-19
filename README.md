# siRNA-GPT · 云端研究工作台

缺氧RPE / VEGFA siRNA筛选辅助Agent，沿用v0.3.2对话界面。当前云端版用于单个研究者：网站密码访问、豆包自然语言交互、候选/转录本核对、已有官方工具结果读取、ARPE-19表达背景关联及证据报告。

## 云端能力边界

OligoFormer/RNA-FM和SeedMatchR的重计算环境仍在本机。本服务明确使用已核对的历史评分和seed结果，不宣称在免费实例重新运行了这些工具。新序列可做信息/转录本核对；新序列完整评分需接入计算后台。对话及生成文件存于实例临时磁盘，重启/休眠可能丢失，重要报告应下载留存。

## Render部署配置

已包含render.yaml。若使用Blueprint，Render读取这个文件；若已经创建Web Service，请核对同样配置：

| 设置 | 值 |
| --- | --- |
| Runtime | Python |
| Build Command | `pip install -r requirements.txt` |
| Start Command | `gunicorn cloud:application --bind 0.0.0.0:$PORT --workers 1 --threads 4 --timeout 180 --access-logfile -` |
| Health Check Path | `/healthz` |
| Instance | Free（演示用途） |

必须只启用1个worker，因为当前任务状态保存在单进程内存。不要开启多个实例。

## 环境变量

| 名称 | 内容 |
| --- | --- |
| `ARK_API_KEY` | 火山方舟API密钥，仅在Render后台填写 |
| `ARK_MODEL` | `doubao-seed-2-1-pro-260915`，或你有权限的实际模型/接入点ID |
| `WEB_PASSWORD` | 至少16字符的网站密码；Blueprint可自动生成 |

登录用户名固定为 `research`。网站密码与API密钥用途不同。不要把它们提交到仓库。已禁止从网页修改云端密钥；连接检查保留。

`RENDER_EXTERNAL_HOSTNAME` / `RENDER_EXTERNAL_URL`由Render提供，用于域名与请求来源检查。`PORT`也由平台提供，不需要手动写死。

部署成功只代表网站运行，不能据此判定豆包API已获授权。必须在站内点“检查连接”，收到真实函数调用响应后才能显示连接已验证。此前403 AccessDenied仍需按服务端说明核对云端模型/项目权限。

## 本地验证

`python -m unittest test_core test_model_client test_http test_responses_integration test_conversation test_api_diagnostics test_cloud -v`

工具协议检查使用明确的测试模型响应，科学核对/历史导入实际执行。Windows无法直接运行Gunicorn，WSGI入口通过无网络测试验证，最终Gunicorn启动需由Render构建日志确认。

## 原文与工具

交互方式参考CRISPR-GPT：https://doi.org/10.1038/s41551-025-01463-z 。科学方法与限制详见data/provenance.json及生成报告。代码只整合官方工具输出，没有发明新脱靶算法或将模型分数当作敲低率。
