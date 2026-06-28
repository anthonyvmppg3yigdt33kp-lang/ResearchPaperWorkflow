# Release Notes: v4.1.0

Release focus: next-generation truth-layer workflow for bioinformatics and
clinical manuscript production, plus beginner-friendly guidance for clinicians
and graduate students.

## What Changed

### Trustworthy workflow completion

- Added `workflow_contract.yaml` as the machine-readable contract for the
  canonical 20-stage V4 pipeline.
- Added unified `StageResult` truth fields: `execution_mode`,
  `outputs_verified`, `required_outputs`, `missing_outputs`, and
  `quality_gate_results`.
- Added persisted `stage_results/<stage>_result.json` records so status,
  resume, validation, and audit all read the same stage truth.
- `template`, `pending_harness`, and `needs_input` can no longer be treated as
  completed states.

### Real V4 execution path

- Expanded `AgentDispatcher` with real stage executors for planning, data audit,
  figure planning, analysis handoff, writing, assembly, AIGC hygiene, integrity,
  review, revision, and finalization.
- Added stricter upstream checks for `run-aigc-humanizer`; it cannot run before
  `assemble_manuscript`.
- Added fail-closed verification for configured critical/high quality gates.

### Unified CLI/API/E2E entrypoints

- Added `WorkflowAPI` as the shared service layer for Python callers and CLI.
- CLI commands now route through `WorkflowAPI` instead of maintaining a separate
  state implementation.
- Non-dry-run `E2EWorkflow` now delegates to the V4 `WorkflowAPI` and records V4
  stage events into legacy phase reports.
- Legacy E2E dry-run remains available for planning display only.

### Agent harness wiring

- Added `AgentHarness` for pending external skill or human-agent work.
- Added CLI commands:
  - `list-harness-invocations`
  - `complete-harness-invocation`
- Harness completion validates required outputs and rejects missing, empty, or
  placeholder artifacts.

### Contract and workflow validation

- Added `validate-workflow --strict` for project-level truth checks.
- Added `validate-contract --strict` for global wiring checks across config,
  workflow contract, engine stages, dispatcher handlers, agent routing, and gate
  references.
- Added drift propagation checks that mark downstream stages stale when upstream
  artifacts change.

### Beginner and production documentation

- Added `docs/NEXT_GEN_V4_TRUTH_LAYER.md` as the canonical current architecture
  and operations guide.
- Added `docs/NEXT_GEN_COMPLETION_AUDIT.md` mapping upgrade requirements to
  implementation and runtime evidence.
- Added `docs/CLINICIAN_GRADUATE_USER_GUIDE_ZH.md`, a Chinese guide for
  clinicians and graduate students with low/intermediate/advanced tracks and
  five starting scenarios.
- Marked older 18-stage/legacy documents as historical.
- Updated README to the current CLI, validation commands, harness flow, and test
  count.

## Who Should Upgrade

Upgrade if you use ResearchPaperWorkflow for:

- clinical or bioinformatics manuscript planning,
- single-cell or spatial transcriptomics workflows,
- patient-level statistical analysis planning,
- manuscript drafting from existing results,
- multi-agent or human-in-the-loop paper production,
- reproducibility and audit-focused project tracking.

## Migration Notes

- Use `python -m paper_workflow.cli` as the preferred CLI module path.
- Run `python -m paper_workflow.cli validate-contract --strict` after pulling
  this release.
- Existing paper projects should run:

```bash
python -m paper_workflow.cli status --paper <paper_id>
python -m paper_workflow.cli validate-workflow --paper <paper_id> --strict
python -m paper_workflow.cli detect-artifact-drift --paper <paper_id>
```

- If a stage is now blocked as `pending_harness`, add the required real artifact
  and run:

```bash
python -m paper_workflow.cli list-harness-invocations --paper <paper_id>
python -m paper_workflow.cli complete-harness-invocation --paper <paper_id> --invocation <stage> --strict
python -m paper_workflow.cli run-pipeline --paper <paper_id> --stop-on-failure
```

## Validation

Release validation performed before publishing:

```text
python -m compileall -q src
python -m pytest -q
python -m paper_workflow.cli validate-contract --strict
```

Current test result:

```text
60 passed
```

Full CLI smoke evidence:

- Minimal valid BibTeX, patient-level data inventory, and primary result CSV
  completed all 20 V4 stages.
- `validate-workflow --strict` returned valid.
- `detect-artifact-drift` returned no drift.
- `stage_results/` contained 20 completed result files.

## Known Boundaries

- The harness verifies external agent outputs but does not execute arbitrary
  remote agents by itself.
- PaperQA2/STORM/AI-Scientist-style literature engines remain reserved behind
  future interfaces.
- Legacy E2E dry-run is a plan display mode; production execution uses V4
  `WorkflowAPI`.
