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
