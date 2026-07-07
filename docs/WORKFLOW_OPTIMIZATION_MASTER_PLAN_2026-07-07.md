# ResearchPaperWorkflow Optimization Master Plan

Created: 2026-07-07

Canonical framework repo: `C:\Users\HP\Documents\论文\ResearchPaperWorkflow`

Canonical implementation root: `C:\Users\HP\Documents\IgG4-ROD  vs  MALT-L`

Current implementation paper root:
`C:\Users\HP\Documents\IgG4-ROD  vs  MALT-L\papers\strat-bulktranscriptomic_immunedeconvolution_and_wgcna_module-20260629-1729`

GitHub repo: `anthonyvmppg3yigdt33kp-lang/ResearchPaperWorkflow`

Active release observed on 2026-07-07: `v4.3.0`, published 2026-06-29.

## 1. Mode And Scope

Mode for this planning pass: `analysis_design_mode`.

Allowed inputs used:

- Framework docs and source: `README.md`, `ARCHITECTURE.md`,
  `config/default_config.yaml`, `src/paper_workflow/engine/loop_engine.py`,
  `src/paper_workflow/engine/agent_dispatcher.py`,
  `src/paper_workflow/cli/main.py`.
- Collaboration docs and rules: `docs/CODEX_COLLABORATION_SYSTEM.md`,
  `.agents/skills/codex-collaboration-orchestrator/SKILL.md`,
  `config/result_write_policy.yaml`, `config/visualization_contract.yaml`.
- IgG4 implementation evidence:
  `docs/OMICS_WORKFLOW_UPGRADE_2026-07-04.md`,
  `config/custom_agents.yaml`,
  paper-level `brief/STAGE_SUMMARY.md`,
  paper-level `project_passport.yaml`,
  `results/HRA010437_ecotype_project_20260704/14_optimization_upgrade_20260705/summary.md`.
- GitHub live checks through `gh CLI`.

Forbidden in this pass:

- No analysis execution.
- No package installation or database download.
- No checkpoint promotion.
- No cleanup/move/delete of legacy result folders.
- No PR/release publication before implementation and tests exist.

Evidence standard: every design claim below is tied to a file, command result,
or explicit observed repository state. Memory-derived prior context is treated
only as a routing clue.

## 2. Current State Evidence

### Framework

- `README.md` describes V4 as a 20-stage workflow with 44 integrity gates,
  13 routed agents, skill installation, and a CLI surface.
- `ARCHITECTURE.md` documents a four-layer design:
  Strategy, Decision, Execution, Supervision.
- `config/default_config.yaml` currently places `target_journal` at order 2,
  `design_analysis_plan` at order 5, `figure_planning` at order 7, and
  `run_analysis` at order 8.
- `loop_engine.py` implements the state machine around
  `pending`, `running`, `completed`, `failed`, `stale`, `skipped`, `blocked`,
  and pipeline states including `clean`, `stale_stages`, `gate_failure`,
  `drift_detected`, and `blocked`.
- `agent_dispatcher.py` connects stages to handlers, but the current
  `figure_planning` and `run_analysis` paths mostly create templates and a
  `results/run_manifest.yaml`. They do not yet select a concrete analysis
  module, run a typed analysis plan, evaluate result quality, or manage
  `results/runs/<run_id>/`.
- GitHub workflow check showed only `Dependency Graph` active. There is no
  project CI workflow currently proving tests, YAML validation, CLI smoke, or
  large-file guards.

### IgG4 Implementation

- The paper-level brief exists under the paper root, not the implementation
  repository root:
  `papers/strat-bulktranscriptomic_immunedeconvolution_and_wgcna_module-20260629-1729/brief/STAGE_SUMMARY.md`.
- The root-level `brief/STAGE_SUMMARY.md` and root-level
  `results/current_run.yaml` were not present during this pass. The framework
  should therefore route by paper root first, and only then use root-level
  shortcuts when they exist.
- The paper brief states current truth source is `project_passport.yaml`,
  pipeline state is `stale_stages`, and the brief is a coordination layer that
  must not promote stale stages to completed.
- The paper passport shows many real outputs and gate results, but also marks
  key downstream outputs as stale. This confirms the user's core pain point:
  there is real evidence, but the workflow truth and continuation path are hard
  to operate from one stable entry point.
- The optimization package summary reports:
  12 axis features tested, 69,858 count-based pseudobulk DE rows, 11 eligible
  count-based states, 6 WGCNA modules graded, and 109 manifested files. It also
  states that the results strengthen an exploratory route but do not validate
  spatial/BCR claims or complete downstream workflow stages.
- `docs/OMICS_WORKFLOW_UPGRADE_2026-07-04.md` already created a useful
  code-only omics reserve and installed major bioinformatics skills, but it
  also records that `fast_context_search` was not available in that session.

### Existing Improvements Already Present

The current working tree already contains useful uncommitted additions:

- `docs/CODEX_COLLABORATION_SYSTEM.md`
- `.agents/skills/codex-collaboration-orchestrator/SKILL.md`
- `config/result_write_policy.yaml`
- `config/visualization_contract.yaml`
- `config/bioinformatics_method_contract.yaml`
- `config/reporting_contract.yaml`
- `AGENTS.md` updates
- `pyproject.toml` updates

This master plan builds on those files rather than replacing them.

## 3. Core Problem Statement

The workflow is architecturally rich but operationally too monolithic for
exploratory clinical bioinformatics. In practice:

1. Planning and analysis agents are declared, but critical analysis execution
   paths are still manifest/template generators.
2. Progress reporting requires repeated prompting because there is no compact,
   canonical brief/current-run layer across repo root and paper root.
3. Analysis output layout is not strict enough; multiple result directories can
   accumulate without a stable continuation pointer.
4. Figure quality is not controlled by a publication-grade source-map contract
   before figures become manuscript/PPT material.
5. Journal selection is too early for exploratory projects; it should be a late
   evidence-maturation or submission-readiness decision unless the user
   explicitly starts with a target journal.
6. Exploratory analysis needs selective retention, not full preservation of
   every transient output.
7. Different tasks should activate only the necessary layers and agents.
8. There is no CI gate proving these contracts and CLI paths on GitHub.

## 4. Target Design

### 4.1 Operating Modes

The framework should make these modes first-class in docs, config, and CLI:

| Mode | Purpose | Writes | Human checkpoint |
|---|---|---|---|
| `exploration_mode` | Read-only orientation and evidence map | none by default | no |
| `analysis_design_mode` | Statistical/bioinformatics design before execution | design docs only | yes before execution |
| `execution_mode` | Approved bounded run or code edit | owned run path only | yes if dependencies/data/raw files change |
| `closeout_audit_mode` | Final gate before stage promotion/submission | audit report only | yes |
| `ppt_briefing_mode` | Brief/PPT source map from confirmed outputs | brief docs/deck only | yes before final deck |
| `retrospective_mode` | Convert friction into rules/contracts/skills | docs/contracts/skills | optional |

### 4.2 Layer Activation Profiles

Instead of activating the full 20-stage loop for every task, add profiles:

| Profile | Active layers | Typical stages | Skip/defer |
|---|---|---|---|
| `quick_status` | Supervision + brief | passport, brief, current run | no analysis |
| `exploratory_omics` | Strategy-light + Execution + Supervision | design plan, data audit, run analysis, verify methods | target journal, full manuscript |
| `analysis_design` | Strategy + Decision | hypotheses, SAP, routing map | execution |
| `evidence_maturation` | Execution + Supervision + Writing-light | verified outputs, source maps, results draft | journal finalization |
| `manuscript_build` | Writing + Review | methods/results/discussion, AIGC scan | raw exploration |
| `submission_closeout` | Supervision + Review + Finalize | integrity, data availability, journal fit | new analysis unless approved |

### 4.3 Result Run Contract

Adopt the layout in `config/result_write_policy.yaml` as mandatory:

```text
results/
  current_run.yaml
  current/
  runs/
    <run_id>/
      intent_packet.md
      analysis_design.yaml
      run_manifest.yaml
      parameters.yaml
      inputs_manifest.yaml
      outputs_manifest.yaml
      figure_source_map.yaml
      table_source_map.yaml
      logs/
      qc/
      tables/
      figures/
      closeout_audit.md
```

Rules:

- New analysis outputs must go under `results/runs/<run_id>/`.
- Legacy results are inventoried first, then optionally migrated after user
  approval.
- `results/current_run.yaml` is the continuation pointer, not "latest folder by
  timestamp".
- Exploratory runs can be marked `discardable`, `retained_summary_only`, or
  `promoted_to_stage_evidence`.
- Large matrices and raw files are referenced by manifest path/hash, not copied
  into every run.

### 4.4 Brief Layer

Every real paper project should have:

```text
brief/
  PROJECT_BRIEF.yaml
  STAGE_SUMMARY.md
  SLIDE_BRIEF.md
  FIGURE_STORYLINE.md
```

The brief layer is not workflow truth. It is the human-readable coordination
surface that points to the truth sources:

- `project_passport.yaml`
- `artifact_ledger.jsonl`
- `integrity_ledger.jsonl`
- `results/current_run.yaml`
- selected run manifests and source maps

### 4.5 Analysis Execution

The current `run_analysis` handler should become a planner/executor wrapper,
not a generic placeholder.

Minimum design:

1. `plan-analysis` creates an `analysis_design.yaml` from user goal, data
   inventory, contracts, and code-library capabilities.
2. User approves the design.
3. `run-analysis` executes one bounded adapter selected by modality:
   bulk RNA-seq, scRNA, spatial, multi-omics, metabolomics, MR, ML biomarker.
4. The adapter writes run-scoped manifests, parameters, logs, tables, figures,
   and quality metrics.
5. `evaluate-run` scores completeness, reproducibility, figure quality,
   error status, runtime, and estimated token/agent-step cost where available.
6. Only `qa_passed` or user-approved exploratory summaries can update
   `results/current_run.yaml`.

### 4.6 Figure Quality

Make `config/visualization_contract.yaml` a gate for manuscript/PPT figures:

- no unmapped final figure;
- source data path, script path, statistical unit, method, and claim boundary
  required;
- R package default plots are acceptable only as QC, not final figures, unless
  polished through a figure adapter;
- figure planning must be source-bound, not an empty template.

### 4.7 Journal Timing

Change default behavior:

- If user supplies a target journal, keep early journal constraints.
- If the project is exploratory, defer final `target_journal` to
  `evidence_maturation` or `submission_closeout`.
- Early stage can record `candidate_journal_class` instead of a final journal.
- Journal choice must reflect actual evidence maturity, figure strength,
  validation status, and claim boundary.

## 5. Work Threads And Steps

### T0. Repository Hygiene And Branch Strategy

Goal: make the implementation path safe before larger edits.

Steps:

1. Inventory current uncommitted changes in framework and IgG4 implementation.
2. Classify files as user-authored, Codex-authored, generated output, or legacy.
3. Create a dedicated branch for the optimization work after confirming the
   intended base.
4. Keep IgG4 implementation outputs out of the framework release unless they
   are test fixtures or docs examples.

Acceptance evidence:

- clean branch plan;
- `git status --short` reviewed;
- no unrelated user work reverted;
- PR scope documented.

### T1. Architecture And Mode Profiles

Goal: convert collaboration modes and layer activation into framework config.

Steps:

1. Add mode/profile config, probably under `config/workflow_modes.yaml`.
2. Add routing rules that map prompt/task type to profile and active stages.
3. Update `AGENTS.md` and docs to require intent packets for non-trivial work.
4. Add tests proving profile selection does not activate full pipeline by
   default.

Acceptance evidence:

- config file exists;
- CLI dry run shows active stages by profile;
- tests cover `exploratory_omics`, `analysis_design`, and `submission_closeout`.

### T2. Run-Scoped Result Management

Goal: stop duplicate result folder drift and make continuation deterministic.

Steps:

1. Implement `ResultRunManager`.
2. Add CLI commands:
   `new-run`, `set-current-run`, `brief-status`, `archive-run`, `evaluate-run`.
3. Enforce `results/runs/<run_id>/` and `results/current_run.yaml`.
4. Add legacy inventory mode for existing result folders.

Acceptance evidence:

- unit tests for run id validation, current pointer, retention policy;
- CLI smoke test creates a run and updates the current pointer;
- no large file copying in tests.

### T3. Real Analysis Design And Execution

Goal: make planning and analysis agents actually operational.

Steps:

1. Add `AnalysisDesign` schema and validators.
2. Add modality adapters:
   `bulk_rnaseq_deseq2`, `scrna_scanpy_or_seurat`, `spatial_squidpy_or_seurat`,
   `multiomics_mixomics_mofa`, `metabolomics_xcms_mzmine`, `mr_twosamplemr`.
3. Start with bulk RNA-seq because it maps directly to the IgG4 pain point.
4. Update `AgentDispatcher._execute_analysis_stage()` to call the manager and
   adapters instead of writing only templates.
5. Preserve dry-run mode for design review.

Acceptance evidence:

- `run_analysis` writes a real run-scoped manifest;
- adapter selection is explainable from data inventory and design;
- failing dependencies return `BLOCKED` with setup instructions, not silent
  partial output.

### T4. Code Library And External Capability Registry

Goal: strengthen capability without uncontrolled vendoring.

Steps:

1. Add a code-library registry schema:
   source URL, commit/ref, license, retained paths, omitted data, capability
   tags, preferred adapter, risk level.
2. Keep code-only snapshots and adapters separate.
3. Add `ingest-code-library --plan` and `ingest-code-library --apply`.
4. Require license/provenance checks before any source is copied.
5. Use external repos as reference/adapter inspiration unless license and
   quality justify vendoring.

Acceptance evidence:

- registry validator;
- candidate table with source URLs and classification;
- no dataset mirroring;
- tests proving missing/empty upstream files are marked unavailable.

### T5. Visualization Quality Framework

Goal: convert ordinary package plots into publication-grade figure outputs.

Steps:

1. Implement source-map validators for figures and tables.
2. Add figure quality rubric:
   evidence binding, readability, statistical unit, color safety,
   export format, panel consistency, caption readiness.
3. Add adapters for volcano, heatmap, UMAP/composition, enrichment, network,
   and multi-panel assembly.
4. Gate PPT/manuscript use on `figure_source_map.yaml`.

Acceptance evidence:

- test fixtures for complete and incomplete figure maps;
- CLI `evaluate-figures` report;
- package default plots marked QC unless polished.

### T6. Bulk Pilot Test Harness

Goal: use a small independent bulk analysis pilot to close the loop between
workflow design, execution, and quality evaluation.

Pilot constraints:

- design first, no execution until approved;
- small fixture or sampled public-style matrix, not large raw downloads;
- run under `results/runs/<run_id>/`;
- produce tables, QC, figures, method text, and evaluation report.

Metrics:

- runtime;
- dependency failures;
- command errors;
- number and size of output files;
- manifest completeness;
- figure-source-map completeness;
- figure quality score;
- reproducibility score;
- agent/tool steps and token estimate where available.

Acceptance evidence:

- one complete pilot run in test fixture mode;
- `evaluate-run` report;
- feedback issues converted into implementation tasks.

### T7. Brief, Reporting, And PPT Lane

Goal: remove repetitive progress-report prompting.

Steps:

1. Implement `refresh-brief` from passport, current run, and selected source
   maps.
2. Add `brief-status` CLI.
3. Add `ppt-brief` source-map mode that never guesses figures.
4. Keep `PROJECT_PROGRESS.md` or equivalent as milestone ledger only, not the
   full session log.

Acceptance evidence:

- paper root with brief files;
- status summary generated from current evidence;
- no stale stage promoted by the brief layer.

### T8. CI/CD And Release Gates

Goal: make GitHub prove the workflow quality before PR/release.

Steps:

1. Add `.github/workflows/ci.yml`.
2. Run:
   `python -m compileall -q src`,
   `python -m pytest -q`,
   YAML schema checks,
   CLI smoke tests,
   contract validation,
   no-large-file guard.
3. Add docs link check if practical.
4. Add release checklist and version bump policy.

Acceptance evidence:

- GitHub Actions workflow active;
- checks green on PR branch;
- release notes generated;
- latest release verified after publication.

### T9. Documentation And User Practice Guide

Goal: make the upgraded workflow usable by the user without prompt bloat.

Steps:

1. Write new practical guide:
   `docs/CLINICAL_RESEARCH_CODEX_WORKFLOW_GUIDE.md`.
2. Include prompt packets for all modes.
3. Include "when not to run analysis" rules.
4. Include result directory and continuation examples.
5. Include troubleshooting for missing dependencies, stale passport, figure
   source-map gaps, and interrupted runs.

Acceptance evidence:

- guide exists;
- examples use actual CLI and path conventions;
- user can start from status, design, execution, audit, or PPT lane.

### T10. PR And Release

Goal: publish the upgraded version.

Steps:

1. Commit coherent batches.
2. Push branch.
3. Open PR with evidence summary and test output.
4. Address review/CI.
5. Tag and publish the next release after all gates pass.

Acceptance evidence:

- PR URL;
- CI check URLs/status;
- release URL;
- `gh release view <tag>` confirms non-draft, non-prerelease, correct target.

## 6. External Repository Candidate Registry

These candidates were searched on 2026-07-07 through GitHub CLI. They are
capability inputs, not approved vendored code.

| Area | Candidate | Stars observed | Use class | Initial decision |
|---|---:|---:|---|---|
| scRNA Python | `scverse/scanpy` | 2506 | dependency/adapter | declare dependency and wrapper |
| scRNA data | `scverse/anndata` | 756 | dependency/adapter | declare dependency and wrapper |
| scRNA R | `satijalab/seurat` | 2764 | dependency/adapter | R setup/renv, no vendoring |
| scRNA R pipeline | `zhanghao-njmu/SCP` | 656 | reference | evaluate functions and license |
| scRNA annotation | `Teichlab/celltypist` | 491 | dependency/adapter | optional cell-type adapter |
| scRNA GRN | `aertslab/pySCENIC` | 622 | dependency/adapter | optional GRN adapter |
| scRNA dynamics | `scverse/cellrank` | 454 | dependency/adapter | optional, only when data supports dynamics |
| GPU scRNA | `scverse/rapids-singlecell` | 379 | optional dependency | only under GPU profile |
| spatial Python | `scverse/squidpy` | 581 | dependency/adapter | declare dependency and wrapper |
| spatial R | `theMILOlab/SPATA2` | 171 | reference/adapter | evaluate before use |
| spatial toolkit | `STOmics/Stereopy` | 288 | reference | do not vendor initially |
| spatial methods | `prabhakarlab/Banksy_py` | 84 | optional adapter | only when spatial domain task exists |
| multi-omics R | `mixOmicsTeam/mixOmics` | 256 | dependency/adapter | declare R dependency in setup |
| multi-omics cancer | `xlucpu/MOVICS` | 147 | reference/adapter | useful for cancer subtyping |
| multi-omics framework | `scverse/muon` | 273 | dependency/adapter | Python multimodal objects |
| multi-omics OT | `cantinilab/Mowgli` | 54 | reference | advanced, not first wave |
| perturbation | `scverse/pertpy` | 336 | optional dependency | only for perturbation tasks |
| pathway/enrichment | `YuLab-SMU/clusterProfiler` | 1212 | dependency/adapter | R enrichment setup |
| pathway/enrichment | `scverse/decoupler` | 272 | dependency/adapter | Python enrichment setup |
| metabolomics | `mzmine/mzmine` | 286 | external tool | setup contract, not vendored |
| metabolomics | XCMS-related repos | low/fragmented | package dependency | use Bioconductor XCMS via setup, not GitHub script copying |
| MR | `MRCIEU/TwoSampleMR` | 551 | dependency/adapter | R MR adapter |
| MR API | `MRCIEU/ieugwasr` | 109 | dependency/adapter | MR data access setup |
| MR package | `cran/MendelianRandomization` | 45 | dependency/adapter | optional secondary MR method |
| R env | `rstudio/renv` | 1157 | setup tool | require `renv.lock` or setup phase |
| skills index | `GoekeLab/awesome-genomic-skills` | 64 | reference index | route ideas, no direct import |
| skills server | `variomeanalytics/bioinformatics-agent-skills` | 58 | reference/MCP idea | evaluate knowledge graph pattern |

Ingestion rule: the first implementation wave should prefer dependencies,
small adapters, and provenance registry entries. Full source snapshots require
explicit license review and retained-file manifests.

## 7. First Implementation Batch

Recommended first batch:

1. Add `config/workflow_modes.yaml`.
2. Add `ResultRunManager` and tests.
3. Add CLI surface for:
   `new-run`, `set-current-run`, `brief-status`, `plan-analysis`,
   `evaluate-run`.
4. Add bulk RNA-seq analysis design schema and dry-run adapter.
5. Add figure/table source-map validator.
6. Add GitHub Actions CI.

Reason: this batch directly fixes continuation, prompt bloat, result location,
and "analysis agent only writes a manifest" without requiring large biological
data execution yet.

## 8. Risks And Mitigations

| Risk | Mitigation |
|---|---|
| Scope becomes another full rewrite | implement by thread, each with tests and CLI proof |
| External repo copying creates license/data risk | dependency/adapter first, vendoring only after license/provenance gate |
| Exploratory outputs consume disk | retention policy and summary-only promotion |
| Workflow truth diverges from pretty reports | passport/current-run remain truth; brief is coordination only |
| Figure polish hides weak evidence | figure source map requires claim boundary and statistical unit |
| Early journal choice biases analysis | defer final target journal unless user specifies it |
| Missing R/Python packages cause partial outputs | setup phase or `BLOCKED`, never silent install during execution |
| fast-context unavailable | configure MCP separately; fallback to `rg` until callable |
| CI unavailable on GitHub | add Actions workflow and verify on PR before release |

## 9. Immediate Next Safe Action

Start T2 and T1 together in a small patch:

- T1: `config/workflow_modes.yaml` + dry-run profile selection.
- T2: `ResultRunManager` + `new-run`/`set-current-run` CLI + tests.

Do not start real bulk execution until:

1. the run layout is implemented;
2. the analysis design schema exists;
3. the user approves the design packet;
4. dependencies are declared through setup or `renv.lock`.

## 10. Closeout For This Planning Pass

Mode used: `analysis_design_mode`.

Files read: framework README, architecture/config/engine/dispatcher/collab
docs/contracts; IgG4 paper brief/passport/upgrade docs; GitHub repo metadata.

Files changed: this master plan only.

Commands run: `git status`, `rg`, `Get-Content`, `gh repo view`,
`gh workflow list`, `gh release list`, `gh search repos`,
`agent-reach doctor --json`.

Current truth source: framework worktree plus IgG4 paper-level
`project_passport.yaml`; GitHub live metadata from `gh`.

Risks: broad goal is not complete; no code implementation, PR, CI, or release
has been performed in this pass.

Next safe action: implement T1/T2 first, then run tests locally before creating
the PR branch.

