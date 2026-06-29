# Release Notes: v4.3.0

Release focus: documentation alignment for the current 20-stage truth-layer
workflow and natural-language Claude/Codex operation.

## What Changed

- Rewrote `ARCHITECTURE.md` as the canonical V4.3 architecture reference.
- Rewrote `USER_GUIDE.md` around model-operated, natural-language workflow use.
- Added `docs/OPERATION_GUIDE_ZH.md`, a unified Chinese operation guide that
  merges the former AI harness interaction guide and clinician/graduate-student
  guide.
- Kept backward-compatible guide links by replacing the two old Chinese guide
  files with pointers to the unified guide.
- Updated README documentation links so the default path starts from V4.3 docs,
  not historical documents.
- Bumped package and config version metadata to `4.3.0`.

## User Impact

- Clinicians and graduate students can now describe work to Codex or Claude in
  natural language without learning lower-level Python commands.
- The documentation now explains the four-layer architecture, AI harness,
  agent-cluster routing, loop state machine, checkpoint policy, artifact ledger,
  stale propagation, and quality-gate information chain in one current series.
- Older pre-truth-layer descriptions are no longer the recommended entrypoint.

## Migration Notes

- Use `docs/OPERATION_GUIDE_ZH.md` for Chinese Claude/Codex usage patterns.
- Use `ARCHITECTURE.md` for implementation architecture.
- Use `USER_GUIDE.md` for user-facing operating principles.
- Existing links to `docs/AI_HARNESS_INTERACTION_GUIDE_ZH.md` and
  `docs/CLINICIAN_GRADUATE_USER_GUIDE_ZH.md` still work, but they now redirect
  readers to the unified V4.3 operation guide.

## Validation

Recommended checks after pulling v4.3.0:

```bash
python -m compileall -q src
python -m pytest -q
python -m paper_workflow.cli validate-contract --strict
```
