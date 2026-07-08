# ResearchPaperWorkflow v4.5.0 Release Notes

Published: 2026-07-08

## Summary

v4.5.0 upgrades ResearchPaperWorkflow from bounded single-flow analysis
execution toward capability-aware method-asset orchestration. The code library
now has a canonical module registry, declared environments, graph planning, and
approved graph execution with node manifests and source maps.

## Added

- `paper_workflow.bioinformatics.*` package:
  - data registry;
  - environment registry;
  - module registry;
  - method selector;
  - analysis graph;
  - analysis graph executor.
- `code_library/module_registry.yaml` as the canonical method-asset registry.
- `code_library/environment_registry.yaml` for runner/package declarations.
- Official Seurat PBMC3K tutorial wrapper:
  `code_library/modules/single_cell/seurat_pbmc3k_basic/`.
- CLI entries:
  - `list-modules`;
  - `inspect-module`;
  - `list-capabilities`;
  - `plan-analysis --from-code-library`.
- New contracts:
  - `config/data_governance_contract.yaml`;
  - `config/environment_contract.yaml`;
  - `config/module_registry_schema.yaml`;
  - `config/analysis_graph_schema.yaml`.
- Tests for module registry, method selection, analysis graph planning, graph
  dry-run execution, and capability CLI.

## Changed

- `run-analysis` now detects `analysis_graph.yaml` / `analysis_graph` designs
  and routes them through `AnalysisGraphExecutor`.
- `ResultRunManager.write_analysis_design()` can write
  `analysis_graph.yaml` and `method_selection_report.md` from the code library.
- `AgentDispatcher._discover_code_modules()` now prefers method assets from
  `module_registry.yaml` and falls back to file scanning only when no registry
  exists.
- `doctor` reports method-asset registry and environment registry health.
- Version metadata updated to `4.5.0`.

## Validation

The v4.5.0 validation path used the official Seurat PBMC3K tutorial data from
the Seurat tutorial page and executed the local Seurat method asset end to end:

- input cells: 2700;
- retained cells after QC: 2638;
- clusters: 9;
- generated outputs: QC metrics, retention table, cluster counts, UMAP,
  marker feature plots, RDS object, sessionInfo, source maps, run manifest, and
  evaluation report.

PBMC3K remains a tutorial fixture. These results validate workflow wiring and
do not constitute project-specific biological evidence.
