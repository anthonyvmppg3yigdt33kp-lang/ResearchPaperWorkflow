# ResearchPaperWorkflow v5.1.0

ResearchPaperWorkflow v5.1.0 is a researcher-facing, fail-closed workflow for biomedical and bioinformatics projects. A scientific question is compiled into a method comparison, Figure-first plan, TargetTask, real execution graph, quality decision, evidence matrix, and manuscript packet. Plans, dry runs, scaffolds, and tutorial fixtures are never promoted to scientific truth.

[![Version](https://img.shields.io/badge/Version-5.1.0-blue.svg)]()
[![Kernel](https://img.shields.io/badge/TargetTask-fail--closed-green.svg)]()
[![Research](https://img.shields.io/badge/Research_Intent-v1-teal.svg)]()

## Researcher Short Path

Start from a scientific intent rather than module names:

```bash
paper-workflow research validate --intent intents/examples/pbmc3k_t_subcluster_intent.yaml
paper-workflow research start --intent intents/examples/pbmc3k_t_subcluster_intent.yaml
paper-workflow research analyze --intent intents/examples/pbmc3k_t_subcluster_intent.yaml
paper-workflow research review --intent intents/examples/pbmc3k_t_subcluster_intent.yaml
paper-workflow research write --intent intents/examples/pbmc3k_t_subcluster_intent.yaml
paper-workflow research package --intent intents/examples/pbmc3k_t_subcluster_intent.yaml
paper-workflow research status --intent intents/examples/pbmc3k_t_subcluster_intent.yaml
```

`research start` writes the following project-scoped artifacts before execution:

- `scientific_assessment.yaml`: facts, assumptions, unknowns, decisions, missing prerequisites, and claim boundary;
- `strategy_simulation.yaml`: recommended, deferred, and planning-only methods with statistical units and reviewer risks;
- `figure_plan.yaml` and `FIGURE_PLAN.md`: scientific message and evidence requirements before module stacking;
- `target_task.yaml`: the compiled production contract;
- `RESEARCH_DASHBOARD.md`: current evidence, blockers, next best actions, and publication readiness.

An intent can also be initialized from the command line:

```bash
paper-workflow research start \
  --project-id my_scrna_project \
  --question "Identify disease-associated immune cell states" \
  --modality single_cell \
  --input data/my_project.rds \
  --dataset-id my_scrna_v1 \
  --format seurat_rds
```

This creates a reviewable intent and plan. It does not run analysis. Real execution still requires `research analyze --approved --execute`.

## What Changed In v5.1

- connected `AIWorkflowHarness` to TargetTask and Research Intent execution instead of declaration-only routing;
- added a method knowledge base that records what each method solves, does not solve, requires, and may claim;
- activated reusable local experience reminders for pseudoreplication, network overclaim, external scaffolds, and Figure-first design;
- added researcher-facing strategy simulation, Figure-first planning, and a compact project dashboard;
- bound TargetTask artifacts to `workflow_contract.yaml` and its 20-stage truth chain;
- fixed FindMarkers classification as exploratory cell-level DE rather than bulk DE;
- added fail-closed Seurat subcluster QA for marker columns, program scores, resolution selection, figures, objects, and session information;
- replaced the previous maximum-cluster resolution choice with a documented lower-resolution plateau preference;
- added CI coverage for the complete Research Intent to TargetTask planning path.

## TargetTask Expert Path

The lower-level production kernel remains available:

```bash
paper-workflow target validate --target targets/examples/pbmc3k_t_subcluster_v5.yaml
paper-workflow target plan --target targets/examples/pbmc3k_t_subcluster_v5.yaml
paper-workflow target run --target targets/examples/pbmc3k_t_subcluster_v5.yaml
paper-workflow target evaluate --target targets/examples/pbmc3k_t_subcluster_v5.yaml
paper-workflow target package --target targets/examples/pbmc3k_t_subcluster_v5.yaml
```

The production kernel enforces module grades, environment gates, data contracts, approval, source maps, scientific QA, and claim boundaries. Adapter contracts, scaffolds, planning contracts, and environment-blocked modules cannot enter real production execution.

## Scientific Boundaries

- `FindMarkers` supports exploratory cell-level marker screening; it does not replace sample-level disease inference.
- Replicate-aware pseudobulk is preferred for cell-type disease contrasts when sample mapping and biological replicates exist.
- Enrichment requires a reviewed ranked-gene statistic and database provenance.
- WGCNA does not replace primary differential expression.
- CellChat, NicheNet, and related network methods are hypothesis-generating without orthogonal validation.
- PBMC3K is an official tutorial fixture. It cannot support disease, clinical, treatment, or causal claims.

Missing data, R packages, source maps, session information, claim boundaries, or required result columns produce `blocked` or `needs_fix`; they never produce a final pass.

## Install

```bash
python -m pip install -e ".[dev]"
```

The package uses a `src/` layout. Run `paper-workflow` after installation. For source-local diagnostics without installation, set `PYTHONPATH=src` so an older global checkout cannot be imported accidentally.

Optional R checks:

```bash
Rscript scripts/check_r_environment.R --json
Rscript scripts/check_r_bioc_environment.R --json
```

Bootstrap scripts print install plans; they do not silently modify the machine:

```bash
Rscript scripts/bootstrap_r_seurat_env.R
Rscript scripts/bootstrap_r_bulk_env.R
Rscript scripts/bootstrap_r_pseudobulk_env.R
```

## PBMC3K Validation

Download the public tutorial data only when real validation is intended:

```bash
Rscript scripts/download_pbmc3k_data.R data/raw/pbmc3k
```

Then run either the researcher path or TargetTask path with `--approved --execute`. Without `--execute`, the workflow performs planning or graph packaging. Missing runtime packages or data must block execution instead of creating fake success artifacts.

The v5.1 release evidence is summarized in [`validation/pbmc3k_v5_1/validation_summary.yaml`](validation/pbmc3k_v5_1/validation_summary.yaml). It records a real two-node Seurat run, fail-closed statuses, executed parameters, runtime, scientific workflow-test metrics, and hashes without committing the tutorial data or large RDS files.

## Release Gates

```bash
python -m compileall -q src scripts tests
python scripts/ci_quality_check.py --json
python scripts/ci_module_grade_audit.py --strict --json
python scripts/ci_supervision_failure_cases.py --json
python scripts/ci_research_experience.py --json
python scripts/ci_graph_dry_run.py --json
python scripts/ci_pbmc3k_target_task.py --json
python scripts/ci_performance_budget.py --json
python -m paper_workflow.cli.main validate-contract --strict
python -m pytest --basetemp .pytest_tmp -q
```

R-dependent checks:

```bash
Rscript scripts/ci_r_method_contract.R
Rscript scripts/ci_seurat_subcluster_smoke.R
Rscript scripts/ci_pbmc3k_target_task.R
```

## Documentation

- [v5.1 tuning plan](docs/V5_1_RESEARCHER_EXPERIENCE_TUNING_PLAN.md)
- [v5.1 acceptance matrix](docs/V5_1_ACCEPTANCE_MATRIX.md)
- [v5.1 productivity scorecard](docs/V5_1_PRODUCTIVITY_SCORECARD.md)
- [v5.1 release notes](docs/RELEASE_NOTES_v5.1.0.md)
- [v5 TargetTask design](docs/V5_TARGET_TASK_DESIGN.md)
- [v5 Seurat validation project](docs/V5_SEURAT_VALIDATION_PROJECT.md)
- [R environment setup](docs/R_ENVIRONMENT_SETUP_ZH.md)
- [v5.0 baseline truth](docs/V5_BASELINE_TRUTH.md)

Historical versioned documents remain as archives. `README.md`, `AGENTS.md`, `AGENT_ROLES.md`, `workflow_contract.yaml`, and `config/default_config.yaml` define the current operating contract.
