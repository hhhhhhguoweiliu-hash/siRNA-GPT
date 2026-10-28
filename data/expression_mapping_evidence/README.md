# 当前表达映射来源

当前完整映射直接保存在`../expression.tsv.gz`的feature_id、approved_symbol、ENTREZID列；逐样本TPM按feature_id与公司TPM原值精确连接，不加总、不删后缀、不以P值挑代表。输入文件与SHA256在`../expression_provenance.json`。

`annotation_overrides_evidence.tsv`和`NCBI_gene_summary_mapping_overrides.json`为本次工作区v3核验保留的精确参考位置/链及别名核对证据。线粒体参考为NC_012920.1；保留已核验参考条目与基因关系，不仅按COX1等歧义符号模糊匹配。完整原注释和其余v3核验表保留在用户工作区`analysis_redraw_20261028_v3/`，本包不冒称已取得公司完整FASTA/GTF生成命令。

原43,385条摘要表保存在`../expression_legacy_20261016.tsv.gz`，`../provenance.json`为历史记录，未改。新作图来源以`../expression_provenance.json`为准。
