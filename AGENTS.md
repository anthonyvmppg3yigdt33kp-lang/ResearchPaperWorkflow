# AGENTS.md - ResearchPaperWorkflow v4.3

This file is read by AI assistants working in the repository. The current
system is the V4.3 truth-layer workflow: 4 logical layers, a 20-stage pipeline,
AI harness operation for Claude/Codex, explicit human checkpoints, and
fail-closed quality gates.

## Project Identity

ResearchPaperWorkflow is a deterministic, auditable, multi-agent research paper
workflow for bioinformatics and clinical manuscripts. It converts research work
from ad-hoc scripting and chat-based drafting into stage results, required
artifacts, ledgers, checkpoints, and validation reports.

Current invariant:

```text
completed = real execution + verified outputs + concrete gate results + checkpoint consistency
```

The user is the final scientific decision maker. The workflow must never invent
data, results, clinical facts, references, or approvals.

## Required Reading

Before major work, read:

- `README.md`
- `ARCHITECTURE.md`
- `USER_GUIDE.md`
- `docs/OPERATION_GUIDE_ZH.md`
- `workflow_contract.yaml`
- `config/default_config.yaml`

For a paper project, also inspect:

- `papers/<paper_id>/project_passport.yaml`
- `papers/<paper_id>/stage_results/`
- `papers/<paper_id>/artifact_ledger.jsonl`
- `papers/<paper_id>/checkpoint_ledger.jsonl`
- `papers/<paper_id>/integrity_ledger.jsonl`
- `papers/<paper_id>/workflow_state/pending_invocations/`

## Core Rules

1. Do not modify raw data or final results without explicit confirmation.
2. Do not fabricate references, statistics, cohorts, datasets, or validation.
3. Do not treat cells, spots, features, or images as independent patients.
4. Distinguish observation, association, interpretation, hypothesis, and
   experimentally validated conclusion.
5. Do not turn correlation into causation.
6. All manuscript claims must bind to a figure, table, result artifact, or
   verified citation.
7. Methods text must match actual code, parameters, versions, and run manifests.
8. Use relative project paths in generated artifacts.
9. Preserve human checkpoints as ledgered decisions.
10. Never mark `template`, `pending_harness`, or `needs_input` as completed.
11. Run or recommend `validate-contract` before production execution changes.
12. Run or recommend `validate-workflow` before submission readiness claims.

## Four Layers

| Layer | Responsibility |
|---|---|
| Strategy | Topic, journal fit, feasibility, hypotheses, SAP context. |
| Decision | Next-stage selection, dependency control, checkpoint blockers, stale routing. |
| Execution | Agent and skill routing, artifact generation, pending harness records. |
| Supervision | Passport, artifacts, hashes, checkpoints, integrity events, validation. |

## 20-Stage Pipeline

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

## Agent Routing

| Agent | Primary responsibility |
|---|---|
| `research_strategist` | Research direction, journal fit, feasibility, hypotheses. |
| `literature_reviewer` | Literature search, BibTeX, citation evidence. |
| `statistician` | SAP, endpoint definition, independence and statistical design. |
| `data_auditor` | Data inventory, quality, availability, statistical unit. |
| `figure_planner` | Figure architecture and evidence-to-panel mapping. |
| `analysis_executor` | Computational analysis outputs and result manifests. |
| `pipeline_engineer` | Reproducibility, method verification, environment evidence. |
| `report_writer` | Manuscript sections, assembly, and revision application. |
| `aigc_humanizer_reviewer` | Responsible AI-text hygiene and conservative revision plan. |
| `integrity_checker` | Quality gates, claim-evidence checks, final package checks. |
| `team_orchestrator` | Internal review, re-review, multi-agent coordination. |
| `code_librarian` | Code provenance and reusable analysis inventory. |
| `multi_omics_integrator` | Multi-omics analysis support. |

## AI Harness Use

For ordinary users, prefer natural-language operation through Codex or Claude.
The model should translate the request to the AI harness and report:

- `paper_id`;
- current pipeline state;
- stage changed;
- artifacts created or missing;
- gate pass/fail status;
- checkpoint requirement;
- pending harness records;
- stale or drifted artifacts;
- next safest action.

## Quality Gate Policy

Critical and high gates are fail-closed. Missing gate results are not passes.

High-risk biomedical gates include:

- statistical analysis plan exists;
- endpoint definition complete;
- patient-level independence;
- pseudoreplication check;
- methods parameters complete;
- claim-artifact binding;
- statistics reported;
- results no overinterpretation;
- BibTeX citation existence;
- data availability statement;
- code availability statement;
- AIGC artifact scan.

## Closeout Standard

Every substantial agent session should end with:

- files changed;
- commands or validations run;
- remaining blockers;
- whether the workflow state is complete, blocked, failed, or stale;
- next recommended step.
