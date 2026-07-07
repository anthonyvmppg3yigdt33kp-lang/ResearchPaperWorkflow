# ResearchPaperWorkflow v4.4.0 Release Notes

Date: 2026-07-07

## Summary

v4.4.0 upgrades ResearchPaperWorkflow from a full-pipeline manuscript engine into
a more controllable clinical research collaboration system. The release adds
mode routing, run-scoped outputs, analysis-design checkpoints, a built-in bulk
RNA-seq pilot executor, curated code-library routing, and CI preflight checks.

## Major Changes

- Added collaboration modes for bounded human-Codex work:
  `exploration_mode`, `analysis_design_mode`, `execution_mode`,
  `closeout_audit_mode`, `ppt_briefing_mode`, and `retrospective_mode`.
- Added result-run management under `results/runs/<run_id>/` with
  `results/current_run.yaml` and `results/current/RUN_POINTER.txt`.
- Added CLI commands:
  `new-run`, `set-current-run`, `plan-analysis`, `run-analysis`,
  `brief-status`, and `evaluate-run`.
- Added an analysis-design contract and adapter layer that blocks real
  execution until human approval and required design fields are resolved.
- Added a built-in bulk RNA-seq Python pilot backend for scoped workflow tests,
  quality reports, source maps, and preview figures without external package
  installation.
- Added contract files for result writing, visualization, bioinformatics
  methods, reporting, workflow modes, and code-library routing.
- Added a curated code-library registry for single-cell, spatial, multi-omics,
  metabolomics, Mendelian randomization, enrichment, and agent-skill discovery.
- Added CI workflow and local preflight scripts for compile checks, YAML/config
  validation, large-file guards, CLI smoke, and pytest.
- Added a practical clinical research Codex workflow guide.

## Scientific Boundaries

- The built-in bulk RNA-seq backend is a workflow pilot, not a publication-grade
  DESeq2/edgeR/limma replacement.
- Publication claims still require a setup-controlled analysis environment,
  source maps, manifest review, and closeout audit.
- Registry entries are capability references or dependency targets, not vendored
  third-party code. Vendoring requires license review, retained-file manifest,
  and commit/release pinning.

## Release Preflight

Run before PR merge or GitHub release:

```bash
python -m compileall -q src
python scripts/ci_quality_check.py
python scripts/ci_cli_smoke.py
python -m pytest -q
```

