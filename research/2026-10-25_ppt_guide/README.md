# PPT图册（2026-10-25）

[12页PDF图册](siRNA_Agent_PPT_Figure_Guide_20261025.pdf)：五张精简英文核心图、三项真实备份素材、两张原版记录图及逐图中文解释。

图内是可追溯的已有记录/数据；没有新增模型、评分、seed或近全长计算。英文图为Arial；中文说明用嵌入微软雅黑。

`figures/01–05`提供PNG/PDF/SVG；`SOURCE_MAP.md`解释每图的用途、结论和限制；`source_manifest.json`记录主版本与来源指纹。旧原件不改，三组独立评分和实测效力不在本批补写。

重排命令（在本目录，使用已安装ReportLab/PyPDF/Pillow和Poppler的Windows Python）：`python build_guide.py --repo <原仓库绝对路径> --tree source_git_tree.json --out <新输出路径>`。只读取已绑定的原文件，不执行模型或科学工具；原仓库输入不能被本脚本覆盖。
