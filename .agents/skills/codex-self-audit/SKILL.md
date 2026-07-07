# codex-self-audit

Use this skill to audit Codex usage, context load, project memory, workflow
state, result-run hygiene, and tool/skill availability.

## Minimal Inputs

- `AGENTS.md`
- `.agents/skills/*/SKILL.md`
- `config/*.yaml`
- project brief files
- `results/current_run.yaml`
- small ledgers/manifests only when needed

## Do Not

- Do not run full validation unless explicitly requested.
- Do not scan raw data directories or large matrices.
- Do not install tools or fix files during a read-only audit.

## Output

Return an evidence-bound report with:

- context hotspots;
- tool/MCP/skill diagnosis;
- workflow-state risks;
- result-folder duplication risks;
- concrete next-pass edits.
