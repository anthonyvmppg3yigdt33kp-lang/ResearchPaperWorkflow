# V5 TargetTask Design

TargetTask is the v5 unit of executable research work. It replaces ambiguous "run some workflow" requests with a contract that states data, environment, modules, quality gates, claim boundary, and outputs.

## Schema

See `config/target_task.schema.yaml`.

Required top-level fields:

- `schema_version`
- `target_id`
- `title`
- `mode`
- `evidence_grade`
- `claim_boundary`
- `data`
- `environment`
- `analysis_goal`
- `workflow`
- `quality_gates`
- `outputs`

`target_id` must match:

```text
<name>_<YYYYMMDD>_v<N>
```

## Commands

```bash
paper-workflow target validate --target targets/examples/pbmc3k_t_subcluster_v5.yaml
paper-workflow target plan --target targets/examples/pbmc3k_t_subcluster_v5.yaml
paper-workflow target run --target targets/examples/pbmc3k_t_subcluster_v5.yaml
paper-workflow target evaluate --target targets/examples/pbmc3k_t_subcluster_v5.yaml
paper-workflow target package --target targets/examples/pbmc3k_t_subcluster_v5.yaml
```

`target run --approved --execute` is the real execution path. Without `--execute`, graph and package dry-run artifacts are produced for validation.

## Failure Behavior

TargetTask validation fails if claim boundary, required envs, workflow steps, or fail-closed gates are missing. Real execution blocks if runtime packages or data are unavailable. Package generation records incomplete evidence but does not generate conclusion paragraphs when final status is not `pass`.
