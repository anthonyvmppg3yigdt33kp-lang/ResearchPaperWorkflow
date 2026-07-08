# Method-Asset Architecture v4.6.0

v4.6.0 upgrades the analysis layer from a single execution adapter into a
multi-omics method-asset orchestration system.

## Layers

| Layer | Main Objects | Responsibility |
|---|---|---|
| Strategy | `MethodSelector`, `list-capabilities`, `plan-analysis` | Choose methods from current data, environments, assets, and reviewer value. |
| Asset Knowledge | `module_registry.yaml`, module folders, figure style registry | Describe methods, inputs, outputs, claim boundaries, maturity, and executable contracts. |
| Environment | `EnvironmentRegistry`, `env_locks/*.lock.yaml` | Resolve runners, packages, lock files, and reproducibility grades without installing packages. |
| Data Truth | `DataRegistry` | Validate immutable input paths, tutorial boundaries, sample mapping, and file manifests. |
| Execution | `AnalysisGraph`, `AnalysisGraphExecutor` | Execute approved DAG nodes inside `results/runs/<run_id>/`. |
| Evidence | `EvidenceGraph`, `EvidenceSynthesizer` | Convert source maps into evidence matrices, claim ledgers, figure storylines, and reviewer-risk reports. |
| Feedback | `module_feedback.py`, usage ledger, proposals | Record module outcomes and route improvement proposals for review. |

## Key Boundaries

The executor can run a method asset, but it cannot declare a workflow stage
complete. Stage completion still flows through:

```text
WorkflowAPI -> PaperLoopEngine -> verify_stage -> passport / ledgers / stage_results
```

The code library can recommend methods, but it cannot invent availability. A
selected module must exist in `module_registry.yaml`, resolve to a source path,
declare an environment, and satisfy registry schema checks.

The feedback loop can propose changes, but it cannot silently mutate executable
contracts. Registry updates remain reviewed source changes.

## Method Asset Contract

Each method asset should declare:

- `id`
- `modality` and aliases
- `step`
- `language`
- `capability_tags`
- biological question types
- source path and upstream provenance
- environment id and packages
- executable command template when supported
- input and output schemas
- reviewer value
- reviewer risk
- claim boundary
- figure and table outputs
- validation status
- method maturity

Thin wrappers are acceptable when they make an existing script executable,
auditable, and source-map aware. They should not hide unreviewed package
installation or write outside their node directory.

## Execution Graph

`AnalysisGraph` is written per run:

```text
papers/<paper_id>/results/runs/<run_id>/analysis_graph.yaml
```

Execution policy defaults:

```yaml
require_user_approval: true
require_data_registry: true
require_env_lock: true
raw_data_mutation: forbidden
write_scope: results/runs/<run_id>/
```

Graph execution writes:

- run manifest
- output manifest
- node manifests
- node stdout/stderr logs
- node sessionInfo where applicable
- aggregate figure and table source maps

## Evidence Graph

`evaluate-run --write-report` reads run manifests and source maps, then writes:

```text
tables/evidence_matrix.tsv
review/reviewer_risk_report.md
brief/FIGURE_STORYLINE.md
claims/claim_ledger.jsonl
```

Evidence levels are conservative. Tutorial figures and marker displays remain
observations or hypotheses unless independent validation and proper statistical
units are present.

## External Code Intake

External code sources are imported into `code_library/external_sources/` with a
manifest and review record. Importing code is not the same as making it
executable. Promotion requires a reviewed module registry change, environment
contract, tests, and source-map outputs.

## CI Architecture

The v4.6.0 GitHub Actions workflow has separate jobs:

- `python-tests`
- `method-asset-schema`
- `cli-smoke-bulk`
- `cli-smoke-graph-dry-run`
- `r-method-smoke-optional`
- `security-light`

The graph dry-run job verifies that code-library modules can be selected,
planned, run in dry-run mode, evaluated, and synthesized into evidence reports.

## AI Harness Boundary

The model-facing harness can route method-asset commands, but execution still
requires paper id, run id, an existing design, and explicit approval. The
harness reports `needs_input` instead of executing when those conditions are
missing.

## Current Module Coverage

v4.6.0 exposes method assets across:

- single-cell RNA-seq
- bulk RNA-seq
- spatial transcriptomics
- cell-cell communication adapters
- evidence synthesis

`doctor --json` reports registry counts, invalid modules, and environment
registry availability so configuration drift is visible before execution.

