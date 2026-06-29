# Agent Roles v4.3

This document describes the current V4.3 agent collaboration model. Agent
routing is configured in `config/default_config.yaml`; stage completion is
verified through `workflow_contract.yaml`, `StageResult`, and `PaperLoopEngine`.

## Collaboration Model

```mermaid
flowchart TB
    R["research_strategist"] --> L["literature_reviewer"]
    R --> S["statistician"]
    L --> W["report_writer"]
    S --> DA["data_auditor"]
    DA --> FP["figure_planner"]
    FP --> AE["analysis_executor"]
    AE --> PE["pipeline_engineer"]
    PE --> W
    W --> AH["aigc_humanizer_reviewer"]
    AH --> IC["integrity_checker"]
    IC --> TO["team_orchestrator"]
    TO --> W
    CL["code_librarian"] --> AE
    MO["multi_omics_integrator"] --> AE
```

## Primary Agents

| Agent | Owns | Main stages |
|---|---|---|
| `research_strategist` | Research direction, journal fit, feasibility, hypotheses | `select_topic`, `target_journal`, `formulate_hypotheses` |
| `literature_reviewer` | Literature substrate, BibTeX, citation evidence | `literature_search` |
| `statistician` | SAP, endpoint definition, independence assumptions | `design_analysis_plan`, `verify_methods` |
| `data_auditor` | Data inventory, quality, availability, statistical unit | `data_audit` |
| `figure_planner` | Figure logic, panels, evidence-to-figure mapping | `figure_planning` |
| `analysis_executor` | Computational outputs and run manifests | `run_analysis` |
| `pipeline_engineer` | Reproducibility, method verification, environment evidence | `verify_methods` |
| `report_writer` | Manuscript sections, assembly, revisions | `write_methods`, `write_results`, `write_introduction`, `write_discussion`, `assemble_manuscript`, `apply_revision` |
| `aigc_humanizer_reviewer` | Responsible AIGC hygiene scan and conservative revision plan | `aigc_humanizer_review` |
| `integrity_checker` | Quality gates, claim-evidence checks, final package checks | `integrity_check`, `finalize` |
| `team_orchestrator` | Internal review, re-review, cross-agent coordination | `internal_review`, `re_review` |
| `code_librarian` | Code provenance and reusable analysis inventory | supporting `run_analysis`, `verify_methods`, `finalize` |
| `multi_omics_integrator` | Multi-omics analysis support | supporting `run_analysis`, `verify_methods` |

## Responsibility Boundaries

- Strategy agents do not invent data or mark downstream work complete.
- Literature agents do not fabricate references. Missing real BibTeX produces
  pending harness or needs-input state.
- Data and analysis agents do not write manuscript claims before outputs are
  verified.
- Writing agents must write from verified artifacts and preserve claim-evidence
  boundaries.
- Integrity agents report and route failures; they do not silently rewrite the
  evidence base.
- No agent can bypass `verify_stage()` or checkpoint requirements.

## Agent To Truth-Layer Flow

```mermaid
sequenceDiagram
    participant L as PaperLoopEngine
    participant D as AgentDispatcher
    participant A as Routed agent
    participant S as StageResult
    participant P as Passport and ledgers

    L->>D: run stage
    D->>A: route by stage and agent config
    A->>S: return artifacts, execution_mode, gates
    D->>L: normalized result
    L->>L: verify required outputs and gates
    L->>P: record artifacts, checkpoints, integrity events
```

The truth layer, not the agent role description, decides whether the stage is
complete.
