# 证据检索与报告保真度：低成本补强任务

2026-10-27（北京时间）。所审提交 `bfa1a0d19f5e207fc0ef4804b14c89ae7834a965`。先读[科研决定与Codex任务](../../docs/reviews/20261027_evidence_fidelity_and_independent_checks_tasks.md)。

本目录是执行方案，不是完成结果。采用L1、条件化L2，L3优先选原始逐样本TPM及seed精确计数两项，L4只做有限离线控制。OligoFormer另列可选，不启动付费问答/云算力。

- `input_inventory.json`：已实际找到并核对指纹的原始TPM、UTR参考及映射；模型权重仅核对存在与大小。
- `acceptance_plan.json`：优先级、10条guide范围、禁止错误断言与待执行状态。
- `validation_results_template.csv`：只有表头，不含伪造复算结果。

L2自洽不等于外部数值正确；L3是独立代码路径核验，不是生物学效力/安全性验证，也不自动成为独立研究者盲评。旧结果、原分和失败保留，数字不同不得改规则凑一致。
