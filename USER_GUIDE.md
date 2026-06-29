# ResearchPaperWorkflow User Guide v4.3

This guide describes how to use ResearchPaperWorkflow v4.3 through Claude,
Codex, or another tool-using AI model. It intentionally avoids asking ordinary
research users to run Python commands. The model operates the workflow tools;
the user describes the research need, supplies evidence, and makes scientific
decisions at checkpoints.

For the full architecture, see `ARCHITECTURE.md`. For Chinese prompt patterns,
see `docs/OPERATION_GUIDE_ZH.md`.

## What The Workflow Is

ResearchPaperWorkflow is not a free-form manuscript-writing prompt. It is a
stateful research workflow kernel for producing auditable biomedical and
bioinformatics manuscripts.

It helps a researcher move from:

```text
rough idea -> journal-aware question -> literature substrate -> hypotheses
-> statistical analysis plan -> data audit -> analysis manifest -> figure plan
-> manuscript sections -> AIGC hygiene review -> integrity check
-> internal review -> revision -> final package
```

The system's promise is not "the AI writes everything automatically." The
promise is:

```text
if a stage says completed, there are real artifacts and real verification records behind it
```

## Roles

| Role | Responsibility |
|---|---|
| Human researcher | Sets the scientific aim, supplies data and references, approves checkpoints, rejects overclaims, decides submission readiness. |
| Claude or Codex | Interprets natural-language requests, calls the workflow harness, reports state, asks for missing inputs, and routes agent work. |
| Workflow engine | Chooses the next safe stage, verifies required outputs, enforces quality gates, tracks artifacts, and resumes from saved state. |
| Agent cluster | Produces or audits stage-specific artifacts through research, literature, data, figure, analysis, writing, review, and integrity roles. |

## The Right Way To Talk To The Workflow

Use natural-language requests that state the current project state, the desired
outcome, available materials, constraints, and what kind of decision you want
the model to make.

Good request shape:

```text
I am starting a new clinical bioinformatics paper. The disease is clear cell
renal cell carcinoma, and I want to study the relationship with diabetes using
single-cell and spatial transcriptomics. Target journal: Genome Biology. Please
create the workflow project, stop after the first checkpoint, and tell me what
scientific decisions I need to approve.
```

Better than:

```text
Write me a paper.
```

The workflow performs best when you include:

- research field and disease context;
- target journal or journal family;
- available data, accessions, or file locations;
- whether the project is new or already partially complete;
- what you want next: planning, data audit, analysis, writing, review, or finalization;
- whether the model should stop after one stage or continue until a checkpoint.

## Common User Scenarios

### 1. New Project, Only A Research Idea

Use this when you have a broad topic but no structured paper project.

Prompt pattern:

```text
I have not started yet. I want to design a bioinformatics manuscript about
[disease] and [clinical factor] using [data type]. Please create the workflow
project, define the research question, suggest the target-journal fit, and stop
at the first human checkpoint before moving downstream.
```

Expected workflow behavior:

- create a paper project and `paper_id`;
- produce initial research question and hypotheses;
- record the project passport;
- stop for human review instead of pretending the whole paper is ready.

Human decision:

- approve, revise, or reject the direction;
- clarify disease, cohort, data type, comparison, and journal target.

### 2. Direction Exists, Literature And Feasibility Needed

Prompt pattern:

```text
I already have the topic direction. Please advance the workflow through journal
fit, literature search, and hypothesis formulation. If the literature step needs
manual references or an external search result, stop and list the missing
artifacts instead of filling placeholders.
```

Expected behavior:

- generate journal profile and feasibility rationale;
- request real BibTeX input when literature evidence is missing;
- avoid treating an empty bibliography as completed.

Human decision:

- provide seed references;
- approve or narrow the hypotheses;
- decide whether the project is feasible enough to proceed.

### 3. Topic Exists, Analysis Plan Needed

Prompt pattern:

```text
The topic and hypotheses are acceptable. Please design the statistical analysis
plan before any primary analysis. I need endpoints, covariates, statistical
unit, validation plan, missing-data policy, multiple-testing policy, and
patient-level independence checks.
```

Expected behavior:

- produce a frozen SAP;
- create a study design protocol;
- create a causal-assumption audit;
- fail closed if endpoint definition or patient-level independence is missing.

Human decision:

- approve the SAP before running analysis;
- fix pseudoreplication risk;
- confirm whether inference is patient, donor, sample, cell, spot, or image level.

### 4. Data Or Results Already Exist

Prompt pattern:

```text
I already have data and some analysis outputs. Please ingest the available
materials into the workflow, audit what is complete, identify missing required
outputs, and mark downstream stages stale if an upstream artifact changed.
Do not write manuscript sections until the run manifest and method verification
are valid.
```

Expected behavior:

- audit the data inventory;
- build or verify figure plan;
- check analysis output manifest;
- verify methods and reproducibility;
- block writing if the analysis truth layer is incomplete.

Human decision:

- supply missing data inventory fields;
- confirm which outputs are official;
- approve or revise figure plan.

### 5. Manuscript Writing From Verified Outputs

Prompt pattern:

```text
The data audit, SAP, analysis manifest, and figure plan are complete. Please
write the Methods and Results from verified artifacts only. Keep claims
conservative, avoid causal language unless supported, and stop after each
section checkpoint for my review.
```

Expected behavior:

- write sections only from verified upstream artifacts;
- record stage results;
- run stage quality gates;
- ask for checkpoint decisions where configured.

Human decision:

- confirm the scientific interpretation;
- reject unsupported biomarker or causal claims;
- provide missing figure legends or statistics.

### 6. Integrity, AIGC Hygiene, And Finalization

Prompt pattern:

```text
The manuscript draft is assembled. Please run AIGC hygiene review, integrity
checks, internal review, revision routing, and final package preparation. Report
every blocking gate and do not finalize until data availability, code
availability, citations, and claim-evidence binding are valid.
```

Expected behavior:

- generate AIGC hygiene report and conservative humanizer plan;
- run citation and claim-evidence checks;
- produce internal review and revision plan;
- prepare final package only after gates pass.

Human decision:

- approve the revised manuscript;
- confirm data and code availability wording;
- decide whether the package is submission-ready.

## Reading Status

When you ask "where are we?", the model should report:

- `paper_id`;
- current pipeline state;
- completed, blocked, stale, or failed stages;
- checkpoint blockers;
- missing required outputs;
- pending harness invocations;
- drifted artifacts;
- recommended next human action.

Do not accept a vague answer such as "the paper is done." Ask the model to show
which stage results and required outputs prove completion.

## What Completed Means

A completed stage must have:

- a `StageResult` file under `stage_results/`;
- `execution_mode: real`;
- all `required_outputs` present and non-empty;
- no missing critical or high quality gate result;
- checkpoint approval if the stage requires human review;
- no upstream drift that invalidates the output.

The following are not completed:

- placeholder templates;
- empty BibTeX or empty hypothesis files;
- pending external search or writing tasks;
- user chat approval with no checkpoint ledger entry;
- manually edited outputs that have not re-entered workflow validation.

## Pending Harness Work

Sometimes the workflow cannot complete a stage internally. Examples:

- real references must be supplied;
- a dataset inventory is missing;
- analysis outputs have not been generated yet;
- an external skill or human author must fill a required artifact.

In that case, the dispatcher writes a pending harness record. The model should
tell you:

- which stage is pending;
- which artifacts are required;
- where those artifacts should be placed;
- what quality standard they must meet;
- how the workflow will verify them afterward.

Supplying the artifact does not automatically complete the stage. The engine
must re-run or validate the stage so the truth layer can record completion.

## Human Checkpoints

Human checkpoints are the scientific control points of the pipeline. Treat them
as formal decisions.

Good checkpoint approval:

```text
I approve the SAP for this project. The statistical unit is patient-level; cell
level summaries are descriptive only. Primary endpoints and covariates are
acceptable. Continue to data audit.
```

Good checkpoint rejection:

```text
Do not approve this checkpoint. The hypothesis still overclaims causality and
the endpoint definition is incomplete. Revise the hypothesis and SAP before
continuing.
```

The model should record your decision in the checkpoint ledger, not only in the
chat transcript.

## Biomedical Safety Rules

For clinical and bioinformatics papers, keep these guardrails explicit:

- distinguish patient, donor, sample, cell, spot, and image-level inference;
- avoid treating cells or spots as independent patients;
- require SAP before primary analysis;
- keep exploratory findings separate from primary endpoints;
- avoid "biomarker", "diagnostic", "therapeutic", or "causal" claims unless
  the evidence chain supports them;
- require external or held-out validation when claiming generalizable models;
- cite only verified references;
- ensure data and code availability before finalization.

## Recommended Closeout From The Model

After each work session, ask for a concise closeout:

```text
Summarize the current paper_id, stages changed, new artifacts, gates passed or
failed, pending harness tasks, human decisions needed, and the next safest
workflow step.
```

This keeps the workflow resumable across Codex, Claude, and future sessions.
