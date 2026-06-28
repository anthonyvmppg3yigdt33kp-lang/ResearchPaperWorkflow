# Release Notes: v4.2.0

## Summary

v4.2.0 improves day-to-day use inside Claude/Codex. Users can now describe research needs in natural language while the model calls a stable AI harness command to create projects, advance stages, validate state, inspect pending harness tasks, and stop at human checkpoints.

The core V4 truth layer is unchanged: stage completion still requires real outputs, non-empty artifacts, gate results, and checkpoint consistency.

## User-Facing Changes

### Natural-Language Model Harness

- Added `python -m paper_workflow.cli ai --request "<user request>" --json`.
- Added alias `python -m paper_workflow.cli ai-harness`.
- The harness classifies common user requests into workflow intents:
  - create a project;
  - check status;
  - advance one pipeline step;
  - validate global contract wiring;
  - validate a concrete paper workflow;
  - list or complete pending harness invocations;
  - record checkpoint approval;
  - run integrity or AIGC review commands.
- Default behavior is conservative: one stage per model turn, stop on failure, no automatic checkpoint approval.

### Claude/Codex Integration Configuration

- Added `ai_harness` configuration in `config/default_config.yaml`.
- Defined five scenario routes:
  - not started;
  - has direction and needs topic research;
  - has topic and needs data analysis;
  - has partial progress and needs workflow design;
  - has most materials and needs manuscript writing.
- `validate-contract --strict` now checks AI harness command mappings and scenario stage references.

### Documentation

- Added `docs/AI_HARNESS_INTERACTION_GUIDE_ZH.md`.
- Updated README so the default beginner path is natural-language use through Claude/Codex, not manual Python command copying.
- Updated the clinician/graduate guide with v4.2 model-interaction guidance.

## Migration Notes

- Existing `paper-workflow` and `python -m paper_workflow.cli ...` commands still work.
- Users who prefer direct CLI can keep using the lower-level commands.
- Claude/Codex instructions should now call the AI harness first, then explain the JSON result to the user.
- If multiple paper projects exist and no `paper_id` is supplied, the harness returns `needs_input` instead of guessing.

## Validation

Recommended verification after pulling v4.2.0:

```bash
python -m paper_workflow.cli validate-contract --strict
python -m pytest -q
```

Expected current result:

```text
65 passed
```

## Known Boundaries

- The harness does not perform semantic literature search by itself; it routes to the existing workflow and pending harness mechanism.
- The model is still responsible for reading the harness JSON, explaining results, and asking the user for missing files or checkpoint decisions.
- `pending_harness` and `needs_input` remain blocking states until real artifacts are supplied and verified.
