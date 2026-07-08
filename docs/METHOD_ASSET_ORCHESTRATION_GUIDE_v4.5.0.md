# Method-Asset Orchestration Guide v4.5.0

This guide describes the v4.5 path for turning the code library into a
selectable, executable, and auditable method knowledge base.

## Core Rule

Do not start by writing new analysis code. Start by asking what data, environment,
and method assets are already available.

```text
research question
-> data inventory
-> module registry
-> environment registry
-> method selection report
-> analysis graph
-> approved graph execution
-> node manifests and source maps
-> run evaluation
```

## Main Files

- `code_library/module_registry.yaml`: canonical method-asset registry.
- `code_library/environment_registry.yaml`: declared execution environments.
- `config/data_governance_contract.yaml`: data truth requirements.
- `config/environment_contract.yaml`: environment and package boundaries.
- `config/module_registry_schema.yaml`: required method-asset fields.
- `config/analysis_graph_schema.yaml`: run graph contract.
- `results/runs/<run_id>/analysis_graph.yaml`: run-scoped executable DAG.
- `results/runs/<run_id>/method_selection_report.md`: planner rationale.
- `results/runs/<run_id>/nodes/<node_id>/node_manifest.yaml`: node execution truth.

## Single-Cell PBMC3K Validation Path

1. Download the official tutorial data into a paper project under `data/raw/`.

```bash
curl -L "https://cf.10xgenomics.com/samples/cell/pbmc3k/pbmc3k_filtered_gene_bc_matrices.tar.gz" \
  -o papers/<paper_id>/data/raw/pbmc3k/pbmc3k_filtered_gene_bc_matrices.tar.gz
```

2. Extract the tarball so the 10X directory exists at:

```text
papers/<paper_id>/data/raw/pbmc3k/filtered_gene_bc_matrices/hg19
```

3. Ask the strategy layer what is available:

```bash
paper-workflow list-capabilities \
  --question "Seurat PBMC3K single-cell QC UMAP marker visualization" \
  --modality scrna
```

4. Write the run-scoped graph:

```bash
paper-workflow plan-analysis \
  --paper <paper_id> \
  --run-id pbmc3k_seurat_20260708_v1 \
  --goal "Use the official Seurat PBMC3K workflow for QC, PCA, clustering, UMAP, and marker plots." \
  --modality scrna \
  --input data/raw/pbmc3k/filtered_gene_bc_matrices/hg19 \
  --primary-contrast "tutorial fixture; no disease contrast" \
  --from-code-library \
  --set-current
```

5. Execute only after approval:

```bash
paper-workflow run-analysis \
  --paper <paper_id> \
  --run-id pbmc3k_seurat_20260708_v1 \
  --approved \
  --execute \
  --set-current
```

Real execution is fail-closed at three layers: CLI, adapter dispatch, and
analysis graph execution. `--execute` without `--approved` exits before any
analysis command is launched, and direct graph execution records
`block_reason: user_approval_required` when approval is missing.

## Production Gates

Before real method-asset execution, the graph executor now evaluates three
contracts:

- `DataRegistry`: `data/data_registry/datasets.yaml` must declare datasets,
  immutable raw paths, sample mapping status, file hashes, and statistical
  units. Group inference without sample/patient mapping is blocked.
- `EnvironmentRegistry`: runner, required package availability, and lock-file
  policy are checked without installing packages. If `require_env_lock: true`
  and the lock file is absent, execution is blocked; if the graph explicitly
  sets `require_env_lock: false`, the run may proceed as exploratory and is
  marked with `environment_reproducibility_grade: degraded`.
- `SourceMapValidator`: run-level source maps are aggregated from node-level
  `figure_source_map.yaml` and `table_source_map.yaml`, preserving each node's
  `statistical_unit`, `source_data`, `method`, and `claim_boundary`.

Environment inspection commands:

```bash
paper-workflow list-envs
paper-workflow inspect-env r_seurat_v5
paper-workflow doctor-env r_seurat_v5 --require-lock
paper-workflow validate-env --module single_cell.seurat_pbmc3k_basic.v1
```

`evaluate-run --json` reports node counts, source-map validity,
environment/data reproducibility fields, evidence grade, and reviewer-risk
counts. A run can execute successfully and still be `degraded_exploratory` or
`needs_fix` if provenance is insufficient for manuscript evidence.

6. Audit the run:

```bash
paper-workflow evaluate-run \
  --paper <paper_id> \
  --run-id pbmc3k_seurat_20260708_v1 \
  --write-report
```

## Expected Outputs

For the Seurat PBMC3K module, a successful run writes:

- `qc/qc_metrics.csv`
- `qc/cell_retention.csv`
- `tables/cluster_counts.csv`
- `tables/marker_presence.csv`
- `figures/qc_violin.png`
- `figures/umap_clusters.png`
- `figures/feature_plot_markers.png`
- `objects/pbmc3k_seurat_basic.rds`
- `logs/sessionInfo.txt`
- node and run manifests
- figure and table source maps

## Claim Boundary

PBMC3K is a tutorial fixture. It validates workflow wiring and method-asset
execution. It does not support disease, diagnostic, or mechanism claims.

## Batch 7 Single-Cell Asset Split

The local `code_library/r/bioinformatics_analysis.R` functions are now exposed
as first-class method assets with independent module directories, metadata,
environment profiles, dry-run fixtures, and thin `main.R` wrappers:

- `single_cell.seurat_qc.v1`
- `single_cell.seurat_integration_harmony.v1`
- `single_cell.seurat_clustering_umap.v1`
- `single_cell.marker_feature_plot.v1`
- `single_cell.pseudobulk_aggregate.v1`
- `single_cell.pseudobulk_deseq2.v1`

Each wrapper supports:

```bash
Rscript code_library/modules/single_cell/<module>/main.R \
  --dry-run \
  --out <tmp_out> \
  --run-id toy_<module>
```

Dry-run writes `node_manifest.yaml`, `parameters.yaml`,
`outputs_manifest.yaml`, `logs/sessionInfo.txt`, and node-level figure/table
source maps. Real execution still requires an approved graph, declared inputs,
and an environment that satisfies the package and lock policy.

## Batch 8 Bulk RNA-seq Assets

Bulk RNA-seq now has publication-oriented method assets in addition to the
Python pilot:

- `bulk_rnaseq.deseq2_de.v1`
- `bulk_rnaseq.limma_voom_de.v1`
- `bulk_rnaseq.wgcna.v1`
- `bulk_rnaseq.fgsea_enrichment.v1`
- `bulk_rnaseq.immune_deconvolution_adapter.v1`

These modules are intentionally stricter than the Python pilot. They declare
contrast/design requirements, required R packages, reviewer risks, and claim
boundaries. Their dry-run wrappers verify output contracts without treating the
result as publication evidence.

```bash
paper-workflow list-modules --modality bulk_rnaseq
paper-workflow list-capabilities \
  --question "publication-oriented bulk RNA-seq DESeq2 limma WGCNA fgsea" \
  --modality bulk_rnaseq
```
