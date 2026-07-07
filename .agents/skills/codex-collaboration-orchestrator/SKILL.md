---
name: codex-collaboration-orchestrator
description: Use this skill whenever the user asks to improve Codex collaboration, turn fuzzy goals into concrete tasks, coordinate long-running research workflows, design human-agent operating modes, route work across skills/MCP/subagents, audit project state, or make Codex interactions more evidence-bound and efficient.
---

# Codex Collaboration Orchestrator

Use this skill to convert broad, ambiguous, or multi-stage user goals into a
clear human-Codex collaboration loop.

## First Move

Identify and state:

- canonical root;
- active mode;
- allowed inputs;
- forbidden actions;
- expected output path;
- evidence standard;
- whether human confirmation is required.

If any item is missing, infer conservatively from local routing files and say
which assumptions are being used.

## Modes

Choose one:

- `exploration_mode`: read-only status, evidence location, project routing.
- `analysis_design_mode`: design analysis, manuscript plan, or implementation blueprint before execution.
- `execution_mode`: approved bounded code/file action.
- `closeout_audit_mode`: final gate, claim-source audit, submission readiness.
- `ppt_briefing_mode`: slide/progress briefing from brief and source maps.
- `retrospective_mode`: after repeated friction, convert the lesson into a durable rule, skill, contract, or prompt macro.

## Minimal Read Order

Read only what is needed:

1. `AGENTS.md`
2. `brief/PROJECT_BRIEF.yaml` if present
3. `results/current_run.yaml` if present
4. `docs/CODEX_COLLABORATION_SYSTEM.md` for collaboration design work
5. named files from the user

For ResearchPaperWorkflow papers, also read `project_passport.yaml` before
making stage-completion claims.

## Intent Packet

When the user gives a fuzzy request, produce this packet before acting:

```text
Mode:
Canonical root:
Goal:
Allowed inputs:
Forbidden actions:
Output path:
Evidence standard:
Human checkpoint:
Closeout:
```

For exploratory design tasks, offer 2-3 concrete task options ranked by impact,
risk, and required evidence.

## Routing Rules

### Skills

Use repository skills for repeatable workflows:

- `workflow-light-mode` for quick status;
- `bioinformatics-analysis-design` before analysis;
- `result-run-management` before creating outputs;
- `research-ppt-briefing` for slides and progress reports;
- `codex-self-audit` for final self-check.

Use domain skills only after the task's data type is clear.

### MCP

Use MCP when live or authorized external data is required:

- PubMed for citation metadata;
- node_repl/browser/chrome for web or UI workflows;
- GitHub tools for repo/PR/release tasks;
- fast-context if available for semantic code search.

If a requested MCP is unavailable, state that and use the next-best local path.

### Subagents

Use subagents only when explicitly requested or when the user asks for parallel
agent work. Good splits:

- one explorer per independent project root;
- one reviewer per risk class;
- one worker per disjoint write set.

The main agent keeps the decision ledger and final closeout.

## Evidence Standards

Separate:

- confirmed fact;
- local file evidence;
- memory-derived routing clue;
- assumption;
- design decision;
- unresolved blocker.

For scientific work, always preserve:

- statistical unit;
- source file;
- method/parameter evidence;
- claim wording boundary;
- whether workflow stage truth changed.

## Closeout

End substantive work with:

```text
Mode used:
Files read:
Files changed:
Commands run:
Checks run:
Current truth source:
Risks:
Next safe action:
Ratchet improvement:
```

Do not mark a broad goal complete unless every explicit requirement has current
evidence.
