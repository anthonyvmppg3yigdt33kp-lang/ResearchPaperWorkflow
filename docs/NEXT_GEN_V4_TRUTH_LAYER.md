# Next-Generation V4 Truth-Layer Workflow

This is the current canonical architecture guide for the next-generation
ResearchPaperWorkflow V4 upgrade. Older documents may still describe the
pre-truth-layer 18-stage design. This document supersedes those counts and
entrypoint rules for production use.

For a clinician/graduate-student walkthrough in Chinese, start with
`docs/CLINICIAN_GRADUATE_USER_GUIDE_ZH.md`.

## Design Goal

The workflow is not a free-form manuscript writer. It is an auditable research
production kernel for bioinformatics and clinical manuscripts.

The central invariant is:

```text
completed == real execution + verified required outputs + concrete gate results + checkpoint state
```

No stage is considered complete because a handler returned success, a template
was written, or an external agent was requested. Completion is reconstructed
from `project_passport.yaml`, `stage_results/*_result.json`, artifact ledgers,
quality-gate results, and checkpoint ledgers.

## Four Layers

| Layer | Current files | Responsibility |
|---|---|---|
| Strategy | `src/paper_workflow/strategy/`, `src/paper_workflow/workflow.py` | Convert research idea, field, journal, feasibility, and hypotheses into an initialized paper project. |
| Decision | `src/paper_workflow/engine/loop_engine.py`, `workflow_contract.yaml` | Decide next safe stage, hydrate truth from persisted records, enforce checkpoint blockers, mark stale dependents. |
| Execution | `src/paper_workflow/engine/agent_dispatcher.py`, `src/paper_workflow/engine/agent_harness.py`, `src/paper_workflow/api.py`, `src/paper_workflow/cli/` | Produce artifacts through real executors or create pending harness invocations for external work. |
| Supervision | `src/paper_workflow/supervision/`, `src/paper_workflow/outputs/stage_result.py` | Persist artifacts, checkpoints, integrity events, stage results, hashes, and validation reports. |

## Canonical Entrypoints

Use these as the supported production paths:

```bash
python -m paper_workflow.cli create-project --idea "..." --field "..." --journal "Genome Biology"
python -m paper_workflow.cli run-pipeline --paper <paper_id> --stop-on-failure
python -m paper_workflow.cli validate-workflow --paper <paper_id> --strict
```

Python callers should use the same service boundary:

```python
from paper_workflow import WorkflowAPI

api = WorkflowAPI(project_root)
created = api.create_project(
    idea="Patient-level single-cell biomarker workflow",
    field="bioinformatics, clinical, single-cell",
    journal="Genome Biology",
)
api.run_pipeline(created["paper_id"], stop_on_failure=True)
```

`WorkflowAPI` is the common service layer for CLI, Python callers, and non-dry-run
`E2EWorkflow`. CLI commands should not reimplement pipeline state transitions.

## E2E Compatibility

`paper_workflow.e2e_workflow` is now a compatibility surface:

- `dry_run=True`: preserves the legacy 5-phase plan display.
- `dry_run=False`: delegates to `WorkflowAPI.run_pipeline()` and records V4
  stage events into legacy `PhaseReport` / `SkillInvocation` objects.
- Non-dry-run E2E invocations therefore cannot bypass `stage_results`, required
  outputs, checkpoint blockers, or quality gates.

## Twenty-Stage Pipeline

| # | Stage | Human checkpoint | Primary required outputs |
|---:|---|---|---|
| 1 | `select_topic` | yes | `research_plan/research_question.md`, `research_plan/hypotheses.yaml` |
| 2 | `target_journal` | no | `research_plan/journal_profile.md` |
| 3 | `literature_search` | no | `references/library.bib` |
| 4 | `formulate_hypotheses` | yes | `research_plan/feasibility_decision.md` |
| 5 | `design_analysis_plan` | yes | SAP, study protocol, causal-assumption audit |
| 6 | `data_audit` | no | data audit report, data inventory |
| 7 | `figure_planning` | yes | figure plan and figure specs |
| 8 | `run_analysis` | no | run manifest |
| 9 | `verify_methods` | no | method run manifest |
| 10 | `write_methods` | no | `manuscript/methods.md` |
| 11 | `write_results` | no | `manuscript/results.md` |
| 12 | `write_introduction` | no | `manuscript/introduction.md` |
| 13 | `write_discussion` | no | `manuscript/discussion.md` |
| 14 | `assemble_manuscript` | no | `manuscript/manuscript_full.md` |
| 15 | `aigc_humanizer_review` | no | AIGC report, revision plan, humanized manuscript |
| 16 | `integrity_check` | no | JSON and Markdown integrity reports |
| 17 | `internal_review` | yes | internal review report |
| 18 | `apply_revision` | no | revised manuscript |
| 19 | `re_review` | no | re-review report |
| 20 | `finalize` | yes | final manuscript, cover letter, data/code statements |

The machine-readable source of truth is `workflow_contract.yaml`.

## Completion Rules

`PaperLoopEngine.verify_stage()` is fail-closed for production-critical states:

- Missing or empty required output: fail.
- `template`, `pending_harness`, or `needs_input`: fail or block.
- Configured critical/high gate with no concrete result: fail.
- Completed human-checkpoint stage with no approved checkpoint: invalid.
- Drifted upstream artifact: mark downstream stages stale.

Use:

```bash
python -m paper_workflow.cli validate-contract --strict
python -m paper_workflow.cli validate-workflow --paper <paper_id> --strict
python -m paper_workflow.cli detect-artifact-drift --paper <paper_id>
python -m paper_workflow.cli sync-artifact-stale --paper <paper_id>
```

`validate-contract` checks global wiring before any paper is run: config stages,
workflow contract stages, engine stages, dispatcher handlers, agent routing, and
quality-gate references must all agree.

## Human-In-The-Loop Policy

Checkpoints are explicit ledger entries:

```bash
python -m paper_workflow.cli checkpoint \
  --paper <paper_id> \
  --stage design_analysis_plan \
  --decision approved \
  --notes "SAP frozen before primary analysis."
```

Unattended smoke tests may use:

```bash
python -m paper_workflow.cli run-pipeline \
  --paper <paper_id> \
  --auto-approve-checkpoints \
  --stop-on-failure
```

Production research should prefer manual approval at checkpoints. The critical
scientific checkpoints are topic direction, hypotheses, SAP freeze, figure plan,
internal review, and final package.

## Agent Harness

When a stage needs human or external agent work, the dispatcher writes an
invocation file under:

```text
papers/<paper_id>/workflow_state/pending_invocations/
```

List and verify those invocations:

```bash
python -m paper_workflow.cli list-harness-invocations --paper <paper_id>
python -m paper_workflow.cli complete-harness-invocation \
  --paper <paper_id> \
  --invocation literature_search \
  --strict
```

The harness verifies declared outputs only. It does not mark the pipeline stage
complete. After external output is present, run the pipeline again so the normal
`run_stage -> verify_stage -> stage_results` path records completion.

## Bioinformatics And Clinical Safeguards

The next-generation default path is tuned for biomedical manuscript risk:

- SAP before analysis: endpoints, covariates, multiple testing, missing data,
  and validation policy are recorded before primary analysis.
- Patient-level inference: gates fail if the statistical unit collapses to cells,
  spots, or technical observations where patient-level inference is claimed.
- Pseudoreplication guard: Methods and Results must preserve biological-unit
  boundaries.
- Claim evidence binding: Results claims are tied to artifacts and statistics.
- Conservative language: Results and Discussion gates discourage causal,
  deployment-ready, first-ever, and biomarker claims without validation.
- AIGC hygiene: text hygiene review runs after assembly and before integrity
  checks, without making authorship accusations.

## Minimal Verification

Use this before calling a workflow production-ready:

```bash
python -m compileall -q src
python -m pytest -q
python -m paper_workflow.cli --help
python -m paper_workflow.cli validate-contract --strict
python -m paper_workflow.cli validate-workflow --paper <paper_id> --strict
```

For a full smoke run, seed the paper with:

- `references/library.bib` containing real BibTeX entries.
- `data/data_inventory_input.yaml` with `statistical_unit: patient`.
- `results/analysis_outputs/primary_results.csv`.

Then run:

```bash
python -m paper_workflow.cli run-pipeline \
  --paper <paper_id> \
  --auto-approve-checkpoints \
  --stop-on-failure
```

Expected final evidence:

- `status` shows all 20 stages completed.
- `validate-workflow --strict` returns valid.
- `detect-artifact-drift` reports no drift.
- `stage_results/` contains 20 `*_result.json` files with
  `engine_stage_status: completed`.
