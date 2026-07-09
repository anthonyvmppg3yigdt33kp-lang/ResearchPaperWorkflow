# V5 Productivity Scorecard

The v5 scorecard is implemented in `paper_workflow.monitoring.performance_ledger` and checked by `scripts/ci_performance_budget.py`.

| Criterion | Weight | Evidence |
|---|---:|---|
| Fail-closed QA | 20 | `run_quality_rules.py`, `result_run_manager.py`, `ci_supervision_failure_cases.py` |
| TargetTask entry | 15 | `paper-workflow target validate|plan|run|evaluate|package` |
| Production module ratio | 15 | v5 module registry grades and production gate |
| Environment truth | 15 | `environment_registry.yaml`, R check/bootstrap scripts |
| Seurat validation fixture | 15 | PBMC3K TargetTask and subcluster wrapper |
| External code wrapper | 10 | `external.lung_master.de_table_standardizer.v1` |
| Documentation truth | 10 | v5 docs and release notes |

Target: at least 75/100.

Expected v5 score after local gates: 100/100 for code/docs readiness criteria. This is not a claim that every biological analysis is production validated. It means the kernel has a bounded executable path, explicit gates, and no known release-blocking mismatch in the repository.

Runtime caveat:

Real Seurat execution depends on local R packages and PBMC3K data. If missing, the correct status is blocked or needs_fix.
