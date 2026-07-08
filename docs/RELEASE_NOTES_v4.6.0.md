# ResearchPaperWorkflow v4.6.0 Release Notes

Release date: 2026-07-09

v4.6.0 hardens the v4.5 method-asset orchestration work into a production-style
analysis system. The release focuses on bounded execution, multi-omics method
coverage, evidence synthesis, external code intake, feedback routing, CI, and a
real PBMC3K validation run.

## Added

- AI harness method-asset routing for capability listing, module inspection,
  analysis planning, gated execution, and run evaluation.
- Split single-cell assets for Seurat QC, Harmony integration, clustering/UMAP,
  marker FeaturePlot, pseudobulk aggregation, and pseudobulk DESeq2 contracts.
- Bulk RNA-seq method assets for DESeq2, limma-voom, WGCNA, fgsea enrichment,
  immune deconvolution, and the Python pilot.
- Spatial and communication assets for spatial QC, spatial FeaturePlot, domain
  detection, deconvolution adapters, ligand-receptor adapters, CellChat, and
  NicheNet.
- Evidence graph synthesis with evidence matrix, reviewer-risk report, figure
  storyline, and claim ledger outputs.
- External code source import and review commands plus a figure style registry.
- Module usage ledger and reviewed improvement proposal commands.
- Production CI jobs for Python tests, method-asset schema checks, CLI smoke,
  graph dry-run, optional R smoke, and light security checks.
- `plan-analysis --module-limit` for bounded strategy plans when only a subset
  of selected assets can consume the current input directly.
- R environment lock files for currently validated Seurat, Harmony, spatial,
  and communication environments.

## Changed

- Version metadata updated to `4.6.0`.
- README and configuration now describe v4.6.0 as the current release line.
- Real graph execution keeps `require_user_approval`, `require_data_registry`,
  and `require_env_lock` enabled by default.
- PBMC3K validation is explicitly classified as `workflow_test` evidence.

## Validation

PBMC3K end-to-end validation used the official Seurat PBMC3K tutorial page and
the 10X PBMC3K filtered gene-barcode matrix tarball.

Observed execution:

```text
paper_id: pbmc3k_validation_20260709
run_id: pbmc3k_validation_20260709_v1
selected module: single_cell.seurat_pbmc3k_basic.v1
execution status: completed
evaluation status: pass
reproducibility grade: locked
evidence grade: workflow_test
initial cells: 2700
filtered cells: 2638
clusters: 9
source map status: pass
```

Generated outputs included QC metrics, cell retention, cluster counts, marker
presence, QC violin plot, UMAP plot, marker FeaturePlot, Seurat RDS, sessionInfo,
node/run manifests, aggregate source maps, evidence matrix, reviewer-risk
report, figure storyline, and claim ledger.

## Compatibility Notes

- Existing v4.5 run-scoped layouts remain compatible.
- Historical v4.5 documentation is retained, but current entry points link to
  the v4.6.0 practice guide and architecture document.
- R environments that do not yet have all required packages installed still fail
  closed during real execution.
- `doctor --json` may report degraded fast-context availability when the MCP
  tool is not exposed to the current agent session; the fallback policy uses
  `rg` plus direct file reads.

