# ResearchPaperWorkflow v5.0.0

ResearchPaperWorkflow v5.0.0 is a fail-closed research production workflow kernel. It keeps paper writing, omics analysis, evidence synthesis, and release work in one auditable system, but it does not treat a plan, scaffold, dry-run wrapper, or attractive draft as current scientific truth.

[![Version](https://img.shields.io/badge/Version-5.0.0-blue.svg)]()
[![Kernel](https://img.shields.io/badge/TargetTask-fail--closed-green.svg)]()

## What Changed In v5

v5 replaces the previous "complex framework with many components" posture with a concrete TargetTask execution path:

```bash
paper-workflow target validate --target targets/examples/pbmc3k_t_subcluster_v5.yaml
paper-workflow target plan --target targets/examples/pbmc3k_t_subcluster_v5.yaml
paper-workflow target run --target targets/examples/pbmc3k_t_subcluster_v5.yaml
paper-workflow target evaluate --target targets/examples/pbmc3k_t_subcluster_v5.yaml
paper-workflow target package --target targets/examples/pbmc3k_t_subcluster_v5.yaml
```

The v5 production kernel adds:

- fail-closed evaluation through `qc/fail_closed_decision.yaml`;
- explicit module grades: `production_capable_real_wrapper`, `validated_workflow_pilot`, `dry_run_contract`, `adapter_contract`, `scaffold_only`, `planning_contract`, `blocked_environment`, `retired`;
- environment-aware graph execution so blocked R/Bioconductor modules do not enter production-visible plans;
- a PBMC3K Seurat TargetTask fixture that validates the workflow mechanics on official tutorial data without making disease or clinical claims;
- a real Seurat subcluster/program wrapper and a real external DE-table standardizer;
- evidence-bound manuscript packet generation: methods draft, results skeleton, figure storyline, evidence matrix, claim ledger, reviewer risk report;
- CI gates for module grading, fail-closed supervision cases, TargetTask smoke, and productivity budget.

## Current Claim Boundary

The included PBMC3K workflow is a tutorial-fixture validation project. It can support workflow validation and exploratory tutorial subcluster structure. It cannot support disease mechanism, clinical biomarker, treatment response, or causal immune-state claims.

If Seurat, Rscript, PBMC3K data, source maps, session info, data registry hash, or claim boundaries are missing, v5 must report `blocked` or `needs_fix`; it must not produce a final pass or manuscript conclusion paragraph.

## Install

```bash
python -m pip install -e ".[dev]"
```

Optional R checks:

```bash
Rscript scripts/check_r_environment.R --json
Rscript scripts/check_r_bioc_environment.R --json
```

The bootstrap scripts print approved install plans; they do not silently mutate the machine environment:

```bash
Rscript scripts/bootstrap_r_seurat_env.R
Rscript scripts/bootstrap_r_bulk_env.R
Rscript scripts/bootstrap_r_pseudobulk_env.R
```

## PBMC3K TargetTask

Download the public tutorial data only when you intend to execute the real Seurat path:

```bash
Rscript scripts/download_pbmc3k_data.R data/raw/pbmc3k
```

Then run the v5 TargetTask:

```bash
paper-workflow target validate --target targets/examples/pbmc3k_t_subcluster_v5.yaml
paper-workflow target plan --target targets/examples/pbmc3k_t_subcluster_v5.yaml
paper-workflow target run --target targets/examples/pbmc3k_t_subcluster_v5.yaml --approved --execute
paper-workflow target evaluate --target targets/examples/pbmc3k_t_subcluster_v5.yaml
paper-workflow target package --target targets/examples/pbmc3k_t_subcluster_v5.yaml
```

Without `--execute`, `target run` performs graph dry-run packaging. With `--execute`, missing runtime packages or data block the run instead of creating fake success artifacts.

## Production Gates

Run these before opening a release PR or publishing a tag:

```bash
python -m compileall -q src scripts tests
python scripts/ci_quality_check.py --json
python scripts/ci_module_grade_audit.py --strict --json
python scripts/ci_supervision_failure_cases.py --json
python scripts/ci_graph_dry_run.py --json
python scripts/ci_pbmc3k_target_task.py --json
python scripts/ci_performance_budget.py --json
python -m pytest -q
```

R-dependent checks are separate because they depend on local R availability:

```bash
Rscript scripts/ci_seurat_subcluster_smoke.R
Rscript scripts/ci_pbmc3k_target_task.R
```

## Documentation

Current v5 documents:

- [v5 production-kernel reform plan](docs/V5_PRODUCTION_KERNEL_REFORM_PLAN.md)
- [v5 TargetTask design](docs/V5_TARGET_TASK_DESIGN.md)
- [v5 Seurat validation project](docs/V5_SEURAT_VALIDATION_PROJECT.md)
- [R environment setup](docs/R_ENVIRONMENT_SETUP_ZH.md)
- [v5 baseline truth](docs/V5_BASELINE_TRUTH.md)
- [v5 productivity scorecard](docs/V5_PRODUCTIVITY_SCORECARD.md)
- [v5 release notes](docs/RELEASE_NOTES_v5.0.0.md)

Historical v4.x architecture and release notes remain in `docs/` as archives, not as the current operating contract.
