# R 环境设置说明

v5 不会在 agent 执行过程中静默安装 R 包。R 环境必须由用户或 CI 明确准备，然后用检查脚本验证。

## Seurat 环境

检查：

```bash
Rscript scripts/check_r_environment.R --json
```

查看安装建议：

```bash
Rscript scripts/bootstrap_r_seurat_env.R
```

建议包：

- Seurat
- SeuratObject
- Matrix
- ggplot2

## Bulk / pseudobulk 环境

检查：

```bash
Rscript scripts/check_r_bioc_environment.R --json
```

查看建议：

```bash
Rscript scripts/bootstrap_r_bulk_env.R
Rscript scripts/bootstrap_r_pseudobulk_env.R
```

缺少 DESeq2、edgeR、limma、fgsea、clusterProfiler、GSVA、WGCNA 等包时，相关模块在 v5 registry 中必须保持非生产可见或 environment blocked，不能进入生产图。

## 解释原则

如果本机没有 R 或 Seurat，这不是 workflow 通过，也不是 workflow 失败；它是环境阻断。正确状态是 `blocked` 或 `needs_fix`，并由 `qc/fail_closed_decision.yaml` 记录。
