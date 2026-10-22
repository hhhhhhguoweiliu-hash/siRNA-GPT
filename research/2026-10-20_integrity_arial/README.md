# 真实性与完整性审计；英文Arial新版图

当前材料有真实数据与运行依据，但不是完整的论文验证结果。用户要求已写入AGENTS和[长期准入规则](../../docs/RESEARCH_INTEGRITY.md)，同时保存为用户长期偏好。

## 本轮真实做了什么

- 对照公司原始 `C:\00000\ARPE RNA-seq\result\result\6_expression\expression\gene_tpm.xls`：唯一VEGFA行的8个逐样本值与作图底表全部完全一致；来源文件SHA256记录在审计中。这里只核对来源与算术，不把文件一致性当作物理实验真实性的独立认证。
- 重核37个历史固定文件、9条候选分数和方向、真实Auto的6项工具，以及新批54计划/逐条结果和ZIP CRC。没有新跑重型模型或代填科学评分。
- 新绘3张候选论文插图：系统示意、一例完整Auto、完整9候选/8皿基线背景。保持使用全部相应数据，未改变任何生物学数值。
- 将不完整三组评价的Figure4留在 `paper/diagnostics/`，从论文PDF排除。失败证据保留，不能挑12个可用重复单元画成完整质量结果。
- 图内文字、正式图注全部英文；真实Arial/Arial Bold，分图标签粗体，标题/表头合理加粗，常规文字5–7pt。PDF为三页可编辑矢量图，字体检查及实际页面尺寸单独保存。以前DejaVu Sans版保留为旧版本，不冒称Arial。

## 查看产物

- [3张候选论文插图PDF](paper/figures/Manuscript_Figures_Arial.pdf)。它们分别承担系统说明、单例执行和描述性背景，不能替代论文的独立质量/湿实验验证。
- [英文图与图注](paper/index.html)、[英文图注JSON](paper/figure_captions_en.json)、[完整底表](paper/data/)。
- [真实性审计](integrity_audit.json)、[字体验证](font_verification.json)、[图的准入分类](paper/manuscript_eligibility.json)、[字体与字重记录](paper/typography_audit.json)。
- [完整未过滤公司TPM表](source/gene_tpm_vendor.tsv.gz)、[字节一致回执](source/source_receipt.json)：gzip只压缩，不修改源表内容；不是只上传VEGFA一行，便于另一对话直接复核全表。

这里保留全部50,116行源记录及8个样本列；行数不解释为独立生物样本或全部唯一基因。VEGFA背景图只回答预先指定的VEGFA问题，使用完整8样本，不是挑选表达较好的样本。完整性按科学问题与预定分析判断，不要求一张单基因图画出全部基因，但绝不能漏掉应纳入的样本、组别或失败。
- [全部失败诊断图](paper/diagnostics/Figure4_development_evidence.png)：仅排障，不是质量比较图。

## 未完成以及如何完成

| 缺项 | 完成办法与门槛 | 分工 |
|---|---|---|
| 有效新开发批次 | 在现有服务部署已通过检查的诊断修复；先保存一条真实不完整原因，再冻结统一参数，另开完整6×3×3批次。预先规定基础设施错误与系统失败处理；正常题和必要证据需达到预定完整覆盖。旧失败不覆盖，不靠补成功案例拼接 | Codex负责代码、真实运行、校验、导出；账号真阻断时再说明具体操作 |
| 论文质量评价 | 由独立领域人员审核/冻结未见任务和答案锚点，完成盲评，再对完整预定数据分析与作图。当前6道已见开发题不变成独立正式测试题 | Codex整理；用户安排独立评审，评审真实评分 |
| 上游重型计算的独立复跑 | 官方权重/源码/参考版本及哈希固定，先官方示例，再当前全部9条或冻结的真实候选，保存完整stdout/输入输出与一致性检查 | Codex执行；缺资源或文件时如实报告。归档一致不冒充本轮重跑 |
| 用户真实文献候选 | 提供准确序列、链方向、末端/修饰及DOI/原文来源；逐条核对后冻结，不能用默认9条替代 | 用户提供准确材料，Codex导入核查 |
| 湿实验结果 | 按既定小规模方案完成真实测量和对照，保留全部预定样本、失败、排除理由及原始仪器文件，再作图 | 用户实际实验，Codex整理和分析 |

质量优越性图和湿实验图在这些条件完成前不生成。当前图数量不表示课题已经做完，也不承诺任何论文结论或录用。

## 复现命令

```powershell
python scripts/audit_research_integrity.py --vendor-tpm 'C:\00000\ARPE RNA-seq\result\result\6_expression\expression\gene_tpm.xls' --output research/new_integrity/audit.json
python -c "import sys,runpy; sys.path.insert(0,'.plot_deps'); sys.argv=['scripts/build_migration_figures.py','--output','research/new_integrity/paper','--combined-pdf']; runpy.run_path('scripts/build_migration_figures.py',run_name='__main__')"
```

需真实Arial字体及requirements-research.txt依赖。缺失字体或字形时报错，不静默替代。字体核查使用包含pypdf的Python运行 `scripts/verify_manuscript_fonts.py`；Poppler重新渲染PDF后目视检查。字体与字号问题在本地中间渲染修复，不修改原始数据；只有验证通过的最终版进入本目录和GitHub。

本轮不调用模型API，因此没有新增有效三组批次。软件状态与科学完成度分开：上一版产品131项检查已过；本轮新增实际数据/字体审计不当科研样本量。

PDF实际复核通过：3页均为嵌入的ArialMT/Arial-BoldMT，文字可提取，无中文字形；普通文字5–7pt、分图标签8pt，SVG文字可编辑。Poppler从最终PDF重新渲染后逐页目视检查。图中O2使用常规数字，避免系统Arial缺少Unicode下标字符而静默换字体。`paper/provenance.json`中的source_commit是出图前工作树基点；实际生成脚本与style文件各有SHA256，最终交付代码版本另见本轮根manifest。
