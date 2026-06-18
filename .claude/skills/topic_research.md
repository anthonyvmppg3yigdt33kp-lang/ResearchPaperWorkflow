---
name: topic_research
description: Research topic selection, literature gap analysis, hypothesis generation, journal targeting, feasibility assessment. 选题调研。触发词：选题, topic, hypothesis, journal, feasibility, 研究设计.
version: "1.0"
paper_loop_stages: "1, 2, 4"
agent: research_strategist
type: skill
---

# Topic Research Skill

Orchestrates Stages 1, 2, and 4 of the paper loop. Delegates Stage 3 (literature search) to `literature_reviewer`.

## Pipeline Position
Stage 1 (`select_topic`) → Stage 2 (`target_journal`) || Stage 3 (`literature_search`) → Stage 4 (`formulate_hypotheses`)

## Integration
See `research_strategist.md` for full agent specification. See `paper_loop.md` for stage sequencing and checkpoint rules.

## Quick Start
```python
from paper_workflow.strategy import ResearchStrategyManager
manager = ResearchStrategyManager()
strategy = manager.create_strategy(idea="...", field="...", target_journal="...")
```
