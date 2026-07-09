# Method-Asset Architecture v4.7.0

v4.7.0 hardens the method-asset orchestra around inspectable source, strict DAG
binding, multilingual execution, and strategy-level method evaluation.

## Core Components

| Component | Files | Responsibility |
|---|---|---|
| Asset registry | `code_library/module_registry.yaml` | Declares method identity, source, inputs, outputs, environment, risk, maturity, and execution command. |
| Source catalog | `code_library/modules/MODULE_SOURCE_CATALOG.md` | Researcher-facing index of every module's purpose, primary script, delegated wrapper, functions, execution type, environment lock, and claim boundary. |
| Environment registry | `code_library/environment_registry.yaml`, `code_library/env_locks/*.lock.yaml` | Declares runners, package contracts, lock files, and reproducibility expectations. |
| Strategy evaluator | `src/paper_workflow/bioinformatics/strategy_evaluator.py` | Compares method families using question type, data context, prerequisites, sample-size risk, figure role, and reviewer value. |
| Graph contract | `AnalysisGraph`, `AnalysisGraphNode.inputs` | Stores node-level input bindings generated from module `input_schema.required`. |
| Graph executor | `AnalysisGraphExecutor` | Runs approved DAG nodes with Rscript, Python, shell, or Jupyter commands after approval, data, environment, package, and input-contract gates. |
| External intake | `CodeSourceImporter` | Imports local sources or clones GitHub repos, parses R/Python functions/imports/capabilities, and generates review-only module proposals. |
| Method audit | `audit-method-assets` | Fails structural gaps and reports maturity warnings without inflating dry-run assets into publication-grade executors. |

## Execution Boundary

Real execution remains fail-closed:

```text
approval granted
-> data registry pass
-> environment lock present
-> runner and packages available
-> node input contract bound
-> command executes inside results/runs/<run_id>/nodes/<node_id>/
-> node/run manifests and source maps written
```

Planning uses lighter environment checks so `list-capabilities` remains fast.
Package availability is enforced by `AnalysisGraphExecutor` during real
execution.

## Strategy Boundary

`MethodSelector` still scores modules, but v4.7 adds a strategy evaluator that
records explicit reasoning:

- pseudobulk DE is preferred for cell-type group contrasts when sample mapping
  and biological replicates exist;
- WGCNA is secondary for module-trait structure and is weak at low sample
  counts;
- spatial deconvolution requires spatial data plus a reviewed single-cell or
  marker reference;
- CellChat/NicheNet-style assets remain hypothesis-generating;
- QC/tutorial figures are prerequisites or workflow tests, not main mechanistic
  figures.

This is not a black-box statistical consultant. It is a structured, auditable
policy layer that prevents keyword scoring from hiding method prerequisites.

## Current Production Boundary

The following are structural guarantees in v4.7:

- every registered module has a catalog entry and sufficient description;
- bulk and pseudobulk R environments now have declared lock files;
- GraphExecutor supports Rscript, Python, shell, and Jupyter method assets;
- node inputs are bound from `input_schema` and block real execution if
  required inputs are unresolved;
- GitHub source intake can clone, parse, and generate proposals without
  auto-registering code;
- CI runs `audit-method-assets --strict` and mandatory R wrapper contract
  parsing/dry-runs.

The following remain intentionally guarded:

- most R modules are validated dry-run wrappers or adapter contracts, not
  final publication-grade executors;
- full Seurat/DESeq2 package-level end-to-end execution still requires a
  provisioned R environment and real data registry;
- evidence graph synthesis is claim-boundary and source-map aware, but not a
  full semantic theorem prover.
