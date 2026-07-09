# V5 Baseline Truth

Current active version: 5.0.0.

Current production-kernel entry:

```bash
paper-workflow target validate|plan|run|evaluate|package --target targets/examples/pbmc3k_t_subcluster_v5.yaml
```

Current reference target:

```text
targets/examples/pbmc3k_t_subcluster_v5.yaml
```

Current required checks:

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

Current truth boundaries:

- PBMC3K is a tutorial fixture.
- Missing R/Seurat/data is an environment blocker.
- `pass` requires bioinformatics QA pass.
- Manuscript result conclusions require final pass.
- Historical v4 docs are archives.
