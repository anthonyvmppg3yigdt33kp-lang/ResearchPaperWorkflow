# Quick Reference v4.3

Use natural-language requests through Codex or Claude as the default interface.

## Start A New Project

```text
I have not started yet. Create a ResearchPaperWorkflow project for [topic],
targeting [journal]. Stop at the first checkpoint and report the paper_id,
initial research question, missing inputs, and decision I need to approve.
```

## Continue One Safe Step

```text
Continue paper_id [id] by one safe workflow step. Stop at checkpoint, missing
input, pending harness, quality-gate failure, or stale artifact. Report current
stage truth and next action.
```

## Validate State

```text
Audit paper_id [id]. Confirm completed stages have real outputs, stage results,
quality-gate results, checkpoint approval where required, and no unpropagated
artifact drift.
```

## Current References

- `README.md`
- `USER_GUIDE.md`
- `ARCHITECTURE.md`
- `docs/OPERATION_GUIDE_ZH.md`
- `docs/NEXT_GEN_V4_TRUTH_LAYER.md`
