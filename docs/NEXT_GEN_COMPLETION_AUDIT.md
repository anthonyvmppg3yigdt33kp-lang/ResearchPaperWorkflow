# Next-Generation Upgrade Completion Audit

Audit date: 2026-06-28

User-facing onboarding for Claude/Codex natural-language use, clinician users,
graduate students, and bioinformatics operators is now consolidated in
`docs/OPERATION_GUIDE_ZH.md`.

This audit maps the requested next-generation upgrade requirements to current
implementation evidence. It is intentionally evidence-bound: a requirement is
not considered satisfied unless a file, test, or runtime check proves it.

## Requirement Matrix

| Requirement | Current status | Evidence |
|---|---|---|
| Artifact unification | Implemented | `StageResult` includes execution mode, required outputs, missing outputs, gate results, and artifacts; `PaperLoopEngine` writes `stage_results/*_result.json`. |
| Completed means real outputs | Implemented | `workflow_contract.yaml`; `verify_stage()` blocks missing outputs and non-real execution modes; tests in `tests/test_truth_layer.py`. |
| Critical/high gates fail closed | Implemented | Unknown or unrun critical/high gates fail; covered by `test_configured_critical_gate_fails_closed_when_not_run`. |
| Key stage real executors | Implemented for the V4 production path | `AgentDispatcher` contains real executors for planning, data audit, figure planning, writing, review, AIGC hygiene, integrity, revision, and finalization; tests run through Phase 1-6. |
| Pending harness is not completion | Implemented | `AgentHarness` verifies required outputs and placeholder patterns; pending/template stages cannot pass `verify_stage()`. |
| CLI/API unified | Implemented | `WorkflowAPI` is the shared service layer; CLI handlers call `WorkflowAPI`; non-dry-run E2E delegates to `WorkflowAPI`. |
| Claude/Codex AI harness | Implemented | `AIWorkflowHarness` routes natural-language requests to `WorkflowAPI`; `ai` / `ai-harness` CLI commands expose model-facing execution. |
| E2E old path cannot bypass truth layer | Implemented for non-dry-run | `E2EWorkflow.run(dry_run=False)` delegates to `WorkflowAPI`; dry-run remains display-only compatibility mode. |
| Human-in-the-loop checkpoint control | Implemented | `checkpoint_blockers()`, `checkpoint_required` state, checkpoint CLI, and validation issue `checkpoint_required`. |
| Resume/status hydrate from persisted truth | Implemented | `PaperLoopEngine` hydrates from passport and stage result files; tests cover reload consistency. |
| Artifact drift propagation | Implemented | `sync_artifact_stale()` uses dependency map; tests cover downstream stale propagation. |
| Bioinformatics/clinical safeguards | Implemented in gates and executors | SAP, endpoint definition, patient-level independence, pseudoreplication, claim-artifact binding, statistics reporting, overinterpretation checks. |
| Production validation command | Implemented | `validate-workflow --strict` checks result files, required outputs, gates, pending harness, checkpoints, and drift propagation. |
| Global contract validation | Implemented | `validate-contract --strict` checks config stages, workflow contract, engine stages, dispatcher handlers, agent routing, gate references, and AI harness scenario routes. |
| User-facing docs reflect current path | Implemented in canonical docs | `README.md`, `ARCHITECTURE.md`, `USER_GUIDE.md`, `docs/OPERATION_GUIDE_ZH.md`, `docs/NEXT_GEN_V4_TRUTH_LAYER.md`, and this audit document. |

## Verification Run

The following checks were run after the V4 truth-layer and E2E delegation work:

```text
python -m compileall -q src
python -m pytest -q
python -m paper_workflow.cli validate-contract --strict
```

Current test result:

```text
65 passed
```

Additional CLI smoke checks performed during the upgrade:

```text
python -m paper_workflow.cli --help
python -m paper_workflow.cli run-pipeline --paper <smoke_id> --auto-approve-checkpoints --stop-on-failure
python -m paper_workflow.cli validate-workflow --paper <smoke_id> --strict
python -m paper_workflow.cli detect-artifact-drift --paper <smoke_id>
python -m paper_workflow.e2e_workflow --paper-id e2e_cli_dryrun_smoke --phases 1 --dry-run --no-report
```

Observed smoke evidence:

- API-backed CLI completed all 20 V4 stages when provided with minimal valid
  BibTeX, patient-level data inventory, and primary result CSV.
- `validate-workflow --strict` returned valid.
- `detect-artifact-drift` returned no drift.
- `stage_results/` contained 20 completed result files.
- `run-aigc-humanizer` failed early when `assemble_manuscript` was incomplete.
- `complete-harness-invocation --strict` rejected placeholder BibTeX and passed
  only after real BibTeX was written.

## Remaining Design Boundaries

These are explicit boundaries, not hidden completions:

- The harness verifies external agent outputs; it does not execute arbitrary
  remote agents or mark stages complete directly.
- Legacy E2E dry-run remains a plan-display compatibility mode. Non-dry-run is
  the production path and delegates to V4.
- PaperQA2/STORM/AI-Scientist-style literature engines are reserved behind the
  `claim_evidence_audit_interface`; they are not part of this minimal truth-layer
  upgrade.
- Archived audit and release-note files may still mention earlier counts as
  history; use `ARCHITECTURE.md`, `docs/NEXT_GEN_V4_TRUTH_LAYER.md`, and
  `workflow_contract.yaml` as the current truth source.

## Completion Standard

The upgrade is considered production-ready for the requested next-generation
kernel when all of the following remain true:

1. `python -m pytest -q` passes.
2. `workflow_contract.yaml` stage ids match config, engine stages, and dispatcher handlers.
3. `validate-workflow --strict` can detect fake completion, missing outputs,
   missing gate results, pending harness, missing checkpoints, and artifact drift.
4. CLI, Python API, and E2E non-dry-run all use `WorkflowAPI`.
5. A user seeing `completed` can trust it means real, verified, checkpointed,
   traceable output rather than a template or unexecuted harness request.
