---
name: figure_planning
description: Scientific figure planning — design Figure 1-6, assign panels, identify missing analyses. 论文图表规划。触发词：figure plan, figure design, panel, 图表规划.
version: "1.0"
paper_loop_stages: "6"
agent: figure_planner
type: skill
---

# Figure Planning Skill

Orchestrates Stage 6 (`figure_planning`) of the paper loop. Designs figure architecture and exports machine-readable specs consumed by `analysis_executor` (Stage 7).

## Standard Figure Architecture
- Figure 1: Study overview + data characteristics
- Figure 2: Molecular landscape
- Figure 3: Differential analysis key findings
- Figure 4: Pathway and functional analysis
- Figure 5: Mechanism and interactions
- Figure 6: Validation and clinical associations

## Output
- `figure_specs.yaml` — Machine-readable specs (consumed by analysis_executor)
- `figure_plan.md` — Human-readable plan
- `color_palette.yaml` — WCAG-AA verified color definitions
- `missing_figures_checklist.md` — Analysis gaps

## Integration
See `figure_planner.md` for full agent specification. See `paper_loop.md` for stage sequencing.
