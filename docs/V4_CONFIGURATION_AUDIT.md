# V4.3 Configuration Audit

The maintained configuration truth source is the combination of:

- `workflow_contract.yaml`
- `config/default_config.yaml`
- `src/paper_workflow/engine/loop_engine.py`
- `src/paper_workflow/engine/agent_dispatcher.py`
- `src/paper_workflow/api.py`

The current audit question is not whether the old scaffold is documented. The
current question is whether every stage and route agrees across contract,
config, engine, dispatcher, agent routing, quality gates, and AI harness
commands.

## Current Expected Invariants

- The contract and config define the same 20 stage ids.
- Every configured stage exists in the engine.
- Every configured stage has a dispatcher handler.
- Every stage agent exists in `agent_routing.agents`.
- Every referenced quality gate has a definition.
- Required outputs are also declared as produced artifacts.
- AI harness scenario routes reference real stages and supported intents.
- `gate_rules` is not used as the primary current schema; use
  `quality_gates` plus `transition_policy`.

## Recommended Maintainer Audit

Use the current contract validator:

```bash
python -m paper_workflow.cli validate-contract --strict
```

Then run a concrete project validator:

```bash
python -m paper_workflow.cli validate-workflow --paper <paper_id> --strict
```

## Related Current Docs

- `ARCHITECTURE.md`
- `USER_GUIDE.md`
- `docs/OPERATION_GUIDE_ZH.md`
- `docs/NEXT_GEN_V4_TRUTH_LAYER.md`
- `docs/NEXT_GEN_COMPLETION_AUDIT.md`
