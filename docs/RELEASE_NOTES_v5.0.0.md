# ResearchPaperWorkflow v5.0.0 Release Notes

v5.0.0 is a production-kernel upgrade. It introduces a unified TargetTask path, fail-closed run evaluation, explicit module production grading, environment-aware graph execution, and evidence-bound manuscript packets.

## Added

- `paper-workflow target validate|plan|run|evaluate|package`
- `targets/examples/pbmc3k_t_subcluster_v5.yaml`
- `paper_workflow.target_task`
- `paper_workflow.manuscript`
- `paper_workflow.monitoring`
- `single_cell.seurat_subcluster_programs.v1`
- `external.lung_master.de_table_standardizer.v1`
- `config/target_task.schema.yaml`
- R environment check/bootstrap scripts
- PBMC3K download helper
- CI gates for module grade audit, supervision failure cases, TargetTask smoke, Seurat subcluster smoke, and performance budget

## Changed

- Version metadata updated to `5.0.0`.
- Module registry schema upgraded to `module_registry.v5`.
- Environment registry schema upgraded to `environment_registry.v5`.
- Source-map validation now requires `claim_boundary` for tables as well as figures.
- Result evaluation writes `qc/fail_closed_decision.yaml`.
- Module selection includes production grade, environment status, and production gate.
- Analysis graph execution blocks production-disallowed modules when executing.
- Active README, architecture, and user guide now describe v5 current truth.

## Claim Boundary

PBMC3K is a workflow validation fixture only. The release does not claim disease-mechanism or clinical validation from PBMC3K outputs.

## Release Gate

Publish only after local and GitHub checks pass. If R or Seurat is unavailable, report that as an environment blocker; do not convert it into a pass.

Local validation on 2026-07-09:

- `python -m compileall -q src scripts tests`: pass
- `python -m pytest -q`: 148 passed, 2 skipped
- `python scripts/ci_quality_check.py --json`: pass
- `python scripts/ci_module_grade_audit.py --strict --json`: pass
- `python scripts/ci_supervision_failure_cases.py --json`: pass
- `python scripts/ci_pbmc3k_target_task.py --json`: pass, `fake_pass=false`, dry-run package status `degraded_exploratory`
- `python scripts/ci_performance_budget.py --json`: pass, score 100/100
- `python -m paper_workflow.cli.main validate-contract --strict`: pass
- `python -m paper_workflow.cli.main audit-method-assets --strict --show-warnings`: no issues, warnings retained for non-publication-grade dry-run/adapter assets
- `Rscript scripts/check_r_environment.R --json`: pass on the local R 4.5.3 environment
- `Rscript scripts/ci_seurat_subcluster_smoke.R`: pass
- `paper-workflow target run --approved --execute` with PBMC3K data absent: blocked, not pass
