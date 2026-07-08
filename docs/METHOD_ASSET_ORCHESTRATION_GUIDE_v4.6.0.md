# Method-Asset Orchestration Practice Guide v4.6.0

v4.6.0 turns `code_library` from a folder of scripts into a selectable,
executable, auditable, and feedback-driven method knowledge base.

## Operating Rule

Start with available truth, not new code.

```text
question
-> data registry
-> module registry
-> environment registry and locks
-> capability selection
-> analysis graph
-> approved execution
-> source maps and evidence graph
-> feedback ledger and reviewed improvement proposal
```

## Minimal Task Packet

Before a real run, record:

```text
Mode: analysis_design_mode or execution_mode
Canonical root: papers/<paper_id>
Goal: biological or validation question
Allowed inputs: declared data paths only
Forbidden actions: package install, raw data mutation, writing outside run scope
Output path: results/runs/<run_id>
Evidence standard: workflow_test, analysis_ready, or manuscript_ready
Human checkpoint: approval required before --execute
Closeout: evaluate-run --write-report plus manifest review
```

## Prepare Data Truth

Real execution requires `papers/<paper_id>/data/data_registry/datasets.yaml`.
At minimum, declare:

- `dataset_id`
- `modality`
- `role`
- `path`
- `format`
- `immutable: true`
- `sample_mapping.status`
- files when a fixed manifest is required

Tutorial fixtures should use `role: tutorial_fixture` and
`sample_mapping.status: not_required_for_tutorial`. The executor reports these
runs as `evidence_grade: workflow_test`, not as project evidence.

## Inspect Capabilities

Use capability search before planning:

```bash
PYTHONPATH=src python -m paper_workflow.cli.main list-capabilities \
  --question "Seurat PBMC3K single-cell QC UMAP marker visualization" \
  --modality scrna \
  --json
```

Use modality filters such as `scrna`, `bulk_rnaseq`, `spatial`, and
`multiomics`. Spatial and communication queries return reviewer-risk warnings
for overclaiming colocalization, ligand-receptor inference, and causality.

## Plan A Bounded Graph

`plan-analysis --from-code-library` writes both `analysis_design.yaml` and
`analysis_graph.yaml`.

```bash
PYTHONPATH=src python -m paper_workflow.cli.main plan-analysis \
  --paper <paper_id> \
  --run-id <run_id> \
  --goal "Use the official Seurat PBMC3K workflow for QC, PCA, clustering, UMAP, and marker plots." \
  --modality scrna \
  --input data/raw/pbmc3k/filtered_gene_bc_matrices/hg19 \
  --primary-contrast "tutorial fixture; no disease contrast" \
  --from-code-library \
  --module-limit 1 \
  --set-current
```

Use `--module-limit 1` for upstream raw-input validation runs when only the
first selected module can consume the declared input directly. Leave the default
limit when the selected assets are all compatible with the declared graph.

## Execute Only After Approval

```bash
PYTHONPATH=src python -m paper_workflow.cli.main run-analysis \
  --paper <paper_id> \
  --run-id <run_id> \
  --execute \
  --approved \
  --set-current
```

The executor fails closed when approval, data registry, environment lock,
package availability, write scope, or source-map requirements are missing.
Do not disable those gates for production runs.

## Evaluate And Synthesize Evidence

```bash
PYTHONPATH=src python -m paper_workflow.cli.main evaluate-run \
  --paper <paper_id> \
  --run-id <run_id> \
  --write-report \
  --json
```

`--write-report` writes:

- `evaluation_report.yaml`
- `tables/evidence_matrix.tsv`
- `review/reviewer_risk_report.md`
- `brief/FIGURE_STORYLINE.md`
- `claims/claim_ledger.jsonl`

The evidence graph is a claim-boundary tool. It does not turn exploratory
figures into validated manuscript claims.

## Import External Code

External code enters quarantine first:

```bash
PYTHONPATH=src python -m paper_workflow.cli.main import-code-source \
  --github owner/repo \
  --source-id paper_author_method_v1 \
  --paper-doi 10.xxxx/example \
  --license "review_required"

PYTHONPATH=src python -m paper_workflow.cli.main review-code-source \
  --source-id paper_author_method_v1
```

This creates source manifests and review records. It never silently registers
new executable method assets.

Figure style references are similarly explicit:

```bash
PYTHONPATH=src python -m paper_workflow.cli.main register-figure-style \
  --source-id paper_author_method_v1 \
  --style-id nature_multi_panel_v1

PYTHONPATH=src python -m paper_workflow.cli.main list-figure-styles
```

## Feedback Loop

Every graph execution records module usage in
`code_library/module_usage_ledger.jsonl`.

```bash
PYTHONPATH=src python -m paper_workflow.cli.main summarize-module-usage \
  --module single_cell.seurat_pbmc3k_basic.v1

PYTHONPATH=src python -m paper_workflow.cli.main propose-module-improvement \
  --paper <paper_id> \
  --run-id <run_id>
```

`apply-module-improvement --approved` marks a proposal as approved for manual
implementation. It does not mutate `module_registry.yaml`.

## PBMC3K Validation Result

The v4.6.0 release was validated with the official Seurat PBMC3K tutorial data:

- strategy selected `single_cell.seurat_pbmc3k_basic.v1`;
- `--module-limit 1` produced a single executable graph node;
- real execution completed under `r_seurat_v5`;
- `DataRegistry` passed with tutorial-fixture boundaries;
- `EnvironmentRegistry` passed with `r_seurat_v5.lock.yaml`;
- evaluation status was `pass`;
- reproducibility grade was `locked`;
- evidence grade was `workflow_test`;
- generated outputs included QC table, cell retention table, cluster counts,
  marker presence table, QC violin, UMAP, marker FeaturePlot, Seurat RDS, and
  sessionInfo.

Observed PBMC3K summary:

```text
initial_cells: 2700
filtered_cells: 2638
clusters: 9
markers_present: MS4A1, GNLY, CD3E, CD14, FCER1A, FCGR3A, LYZ, PPBP, CD8A
```

## Required Release Checks

Run these before publishing a release:

```bash
PYTHONPATH=src python -m compileall -q src scripts tests
PYTHONPATH=src python scripts/ci_quality_check.py
PYTHONPATH=src python -m pytest -q
PYTHONPATH=src python -m paper_workflow.cli.main validate-contract --strict
PYTHONPATH=src python -m paper_workflow.cli.main doctor --json
PYTHONPATH=src python scripts/ci_cli_smoke.py
PYTHONPATH=src python scripts/ci_graph_dry_run.py --json
PYTHONPATH=src python -m pytest -q tests/test_method_assets.py
```

