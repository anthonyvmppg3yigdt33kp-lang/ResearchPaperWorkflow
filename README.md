# Research Paper Workflow Framework v4.3

Agent-operated research paper workflow for bioinformatics, clinical research,
and reproducible manuscript production. V4.3 aligns the documentation with the
current truth-layer architecture, merges the Chinese Claude/Codex user guides,
and promotes the latest 20-stage workflow as the canonical design.

[![Python 3.9+](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/Tests-65%20passing-brightgreen.svg)](tests/)
[![Version](https://img.shields.io/badge/Version-4.3.0-orange.svg)]()

## What V4.3 Is

ResearchPaperWorkflow is not a prompt pack that asks an AI to write a paper in
one pass. It is an auditable workflow kernel where Claude, Codex, or another
tool-using AI agent can operate a research pipeline while the user supplies
scientific judgment, data, references, and approvals.

The current invariant is:

```text
completed = real execution + verified outputs + concrete gate results + checkpoint consistency
```

## Highlights

- 20-stage V4 paper loop from topic design to final submission package.
- Machine-readable truth contract in `workflow_contract.yaml`.
- Fail-closed stage verification: templates, pending harness records, empty
  files, and missing quality-gate results cannot become completed stages.
- Shared `WorkflowAPI` service boundary for CLI, AI harness, Python callers,
  and non-dry-run E2E compatibility.
- Model-facing AI harness for natural-language Claude/Codex operation.
- Unified `StageResult` files under `stage_results/` for audit and resume.
- Passport and ledger supervision: artifact hashes, checkpoints, integrity
  events, pending harness records, and stale propagation.
- 13-agent routing model covering strategy, literature, statistics, data,
  figures, analysis, writing, AIGC hygiene, integrity, and review.
- Biomedical safeguards for SAP freeze, patient-level independence,
  pseudoreplication, claim-evidence binding, conservative interpretation, data
  availability, code availability, and responsible AIGC text hygiene.

## Claude/Codex First Workflow

Most research users should interact with the workflow through natural language.
The model calls the harness and reports the result.

Example user request:

```text
I have not started yet. I want to design a clinical bioinformatics project about
diabetes and clear cell renal cell carcinoma using single-cell or spatial
transcriptomics. Target journal: Genome Biology. Create the workflow project,
advance only to the first checkpoint, and tell me what scientific decision I
need to approve.
```

Example continuation request:

```text
Continue this paper by one safe workflow step. Stop if there is a checkpoint,
quality-gate failure, pending harness task, missing artifact, or stale
downstream stage. Report the paper_id, current stage truth, missing inputs, and
next safest action.
```

Example validation request:

```text
Audit the current workflow state. Check whether completed stages have real
stage results, non-empty required outputs, concrete quality-gate results,
checkpoint approval where required, and no unpropagated artifact drift.
```

For detailed Chinese natural-language prompt patterns, see
[V4.3 Chinese operation guide](docs/OPERATION_GUIDE_ZH.md).

## Maintainer CLI

The CLI remains available for maintainers, tests, and automation. The important
rule is that all supported entrypoints use the same truth path:

```text
AIWorkflowHarness -> WorkflowAPI -> PaperLoopEngine -> verify_stage -> passport/ledger/stage_results
```

Core commands:

```text
ai
ai-harness
create-project
status
run-pipeline
checkpoint
run-integrity-gate
diagnose-gate-failures
detect-artifact-drift
sync-artifact-stale
validate-workflow
validate-contract
list-harness-invocations
complete-harness-invocation
list-papers
strategy
install-skills
run-aigc-humanizer
```

## 20-Stage Pipeline

```mermaid
flowchart LR
    A["1-5 Research design"] --> B["6-9 Data, figures, analysis, methods verification"]
    B --> C["10-14 Manuscript writing and assembly"]
    C --> D["15-20 AIGC hygiene, integrity, review, revision, finalization"]
```

Stages:

1. `select_topic`
2. `target_journal`
3. `literature_search`
4. `formulate_hypotheses`
5. `design_analysis_plan`
6. `data_audit`
7. `figure_planning`
8. `run_analysis`
9. `verify_methods`
10. `write_methods`
11. `write_results`
12. `write_introduction`
13. `write_discussion`
14. `assemble_manuscript`
15. `aigc_humanizer_review`
16. `integrity_check`
17. `internal_review`
18. `apply_revision`
19. `re_review`
20. `finalize`

## Project Truth Files

Generated paper projects store recoverable state under `papers/<paper_id>/`:

- `project_passport.yaml`: project identity and stage snapshot.
- `stage_results/*_result.json`: normalized result for each stage.
- `artifact_ledger.jsonl`: append-only artifact hashes.
- `checkpoint_ledger.jsonl`: human approvals and revision decisions.
- `integrity_ledger.jsonl`: quality-gate events.
- `workflow_state/pending_invocations/*.json`: external or human work required
  before a stage can complete.

## Documentation

- [V4.3 architecture](ARCHITECTURE.md)
- [V4.3 user guide](USER_GUIDE.md)
- [V4.3 Chinese operation guide](docs/OPERATION_GUIDE_ZH.md)
- [Next-generation truth-layer guide](docs/NEXT_GEN_V4_TRUTH_LAYER.md)
- [Next-generation completion audit](docs/NEXT_GEN_COMPLETION_AUDIT.md)
- [Release notes v4.3.0](docs/RELEASE_NOTES_v4.3.0.md)
- [Release notes v4.2.0](docs/RELEASE_NOTES_v4.2.0.md)
- [Release notes v4.1.0](docs/RELEASE_NOTES_v4.1.0.md)

Backward-compatible links:

- [AI harness interaction guide](docs/AI_HARNESS_INTERACTION_GUIDE_ZH.md)
- [Clinician and graduate student guide](docs/CLINICIAN_GRADUATE_USER_GUIDE_ZH.md)

Those two files now point to the unified V4.3 Chinese operation guide.

## Verification

Recommended maintainer checks:

```bash
python -m compileall -q src
python -m pytest -q
python -m paper_workflow.cli validate-contract --strict
```

Current next-generation V4 verification baseline: `65 passed`.

## License

MIT License. See [LICENSE](LICENSE).
