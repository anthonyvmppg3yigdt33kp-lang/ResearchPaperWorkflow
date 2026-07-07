# result-run-management

Use this skill when creating, reviewing, or cleaning result runs.

## Required Layout

```text
results/runs/<run_id>/
results/current_run.yaml
results/current/
```

Legacy result folders may remain in place until the user approves migration.
Create pointers first; move or delete only after explicit approval.

## Minimal Inputs

- `config/result_write_policy.yaml`
- existing `results/current_run.yaml`
- run manifest for the target run
- list of files to be produced or referenced

## Do Not

- Do not create timestamped sibling directories without a run manifest.
- Do not overwrite `current_run.yaml` without recording previous pointer.
- Do not delete duplicate runs during an audit-only or pointer-only pass.

## Output

Return:

- selected `run_id`;
- target output directory;
- manifest path;
- current pointer update;
- duplicate-risk note.
