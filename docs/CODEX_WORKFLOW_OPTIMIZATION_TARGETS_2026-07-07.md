# Codex Workflow Optimization Targets — ResearchPaperWorkflow

Created: 2026-07-07  
Target branch: `codex/workflow-optimization-targets-20260707`  
Base branch: `master`  
Intended next release line: `v4.5.x` after implementation, tests, PR review, and release tagging.

This document converts the current workflow-optimization request into Codex-executable target packets. It is intentionally written as an implementation control document, not as a brainstorming note.

---

## 1. Operating Objective

Build ResearchPaperWorkflow into a clinical-research human-AI collaboration system that can:

1. understand vague biomedical research requests;
2. activate only the smallest useful workflow profile;
3. design analysis before execution;
4. run bounded, auditable analysis adapters only after explicit approval;
5. keep all results under deterministic run-scoped directories;
6. preserve exploratory progress without retaining every transient artifact;
7. enforce figure/table source maps before manuscript or PPT use;
8. defer final journal choice until evidence maturity unless the user explicitly supplies a target journal;
9. keep workflow truth separate from human-readable progress briefs;
10. expose transparent CLI, configuration, tests, and release gates.

The target state is not a larger monolith. The target state is a thinner routing kernel plus stronger contracts, adapters, source maps, and checkpoints.

---

## 2. Current Repository Understanding

### 2.1 Architecture already present

The repository already contains a mature truth-layer foundation:

- `README.md` declares v4.4 behavior, including collaboration modes, run-scoped result management, bounded analysis execution, code-library routing, and CI preflight.
- `ARCHITECTURE.md` defines the four-layer control model: Strategy, Decision, Execution, and Supervision.
- `workflow_contract.yaml` defines the truth condition for completed stages: real execution, required outputs, concrete quality-gate results, and checkpoint consistency.
- `src/paper_workflow/engine/loop_engine.py` implements the observe/decide/run/verify/record/stale/diagnose loop and stage states.
- `src/paper_workflow/engine/agent_dispatcher.py` maps stages to execution handlers and normalizes placeholder, pending harness, and needs-input outputs.
- `src/paper_workflow/outputs/result_run_manager.py` implements `results/runs/<run_id>/`, `results/current_run.yaml`, and `results/current/RUN_POINTER.txt`.
- `src/paper_workflow/analysis/` contains `AnalysisDesign` and bounded bulk RNA-seq dry-run / Python pilot adapters.
- `config/workflow_modes.yaml`, `config/result_write_policy.yaml`, `config/visualization_contract.yaml`, `config/bioinformatics_method_contract.yaml`, and `config/code_library_registry.yaml` already encode most of the desired policy direction.
- `.github/workflows/ci.yml`, `scripts/ci_quality_check.py`, and `scripts/ci_cli_smoke.py` provide a CI preflight surface.

### 2.2 Main remaining gaps

The system is close to the desired architecture, but several pieces are not yet strong enough for routine clinical bioinformatics collaboration:

1. **Routing gap** — `workflow_modes.yaml` exists, but mode/profile selection is not yet a first-class resolver used consistently by AI harness, CLI, and stage activation.
2. **Journal timing gap** — `target_journal` is still configured as an early default stage in `config/default_config.yaml` and `workflow_contract.yaml`. Exploratory projects need candidate journal class early, not a final target journal.
3. **Analysis execution gap** — stage-level `run_analysis` still defaults to a safe dry-run/pending-harness behavior when called through the 20-stage loop. Real pilot execution exists mainly through `paper-workflow run-analysis --execute --approved --backend python_builtin_pilot`.
4. **Modality gap** — only bulk RNA-seq has a bounded pilot adapter. Single-cell, spatial, metabolomics, Mendelian randomization, multi-omics, and AI-biomarker workflows need adapters, setup contracts, and explicit blocked states.
5. **Visualization gap** — source-map policy exists, but figure source-map validation, quality scoring, and final-figure gates need to be enforced by CLI/tests and manuscript/PPT lanes.
6. **Exploration-retention gap** — run status exists, but `discardable`, `retained_summary_only`, and `promoted_to_stage_evidence` retention policy must be implemented so exploratory work does not become uncontrolled storage.
7. **Briefing gap** — `brief-status` exists, but full `refresh-brief` and concise progress surfaces need to be generated from truth files without making the user repeatedly restate progress.
8. **Code-library gap** — registry exists, but ingestion, provenance validation, license review, and adapter selection are not yet operational.
9. **Contract gap** — `workflow_contract.yaml` still requires `results/run_manifest.yaml` for `run_analysis`, while v4.4 run-scoped logic writes under `results/runs/<run_id>/`. The contract needs a variable/run-pointer-aware resolver.
10. **Release gate gap** — CI exists, but the next release must not be tagged until the implementation targets below pass local and GitHub checks.

---

## 3. Non-Negotiable Invariants

Codex must preserve these invariants in every patch:

1. **No silent execution**: new analysis must not run without an `analysis_design.yaml` and explicit user approval.
2. **No false completion**: `template`, `pending_harness`, and `needs_input` outputs must never become completed stage truth.
3. **No output ambiguity**: new analysis outputs must be written only under `results/runs/<run_id>/` unless a legacy migration is explicitly approved.
4. **No newest-folder inference**: continuation must use `results/current_run.yaml`, not the latest timestamped folder.
5. **No raw data mutation**: raw matrices and external databases are referenced by manifest path/hash, not copied or rewritten during execution mode.
6. **No package installation during execution mode**: dependency installation belongs to setup mode or documented environment setup, not agent execution.
7. **No final claims from exploratory outputs**: exploratory runs may generate hypotheses, not definitive conclusions.
8. **No unmapped final figures**: manuscript/PPT figures require source data, script, method, statistical unit, and claim boundary.
9. **No early forced journal**: final target journal is deferred unless the user explicitly supplies one.
10. **No deletion without archive plan**: legacy folders and exploratory runs can be inventoried or archived only with explicit retention decisions.

---

## 4. Thread Map

| Thread | Objective | Primary files | Release critical |
|---|---|---|---|
| T0 | Repository hygiene and baseline audit | docs, CI, tests | yes |
| T1 | Mode/profile resolver and smallest-useful-routing | `config/workflow_modes.yaml`, AI harness, CLI | yes |
| T2 | Run-scoped result management and retention | `ResultRunManager`, CLI, tests | yes |
| T3 | Analysis-design state machine | `analysis/design.py`, manager, CLI, contract | yes |
| T4 | Real bounded analysis adapters | `analysis/adapters.py`, `code_library/`, configs | yes, staged |
| T5 | Code-library registry and ingestion | `config/code_library_registry.yaml`, CLI, validators | yes |
| T6 | Visualization quality and source maps | visualization contract, CLI, validators | yes |
| T7 | Brief/progress/PPT coordination lane | `brief/`, CLI, docs | yes |
| T8 | Workflow contract migration | `workflow_contract.yaml`, default config, loop engine | yes |
| T9 | Test board and feedback loop | `tests/`, `scripts/`, CI | yes |
| T10 | Documentation, PR, release | docs, release notes, PR body, tag | yes |

---

## 5. Codex Execution Protocol

Every Codex task must be submitted in this format:

```text
目标：<T编号 + precise deliverable>
范围：<allowed files/directories>
输入：<truth files, config files, test fixtures, user approvals>
禁止：<actions that must not happen>
步骤：<ordered implementation steps>
完成标准：<files changed + CLI/test evidence>
停止条件：<when to stop and ask/record blocker>
```

Codex must work in small batches. Do not combine broad architecture changes, adapter execution, result migration, and release tagging in one patch.

---

## 6. Detailed Targets

### 目标 T0 — Repository Hygiene And Baseline Audit

**Purpose**: establish a safe base before implementation.

**Scope**:

- Read-only audit first.
- No generated paper outputs committed.
- No external datasets, large binaries, or vendored repositories.

**Steps**:

1. Confirm current branch and base commit.
2. Run baseline checks locally:
   - `python -m compileall -q src`
   - `python scripts/ci_quality_check.py`
   - `python scripts/ci_cli_smoke.py`
   - `python -m pytest -q`
   - `python -m paper_workflow.cli validate-contract --strict`
3. Record test output in the PR body or release checklist.
4. Classify changed files as source, config, docs, tests, fixtures, or generated.
5. Verify `papers/`, `results/`, large raw data, and temporary folders are not committed.

**Completion standard**:

- Baseline status documented.
- Any failing test is converted into a blocker or separate target.
- No unrelated user work is reverted.

**Stop conditions**:

- Untracked user data or analysis results are present.
- CI-quality check finds large files or invalid YAML.
- Existing tests fail for reasons unrelated to the active target.

---

### 目标 T1 — First-Class Mode/Profile Resolver

**Purpose**: make the workflow activate the smallest useful profile instead of the full 20-stage loop by default.

**Required behavior**:

- Vague request -> `exploration_mode` / `quick_status`, no write or analysis.
- New analysis request -> `analysis_design_mode`, write design only.
- Approved bounded analysis -> `execution_mode`, write only under the active run path.
- Manuscript/PPT request -> source-map-bound writing or briefing profile.
- Submission request -> closeout audit, not new analysis.

**Steps**:

1. Add a resolver module, for example `src/paper_workflow/routing/mode_resolver.py`.
2. Load `config/workflow_modes.yaml` and expose:
   - `resolve_mode(request_text, explicit_mode=None, explicit_profile=None)`
   - `resolve_profile(mode, request_text)`
   - `active_layers(profile)`
   - `active_stages(profile)`
   - `deferred_stages(profile)`
3. Add CLI command:
   - `paper-workflow route-task --request "..." --json`
   - Optional: `--mode`, `--profile`, `--paper`.
4. Update `AIWorkflowHarness` so it uses the resolver before choosing API actions.
5. Add a dry-run output that shows mode, profile, active stages, deferred stages, writes allowed, and forbidden actions.
6. Add tests proving fuzzy requests do not activate `run_analysis`, `target_journal`, or manuscript stages.

**Completion standard**:

- `route-task` works in JSON and human-readable modes.
- Unit tests cover `quick_status`, `analysis_design`, `exploratory_omics`, `ppt_briefing_mode`, and `submission_closeout`.
- AI harness does not bypass mode/profile policy.

**Stop conditions**:

- The resolver would cause a full pipeline run for a vague or exploratory request.
- The resolver marks `execution_mode` without explicit approval.

---

### 目标 T2 — Run-Scoped Result Management And Retention Policy

**Purpose**: eliminate ambiguous result folders and make continuation deterministic.

**Required layout**:

```text
papers/<paper_id>/results/
  current_run.yaml
  current/RUN_POINTER.txt
  runs/<run_id>/
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
    evaluation_report.yaml
    closeout_audit.md
```

**Steps**:

1. Extend `ResultRunManager` with retention state:
   - `discardable`
   - `retained_summary_only`
   - `promoted_to_stage_evidence`
   - `archived`
   - `stale`
2. Add `retention_policy.yaml` support per run.
3. Add CLI commands:
   - `archive-run --paper <id> --run-id <id> --policy retained_summary_only`
   - `list-runs --paper <id> --json`
   - `inventory-legacy-results --paper <id> --json`
4. Prevent accidental writes outside `results/runs/<run_id>/` during execution mode.
5. Add a root/paper resolution rule: paper-root truth wins; repo-root shortcuts are only pointers.
6. Add tests for run ID validation, pointer updates, retention policy, legacy inventory, and no large-file copying.

**Completion standard**:

- A user can answer “where are my current outputs?” by reading `results/current_run.yaml`.
- A user can answer “what should I continue from?” with `brief-status` or `list-runs`.
- Exploratory runs can be summarized without preserving every transient table/figure.

**Stop conditions**:

- A command creates a sibling timestamp folder under `results/`.
- A command deletes legacy outputs without an explicit archive plan.

---

### 目标 T3 — Analysis-Design State Machine

**Purpose**: make planning and analysis agents operational, transparent, and approval-bound.

**Steps**:

1. Expand `AnalysisDesign` schema with:
   - `design_id`
   - `design_version`
   - `author_decision`
   - `approval_timestamp`
   - `data_inventory_refs`
   - `software_environment_refs`
   - `expected_runtime_class`
   - `retention_policy`
   - `claim_boundary`
   - `exploratory_or_primary`
2. Add validators for each modality:
   - bulk RNA-seq
   - single-cell RNA-seq
   - spatial transcriptomics
   - multi-omics integration
   - metabolomics
   - Mendelian randomization
   - ML biomarker modeling
3. Add explicit design states:
   - `draft`
   - `needs_user_input`
   - `approved_for_pilot`
   - `approved_for_real_execution`
   - `executed`
   - `evaluated`
   - `promoted`
   - `archived`
4. Make `run-analysis --execute` fail closed unless design approval is present.
5. Ensure `run_analysis` stage in the paper loop can read the current run pointer and return either:
   - real completed run evidence, or
   - blocked/pending harness with exact setup instructions.
6. Add tests for unresolved fields, missing approval, missing input files, and blocked dependency states.

**Completion standard**:

- `plan-analysis` writes a meaningful design packet.
- `run-analysis` refuses unapproved real execution.
- `evaluate-run` reports completeness, reproducibility, figure/table source maps, warnings, errors, and retention status.

**Stop conditions**:

- A design with `requires_human_input` can execute real analysis.
- A stage can become completed from a dry-run package alone.

---

### 目标 T4 — Bounded Analysis Adapter Expansion

**Purpose**: add practical multi-omics capability without uncontrolled vendoring or unsafe execution.

**Adapter principle**:

Every adapter must have three modes:

1. `dry_run`: write execution blueprint and manifests only.
2. `pilot`: run a small fixture or lightweight execution where safe.
3. `real`: run only when dependencies, inputs, approvals, and environment are declared.

**Wave 1 adapters**:

1. `bulk_rnaseq_deseq2_contract`
   - Keep Python pilot for CI smoke.
   - Add DESeq2/edgeR/limma R setup contract.
   - Real execution may call R only if setup file and approval exist.
2. `scrna_scanpy_or_seurat_contract`
   - Dry-run first.
   - Required inputs: h5ad/rds/matrix + metadata + sample/donor column.
   - Required outputs: QC, cell annotation evidence, sample-level composition, pseudobulk-ready plan.
3. `spatial_squidpy_or_seurat_contract`
   - Dry-run first.
   - Required inputs: spatial coordinates, image/spot metadata if available, sample ID.
   - Outputs: spatial QC, coordinate plots, domain/SVG plan, claim-boundary audit.
4. `multiomics_mixomics_mofa_contract`
   - Require sample matching and modality inventory before any integration.
5. `metabolomics_xcms_mzmine_contract`
   - Treat MZmine as external tool and XCMS as setup-phase dependency.
   - Do not mirror raw LC-MS data.
6. `mr_twosamplemr_contract`
   - Require exposure/outcome, instrument selection, harmonization, pleiotropy, sensitivity, and population ancestry audit.
7. `ml_biomarker_contract`
   - Require train/test split, leakage audit, nested CV or external validation plan, calibration metrics, and claim-boundary restrictions.

**Steps**:

1. Create adapter base class with shared output contract.
2. Register adapters by modality and backend.
3. Add dependency/setup checker per adapter.
4. Add blocked-state messages with exact missing setup items.
5. Add minimal fixtures only where small and license-safe.
6. Add tests for dry-run and blocked behavior before real execution.

**Completion standard**:

- Unsupported modalities no longer return a generic unsupported error; they return a modality-specific setup/design contract.
- At least bulk RNA-seq pilot remains executable in CI without external dependencies.
- Single-cell, spatial, multi-omics, metabolomics, MR, and ML adapters can produce design blueprints and blocked setup reports.

**Stop conditions**:

- Adapter downloads databases or installs packages during execution mode.
- Adapter writes outputs outside the active run directory.
- Adapter makes causal, mechanistic, clinical, or diagnostic claims from exploratory outputs.

---

### 目标 T5 — Code-Library Registry, Provenance, And Ingestion

**Purpose**: strengthen agent capability while avoiding license, data, and reproducibility risk.

**Policy**:

- Prefer dependency or adapter wrappers.
- Use external repositories as reference/capability registry entries unless license/provenance review justifies vendoring.
- Never mirror datasets, model weights, large binaries, or raw omics data by default.

**Candidate capability classes**:

- Single-cell Python: Scanpy, AnnData, scVI-tools, CellTypist, pySCENIC, CellRank.
- Single-cell R: Seurat, SCP.
- Spatial: Squidpy, Seurat spatial, Stereopy, SPATA2, Banksy.
- Multi-omics: Muon, mixOmics, MOVICS, MOFA/MOFA2-style contracts.
- Pathway/enrichment: clusterProfiler, decoupler, gseapy, g:Profiler.
- Metabolomics: MZmine, XCMS.
- Mendelian randomization: TwoSampleMR, ieugwasr, MendelianRandomization.
- Environment: renv, pyproject optional extras, container/session info.
- Agent skills: curated genomic/bioinformatics skill indexes, MCP-style capability routing.

**Steps**:

1. Add registry validator beyond current CI checks:
   - source URL
   - license
   - latest checked ref/release
   - retained paths if vendored
   - omitted data/binary list
   - capability tags
   - preferred adapter
   - risk level
2. Add CLI:
   - `ingest-code-library --plan --source <url>`
   - `ingest-code-library --apply --source <url> --license-reviewed`
   - `list-code-capabilities --modality scrna --json`
3. Store registry manifests under `code_library/registry/`.
4. Add tests proving unavailable/missing upstream files are marked unavailable, not silently imported.
5. Add documentation showing adapter-first use.

**Completion standard**:

- Agents can query capability tags without loading full external repos.
- Vendoring requires license/provenance evidence.
- Code-library choices are explainable in `analysis_design.yaml`.

**Stop conditions**:

- Any external code is copied without license review.
- Any external dataset or large binary is mirrored.

---

### 目标 T6 — Visualization Quality Framework

**Purpose**: upgrade figures from package-default QC plots to publication/PPT-ready evidence-bound visuals.

**Steps**:

1. Implement source-map validators:
   - `validate_figure_source_map(path)`
   - `validate_table_source_map(path)`
2. Add CLI:
   - `evaluate-figures --paper <id> --run-id <id> --json`
3. Add figure quality scoring fields:
   - evidence binding
   - source data availability
   - script availability
   - statistical unit declared
   - claim boundary declared
   - readability
   - export format
   - caption readiness
   - color safety
   - panel consistency
4. Classify outputs:
   - `qc_only`
   - `analysis_preview`
   - `candidate_final`
   - `manuscript_ready`
   - `ppt_ready`
5. Add figure adapters for common biomedical outputs:
   - volcano
   - heatmap
   - UMAP/composition
   - enrichment dotplot/GSEA
   - network/module plot
   - spatial feature/domain plot
   - MR forest/funnel/scatter
6. Gate manuscript/PPT lanes on source-map and quality status.

**Completion standard**:

- A default R/Scanpy/Seurat plot is treated as QC or preview unless source-mapped and polished.
- `evaluate-figures` reports missing evidence, method, source, script, or claim boundary.
- Manuscript/PPT generation refuses unmapped final figures.

**Stop conditions**:

- Figure path is used as final evidence without source data and script.
- Plot aesthetics hide missing statistics or weak evidence.

---

### 目标 T7 — Brief, Progress, And PPT Coordination Lane

**Purpose**: remove repeated progress-report prompting and make collaboration state visible.

**Required files**:

```text
papers/<paper_id>/brief/
  PROJECT_BRIEF.yaml
  STAGE_SUMMARY.md
  RUN_SUMMARY.md
  FIGURE_STORYLINE.md
  SLIDE_BRIEF.md
```

**Steps**:

1. Implement `refresh-brief` CLI.
2. Generate brief files from truth sources:
   - `project_passport.yaml`
   - `stage_results/*.json`
   - `artifact_ledger.jsonl`
   - `integrity_ledger.jsonl`
   - `results/current_run.yaml`
   - selected run manifests/source maps
3. Add `brief-status --refresh` option.
4. Ensure brief files never promote stale or pending stages.
5. Add concise user-facing progress format:
   - current truth state
   - current run pointer
   - last completed stage
   - blocked stage
   - missing inputs
   - next safest action
6. Add PPT lane that uses only source-mapped figures and tables.

**Completion standard**:

- The user can resume a project from `brief-status` without restating prior progress.
- The brief layer is readable, compact, and explicitly points to truth files.
- PPT generation does not guess figure meaning.

**Stop conditions**:

- Brief files become the source of workflow truth.
- Stale or exploratory artifacts are presented as final evidence.

---

### 目标 T8 — Workflow Contract And Journal-Timing Migration

**Purpose**: align the 20-stage contract with exploratory clinical research practice while preserving backward compatibility.

**Steps**:

1. Do not remove `target_journal` immediately; migrate behavior safely.
2. Add a conditional journal policy:
   - if user supplies target journal -> early `target_journal` remains active;
   - if exploratory project -> early stage records `candidate_journal_class` only;
   - final target journal decision moves to `evidence_maturation` or `submission_closeout`.
3. Update `workflow_contract.yaml` so `run_analysis` can validate run-scoped outputs through `results/current_run.yaml` and `results/runs/<run_id>/run_manifest.yaml`.
4. Implement a required-output resolver that can evaluate dynamic paths from current run pointer.
5. Update `verify_methods` to prefer current run-scoped manifest and fall back to legacy manifest only with warnings.
6. Add migration docs for v4.4 projects.
7. Add tests for:
   - exploratory project with deferred journal;
   - explicit target journal project;
   - run-scoped required output resolution;
   - legacy `results/run_manifest.yaml` compatibility.

**Completion standard**:

- Exploratory analysis no longer forces final journal selection before results mature.
- `run_analysis` truth verification recognizes run-scoped manifests.
- Existing projects still validate or produce actionable migration warnings.

**Stop conditions**:

- Backward compatibility is broken without migration path.
- Journal selection is deleted instead of made conditional.

---

### 目标 T9 — Test Board And Feedback Loop

**Purpose**: make optimization measurable and self-correcting.

**Test board sections**:

1. Config/schema validation.
2. Mode/profile routing.
3. Result-run manager and retention.
4. AnalysisDesign validation.
5. Adapter dry-run/blocked/pilot behavior.
6. Figure/table source-map validation.
7. Brief generation.
8. Contract dynamic-output verification.
9. CLI smoke.
10. No-large-file guard.

**Steps**:

1. Create or extend unit tests under `tests/`.
2. Add fixture paper projects with minimal files only.
3. Add one bulk RNA-seq pilot fixture that runs in CI without external packages.
4. Add negative tests:
   - missing approval;
   - missing input files;
   - unresolved design field;
   - unmapped figure;
   - stale current run;
   - unsupported modality setup missing;
   - attempted output outside run directory.
5. Extend `scripts/ci_quality_check.py` for any new config.
6. Extend `scripts/ci_cli_smoke.py` only after CLI commands are stable.
7. Record feedback as follow-up issues or PR checklist items, not as hidden notes.

**Completion standard**:

- Local preflight passes.
- GitHub Actions passes on PR.
- Failing tests produce actionable blocker messages.

**Stop conditions**:

- Tests depend on large external datasets or online downloads.
- CI requires unpinned or interactive package installation.

---

### 目标 T10 — Documentation, PR, And Release

**Purpose**: make the upgraded workflow usable and safely publishable.

**Docs to update**:

1. `README.md`
2. `ARCHITECTURE.md`
3. `docs/CLINICAL_RESEARCH_CODEX_WORKFLOW_GUIDE.md`
4. `docs/CODEX_COLLABORATION_SYSTEM.md`
5. `docs/RELEASE_NOTES_v4.5.0.md`
6. migration guide from v4.4 result layout to v4.5 dynamic run pointer behavior.

**Guide must include**:

- How to start with a vague clinical research question.
- How to run quick status without prompt bloat.
- How to create an analysis design.
- How to approve and run a bounded pilot.
- How to evaluate outputs and figures.
- How to promote a run to stage evidence.
- How to defer journal selection.
- How to resume from `results/current_run.yaml` and `brief/STAGE_SUMMARY.md`.
- What not to do.

**PR requirements**:

- PR body must list changed threads.
- PR body must list tests run and outputs.
- PR body must declare whether release is blocked or ready.
- PR must not include generated paper outputs or external datasets.

**Release requirements**:

Only release after:

1. implementation patches are merged or approved;
2. local preflight passes;
3. GitHub Actions passes;
4. release notes are accurate;
5. version numbers are updated consistently;
6. tag target matches the merge commit;
7. release is not a draft unless intentionally pre-release.

**Stop conditions**:

- Release would only document intent without implementing the target changes.
- CI is failing or unobserved.
- Version number and release notes disagree.

---

## 7. Recommended Batch Order

### Batch A — Routing and contracts

Targets: T0, T1, T8 partial.  
Goal: make mode/profile routing and journal deferral testable before touching analysis execution.

### Batch B — Result management and brief layer

Targets: T2, T7.  
Goal: make continuation deterministic and progress summaries compact.

### Batch C — Analysis state machine and bulk pilot hardening

Targets: T3, T4 bulk RNA-seq.  
Goal: ensure design -> approval -> execution -> evaluation -> retention works end to end.

### Batch D — Multi-omics adapter contracts and code-library registry

Targets: T4 non-bulk adapters, T5.  
Goal: add modality-specific blocked/dry-run adapters and capability lookup without unsafe vendoring.

### Batch E — Visualization quality gates

Targets: T6, T9.  
Goal: make source maps and figure quality enforceable.

### Batch F — Documentation, release checklist, final PR

Targets: T10.  
Goal: publish only after implementation and CI evidence exist.

---

## 8. Minimal First Codex Task

Use this as the first implementation prompt:

```text
目标：T1 + T8 partial — implement first-class mode/profile resolver and defer final target journal for exploratory projects.
范围：src/paper_workflow/routing/, src/paper_workflow/ai_harness.py, src/paper_workflow/cli/main.py, config/workflow_modes.yaml, workflow_contract.yaml, tests/, docs only as needed.
输入：README.md, ARCHITECTURE.md, config/workflow_modes.yaml, config/default_config.yaml, workflow_contract.yaml, docs/CODEX_WORKFLOW_OPTIMIZATION_TARGETS_2026-07-07.md.
禁止：run analysis, install packages, download databases, modify papers/results generated data, remove target_journal without migration.
步骤：
1. Add mode resolver module and tests.
2. Add route-task CLI dry-run.
3. Wire AI harness to resolver without bypassing WorkflowAPI truth path.
4. Add conditional journal policy: explicit target journal early, exploratory candidate_journal_class early, final journal deferred.
5. Add tests proving fuzzy/exploratory requests do not activate full pipeline.
6. Run compileall, ci_quality_check, relevant pytest, and CLI smoke if command surface changed.
完成标准：route-task returns mode/profile/active/deferred stages; tests pass; no generated analysis outputs are committed.
停止条件：any change would make unapproved analysis executable or break existing create/status/run pipeline behavior.
```

---

## 9. Practical Collaboration Rules For The User And Agent

When a new task arrives, the system should answer these questions before doing work:

1. What is the smallest useful mode?
2. Which layer is actually needed?
3. What files may be written?
4. Is there an active run pointer?
5. Is an analysis design approved?
6. Are there missing data/environment prerequisites?
7. What is the next safest action?
8. What should be reported back to the user in one compact paragraph?

The default user-facing status format should be:

```text
Mode/Profile: <mode>/<profile>
Truth source: <project_passport.yaml + stage_results>
Current run: <run_id or none>
Stage state: <last completed / blocked / stale>
Missing input: <only actionable blockers>
Next safest action: <one command or one decision>
Output location: <exact path>
```

---

## 10. Definition Of Done For The Optimization Program

The optimization program is complete only when the following are true:

1. mode/profile routing is operational in CLI and AI harness;
2. exploratory projects no longer force early final journal selection;
3. every analysis run has a deterministic `results/runs/<run_id>/` home;
4. current continuation is recoverable from `results/current_run.yaml`;
5. exploratory retention policy is implemented;
6. `run-analysis` enforces design approval;
7. non-bulk omics modalities have at least dry-run/blocked adapters with setup contracts;
8. code-library registry and ingestion validator are operational;
9. final figures/tables require source maps and quality evaluation;
10. brief/status lane reduces repetitive prompting;
11. tests cover positive and negative paths;
12. CI passes;
13. guide and release notes match implemented behavior;
14. release tag is created only after implementation evidence is real.

---

## 11. Immediate Repository Note

This file is a planning/control artifact. It does not itself complete the optimization program. Do not tag a release from this document alone. Use it to drive the next Codex implementation PRs in small batches.
