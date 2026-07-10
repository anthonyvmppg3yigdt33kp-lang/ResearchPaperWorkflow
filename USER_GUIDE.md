# ResearchPaperWorkflow v5.1 User Guide

Use v5.1 when you want to start from a research question and obtain a bounded plan, real execution route, quality decision, and manuscript packet without promoting incomplete evidence into claims.

## Researcher Pattern

```bash
paper-workflow research validate --intent intents/examples/pbmc3k_t_subcluster_intent.yaml
paper-workflow research start --intent intents/examples/pbmc3k_t_subcluster_intent.yaml
paper-workflow research analyze --intent intents/examples/pbmc3k_t_subcluster_intent.yaml
paper-workflow research review --intent intents/examples/pbmc3k_t_subcluster_intent.yaml
paper-workflow research write --intent intents/examples/pbmc3k_t_subcluster_intent.yaml
paper-workflow research status --intent intents/examples/pbmc3k_t_subcluster_intent.yaml
```

Start writes the scientific assessment, method alternatives, Figure plan, compiled TargetTask, and dashboard. Analyze without `--execute` remains a graph dry run. Analyze with `--approved --execute` uses the production kernel and may still block on data, environment, module, or QA gates.

## TargetTask Expert Pattern

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

## Add A Research Intent

Copy `intents/examples/pbmc3k_t_subcluster_intent.yaml` and set:

- the scientific question and project goal;
- data path, modality, format, sample mapping, and replicate status;
- expected figures, tables, and reports;
- optional required modules only when method review has already occurred;
- Figure messages and required evidence;
- the strongest defensible claim boundary.

Review `strategy_simulation.yaml` before approving execution. A deferred method is a scientific or environment requirement, not an invitation to silently substitute a weaker method.

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
