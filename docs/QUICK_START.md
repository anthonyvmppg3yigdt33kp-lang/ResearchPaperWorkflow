# Historical Note

This quick start predates the next-generation V4 truth layer. Use
`docs/NEXT_GEN_V4_TRUTH_LAYER.md` for the current 20-stage workflow,
`WorkflowAPI`, agent harness, and validation commands.

# Quick Start Guide — Research Paper Workflow Framework v1.0.0

This guide gets you from zero to a working paper pipeline in under 10 minutes.

---

## 1. Installation

**Requirements**: Python 3.9+, Git

```bash
# Clone the repository
git clone https://github.com/your-org/ResearchPaperWorkflow.git
cd ResearchPaperWorkflow

# Install in development mode (core dependencies only)
pip install -e .

# Optional: install with plotting dependencies (matplotlib, seaborn, pandas, numpy, scipy)
pip install -e ".[plotting]"

# Optional: install with all dependencies (plotting + scikit-learn, statsmodels)
pip install -e ".[full]"
```

**Verify installation:**

```bash
python -m paper_workflow.cli --help
```

Expected output shows 10 subcommands: `create-project`, `status`, `run-pipeline`, `checkpoint`, `run-integrity-gate`, `diagnose-gate-failures`, `detect-artifact-drift`, `sync-artifact-stale`, `list-papers`, `strategy`.

```bash
# Run the test suite (5 integration test suites, all should pass)
python tests/test_all.py
```

---

## 2. Creating Your First Paper Project

A paper project is a directory under `papers/` containing its own passport, configuration, and all generated artifacts.

### Using the CLI

```bash
python -m paper_workflow.cli create-project \
  --idea "Single-cell transcriptomics reveals immune cell infiltration patterns in kidney disease" \
  --field "single-cell, nephrology, immunology" \
  --journal "Genome Biology"
```

**What happens:**
1. A research strategy is generated (topic assessment, journal fit, hypotheses, feasibility report)
2. A paper directory is created under `papers/paper_<slug>_YYYYMMDD/`
3. A project passport (`project_passport.yaml`) is initialized
4. The pipeline state is set to `ready`

**Paper directory structure after creation:**

```
papers/paper_single_cell_transcriptomics_reveals_20260618/
├── project_passport.yaml        # Project identity, pipeline state, stage status
├── artifact_ledger.jsonl        # Append-only artifact hash log
├── checkpoint_ledger.jsonl      # User-approved checkpoint log
├── integrity_ledger.jsonl       # Integrity gate event log
├── strategy/
│   └── research_strategy.yaml   # Full research strategy
├── manuscript/                  # Will hold manuscript sections
├── references/                  # Will hold literature, citation library
├── results/                     # Will hold analysis outputs
├── figures/                     # Will hold generated figures
├── data/                        # Will hold data audit, inventory
├── review/                      # Will hold review reports
└── submission/                  # Will hold final submission package
```

### Using the Makefile

```bash
make init-paper IDEA="Your idea here" FIELD="bioinformatics" JOURNAL="Bioinformatics"
```

### Using Python API

```python
from paper_workflow.workflow import PaperWorkflow

wf = PaperWorkflow()
wf.initialize(
    idea="Your research idea",
    field="bioinformatics, transcriptomics",
    journal="Genome Biology",
    timeline_weeks=8,
)

print(f"Paper ID: {wf.paper_id}")
print(f"State: {wf.state.pipeline_state}")
```

---

## 3. Understanding Pipeline Status

### Viewing Status

```bash
python -m paper_workflow.cli status --paper <paper_id>
```

Example output:

```
============================================================
Paper: paper_single_cell_transcriptomics_20260618
State: clean
============================================================

Phase 1: Research & Planning
----------------------------------------
  [OK] create_project [CHECKPOINT]
  [   ] search_literature
  [   ] research_plan [CHECKPOINT]

Phase 2: Data & Methods
----------------------------------------
  [   ] data_audit
  [   ] figure_planning [CHECKPOINT]
  [   ] run_analysis
  [   ] verify_methods

Phase 3: Writing
----------------------------------------
  [   ] write_methods
  [   ] write_results
  [   ] write_introduction
  [   ] write_discussion

Phase 4: Assembly & Review
----------------------------------------
  [   ] assemble_manuscript [CHECKPOINT]
  [   ] integrity_check [CHECKPOINT]
  [   ] internal_review [CHECKPOINT]

Phase 5: Revision
----------------------------------------
  [   ] apply_revision
  [   ] re_review [CHECKPOINT]

Phase 6: Finalize
----------------------------------------
  [   ] quality_check
  [   ] finalize [CHECKPOINT]
============================================================
```

### Status Icons

| Icon | Meaning |
|------|---------|
| `[OK]` | Stage completed successfully |
| `[..]` | Stage currently running |
| `[FAIL]` | Stage failed (see `diagnose-gate-failures`) |
| `[STALE]` | Stage needs re-run (upstream artifact changed) |
| `[   ]` | Pending — not yet reached |
| `[BLOCK]` | Blocked by upstream failures or dependencies |
| `[SKIP]` | Skipped (not required for this paper type) |

### Pipeline States

| State | Meaning | Action |
|-------|---------|--------|
| `clean` | All stages in sync, no issues | Continue to next stage |
| `in_progress` | A stage is running | Wait for completion |
| `drift_detected` | Artifact hash mismatch detected | Run `sync-artifact-stale` |
| `stale_stages` | Downstream stages marked stale | Re-run stale stages |
| `gate_failure` | Integrity checks failed | Run `diagnose-gate-failures` |
| `blocked` | Cannot proceed | Resolve blocking issue |

### Listing All Projects

```bash
python -m paper_workflow.cli list-papers
# or
make list
```

---

## 4. Running the Pipeline

### Full Run (Automatic)

```bash
python -m paper_workflow.cli run-pipeline --paper <paper_id>
```

The pipeline runs stages sequentially in dependency order. It stops at human checkpoints (marked `[CHECKPOINT]`), waiting for your decision. Stages are marked with an icon showing their current status.

You can set `--stop-on-failure` to halt when a stage fails:

```bash
python -m paper_workflow.cli run-pipeline --paper <paper_id> --stop-on-failure
```

### Human Checkpoint Stages

These stages require explicit approval before the pipeline can continue:

1. **create_project** — Confirm the research direction, journal target, and timeline
2. **research_plan** — Approve the study design, hypotheses, and analysis plan
3. **figure_planning** — Confirm figure layout and analysis roadmap
4. **assemble_manuscript** — Review the assembled manuscript
5. **integrity_check** — Review integrity gate results before internal review
6. **internal_review** — Review the simulated peer review
7. **re_review** — Confirm revisions are satisfactory
8. **finalize** — Final approval before submission package generation

### Recording Checkpoint Decisions

```bash
python -m paper_workflow.cli checkpoint \
  --paper <paper_id> \
  --stage "research_plan" \
  --decision "approved" \
  --notes "Study design looks solid. Proceed with data audit."
```

Valid decisions: `approved`, `rejected`, `revision_needed`

### Running Integrity Gates

```bash
python -m paper_workflow.cli run-integrity-gate --paper <paper_id>
```

This runs all 16 integrity checks (5 CRITICAL, 8 HIGH, 3 MEDIUM) on the current manuscript. Critical failures block pipeline progress and must be resolved first.

**The 16 integrity gates:**

| Severity | Gates |
|----------|-------|
| **CRITICAL** | BibTeX existence, Citation traceability, Results no-citations, Claim-artifact binding, Figure references |
| **HIGH** | Data availability, Code availability, No local paths, Parameters complete, Limitations discussed, No overinterpretation, Statistics reported, Pseudoreplication check |
| **MEDIUM** | Section length minimum, No bullets in prose, Figure count |

### Detecting and Syncing Drift

When upstream artifacts change (e.g., a figure file is regenerated), downstream stages that consumed that artifact become stale:

```bash
# Detect drift
python -m paper_workflow.cli detect-artifact-drift --paper <paper_id>

# Sync drift (marks downstream stages stale)
python -m paper_workflow.cli sync-artifact-stale --paper <paper_id>
```

---

## 5. Common Workflows

### Workflow A: New Paper From Scratch (Full Pipeline)

This is the complete 18-stage pipeline for original research. Use when you have a research idea but no results yet.

```
Step 1: Create the project
  python -m paper_workflow.cli create-project \
    --idea "Your idea" --field "your field" --journal "Target Journal"

Step 2: Run the pipeline (stops at checkpoints)
  python -m paper_workflow.cli run-pipeline --paper <paper_id>

Expected stage progression:
  create_project [CHECKPOINT]  ← You approve the research direction
    → search_literature        ← Automated literature search
    → research_plan [CHECKPOINT] ← You approve the study design
    → data_audit               ← Automated data quality check
    → figure_planning [CHECKPOINT] ← You approve figure layout
    → run_analysis             ← Automated analysis execution
    → verify_methods           ← Automated reproducibility check
    → write_methods            ← Automated drafting
    → write_results            ← Automated drafting
    → write_introduction       ← Automated drafting
    → write_discussion         ← Automated drafting
    → assemble_manuscript [CHECKPOINT] ← You review assembled draft
    → integrity_check [CHECKPOINT] ← You review gate results
    → internal_review [CHECKPOINT] ← You review simulated peer review
    → apply_revision           ← Automated revision
    → re_review [CHECKPOINT]   ← You confirm revisions
    → quality_check            ← Automated final quality gate
    → finalize [CHECKPOINT]    ← You approve final submission package

Step 3: At each checkpoint, review and decide:
  python -m paper_workflow.cli checkpoint \
    --paper <paper_id> --stage <stage> --decision approved

Step 4: If anything fails, diagnose and fix:
  python -m paper_workflow.cli diagnose-gate-failures --paper <paper_id>

Step 5: Retrieve the final submission package:
  papers/<paper_id>/submission/
  ├── manuscript_final.pdf
  ├── manuscript_final.docx
  ├── manuscript_final.tex
  ├── cover_letter.md
  ├── supplementary_package.zip
  └── provenance_report.json
```

### Workflow B: From Existing Analysis Results

Use when you already have analysis results, figures, and data — you want to focus on writing and quality assurance.

```
Step 1: Create the project
  python -m paper_workflow.cli create-project \
    --idea "Your idea" --field "your field" --journal "Target Journal"

Step 2: Skip research and analysis stages by marking them complete.
  (Manually or via API — see Automation Options below)

Step 3: Place your existing results in papers/<paper_id>/results/
  and figures in papers/<paper_id>/figures/

Step 4: Start from figure_planning or write_results:
  - Write a figure_plan.json from your existing analyses
  - Then run the pipeline, which will skip completed stages

Step 5: The pipeline proceeds through writing → assembly → review → finalize.

Python API approach:
  from paper_workflow.workflow import PaperWorkflow
  from paper_workflow.engine.loop_engine import StageStatus

  wf = PaperWorkflow()
  wf.initialize(idea=..., field=..., journal=...)

  # Mark early stages as manually completed
  skip_stages = ["search_literature", "research_plan", "data_audit",
                 "figure_planning", "run_analysis", "verify_methods"]
  for s in skip_stages:
      wf.engine.stages[s].status = StageStatus.COMPLETED

  # Continue from writing phase
  wf.run(stop_at_checkpoint=True)
```

### Workflow C: Revision Cycle (Post-Review)

Use when responding to peer review comments or iterating on a draft.

```
Step 1: Diagnose what needs fixing
  python -m paper_workflow.cli diagnose-gate-failures --paper <paper_id>

Step 2: Review the diagnosis — it identifies:
  - Failed stages with specific errors
  - Gate failures with rule names
  - Stale stages that need re-execution
  - Retry counts vs max retries

Step 3: Fix issues (manually or via pipeline re-run)

Step 4: Mark the revision stages:
  python -m paper_workflow.cli run-pipeline --paper <paper_id>
  # This will run apply_revision → re_review → quality_check → finalize

Step 5: Re-run integrity gates
  python -m paper_workflow.cli run-integrity-gate --paper <paper_id>

Step 6: If all passes, finalize
  python -m paper_workflow.cli checkpoint \
    --paper <paper_id> --stage finalize --decision approved
```

This workflow is designed for multiple revision rounds — each time through the `apply_revision → re_review → quality_check` loop generates a new tracked version.

### Workflow D: Quick Strategy Assessment (No Pipeline)

Use when you only want a research strategy (topic assessment, journal fit, feasibility, hypotheses) without running the full pipeline.

```bash
python -m paper_workflow.cli strategy \
  --idea "Your research idea" \
  --field "your field, keywords" \
  --journal "Target Journal" \
  --timeline 12
```

This produces a complete `research_strategy.yaml` saved to `papers/paper_<slug>_YYYYMMDD/strategy/` but does not initialize a full paper project or start the pipeline.

---

## 6. Customizing Configuration

The framework is domain-agnostic — all domain-specific settings live in YAML configuration files.

### Per-Project Configuration

Each paper can override defaults by placing a `paper_config.yaml` in its project directory:

```
papers/<paper_id>/paper_config.yaml
```

Any key from `config/default_config.yaml` can be overridden here. The paper-level config is merged on top of the defaults.

### Key Configuration Files

| File | Purpose | When to Modify |
|------|---------|---------------|
| `config/default_config.yaml` | Master configuration: pipeline stages, paper types, quality gates, writing standards, domain definitions, skill routing, agent definitions, supervision settings | To change global behavior for all projects |
| `config/journal_database.yaml` | 25 journal profiles with formatting requirements, word/fig limits, special requirements | To add or update journal targets |
| `config/templates/methods_template.md` | Methods section template | To customize section structure |
| `config/templates/results_template.md` | Results section template | To customize section structure |
| `papers/<paper_id>/paper_config.yaml` | Per-project overrides | To customize a single paper |

### Changing the Target Journal

1. Edit the paper's strategy file: `papers/<paper_id>/strategy/research_strategy.yaml`
2. Update `project_passport.yaml` with the new journal name
3. Run `run-integrity-gate` to check journal format compliance

### Adding a New Journal to the Database

Edit `config/journal_database.yaml` and add an entry under `journals:`. Each journal requires:

```yaml
journals:
  Your Journal Name:
    full_name: "Full Journal Name"
    impact_factor: X.X
    category: specialty-high     # One of: high-impact, high-open, specialty-high, specialty-open, methods, clinical
    format_type: LaTeX
    citation_style: Vancouver
    abstract_word_limit: 250
    figure_limit: 8
    main_text_word_limit: 5000
    requires_data_availability: true
    requires_code_availability: true
    open_access: false
    submission_system: "Editorial Manager"
    special_requirements:
      - "Requirement 1"
      - "Requirement 2"
    scope_keywords:
      - keyword1
      - keyword2
```

### Changing Paper Type

The framework supports six paper types, each with specific stage requirements, word limits, and optional extras:

| Paper Type | Pipeline Mode | Key Characteristics |
|------------|--------------|-------------------|
| `original_research` | Full 18-stage | Complete IMRAD, all reporting guidelines |
| `methods` | Methods-focused | Emphasizes verification + benchmarking; skips hypotheses, figure planning, intro, discussion |
| `review` | Review-focused | Emphasizes literature search + synthesis; skips data analysis |
| `clinical_research` | Full | Adds ethics, clinical stats gates, CONSORT/STROBE |
| `data_resource` | Data-focused | Emphasizes data audit + availability; skips analysis |
| `brief_communication` | Condensed | Stricter limits, fewer stages, combined sections |

Set the paper type at creation:

```python
wf.initialize(idea=..., field=..., journal=..., paper_type="methods")
# or override in paper_config.yaml:
# paper_type: methods
```

### Customizing Quality Gates

To disable a gate or change its severity, override it in `paper_config.yaml`:

```yaml
quality_gates:
  g12_no_bullets_in_prose:
    enabled: false
  g13_statistics_reported:
    severity: CRITICAL   # Elevate from HIGH to CRITICAL
```

---

## 7. Adding New Analysis Methods

The framework is extensible through its code library and configuration.

### Adding Reusable Code Patterns

Place new analysis code in the `code_library/` directory:

```
code_library/
├── patterns/          # Reusable analysis patterns (QC, clustering, DE)
├── snippets/          # Small reusable snippets (I/O, logging, config)
├── solutions/         # Complete solutions for common problems
├── modules/           # Self-contained analysis modules
├── pipelines/         # Pipeline templates
└── r/                 # R-specific analysis scripts
```

Example: adding a new QC pattern

```python
# code_library/patterns/qc/my_new_qc.py
"""Custom QC pattern for spatial transcriptomics data."""

def run_spatial_qc(adata, min_genes=200, max_mt_pct=20):
    """Filter spatial data by gene count and MT percentage.
    
    Parameters
    ----------
    adata : AnnData
        Input spatial data object
    min_genes : int
        Minimum number of genes per spot
    max_mt_pct : float
        Maximum mitochondrial gene percentage
    
    Returns
    -------
    AnnData
        Filtered data object
    """
    ...
```

The framework discovers these patterns automatically via the skills dispatcher (`config/default_config.yaml`, section 6).

### Registering a New Agent

Add to `config/default_config.yaml` under `agent_routing.agents`:

```yaml
my_new_analyst:
  agent_id: "my_new_analyst"
  role: "Custom Analysis Specialist"
  expertise: [my_domain_analysis]
  triggers: ["Run my analysis", "Custom pipeline"]
  input_contract:
    required: [analysis_spec]
    optional: [parameters]
  output_contract:
    required: [results]
  tool_permissions:
    allow: ["Bash(python **)", Read, Write]
  skills: [statistical_testing]
```

Then reference the agent in pipeline stage definitions.

### Registering a New Skill

Add to `config/default_config.yaml` under `skills_dispatcher.skills`:

```yaml
my_new_skill:
  skill_id: "my_new_skill"
  description: "Description of the skill"
  triggers:
    - {keywords: [keyword1, keyword2], weight: 10}
  tools: [relevant-mcp-tools]
  chained_skills: [paper_writing]
```

### Creating a Custom Pipeline

Define a custom pipeline by subclassing `PaperLoopEngine` or creating a new configuration with a custom stage list:

```python
from paper_workflow.engine.loop_engine import PaperLoopEngine, StageDefinition, StageStatus

class CustomPipeline(PaperLoopEngine):
    CUSTOM_STAGES = [
        StageDefinition(name="custom_step_1", phase=1, category="custom",
                       description="My custom analysis",
                       produces_artifacts=["results/custom_output.csv"],
                       agent="my_new_analyst", skill="my_new_skill"),
        StageDefinition(name="custom_step_2", phase=1, category="custom",
                       description="My custom post-processing",
                       upstream=["custom_step_1"],
                       produces_artifacts=["figures/custom_figure.pdf"]),
    ]

    def __init__(self, project_root, paper_id, papers_dir=None):
        # Replace default stages with custom ones
        PaperLoopEngine.PIPELINE_STAGES = self.CUSTOM_STAGES
        super().__init__(project_root, paper_id, papers_dir)
```

---

## 8. Troubleshooting Common Issues

### Issue: `pip install -e .` fails with "No module named setuptools"

```bash
pip install --upgrade setuptools wheel
pip install -e .
```

### Issue: `ModuleNotFoundError: No module named 'paper_workflow'`

Ensure the package is installed in development mode:

```bash
pip install -e .
```

Verify the entry point:

```bash
paper-workflow --help
# or
python -m paper_workflow.cli --help
```

### Issue: "Paper not found" when running status or pipeline

The paper ID must match an existing directory under `papers/`. List available papers:

```bash
python -m paper_workflow.cli list-papers
```

Use the exact directory name as the `--paper` argument.

### Issue: Pipeline is BLOCKED — what do I do?

```bash
# Step 1: Diagnose
python -m paper_workflow.cli diagnose-gate-failures --paper <paper_id>

# Step 2: Review the output for:
#   - failed_stages: stages that errored
#   - gate_failures: integrity rules that failed (CRITICAL must be fixed)
#   - stale stages: need re-running after upstream changes

# Step 3: Fix CRITICAL failures first (they block the pipeline)

# Step 4: Re-run integrity gates to verify fixes
python -m paper_workflow.cli run-integrity-gate --paper <paper_id>

# Step 5: Re-run the pipeline
python -m paper_workflow.cli run-pipeline --paper <paper_id>
```

### Issue: Artifact drift detected — stages marked STALE

This means an upstream output file was modified. Downstream stages that consumed it are now stale.

```bash
# See what drifted
python -m paper_workflow.cli detect-artifact-drift --paper <paper_id>

# Mark affected stages stale (the pipeline will re-run them)
python -m paper_workflow.cli sync-artifact-stale --paper <paper_id>

# Re-run the pipeline to refresh stale stages
python -m paper_workflow.cli run-pipeline --paper <paper_id>
```

### Issue: Stage fails with "gate_failure" — too many retries

Each stage has a `max_retries` limit (default 3). After exhausting retries, the stage stays in FAILED state.

```bash
# Check retry count and max
python -m paper_workflow.cli diagnose-gate-failures --paper <paper_id>
# Output includes: retry_count, max_retries

# If max retries exceeded, you can manually reset via Python:
python -c "
from paper_workflow.engine.loop_engine import PaperLoopEngine, StageStatus
from pathlib import Path
engine = PaperLoopEngine(Path.cwd(), '<paper_id>')
engine.stages['<failed_stage>'].status = StageStatus.PENDING
engine.stages['<failed_stage>'].retry_count = 0
engine.stages['<failed_stage>'].errors = []
engine._update_passport()
print('Stage reset. Re-run the pipeline.')
"
```

### Issue: Tests fail with "AGENTS.md not found"

The framework discovers the project root by finding `AGENTS.md` (or `CLAUDE.md`). Ensure this file exists at the repository root:

```bash
# Verify
ls AGENTS.md

# If missing, re-clone or create a minimal one:
echo "# Research Paper Workflow" > AGENTS.md
```

### Issue: "Missing data availability statement" integrity gate failure

Add a data availability section to your manuscript methods or create a standalone statement:

```bash
# Create the statement file in the paper directory
echo "## Data Availability

All raw sequencing data have been deposited in the Gene Expression Omnibus (GEO) under accession GSEXXXXXX. Processed data and analysis results are available at [repository URL]." > papers/<paper_id>/manuscript/data_availability.md
```

### Issue: "No bullets in prose" integrity gate failure

The framework enforces natural prose in manuscript body. Convert bullet points to flowing paragraphs. Bullet points are only allowed in figure legends, tables, and supplementary materials.

### Issue: "Statistics reported" integrity gate failure

Ensure all quantitative claims include:
- Exact p-values (not just "p < 0.05")
- Effect sizes with confidence intervals (OR/HR/β/Cohen d + 95% CI)
- Test statistic name and value

Example of passing prose: `"Treated group showed significantly higher expression (log2FC = 1.42, 95% CI [1.12, 1.72], p = 0.003, Wald test)."`

### Issue: "Claim-to-artifact binding" integrity gate failure

Every factual claim in the manuscript must be traceable to a specific supporting artifact. Generate or update the claims evidence table:

```
papers/<paper_id>/manuscript/claims_evidence_table.md
```

Format: `| Claim | Supporting Artifact | Evidence Strength | Limitation |`

### Quick Reference: CLI Commands

| Command | Purpose |
|---------|---------|
| `create-project --idea "..." --field "..." --journal "..."` | Create new paper project |
| `status --paper <id>` | Show pipeline status |
| `run-pipeline --paper <id> [--stop-on-failure]` | Run pipeline |
| `checkpoint --paper <id> --stage <s> --decision approved` | Approve a checkpoint |
| `run-integrity-gate --paper <id>` | Run all 16 integrity checks |
| `diagnose-gate-failures --paper <id>` | Diagnose what went wrong |
| `detect-artifact-drift --paper <id>` | Find changed artifacts |
| `sync-artifact-stale --paper <id>` | Mark downstream stages stale |
| `list-papers` | List all paper projects |
| `strategy --idea "..." --field "..." [--journal "..."]` | Assess research strategy only |

### Quick Reference: Makefile Targets

| Command | Purpose |
|---------|---------|
| `make install` | Install core dependencies |
| `make install-full` | Install + plotting deps |
| `make install-all` | Install all deps |
| `make test` | Run all integration tests |
| `make init-paper IDEA="..." FIELD="..." JOURNAL="..."` | Create paper project |
| `make status PAPER=<id>` | Show pipeline status |
| `make run PAPER=<id>` | Run pipeline |
| `make integrity PAPER=<id>` | Run integrity gates |
| `make list` | List all papers |
| `make lint` | Run linter |
| `make format` | Format code |
| `make clean` | Clean cache files |

---

## Next Steps

- Read `docs/ARCHITECTURE.md` for the four-layer system design
- Read `AGENTS.md` for core rules and output standards
- Explore `config/default_config.yaml` for all configurable options
- Review `examples/example_project/` for a sample paper workflow

For help with specific paper-writing tasks (methods section, figure design, literature search), the framework invokes specialized skills and agents — see `config/default_config.yaml` sections 6 (Skills Dispatcher) and 7 (Agent Routing) for the full mapping.

---

*Last updated: 2026-06-18*
