# Method-Asset Architecture v4.8.0

v4.8.0 moves ResearchPaperWorkflow from a paper-workflow framework with method
asset orchestration toward a sustainable bioinformatics method asset library.
The main production chain is:

```text
external code source
-> retained source manifest
-> method_blocks.yaml
-> depersonalized adaptation scaffold
-> reviewed executable module
-> module_registry output_bindings
-> analysis graph artifact binding
-> run-scoped execution
-> bioinformatics QA and next-analysis plan
```

## Architecture

| Layer | Components | Responsibility |
|---|---|---|
| Source intake | `CodeSourceImporter`, `SourceParser`, `method_block_extractor.py` | Retain local/GitHub scripts, parse R/Python files, detect method calls, write `method_blocks.yaml`, and keep registry mutation disabled by default. |
| Depersonalization | `method_depersonalizer.py` | Detect disease labels, project labels, object names, and personal paths; convert them into parameterization and provenance-review plans. |
| Adaptation | `adapt-method-block`, `method_adapter.py` | Generate reviewed module scaffolds under `code_library/modules/external/<source_id>/<module>/` without changing `module_registry.yaml`; optionally write `registry_patch.yaml` after license approval. |
| Registry | `code_library/module_registry.yaml` | Declares executable modules, input schemas, output schemas, environments, reviewer risks, claim boundaries, and `output_bindings`. |
| Execution graph | `analysis_graph.py`, `analysis_graph_executor.py` | Builds DAG nodes, binds upstream artifacts such as `seurat_rds` and `ranked_gene_statistic`, resolves run-relative node paths, writes repository-relative report paths, and writes manifests/source maps under `results/runs/<run_id>/`. |
| Strategy | `StrategyEvaluator`, `MethodSelector`, `LiteratureMethodAdvisor` | Explains recommended and non-recommended methods, prerequisites, statistical unit, reviewer risk, claim boundary, and next-step plan. Optional evidence packets live at `research_plan/method_evidence_packet.yaml`. |
| QA | `BioinformaticsRunQualityRules`, `ResultRunManager.evaluate_run` | Writes `qc/bioinformatics_quality_report.yaml` and `qc/next_analysis_plan.yaml`; checks required tables, columns, FDR ranges, logFC presence, session info, source-map boundaries, path leakage, data-registry hash, and group/sample reports. |

## New Registered Method Assets

- `single_cell.seurat_findmarkers_group_de.v1`
  - Real execution: reads a Seurat RDS, parameterizes `group_column`,
    `ident_1`, `ident_2`, optional subset, assay, slot, and test settings.
  - Outputs: `tables/findmarkers_results.csv`,
    `tables/findmarkers_summary.csv`, `qc/group_size_sample_mapping.csv`,
    `figures/findmarkers_volcano.png`, `objects/findmarkers_parameters.rds`,
    `logs/sessionInfo.txt`, and source maps.
  - Boundary: cell-level marker/differential expression is exploratory unless
    biological replicate-aware inference is documented.

- `bulk_rnaseq.limma_voom_de_real.v1`
  - Real execution: reads count matrix plus sample metadata, validates sample
    alignment, runs edgeR normalization and limma-voom modeling.
  - Outputs: `tables/limma_voom_results.csv`, `qc/design_summary.csv`,
    `figures/limma_voom_volcano.png`, `objects/limma_voom_parameters.rds`,
    `logs/sessionInfo.txt`, and source maps.
  - Boundary: DE is association evidence and depends on valid sample-level
    design.

## Hard Boundaries

- `import-code-source` never mutates `module_registry.yaml`.
- External scripts are retained for review; disease names, project paths, and
  object names may appear in provenance, not reusable module logic.
- Dry-run and tutorial outputs are contract evidence only, not publication-grade
  biological evidence.
- Graph execution remains fail-closed on approval, data registry, environment,
  package, input binding, and source-map gates.
- `evaluate-run` can recommend next modules, but human review remains required
  before claims or registry promotion.

## Artifact Binding Contract

Modules may declare:

```yaml
output_bindings:
  seurat_rds: objects/seurat_qc.rds
  ranked_gene_statistic: tables/findmarkers_results.csv
```

When downstream required inputs match compatible bindings, generated
`analysis_graph.yaml` records:

```yaml
binding_source: upstream_output.<node_id>.<binding_name>
status: bound
value: nodes/<node_id>/<relative_output_path>
```

The executor resolves `nodes/...` paths relative to the active run directory, so
node-to-node artifact flow stays inside `results/runs/<run_id>/`.

Reportable run artifacts should avoid local personal paths. Operational
execution may still use local runners and working directories, but manifests,
source maps, QC summaries, and evaluation reports should use repository-relative
paths whenever the referenced file is inside the project root.
