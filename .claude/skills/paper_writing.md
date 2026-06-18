---
name: paper_writing
description: Scientific manuscript writing — IMRAD structure, figure integration, LaTeX assembly, submission preparation. 论文撰写。触发词：论文, manuscript, writing, IMRAD, 投稿.
version: "1.0"
paper_loop_stages: "9, 10, 11, 12, 13, 16, 18"
agent: report_writer
type: skill
---

# Paper Writing Skill

Orchestrates Stages 9-13, 16, and 18 of the paper loop. Handles all IMRAD drafting, manuscript assembly, revision application, and final export.

## IMRAD Structure
- **Title & Abstract** — Research question + main findings + significance
- **Introduction** — Background → knowledge gap → objective → hypothesis
- **Methods** — Data + analysis pipeline + statistics (reproducible)
- **Results** — Findings + figures/tables (objective, no interpretation)
- **Discussion** — Main findings → literature comparison → limitations → future

## Writing Standards
- Objective: "showed/demonstrated" — not "interesting/remarkable"
- Quantitative: exact p-values, effect sizes, confidence intervals
- Humble: no "first/novel" without extraordinary evidence
- Limitations: mandatory in Discussion
- No bullet points in body text

## Integration
See `report_writer.md` for full agent specification. See `paper_loop.md` for stage sequencing and checkpoint rules. See `paper_writing/SKILL.md` for the comprehensive 10-stage pipeline integration guide.
