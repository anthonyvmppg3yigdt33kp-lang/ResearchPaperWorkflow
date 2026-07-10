# Seurat Subcluster Programs

This module is the v5 TargetTask validation asset for PBMC3K T-cell-like
subcluster refinement. It accepts a Seurat RDS object, subsets cells by a
declared marker panel or metadata identity, explores a resolution grid, computes
subcluster markers, scores simple gene programs, and writes source maps plus QA
manifests.

Marker-driven subsetting requires at least two declared markers and two
T/NK lineage anchors (`CD3D`, `CD3E`, `NKG7`, `GNLY`) per cell by default.
Both thresholds and the anchor panel are configurable. Metadata-based subsetting remains available
when a reviewed parent identity is already stored in the object. Resolution
selection prefers the first stable cluster-count plateau and otherwise uses the
middle eligible resolution; the selected value and reason are written to QC.

Boundary: this is a workflow-test and exploratory single-cell module. PBMC3K is
an official tutorial fixture, so outputs cannot support disease mechanism,
clinical biomarker, treatment-response, or causal immune-state claims.

Dry-run:

```bash
Rscript code_library/modules/single_cell/seurat_subcluster_programs/main.R \
  --dry-run \
  --out tmp/seurat_subcluster_dry \
  --run-id seurat_subcluster_dry
```

Real run requires `Seurat`, `Matrix`, and `ggplot2` in `r_seurat_v5`.
