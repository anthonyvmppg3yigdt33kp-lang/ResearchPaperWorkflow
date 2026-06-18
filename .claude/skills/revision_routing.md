---
name: revision_routing
description: Review response and revision routing — diagnose gate failures, generate revision plans, track commitment ledger. 修订路由。触发词：revision, review response, gate failure, 修订, 审稿, rebuttal.
version: "1.0"
paper_loop_stages: "15, 16, 17"
agent: team_orchestrator (routing), report_writer (execution)
type: skill
---

# Revision Routing Skill

Orchestrates the review-revision loop (Stages 15-17). Routes integrity gate failures to responsible agents. Manages the 5-cycle revision limit.

## Workflow
1. Diagnose gate failures → unified revision issues
2. Generate revision plan → per-issue actions with agent assignments
3. Apply revisions → `report_writer` executes; mark downstream stages stale
4. Re-review → `integrity_checker` verifies gates pass
5. Track → `commitment_ledger.csv`

## Integration
See `team_orchestrator.md` for full pipeline coordination spec. See `integrity_checker.md` for gate definitions. See `paper_loop.md` for stage sequencing.
