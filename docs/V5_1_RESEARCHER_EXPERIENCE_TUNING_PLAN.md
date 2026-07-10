# v5.1 Researcher Experience Tuning Plan

## Purpose

v5.0 established the fail-closed TargetTask production kernel. v5.1 removes the remaining gap between a researcher's idea and that kernel. The version does not expand the algorithm catalog. It adds a thin scientific-intent layer, closes confirmed orchestration defects, and makes the current evidence, blockers, and next action visible in one place.

## Baseline Truth

The release baseline is GitHub `v5.0.0` at commit `88133053daadd57dedee82b057886a7383bb2a0d`. Baseline source-local tests passed, while live inspection confirmed five gaps:

1. `AIWorkflowHarness` declared `target_task` but had no execution branch.
2. `StrategyEvaluator.method_family()` could classify FindMarkers as bulk DE.
3. TargetTask outputs were not bound into `workflow_contract.yaml`.
4. Seurat subcluster artifacts lacked method-specific fail-closed QA.
5. current Agent and legacy Skill documents still described v4.x behavior.

The local shell also imported an older checkout when `PYTHONPATH=src` or an editable installation was absent. Release instructions now make the source-layout requirement explicit.

## Phase 1: Production-Chain Corrections

Status: implemented and covered by focused tests.

- route natural-language TargetTask validate, plan, run, evaluate, and package requests to `TargetTaskOrchestrator`;
- require an existing TargetTask path and explicit approval for real execution;
- regenerate mode/profile packets after intent overrides so active stages and forbidden actions remain coherent;
- classify FindMarkers as `cell_level_de_exploratory` and state the pseudoreplication boundary;
- add `target_task_contract` to the workflow truth layer and validate its required outputs and stage bridges;
- add Seurat subcluster checks for required marker columns, valid FDR, nonempty finite program scores, resolution grid, one selected resolution, QC status, RDS object, five figures, and session information.

## Phase 2: Research Intent Contract

Status: implemented.

`research_intent.v1` records the scientific question before modules are selected. It separates facts, assumptions, decisions, and unknowns and requires:

- a stable project identifier;
- project goal and claim boundary;
- dataset identifier, modality, format, and path;
- expected figures, tables, or reports;
- optional sample, condition, replicate, workflow, parameter, and Figure goals.

`ResearchIntentPlanner` compiles this contract into project-scoped artifacts under `papers/<project_id>/research_plan/`. Missing data can block execution without preventing strategy design.

## Phase 3: Scientific Planner And Strategy Simulation

Status: implemented.

The planner reads `code_library/method_knowledge_base.yaml`, module production gates, and local experience lessons. For every relevant method it reports:

- what the method solves and does not solve;
- statistical unit;
- prerequisites and missing prerequisites;
- executable, deferred, or planning-only status;
- module grade and environment gate;
- reviewer risks and claim boundary;
- appropriate figure roles.

For single-cell disease contrasts, absent sample mapping or biological replicates defers pseudobulk and limits FindMarkers to exploratory screening. Enrichment cannot precede a ranked-gene result. WGCNA and communication analysis remain secondary hypothesis tools.

## Phase 4: Figure-First Planning

Status: implemented.

The planner produces `figure_plan.yaml` and `FIGURE_PLAN.md`. Each figure declares a scientific message, required evidence, required modules, and claim boundary. This prevents a method stack from becoming the research story by default. The plan explicitly rejects UMAP-only inference, enrichment without ranking provenance, and network predictions presented as mechanism proof.

## Phase 5: Research Dashboard And Short CLI

Status: implemented.

The public researcher path is one command group:

```text
research validate
research start
research analyze
research review
research write
research package
research status
```

`RESEARCH_DASHBOARD.md` consolidates question, current status, recommended and deferred methods, blockers, next best actions, claim boundary, and publication readiness. Expert TargetTask and registry commands remain available but are not required for routine project control.

## Phase 6: Experience And Knowledge Activation

Status: implemented.

The method knowledge base is distinct from executable module metadata: it explains scientific purpose and alternatives. Local experience entries are now read by the planner rather than stored passively. Current lessons cover external scaffold promotion, single-cell pseudoreplication, network overclaim, fail-closed TargetTask use, and Figure-first design.

## Phase 7: Seurat Quality Improvement

Status: implemented and real-data validated on the official PBMC3K tutorial fixture.

The subcluster wrapper no longer selects the resolution with the maximum cluster count. It prefers the first stable cluster-count plateau and records the reason, falling back to the middle eligible resolution. Empty marker results or empty/nonfinite program scores now stop with a blocked QC report.

Marker-driven subsetting now requires both a minimum total marker count and a minimum lineage-anchor count. TargetTask parameters are mapped into graph node parameters and concrete R command arguments, including QC thresholds, clustering settings, subset rules, marker test, and declared program gene sets. The final release run retained 1,372 of 2,638 QC-passing cells, selected six exploratory subclusters at resolution 0.4, produced 2,962 marker rows and 24 program-summary rows, and passed source-map, environment, and bioinformatics QA gates.

## Phase 8: Documentation And Agent Alignment

Status: implemented.

- `AGENT_ROLES.md` now describes a v5.1 research-team overlay over the existing configured agents.
- `.claude/SKILL_REGISTRY.md` marks its stage map as a retained legacy map under the v5.1 operating contract.
- README and user/architecture guidance distinguish researcher and expert paths.
- historical versioned documents remain archived; current unversioned documents no longer claim v4.x behavior.

## Phase 9: Verification

Release-blocking checks:

1. source-local contract validation passes;
2. all Python tests pass with a repository-local `--basetemp`;
3. supervision fault injection never yields pass;
4. Research Intent smoke generates all planning artifacts without analysis execution;
5. module grade and complexity budgets pass;
6. R wrappers parse and dry-run with the detected R executable;
7. PBMC3K real execution either passes with auditable artifacts or reports a concrete block; no fake pass is allowed;
8. GitHub pull-request CI passes before merge and release.

The committed evidence packet is `validation/pbmc3k_v5_1/validation_summary.yaml` plus an artifact SHA-256 manifest. Large tutorial data, figures, and RDS files remain local.

## Phase 10: Performance And Evidence Closure

Status: implemented.

Every analysis graph run now writes `performance/node_timing.yaml`, `performance/output_size_report.yaml`, and `performance/performance_ledger.tsv`. The final PBMC3K release run completed two real R nodes in 237.93 seconds. Performance files are part of the run manifest, and the validation capture script refuses to create release evidence unless real execution, source maps, bioinformatics QA, and final evaluation all pass.

## Non-Goals

- no automatic package installation;
- no automatic mechanism or clinical claims;
- no promotion of adapter/scaffold assets;
- no replacement of researcher review, sample-level design, or orthogonal validation;
- no new web dashboard or large frontend surface.
