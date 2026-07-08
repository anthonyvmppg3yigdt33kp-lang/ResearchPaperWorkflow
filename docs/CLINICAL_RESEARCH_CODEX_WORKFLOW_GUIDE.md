# Clinical Research Codex Workflow Guide

Created: 2026-07-07

This guide describes the optimized human-Codex operating pattern for clinical
bioinformatics projects using ResearchPaperWorkflow.

## 1. Default Interaction Packet

Use this structure for non-trivial work:

```text
Mode:
Canonical root:
Paper:
Goal:
Allowed inputs:
Forbidden actions:
Output path:
Evidence standard:
Human checkpoint:
Closeout:
```

Do not start a broad task with only "continue" or "fully optimize". Pick a
mode and a paper root.

## 2. Modes

| Mode | Use When | Default Boundary |
|---|---|---|
| `exploration_mode` | Locate state, files, evidence, next safe action | read-only |
| `analysis_design_mode` | Design statistical/bioinformatics analysis | no execution |
| `execution_mode` | Run an approved bounded task | write only under `results/runs/<run_id>/` |
| `closeout_audit_mode` | Submission/checkpoint/claim audit | no new analysis |
| `ppt_briefing_mode` | Build a slide brief from source maps | no guessed figures |
| `retrospective_mode` | Convert repeated friction into durable rules | docs/contracts/skills only |

## 3. Result Layout

Every new analysis run should use:

```text
papers/<paper_id>/
  results/
    current_run.yaml
    current/RUN_POINTER.txt
    runs/<run_id>/
      intent_packet.md
      analysis_design.yaml
      run_manifest.yaml
      parameters.yaml
      inputs_manifest.yaml
      outputs_manifest.yaml
      evaluation_report.yaml
      figure_source_map.yaml
      table_source_map.yaml
      logs/
      qc/
      tables/
      figures/
```

`results/current_run.yaml` is the continuation pointer. Do not infer "current"
from the newest timestamped folder.

## 4. Status And Planning Commands

Create a run:

```bash
python -m paper_workflow.cli.main new-run \
  --paper <paper_id> \
  --run-id bulk_de_20260707_v1 \
  --mode analysis_design_mode \
  --set-current
```

Prepare an analysis design without running analysis:

```bash
python -m paper_workflow.cli.main plan-analysis \
  --paper <paper_id> \
  --run-id bulk_de_20260707_v1 \
  --goal "Design a bulk RNA-seq differential expression pilot." \
  --modality bulk_rnaseq \
  --input data/pilot/counts.csv \
  --input data/pilot/metadata.csv \
  --primary-contrast "IgG4_ROD vs MALT_L" \
  --execution-backend python_builtin_pilot \
  --set-current
```

Report current state:

```bash
python -m paper_workflow.cli.main brief-status --paper <paper_id>
```

Evaluate a run package:

```bash
python -m paper_workflow.cli.main evaluate-run \
  --paper <paper_id> \
  --run-id bulk_de_20260707_v1 \
  --write-report
```

## 5. Bulk Pilot Execution

The built-in pilot backend is only a workflow test harness. It reads a count
matrix CSV and metadata CSV, then produces sample-level pilot outputs without R
or external downloads.

Required count matrix:

```text
gene,A1,A2,A3,B1,B2,B3
CXCL13,120,130,125,10,12,9
```

Required metadata:

```text
sample_id,condition,batch
A1,IgG4_ROD,b1
B1,MALT_L,b1
```

Run the pilot only after approval:

```bash
python -m paper_workflow.cli.main run-analysis \
  --paper <paper_id> \
  --run-id bulk_de_20260707_v1 \
  --execute \
  --approved \
  --backend python_builtin_pilot \
  --set-current
```

The pilot writes:

- `tables/differential_expression_pilot.csv`
- `qc/sample_qc.csv`
- `qc/bulk_pilot_qc_report.md`
- `qc/pilot_quality_report.yaml`
- `figures/volcano_plot.svg`
- `figures/deg_heatmap.svg`
- `figure_source_map.yaml`
- `table_source_map.yaml`

Scientific boundary: these are workflow-quality pilot outputs. Publication
claims still require a setup-controlled DESeq2/edgeR/limma pipeline and final
closeout audit.

## 6. When Not To Execute

Do not run analysis if:

- the design has no user approval;
- the statistical unit is unclear;
- the count matrix or metadata cannot be mapped to sample IDs;
- dependencies require installation during agent execution;
- expected outputs would be written outside `results/runs/<run_id>/`;
- the project passport says `stale_stages` and the task is checkpoint
  promotion rather than exploration.

## 7. Closeout

Each substantive task should end with:

```text
Mode used:
Files read:
Files changed:
Commands run:
Checks run:
Current truth source:
Risks:
Next safe action:
Ratchet improvement:
```

For scientific work also state:

```text
Statistical unit:
Claim boundary:
Source maps:
Whether workflow stage truth changed:
```

## 8. Release Preflight

Before opening a PR or publishing a release, run:

```bash
python -m compileall -q src
python scripts/ci_quality_check.py
python scripts/ci_cli_smoke.py
python -m pytest -q
```

GitHub Actions runs the same checks from `.github/workflows/ci.yml` on pull
requests and pushes to `master` or `codex/**` branches.

The quality gate checks:

- YAML parse status for `config/` and `.github/workflows/`;
- required collaboration modes and pipeline profiles;
- result-write policy and current-run contract;
- bioinformatics analysis-design contract;
- curated method-asset registry and legacy code-library capability registry;
- large-file guard outside excluded runtime/output directories.

## 9. Code Library And Method-Asset Registries

Use `code_library/module_registry.yaml` as the first lookup surface when an
analysis agent needs to choose executable or auditable local method assets. Use
`config/code_library_registry.yaml` only for broader external capability
discovery and dependency/reference decisions. The method-asset registry records:

- modality and analysis step;
- input/output schema;
- environment profile;
- execution contract when available;
- reviewer value and reviewer risk;
- claim boundary;
- figure/table outputs and source-map requirements;
- validation status and method maturity.

The external capability registry records:

- source URL;
- analysis area;
- use class such as dependency adapter, R setup dependency, external tool, or
  reference index;
- capability tags for routing;
- local status and initial ingestion decision.

Registry entries are not vendored code. The default policy is:

```text
dependency_or_adapter_first
license review before vendoring
no dataset mirroring
no large binary mirroring
retained-file manifest required for snapshots
commit or release pin required for snapshots
```

This keeps capability routing broad while preventing uncontrolled repository
copying into clinical research projects.
