# Historical Note

This blueprint predates the next-generation V4 truth layer. Use
`docs/NEXT_GEN_V4_TRUTH_LAYER.md` for the current 20-stage workflow,
`WorkflowAPI`, agent harness, and validation commands.

# Research Paper Workflow v2 — Framework Blueprint

**Version**: 1.0.0 | **Generated**: 2026-06-19 | **Source**: `config/default_config.yaml` + `src/paper_workflow/engine/loop_engine.py`

A deterministic, auditable, multi-agent pipeline for academic paper production — 18 stages, 12 agents, 28 registered skills, 16 integrity gates, 4-layer architecture, 6 paper types, 5 research domains.

---

## Table of Contents

1. [Complete 18-Stage Pipeline Flow](#1-complete-18-stage-pipeline-flow)
2. [Agent Dispatch Matrix](#2-agent-dispatch-matrix)
3. [Skill-to-Agent-to-Stage Routing](#3-skill-to-agent-to-stage-routing)
4. [Integrity Gate Activation Map](#4-integrity-gate-activation-map)
5. [Data Flow Architecture](#5-data-flow-architecture)
6. [Extension Architecture](#6-extension-architecture)
7. [Complete File Manifest](#7-complete-file-manifest)

---

## 1. Complete 18-Stage Pipeline Flow

### 1.1 Phase-Grouped ASCII Flow Diagram

```
                         RESEARCH PAPER WORKFLOW v2 — 18-STAGE PIPELINE
                   6 Phases · 12 Agents · 16 Integrity Gates · 7 Human Checkpoints


PHASE 1: RESEARCH & PLANNING (Stages 1–4)
═══════════════════════════════════════════════════════════════════════════════════════

  [USER IDEA]
      │
      ▼
  ┌────────────────────────────────────────────────────────────────────────────────┐
  │ S1: select_topic                           Agent: research_strategist          │
  │     "Select Research Topic & Assess Feasibility"                               │
  │     Skill: topic_research, deep-research                                       │
  │     ⏱ 30min  │  🔴 CP-1 HUMAN CHECKPOINT  │  Produces: topic_proposal.md      │
  │                                             │            feasibility_assessment.md│
  └───────────────────────┬────────────────────────────────────────────────────────┘
                          │
                    ┌─────┴─────┐
                    ▼           ▼
  ┌──────────────────────────┐ ┌──────────────────────────────────────────────────┐
  │ S2: target_journal       │ │ S3: literature_search                            │
  │     "Select Target       │ │     "Systematic Literature Search & Review"      │
  │      Journal"            │ │                                                  │
  │ Agent: research_strategist│ │ Agent: literature_reviewer                       │
  │ Skill: deep-research,    │ │ Skill: deep-research, nature-academic-search,    │
  │        nature-academic-  │ │        nature-citation                           │
  │        search            │ │ ⏱ 60min  │  Produces: literature_review.md,     │
  │ ⏱ 20min                  │ │           │            references.bib,           │
  │ Produces: journal_       │ │           │            citation_map.yaml          │
  │ selection_report.md,     │ │                                                  │
  │ journal_requirements.yaml│ │                                                  │
  └────────────┬─────────────┘ └──────────────────────┬───────────────────────────┘
               │                                      │
               └──────────────────┬───────────────────┘
                                  │  [MERGE POINT — both S2 and S3 must complete]
                                  ▼
  ┌────────────────────────────────────────────────────────────────────────────────┐
  │ S4: formulate_hypotheses                   Agent: research_strategist          │
  │     "Formulate Research Hypotheses & Study Design"                             │
  │     Skill: scientific-writing, topic_research                                  │
  │     Depends on: S1 + S2 + S3                                                  │
  │     ⏱ 15min  │  🔴 CP-2 HUMAN CHECKPOINT  │  Produces: hypotheses_document.md │
  │                                             │            research_questions.yaml│
  └────────────────────────────────────────────────────────────────────────────────┘
                          │
                          ▼  [GATE: hypotheses not testable? → retry or abort]


PHASE 2: DATA & METHODS (Stages 5–8)
═══════════════════════════════════════════════════════════════════════════════════════

  ┌────────────────────────────────────────────────────────────────────────────────┐
  │ S5: data_audit                             Agent: data_auditor                 │
  │     "Data Audit & Validation"                                                   │
  │     Skill: nature-data, qc_pipeline                                             │
  │     ⏱ 40min  │  Produces: data_audit_report.md, data_availability_statement.md │
  └───────────────────────┬────────────────────────────────────────────────────────┘
                          │
                          ▼
  ┌────────────────────────────────────────────────────────────────────────────────┐
  │ S6: figure_planning                        Agent: figure_planner               │
  │     "Figure Planning & Visual Storytelling Design"                              │
  │     Skill: figure_planning, nature-figure                                       │
  │     Depends on: S4 + S5                                                         │
  │     ⏱ 30min  │  🔴 CP-3 HUMAN CHECKPOINT  │  Produces: figure_plan.md         │
  │                                             │            figure_specifications.yaml│
  └───────────────────────┬────────────────────────────────────────────────────────┘
                          │
                          ▼
  ┌────────────────────────────────────────────────────────────────────────────────┐
  │ S7: run_analysis                           Agent: analysis_executor            │
  │     "Run Computational Analysis Pipeline"                                       │
  │     Skill: spatial_analysis, statistical_testing, pathway_inference, qc_pipeline│
  │     Depends on: S5 + S6                                                         │
  │     ⏱ 120min (longest stage) │  Produces: analysis_results.yaml, figures/,     │
  │                               │            statistical_outputs/                 │
  └───────────────────────┬────────────────────────────────────────────────────────┘
                          │
                          ▼
  ┌────────────────────────────────────────────────────────────────────────────────┐
  │ S8: verify_methods                         Agent: pipeline_engineer            │
  │     "Verify Methods & Reproducibility"                                         │
  │     Skill: qc_pipeline, statistical_testing                                    │
  │     ⏱ 20min  │  ⚡ GATE: all_outputs_exist [CRITICAL]                          │
  │              │  ⚡ GATE: code_reproducible  [CRITICAL]                          │
  │              │  Produces: methods_verification_report.md                       │
  └────────────────────────────────────────────────────────────────────────────────┘
                          │
                          ▼  [GATE: reproducibility failure? → retry or abort]


PHASE 3: WRITING (Stages 9–12)
═══════════════════════════════════════════════════════════════════════════════════════

  ┌────────────────────────────────────────────────────────────────────────────────┐
  │ S9: write_methods                          Agent: report_writer                │
  │     "Write Methods Section — Complete, Reproducible Detail"                    │
  │     Skill: scientific-writing, nature-writing                                  │
  │     ⏱ 40min  │  🔴 CP-4 HUMAN CHECKPOINT  │  ⚡ no_local_paths [CRITICAL]     │
  │              │  ⚡ parameters_complete [HIGH]│  Produces: methods_section.md    │
  └───────────────────────┬────────────────────────────────────────────────────────┘
                          │
          ┌───────────────┼───────────────┐
          ▼               │               ▼
  ┌──────────────────┐    │    ┌──────────────────────────────────────────────────┐
  │ S10: write_results│    │    │ S11: write_introduction                         │
  │     "Write Results│    │    │     "Write Introduction — Literature-Grounded   │
  │      Section"     │    │    │      Background"                                │
  │ Agent: report_    │    │    │ Agent: report_writer                            │
  │        writer     │    │    │ Skill: scientific-writing, nature-writing,      │
  │ Skill: scientific-│    │    │        nature-academic-search                   │
  │        writing,   │    │    │ Depends on: S3 + S4                             │
  │        nature-    │    │    │ ⏱ 40min │ 🔴 CP-5 HUMAN CHECKPOINT             │
  │        writing,   │    │    │ ⚡ citations_exist_in_bibtex [CRITICAL]         │
  │        nature-    │    │    │ Produces: introduction_section.md               │
  │        polishing  │    │    └──────────────────────┬──────────────────────────┘
  │ Depends on: S8 +  │    │                           │
  │             S6    │    │                           │
  │ ⏱ 60min           │    │                           │
  │ 🔴 CP-5 HUMAN     │    │                           │
  │ ⚡ no_citations_   │    │                           │
  │ in_results [CRIT] │    │                           │
  │ ⚡ figures_        │    │                           │
  │ referenced [CRIT] │    │                           │
  │ Produces:         │    │                           │
  │ results_section.md│    │                           │
  │ claims_evidence_  │    │                           │
  │ table.md          │    │                           │
  └────────┬─────────┘    │                           │
           │              │                           │
           └──────────────┼───────────────────────────┘
                          ▼
  ┌────────────────────────────────────────────────────────────────────────────────┐
  │ S12: write_discussion                      Agent: report_writer                │
  │     "Write Discussion — Interpretation, Limitations, Future Directions"        │
  │     Skill: scientific-writing, nature-writing, nature-polishing                │
  │     Depends on: S3 + S10                                                       │
  │     ⏱ 50min  │  🔴 CP-6 HUMAN CHECKPOINT                                      │
  │              │  ⚡ citations_exist_in_bibtex  [CRITICAL]                        │
  │              │  ⚡ limitations_discussed      [HIGH]                            │
  │              │  Produces: discussion_section.md                                 │
  └────────────────────────────────────────────────────────────────────────────────┘
                          │
                          ▼  [ALL FOUR IMRAD SECTIONS COMPLETE]


PHASE 4: ASSEMBLY & REVIEW (Stages 13–15)
═══════════════════════════════════════════════════════════════════════════════════════

  ┌────────────────────────────────────────────────────────────────────────────────┐
  │ S13: assemble_manuscript                   Agent: report_writer                │
  │     "Assemble Full Manuscript — Merge All Sections"                             │
  │     Skill: scientific-writing, nature-writing, nature-polishing,               │
  │            nature-citation, nature-figure, nature-data                         │
  │     Depends on: S9 + S10 + S11 + S12    [MERGE POINT — ALL SECTIONS]           │
  │     ⏱ 60min  │  🔴 CP-7 HUMAN CHECKPOINT                                      │
  │              │  Produces: manuscript_draft.md, manuscript_draft.pdf            │
  └───────────────────────┬────────────────────────────────────────────────────────┘
                          │
                          ▼
  ┌────────────────────────────────────────────────────────────────────────────────┐
  │ S14: integrity_check                       Agent: integrity_checker            │
  │     "Run Full 16-Gate Integrity & Quality Check"                               │
  │     Skill: qc_pipeline, nature-data, nature-citation                           │
  │     ⚡ bibtex_citation_existence       [CRITICAL] ← BLOCKS PIPELINE             │
  │     ⚡ citation_evidence_traceability  [CRITICAL] ← BLOCKS PIPELINE             │
  │     ⚡ results_no_citations            [CRITICAL] ← BLOCKS PIPELINE             │
  │     ⚡ claim_artifact_binding          [CRITICAL] ← BLOCKS PIPELINE             │
  │     ⚡ figures_referenced              [CRITICAL] ← BLOCKS PIPELINE             │
  │     ⚡ data_availability_statement     [HIGH]                                   │
  │     ⚡ code_availability_statement     [HIGH]                                   │
  │     ⚡ no_local_paths                  [HIGH]                                   │
  │     ⚡ methods_parameters_complete     [HIGH]                                   │
  │     ⚡ discussion_limitations          [HIGH]                                   │
  │     ⚡ results_no_overinterpretation   [HIGH]                                   │
  │     ⚡ statistics_reported             [HIGH]                                   │
  │     ⚡ pseudoreplication_check         [HIGH]                                   │
  │     ⚡ section_length_minimum          [MEDIUM]                                 │
  │     ⚡ no_bullets_in_prose             [MEDIUM]                                 │
  │     ⚡ figure_count_requirements       [MEDIUM]                                 │
  │     ⏱ 40min  │  Produces: integrity_report.yaml, quality_gate_results.yaml    │
  └───────────────────────┬────────────────────────────────────────────────────────┘
                          │  [ANY CRITICAL FAILURE → STAGE FAILED → PIPELINE BLOCKED]
                          │  [ALL CRITICAL PASS → ADVANCE]
                          ▼
  ┌────────────────────────────────────────────────────────────────────────────────┐
  │ S15: internal_review                       Agent: team_orchestrator            │
  │     "Multi-Perspective Internal Peer Review — 5 Reviewer Personas"              │
  │     Skill: academic-paper-reviewer, humanizer                                  │
  │     ⏱ 60min  │  🔴 CP-8 HUMAN CHECKPOINT                                      │
  │              │  Produces: internal_review_report.md, revision_roadmap.yaml     │
  └────────────────────────────────────────────────────────────────────────────────┘
                          │
                          ▼  [REVIEW REJECTED? → retry S15 or abort]
                             [APPROVED WITH CHANGES? → advance to S16]


PHASE 5: REVISION (Stages 16–17)
═══════════════════════════════════════════════════════════════════════════════════════

  ┌────────────────────────────────────────────────────────────────────────────────┐
  │ S16: apply_revision                        Agent: report_writer                │
  │     "Apply Targeted Revisions Based on Review Feedback"                         │
  │     Skill: scientific-writing, nature-writing, nature-polishing,               │
  │            humanizer, nature-response                                          │
  │     ⏱ 60min  │  🔴 CP-9 HUMAN CHECKPOINT                                      │
  │              │  Max retries: 3                                                 │
  │              │  Produces: revised_manuscript.md, revision_tracker.yaml         │
  └───────────────────────┬────────────────────────────────────────────────────────┘
                          │  [DOWNSTREAM STAGES MARKED STALE]
                          ▼
  ┌────────────────────────────────────────────────────────────────────────────────┐
  │ S17: re_review                            Agent: team_orchestrator             │
  │     "Re-Review Revised Manuscript — Verify All Issues Addressed"                │
  │     Skill: academic-paper-reviewer, nature-citation                            │
  │     ⏱ 40min  │  🔴 CP-10 HUMAN CHECKPOINT                                     │
  │              │  Verdict: READY | MINOR REMAINING | NOT READY                   │
  │              │  NOT READY → loop back to S16 (max 5 revision cycles)           │
  │              │  Produces: re_review_report.md, final_quality_gates.yaml        │
  └────────────────────────────────────────────────────────────────────────────────┘
                          │
                          ▼  [READY → advance to finalize]


PHASE 6: FINALIZE (Stage 18)
═══════════════════════════════════════════════════════════════════════════════════════

  ┌────────────────────────────────────────────────────────────────────────────────┐
  │ S18: finalize                              Agent: integrity_checker            │
  │     "Final Quality Check & Submission Package Assembly"                         │
  │     Skill: nature-polishing, nature-data, nature-citation, nature-figure       │
  │     Full 16-gate re-run. Provenance report with SHA-256 chain.                 │
  │     ⏱ 30min  │  🔴 CP-FINAL HUMAN CHECKPOINT  │  Max retries: 1               │
  │              │  ⚡ section_length_minimum   [MEDIUM]                            │
  │              │  ⚡ no_bullets_in_prose      [MEDIUM]                            │
  │              │  Produces: final_manuscript.md, final_manuscript.pdf,            │
  │              │            submission_package.yaml, reproducibility_bundle.zip  │
  │              │  On pass → pipeline_complete                                    │
  └────────────────────────────────────────────────────────────────────────────────┘
                          │
                          ▼
                    ╔══════════════╗
                    ║  PIPELINE    ║
                    ║  COMPLETE    ║
                    ║  ✓ 18/18     ║
                    ╚══════════════╝


LEGEND:
  🔴 CP-N  = Human Checkpoint (7 total: S1, S4, S6, S9, S11, S13, S15, S16, S17, S18)
  ⚡       = Integrity Gate active at this stage (see Section 4 for full map)
  ──►     = Dependency arrow (upstream must complete before downstream starts)
  ══      = Phase boundary
```

### 1.2 Dependency Graph (Compact)

```
                           PHASE 1                PHASE 2                 PHASE 3
                    ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐
                    │ S1              │  │ S5               │  │ S9               │
                    │ select_topic    │  │ data_audit       │  │ write_methods    │
                    └────────┬────────┘  └────────┬─────────┘  └────────┬─────────┘
                    ┌────────┴────────┐           │                    │
                    │                 │           ▼                    ▼
               ┌────┴────┐      ┌────┴────┐  ┌──────────┐     ┌──────────────┐
               │ S2      │      │ S3      │  │ S6       │     │ S10          │
               │ target_ │      │literature│  │ figure_  │     │ write_results│
               │ journal │      │_search  │  │ planning │     └──────┬───────┘
               └────┬────┘      └────┬────┘  └────┬─────┘            │
                    │                │            │                   │
                    └────────┬───────┘            │    ┌──────────────┴───────┐
                             ▼                    │    │ S11                  │
                        ┌──────────┐              │    │ write_introduction   │
                        │ S4       │              │    └──────────┬───────────┘
                        │ formulate│              │               │
                        │hypotheses│              │               │
                        └────┬─────┘              │               │
                             │                    │               │
                             ▼                    ▼               │
                        ┌──────────┐         ┌──────────┐        │
                        │ ENTER    │────────▶│ S7       │        │
                        │ PHASE 2  │         │ run_     │        │
                        └──────────┘         │ analysis │        │
                                             └────┬─────┘        │
                                                  │               │
                    PHASE 4                        ▼               │
               ┌──────────────────┐          ┌──────────┐        │
               │ S13              │◀─────────│ S8       │        │
               │ assemble_        │          │ verify_  │        │
               │ manuscript       │          │ methods  │        │
               └────────┬─────────┘          └──────────┘        │
                        │                                         │
                        ▼              PHASE 3 ENTRY              │
               ┌──────────────────┐  ┌──────────────────┐        │
               │ S14              │  │ S12              │◀───────┘
               │ integrity_check  │  │ write_discussion │
               └────────┬─────────┘  └────────┬─────────┘
                        │                     │
                        ▼                     │
               ┌──────────────────┐           │
               │ S15              │           │
               │ internal_review  │           │
               └────────┬─────────┘           │
                        │                     │
                    PHASE 5                   │
               ┌──────────────────┐           │
               │ S16              │           │
               │ apply_revision   │           │
               └────────┬─────────┘           │
                        │                     │
                        ▼                     │
               ┌──────────────────┐           │
               │ S17              │           │
               │ re_review        │───────────┘
               └────────┬─────────┘  (loop max 5×)
                        │
                    PHASE 6
               ┌──────────────────┐
               │ S18              │
               │ finalize         │
               └──────────────────┘
```

### 1.3 Pipeline State Machine

```
                                    ┌──────────┐
                                    │  CLEAN   │ ◄── All 18 stages completed
                                    └────┬─────┘
                                         │
                                         │ observe() → decide_next_stage()
                                         ▼
                                    ┌─────────────┐
                              ┌─────│ IN_PROGRESS │─────┐
                              │     └──────┬──────┘     │
                              │            │            │
                              ▼            ▼            ▼
                         ┌─────────┐ ┌──────────┐ ┌──────────┐
                         │  GATE   │ │  STALE   │ │ BLOCKED  │
                         │ FAILURE │ │  STAGES  │ │(terminal)│
                         └────┬────┘ └────┬─────┘ └──────────┘
                              │           │
                              ▼           ▼
                         diagnose()   sync_stale()
                              │           │
                              ▼           ▼
                         revision    re-run stale
                         plan        stages
                              │           │
                              └─────┬─────┘
                                    │
                                    ▼
                              ┌──────────┐
                              │  CLEAN   │ (resolved)
                              └──────────┘

  DRIFT_DETECTED ──► detect_artifact_drift() ──► STALE_STAGES ──► re-run
```

### 1.4 Stage-to-Phase Quick Reference

```
  PHASE 1  │ S1 select_topic ── S2 target_journal ──► S4 formulate_hypotheses
           │                   S3 literature_search ──┘

  PHASE 2  │ S5 data_audit ── S6 figure_planning ── S7 run_analysis ── S8 verify_methods

  PHASE 3  │ S9 write_methods ── S10 write_results ──► S12 write_discussion
           │                     S11 write_introduction ──┘

  PHASE 4  │ S13 assemble_manuscript ── S14 integrity_check ── S15 internal_review

  PHASE 5  │ S16 apply_revision ── S17 re_review ──► loop back to S16 (max 5×)

  PHASE 6  │ S18 finalize
```

---

## 2. Agent Dispatch Matrix

### 2.1 Complete Agent-to-Stage Mapping

```
┌────────────────────────┬──────────┬──────────────────────────────────────────┬──────────────┬──────────────────────────────────────┐
│ AGENT                  │ STAGES   │ STAGE NAMES                              │ # STAGES     │ PRIMARY SKILLS                       │
│ (12 total)             │ ASSIGNED │                                          │ OWNED        │                                      │
├────────────────────────┼──────────┼──────────────────────────────────────────┼──────────────┼──────────────────────────────────────┤
│ research_strategist    │ S1, S2,  │ select_topic, target_journal,            │ 3            │ topic_research, deep-research,       │
│                        │ S4       │ formulate_hypotheses                     │              │ nature-academic-search               │
├────────────────────────┼──────────┼──────────────────────────────────────────┼──────────────┼──────────────────────────────────────┤
│ literature_reviewer    │ S3       │ literature_search                        │ 1            │ deep-research, nature-academic-      │
│                        │          │                                          │              │ search, nature-citation              │
├────────────────────────┼──────────┼──────────────────────────────────────────┼──────────────┼──────────────────────────────────────┤
│ data_auditor           │ S5       │ data_audit                               │ 1            │ nature-data, qc_pipeline             │
├────────────────────────┼──────────┼──────────────────────────────────────────┼──────────────┼──────────────────────────────────────┤
│ figure_planner         │ S6       │ figure_planning                          │ 1            │ figure_planning, nature-figure       │
├────────────────────────┼──────────┼──────────────────────────────────────────┼──────────────┼──────────────────────────────────────┤
│ analysis_executor      │ S7       │ run_analysis                             │ 1            │ spatial_analysis, statistical_testing│
│                        │          │                                          │              │ pathway_inference, qc_pipeline       │
├────────────────────────┼──────────┼──────────────────────────────────────────┼──────────────┼──────────────────────────────────────┤
│ pipeline_engineer      │ S7, S8   │ run_analysis, verify_methods             │ 2            │ qc_pipeline, spatial_analysis        │
├────────────────────────┼──────────┼──────────────────────────────────────────┼──────────────┼──────────────────────────────────────┤
│ statistician           │ S8       │ verify_methods (async audit)             │ 1            │ statistical_testing                  │
│ (cross-cutting)        │          │                                          │              │                                      │
├────────────────────────┼──────────┼──────────────────────────────────────────┼──────────────┼──────────────────────────────────────┤
│ report_writer          │ S9, S10, │ write_methods, write_results,            │ 6            │ scientific-writing, nature-writing,  │
│                        │ S11, S12,│ write_introduction, write_discussion,    │              │ nature-polishing, humanizer,         │
│                        │ S13, S16 │ assemble_manuscript, apply_revision      │              │ nature-citation, nature-response     │
├────────────────────────┼──────────┼──────────────────────────────────────────┼──────────────┼──────────────────────────────────────┤
│ integrity_checker      │ S8, S14, │ verify_methods, integrity_check,         │ 5            │ qc_pipeline, academic-paper-reviewer,│
│                        │ S15, S17,│ internal_review, re_review,              │              │ nature-data, nature-citation         │
│                        │ S18      │ finalize                                 │              │                                      │
├────────────────────────┼──────────┼──────────────────────────────────────────┼──────────────┼──────────────────────────────────────┤
│ team_orchestrator      │ S15, S17,│ internal_review, re_review,              │ 3            │ deep-research                        │
│ (coordinator)          │ S18      │ finalize                                 │              │                                      │
├────────────────────────┼──────────┼──────────────────────────────────────────┼──────────────┼──────────────────────────────────────┤
│ code_librarian         │ S7, S8,  │ run_analysis, verify_methods,            │ 3            │ qc_pipeline                          │
│                        │ S18      │ finalize                                 │              │                                      │
├────────────────────────┼──────────┼──────────────────────────────────────────┼──────────────┼──────────────────────────────────────┤
│ multi_omics_integrator │ S7, S8   │ run_analysis, verify_methods             │ 2            │ multi_omics, spatial_analysis,       │
│                        │          │                                          │              │ pathway_inference                    │
└────────────────────────┴──────────┴──────────────────────────────────────────┴──────────────┴──────────────────────────────────────┘
```

### 2.2 Agent Phase Coverage Matrix

```
┌────────────────────────┬──────────┬──────────┬──────────┬──────────┬──────────┬──────────┐
│ AGENT                  │ PHASE 1  │ PHASE 2  │ PHASE 3  │ PHASE 4  │ PHASE 5  │ PHASE 6  │
│                        │ Research │ Data &   │ Writing  │ Assembly │ Revision │ Finalize │
│                        │&Planning │ Methods  │          │ & Review │          │          │
├────────────────────────┼──────────┼──────────┼──────────┼──────────┼──────────┼──────────┤
│ research_strategist    │    ███   │          │          │          │          │          │
│ literature_reviewer    │    █     │          │          │          │          │          │
│ data_auditor           │          │    █     │          │          │          │          │
│ figure_planner         │          │    █     │          │          │          │          │
│ analysis_executor      │          │    ███   │          │          │          │          │
│ pipeline_engineer      │          │    ██    │          │          │          │          │
│ statistician           │          │    █     │          │          │          │          │
│ report_writer          │          │          │   ████   │    █     │    █     │          │
│ integrity_checker      │          │    █     │          │   ███    │    █ █   │    █     │
│ team_orchestrator      │          │          │          │    █     │    █     │    █     │
│ code_librarian         │          │    ██    │          │          │          │    █     │
│ multi_omics_integrator │          │    ██    │          │          │          │          │
├────────────────────────┼──────────┼──────────┼──────────┼──────────┼──────────┼──────────┤
│ ACTIVE AGENTS / PHASE  │    2     │    9     │    1     │    3     │    3     │    3     │
└────────────────────────┴──────────┴──────────┴──────────┴──────────┴──────────┴──────────┘

█ = Primary stage ownership    █ = Shared/cross-cutting stage
```

### 2.3 Agent Responsibility Boundaries (I Do / I Don't Do)

```
┌────────────────────────┬──────────────────────────────────────┬──────────────────────────────────────────┐
│ AGENT                  │ I DO                                 │ I DON'T DO                               │
├────────────────────────┼──────────────────────────────────────┼──────────────────────────────────────────┤
│ research_strategist    │ Define questions, assess             │ Run code, search literature              │
│                        │ feasibility, target journals,        │ (delegates to literature_reviewer)       │
│                        │ generate hypotheses                  │                                          │
├────────────────────────┼──────────────────────────────────────┼──────────────────────────────────────────┤
│ literature_reviewer    │ Search databases (PubMed,            │ Run analysis code, write                 │
│                        │ Consensus), build bibliographies,    │ manuscript sections                      │
│                        │ synthesize evidence                  │                                          │
├────────────────────────┼──────────────────────────────────────┼──────────────────────────────────────────┤
│ data_auditor           │ Read/assess data quality,            │ Modify data, write manuscript            │
│                        │ validate metadata, detect batch      │ text                                     │
│                        │ effects                              │                                          │
├────────────────────────┼──────────────────────────────────────┼──────────────────────────────────────────┤
│ figure_planner         │ Design figure architecture,          │ Run analysis, generate figures           │
│                        │ choose palettes, specify panels      │ (delegates to analysis_executor)         │
├────────────────────────┼──────────────────────────────────────┼──────────────────────────────────────────┤
│ analysis_executor      │ Run R/Python pipelines,              │ Design figures (delegates to             │
│                        │ generate results and figures,        │ figure_planner), write prose             │
│                        │ log sessions                         │                                          │
├────────────────────────┼──────────────────────────────────────┼──────────────────────────────────────────┤
│ pipeline_engineer      │ Build Docker/conda environments,     │ Run primary analysis                     │
│                        │ verify reproducibility               │ (delegates to analysis_executor)         │
├────────────────────────┼──────────────────────────────────────┼──────────────────────────────────────────┤
│ statistician           │ Review study design, audit           │ Modify data, write manuscript            │
│                        │ test selection, validate             │ text (advisory only)                     │
│                        │ statistical reporting                │                                          │
├────────────────────────┼──────────────────────────────────────┼──────────────────────────────────────────┤
│ report_writer          │ Write IMRAD sections,                │ Run analysis, search literature,         │
│                        │ assemble manuscripts,                │ check integrity (delegates)              │
│                        │ format for journals                  │                                          │
├────────────────────────┼──────────────────────────────────────┼──────────────────────────────────────────┤
│ integrity_checker      │ Run 16 gates, cross-reference        │ Modify manuscript, add citations,        │
│                        │ citations, verify claim-artifact     │ generate figures                         │
│                        │ binding                              │                                          │
├────────────────────────┼──────────────────────────────────────┼──────────────────────────────────────────┤
│ team_orchestrator      │ Task decomposition, agent            │ Execute domain tasks                     │
│                        │ dispatch, parallel scheduling,       │ (purely coordination)                    │
│                        │ deadlock detection                   │                                          │
├────────────────────────┼──────────────────────────────────────┼──────────────────────────────────────────┤
│ code_librarian         │ Manage code library, track           │ Run primary analysis                     │
│                        │ scripts, plugin registration         │                                          │
├────────────────────────┼──────────────────────────────────────┼──────────────────────────────────────────┤
│ multi_omics_integrator │ Integrate cross-omics data           │ Design study, write full                 │
│                        │ (MOFA, DIABLO), factor analysis      │ manuscripts                              │
└────────────────────────┴──────────────────────────────────────┴──────────────────────────────────────────┘
```

---

## 3. Skill-to-Agent-to-Stage Routing

### 3.1 Trigger Word Routing Flow

```
                          USER INPUT (Natural Language)
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                         SKILLS DISPATCHER (Keyword Match)                             │
│                                                                                     │
│  Routing Strategy: best_match_with_fallback                                          │
│  Fallback Agent: team_orchestrator                                                   │
│  Min Confidence: 0.6                                                                 │
│                                                                                     │
│  ┌───────────────────────────────────────────────────────────────────────────────┐  │
│  │ TRIGGER KEYWORD SET                     → SKILL            → PHASE             │  │
│  ├───────────────────────────────────────────────────────────────────────────────┤  │
│  │ "literature search", "deep调研",        → deep-research    → research          │  │
│  │ "系统性检索", "文献综述"                                                       │  │
│  │                                                                               │  │
│  │ "search PubMed", "MeSH search",         → nature-academic- → research          │  │
│  │ ".nbib", ".ris", "文献检索"               search                               │  │
│  │                                                                               │  │
│  │ "add citations", "Nature系列引用",       → nature-citation  → writing           │  │
│  │ "分段引用", "补引用", "配文献"                                                │  │
│  │                                                                               │  │
│  │ "write Methods", "write Results",       → scientific-      → writing           │  │
│  │ "IMRAD", "scientific manuscript",         writing                               │  │
│  │ "CONSORT", "STROBE", "写论文段落"                                              │  │
│  │                                                                               │  │
│  │ "write abstract", "Nature-style",       → nature-writing   → writing           │  │
│  │ "从零写论文", "搭论文框架",                                                   │  │
│  │ "起草论文", "CNS风格"                                                          │  │
│  │                                                                               │  │
│  │ "polish manuscript", "improve           → nature-polishing → writing           │  │
│  │ language", "润色", "改写",                                                    │  │
│  │ "proofreading", "排版"                                                         │  │
│  │                                                                               │  │
│  │ "remove AI traces", "去AI味",           → humanizer        → polish            │  │
│  │ "不像AI写的", "更自然"                                                        │  │
│  │                                                                               │  │
│  │ "create figure", "journal-ready         → nature-figure    → visualization     │  │
│  │ figure", "论文配图", "科研绘图",                                              │  │
│  │ "画图", "出图", "export SVG"                                                   │  │
│  │                                                                               │  │
│  │ "data availability", "数据可用性",      → nature-data      → writing           │  │
│  │ "GEO submission", "FAIR data"                                                 │  │
│  │                                                                               │  │
│  │ "reviewer response", "审稿意见",        → nature-response  → revision          │  │
│  │ "逐点回复", "修回信", "rebuttal"                                              │  │
│  │                                                                               │  │
│  │ "review manuscript", "peer review",     → academic-paper-  → review            │  │
│  │ "审稿", "critique paper"                  reviewer                             │  │
│  │                                                                               │  │
│  │ "research topic", "课题调研",           → topic_research   → research          │  │
│  │ "选题", "创新性评估"                                                          │  │
│  │                                                                               │  │
│  │ "quality control", "质量控制",          → qc_pipeline      → verification      │  │
│  │ "integrity check", "pipeline validation"                                       │  │
│  │                                                                               │  │
│  │ "spatial transcriptomics",              → spatial_analysis → analysis          │  │
│  │ "空间转录组", "空间解卷积"                                                   │  │
│  │                                                                               │  │
│  │ "statistical test", "p-value",          → statistical_     → analysis          │  │
│  │ "effect size", "统计检验"                 testing                              │  │
│  │                                                                               │  │
│  │ "pathway analysis", "GO enrichment",    → pathway_         → analysis          │  │
│  │ "GSEA", "通路富集", "KEGG"               inference                             │  │
│  │                                                                               │  │
│  │ "figure plan", "visual storytelling",   → figure_planning  → strategy          │  │
│  │ "图表规划", "figure layout"                                                  │  │
│  └───────────────────────────────────────────────────────────────────────────────┘  │
└───────────────────────────────────┬─────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                          AGENT ROUTER (Skill → Agent)                                │
│                                                                                     │
│  Routing Strategy: best_match_with_fallback                                          │
│                                                                                     │
│  ┌───────────────────────────────────────────────────────────────────────────────┐  │
│  │ SKILL DISPATCHED            → PRIMARY AGENT         → SECONDARY / FALLBACK     │  │
│  ├───────────────────────────────────────────────────────────────────────────────┤  │
│  │ deep-research               → literature_reviewer   → research_strategist      │  │
│  │ nature-academic-search      → literature_reviewer   → research_strategist      │  │
│  │ nature-citation             → report_writer         → literature_reviewer      │  │
│  │ scientific-writing          → report_writer         → (none)                   │  │
│  │ nature-writing              → report_writer         → (none)                   │  │
│  │ nature-polishing            → report_writer         → (none)                   │  │
│  │ humanizer                   → report_writer         → (none)                   │  │
│  │ nature-figure               → figure_planner        → analysis_executor        │  │
│  │ nature-data                 → data_auditor          → report_writer            │  │
│  │ nature-response             → report_writer         → integrity_checker        │  │
│  │ academic-paper-reviewer     → integrity_checker     → team_orchestrator        │  │
│  │ topic_research              → research_strategist   → (none)                   │  │
│  │ qc_pipeline                 → integrity_checker     → data_auditor             │  │
│  │ spatial_analysis            → analysis_executor     → pipeline_engineer        │  │
│  │ statistical_testing         → statistician          → analysis_executor        │  │
│  │ pathway_inference           → analysis_executor     → (none)                   │  │
│  │ figure_planning             → figure_planner        → (none)                   │  │
│  └───────────────────────────────────────────────────────────────────────────────┘  │
└───────────────────────────────────┬─────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                          STAGE EXECUTION (Agent → Pipeline Stage)                    │
│                                                                                     │
│  ┌───────────────────────────────────────────────────────────────────────────────┐  │
│  │ AGENT DISPATCHED            → EXECUTES STAGE(S)                                 │  │
│  ├───────────────────────────────────────────────────────────────────────────────┤  │
│  │ research_strategist         → S1 select_topic                                  │  │
│  │                             → S2 target_journal                                │  │
│  │                             → S4 formulate_hypotheses                          │  │
│  │                                                                               │  │
│  │ literature_reviewer         → S3 literature_search                             │  │
│  │                                                                               │  │
│  │ data_auditor                → S5 data_audit                                    │  │
│  │                                                                               │  │
│  │ figure_planner              → S6 figure_planning                               │  │
│  │                                                                               │  │
│  │ analysis_executor           → S7 run_analysis                                  │  │
│  │ (+ statistician async)                                                        │  │
│  │                                                                               │  │
│  │ pipeline_engineer           → S8 verify_methods                                │  │
│  │                                                                               │  │
│  │ report_writer               → S9  write_methods                               │  │
│  │                             → S10 write_results                                │  │
│  │                             → S11 write_introduction                           │  │
│  │                             → S12 write_discussion                             │  │
│  │                             → S13 assemble_manuscript                          │  │
│  │                             → S16 apply_revision                               │  │
│  │                                                                               │  │
│  │ integrity_checker           → S14 integrity_check                              │  │
│  │ (+ team_orchestrator)       → S15 internal_review                              │  │
│  │                             → S17 re_review                                    │  │
│  │                             → S18 finalize                                     │  │
│  └───────────────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

### 3.2 End-to-End Routing Example

```
USER SAYS: "润色我的讨论部分，然后检查引用是否完整"

  1. KEYWORD MATCH (SkillsDispatcher):
     "润色"           → nature-polishing  (weight: high, phase: writing)
     "讨论部分"       → scientific-writing (weight: medium, phase: writing)
     "检查引用"       → nature-citation   (weight: high, phase: writing)

  2. SKILL CHAIN RESOLUTION:
     Primary:  nature-polishing
     Chained:  nature-citation (triggered by "引用")

  3. AGENT RESOLUTION (AgentRouter):
     nature-polishing → agent: report_writer
     nature-citation  → agent: report_writer  (same agent, sequential execution)

  4. STAGE RESOLUTION:
     "讨论部分" context narrows to S12 (write_discussion)
     nature-citation triggers integrity check against S14 gate rules

  5. EXECUTION:
     report_writer receives dispatch: {stage: "write_discussion", skills: [nature-polishing, nature-citation]}
     → polishes discussion_section.md
     → validates all \cite{} keys against references.bib
     → reports gate C1 (bibtex_citation_existence) status
```

### 3.3 Skill Phase Distribution

```
  PHASE          SKILLS ACTIVE
  ─────          ─────────────
  research       deep-research, nature-academic-search, topic_research
  strategy       figure_planning
  analysis       spatial_analysis, statistical_testing, pathway_inference
  verification   qc_pipeline
  visualization  nature-figure
  writing        scientific-writing, nature-writing, nature-polishing,
                 nature-citation, nature-data
  polish         humanizer
  revision       nature-response
  review         academic-paper-reviewer
```

---

## 4. Integrity Gate Activation Map

### 4.1 Gate Severity Hierarchy

```
  ┌─────────────────────────────────────────────────────────────────┐
  │                    INTEGRITY GATE SEVERITY PYRAMID               │
  │                                                                 │
  │                        ┌─────────┐                              │
  │                        │    5    │  CRITICAL                     │
  │                        │ CRITICAL│  Pipeline BLOCKED on failure. │
  │                        │  GATES  │  Must fix before proceeding.  │
  │                        └────┬────┘                              │
  │                             │                                   │
  │                        ┌────┴────┐                              │
  │                        │    8    │  HIGH                         │
  │                        │  HIGH   │  Must resolve or document.    │
  │                        │  GATES  │  Blocks submission.          │
  │                        └────┬────┘                              │
  │                             │                                   │
  │                        ┌────┴────┐                              │
  │                        │    3    │  MEDIUM                       │
  │                        │ MEDIUM  │  Advisory. Informational      │
  │                        │  GATES  │  only. Does not block.        │
  │                        └─────────┘                              │
  │                                                                 │
  │  TOTAL: 16 GATES across 3 severity levels                       │
  └─────────────────────────────────────────────────────────────────┘
```

### 4.2 Gate-to-Stage Activation Matrix

```
┌──────┬──────────────────────────────────────┬──────────┬──────────┬───────────────────────────────────────────┬──────────┐
│ GATE │ GATE NAME                            │ SEVERITY │ BLOCKING │ ACTIVATES AT STAGES                       │ AUTO-FIX │
│  #   │                                      │          │          │                                           │          │
├──────┼──────────────────────────────────────┼──────────┼──────────┼───────────────────────────────────────────┼──────────┤
│ C1   │ bibtex_citation_existence            │ CRITICAL │    YES   │ S11, S12, S14, S18                        │    NO    │
│ C2   │ citation_evidence_traceability       │ CRITICAL │    YES   │ S14, S18                                  │    NO    │
│ C3   │ results_no_citations                 │ CRITICAL │    YES   │ S10, S14, S18                             │    NO    │
│ C4   │ claim_artifact_binding               │ CRITICAL │    YES   │ S14, S18                                  │    NO    │
│ C5   │ figures_referenced                   │ CRITICAL │    YES   │ S10, S13, S14, S18                        │    NO    │
├──────┼──────────────────────────────────────┼──────────┼──────────┼───────────────────────────────────────────┼──────────┤
│ H1   │ data_availability_statement          │ HIGH     │    YES   │ S5, S9, S14, S18                          │   YES    │
│ H2   │ code_availability_statement          │ HIGH     │    YES   │ S9, S14, S18                              │   YES    │
│ H3   │ no_local_paths                       │ HIGH     │    YES   │ S9, S10, S11, S12, S13, S14, S18          │   YES    │
│ H4   │ methods_parameters_complete          │ HIGH     │    YES   │ S9, S14, S18                              │    NO    │
│ H5   │ discussion_limitations               │ HIGH     │    YES   │ S12, S14, S18                             │    NO    │
│ H6   │ results_no_overinterpretation        │ HIGH     │    YES   │ S10, S14, S18                             │    NO    │
│ H7   │ statistics_reported                  │ HIGH     │    YES   │ S10, S14, S18                             │    NO    │
│ H8   │ pseudoreplication_check              │ HIGH     │    YES   │ S8, S14, S18                              │    NO    │
├──────┼──────────────────────────────────────┼──────────┼──────────┼───────────────────────────────────────────┼──────────┤
│ M1   │ section_length_minimum               │ MEDIUM   │    NO    │ S9, S10, S11, S12, S14, S18               │    NO    │
│ M2   │ no_bullets_in_prose                  │ MEDIUM   │    NO    │ S9, S10, S11, S12, S13, S14, S18          │   YES    │
│ M3   │ figure_count_requirements            │ MEDIUM   │    NO    │ S6, S13, S14, S18                         │    NO    │
└──────┴──────────────────────────────────────┴──────────┴──────────┴───────────────────────────────────────────┴──────────┘
```

### 4.3 Gate Execution Order (Optimized for Fastest Failure Detection)

```
  EXECUTION ORDER (at S14 integrity_check):
  ═══════════════════════════════════════════

   ┌─ FAST PATTERN MATCH ─────────────────────────────────────┐
   │  1. C3: results_no_citations       — regex scan Results  │
   │  2. M2: no_bullets_in_prose        — bullet pattern scan │
   │  3. M1: section_length_minimum     — word count check    │
   │  4. H3: no_local_paths             — path pattern scan   │
   └──────────────────────────────────────────────────────────┘
                              │
   ┌─ CROSS-REFERENCE ────────────────────────────────────────┐
   │  5. C1: bibtex_citation_existence   — BibTeX vs \cite{} │
   │  6. C5: figures_referenced          — figures/ vs \ref{} │
   │  7. C2: citation_evidence_traceability — DOI/PMID check  │
   └──────────────────────────────────────────────────────────┘
                              │
   ┌─ CONTENT PRESENCE ───────────────────────────────────────┐
   │  8. H1: data_availability_statement — section search     │
   │  9. H2: code_availability_statement — section search     │
   │ 10. H4: methods_parameters_complete  — fields audit       │
   │ 11. H5: discussion_limitations       — paragraph search   │
   └──────────────────────────────────────────────────────────┘
                              │
   ┌─ SEMANTIC ANALYSIS ──────────────────────────────────────┐
   │ 12. C4: claim_artifact_binding       — numeric trace     │
   │ 13. H6: results_no_overinterpretation — causal language  │
   │ 14. H7: statistics_reported          — stat pattern match│
   │ 15. H8: pseudoreplication_check      — design audit      │
   └──────────────────────────────────────────────────────────┘
                              │
   ┌─ JOURNAL COMPLIANCE ─────────────────────────────────────┐
   │ 16. M3: figure_count_requirements    — count vs limit    │
   └──────────────────────────────────────────────────────────┘
```

### 4.4 Post-Failure Resolution Workflow

```
  S14 integrity_check FAILS CRITICAL gate
            │
            ▼
  ┌─────────────────────────────────────────────────────────────┐
  │  PIPELINE STATE → GATE_FAILURE                              │
  │  Pipeline BLOCKED. Cannot advance to S15.                   │
  └──────────────────────────┬──────────────────────────────────┘
                             │
                             ▼
  ┌─────────────────────────────────────────────────────────────┐
  │  integrity_checker emits:                                   │
  │    • integrity_report.json  (machine-readable)              │
  │    • integrity_report.md    (human-readable)                │
  │    • quality_gate_results.yaml                              │
  └──────────────────────────┬──────────────────────────────────┘
                             │
                             ▼
  ┌─────────────────────────────────────────────────────────────┐
  │  team_orchestrator routes failures to responsible agents:    │
  │                                                             │
  │  bibtex failures (C1)      → literature_reviewer            │
  │  citation trace (C2)       → literature_reviewer            │
  │  results citations (C3)    → report_writer                  │
  │  claim binding (C4)        → report_writer                  │
  │  figure references (C5)    → figure_planner                 │
  │  data statement (H1)       → data_auditor                   │
  │  code statement (H2)       → pipeline_engineer              │
  │  local paths (H3)          → report_writer                  │
  │  parameters (H4)           → report_writer + pipeline_engineer│
  │  limitations (H5)          → report_writer                  │
  │  overinterpretation (H6)   → report_writer                  │
  │  statistics (H7)           → statistician                   │
  │  pseudoreplication (H8)    → statistician                   │
  │  section length (M1)       → report_writer                  │
  │  bullets (M2)              → report_writer                  │
  │  figure count (M3)         → figure_planner                 │
  └──────────────────────────┬──────────────────────────────────┘
                             │
                             ▼
  ┌─────────────────────────────────────────────────────────────┐
  │  After fixes applied → re-run S14 integrity_check           │
  │  All decisions logged to checkpoint_ledger.jsonl            │
  │  integrity_ledger.jsonl records all gate events             │
  └─────────────────────────────────────────────────────────────┘
```

### 4.5 Gate Coverage by Stage

```
  STAGE   CRITICAL GATES          HIGH GATES                   MEDIUM GATES
  ─────   ──────────────          ──────────                   ────────────
  S5                              H1
  S6                                                           M3
  S8                              H8
  S9                              H1, H2, H3, H4               M1, M2
  S10     C3, C5                  H3, H6, H7                   M1, M2
  S11     C1                      H3                           M1, M2
  S12     C1                      H3, H5                       M1, M2
  S13     C5                      H3                           M2, M3
  S14     C1, C2, C3, C4, C5     H1, H2, H3, H4, H5, H6, H7, H8  M1, M2, M3
  S18     C1, C2, C3, C4, C5     H1, H2, H3, H4, H5, H6, H7, H8  M1, M2, M3
```

---

## 5. Data Flow Architecture

### 5.1 Four-Layer Architecture with Data Flow

```
┌──────────────────────────────────────────────────────────────────────────────────────────┐
│                                      USER INPUT                                           │
│                              (idea, field, journal name)                                  │
└───────────────────────────────────────┬──────────────────────────────────────────────────┘
                                        │
                                        ▼
┌──────────────────────────────────────────────────────────────────────────────────────────┐
│  LAYER 1: STRATEGY (src/paper_workflow/strategy/)                                         │
│                                                                                          │
│  ┌──────────────┐    ┌──────────────────┐    ┌──────────────────┐    ┌────────────────┐  │
│  │TopicSelector │───▶│ JournalTargeter  │───▶│FeasibilityAssessor│───▶│Hypothesis      │  │
│  │Idea→Research │    │Name→JournalTarget│    │4-dim assessment  │    │Framework        │  │
│  │Topic         │    │(25 journals)     │    │→Go/No-Go         │    │→ H1-H4         │  │
│  └──────────────┘    └──────────────────┘    └──────────────────┘    └────────────────┘  │
│                                                                                          │
│  OUTPUT: ResearchStrategy dataclass (topic + journal + feasibility + H1-H4)              │
└───────────────────────────────────────┬──────────────────────────────────────────────────┘
                                        │
                                        ▼  ResearchStrategy
┌──────────────────────────────────────────────────────────────────────────────────────────┐
│  LAYER 2: DECISION (src/paper_workflow/engine/)                                           │
│                                                                                          │
│  ┌───────────────────────────────────────────────────────────────────────────────────┐   │
│  │                          PaperLoopEngine                                           │   │
│  │                                                                                   │   │
│  │   ① OBSERVE ──► ② DECIDE ──► ③ RUN ──► ④ VERIFY ──► ⑤ RECORD ──► ⑥ MARK_STALE   │   │
│  │       ▲                                                              │            │   │
│  │       │                                                              ▼            │   │
│  │       └──────────────────────── ⑦ DIAGNOSE ◄─────────────────────────┘            │   │
│  │                                                                                   │   │
│  │   State Machine: CLEAN ⇄ IN_PROGRESS ⇄ GATE_FAILURE ⇄ STALE_STAGES ⇄ BLOCKED     │   │
│  └───────────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                          │
│  OUTPUT: Stage dispatch decision {agent, skill, parameters, stage_name}                  │
└───────────────────────────────────────┬──────────────────────────────────────────────────┘
                                        │
                                        ▼  Dispatch Instruction
┌──────────────────────────────────────────────────────────────────────────────────────────┐
│  LAYER 3: EXECUTION (src/paper_workflow/cli/ + .claude/agents/ + .claude/skills/)        │
│                                                                                          │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐     │
│  │  12 AGENTS (Bounded Contracts)             28 SKILLS (Workflow Templates)        │     │
│  │                                                                                  │     │
│  │  research_strategist   ─┐                   topic_research                       │     │
│  │  literature_reviewer   ─┤                   literature_search                    │     │
│  │  data_auditor          ─┤                   paper_loop                           │     │
│  │  figure_planner        ─┤                   figure_planning                      │     │
│  │  analysis_executor     ─┤                   paper_writing                        │     │
│  │  pipeline_engineer     ─┼─── DISPATCH ───▶  revision_routing                     │     │
│  │  statistician          ─┤                   qc_pipeline                          │     │
│  │  report_writer         ─┤                   spatial_analysis                     │     │
│  │  integrity_checker     ─┤                   pathway_inference                    │     │
│  │  team_orchestrator     ─┤                   statistical_testing                  │     │
│  │  code_librarian        ─┤                   multi_omics                          │     │
│  │  multi_omics_integrator─┘                   reproducibility                      │     │
│  └──────────────────────────────────────────────────────────────────────────────────┘     │
│                                                                                          │
│  OUTPUT: Physical artifacts on disk in papers/{paper_id}/                                 │
│    • manuscript/*.md, *.tex, *.pdf       • figures/*.svg, *.tiff, *.pdf                   │
│    • results/*.csv, *.yaml               • references/*.bib, citation_evidence.csv        │
│    • data/*.yaml                          • integrity/*.json, *.md                        │
│    • review/*.md, *.yaml                  • submission/*.pdf, *.zip                       │
└───────────────────────────────────────┬──────────────────────────────────────────────────┘
                                        │
                                        ▼  Artifacts + Events
┌──────────────────────────────────────────────────────────────────────────────────────────┐
│  LAYER 4: SUPERVISION (src/paper_workflow/supervision/)                                   │
│                                                                                          │
│  ┌──────────────────────────────────────────────────────────────────────────────────┐    │
│  │                         PASSPORT SYSTEM (4 Ledger Files)                          │    │
│  │                                                                                  │    │
│  │  papers/{paper_id}/                                                              │    │
│  │  ├── project_passport.yaml      ← Identity + stage states (YAML, readable)        │    │
│  │  ├── artifact_ledger.jsonl      ← Append-only artifact SHA-256 log               │    │
│  │  ├── checkpoint_ledger.jsonl    ← Append-only human decision audit trail         │    │
│  │  └── integrity_ledger.jsonl     ← Append-only gate event history                 │    │
│  │                                                                                  │    │
│  │  ┌─────────────────────────────────────────────────────────────────────────┐     │    │
│  │  │                      INTEGRITY GATE CHECKER                              │     │    │
│  │  │                                                                          │     │    │
│  │  │  16 automated quality rules across 3 severity levels                     │     │    │
│  │  │  run_all_checks(sections, bibtex, figures, journal) → IntegrityReport    │     │    │
│  │  │                                                                          │     │    │
│  │  │  CRITICAL failures → BLOCK pipeline    HIGH failures → WARN              │     │    │
│  │  │                                                                          │     │    │
│  │  └─────────────────────────────────────────────────────────────────────────┘     │    │
│  │                                                                                  │    │
│  │  ┌─────────────────────────────────────────────────────────────────────────┐     │    │
│  │  │  StaleDetection: SHA-256 hash comparison → artifact drift detection      │     │    │
│  │  │  FuseBreaker: Circuit breaker for runaway pipelines                      │     │    │
│  │  │  DecisionRecorder: Immutable checkpoint audit trail                      │     │    │
│  │  └─────────────────────────────────────────────────────────────────────────┘     │    │
│  └──────────────────────────────────────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────────────────────────────────────┘
```

### 5.2 Artifact Lifecycle via Passport

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                         ARTIFACT LIFECYCLE                                            │
│                                                                                     │
│  ┌─────────┐     ┌─────────────┐     ┌──────────────┐     ┌──────────────────────┐ │
│  │ CREATED │────▶│  RECORDED   │────▶│   VERIFIED   │────▶│       ACTIVE         │ │
│  │ (agent  │     │ SHA-256 hash│     │ gate checks  │     │ hash matches current  │ │
│  │ output) │     │ in ledger   │     │ pass         │     │ file on disk          │ │
│  └─────────┘     └─────────────┘     └──────────────┘     └──────────┬───────────┘ │
│                                                                      │             │
│                                               ┌──────────────────────┼───────┐     │
│                                               │                      │       │     │
│                                               ▼                      ▼       ▼     │
│                                         ┌──────────┐          ┌──────────┐ ┌─────┐│
│                                         │ MODIFIED │          │  STALE   │ │DEL- ││
│                                         │ hash     │          │ upstream │ │ETED ││
│                                         │ changed  │          │ changed  │ │file ││
│                                         └────┬─────┘          └────┬─────┘ │miss-││
│                                              │                     │       │ing  ││
│                                              ▼                     ▼       └──┬──┘│
│                                         ┌──────────────────────────────┐      │   │
│                                         │    STALE CASCADE             │      │   │
│                                         │                              │      │   │
│                                         │  Upstream artifact changed:  │      │   │
│                                         │  → marks all downstream      │      │   │
│                                         │    stages as STALE           │      │   │
│                                         │  → pipeline_state =          │      │   │
│                                         │    STALE_STAGES              │      │   │
│                                         │  → triggers re-run from      │      │   │
│                                         │    first stale stage         │      │   │
│                                         └──────────────────────────────┘      │   │
│                                                                                │   │
│  LEDGER FILES (all append-only):                                               │   │
│  ┌──────────────────────────────────────────────────────────────────────────┐  │   │
│  │ artifact_ledger.jsonl    ← Every artifact with SHA-256 hash + status      │  │   │
│  │ checkpoint_ledger.jsonl  ← Every human decision with timestamp           │  │   │
│  │ integrity_ledger.jsonl   ← Every gate execution + every drift event      │  │   │
│  │ project_passport.yaml    ← Canonical pipeline state (single source of     │  │   │
│  │                            truth for "what stage are we at?")             │  │   │
│  └──────────────────────────────────────────────────────────────────────────┘  │   │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

### 5.3 Normal Stage Progression Event Flow

```
  DECISION:     decide_next_stage() → "write_methods"
  EXECUTION:    run_stage("write_methods") → status=RUNNING
  EXECUTION:    agent report_writer produces manuscript/methods.md
  SUPERVISION:  PaperPassport.record_artifact("manuscript/methods.md", "write_methods")
                  → artifact_ledger.jsonl (append SHA-256)
                  → project_passport.yaml (update stage artifacts)
  DECISION:     verify_stage("write_methods")
                  → IntegrityGateChecker runs gate rules
                  → All gates pass
  SUPERVISION:  project_passport.yaml → status=COMPLETED
                  → integrity_ledger.jsonl (gate_run event)
  DECISION:     record_and_sync()
                  → check downstream stages for staleness
                  → pipeline_state = CLEAN (or IN_PROGRESS if more stages)
```

### 5.4 Artifact Drift Cascade Flow

```
  SUPERVISION:  detect_artifact_drift()
                  → "results/de_results.csv" hash mismatch detected
                  → artifact_ledger.jsonl entry status → "modified"
                  → integrity_ledger.jsonl → drift_detected event
  SUPERVISION:  sync_artifact_stale(dependency_map)
                  → verify_methods (S8) marked STALE
                  → write_methods (S9) marked STALE
                  → write_results (S10) marked STALE
                  → write_discussion (S12) marked STALE
                  → assemble_manuscript (S13) marked STALE
                  → integrity_check (S14) marked STALE
                  → ... cascades through all downstream stages
  DECISION:     pipeline_state → STALE_STAGES
  DECISION:     decide_next_stage() → S8 (first stale stage in dependency order)
  EXECUTION:    re-run S8 verify_methods → re-produces artifacts → re-verify
  (cascade continues until all STALE stages are re-executed and re-verified)
```

---

## 6. Extension Architecture

### 6.1 Extension Points Overview

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                           EXTENSION ARCHITECTURE                                      │
│                                                                                     │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  ┌────────────────┐  │
│  │ Research Domain │  │   New Journal   │  │  New Paper Type │  │  New Integrity │  │
│  │ config YAML     │  │ journal db YAML │  │ config YAML     │  │ Gate + checker │  │
│  │ (no code change)│  │ (no code change)│  │ (no code change)│  │ (add method)   │  │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘  └────────────────┘  │
│                                                                                     │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  ┌────────────────┐  │
│  │   New Agent     │  │   New Skill     │  │  Custom Script  │  │  New CLI Cmd   │  │
│  │ config + .md    │  │ .md + config    │  │ auto-discovered │  │ add handler    │  │
│  │ (definition)    │  │ (no code change)│  │ (no code change)│  │ (code change)  │  │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘  └────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

### 6.2 Code Library Plugin Registration Workflow

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                     CODE LIBRARY — PLUGIN REGISTRATION FLOW                           │
│                                                                                     │
│  CONFIG (config/default_config.yaml → code_library):                                 │
│                                                                                     │
│    code_library:                                                                    │
│      auto_discover:                                                                 │
│        enabled: true                                                                │
│        on_startup: true            ← scan on pipeline init                          │
│        on_stage_enter: true        ← scan when entering analysis stages             │
│                                                                                     │
│      scan_paths:                                                                    │
│        - "code_library/patterns/qc/"         ← QC patterns (mt_filter.py)           │
│        - "code_library/patterns/clustering/" ← Clustering (leiden, multi_res)       │
│        - "code_library/modules/"             ← Reusable analysis modules            │
│        - "code_library/solutions/"           ← Domain-specific solutions            │
│        - "code_library/snippets/"            ← I/O snippets (h5ad, yaml, logging)   │
│        - "code_library/r/"                   ← R analysis scripts                   │
│        - "code_library/pipelines/"           ← End-to-end pipeline scripts          │
│                                                                                     │
│  REGISTRATION FLOW:                                                                 │
│                                                                                     │
│  ┌─────────────────┐                                                                │
│  │ 1. Scan paths   │  On startup + on_stage_enter(S7 run_analysis)                  │
│  │    for .py, .R, │                                                                │
│  │    .sh, .ipynb  │                                                                │
│  └────────┬────────┘                                                                │
│           │                                                                         │
│           ▼                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐                │
│  │ 2. Validate each discovered script:                             │                │
│  │    • check_syntax: true       ← parse/compile check             │                │
│  │    • check_imports: true      ← verify dependencies available   │                │
│  │    • dry_run_available: true  ← can we test-run?                │                │
│  └───────────────────────────────┬─────────────────────────────────┘                │
│                                  │                                                  │
│                                  ▼                                                  │
│  ┌─────────────────────────────────────────────────────────────────┐                │
│  │ 3. Register in plugin_registry.yaml:                            │                │
│  │                                                                 │                │
│  │    plugins:                                                     │                │
│  │      mt_filter:                                                 │                │
│  │        path: "code_library/patterns/qc/mt_filter.py"           │                │
│  │        language: "Python"                                       │                │
│  │        runner: "python"                                         │                │
│  │        category: "qc"                                           │                │
│  │        stages: ["data_audit", "run_analysis"]                   │                │
│  │        hash: "sha256:abc123..."                                 │                │
│  └───────────────────────────────┬─────────────────────────────────┘                │
│                                  │                                                  │
│                                  ▼                                                  │
│  ┌─────────────────────────────────────────────────────────────────┐                │
│  │ 4. Make available to agents:                                    │                │
│  │    • analysis_executor can import registered modules            │                │
│  │    • pipeline_engineer can execute registered scripts           │                │
│  │    • code_librarian tracks all registered plugins               │                │
│  │    • Drift detection: hash change → re-validate + notify        │                │
│  └─────────────────────────────────────────────────────────────────┘                │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

### 6.3 Custom Script Auto-Discovery

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                     CUSTOM ANALYSIS SCRIPTS — AUTO-DISCOVERY                          │
│                                                                                     │
│  CONFIG (config/default_config.yaml → extension_points → custom_analysis_scripts):   │
│                                                                                     │
│    custom_analysis_scripts:                                                         │
│      enabled: true                                                                  │
│      scan_patterns:                                                                 │
│        - extension: ".py"                                                           │
│          scan_dirs: ["scripts/custom/", "extensions/python/"]                       │
│          registration: {auto_detect: true, require_manifest: false}                 │
│        - extension: ".R"                                                            │
│          scan_dirs: ["scripts/custom/", "extensions/R/"]                            │
│          registration: {auto_detect: true, require_manifest: false}                 │
│        - extension: ".sh"                                                           │
│          scan_dirs: ["scripts/custom/", "extensions/shell/"]                        │
│          registration: {auto_detect: true, require_manifest: false}                 │
│                                                                                     │
│      validation:                                                                    │
│        check_syntax: true                                                           │
│        check_imports: true                                                          │
│        dry_run_available: true                                                      │
│                                                                                     │
│      execution:                                                                     │
│        sandbox: true                                                                │
│        timeout_seconds: 3600                                                        │
│        resource_limits: {max_memory_mb: 16384, max_cpu_cores: 8}                   │
│                                                                                     │
│  DISCOVERY FLOW:                                                                    │
│                                                                                     │
│    User drops my_custom_analysis.py into scripts/custom/                            │
│                              │                                                      │
│                              ▼                                                      │
│    On next stage transition (or pipeline init):                                     │
│    ┌──────────────────────────────────────────────────────────────────┐             │
│    │ 1. Scanner detects new file: "scripts/custom/my_custom_analysis.py"│            │
│    │ 2. Syntax check: python -c "import ast; ast.parse(...)"            │             │
│    │ 3. Import check: verify all imported modules available             │             │
│    │ 4. Dry run (if available): execute with --dry-run flag            │             │
│    │ 5. Register: add to plugin_registry.yaml with metadata            │             │
│    │ 6. Notify: code_librarian records new plugin                     │             │
│    │ 7. Available: analysis_executor can now invoke the custom script │             │
│    └──────────────────────────────────────────────────────────────────┘             │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

### 6.4 New Agent Registration

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                     NEW AGENT REGISTRATION WORKFLOW                                    │
│                                                                                     │
│  STEP 1: Define in config (config/default_config.yaml → agent_routing → agents):     │
│                                                                                     │
│    new_agent_name:                                                                  │
│      description: "What this agent does"                                            │
│      primary_skills: [skill_a, skill_b]                                             │
│      stages: [stage_id_a, stage_id_b]                                               │
│                                                                                     │
│  STEP 2: Create agent definition (.claude/agents/new_agent_name.md):                │
│                                                                                     │
│    I DO:        [bounded responsibilities]                                          │
│    I DON'T DO:  [delegated responsibilities]                                        │
│    CONTRACT:    input → output specification                                        │
│    TOOLS:       allowed / denied tool permissions                                   │
│                                                                                     │
│  STEP 3: Validation (automatic):                                                    │
│                                                                                     │
│    ┌──────────────────────────────────────────────────────────────┐                 │
│    │ • must_declare_primary_skills ✓                              │                 │
│    │ • must_declare_stages ✓                                      │                 │
│    │ • must_follow_supervision_rules ✓                            │                 │
│    │ • can_own_stages: true                                       │                 │
│    │ • can_use_skills: true                                       │                 │
│    │ • can_access_artifacts: true                                 │                 │
│    │ • AgentRouter validates I/O contract                         │                 │
│    └──────────────────────────────────────────────────────────────┘                 │
│                                                                                     │
│  STEP 4: AgentRouter picks up new agent on next dispatch:                            │
│                                                                                     │
│    AgentRouter.resolve(task_keywords) → new_agent_name ✓                            │
│    ConfigLoader validates input_contract against available artifacts                │
│    Supervision layer tracks new agent activity in passport ledgers                  │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

### 6.5 New Skill Registration

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                     NEW SKILL REGISTRATION WORKFLOW                                    │
│                                                                                     │
│  STEP 1: Define in config (config/default_config.yaml → skills_dispatcher):          │
│                                                                                     │
│    new_skill_name:                                                                  │
│      triggers: ["keyword1", "keyword2", "中文触发词"]                                │
│      phase: "research|analysis|writing|polish|revision|review|verification"         │
│      agent: "primary_agent"                                                         │
│                                                                                     │
│  STEP 2: Create skill definition (.claude/skills/new_skill_name.md):                │
│                                                                                     │
│    Standard SKILL.md format with purpose, inputs, outputs, and workflow steps.      │
│                                                                                     │
│  STEP 3: Validation (automatic):                                                    │
│                                                                                     │
│    ┌──────────────────────────────────────────────────────────────┐                 │
│    │ • must_declare_triggers ✓                                    │                 │
│    │ • must_declare_phase ✓                                       │                 │
│    │ • must_declare_agent ✓                                       │                 │
│    │ • must_validate_before_registration ✓                        │                 │
│    │ • dry_run_on_register: true                                  │                 │
│    │ • conflict_detection: true ← checks for trigger overlap      │                 │
│    └──────────────────────────────────────────────────────────────┘                 │
│                                                                                     │
│  STEP 4: Custom skill manifest (config/custom_skills.yaml):                          │
│                                                                                     │
│    SkillsDispatcher picks up new skill on next keyword match.                        │
│    Chained skills auto-queued after primary skill completion.                        │
│    Agent assignment verified against declared agent field.                          │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

### 6.6 Supported Language Runtimes

```
  ┌──────────┬──────────────┬──────────────────────┬──────────────────┬───────────────┐
  │ LANGUAGE │ EXTENSION    │ RUNNER               │ MIN VERSION      │ PKG MANAGER   │
  ├──────────┼──────────────┼──────────────────────┼──────────────────┼───────────────┤
  │ R        │ .R           │ Rscript              │ 4.0.0            │ renv          │
  │ Python   │ .py          │ python               │ 3.9.0            │ pip           │
  │ Shell    │ .sh          │ bash                 │ 5.0.0            │ —             │
  │ Jupyter  │ .ipynb       │ jupyter nbconvert    │ 6.0.0            │ pip           │
  │          │              │ --to notebook --execute│                 │               │
  └──────────┴──────────────┴──────────────────────┴──────────────────┴───────────────┘
```

### 6.7 Extension Matrix: What Requires Code Change

```
  ┌──────────────────────────────────────┬─────────────────────────────┬─────────────┐
  │ EXTENSION                            │ MECHANISM                   │ CODE CHANGE │
  ├──────────────────────────────────────┼─────────────────────────────┼─────────────┤
  │ New research domain                  │ config YAML section         │ NO          │
  │ New journal in database              │ journal_database.yaml       │ NO          │
  │ New paper type                       │ config YAML section         │ NO          │
  │ New integrity gate                   │ config YAML + checker method│ YES (method)│
  │ New agent                            │ config YAML + .md definition│ NO          │
  │ New skill                            │ config YAML + .md definition│ NO          │
  │ Custom analysis script               │ drop into scripts/custom/   │ NO          │
  │ New CLI command                      │ add handler in main.py      │ YES (handler)│
  │ Per-paper config override            │ papers/{id}/paper_config.yaml│ NO         │
  │ New code library plugin              │ drop into code_library/     │ NO          │
  │ New language runtime                 │ config YAML + runner check  │ NO          │
  └──────────────────────────────────────┴─────────────────────────────┴─────────────┘
```

---

## 7. Complete File Manifest

### 7.1 Project Tree by Layer

```
ResearchPaperWorkflow_v2/                          ← PROJECT ROOT
│
├── config/                                        ← CONFIGURATION LAYER
│   ├── default_config.yaml                        ← Master config (1337 lines): 18 stages, 12 agents,
│   │                                               16 gates, 16 skills dispatched, 6 paper types,
│   │                                               5 research domains, extension points
│   ├── journal_database.yaml                      ← 25 journals across 6 tiers with formatting requirements
│   └── templates/
│       ├── methods_template.md                    ← Methods section structural template
│       ├── results_template.md                    ← Results section structural template
│       └── PHASE_REPORT_TEMPLATE.md               ← Phase report template for workflow summaries
│
├── src/paper_workflow/                            ← SOURCE CODE (4-layer architecture)
│   │
│   ├── strategy/                                  ← LAYER 1: STRATEGY
│   │   ├── __init__.py                            ← Package init
│   │   ├── research_strategy.py                   ← Top-level ResearchStrategyManager orchestrator
│   │   ├── topic_selector.py                      ← Idea string → structured ResearchTopic dataclass
│   │   ├── journal_targeter.py                    ← Journal name → JournalTarget (25 journal DB)
│   │   ├── feasibility.py                         ← 4-dim assessment → Go/No-Go FeasibilityReport
│   │   └── hypothesis_framework.py                ← Topic → H1-H4 hypotheses generation
│   │
│   ├── engine/                                    ← LAYER 2: DECISION
│   │   ├── __init__.py                            ← Package init
│   │   └── loop_engine.py                         ← PaperLoopEngine: 18-stage state machine,
│   │                                               8-step observe-decide-run-verify-record-
│   │                                               mark_stale-diagnose cycle, Passport integration
│   │
│   ├── cli/                                       ← LAYER 3: EXECUTION (user interface)
│   │   ├── __init__.py                            ← Package init
│   │   └── main.py                                ← 12 CLI commands: create, status, start, resume,
│   │                                               checkpoint, integrity, diagnose, revise, export,
│   │                                               config, list, reset
│   │
│   ├── reporting/                                 ← LAYER 3: EXECUTION (reporting)
│   │   ├── __init__.py                            ← Package init
│   │   └── phase_reporter.py                      ← Phase-level workflow report generator
│   │
│   ├── supervision/                               ← LAYER 4: SUPERVISION
│   │   ├── __init__.py                            ← Package init
│   │   ├── passport.py                            ← PaperPassport: 4-file ledger system
│   │   │                                            (project_passport.yaml, artifact_ledger.jsonl,
│   │   │                                             checkpoint_ledger.jsonl, integrity_ledger.jsonl)
│   │   └── integrity.py                           ← IntegrityGateChecker: 16-rule automated gate engine
│   │                                                IntegrityReport + GateResult dataclasses
│   │
│   └── utils/                                     ← SHARED UTILITIES
│       ├── config_loader.py                       ← ConfigLoader: YAML parsing, stage/agent/gate loading
│       ├── agent_protocols.py                     ← Agent I/O contract definitions and validation
│       └── reproducibility.py                     ← Reproducibility utilities (seeds, env snapshots, git info)
│
├── .claude/                                       ← EXECUTION LAYER (agent/skill/team definitions)
│   ├── SKILL_REGISTRY.md                          ← Complete 28-skill registry with stage mapping,
│   │                                                trigger keywords, agent assignments, chain diagrams
│   │
│   ├── skills/                                    ← 12 framework skill definitions
│   │   ├── paper_loop.md                          ← Main loop engine: observe→decide→run→verify pipeline
│   │   ├── topic_research.md                      ← Research strategy wrapper (S1, S2, S4)
│   │   ├── literature_search.md                   ← Systematic literature search wrapper (S3)
│   │   ├── figure_planning.md                     ← Figure planning wrapper (S6)
│   │   ├── paper_writing.md                       ← IMRAD writing wrapper (S9-S13, S16, S18)
│   │   ├── revision_routing.md                    ← Revision routing wrapper (S15-S17)
│   │   ├── qc_pipeline.md                         ← Quality control & integrity gate wrapper
│   │   ├── spatial_analysis.md                    ← Spatial transcriptomics analysis wrapper
│   │   ├── pathway_inference.md                   ← Pathway/gene set enrichment wrapper
│   │   ├── statistical_testing.md                 ← Statistical testing wrapper
│   │   ├── multi_omics.md                         ← Multi-omics integration wrapper
│   │   └── reproducibility.md                     ← Reproducibility verification wrapper
│   │
│   ├── agents/                                    ← 10 agent definition files
│   │   ├── research_strategist.md                 ← Strategy agent (S1, S2, S4)
│   │   ├── literature_reviewer.md                 ← Literature agent (S3)
│   │   ├── data_auditor.md                        ← Data quality agent (S5)
│   │   ├── figure_planner.md                      ← Figure design agent (S6)
│   │   ├── analysis_executor.md                   ← Analysis execution agent (S7)
│   │   ├── pipeline_engineer.md                   ← Reproducibility agent (S8)
│   │   ├── statistician.md                        ← Statistics audit agent (cross-cutting)
│   │   ├── report_writer.md                       ← Writing agent (S9-S13, S16, S18)
│   │   ├── integrity_checker.md                   ← Quality agent (S14, S15, S17, S18)
│   │   └── team_orchestrator.md                   ← Coordination agent (all stages)
│   │
│   └── teams/                                     ← 1 team configuration
│       └── paper_writing_team.md                  ← 9+1 agent team with 18-stage details,
│                                                    checkpoint configs, dependency graph
│
├── code_library/                                  ← REUSABLE ANALYSIS PATTERNS
│   ├── patterns/
│   │   ├── qc/
│   │   │   └── mt_filter.py                       ← Mitochondrial gene filter pattern
│   │   └── clustering/
│   │       ├── leiden_clustering.py               ← Leiden clustering parameterized pattern
│   │       └── multi_resolution.py                ← Multi-resolution clustering sweep
│   ├── modules/                                   ← Reusable analysis modules
│   ├── solutions/                                 ← Domain-specific analysis solutions
│   ├── snippets/
│   │   ├── h5ad_io.py                             ← AnnData H5AD I/O snippet
│   │   ├── logging_setup.py                       ← Structured logging setup snippet
│   │   └── yaml_config.py                         ← YAML config loading snippet
│   ├── r/                                         ← R analysis scripts
│   └── pipelines/                                 ← End-to-end pipeline scripts
│
├── papers/                                        ← PAPER PROJECTS (runtime artifacts)
│   ├── test_e2e_dryrun/                           ← E2E test: dry-run mode
│   │   ├── project_passport.yaml
│   │   ├── checkpoint_ledger.jsonl
│   │   ├── workflow_report.md
│   │   └── workflow_state/
│   ├── test_e2e_conv/                             ← E2E test: conversational mode
│   │   ├── project_passport.yaml
│   │   ├── checkpoint_ledger.jsonl
│   │   └── workflow_state/
│   ├── test_e2e_abort/                            ← E2E test: abort scenario
│   │   ├── project_passport.yaml
│   │   ├── checkpoint_ledger.jsonl
│   │   └── workflow_state/
│   ├── test_e2e_cb/                               ← E2E test: circuit breaker
│   │   ├── project_passport.yaml
│   │   ├── artifact_ledger.jsonl
│   │   ├── checkpoint_ledger.jsonl
│   │   ├── research_plan/
│   │   └── workflow_state/
│   ├── test_e2e_live/                             ← E2E test: live execution
│   │   ├── project_passport.yaml
│   │   ├── artifact_ledger.jsonl
│   │   ├── checkpoint_ledger.jsonl
│   │   ├── research_plan/
│   │   ├── data/
│   │   ├── results/
│   │   └── integrity/
│   └── test_e2e_final/                            ← E2E test: finalize
│       ├── project_passport.yaml
│       ├── artifact_ledger.jsonl
│       ├── checkpoint_ledger.jsonl
│       └── research_plan/
│
├── docs/                                          ← DOCUMENTATION
│   ├── ARCHITECTURE.md                            ← Full architecture document (1298 lines):
│   │                                                10 sections covering 4-layer architecture,
│   │                                                18-stage pipeline, loop engine, passport system,
│   │                                                integrity gates, agent system, skill system,
│   │                                                data flow, extension points, comparison
│   ├── QUICK_START.md                             ← Quick start guide
│   └── FRAMEWORK_BLUEPRINT.md                     ← THIS FILE: comprehensive visualization document
│
├── tests/                                         ← TEST SUITE
│   └── test_all.py                                ← Full integration test suite
│
├── logs/                                          ← PIPELINE LOGS
│   └── pipeline.log                               ← Structured JSON logs with rotation
│
├── scripts/custom/                                ← CUSTOM USER SCRIPTS (auto-discovered)
├── extensions/                                    ← EXTENSION SCRIPTS
│   ├── python/                                    ← Python extensions
│   ├── R/                                         ← R extensions
│   └── shell/                                     ← Shell extensions
│
├── AGENTS.md                                      ← Project-level agent instructions
├── CLAUDE.md                                      ← Project-level Claude instructions
└── README.md                                      ← Project overview and setup instructions
```

### 7.2 File Count by Layer

```
  ┌──────────────────────────┬──────────┬──────────────────────────────────────────┐
  │ LAYER / DIRECTORY        │ FILES    │ DESCRIPTION                              │
  ├──────────────────────────┼──────────┼──────────────────────────────────────────┤
  │ Configuration            │    6     │ YAML configs, journal DB, templates      │
  │ Strategy (source)        │    5     │ Research planning and hypothesis gen     │
  │ Decision (engine)        │    1     │ PaperLoopEngine state machine            │
  │ Execution (CLI+reporting)│    3     │ CLI commands, phase reporter             │
  │ Supervision              │    2     │ Passport system, integrity gate checker  │
  │ Utilities                │    3     │ Config loading, agent protocols, repro   │
  │ Agent Definitions        │   10     │ .claude/agents/ — agent I/O contracts    │
  │ Skill Definitions        │   12     │ .claude/skills/ — workflow templates     │
  │ Team Configurations      │    1     │ .claude/teams/ — multi-agent team specs   │
  │ Skill Registry           │    1     │ .claude/SKILL_REGISTRY.md — 28 skills    │
  │ Code Library             │   20+    │ Reusable analysis patterns & snippets    │
  │ Test Projects            │   30+    │ E2E test papers with full artifact trees │
  │ Documentation            │    3     │ ARCHITECTURE.md, QUICK_START, BLUEPRINT  │
  │ Tests                    │    1     │ Integration test suite                   │
  ├──────────────────────────┼──────────┼──────────────────────────────────────────┤
  │ TOTAL                    │  100+    │ Complete framework file count             │
  └──────────────────────────┴──────────┴──────────────────────────────────────────┘
```

### 7.3 Configuration File Statistics

```
  ┌──────────────────────────────────────┬──────────┬─────────────────────────────────┐
  │ FILE                                 │ LINES    │ CONTENTS                        │
  ├──────────────────────────────────────┼──────────┼─────────────────────────────────┤
  │ config/default_config.yaml           │  2,099   │ Pipeline, agents, skills, gates, │
  │                                      │          │ paper types, domains, extension │
  │ config/journal_database.yaml         │  1,148   │ 25 journals, 6 tiers             │
  │ config/templates/methods_template.md │      —   │ Methods section template         │
  │ config/templates/results_template.md │      —   │ Results section template         │
  │ .claude/SKILL_REGISTRY.md            │  1,309   │ 28 skills mapped to stages       │
  │ .claude/teams/paper_writing_team.md  │  2,421   │ Full team config + stage details │
  │ docs/ARCHITECTURE.md                 │  1,298   │ Complete architecture reference   │
  │ docs/FRAMEWORK_BLUEPRINT.md          │    this   │ Visual blueprint (this document)  │
  └──────────────────────────────────────┴──────────┴─────────────────────────────────┘
```

---

## Appendix A: Quick Reference Cards

### A.1 Pipeline at a Glance

```
  PHASE 1 → S1-S2-S3 → S4       (Research & Planning, 4 stages, 2 human checkpoints)
  PHASE 2 → S5-S6-S7 → S8       (Data & Methods, 4 stages, 2 CRITICAL gates)
  PHASE 3 → S9 → S10|S11 → S12  (Writing, 4 stages, 3 human checkpoints)
  PHASE 4 → S13-S14-S15          (Assembly & Review, 3 stages, 5 CRITICAL gates at S14)
  PHASE 5 → S16-S17 (↑loop)      (Revision, 2 stages, max 5 cycles)
  PHASE 6 → S18                  (Finalize, 1 stage, full 16-gate re-run)
```

### A.2 Agent Count by Type

```
  Strategy & Research:   2 agents  (research_strategist, literature_reviewer)
  Data & Analysis:       5 agents  (data_auditor, figure_planner, analysis_executor,
                                    pipeline_engineer, multi_omics_integrator)
  Cross-Cutting Expert:  1 agent   (statistician)
  Writing:               1 agent   (report_writer)
  Quality Assurance:     1 agent   (integrity_checker)
  Coordination:          1 agent   (team_orchestrator)
  Code Management:       1 agent   (code_librarian)
  ─────────────────────────────────
  TOTAL:                12 agents
```

### A.3 Key Numbers

```
  18    Pipeline stages
   6    Pipeline phases
  12    Specialized agents
  28    Registered skills (12 framework + 16 external)
  16    Integrity gates (5 CRITICAL, 8 HIGH, 3 MEDIUM)
   7    Human checkpoints (10 including phase-gate re-checks)
   4    Passport ledger files per paper
   6    Paper types supported
   5    Research domains configured
  25    Journals in database
   4    Language runtimes supported
   5    Max revision cycles (S16→S17→S16)
  120   Max analysis minutes (S7, longest stage)
   8    Steps in the loop engine cycle
```

---

*Blueprint version 1.0.0. Synchronized with framework version 1.0.0. Generated from live config and source code on 2026-06-19.*
