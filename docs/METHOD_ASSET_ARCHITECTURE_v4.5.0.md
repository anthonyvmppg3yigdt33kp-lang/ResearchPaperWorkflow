# Method-Asset Architecture v4.5.0

V4.5 changes the analysis layer from a single adapter model into a method-asset
orchestration model.

## Objects

| Object | File Or Module | Responsibility |
|---|---|---|
| DataRegistry | `paper_workflow.bioinformatics.data_registry` | Read paper-scoped data inventory without loading raw matrices. |
| EnvironmentRegistry | `paper_workflow.bioinformatics.environment_registry` | Resolve declared runners and environment metadata. |
| ModuleRegistry | `paper_workflow.bioinformatics.module_registry` | Query method assets by modality, step, language, and tags. |
| MethodSelector | `paper_workflow.bioinformatics.module_selector` | Score modules using biological fit, data fit, environment status, code maturity, figure value, reviewer risk, and evidence gain. |
| AnalysisGraph | `paper_workflow.bioinformatics.analysis_graph` | Store the run-scoped method DAG. |
| AnalysisGraphExecutor | `paper_workflow.bioinformatics.analysis_graph_executor` | Execute approved graph nodes and write manifests/source maps. |

## Execution Boundary

The executor can run declared modules, but it cannot mark a workflow stage
complete by itself. Completion still flows through:

```text
WorkflowAPI -> PaperLoopEngine -> verify_stage -> passport / ledgers / stage_results
```

This prevents a successful script from becoming an unsupported manuscript claim.

## Registry Boundary

`code_library/plugin_registry.yaml` remains as a legacy file inventory. It is not
the planning truth source. New method assets must be represented in
`code_library/module_registry.yaml` with:

- input/output schema;
- environment profile;
- reviewer value;
- reviewer risk;
- claim boundary;
- figure/table outputs;
- validation status;
- method maturity;
- execution contract when executable.

## Graph Boundary

`analysis_graph.yaml` is the approved execution contract. A node must declare:

- `node_id`;
- `module_id`;
- dependencies;
- inputs;
- parameters;
- expected outputs.

Each executed node writes:

- `parameters.yaml`;
- `node_manifest.yaml`;
- stdout/stderr logs;
- session information when applicable;
- node-scoped output files.

The run writes:

- `run_manifest.yaml`;
- `outputs_manifest.yaml`;
- `figure_source_map.yaml`;
- `table_source_map.yaml`;
- `evaluation_report.yaml` when evaluated.

## Feedback Boundary

Run feedback should update method assets only through reviewed registry changes.
Do not silently mutate module contracts based on one exploratory run. Record
candidate improvements in docs or a future registry update proposal, then test
them with fixtures.
