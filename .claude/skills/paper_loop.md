---
name: paper_loop
description: Paper loop engine — 18-stage manuscript pipeline with integrity gates, stale detection, and revision routing. 论文循环引擎。触发词：paper loop, manuscript pipeline, integrity gate, stale detection, revision routing.
version: "1.0"
paper_loop_stages: "1-18"
agent: team_orchestrator
type: skill
---

# Paper Loop Skill

Canonical pipeline definition for the 18-stage paper workflow. All other framework skills delegate stage sequencing to this skill.

## 18 Stage Pipeline

| Phase | Stages |
|-------|--------|
| 1. Research & Planning | `select_topic` → `target_journal` || `literature_search` → `formulate_hypotheses` |
| 2. Data & Methods | `data_audit` → `figure_planning` → `run_analysis` → `verify_methods` |
| 3. Writing | `write_methods` → `write_results` → `write_introduction` → `write_discussion` |
| 4. Assembly & Review | `assemble_manuscript` → `integrity_check` → `internal_review` |
| 5. Revision | `apply_revision` → `re_review` (max 5 cycles) |
| 6. Finalize | `finalize` |

## Loop Model
```
observe → decide → run → verify → record → mark_stale → diagnose → repeat
```

## Passport System
- `project_passport.yaml` — Project identity
- `artifact_ledger.jsonl` — Append-only artifact hash log
- `checkpoint_ledger.jsonl` — User-approved checkpoints
- `integrity_ledger.jsonl` — Integrity gate events

## Integrity Gates (16 rules)
| Severity | Count | Rules |
|----------|-------|-------|
| CRITICAL | 5 | bibtex, citation traceability, Results no-cite, claim-artifact binding, figure refs |
| HIGH | 8 | data/code availability, no local paths, parameters, limitations, no overinterpretation, statistics, pseudoreplication |
| MEDIUM | 3 | section length, no bullets, figure count |

## Usage
```python
from paper_workflow.engine import PaperLoopEngine
engine = PaperLoopEngine(project_root, paper_id="my_paper")
stage = engine.decide_next_stage()
```

See `AGENTS.md` for full pipeline specification, agent invocation rules, and quality gate protocol.
