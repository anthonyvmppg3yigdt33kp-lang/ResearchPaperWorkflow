# v4.8 现实审查摘要

v4.8 已经具备研究工作流、方法资产、分析图、运行目录和证据合成的基础，但仍更像一个复杂框架，而不是一个可以稳定落地的科研生产系统。核心问题不是功能太少，而是边界不够硬：计划、dry-run、adapter、scaffold、真实可执行 wrapper、环境状态和 manuscript claim 之间没有足够清晰的生产分级。

v5 的目标是把系统收敛到一个可执行、可审计、可 fail-closed 的生产内核。新的主入口是：

```bash
paper-workflow target validate --target targets/examples/pbmc3k_t_subcluster_v5.yaml
paper-workflow target plan --target targets/examples/pbmc3k_t_subcluster_v5.yaml
paper-workflow target run --target targets/examples/pbmc3k_t_subcluster_v5.yaml
paper-workflow target evaluate --target targets/examples/pbmc3k_t_subcluster_v5.yaml
paper-workflow target package --target targets/examples/pbmc3k_t_subcluster_v5.yaml
```

本轮升级必须解决七个问题：QA 不能 fail-open；模块 registry 不能把资产数量误当生产能力；策略评估必须影响 graph/order/env；bulk/pseudobulk 环境缺口必须阻断生产图；外部代码必须转成真实 wrapper 或明确非生产；Windows 个人路径必须被拦截；文档不能把未验证内容写成已验证结论。

PBMC3K 示例是工作流验证 fixture，不是疾病机制项目。它只能支持 tutorial workflow validation 和 exploratory subcluster structure，不能支持疾病机制、临床 biomarker、治疗反应或因果免疫状态。
