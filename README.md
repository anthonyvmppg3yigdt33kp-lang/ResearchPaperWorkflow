# Research Paper Workflow Framework v3.0

**A general-purpose, agent-driven research paper workflow system for bioinformatics and clinical research — upgraded to evidence-centric medical evidence generation.**

[![Python 3.9+](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/Tests-5/5%20Pass-brightgreen.svg)](tests/)
[![Version](https://img.shields.io/badge/Version-3.0.0-orange.svg)]()

---

## What It Does

This framework transforms the research paper writing process from ad-hoc scripting and manual coordination into a **deterministic, auditable, multi-agent pipeline** with medical evidence quality assurance:

- **4-layer architecture**: Strategy → Decision → Execution → Supervision
- **19-stage paper pipeline**: Including new Statistical Analysis Plan (SAP) pre-specification stage
- **7-framework skills + 28 external skills**: Covering every research phase via the skill registry
- **18 domain-specific agents**: With clear responsibility boundaries (6 new medical agents in v3.0)
- **1 collaborative team** (`paper_writing_team`): For full-cycle manuscript production
- **Passport system**: 5-ledger hash-based artifact tracking, claim binding, and stale detection
- **41 integrity gates**: Automated quality enforcement (17 CRITICAL, 21 HIGH, 3 MEDIUM)
  - Including clinical design, data bias, statistics/model, single-cell/spatial omics, and AI/ML categories
- **Evidence Graph**: Full claim→statistics→artifact→code→parameter traceability
- **CLI surface**: 10 commands for full pipeline control

## Design Philosophy

> **Main thread plans & integrates. Subagents explore, review, and execute in parallel. Skills provide reusable workflows. The loop engine manages state and iteration.**

This is NOT a "smarter chatbot"—it's a **project execution system** that reads files, runs code, spawns parallel subagents, and enforces scientific quality gates.

## Architecture

```
┌──────────────────────────────────────────────────────────┐
│  STRATEGY LAYER                                          │
│  Topic → Journal → Feasibility → Hypotheses               │
├──────────────────────────────────────────────────────────┤
│  DECISION LAYER                                          │
│  Skills Dispatcher + MCP Router + Paper Loop Engine       │
├──────────────────────────────────────────────────────────┤
│  EXECUTION LAYER                                         │
│  Pipeline Orchestrator + Quality Gates + CLI              │
├──────────────────────────────────────────────────────────┤
│  SUPERVISION LAYER                                       │
│  Passport + Provenance + Integrity + Stale Detection      │
└──────────────────────────────────────────────────────────┘
```

## 📖 Documentation

- **[USER_GUIDE.md](USER_GUIDE.md)** — 完整操作指南（从零到投稿）
- **[ARCHITECTURE.md](ARCHITECTURE.md)** — 四层系统架构
- **[QUICK_REFERENCE.md](QUICK_REFERENCE.md)** — 一页速查卡

## Quick Start

```bash
# Clone
git clone https://github.com/anthonyvmppg3yigdt33kp-lang/ResearchPaperWorkflow.git
cd ResearchPaperWorkflow

# Install
pip install -e .

# Create your first paper project
python -m paper_workflow.cli create-project \
  --idea "Your research idea" \
  --field "your field, keywords" \
  --journal "Genome Biology"

# Check status
python -m paper_workflow.cli status --paper <paper_id>

# Run pipeline
python -m paper_workflow.cli run-pipeline --paper <paper_id>

# Run tests
python tests/test_all.py
```

## Usage Patterns

### Pattern 1: New Paper from Scratch
```
create-project → search-literature → research-plan → data-audit
→ figure-planning → run-analysis → verify-methods
→ write-methods → write-results → write-introduction → write-discussion
→ assemble-manuscript → integrity-check → internal-review
→ apply-revision → re-review → quality-check → finalize
```

### Pattern 2: From Existing Results
```
create-project → record-artifacts → figure-planning
→ write-results → ... → finalize
```

### Pattern 3: Revision Cycle
```
diagnose-gate-failures → generate-revision-plan
→ apply-revision → re-review → quality-check
```

## Key Features

### Loop Engine
- **observe → decide → run → verify → record → mark_stale → diagnose → repeat**
- 18 pipeline stages with dependency tracking
- Automatic stale detection when upstream artifacts change
- Human checkpoints at critical decision points

### Passport System
- `project_passport.yaml` — Project identity and metadata
- `artifact_ledger.jsonl` — Append-only artifact hash log
- `checkpoint_ledger.jsonl` — User-approved checkpoints
- `integrity_ledger.jsonl` — Integrity gate events

### Integrity Gates (16 rules)
| Severity | Rules |
|----------|-------|
| **CRITICAL** | BibTeX existence, citation traceability, Results no-citations, claim-artifact binding, figure references |
| **HIGH** | Data availability, code availability, no local paths, parameters complete, limitations discussed, no overinterpretation, statistics reported, pseudoreplication check |
| **MEDIUM** | Section length minimum, no bullets in prose, figure count, journal format |

### Agent System (10 agents)
`research_strategist` · `literature_reviewer` · `data_auditor` · `figure_planner` · `analysis_executor` · `pipeline_engineer` · `statistician` · `report_writer` · `integrity_checker` · `team_orchestrator`

### Framework Skills (5 skills)
`topic_research` · `paper_loop` · `figure_planning` · `paper_writing` · `revision_routing`

### External Skills (28 skills, see `.claude/SKILL_REGISTRY.md`)
Covering: research · writing · polishing · figures · citations · review · data compliance · detection · presentation · orchestration · domain analysis · meta

## Project Structure

```
ResearchPaperWorkflow/
├── src/paper_workflow/          # Core Python package
│   ├── strategy/                # Strategy layer (topic, journal, feasibility, hypothesis)
│   ├── engine/                  # Paper loop engine
│   ├── supervision/             # Passport, integrity gates
│   ├── cli/                     # CLI surface
│   └── workflow.py              # Unified workflow orchestrator
├── .claude/                     # Agent/skill/team definitions
│   ├── SKILL_REGISTRY.md        # 28-skill mapping with trigger words
│   ├── skills/ (5) + agents/ (10) + teams/ (1)
├── config/                      # Configuration files
│   ├── default_config.yaml      # Pipeline configuration
│   ├── journal_database.yaml    # Journal profiles
│   └── templates/               # Paper section templates
├── code_library/                # Reusable analysis code
│   ├── modules/                 # Full analysis modules
│   ├── patterns/                # QC, clustering patterns
│   ├── snippets/                # I/O, logging, config utilities
│   └── solutions/               # Common problem solutions
├── docs/                        # Documentation
├── tests/                       # Integration tests
├── examples/                    # Example project
└── papers/                      # Generated paper projects (gitignored)
```

## Supported Paper Types

| Type | Description | Typical Pipeline |
|------|-------------|-----------------|
| `original_research` | Primary research article | Full 18-stage pipeline |
| `methods` | Methods/tool paper | Emphasizes verification + benchmarking |
| `review` | Literature review | Emphasizes literature search + synthesis |
| `clinical_research` | Clinical/translational study | Adds ethics + clinical statistics gates |
| `data_resource` | Data/resource descriptor | Emphasizes data audit + availability |
| `brief_communication` | Short report | Condensed pipeline, stricter limits |

## Supported Research Domains

The framework is domain-agnostic but pre-configured for:
- **Bioinformatics & Computational Biology**
- **Spatial Transcriptomics & Single-Cell Genomics**
- **Clinical & Translational Research**
- **Multi-Omics Integration**
- **Machine Learning in Biomedicine**

Configuration is fully externalized — adapt to any research domain by modifying `config/default_config.yaml` and `config/journal_database.yaml`.

## Integration with AI Assistants

This framework is designed to work with AI coding assistants (Claude Code, Codex, etc.):

1. **AGENTS.md**: Assistant reads this on startup — defines project rules
2. **Skills**: Assistant invokes skills for specialized tasks
3. **MCP Tools**: Connects to PubMed, Consensus, Context7, etc.
4. **Subagents**: Assistant spawns specialized subagents for parallel work

## License

MIT License — See [LICENSE](LICENSE)

## Citation

If you use this framework in your research, please cite:
```
@software{research_paper_workflow_2026,
  title = {Research Paper Workflow Framework},
  year = {2026},
  url = {https://github.com/anthonyvmppg3yigdt33kp-lang/ResearchPaperWorkflow}
}
```

---

*Built on the loop-engineering principles of Draftpaper_loop and the three-layer architecture pattern.*
