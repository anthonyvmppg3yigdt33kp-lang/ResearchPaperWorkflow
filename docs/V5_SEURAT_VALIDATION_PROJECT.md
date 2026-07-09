# V5 Seurat Validation Project

The v5 reference project is:

```text
targets/examples/pbmc3k_t_subcluster_v5.yaml
```

It uses the official Seurat PBMC3K tutorial dataset as a workflow fixture. The data can be downloaded with:

```bash
Rscript scripts/download_pbmc3k_data.R data/raw/pbmc3k
```

## Modules

1. `single_cell.seurat_pbmc3k_basic.v1`
2. `single_cell.seurat_subcluster_programs.v1`

The first module performs the basic PBMC3K Seurat tutorial workflow and writes a Seurat RDS object. The second module performs T-cell-like subsetting, resolution-grid subclustering, marker table generation, program scoring, figures, source maps, session info, and manifests.

## Claim Boundary

Allowed:

- workflow validation;
- exploratory tutorial subcluster structure;
- method packet demonstration.

Forbidden:

- disease mechanism;
- clinical biomarker;
- treatment response;
- causal immune state.

## Validation Modes

Dry-run mode checks graph wiring and evidence packet generation without requiring Seurat packages.

Real execution requires:

- `Rscript`;
- `Seurat`;
- `SeuratObject`;
- `Matrix`;
- `ggplot2`;
- PBMC3K 10X matrix files.

If any are missing, v5 must block or return `needs_fix`; it must not report a final pass.
