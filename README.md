# Research Paper Workflow Framework v4.0

Agent-driven research paper workflow for bioinformatics, clinical research, and reproducible manuscript production.

[![Python 3.9+](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/Tests-42%20passing-brightgreen.svg)](tests/)
[![Version](https://img.shields.io/badge/Version-4.0.0-orange.svg)]()

## V4 Highlights

- 20-stage paper loop, including `design_analysis_plan` and the new `aigc_humanizer_review` stage.
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
python -m paper_workflow.cli.main install-skills

python -m paper_workflow.cli.main create-project \
  --idea "Your research idea" \
  --field "single-cell, spatial transcriptomics, disease" \
  --journal "Genome Biology"

python -m paper_workflow.cli.main list-papers
python -m paper_workflow.cli.main status --paper <paper_id>
python -m paper_workflow.cli.main run-pipeline --paper <paper_id>
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
python -m paper_workflow.cli.main run-aigc-humanizer --paper <paper_id>
```

## Skill Installation

V4 ships a skill manifest at `config/required_skills.yaml`. During install or CLI startup, the workflow compares bundled skills with local roots:

- `~/.codex/skills`
- `~/.agents/skills`
- `~/.claude/skills`

Missing bundled skills are copied to `~/.codex/skills/<skill>/SKILL.md`.

```bash
python -m paper_workflow.cli.main install-skills --check-only
python -m paper_workflow.cli.main install-skills
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

- [V4 installation and usage guide](docs/V4_INSTALLATION_AND_USAGE_GUIDE.md)
- [V4 configuration audit](docs/V4_CONFIGURATION_AUDIT.md)
- [Architecture](ARCHITECTURE.md)
- [User guide](USER_GUIDE.md)

## Verification

```bash
python -m pytest -q
```

Current V4 verification: `42 passed`.

## License

MIT License. See [LICENSE](LICENSE).
