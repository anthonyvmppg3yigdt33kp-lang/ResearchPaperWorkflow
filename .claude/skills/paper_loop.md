---
name: paper_loop
description: Paper loop engine for the V4 20-stage manuscript pipeline with 44 integrity gates, stale detection, revision routing, and AIGC text hygiene review.
version: "4.0"
paper_loop_stages: "1-20"
agent: team_orchestrator
type: skill
---

# Paper Loop Skill

Canonical pipeline definition for ResearchPaperWorkflow V4. All framework agents and skills defer to this stage order unless the user explicitly chooses a reduced workflow.

## 20 Stage Pipeline

| Phase | Stages |
|-------|--------|
| 1. Research & Planning | `select_topic` -> `target_journal` + `literature_search` -> `formulate_hypotheses` -> `design_analysis_plan` |
| 2. Data & Methods | `data_audit` -> `figure_planning` -> `run_analysis` -> `verify_methods` |
| 3. Writing | `write_methods` -> `write_results` -> `write_introduction` -> `write_discussion` |
| 4. Assembly & Review | `assemble_manuscript` -> `aigc_humanizer_review` -> `integrity_check` |
| 5. Revision | `internal_review` -> `apply_revision` -> `re_review` (max 5 cycles) |
| 6. Finalize | `finalize` |

## Loop Model

```text
observe -> decide -> run -> verify -> record -> mark_stale -> diagnose -> repeat
```

## V4 Checkpoints

- `select_topic`: approve research direction.
- `formulate_hypotheses`: approve hypotheses and paper scope.
- `design_analysis_plan`: freeze SAP before primary analysis.
- `figure_planning`: approve figure story and required analyses.
- `internal_review`: approve revision priority matrix.
- `finalize`: approve submission package.

## Integrity Gates

V4 has 44 gates across:

- citation and claim integrity
- clinical design
- data and bias
- statistics and model
- single-cell and spatial omics
- AI/ML
- AIGC text hygiene
- format and completeness

Critical failures block the pipeline. High and medium failures must be documented or revised before final submission.

## AIGC Text Hygiene

`aigc_humanizer_review` runs after manuscript assembly and before `integrity_check`. It generates:

- `review/aigc_detection_report.md`
- `review/humanizer_revision_plan.yaml`
- `manuscript/manuscript_humanized.md`

The scan is a responsible text hygiene triage. It must not claim authorship attribution.

## Usage

```python
from paper_workflow.engine import PaperLoopEngine

engine = PaperLoopEngine(project_root, paper_id="my_paper")
stage = engine.decide_next_stage()
```

See `docs/V4_INSTALLATION_AND_USAGE_GUIDE.md` for full installation, migration, and execution steps.
