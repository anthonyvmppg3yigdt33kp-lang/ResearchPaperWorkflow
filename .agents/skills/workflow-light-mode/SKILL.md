# workflow-light-mode

Use this skill when the user asks for project status, workflow continuation,
or a quick orientation and does not explicitly request a full validation pass.

## Minimal Inputs

- `AGENTS.md`
- `brief/PROJECT_BRIEF.yaml` if present
- `results/current_run.yaml` if present
- `papers/<paper_id>/project_passport.yaml` for ResearchPaperWorkflow papers
- named files in the user request

## Do Not

- Do not run `validate-workflow --strict`.
- Do not run data analysis, package installation, or download commands.
- Do not enumerate raw matrices or large result folders.
- Do not treat `template`, `pending_harness`, `needs_input`, or `stale` as completed.

## Output

Return a short status with:

- paper/project id;
- truth source read;
- current state;
- blockers;
- next safe action;
- whether user approval is needed.
