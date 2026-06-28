# Research Paper Workflow Framework v4.0

Agent-driven research paper workflow for bioinformatics, clinical research, and reproducible manuscript production.

[![Python 3.9+](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/Tests-60%20passing-brightgreen.svg)](tests/)
[![Version](https://img.shields.io/badge/Version-4.1.0-orange.svg)]()

## V4 Highlights

- 20-stage paper loop, including `design_analysis_plan` and `aigc_humanizer_review`.
- Truth-layer contract in `workflow_contract.yaml`: completed means real outputs, non-empty artifacts, passable gates, and checkpoint state all agree.
- Unified `StageResult` and per-stage `stage_results/<stage>_result.json` records for audit and resume.
- Shared `WorkflowAPI` service layer used by CLI, Python callers, and non-dry-run E2E compatibility mode.
- Agent harness bridge for pending external skill work: pending invocations can be listed, verified, and completed only after required artifacts are real.
- 44 integrity gates across citation, clinical design, data bias, statistics, omics, AI/ML, AIGC text hygiene, and format checks.
- 13 routed agents, including the new `aigc_humanizer_reviewer`.
- Automatic local skill comparison and bundled-skill installer for Claude Code and Codex users.
- CLI command for standalone AIGC text hygiene review and conservative humanizer revision.
- Clean V4 installation and migration guide for bringing your own research topic, data, references, and drafts into the workflow.

## Quick Start

```bash
git clone https://github.com/anthonyvmppg3yigdt33kp-lang/ResearchPaperWorkflow.git
cd ResearchPaperWorkflow

python -m pip install -e .
python -m paper_workflow.cli install-skills

python -m paper_workflow.cli create-project \
  --idea "Your research idea" \
  --field "single-cell, spatial transcriptomics, disease" \
  --journal "Genome Biology"

python -m paper_workflow.cli list-papers
python -m paper_workflow.cli status --paper <paper_id>
python -m paper_workflow.cli run-pipeline --paper <paper_id> --stop-on-failure
```

Makefile shortcuts are also available:

```bash
make install
make init-paper IDEA="Your research idea" FIELD="your field" JOURNAL="Genome Biology"
make run PAPER=<paper_id>
```

## AIGC And Humanizer Review

The V4 paper loop runs `aigc_humanizer_review` after manuscript assembly and before the main integrity pass:

```text
assemble_manuscript -> aigc_humanizer_review -> integrity_check
```

It produces:

- `review/aigc_detection_report.md`
- `review/humanizer_revision_plan.yaml`
- `manuscript/manuscript_humanized.md`

Run it directly when you already have a draft:

```bash
python -m paper_workflow.cli run-aigc-humanizer --paper <paper_id>
```

`run-aigc-humanizer` is guarded by upstream state. It will not run before
`assemble_manuscript` is completed.

## Truth Layer And Harness

The canonical completion rule is fail-closed:

- `execution_mode` must be `real`.
- Required outputs from `workflow_contract.yaml` must exist and be non-empty.
- Configured critical/high quality gates must produce concrete pass results.
- Human-checkpoint stages require an approved checkpoint before downstream progress.
- `template`, `pending_harness`, and `needs_input` are not completed states.

External or human agent work is represented by files under
`workflow_state/pending_invocations/`:

```bash
python -m paper_workflow.cli list-harness-invocations --paper <paper_id>
python -m paper_workflow.cli complete-harness-invocation \
  --paper <paper_id> \
  --invocation literature_search \
  --strict
```

Completing a harness invocation verifies artifacts only. The stage still needs
to re-enter `run-pipeline` so `run_stage -> verify_stage -> stage_results` is
the only path to completed.

## Skill Installation

V4 ships a skill manifest at `config/required_skills.yaml`. During install or CLI startup, the workflow compares bundled skills with local roots:

- `~/.codex/skills`
- `~/.agents/skills`
- `~/.claude/skills`

Missing bundled skills are copied to `~/.codex/skills/<skill>/SKILL.md`.

```bash
python -m paper_workflow.cli install-skills --check-only
python -m paper_workflow.cli install-skills
```

Set `PAPER_WORKFLOW_SKILL_TARGET` to install into another root, or `PAPER_WORKFLOW_SKIP_SKILL_CHECK=1` to disable the startup check.

## Core CLI

```text
create-project
status
run-pipeline
checkpoint
run-integrity-gate
diagnose-gate-failures
detect-artifact-drift
sync-artifact-stale
validate-workflow
validate-contract
list-harness-invocations
complete-harness-invocation
list-papers
strategy
install-skills
run-aigc-humanizer
```

## Project Layout

```text
ResearchPaperWorkflow/
  src/paper_workflow/          Core Python package
  config/default_config.yaml   V4 pipeline, gates, agents, dispatcher rules
  config/required_skills.yaml  Skill comparison and installer manifest
  .claude/agents/              Claude/Codex agent specs
  .claude/skills/              Bundled workflow skills
  docs/                        Guides and audit notes
  tests/                       Integration and sync tests
  papers/                      Generated paper projects, ignored by git
```

## Documentation

- [Clinician and graduate student guide](docs/CLINICIAN_GRADUATE_USER_GUIDE_ZH.md)
- [Next-generation V4 truth-layer guide](docs/NEXT_GEN_V4_TRUTH_LAYER.md)
- [Next-generation completion audit](docs/NEXT_GEN_COMPLETION_AUDIT.md)
- [Release notes v4.1.0](docs/RELEASE_NOTES_v4.1.0.md)
- [V4 installation and usage guide](docs/V4_INSTALLATION_AND_USAGE_GUIDE.md) (historical; see next-generation guide first)
- [V4 configuration audit](docs/V4_CONFIGURATION_AUDIT.md)
- [Architecture](ARCHITECTURE.md) (historical)
- [User guide](USER_GUIDE.md) (historical)

## Verification

```bash
python -m pytest -q
python -m paper_workflow.cli validate-contract --strict
```

Current next-generation V4 verification: `60 passed`.

## License

MIT License. See [LICENSE](LICENSE).
