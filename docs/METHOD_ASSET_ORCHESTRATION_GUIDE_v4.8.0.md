# Method-Asset Orchestration Practice Guide v4.8.0

This guide is the practical path for turning reviewed literature code into
maintainable bioinformatics method assets.

## 1. Import A Source For Review

```powershell
$env:PYTHONPATH = "src"
python -m paper_workflow.cli.main import-code-source `
  --local "C:\path\to\reviewed-code" `
  --source-id reviewed_code_v1 `
  --license requires_human_review `
  --json
```

Expected review files:

- `source_manifest.yaml`
- `retained_files_manifest.yaml`
- `parsed_source_index.yaml`
- `method_blocks.yaml`
- `module_proposals.yaml`
- `license_review.yaml`

`method_blocks.yaml` is the method-understanding layer. Each block records the
source file, line range, detected calls, method family, inferred inputs/outputs,
hardcoded terms, disease/project terms, object terms, parameterization plan,
candidate module family, reviewer risk, claim boundary, and
`status: requires_human_review`.

## 2. Adapt A Reviewed Block

```powershell
python -m paper_workflow.cli.main adapt-method-block `
  --source-id reviewed_code_v1 `
  --block-id <block_id> `
  --module-id external.reviewed_code_v1.findmarkers.v1 `
  --family seurat_findmarkers_group_de `
  --approved-review `
  --json
```

The scaffold is written to:

```text
code_library/modules/external/<source_id>/<module_name>/
```

It contains `main.R`, `R/functions.R`, `module.yaml`, `env_profile.yaml`,
`README.md`, `PROVENANCE.md`, `tests/toy_input_manifest.yaml`, and
`tests/expected_outputs.yaml`.

By default, this does not write `module_registry.yaml`. If `--register` is used,
`license_review.yaml` must say `status: approved_for_adaptation`; the command
still writes only `registry_patch.yaml`.

## 3. Use Registered Method Assets

List capabilities:

```powershell
python -m paper_workflow.cli.main list-capabilities `
  --question "单细胞疾病组差异分析，比较 FindMarkers、pseudobulk、limma 和富集分析" `
  --modality scrna `
  --json
```

Plan a graph:

```powershell
python -m paper_workflow.cli.main plan-analysis `
  --paper test_paper `
  --run-id method_asset_demo_20260709_v1 `
  --goal "Run QC, clustering, FindMarkers, and enrichment with artifact binding." `
  --modality scrna `
  --input data/raw/input.rds `
  --from-code-library `
  --module-limit 4 `
  --set-current `
  --json
```

Review `analysis_graph.yaml`. Downstream inputs should show
`binding_source: upstream_output...` when upstream artifacts satisfy the input
contract.

## 4. Execute And Evaluate

```powershell
python -m paper_workflow.cli.main run-analysis `
  --paper test_paper `
  --run-id method_asset_demo_20260709_v1 `
  --execute `
  --approved `
  --set-current `
  --json

python -m paper_workflow.cli.main evaluate-run `
  --paper test_paper `
  --run-id method_asset_demo_20260709_v1 `
  --write-report `
  --json
```

The evaluator writes:

- `evaluation_report.yaml`
- `qc/bioinformatics_quality_report.yaml`
- `qc/next_analysis_plan.yaml`
- evidence synthesis outputs when source maps are present.

If R packages or data are missing, execution must be blocked explicitly. Do not
replace blocked execution with synthetic pass artifacts.

## 5. Claim Boundaries

- PBMC3K tutorial outputs are workflow validation only.
- FindMarkers disease-group comparisons are exploratory unless replicate-aware
  inference is documented.
- Pseudobulk or sample-level DE is preferred for disease-group inference when
  biological replicates and sample metadata are available.
- WGCNA does not replace primary group DE.
- Enrichment must follow a valid ranked gene table and record gene-set/database
  provenance.
- CellChat, NicheNet, and SCENIC-style outputs are hypothesis-generating unless
  independently validated.

## 6. Required Preflight

```powershell
python -m compileall -q src scripts tests
python scripts/ci_quality_check.py
python -m paper_workflow.cli.main validate-contract --strict
python -m paper_workflow.cli.main audit-method-assets --strict --show-warnings
python scripts/ci_graph_dry_run.py --json
python -m pytest -q
```

If R is available:

```powershell
Rscript scripts/ci_r_method_contract.R
```

## 7. v4.8.0 Acceptance Snapshot

- Local `lung-master` intake: 132 retained files, 70 parsed source scripts, 82
  method blocks.
- Observed method families: differential-expression post-processing,
  enrichment, percent-expression summaries, Seurat marker/feature plots,
  volcano plots, clinical/general plotting, and DESeq2 utility scripts.
- Observed project-specific terms are retained in provenance/review fields
  only, including LUAD, LUSC, Tumour/tumour, Healthy, Background, and NSCLC.
- PBMC3K tutorial run `pbmc3k_demo_20260709_v1`: execution `pass`, evidence
  grade `workflow_test`, bioinformatics QA `pass`, no Windows personal path leak
  in run artifacts.
- Do not promote the lung-master scaffold or PBMC3K tutorial outputs to
  publication-grade evidence without license approval, real project data,
  replicate/sample mapping, and manuscript-specific source-map review.
