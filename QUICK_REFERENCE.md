# Quick Reference v5.1

## Start From A Scientific Question

```bash
paper-workflow research start --intent intents/examples/pbmc3k_t_subcluster_intent.yaml
paper-workflow research status --intent intents/examples/pbmc3k_t_subcluster_intent.yaml
```

Review `scientific_assessment.yaml`, `strategy_simulation.yaml`, `FIGURE_PLAN.md`, and `RESEARCH_DASHBOARD.md`. No biological analysis runs at this step.

## Execute An Approved Intent

```bash
paper-workflow research analyze \
  --intent intents/examples/pbmc3k_t_subcluster_intent.yaml \
  --approved \
  --execute
```

The command may still return `blocked` when data, environment, module, or QA gates fail.

## Expert TargetTask Control

```bash
paper-workflow target validate --target targets/examples/pbmc3k_t_subcluster_v5.yaml
paper-workflow target plan --target targets/examples/pbmc3k_t_subcluster_v5.yaml
paper-workflow target run --target targets/examples/pbmc3k_t_subcluster_v5.yaml
paper-workflow target evaluate --target targets/examples/pbmc3k_t_subcluster_v5.yaml
paper-workflow target package --target targets/examples/pbmc3k_t_subcluster_v5.yaml
```

## Continue The Paper Lifecycle

Use the 20-stage PaperLoop only after the analysis evidence is mapped into the project truth layer. Continue one bounded stage per turn and stop at checkpoints, missing inputs, failed gates, or stale artifacts.

## Current References

- `README.md`
- `USER_GUIDE.md`
- `ARCHITECTURE.md`
- `AGENTS.md`
- `AGENT_ROLES.md`
- `workflow_contract.yaml`
- `docs/V5_1_RESEARCHER_EXPERIENCE_TUNING_PLAN.md`
- `docs/V5_1_ACCEPTANCE_MATRIX.md`
