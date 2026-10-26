# VEGFA基线图的实际作图数据

用户提供的图为VEGFA gene TPM常氧/缺氧散点图，图中均值20.10、102.39，均值比5.09。

- `VEGFA_TPM_plot_data.xlsx`：两列Prism数据、8个样本长表、描述性均值和中文来源说明。
- `VEGFA_TPM_Prism.csv`：可直接导入的两列数据。同行不代表配对。
- `source.tsv`：从GitHub main真实源表读取的内容，去掉BOM并统一为LF换行，数值未改。
- `build_workbook.py`：只整理源表与计算描述性均值，不运行模型或科学预测。

源文件：`research/2026-10-20_integrity_arial/paper/data/VEGFA_eight_samples_TPM.tsv`；读取时Git blob为`f4a644cc55909f01a14fcffe5b7b430048c758ad`。

同一培养批次，每状态4皿、分别提RNA，未转染、无siRNA；缺氧为1% O2、连续24小时。不是4轮独立培养，不根据编号自动配对。此表不新增检验、干预效力或独立评价结论。
