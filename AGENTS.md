# AGENTS.md -- ResearchPaperWorkflow lightweight entry

This file is loaded at session start. Keep it short. Detailed agent maps,
quality gates, case studies, and long skill inventories are read on demand from
`docs/`, `config/`, `.claude/`, and `.agents/skills/`.

## Project Identity

ResearchPaperWorkflow is an auditable research-paper workflow for biomedical,
bioinformatics, and clinical manuscripts. The user is the final scientific
decision maker. Never invent data, statistics, cohorts, citations, clinical
facts, mechanisms, or approvals.

Current invariant:

```text
completed = real execution + verified outputs + concrete gate results + checkpoint consistency
```

## Operating Modes

Choose one mode before doing substantial work.

| Mode | Use When | Allowed Inputs | Forbidden Actions | User Approval |
|---|---|---|---|---|
| `exploration_mode` | Locate code, files, project state, or evidence. | `AGENTS.md`, `README.md`, small config files, file names, manifests, ledgers. | Editing, running analyses, creating result directories. | No, unless scope is unclear. |
| `analysis_design_mode` | Plan bioinformatics/statistical analyses before execution. | `brief/PROJECT_BRIEF.yaml`, `data/data_inventory.yaml`, `results/current_run.yaml`, prior manifests. | Running R/Python analysis, downloading data, installing packages. | Yes before execution. |
| `execution_mode` | Run an approved, bounded command or patch owned files. | Approved design, owned scripts, manifests, small configs. | Unapproved raw-data changes, ad hoc result folders, package installs. | Yes unless already explicit. |
| `closeout_audit_mode` | Submission readiness, integrity gates, final QA. | Passport, ledgers, manuscript, figure maps, citation records. | Treating exploratory outputs as completion. | Yes for full gates. |
| `ppt_briefing_mode` | Stage summary, slide deck, journal club, progress report. | `brief/PROJECT_BRIEF.yaml`, `brief/SLIDE_BRIEF.md`, `brief/FIGURE_STORYLINE.md`, `results/current_run.yaml`, `results/figure_source_map.yaml`. | Reading raw matrices by default, recomputing figures, broad audits. | No for read-only briefing. |

## Minimal Reading

Default read set:

- `AGENTS.md`
- `brief/PROJECT_BRIEF.yaml` if present
- `results/current_run.yaml` if present
- the specific files named by the user

Read on demand:

- `README.md`, `ARCHITECTURE.md`, `USER_GUIDE.md`, `docs/*.md`
- `docs/CODEX_COLLABORATION_SYSTEM.md` for human-Codex collaboration design,
  orchestration patterns, system-prompt proposals, and ratchet improvements
- `config/default_config.yaml`, `workflow_contract.yaml`
- `papers/<paper_id>/project_passport.yaml`
- ledgers and `stage_results/`
- `.claude/SKILL_REGISTRY.md`

Do not load long docs, all ledgers, all stage results, or entire result folders
unless the selected mode requires them.

## Hard Rules

- Do not modify raw data, final results, or user-authored drafts without
  explicit confirmation.
- Do not create a new result directory when updating an existing run would be
  more correct. Use `results/runs/<run_id>/`, `results/current_run.yaml`, and a
  `results/current` pointer.
- Every generated figure or table must have source data, script, method,
  statistical unit, and interpretation recorded in a source map or manifest.
- Distinguish observed result, statistical association, biological
  interpretation, mechanistic hypothesis, and experimentally validated
  conclusion.
- Do not treat cells, spots, features, images, or reads as independent patients
  when the correct unit is sample, donor, or patient.
- Methods text must match actual code, parameters, software versions, and run
  manifests.
- Do not treat `template`, `pending_harness`, or `needs_input` as completed.
- Run or recommend `validate-contract --strict` before production execution
  changes.
- Run or recommend `validate-workflow --strict` before submission readiness
  claims.
- Run full validation only in `closeout_audit_mode` or when explicitly asked.
- If `fast-context` is unavailable, say so and use `rg` plus direct reads.

## Skill Routing

Prefer repository skills under `.agents/skills/<skill>/SKILL.md` for Codex.
Legacy Claude skills under `.claude/skills/*.md` are reference material only
unless mirrored or explicitly requested.

High-value skills:

- `codex-collaboration-orchestrator`
- `workflow-light-mode`
- `bioinformatics-analysis-design`
- `single-cell-analysis`
- `spatial-transcriptomics-analysis`
- `multi-omics-analysis`
- `figure-storyline-planning`
- `research-ppt-briefing`
- `result-run-management`
- `codex-self-audit`

## Closeout Format

End substantive work with:

- mode used;
- files changed;
- commands run;
- tests or checks run;
- unresolved risks;
- next safe action.
