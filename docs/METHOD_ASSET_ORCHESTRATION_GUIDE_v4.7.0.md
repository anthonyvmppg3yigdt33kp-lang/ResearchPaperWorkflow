# Method-Asset Orchestration Practice Guide v4.7.0

## 1. Inspect Available Assets

Start by auditing the local method knowledge base:

```bash
PYTHONPATH=src python -m paper_workflow.cli.main audit-method-assets --strict --show-warnings
```

Open `code_library/modules/MODULE_SOURCE_CATALOG.md` to inspect each module's
purpose, script, delegated wrapper, function list, execution type, environment
lock, maturity, validation status, and claim boundary.

## 2. Ask Strategy Questions Before Planning

Use `list-capabilities` for method choice. The output now includes
`strategy_evaluation`:

```bash
PYTHONPATH=src python -m paper_workflow.cli.main list-capabilities \
  --question "Should I run pseudobulk DE or WGCNA for cell-type differential expression?" \
  --modality scrna \
  --json
```

Read these fields before accepting the plan:

- `question_type`
- `method_family`
- `decision`
- `prerequisites`
- `risks`
- `comparison_notes`
- `figure_role`

## 3. Plan With Bound Inputs

`plan-analysis --from-code-library` writes node input contracts into
`analysis_graph.yaml`:

```bash
PYTHONPATH=src python -m paper_workflow.cli.main plan-analysis \
  --paper <paper_id> \
  --run-id <run_id> \
  --goal "Run single-cell QC, UMAP, marker display, and decide downstream pseudobulk DE readiness." \
  --modality scrna \
  --input data/raw/pbmc3k/filtered_gene_bc_matrices/hg19 \
  --primary-contrast "tutorial fixture; no disease contrast" \
  --from-code-library \
  --module-limit 1 \
  --set-current
```

For real group inference, declare a paper-scoped data registry with immutable
paths and sample mapping before execution.

## 4. Execute Through The Graph Gate

Real execution requires approval:

```bash
PYTHONPATH=src python -m paper_workflow.cli.main run-analysis \
  --paper <paper_id> \
  --run-id <run_id> \
  --execute \
  --approved \
  --set-current
```

The executor supports `rscript`, `python`, `shell`, `bash`, and
`jupyter`/`ipynb` execution types. It blocks before running a command when
required node inputs are unresolved, environment locks are missing, packages are
unavailable, or the data registry fails.

## 5. Import External Code Safely

Clone and parse a GitHub method source without registering it:

```bash
PYTHONPATH=src python -m paper_workflow.cli.main import-code-source \
  --github https://github.com/<owner>/<repo> \
  --source-id reviewed_method_source_v1 \
  --clone \
  --license "requires_human_review" \
  --json
```

Review the generated packet:

```text
code_library/external_sources/<source_id>/source_manifest.yaml
code_library/external_sources/<source_id>/parsed_source_index.yaml
code_library/external_sources/<source_id>/module_proposals.yaml
code_library/external_sources/<source_id>/license_review.yaml
```

Promotion to `module_registry.yaml` remains a normal reviewed code change.

## 6. Validate Evidence

After execution:

```bash
PYTHONPATH=src python -m paper_workflow.cli.main evaluate-run \
  --paper <paper_id> \
  --run-id <run_id> \
  --write-report \
  --json
```

Treat PBMC3K and other tutorial runs as `workflow_test` evidence. Treat
dry-run wrappers and adapter contracts as readiness checks until real-data
execution, package validation, source maps, and reviewer-risk boundaries pass.

## 7. Release Checklist

Run before release:

```bash
PYTHONPATH=src python -m compileall -q src scripts tests
PYTHONPATH=src python scripts/ci_quality_check.py
PYTHONPATH=src python -m paper_workflow.cli.main audit-method-assets --strict --json
PYTHONPATH=src python -m paper_workflow.cli.main validate-contract --strict
PYTHONPATH=src python -m paper_workflow.cli.main doctor --json
PYTHONPATH=src python scripts/ci_cli_smoke.py
PYTHONPATH=src python scripts/ci_graph_dry_run.py --json
PYTHONPATH=src python -m pytest -q
```

On GitHub, verify that the CI run for the release commit passes, including the
mandatory R method contract job.
