# ResearchPaperWorkflow v5 User Guide

Use v5 when you want a bounded research workflow that can plan, execute, evaluate, and package a scientific analysis without promoting incomplete evidence into manuscript claims.

## Basic Pattern

```bash
paper-workflow target validate --target targets/examples/pbmc3k_t_subcluster_v5.yaml
paper-workflow target plan --target targets/examples/pbmc3k_t_subcluster_v5.yaml
paper-workflow target run --target targets/examples/pbmc3k_t_subcluster_v5.yaml
paper-workflow target evaluate --target targets/examples/pbmc3k_t_subcluster_v5.yaml
paper-workflow target package --target targets/examples/pbmc3k_t_subcluster_v5.yaml
```

Use `--approved --execute` only when the target data and environment are ready:

```bash
paper-workflow target run --target targets/examples/pbmc3k_t_subcluster_v5.yaml --approved --execute
```

Without `--execute`, the command plans and dry-runs graph packaging. With `--execute`, missing packages or data block the run.

## Prepare PBMC3K

```bash
Rscript scripts/download_pbmc3k_data.R data/raw/pbmc3k
Rscript scripts/check_r_environment.R --json
```

If R packages are missing, inspect:

```bash
Rscript scripts/bootstrap_r_seurat_env.R
```

Run installation manually in an approved R session.

## Read The Output

After a TargetTask run, inspect:

- `evaluation_report.yaml` for final status;
- `qc/fail_closed_decision.yaml` for blockers;
- `qc/next_analysis_plan.yaml` for next actions;
- `tables/evidence_matrix.tsv` for source-mapped evidence;
- `manuscript/results_skeleton.md` for what can and cannot be said.

Do not use `results_skeleton.md` as a scientific conclusion unless the final status is `pass`.

## Add A New TargetTask

Copy `targets/examples/pbmc3k_t_subcluster_v5.yaml` and change:

- `target_id`
- `title`
- `data`
- `environment.required_envs`
- `analysis_goal.allowed_claims`
- `analysis_goal.forbidden_claims`
- `workflow.required_modules`
- `quality_gates`

Keep `quality_gates.fail_closed`, `require_source_maps`, `require_claim_boundary`, and `require_no_personal_paths` set to `true`.

## Add A New Module

Each module needs:

- `module.yaml`
- real `main.py` or `main.R` entrypoint, or an explicit non-production grade;
- `README.md`
- `env_profile.yaml`
- source maps and manifests written by execution;
- a main registry entry with v5 fields.

Run:

```bash
python scripts/ci_module_grade_audit.py --strict --json
python -m paper_workflow.cli.main audit-method-assets --strict --show-warnings
```

## Release Checklist

Use the release gate commands in `ARCHITECTURE.md`. If any gate fails, do not tag a release. If R is unavailable locally, record that as an environment limitation rather than converting the missing R path into a pass.
