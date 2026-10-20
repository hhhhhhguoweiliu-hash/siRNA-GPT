# 历史官方工具适配器

根目录oligo_worker.py和seed_worker.R来自此前本地0.3.2实现，按core.py现有接口放置，方便继续核验接入；本次没有重跑它们或新增预测结果。它们是适配/IO代码，不是重新实现科学算法。

依赖目录需满足data/provenance.json以及docs/DATA_PROVENANCE.md。另需官方RNA-FM源码、官方示例、prepared/utr_manifest_representative.tsv等实际引用文件。历史R脚本带有用户Windows库路径，接手时改为明确的环境配置并验证跨平台行为。

科学环境与轻量云端requirements.txt分开。历史CPU运行记录为Python3.8.16、torch2.2.1+cpu、numpy1.24.4、pandas2.0.3、SeedMatchR1.1.1；这些是历史环境事实，不承诺在其他Python/OS能直接安装。先在目标环境做官方示例和数值核对，再接真实任务。

不要把1.2GB预训练权重提交Git，不在未验证前放开云端live模式，不把适配器文件存在等同于已部署可访问计算后台。
