# Historical Note

This document is retained for background. The current production architecture is
the V4 truth-layer design documented in `docs/NEXT_GEN_V4_TRUTH_LAYER.md`.
Older counts such as 18 stages, 16 gates, or legacy E2E execution should be
treated as historical unless they are repeated in the next-generation guide.

# Research Paper Workflow Framework — Architecture

**Version**: 1.0.0 | **Last Updated**: 2026-06-18

A deterministic, auditable, multi-agent pipeline for transforming the research paper writing process from ad-hoc scripting into a structured software system. The architecture is organized into four layers, 18 pipeline stages, an 8-step loop engine, a 4-file passport system, 16 integrity gates, 11 specialized agents, and 12 domain-aware skills.

---

## Table of Contents

1. [Four-Layer Architecture](#1-four-layer-architecture)
2. [18-Stage Pipeline with Phase Groupings](#2-18-stage-pipeline-with-phase-groupings)
3. [Loop Engine Design](#3-loop-engine-design)
4. [Passport System](#4-passport-system)
5. [Integrity Gate System](#5-integrity-gate-system)
6. [Agent System](#6-agent-system)
7. [Skill System](#7-skill-system)
8. [Data Flow Between Layers](#8-data-flow-between-layers)
9. [Extension Points for New Domains](#9-extension-points-for-new-domains)
10. [Comparison with Draftpaper\_loop Design Principles](#10-comparison-with-draftpaper_loop-design-principles)

---

## 1. Four-Layer Architecture

The framework is organized into four vertically stacked layers. Each layer is an independent Python package inside `src/paper_workflow/`, connected through well-defined data contracts. Layers communicate downward via method calls and upward via event records in the passport ledger files.

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                     STRATEGY LAYER (src/paper_workflow/strategy/)             │
│  Research question formulation, journal targeting, feasibility assessment,    │
│  hypothesis generation. Pure planning — no execution.                         │
│                                                                              │
│  Components:                                                                 │
│    TopicSelector       → Converts NL idea → structured ResearchTopic         │
│    JournalTargeter     → Resolves journal → JournalTarget (25 journals)      │
│    FeasibilityAssessor → 4-dim assessment (data/methods/journal/timeline)    │
│    HypothesisFramework → Generates H1-H4 (primary→exploratory)               │
│    ResearchStrategyManager → Top-level orchestrator combining all above      │
│                                                                              │
│  Input:  User idea string, field keywords                                    │
│  Output: ResearchStrategy dataclass (topic + journal + feasibility + H1-H4)  │
├──────────────────────────────────────────────────────────────────────────────┤
│                     DECISION LAYER (src/paper_workflow/engine/)              │
│  Agent routing, skill dispatch, pipeline state machine. Makes decisions      │
│  about what should run next — does not execute.                              │
│                                                                              │
│  Components:                                                                 │
│    PaperLoopEngine    → 18-stage state machine, dependency resolution        │
│    SkillsDispatcher   → Keyword→skill mapping (in config/default_config.yaml)│
│    AgentRouter        → Task-type→agent mapping with I/O contracts           │
│    TeamOrchestrator   → Multi-agent coordination, deadlock detection         │
│                                                                              │
│  Input:  Passport state, stage dependencies, artifact hashes                 │
│  Output: Stage dispatch decision (agent + skill + parameters)                │
├──────────────────────────────────────────────────────────────────────────────┤
│                     EXECUTION LAYER (src/paper_workflow/cli/, .claude/)      │
│  Actually runs analysis code, writes manuscript sections, generates figures. │
│  Agents and skills are the execution units.                                  │
│                                                                              │
│  Components:                                                                 │
│    11 domain agents   → Specialized executors with bounded contracts         │
│    12 skills          → Reusable workflow templates (Markdown definitions)   │
│    3 teams            → Multi-agent collaboration configurations            │
│    12 CLI commands    → User-facing control surface                         │
│    code_library/      → Reusable analysis patterns (QC, clustering, I/O)    │
│                                                                              │
│  Input:  Stage dispatch with agent+skill assignment                          │
│  Output: Artifacts (manuscript sections, figures, tables, analysis logs)     │
├──────────────────────────────────────────────────────────────────────────────┤
│                     SUPERVISION LAYER (src/paper_workflow/supervision/)      │
│  State persistence, artifact provenance, quality enforcement. Active at      │
│  every stage transition — not just at the end.                               │
│                                                                              │
│  Components:                                                                 │
│    PaperPassport       → 4-file identity + artifact + checkpoint + integrity │
│    IntegrityGateChecker → 16-rule automated quality enforcement              │
│    StaleDetection      → SHA-256 based upstream→downstream cascade          │
│    FuseBreaker         → Circuit breaker for runaway pipelines              │
│    DecisionRecorder    → Append-only decision log to checkpoint_ledger.jsonl │
│                                                                              │
│  Input:  All artifacts produced by execution layer                           │
│  Output: Gate reports, passport updates, stale-stage markings                │
└──────────────────────────────────────────────────────────────────────────────┘
```

### Layer Interaction Rules

1. **Strategy never executes.** The Strategy layer produces plans, not artifacts.
2. **Decision never modifies data.** The Decision layer reads state and issues dispatch instructions.
3. **Execution never decides what to run next.** It only runs what it is told to run.
4. **Supervision observes all layers.** Every layer writes to the passport; supervision reads all ledger files.
5. **Downward calls only.** Higher layers call lower layers; lower layers report upward only through ledger files (event sourcing pattern).

### Why Four Layers?

| Concern | Without layers | With layers |
|---------|---------------|-------------|
| Research direction change | Rewrite analysis scripts | Replace strategy config only |
| Journal change mid-project | Manually reformat everything | `JournalTargeter.resolve_journal("NewJournal")` — pipeline reconfigures |
| New agent added | Unknown side effects | Agent registered in config, contract-checked by router |
| Integrity rule change | Hunt through all scripts | Add/modify gate in `integrity.py`, all stages inherit |

---

## 2. 18-Stage Pipeline with Phase Groupings

The pipeline is the backbone of the framework — 18 discrete stages grouped into 6 sequential phases. Each stage has explicit upstream dependencies, produces declared artifacts, and runs through specific agents.

### Phase 1: Research & Planning (Stages 1–4)

**Goal**: Define what to study, where to publish, what is known, and what to test.

```
Stage 1: create_project     [🔴 CP-1 Human Checkpoint]
         Agent: research_strategist  |  Skill: topic_research
         Produces: project_passport.yaml, paper_config.yaml
         └─► Entry point. Initializes passport and paper directory.

Stage 2: target_journal     ╗
Stage 3: literature_search  ╝  [PARALLEL — both depend on Stage 1]
         Agent: research_strategist (S2) / literature_reviewer (S3)
         Produces: journal_profile.md, citation_library.bib, citation_evidence.jsonl
         └─► Runs simultaneously after CP-1. Saves ~20 minutes.

Stage 4: formulate_hypotheses  [🔴 CP-2 Human Checkpoint]
         Agent: research_strategist  |  Skill: topic_research
         Depends on: Stage 2 AND Stage 3 (merge point)
         Produces: hypotheses.yaml, study_design.md, power_analysis.md
         └─► Last checkpoint before data analysis. Irreversible — analysis plan locked.
```

### Phase 2: Data & Methods (Stages 5–8)

**Goal**: Audit data quality, plan figures, execute analysis, verify reproducibility.

```
Stage 5: data_audit
         Agent: data_auditor  |  Skill: qc_pipeline
         Produces: data_audit_report.md, metadata_validation.yaml, qc_metrics.json
         └─► Read-only audit. Never modifies raw data.

Stage 6: figure_planning
         Agent: figure_planner  |  Skill: figure_planning
         Produces: figure_plan.md, figure_specs.yaml, color_palette.yaml
         └─► Designs Figure 1-6 before analysis runs. Feeds specs into Stage 7.

Stage 7: run_analysis            [Longest stage — up to 4 hours]
         Agent: analysis_executor  |  Skills: statistical_testing, spatial_analysis, pathway_inference, multi_omics
         Produces: result_tables/*.csv, figures/*.pdf, analysis_log.txt, session_info.txt
         └─► Async cross-validation by statistician agent after completion.

Stage 8: verify_methods
         Agent: pipeline_engineer  |  Skill: reproducibility
         Produces: reproducibility_report.md, environment_snapshot.yaml
         └─► Replay analysis in isolated environment. Compare checksums.
```

### Phase 3: Writing (Stages 9–12)

**Goal**: Write all IMRAD sections. Introduction and Discussion can partially overlap.

```
Stage 9:  write_methods
          Agent: report_writer  |  Skill: paper_writing
          Produces: manuscript/methods.md, methods_parameter_table.csv

Stage 10: write_results
          Agent: report_writer  |  Skill: paper_writing
          Produces: manuscript/results.md, claims_evidence_table.csv
          └─► Async cross-validation by statistician after completion.

Stage 11: write_introduction
          Agent: report_writer  |  Skill: paper_writing
          Produces: manuscript/introduction.md
          └─► Can draft literature review portion while Stage 10 finalizes.

Stage 12: write_discussion
          Agent: report_writer  |  Skill: paper_writing
          Produces: manuscript/discussion.md
          └─► Requires Stage 10 + Stage 11. Mandatory Limitations paragraph (>=100 words).
```

### Phase 4: Assembly & Review (Stages 13–15)

**Goal**: Assemble full manuscript, run integrity gates, simulate peer review.

```
Stage 13: assemble_manuscript  [🔴 CP-3 Human Checkpoint]
          Agent: report_writer  |  Skill: paper_writing
          Depends on: ALL writing stages complete (merge point)
          Produces: manuscript_full.md, manuscript_full.tex, manuscript_full.docx

Stage 14: integrity_check      [🔴 CP-4 Human Checkpoint]
          Agent: integrity_checker  |  Skill: qc_pipeline
          Produces: integrity_report.json, integrity_report.md
          └─► CRITICAL failures BLOCK pipeline. 16 gates executed in optimized order.

Stage 15: internal_review      [🔴 CP-5 Human Checkpoint]
          Agent: integrity_checker (orchestrator) + statistician + literature_reviewer
          Produces: review_summary.md, revision_priority_matrix.yaml
          └─► 3+ independent reviewer personas, parallel review.
```

### Phase 5: Revision (Stages 16–17)

**Goal**: Apply reviewer feedback, re-review. Maximum 5 revision cycles.

```
Stage 16: apply_revision
          Agent: report_writer  |  Skill: revision_routing
          Produces: revision_tracker.md, change_log.yaml, commitment_ledger.csv
          └─► Marks downstream stages stale. Re-runs affected pipeline stages.

Stage 17: re_review            [🔴 CP-6 Human Checkpoint]
          Agent: integrity_checker  |  Skill: revision_routing
          Produces: re_review_report.md, regression_check.yaml
          └─► Verdict: READY / MINOR REMAINING / NOT READY.
          └─► NOT READY → loop back to Stage 16 (max 5 cycles).
```

### Phase 6: Finalize (Stage 18)

**Goal**: Final quality check, export submission-ready package.

```
Stage 18: finalize             [🔴 CP-FINAL Human Checkpoint]
          Agent: integrity_checker + report_writer
          Produces: manuscript_final.pdf, cover_letter.md, supplementary_package.zip,
                    provenance_report.json
          └─► Full 16-gate re-run. Provenance report with complete SHA-256 artifact chain.
          └─► Terminal checkpoint. Pipeline complete.
```

### Stage Dependency Graph

```
S1 ──┬── S2 ──┬── S4 ── S5 ── S6 ── S7 ── S8 ── S9 ──┬── S10 ──┬── S12 ──┐
     │         │                                        │         │          │
     └── S3 ──┘                                        │    ┌──── S11 ──────┤
                                                       │    │               │
                                                       └────┤               │
                                                            └── S13 ◄───────┘
                                                              │
                                                              ▼
                                                            S14 ── S15 ── S16 ── S17 ── S18
                                                                              ▲       │
                                                                              └─── loop (max 5)
```

### Pipeline State Machine

```
CLEAN ──► IN_PROGRESS ──► CLEAN (all stages completed)
   │            │
   │            ├──► GATE_FAILURE ──► diagnose ──► revision ──► IN_PROGRESS
   │            │
   │            ├──► STALE_STAGES ──► sync ──► IN_PROGRESS
   │            │
   │            └──► BLOCKED (unresolvable dependency cycle or max retries exceeded)
   │
   └──► DRIFT_DETECTED ──► sync_artifact_stale ──► STALE_STAGES
```

### Paper Type Stage Selection

Not all paper types use all 18 stages. The `config/default_config.yaml` defines which stages are required or skipped per paper type:

| Paper Type | Stages Run | Stages Skipped | Key Differences |
|------------|-----------|----------------|-----------------|
| `original_research` | All 18 | None | Full pipeline |
| `methods` | 14 | S4, S6, S11, S12 | No hypotheses, figure planning, intro, or discussion |
| `review` | 13 | S4, S5, S6, S7, S8 | Literature-focused; skips data/analysis |
| `clinical_research` | All 18 | None | Adds ethics gates, CONSORT/STROBE checklists |
| `data_resource` | 12 | S3, S4, S6, S7, S11, S12 | Data-focused; minimum writing |
| `brief_communication` | 14 | S4, S6, S8, S17 | Condensed pipeline; stricter limits |

---

## 3. Loop Engine Design

The `PaperLoopEngine` (in `src/paper_workflow/engine/loop_engine.py`) implements an 8-step iterative cycle. It is the central state machine that drives pipeline progression.

### The 8-Step Cycle

```
 ┌──────────────────────────────────────────────────────────────┐
 │                                                              │
 │   ① OBSERVE    ② DECIDE     ③ RUN        ④ VERIFY           │
 │   ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐        │
 │   │ Read    │  │ Resolve │  │ Dispatch│  │ Run     │        │
 │   │ passport│─►│ deps    │─►│ agent+  │─►│ per-stage│       │
 │   │ + state │  │ find    │  │ skill   │  │ gate    │        │
 │   │         │  │ next    │  │         │  │ checks  │        │
 │   └─────────┘  └─────────┘  └─────────┘  └─────────┘        │
 │        ▲                                         │           │
 │        │                                         ▼           │
 │   ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐        │
 │   │ Analyze │  │ Cascade │  │ Append  │  │ Write   │        │
 │   │ failures│◄─│ stale to│◄─│ to      │◄─│ artifact│       │
 │   │ build   │  │ down-   │  │ passport│  │ hashes  │        │
 │   │ plan    │  │ stream   │  │ ledgers │  │ to      │        │
 │   │         │  │         │  │         │  │ ledger  │        │
 │   └─────────┘  └─────────┘  └─────────┘  └─────────┘        │
 │   ⑦ DIAGNOSE   ⑥ MARK_STALE  ⑤ RECORD                       │
 │                                                              │
 └──────────────────────────────────────────────────────────────┘
```

### Step Details

#### Step 1: OBSERVE — Read Current State

```python
engine.observe()
# Returns: {paper_id, pipeline_state, stages: {name: {status, completed_at, retry_count, has_errors}}, timestamp}
```

Reads the project passport and all stage states. No modifications. This is a pure read operation that provides the current ground truth.

#### Step 2: DECIDE — Determine Next Safe Stage

```python
engine.decide_next_stage()
# Returns: stage_name | None (pipeline complete or blocked)
```

Iterates through all 18 stages in order. For each stage that is not COMPLETED and not at max retries, checks whether all upstream dependencies are COMPLETED. Returns the first eligible stage. Returns `None` if all stages are complete (`CLEAN`) or if no progress is possible (`BLOCKED`).

Decision rules:
- A stage is eligible only when **all** its `upstream` stages are `COMPLETED`
- `FAILED` stages are re-tried if `retry_count < max_retries`
- `STALE` stages are re-run (upstream change detected)
- If no eligible stage exists and not all stages are complete → `BLOCKED`

#### Step 3: RUN — Execute the Stage

```python
engine.run_stage(stage_name)
# Returns: {success, stage, agent, skill}
```

Marks the stage as `RUNNING`, records the start timestamp, transitions pipeline state to `IN_PROGRESS`. The actual execution is handled by the agent/skill assigned to the stage definition. This method sets up the execution context — the `PaperWorkflow._execute_stage()` method in `workflow.py` does the actual dispatch to the agent.

#### Step 4: VERIFY — Run Gate Checks

```python
engine.verify_stage(stage_name)
# Returns: {stage, all_passed, results: [{rule, severity, passed, message}]}
```

Runs the stage-specific gate rules defined in the `StageDefinition.gate_rules` list. All rules must pass for the stage to be marked `COMPLETED`. Any failure sets the stage to `FAILED` and the pipeline to `GATE_FAILURE`.

#### Step 5: RECORD — Persist Artifacts and Sync

```python
engine.record_and_sync()
# Returns: {passport_updated, stale_report: {stale_stages, count}}
```

Two operations:
1. **Record**: Updates the project passport with current stage states. Records all produced artifacts in `artifact_ledger.jsonl` with SHA-256 hashes.
2. **Sync**: Scans downstream stages for staleness. If any upstream stage is `STALE`, marks the dependent stage as `STALE` as well (cascade).

#### Step 6: MARK\_STALE — Cascade Staleness

```python
engine._sync_stale()
# Returns: {stale_stages: [stage_names], count: N}
```

When an upstream artifact changes (detected via hash mismatch in the passport), all downstream stages that depend on it are marked `STALE`. This cascades through the entire dependency chain. For example, if `run_analysis` is re-run, then `verify_methods`, `write_methods`, `write_results`, and everything downstream becomes `STALE`.

#### Step 7: DIAGNOSE — Analyze Failures

```python
engine.diagnose_failures()
# Returns: {failed_stages: N, failures: [{stage, errors, gate_failures, retry_count, max_retries}], revision_needed: bool}
```

Collects all `FAILED` stages, extracts error messages and gate failures, checks retry counts against maximums. Returns a structured diagnosis that the `revision_routing` skill uses to generate revision plans. This is the entry point for the revision cycle.

#### Step 8: REPEAT — Loop Until Terminal State

The cycle repeats from OBSERVE until one of three terminal conditions:
- **CLEAN**: All 18 stages completed successfully
- **BLOCKED**: No eligible stage (unresolvable dependency or max retries exceeded on required stage)
- **HUMAN CHECKPOINT**: Pipeline pauses at a checkpoint stage, waiting for user approval

### Engine State Lifecycle per Stage

```
PENDING ──► RUNNING ──► COMPLETED ──► (upstream changes) ──► STALE ──► (re-run) ──► RUNNING
                │
                ├──► FAILED ──► (retry < max) ──► PENDING
                │         └──► (retry >= max) ──► BLOCKED
                │
                └──► SKIPPED (paper type excludes this stage)
```

### Fuse / Circuit Breaker

The supervision layer includes a fuse mechanism defined in `config/default_config.yaml` under `supervision.fuse`:

| Threshold | Limit | Action |
|-----------|-------|--------|
| Consecutive stage failures | 3 | PAUSE — require human intervention |
| Consecutive gate failures | 5 | PAUSE — too many quality issues |
| Total retry count | 20 | ABORT — systemic issue |
| Agent failure rate | 50% | QUARANTINE — reroute to fallback |
| Time since last success | 4 hours | PAUSE — no progress |
| Disk space | <5 GB | PAUSE — low disk space |

---

## 4. Passport System

The Passport system provides the framework's persistent memory. All state is file-based (not conversation-based), making the pipeline portable across machines and AI sessions.

### Four Ledger Files

```
papers/{paper_id}/
├── project_passport.yaml      # Identity + metadata + stage states (YAML, readable)
├── artifact_ledger.jsonl      # Append-only artifact tracking (JSONL, machine-parsed)
├── checkpoint_ledger.jsonl    # Human decisions at checkpoints (JSONL, append-only)
└── integrity_ledger.jsonl     # Integrity gate events (JSONL, append-only)
```

### File 1: `project_passport.yaml`

**Purpose**: Paper identity and current pipeline state. The single source of truth for "what is this paper and where is it?"

```yaml
paper_id: "paper_test_spatial_20260618"
created_at: "2026-06-18T10:30:00"
updated_at: "2026-06-18T14:22:00"
idea: "Spatial transcriptomics analysis of kidney aging"
field: "spatial transcriptomics, aging, kidney"
target_journal: "Genome Biology"
paper_type: "original_research"
status: "in_progress"
pipeline_state: "in_progress"
stages:
  create_project: {status: completed, completed_at: "..."}
  search_literature: {status: running, started_at: "..."}
  research_plan: {status: pending}
  # ... all 18 stages
metadata:
  version: "1.0"
  total_stages: 18
  completed_stages: 3
```

**Key properties**:
- Human-readable YAML — can be opened and understood without tooling
- Updated on every `record_and_sync()` call
- Contains the canonical stage status for the loop engine's OBSERVE step

### File 2: `artifact_ledger.jsonl`

**Purpose**: Append-only log of every artifact produced by the pipeline. Each entry records the file path, SHA-256 hash, file size, producing stage, and status.

```jsonl
{"path": "manuscript/methods.md", "hash_sha256": "a1b2c3...", "size_bytes": 4521, "stage": "write_methods", "recorded_at": "2026-06-18T11:00:00", "status": "active"}
{"path": "results/differential_expression.csv", "hash_sha256": "d4e5f6...", "size_bytes": 128340, "stage": "run_analysis", "recorded_at": "2026-06-18T12:30:00", "status": "active"}
```

**Status lifecycle**:
- `active` → normal state, hash matches current file
- `modified` → hash changed since last record (drift detected)
- `deleted` → file no longer exists on disk

**Drift detection**: On every `detect_artifact_drift()` call, the passport recomputes SHA-256 for every tracked artifact and compares against the ledger. Any mismatch triggers an `integrity_ledger` event and marks the artifact status as `modified`.

### File 3: `checkpoint_ledger.jsonl`

**Purpose**: Immutable audit trail of every human decision at pipeline checkpoints.

```jsonl
{"checkpoint_id": "cp_create_project_20260618103000", "stage": "create_project", "decision": "approved", "notes": "Research question is clear. Proceed.", "recorded_at": "2026-06-18T10:35:00", "artifacts_snapshot": ["project_passport.yaml", "paper_config.yaml"]}
```

**Why append-only?** Scientific decisions must be auditable. You cannot delete or modify a checkpoint record — you can only append a new one. This ensures a complete paper trail from initial idea to final submission.

### File 4: `integrity_ledger.jsonl`

**Purpose**: Complete history of every integrity gate execution and artifact drift event.

```jsonl
{"event_id": "ie_gate_run_20260618140000", "event_type": "gate_run", "details": {"total_gates": 16, "critical_failures": 0, "high_failures": 2}, "recorded_at": "2026-06-18T14:00:00"}
{"event_id": "ie_drift_detected_20260618141000", "event_type": "drift_detected", "details": {"artifact": "results/de_results.csv", "old_hash": "a1b2...", "new_hash": "c3d4..."}, "recorded_at": "2026-06-18T14:10:00"}
```

### Passport Data Flow

```
Any execution ──► PaperPassport.record_artifact() ──► artifact_ledger.jsonl (append)
                                                    ──► project_passport.yaml (update stage)
Any gate run  ──► PaperPassport.record_integrity_event() ──► integrity_ledger.jsonl (append)
Human decision ──► PaperPassport.record_checkpoint() ──► checkpoint_ledger.jsonl (append)
                                                      ──► project_passport.yaml (update)
Hash mismatch  ──► PaperPassport.detect_artifact_drift() ──► integrity_ledger.jsonl (drift event)
                 ──► PaperPassport.sync_artifact_stale()  ──► project_passport.yaml (mark stages stale)
```

### Export and Portability

```python
passport.export_summary()
# Returns:
# {
#   "paper_id": "paper_test_20260618",
#   "idea": "...",
#   "target_journal": "Genome Biology",
#   "status": "in_progress",
#   "total_artifacts": 47,
#   "total_checkpoints": 3,
#   "total_integrity_events": 12,
#   "artifact_summary": {"active": 42, "modified": 3, "deleted": 2}
# }
```

The entire `papers/{paper_id}/` directory is self-contained and portable. Copy it to another machine, point the framework at it, and the passport provides the complete state needed to resume.

---

## 5. Integrity Gate System

The integrity gate system (`src/paper_workflow/supervision/integrity.py`) enforces 16 automated quality rules across 3 severity levels. It is implemented as a pure checker — it diagnoses but never modifies.

### Gate Architecture

```
IntegrityGateChecker (16 gates)
├── CRITICAL (5 gates: C1-C5) — Pipeline BLOCKED on failure
│   ├── C1: bibtex_citation_existence       → Every \cite{} has BibTeX entry
│   ├── C2: citation_evidence_traceability  → Every citation has evidence record
│   ├── C3: results_no_citations            → Results section has zero \cite{}
│   ├── C4: claim_artifact_binding           → Every claim binds to figure/table
│   └── C5: figures_referenced              → Every \ref{fig:...} points to real file
│
├── HIGH (8 gates: H1-H8) — WARN, must document if not fixed
│   ├── H1: data_availability_statement     → Data Availability section present
│   ├── H2: code_availability_statement     → Code Availability section present
│   ├── H3: no_local_paths                  → No absolute paths in manuscript
│   ├── H4: methods_parameters_complete     → All parameters and versions documented
│   ├── H5: discussion_limitations          → Dedicated Limitations paragraph
│   ├── H6: results_no_overinterpretation   → No causal language for correlations
│   ├── H7: statistics_reported             → Exact p-values + effect sizes + CI
│   └── H8: pseudoreplication_check         → Correct biological replicate unit
│
└── MEDIUM (3 gates: M1-M3) — Advisory only
    ├── M1: section_length_minimum          → Each section meets word count minimum
    ├── M2: no_bullets_in_prose             → Natural prose paragraphs only
    └── M3: figure_count_requirements       → Within journal figure limit
```

### Severity Hierarchy and Pipeline Behavior

| Severity | Count | Pipeline Impact | Resolution Requirement |
|----------|-------|-----------------|----------------------|
| **CRITICAL** | 5 | **BLOCK** — pipeline cannot advance past `integrity_check` or `quality_check` | Must be fixed before proceeding |
| **HIGH** | 8 | **WARN** — logged, must be explicitly accepted or remediated | Document if not fixed; unresolved HIGH failures accumulate |
| **MEDIUM** | 3 | **ADVISORY** — informational only | No resolution required; logged for awareness |

### Gate Execution Order (Optimized)

Gates are executed in an optimized order that detects the fastest, most impactful failures first:

```
1. C3 (Results no-citations)      ← Fast pattern match, blocks if failed
2. C5 (Figure references)         ← Fast cross-reference
3. C1 (Citation traceability)     ← Cross-reference check
4. C2 (Citation integrity)        ← External MCP validation, slowest CRITICAL
5. C4 (Claim-artifact binding)    ← Semantic analysis
6. M1, M2 (Section length, bullets) ← Fast pattern match
7. H1, H2 (Data/code availability)  ← Content presence check
8. H3, H4 (No paths, parameters)    ← Pattern + diff
9. H5, H6 (Limitations, overinterpretation) ← Semantic
10. H7 (Statistics reporting)        ← Pattern match
11. H8 (Pseudoreplication)           ← Semantic + code analysis
12. M3 (Journal format)              ← Spec validation
```

### Gate Check Implementation

Each gate is a method on `IntegrityGateChecker` that returns a `GateResult` dataclass:

```python
@dataclass
class GateResult:
    rule: str          # Gate ID, e.g. "bibtex_citation_existence"
    severity: str      # "critical" | "high" | "medium"
    passed: bool       # True if gate check passed
    message: str       # Human-readable summary
    details: dict      # Structured failure details (missing keys, violations, counts)
    checked_at: str    # ISO 8601 timestamp
```

**Example — C1 (BibTeX existence)**:
1. Parse `library.bib` to extract all `@article{key,` definitions
2. Parse all manuscript sections for `\cite{key}`, `\citep{key}`, `\citet{key}`
3. Compute `missing = cited_keys - bibtex_keys`
4. If `len(missing) > 0` → FAIL with list of missing keys
5. Otherwise → PASS

**Example — H7 (Statistics reported)**:
1. Scan Results for `p [<=>] 0.\d+` patterns (exact p-values)
2. Scan for `β =`, `OR =`, `HR =`, `d =`, `r =` (effect sizes)
3. If either category is missing → FAIL with specifics

### Integrity Report Output

Two formats are generated:
- **Machine-readable**: `integrity_report.json` (full `IntegrityReport.to_dict()`)
- **Human-readable**: `integrity_report.md` (Markdown table with severity-colored results)

### Post-Failure Workflow

```
integrity_check fails CRITICAL
  → Pipeline BLOCKED
  → integrity_checker emits integrity_report.json + .md
  → User runs diagnose-gate-failures (CLI command)
  → team_orchestrator routes each failure to responsible agent
      ├── bibtex failures → literature_reviewer
      ├── claim-binding failures → report_writer
      ├── statistics failures → statistician
      └── format failures → report_writer
  → After fixes, re-run integrity_check
  → All decisions logged to checkpoint_ledger.jsonl
```

---

## 6. Agent System

The framework defines 11 specialized agents, each with an explicit responsibility boundary, input/output contract, tool permissions, and banned operations. Agents operate within the execution layer and are dispatched by the decision layer.

### Agent Roster

#### Coordinator

| Agent | Role | Phases | Stages |
|-------|------|--------|--------|
| `team_orchestrator` | Multi-Agent Coordinator | Cross-cutting (all) | Task decomposition, dispatch, deadlock detection |

**Responsibility**: Task decomposition, agent dispatch, parallel scheduling, deadlock detection, progress tracking, human checkpoint routing. Does NOT execute domain tasks — purely coordination.

**Contract**:
- Input: `task_description`, `available_agents`, optional `priority_matrix`
- Output: `execution_plan`, `agent_assignments`, `progress_report`
- Max parallel subagents: 6

#### Domain Agents (10)

| # | Agent | Role | Phases | Key Stages |
|---|-------|------|--------|------------|
| 1 | `research_strategist` | Research Design & Strategy | 1 | S1, S2, S4 |
| 2 | `literature_reviewer` | Literature Search & Synthesis | 1, 4 | S3, S15 (reviewer persona) |
| 3 | `data_auditor` | Data Quality Audit | 2 | S5 |
| 4 | `figure_planner` | Figure Architecture & Design | 2 | S6 |
| 5 | `analysis_executor` | Data Analysis Execution | 2 | S7 |
| 6 | `pipeline_engineer` | Pipeline Engineering & Reproducibility | 2 | S8 |
| 7 | `statistician` | Statistical Consulting (cross-cutting) | 2, 3, 4 | Async audit after S7, S10; reviewer in S15 |
| 8 | `report_writer` | Manuscript Writing & Assembly | 3, 4, 5, 6 | S9-S13, S16, S18 |
| 9 | `integrity_checker` | Quality Assurance & Gate Enforcement | 4, 5, 6 | S14, S15, S17, S18 |
| 10 | `multi_omics_integrator` | Multi-Omics Integration Specialist | 2 | S7 (multi-omics domain) |

### Responsibility Boundaries (I Do / I Don't Do)

Each agent has an explicit boundary enforced by tool permission allow/deny lists:

| Agent | I DO | I DON'T DO |
|-------|------|------------|
| `research_strategist` | Define questions, assess feasibility, target journals, generate hypotheses | Run code, search literature (delegates to `literature_reviewer`) |
| `literature_reviewer` | Search databases (PubMed, Consensus, Semantic Scholar), build bibliographies, synthesize evidence | Run analysis code, write manuscript sections |
| `data_auditor` | Read and assess data quality, validate metadata, detect batch effects | Modify data, write manuscript text |
| `figure_planner` | Design figure architecture, choose color palettes, specify panel composition | Run analysis, generate figures (delegates to `analysis_executor`) |
| `analysis_executor` | Run R/Python pipelines, generate result tables and figures, log sessions | Design figures (delegates to `figure_planner`), write prose |
| `pipeline_engineer` | Build Docker/conda environments, verify reproducibility, manage dependencies | Run primary analysis (delegates to `analysis_executor`) |
| `statistician` | Review study design, audit test selection, validate statistical reporting | Modify data, write manuscript text (advisory only) |
| `report_writer` | Write IMRAD sections, assemble manuscripts, format for journals | Run analysis, search literature, check integrity (delegates) |
| `integrity_checker` | Run 16 gates, cross-reference citations, verify claim-artifact binding | Modify manuscript, add citations, generate figures |
| `multi_omics_integrator` | Integrate cross-omics data (MOFA, DIABLO), run factor analysis | Design study, write full manuscripts |

### Agent Contract System

Every agent is defined with formal input/output contracts in `config/default_config.yaml`. This enables the `AgentRouter` to validate dispatch decisions:

```yaml
analysis_executor:
  input_contract:
    required: [analysis_spec, input_data_paths]
    optional: [parameter_overrides, output_directory]
  output_contract:
    required: [result_tables, figures, analysis_log, session_info]
    optional: [intermediate_files]
  tool_permissions:
    allow: ["Bash(Rscript **)", "Bash(python **)", Read, Write, Glob, Grep]
    deny: []
  max_parallel_subagents: 2
  timeout_seconds: 7200
```

### Agent Invocation Flow

```
User request / Pipeline stage
       │
       ▼
AgentRouter (config/agent_routing)
  ├── Match task keywords → agent
  ├── Validate input contract
  ├── Check tool permissions
  └── Dispatch agent
       │
       ▼
Agent executes within bounded contract
  ├── Uses allowed tools only
  ├── Produces required output artifacts
  └── Reports completion to team_orchestrator
       │
       ▼
Supervision layer records artifacts in passport
```

### Cross-Cutting Agent: `statistician`

The `statistician` is the only cross-cutting agent — it does not own any single stage but audits three stages asynchronously:

| When | What | Output |
|------|------|--------|
| After `run_analysis` (S7) | Audit test selection, p-values, effect sizes, multiple testing correction | `stats_audit_analysis.md` |
| After `write_results` (S10) | Verify every statistical claim matches analysis output | `stats_audit_results.md` |
| During `internal_review` (S15) | Full statistical review as Reviewer 1 persona | `reviewer1_statistical.md` |

This design prevents the statistician from blocking the pipeline — audits run asynchronously and findings are surfaced at the next checkpoint.

### Three Collaborative Teams

The paper writing team definition (`.claude/teams/paper_writing_team.md`) is the primary team configuration, with 2 additional team configurations referenced in the architecture:

| Team | Purpose | Agents | Coordination Model |
|------|---------|--------|-------------------|
| `paper_writing_team` | Full-cycle manuscript production (primary) | All 9 domain agents + coordinator | `team_orchestrator` dispatches, agents execute |
| `review_team` | Internal peer review | `integrity_checker` + `statistician` + `literature_reviewer` | Parallel review, synthesized report |
| `analysis_team` | Data analysis pipeline | `analysis_executor` + `pipeline_engineer` + `data_auditor` | Sequential with async validation |

---

## 7. Skill System

Skills are reusable workflow templates defined as Markdown files in `.claude/skills/`. Unlike agents (which are executors with tool permissions), skills are procedural knowledge — they define the "how" of a task, while the agent provides the "who."

### Skill Roster (12 Skills)

| # | Skill | Purpose | Used By | Trigger Keywords |
|---|-------|---------|---------|-----------------|
| 1 | `topic_research` | Research topic exploration, feasibility, journal targeting | `research_strategist` | topic, research question, feasibility, journal target, PICO |
| 2 | `literature_search` | Systematic literature search, citation management, evidence synthesis | `literature_reviewer` | literature, search, citation, bibliography, PRISMA |
| 3 | `paper_loop` | Main loop engine — observe→decide→run→verify pipeline orchestration | `team_orchestrator` | pipeline, workflow, loop, stage, automate, orchestrate |
| 4 | `figure_planning` | Figure architecture, panel composition, color design | `figure_planner` | figure, plot, visualization, panel, chart, color palette |
| 5 | `paper_writing` | IMRAD manuscript writing, assembly, formatting | `report_writer` | write, manuscript, draft, abstract, methods, results, discussion |
| 6 | `revision_routing` | Revision planning, reviewer response, targeted fixes | `report_writer`, `integrity_checker` | revision, reviewer, response, rebuttal, revise |
| 7 | `qc_pipeline` | Quality control, integrity checking, gate enforcement | `data_auditor`, `integrity_checker` | check, verify, validate, integrity, gate, quality, audit |
| 8 | `spatial_analysis` | Spatial transcriptomics: deconvolution, domain detection, spatial statistics | `analysis_executor` | spatial, stereo-seq, visium, deconvolution, spatial domain, SVG |
| 9 | `pathway_inference` | Pathway enrichment, gene set analysis, network biology | `analysis_executor` | pathway, enrichment, GO, KEGG, GSEA, gene set, Reactome |
| 10 | `statistical_testing` | Statistical testing, power analysis, model diagnostics | `statistician`, `analysis_executor` | statistic, test, p-value, power analysis, regression, effect size |
| 11 | `multi_omics` | Multi-omics integrative analysis: MOFA, DIABLO, cross-omics correlation | `multi_omics_integrator`, `analysis_executor` | multi-omics, integration, MOFA, DIABLO, cross-omics |
| 12 | `reproducibility` | Reproducibility checks: environment, seeds, paths, Docker | `pipeline_engineer` | reproducible, docker, environment, conda, renv, seed, snapshot |

### Skill Invocation Patterns

Skills are invoked through two mechanisms:

#### Pattern 1: Pipeline Stage Dispatch

The `PaperLoopEngine` maps each stage to an agent+skill pair in the `StageDefinition`:

```python
StageDefinition(
    name="write_methods",
    agent="report_writer",      # WHO executes
    skill="paper_writing",      # HOW to execute
    ...
)
```

The `PaperWorkflow._execute_stage()` method reads these fields and dispatches accordingly.

#### Pattern 2: Keyword-Based Routing

The `SkillsDispatcher` (configured in `config/default_config.yaml` under `skills_dispatcher`) uses keyword-weighted matching to route free-form user requests to the appropriate skill:

```yaml
skills_dispatcher:
  routing_strategy: "max_score_with_chain"
  min_confidence_threshold: 0.6

  paper_writing:
    triggers:
      - {keywords: [write, manuscript, draft, abstract, introduction, methods, results, discussion, section, paragraph], weight: 10}
      - {keywords: [edit, revise, format, assemble, compile], weight: 5}
    chained_skills: [revision_routing, qc_pipeline, reproducibility]
```

**Chaining**: When the top-scoring skill specifies `chained_skills`, those skills are automatically queued to run after the primary skill completes. This enables multi-step workflows from a single user request (e.g., "write methods" → chains `qc_pipeline` → chains `reproducibility`).

### Skill Hierarchy

```
paper_loop (meta-skill — orchestrates the pipeline)
├── topic_research ──────── chains → literature_search
├── literature_search ───── chains → paper_writing, topic_research
├── figure_planning ─────── chains → paper_writing, statistical_testing
├── paper_writing ───────── chains → revision_routing, qc_pipeline, reproducibility
├── revision_routing ────── chains → paper_writing, qc_pipeline
├── qc_pipeline ─────────── chains → reproducibility, revision_routing
├── spatial_analysis ────── chains → statistical_testing, figure_planning
├── pathway_inference ───── chains → statistical_testing, figure_planning
├── statistical_testing ─── chains → figure_planning, paper_writing
├── multi_omics ─────────── chains → statistical_testing, pathway_inference, figure_planning
└── reproducibility ─────── chains → qc_pipeline
```

---

## 8. Data Flow Between Layers

### Artifact Flow Diagram

```
USER INPUT (idea, field, journal)
       │
       ▼
┌─────────────────────────────────────────────────────────────────┐
│ STRATEGY LAYER                                                  │
│                                                                 │
│  idea string ──► TopicSelector ──► ResearchTopic dataclass      │
│  topic + journal name ──► JournalTargeter ──► JournalTarget     │
│  topic + journal ──► FeasibilityAssessor ──► FeasibilityReport  │
│  topic + feasibility ──► HypothesisFramework ──► H1-H4          │
│                                                                 │
│  Output: ResearchStrategy (saved as strategy/{id}.yaml)         │
└──────────────────────────────┬──────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│ DECISION LAYER                                                  │
│                                                                 │
│  ResearchStrategy ──► PaperLoopEngine.initialize()              │
│  Loop: observe() → decide_next_stage() → dispatch               │
│                                                                 │
│  Output: stage dispatch = {agent, skill, parameters}            │
└──────────────────────────────┬──────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│ EXECUTION LAYER                                                 │
│                                                                 │
│  Agent receives dispatch ──► executes bounded task             │
│  Produces:                                                      │
│    - Manuscript sections (.md, .tex, .docx)                    │
│    - Figures (.pdf, .svg, .tiff)                               │
│    - Result tables (.csv)                                       │
│    - Analysis scripts (.R, .py)                                 │
│    - Environment snapshots (.yaml, Dockerfile)                  │
│    - Citation library (.bib)                                    │
│    - Evidence tables (.csv, .jsonl)                             │
│                                                                 │
│  Output: Physical artifacts on disk in papers/{paper_id}/       │
└──────────────────────────────┬──────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│ SUPERVISION LAYER                                               │
│                                                                 │
│  For each artifact:                                             │
│    PaperPassport.record_artifact(path, stage, sha256)           │
│      → artifact_ledger.jsonl (append)                           │
│      → project_passport.yaml (update stage)                     │
│                                                                 │
│  On pipeline events:                                            │
│    PaperPassport.record_integrity_event(type, details)          │
│      → integrity_ledger.jsonl (append)                          │
│                                                                 │
│  On human decisions:                                            │
│    PaperPassport.record_checkpoint(stage, decision)             │
│      → checkpoint_ledger.jsonl (append)                         │
│                                                                 │
│  On gate execution:                                             │
│    IntegrityGateChecker.run_all_checks(sections, bibtex, ...)   │
│      → IntegrityReport → integrity_report.json + .md            │
│      → If CRITICAL failure → pipeline_state = GATE_FAILURE      │
│                                                                 │
│  On artifact change:                                            │
│    PaperPassport.detect_artifact_drift()                        │
│      → Drifted artifacts list                                   │
│    PaperPassport.sync_artifact_stale(dep_map)                   │
│      → Downstream stages marked STALE                           │
│      → pipeline_state = STALE_STAGES                            │
└─────────────────────────────────────────────────────────────────┘
```

### Cross-Layer Event Flow

The loop engine coordinates cross-layer flow through these specific event sequences:

**Normal Stage Progression**:
```
DECISION: decide_next_stage() → "write_methods"
EXECUTION: run_stage("write_methods") → RUNNING
EXECUTION: agent produces artifacts
SUPERVISION: record_artifact() for each artifact
DECISION: verify_stage("write_methods") → gate checks pass
SUPERVISION: project_passport.yaml updated → COMPLETED
DECISION: record_and_sync() → check for stale downstream
```

**Artifact Drift Cascade**:
```
SUPERVISION: detect_artifact_drift() finds "results/de_results.csv" modified
SUPERVISION: sync_artifact_stale() marks verify_methods, write_methods, write_results as STALE
DECISION: pipeline_state → STALE_STAGES
DECISION: decide_next_stage() → first STALE stage in dependency order
EXECUTION: re-run stale stage
```

**Gate Failure Recovery**:
```
DECISION: verify_stage("integrity_check") → gate CRITICAL failure
SUPERVISION: pipeline_state → GATE_FAILURE
DECISION: decide_next_stage() → None (BLOCKED)
USER: runs diagnose-gate-failures
DECISION: diagnosis → revision plan
EXECUTION: agents fix failures
DECISION: re-run integrity_check → gates pass → CLEAN
```

---

## 9. Extension Points for New Domains

The framework is designed to be extended without modifying core code. All domain-specific configuration is externalized in YAML files.

### Extension Point 1: New Research Domain

Add a new domain section to `config/default_config.yaml` under `research_domains`:

```yaml
research_domains:
  proteomics:                        # NEW DOMAIN
    name: "Proteomics"
    description: "Mass spectrometry-based proteomics analysis."
    keywords:
      primary: [proteomics, mass spectrometry, protein expression, PTM]
      secondary: [TMT, LFQ, DIA, DDA, phosphoproteomics, interactomics]
    common_methods:
      - {name: "Differential Protein Expression", tools: [limma, DEP, MSstats],
         reporting: [log2FC, p-value, adjusted p-value]}
      - {name: "Pathway Enrichment", tools: [clusterProfiler, ReactomePA],
         reporting: [enrichment score, FDR, gene ratio]}
    repositories: [PRIDE, ProteomeXchange, MassIVE]
    common_pitfalls:
      - "Missing value imputation method not justified"
      - "Batch effects between TMT plexes"
      - "Normalization method not appropriate for data distribution"
```

No code changes required. The `TopicSelector`, `FeasibilityAssessor`, and `HypothesisFramework` read domain keywords from config.

### Extension Point 2: New Journal

Add a new journal entry to `config/journal_database.yaml` under `journals`:

```yaml
journals:
  New Journal Name:
    full_name: "Full Journal Name"
    impact_factor: 5.0
    category: specialty-open
    format_type: LaTeX
    citation_style: Vancouver
    abstract_word_limit: 250
    figure_limit: 8
    main_text_word_limit: 5000
    requires_data_availability: true
    requires_code_availability: true
    open_access: true
    submission_system: "Editorial Manager"
    special_requirements: ["Data availability statement", "ORCID required"]
    scope_keywords: [genomics, bioinformatics, computational biology]
```

The `JournalTargeter` will automatically resolve this by name and include it in recommendations.

### Extension Point 3: New Paper Type

Add a new entry under `paper_types` in `config/default_config.yaml`:

```yaml
paper_types:
  perspective:                       # NEW TYPE
    name: "Perspective / Opinion"
    pipeline_mode: opinion_focused
    required_stages: [select_topic, target_journal, literature_search,
                      write_introduction, write_discussion, assemble_manuscript,
                      integrity_check, finalize]
    skipped_stages: [formulate_hypotheses, data_audit, figure_planning,
                     run_analysis, verify_methods, write_methods,
                     write_results, internal_review, apply_revision, re_review]
    word_limits: {abstract: 150, introduction: 1500, discussion: 2500, total: 4000}
    figure_limits: {main_figures: 1, supplementary_figures: 0, tables: 1}
    structure: [abstract, main_text, references, competing_interests]
    reporting_guidelines: []
    required_gate_severities: [CRITICAL]
    optional_gate_severities: [HIGH, MEDIUM]
```

The `PaperLoopEngine` will automatically include only the `required_stages` in the pipeline.

### Extension Point 4: New Integrity Gate

Add a new gate definition to `config/default_config.yaml` under `quality_gates`:

```yaml
quality_gates:
  g17_reproducibility_score:         # NEW GATE
    id: g17
    name: "Reproducibility Score"
    severity: HIGH
    description: "Analysis must achieve a reproducibility score above threshold."
    category: [reproducibility, rigor]
    check: {type: threshold, source: reproducibility_report.md, method: extract_score}
    thresholds: {min_score: 0.8}
    failure_action: "WARN — improve reproducibility before submission."
    auto_fix: false
```

Then add the check method to `IntegrityGateChecker` and include the gate in `run_all_checks()`. New gate IDs are automatically picked up by the reporting system.

### Extension Point 5: New Agent

Define the agent in `config/default_config.yaml` under `agent_routing.agents`:

```yaml
agent_routing:
  agents:
    imaging_analyst:                 # NEW AGENT
      agent_id: "imaging_analyst"
      role: "Imaging Data Analysis"
      expertise: [image_segmentation, feature_extraction, spatial_statistics]
      triggers: ["Analyze images", "Segment cells", "Extract features", "Image quantification"]
      input_contract:
        required: [image_paths, analysis_spec]
        optional: [segmentation_model, output_format]
      output_contract:
        required: [segmentation_masks, feature_table, analysis_report]
        optional: [visualization_outputs]
      tool_permissions:
        allow: ["Bash(python **)", Read, Write, Glob]
        deny: []
      max_parallel_subagents: 1
      skills: [spatial_analysis, statistical_testing]
```

Create the agent definition file in `.claude/agents/imaging_analyst.md` with the I Do / I Don't Do boundaries. Assign the agent to relevant pipeline stages by modifying `StageDefinition` entries.

### Extension Point 6: New CLI Command

Add a new subparser and handler to `src/paper_workflow/cli/main.py`:

```python
# In main():
p = sub.add_parser("export-provenance")
p.add_argument("--paper", required=True)
p.add_argument("--format", choices=["json", "pdf"], default="json")

# Handler:
def cmd_export_provenance(args):
    # ... implementation

# Register:
{"export-provenance": cmd_export_provenance, ...}
```

### Extension Point 7: Config Override per Paper

Every paper can override the default configuration by creating `papers/{paper_id}/paper_config.yaml`. The framework merges this with `config/default_config.yaml` at initialization time, with per-paper settings taking precedence. This allows paper-specific journal requirements, gate thresholds, and stage timeouts without modifying the global config.

### Summary: What Can Be Extended Without Code Changes

| Extension | Mechanism | Code Change Required? |
|-----------|-----------|----------------------|
| New research domain | `config/default_config.yaml` → `research_domains` | No |
| New journal | `config/journal_database.yaml` → `journals` | No |
| New paper type | `config/default_config.yaml` → `paper_types` | No |
| New integrity gate | `config/default_config.yaml` → `quality_gates` + add check method | Yes (check method) |
| New agent | `config/default_config.yaml` → `agent_routing` + `.claude/agents/` definition | No (definition only) |
| New skill | `.claude/skills/new_skill.md` + config entry | No |
| New CLI command | `cli/main.py` → add subparser + handler | Yes (handler function) |
| Per-paper overrides | `papers/{paper_id}/paper_config.yaml` | No |

---

## 10. Comparison with Draftpaper\_loop Design Principles

The framework's loop engine design draws from Draftpaper\_loop principles — a methodology for iterative, stateful document production where each cycle improves the draft through structured observation, targeted revision, and quality verification.

### Core Design Principles Compared

| Principle | Draftpaper\_loop | Research Paper Workflow |
|-----------|-----------------|------------------------|
| **Statefulness** | Document state tracked via explicit version markers | Full passport system with 4 append-only ledgers and SHA-256 artifact hashing |
| **Iteration** | Single document loop: draft → review → revise | 18-stage pipeline with nested revision loop (S15→S16→S17, max 5 cycles) |
| **Observability** | Manual "what changed?" inspection | Automated `observe()` returning structured stage state + artifact drift detection |
| **Quality gates** | Ad-hoc checklist before "done" | 16 automated gates across 3 severity levels, CRITICAL gates block pipeline |
| **Reversibility** | "Save as new version" manual approach | Append-only ledgers ensure every state transition is auditable; SHA-256 hashes detect any artifact modification |
| **Human-in-the-loop** | Reviewer provides comments | 6 structured human checkpoints at critical decision points with explicit approve/reject/revision_needed protocol |
| **Parallelism** | Single-threaded review | 3 parallel execution opportunities (S2\|S3, S11\|S10, S15 reviewers), ~75 min saved |
| **Domain coupling** | Tightly coupled to document type | Fully externalized — all domain config in YAML, pipeline adapts by paper type |

### Key Architectural Differences

#### 1. From Single Loop to Layered Pipeline

Draftpaper\_loop operates on a single document with one revision loop. The Research Paper Workflow decomposes paper production into 4 layers:

```
Draftpaper_loop:        [Draft] → [Review] → [Revise] → [Done]
                              ↑________________________|

Research Paper:          STRATEGY → EXECUTION → DECISION → SUPERVISION
                         (plan)     (build)     (write)    (enforce)
                                                           ↑
                         Revision loop: [S15→S16→S17] _____|
```

This decomposition allows independent optimization of each layer. Strategy can change without re-executing analysis. Writing can be revised without re-running experiments. Supervision runs continuously, not just at the end.

#### 2. From Manual State to Automated Provenance

Draftpaper\_loop relies on the user to track what changed between iterations. The Research Paper Workflow automates this through:

- **SHA-256 hashing** of every artifact → any modification is automatically detected
- **Append-only ledgers** → complete audit trail from idea to submission
- **Stale cascade** → when an upstream artifact changes, all dependent downstream stages are automatically marked STALE
- **Drift detection** → `detect_artifact_drift()` compares current hashes against ledger on demand

#### 3. From Ad-Hoc Review to Multi-Agent QA

Draftpaper\_loop uses a single reviewer (human or AI). The Research Paper Workflow deploys:

- **16 automated integrity gates** that run before any human review — catching mechanical errors (missing citations, bullet points in prose, absolute paths) automatically
- **3+ independent reviewer personas** in Stage 15 (statistical, literature, general, plus optional Devil's Advocate)
- **Async statistical auditing** by the `statistician` agent that cross-validates analysis output against written results

#### 4. From Single-Author to Team Coordination

Draftpaper\_loop assumes a single author/editor. The Research Paper Workflow supports:

- **11 specialized agents** with bounded contracts — each does one thing well
- **Formal I/O contracts** — agents know exactly what they receive and must produce
- **Banned tool lists** — agents physically cannot exceed their authority (e.g., `report_writer` cannot run R scripts)
- **Team orchestration** — `team_orchestrator` handles task decomposition, parallel scheduling, and deadlock detection

#### 5. From One-Document to Six Paper Types

Draftpaper\_loop is designed for a single document structure. The Research Paper Workflow supports 6 paper types (`original_research`, `methods`, `review`, `clinical_research`, `data_resource`, `brief_communication`) by selecting different subsets of the 18-stage pipeline. The same framework produces a 6,500-word original research article or a 2,500-word brief communication without code changes — only configuration.

### Design Decisions Preserved from Draftpaper\_loop

Despite the architectural expansion, three core Draftpaper\_loop principles are preserved:

1. **Main thread plans and integrates.** The `PaperWorkflow` class (main thread) coordinates all activity. Subagents execute, review, and report — they never make top-level decisions about pipeline progression.

2. **Every claim must be bound to evidence.** The C4 gate (`claim_artifact_binding`) enforces what Draftpaper\_loop does manually — every factual claim must trace to a specific figure, table, or statistical output. Claims without evidence are CRITICAL failures that block the pipeline.

3. **The loop never ends without a quality verdict.** The pipeline cannot reach `CLEAN` state until all 16 integrity gates pass (at minimum, all CRITICAL gates). This is the automated equivalent of Draftpaper\_loop's "reviewer sign-off" requirement.

### When to Use Each Approach

| Scenario | Use Draftpaper\_loop | Use Research Paper Workflow |
|----------|---------------------|----------------------------|
| Single short paper (<3,000 words) | Good fit | Overkill |
| First draft of any paper | Good fit (rapid iteration) | Good fit (structured pipeline) |
| Multi-author collaborative paper | Weak (no coordination primitives) | Strong (team orchestration, contracts) |
| Paper with complex analysis pipeline | Weak (no analysis tracking) | Strong (full analysis → methods traceability) |
| Journal with strict formatting requirements | Manual compliance | Automated (journal database + gate M3) |
| Paper requiring reproducibility audit | Manual | Automated (Stage 8 + gate H3, H4) |
| Series of similar papers (lab pipeline) | Repetitive | Reusable (config-driven, per-paper overrides) |

---

## Appendix A: File-to-Layer Mapping

```
src/paper_workflow/
├── strategy/                         # STRATEGY LAYER
│   ├── topic_selector.py             #   Idea → structured topic
│   ├── journal_targeter.py           #   Journal name → JournalTarget
│   ├── feasibility.py                #   4-dim assessment → Go/No-Go
│   ├── hypothesis_framework.py       #   Topic → H1-H4 hypotheses
│   └── research_strategy.py          #   Top-level orchestrator
├── engine/                           # DECISION LAYER
│   └── loop_engine.py                #   18-stage state machine
├── cli/                              # EXECUTION LAYER (user interface)
│   └── main.py                       #   12 CLI commands
├── supervision/                      # SUPERVISION LAYER
│   ├── passport.py                   #   4-file ledger system
│   └── integrity.py                  #   16-rule gate checker
└── workflow.py                       # CROSS-LAYER: Unified orchestrator

.claude/                              # EXECUTION LAYER (agent/skill/team definitions)
├── agents/                           #   11 agent definition files
├── skills/                           #   12 skill workflow templates
└── teams/                            #   3 team configurations

config/                               # CONFIGURATION (externalized domain knowledge)
├── default_config.yaml               #   Master config: pipeline, agents, skills, gates,
│                                     #     paper types, domains, supervision
├── journal_database.yaml             #   25 journals across 6 tiers
└── templates/                        #   Paper section templates
```

## Appendix B: Key Data Structures

### ResearchStrategy
```python
@dataclass
class ResearchStrategy:
    strategy_id: str
    created_at: str
    topic: Optional[ResearchTopic]          # From TopicSelector
    journal_target: Optional[JournalTarget]  # From JournalTargeter
    feasibility: Optional[FeasibilityReport] # From FeasibilityAssessor
    hypotheses: list[Hypothesis]            # From HypothesisFramework
    timeline_weeks: int = 8
    phases: list[dict]
    risks: list[dict]
    dependencies: list[dict]
    status: str  # "draft" | "ready" | "in_progress" | "completed"
```

### StageDefinition
```python
@dataclass
class StageDefinition:
    name: str                    # e.g., "write_results"
    description: str
    phase: int                   # 1-6
    category: str                # "research" | "analysis" | "writing" | "review" | "finalize"
    upstream: list[str]          # Dependency stage names
    downstream: list[str]        # Stages that depend on this one
    required_artifacts: list[str]
    produces_artifacts: list[str]
    gate_rules: list[dict]       # [{rule, severity}]
    agent: str                   # Agent ID
    skill: str                   # Skill ID
    human_checkpoint: bool
    max_retries: int = 3
    timeout_minutes: int = 30
```

### IntegrityReport
```python
@dataclass
class IntegrityReport:
    report_id: str
    paper_id: str
    checked_at: str
    results: list[GateResult]
    passed: bool                 # True only if ALL gates passed
    critical_failures: int       # Pipeline-blocking failures
    high_failures: int           # Must-document failures
    medium_failures: int         # Advisory failures
    low_failures: int

    @property
    def blocks_pipeline(self) -> bool:
        return self.critical_failures > 0
```

## Appendix C: Configuration File Sizes

| File | Lines | Purpose |
|------|-------|---------|
| `config/default_config.yaml` | 1,337 | Master configuration (pipeline, agents, skills, gates, domains, supervision) |
| `config/journal_database.yaml` | 1,148 | 25 journals across 6 tiers with formatting requirements |
| `config/templates/methods_template.md` | — | Methods section template |
| `config/templates/results_template.md` | — | Results section template |
| `.claude/teams/paper_writing_team.md` | 2,421 | Full team configuration with 18-stage details, checkpoint configs, dependency graph |

---

*Architecture document version 1.0.0. Synced with framework version 1.0.0. Last updated 2026-06-18.*
