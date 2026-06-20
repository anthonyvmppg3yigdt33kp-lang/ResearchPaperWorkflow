# AGENTS.md -- Research Paper Workflow Framework

> **Role**: This file is read by AI assistants on session start. It defines project identity, core rules, complete skill inventory with trigger words, agent invocation rules, code library index, and quality gate protocol.

---

## Project Identity

This is a **full-stack bioinformatics research workflow system** that transforms the research paper writing process from ad-hoc scripting into a deterministic, auditable, multi-agent pipeline. The framework spans the complete lifecycle: ideation, literature review, data analysis, manuscript drafting, figure generation, citation management, peer review simulation, revision, and final submission.

**Architecture**: 4-layer (Strategy -> Decision -> Execution -> Supervision), **19-stage pipeline** (v3.0), 6 phases, 8-step loop engine, 5-file passport system, **41 integrity gates** (17 CRITICAL + 21 HIGH + 3 MEDIUM).

**The user is the final scientific decision maker.** The framework must never invent data, results, clinical facts, or references.

---

## Core Rules

1. **Never modify** raw data or existing final results without explicit confirmation.
2. **All generated results** must have a corresponding reproducible script or pipeline stage.
3. **Every claim** in manuscripts must be bound to a specific figure, table, or result artifact.
4. **Distinguish clearly** between:
   - Observed result (what the data shows)
   - Statistical association (test result with effect size and p-value)
   - Biological interpretation (what it might mean)
   - Mechanistic hypothesis (proposed causal chain)
   - Experimentally validated conclusion (proven by independent experiment)
5. **Do not interpret** correlation as causation.
6. **Do not treat** cells/spots/features as independent biological samples when the correct unit is patient/sample.
7. **Always report** assumptions, potential confounders, and limitations.
8. **All paths** must be relative to the project root -- no hardcoded absolute paths.
9. **All random seeds** must be set and documented.
10. **Methods-to-Code Traceability**: Every parameter value in Methods text must match the exact value used in the analysis code. Any mismatch is a CRITICAL integrity gate failure.
11. **No guessing**: All numbers written into manuscripts must come from actual code output or verified data.
12. **Skill over script**: When a skill (installable workflow) exists for a task, invoke it rather than hand-coding the workflow from scratch.
13. **MCP tools first**: For literature search, use PubMed/Consensus MCP tools. For code understanding, use `fast-context` MCP. For web search, use `grok-search` or `exa` MCP.
14. **Per-project passport**: Every paper project maintains a `papers/{paper_id}/project_passport.yaml` with complete state. Read it before any major task.

---

## Required Reading Before Major Tasks

Before starting any major task, read:
- `README.md` -- Framework overview
- `docs/ARCHITECTURE.md` -- Full system architecture
- `config/default_config.yaml` -- Current pipeline configuration

For paper-specific tasks, also read:
- `papers/{paper_id}/project_passport.yaml` -- Project state and stage status
- `papers/{paper_id}/paper_config.yaml` -- Paper-specific configuration overrides
- `.claude/SKILL_REGISTRY.md` -- Complete 28-skill mapping with trigger words

---

## Complete Skill Inventory (28 Skills)

All skills are organized by research phase. **Trigger words** are listed for each skill -- when a user request matches these, the skill MUST be invoked.

### RESEARCH PHASE Skills (6 skills)

| # | Skill | Purpose | Trigger Words |
|---|-------|---------|---------------|
| 1 | **`deep-research`** | Enterprise-grade multi-source research with citation tracking, source credibility scoring, cross-verification. Produces structured citation-backed reports. | "deep research", "comprehensive analysis", "research report", "compare X vs Y", "analyze trends", "state of the art" |
| 2 | **`tavily-research`** | AI-powered multi-source research via Tavily CLI. Returns structured report with explicit web citations. 30-120 seconds. | "research", "investigate", "analyze in depth", "market analysis", "literature review" (general/non-biomedical) |
| 3 | **`paper-glance`** | Universal paper processing: deep analysis report, mind map, review comments, promotional script, podcast audio generation. **MUST trigger on any PDF upload or paper text paste.** | "帮我看这篇论文", "paper analysis", "analyze this paper", "论文", "paper", "文献", "arxiv", PDF upload |
| 4 | **`summarize`** | Quick text/transcript summarization from URLs, podcasts, local files. Fallback for "transcribe this YouTube/video". | "summarize", "summary", "digest", "transcribe", "extract key points" |
| 5 | **`nature-reader`** | Chinese-English side-by-side paper reader from PDF/DOI/arXiv/HTML. Preserves figure/table placement, source anchors for every block. | "读论文", "精读论文", "论文翻译", "文献翻译", "文献阅读", "帮我读这篇文章", "translate paper", "read paper" |
| 6 | **`find-skills`** | Skill discovery and installation. Helps users find installable skills for new capabilities. | "how do I do X", "find a skill for X", "is there a skill that can..." |

### LITERATURE SEARCH Skills (2 skills)

| # | Skill | Purpose | Trigger Words |
|---|-------|---------|---------------|
| 7 | **`nature-academic-search`** | Multi-source literature search (PubMed, CrossRef, arXiv, Scopus, ScienceDirect) with citation file management, MeSH search strategy, reference deduplication. | "文献检索", "查文献", "找文献", "文献综述检索", "查论文", "引文核对", "参考文献管理", "literature search", "systematic review search" |
| 8 | **`nature-citation`** | Add strict Nature/CNS citations to manuscript text. Splits passages into citable segments, searches Nature Portfolio/AAAS Science/Cell Press journals, exports reference-manager-ready output. | "分段引用", "自动给出引用", "Nature系列引用", "CNS及子刊", "补引用", "找引用", "add citations", "find sources for claim", "build reference list" |

### WRITING PHASE Skills (4 skills)

| # | Skill | Purpose | Trigger Words |
|---|-------|---------|---------------|
| 9 | **`scientific-writing`** | Core IMRAD scientific manuscript writing. Two-stage process: section outlines with key points, then conversion to flowing prose. Supports CONSORT/STROBE/PRISMA/STREGA reporting guidelines. Full paragraphs only (never bullet points in final output). | "write methods section", "draft results", "scientific manuscript", "IMRAD", "写方法", "写结果", "写讨论", "reporting guidelines" |
| 10 | **`nature-writing`** | Nature-style manuscript drafting from author-provided claims, results, figures, notes, or Chinese drafts. Bottom-up construction (raw material to prose). | "write Nature paper", "Nature-style manuscript", "Nature writing", "写Nature风格论文", "draft from results", "write paper from scratch" |
| 11 | **`research-paper-writing`** | ML/CV/NLP-style paper writing with CS-specific section structure (Related Work, Experiments, claim-support alignment for reviewer-facing presentation). | "write ML paper", "CV paper", "conference paper", "NLP paper", "draft experiments section" |
| 12 | **`academic-paper`** | 12-agent academic paper writing pipeline. 10 modes (full/plan/outline/revision/revision-coach/abstract/lit-review/format-convert/citation-check/disclosure). 6 paper types, 5 citation formats, LaTeX/DOCX/PDF output. | "write paper", "academic paper", "guide my paper", "parse reviews", "AI disclosure", "寫論文", "學術論文", "draft manuscript" |

### POLISHING PHASE Skills (4 skills)

| # | Skill | Purpose | Trigger Words |
|---|-------|---------|---------------|
| 13 | **`academic-paper-polish`** | Standard academic prose polishing. Improves fluency, consistent register, discipline-appropriate vocabulary. | "polish my paper", "language editing", "proofreading", "improve academic English" |
| 14 | **`nature-polishing`** | Nature-leaning English prose polish using curated patterns from actual Nature/Nature Communications articles + Academic Phrasebank. Also handles LaTeX layout/typesetting fixes. | "Nature polish", "润色", "改写", "学术英语", "英文润色", "polish to Nature level", "academic writing polish" |
| 15 | **`humanizer`** | Remove signs of AI-generated writing from English text. Detects and fixes: inflated symbolism, promotional language, superficial -ing analyses, vague attributions, em dash overuse, rule of three, AI vocabulary words, excessive conjunctive phrases. | "remove AI signs", "make it sound human", "naturalize", "remove AI writing patterns", "de-AI the text" |
| 16 | **`remove-ai-flavor`** | Remove AI flavor from Chinese text (公众号, 自媒体, 演讲稿, 课程稿, 产品文案). Fixes template-like writing, buzzword stacking, em dash abuse, bullet stacking, forced bolding. **NOT for English papers -- use `humanizer` instead.** | "去AI味", "去除AI痕迹", "不像AI写的", "更像人写的", "更自然", "别太机器味", "去掉模板感" |

### FIGURE PHASE Skills (1 skill)

| # | Skill | Purpose | Trigger Words |
|---|-------|---------|---------------|
| 17 | **`nature-figure`** | Submission-grade figure workflow for Python (matplotlib/seaborn) or R (ggplot2/patchwork/ComplexHeatmap). Defines figure conclusion -> evidence logic -> export targets -> review risks before plotting. Outputs 300+ DPI TIFF/PDF/SVG with colorblind-safe palettes. | "论文配图", "科研绘图", "画图", "作图", "出图", "论文图表", "scientific figure", "journal figure", "make figure for paper", "publication figure" |

### CITATION PHASE Skills (1 skill)

*(Covered above: `nature-citation` [#8] and `nature-academic-search` [#7])*

### REVIEW PHASE Skills (2 skills)

| # | Skill | Purpose | Trigger Words |
|---|-------|---------|---------------|
| 18 | **`academic-paper-reviewer`** | Multi-perspective paper review with 5 independent reviewers (EIC + 3 peer reviewers + Devil's Advocate). 6 modes (full/re-review/quick/methodology/socratic/calibration). Field-specific expertise simulation. | "review paper", "peer review", "manuscript review", "referee report", "review my paper", "critique paper", "simulate review", "审稿", "同行评审" |
| 19 | **`nature-response`** | Point-by-point reviewer response letter drafting for Nature-family manuscript revisions. Handles major/minor revision requests, rebuttal letters, response to reviewers. | "审稿意见回复", "逐点回复", "修回信", "大修回复", "小修回复", "reviewer response", "rebuttal letter", "reply to reviewers", "response to reviewers" |

### DATA & COMPLIANCE Skills (1 skill)

| # | Skill | Purpose | Trigger Words |
|---|-------|---------|---------------|
| 20 | **`nature-data`** | Nature-ready Data Availability statements, data repository plans, dataset citations, FAIR metadata checklists. Prepares/audits/revises data statements for manuscripts. | "数据可用性声明", "数据可用性", "数据共享", "代码可用性", "学术写作数据声明", "data availability statement", "data sharing plan", "repository selection" |

### DETECTION PHASE Skills (1 skill)

| # | Skill | Purpose | Trigger Words |
|---|-------|---------|---------------|
| 21 | **`ai-writing-detection`** | Comprehensive AI writing detection patterns and methodology. Provides vocabulary lists, structural patterns, model-specific fingerprints, false positive prevention. | "AI writing detection", "check for AI writing", "detect AI text", "AI痕迹检测", "查AI" |

### PRESENTATION PHASE Skills (1 skill)

| # | Skill | Purpose | Trigger Words |
|---|-------|---------|---------------|
| 22 | **`nature-paper2ppt`** | Paper-to-presentation conversion. Builds Nature-style Chinese PPTX from paper/PDF/abstract/figures. Identifies paper type, selects figures, writes Chinese slide content + speaker notes, runs self-review/revision loop. | "论文做PPT", "组会PPT", "文献汇报", "学术汇报", "做幻灯片", "讲paper", "paper to slides", "academic presentation", "journal club slides" |

### ORCHESTRATION Phase Skills (1 skill)

| # | Skill | Purpose | Trigger Words |
|---|-------|---------|---------------|
| 23 | **`academic-pipeline`** | Full 10-stage orchestrated pipeline: research -> write -> integrity check -> review -> revise -> re-review -> re-revise -> final integrity check -> finalize. Coordinates deep-research, academic-paper, and academic-paper-reviewer with mandatory integrity verification at two points. | "academic pipeline", "research to paper", "full paper workflow", "paper pipeline", "end-to-end paper", "research-to-publication", "complete paper workflow" |

### DOMAIN-SPECIFIC ANALYSIS Skills (2 skills)

| # | Skill | Purpose | Trigger Words |
|---|-------|---------|---------------|
| 24 | **`wgcna-analyst`** | WGCNA co-expression network analysis specialist. Full pipeline execution, code repair, result analysis, module-trait association, hub gene screening, visualization, Cytoscape export, downstream ML integration. **Auto-triggered on any WGCNA keyword.** | WGCNA, 共表达网络, co-expression network, 模块分析, module analysis, pickSoftThreshold, blockwiseModules, 软阈值, hub gene, module eigengene, module-trait, 免疫浸润+WGCNA, TOM矩阵, scale-free topology, signedKME |
| 25 | **`ccg`** (all subskills) | Quality gates & multi-agent orchestration toolkit. Subskills used: `ccg:review` (code review), `ccg:test` (test generation), `ccg:commit` (version control), `ccg:debug` (failure diagnosis), `ccg:team-plan`/`ccg:team-exec`/`ccg:team-review` (multi-agent coordination), `ccg:workflow` (full dev workflow). | "code review", "verify change", "debug pipeline", "run analysis in parallel", see ccg subskill list |

### META Skills (3 skills)

| # | Skill | Purpose | Trigger Words |
|---|-------|---------|---------------|
| 26 | **`darwin-skill`** | Autonomous skill optimizer using 8-dimension rubric + hill-climbing with git version control. | "优化skill", "skill评分", "自动优化", "auto optimize", "skill质量检查" |
| 27 | **`skill-creator`** | Create, modify, and benchmark skills. | "create skill", "edit skill", "optimize skill", "measure skill performance" |
| 28 | **`agent-browser`** | Browser automation for journal portals, submission systems, web-based database queries. | "open journal website", "check submission portal", "navigate to author guidelines" |

---

## Skill Dispatch Priority

When multiple skills match a user request, dispatch in this order:

1. **Domain-specific analysis** (e.g., `wgcna-analyst`) -- most specific, highest priority
2. **Pipeline orchestrator** (`academic-pipeline`) -- if "end-to-end" / "full workflow"
3. **Core writing** (`academic-paper`, `scientific-writing`, `nature-writing`, `research-paper-writing`)
4. **Research** (`deep-research`, `nature-academic-search`, `tavily-research`, `paper-glance`)
5. **Quality** (`academic-paper-reviewer`, `ai-writing-detection`, `ccg:review`)
6. **Language** (`nature-polishing`, `humanizer`, `academic-paper-polish`, `remove-ai-flavor`)
7. **Figures** (`nature-figure`)
8. **Citations** (`nature-citation`)
9. **Meta** (`find-skills`, `skill-creator`, `darwin-skill`)

### Journal-Tier Skill Routing

| Target Journal Tier | Writing Skill | Polishing Skill | Citation Skill |
|--------------------|---------------|-----------------|----------------|
| Nature/CNS Flagship | `nature-writing` | `nature-polishing` | `nature-citation` |
| Nature Communications / Science Advances | `nature-writing` | `nature-polishing` | `nature-citation` |
| Top Field (IF 8-20) | `scientific-writing` | `nature-polishing` | `nature-academic-search` |
| Strong Field (IF 4-8) | `scientific-writing` | `academic-paper-polish` | `nature-academic-search` |
| Solid Specialty (IF 2-4) | `scientific-writing` | `academic-paper-polish` | `nature-academic-search` |
| CS Conference/Journal | `research-paper-writing` | `academic-paper-polish` | `nature-academic-search` |

### Prose Quality Pipeline

```
Draft (raw) -> Structural Polish -> Language Polish -> AI-Sign Removal -> Final Prose

  Draft:        academic-paper / scientific-writing / nature-writing / research-paper-writing
  Structural:   nature-polishing (restructure mode)
  Language:     nature-polishing / academic-paper-polish
  AI Removal:   humanizer (English) / remove-ai-flavor (Chinese)
  Final:        integrity_check gate M2 (no_bullets_in_prose)
```

---

## Agent Invocation Rules

### When to Use Which Agent

The framework has 10 specialized agents (defined in `.claude/agents/`) plus `analysis_executor` (defined in the team YAML but without a standalone agent file). For AI assistant operation, the primary agents that handle the complete lifecycle are:

| Task | Agent to Invoke | How to Invoke |
|------|----------------|---------------|
| Research design, topic selection, journal targeting, feasibility, hypothesis generation | `research_strategist` | Use `deep-research` + `nature-academic-search` skills |
| Literature search, bibliography building, citation management, evidence synthesis | `literature_reviewer` | Use `nature-academic-search` + `paper-glance` + `nature-reader` |
| Data quality audit, metadata validation, batch effect detection | `data_auditor` | Use `ccg:review` skill; read-only operations |
| Figure architecture, panel design, color palette selection | `figure_planner` | Use `nature-figure` skill |
| Data analysis execution (R/Python pipelines) | `analysis_executor` | Use `wgcna-analyst` (if WGCNA) + `ccg:team-exec` |
| Pipeline engineering, reproducibility verification, environment management | `pipeline_engineer` | Use `ccg:workflow` + `nature-data` |
| Statistical testing, power analysis, test selection audit, results validation | `statistician` | Cross-cutting -- audits after S7 & S10 asynchronously |
| Manuscript writing, IMRAD assembly, formatting, revision application | `report_writer` | Use `academic-paper` + `scientific-writing` + `nature-writing` + polishing skills |
| Quality assurance, integrity gate enforcement, citation cross-referencing | `integrity_checker` | Use `academic-paper-reviewer` + `ai-writing-detection` + `ccg:team-review` |
| Multi-agent coordination, task decomposition, parallel scheduling, deadlock detection | `team_orchestrator` | Use `academic-pipeline` + `ccg:team-plan` |
| Multi-omics integration (MOFA, DIABLO, cross-omics correlation) | `multi_omics_integrator` | Use `ccg:team-exec` + domain-specific skills |

### Agent Responsibility Boundaries (I Do / I Don't Do)

| Agent | I DO | I DON'T DO |
|-------|------|------------|
| `research_strategist` | Define questions, assess feasibility, target journals, generate hypotheses | Run code, search literature (delegates to `literature_reviewer`) |
| `literature_reviewer` | Search databases, build bibliographies, synthesize evidence | Run analysis code, write manuscript sections |
| `data_auditor` | Read and assess data quality, validate metadata, detect batch effects | Modify data, write manuscript text |
| `figure_planner` | Design figure architecture, choose color palettes, specify panels | Run analysis, generate figures (hands to `analysis_executor`) |
| `analysis_executor` | Run R/Python pipelines, generate result tables and figures, log sessions | Design figures, write prose |
| `pipeline_engineer` | Build Docker/conda environments, verify reproducibility, manage deps | Run primary analysis |
| `statistician` | Review study design, audit test selection, validate reported statistics | Modify data, write manuscript text (advisory only) |
| `report_writer` | Write IMRAD sections, assemble manuscripts, format for journals | Run analysis, search literature, check integrity |
| `integrity_checker` | Run 16 gates, cross-reference citations, verify claim-artifact binding | Modify manuscript, add citations, generate figures |
| `multi_omics_integrator` | Integrate cross-omics data (MOFA, DIABLO), run factor analysis | Design study, write full manuscripts |

### Team Dispatch

| Team | For | Composition |
|------|-----|-------------|
| `paper_writing_team` | Full-cycle manuscript production (primary team) | All 9 domain agents + `team_orchestrator` |
| `review_team` | Internal peer review (stage 15) | `integrity_checker` + `statistician` + `literature_reviewer` |
| `analysis_team` | Data analysis pipeline (stages 5-8) | `analysis_executor` + `pipeline_engineer` + `data_auditor` |

---

## Code Library Index

The `code_library/` directory contains reusable analysis patterns. Import from here rather than writing from scratch.

### Python Modules

```
code_library/
├── __init__.py                          # Module index with __all__
├── modules/
│   └── cell_type_annotation.py          # Marker-based cell type annotation (scanpy)
├── snippets/
│   ├── h5ad_io.py                       # Safe h5ad read/write with validation
│   ├── logging_setup.py                 # Structured logging configuration
│   └── yaml_config.py                   # YAML config loader with dot-notation access
├── solutions/
│   ├── ambient_rna_removal.py           # SoupX + simple ambient RNA correction
│   ├── doublet_detection.py             # Scrublet + statistical doublet detection
│   └── ensembl_to_symbol.py             # Ensembl ID to gene symbol conversion
└── r/
    └── bioinformatics_analysis.R        # R module: Seurat, DE, WGCNA, GSVA, visualization
```

### Available Analysis Patterns

| Pattern | File | Function |
|---------|------|----------|
| MT% Filtering | `patterns/qc/mt_filter.py` | MT% filtering with tissue-specific thresholds |
| Leiden Clustering | `patterns/clustering/leiden_clustering.py` | Leiden clustering with silhouette auto-select |
| Multi-Resolution | `patterns/clustering/multi_resolution.py` | Multi-resolution clustering comparison |

### R Module (`code_library/r/bioinformatics_analysis.R`)

Provides agent-callable, parameter-documented, reproducible R functions covering:
- **Section 1**: Seurat-based single-cell analysis (NormalizeData, FindVariableFeatures, RunPCA, RunUMAP, FindClusters)
- **Section 2**: Differential expression (FindAllMarkers, FindMarkers, DESeq2, limma, edgeR)
- **Section 3**: WGCNA co-expression network analysis
- **Section 4**: GSVA / fgsea pathway enrichment
- **Section 5**: clusterProfiler GO/KEGG enrichment
- **Section 6**: Publication-quality visualization (ggplot2 + Nature palettes)

Loading: `source("C:/Users/HP/Desktop/ResearchPaperWorkflow_v2/code_library/r/bioinformatics_analysis.R")`

### Usage Conventions

1. All functions print structured messages (key results for agent parsing).
2. All paths use `{PLACEHOLDER}` comments for portability -- change before use.
3. Default seed is `42L` -- use `set_random_seed()` to change.
4. Nature color palettes are pre-defined: `NATURE_REDS`, `NATURE_BLUES`, `NATURE_GREENS`, `NATURE_ORANGES`, `NATURE_PURPLES`, `NATURE_DIVERGENT`.

---

## Quality Gate Protocol

### 16 Integrity Gates

| Severity | ID | Gate | Description |
|----------|----|------|-------------|
| **CRITICAL** | C1 | `bibtex_citation_existence` | Every \cite{} has a BibTeX entry |
| **CRITICAL** | C2 | `citation_evidence_traceability` | Every citation has evidence record |
| **CRITICAL** | C3 | `results_no_citations` | Results section has zero \cite{} commands |
| **CRITICAL** | C4 | `claim_artifact_binding` | Every claim binds to a figure or table |
| **CRITICAL** | C5 | `figures_referenced` | Every \ref{fig:...} points to a real file |
| **HIGH** | H1 | `data_availability_statement` | Data Availability section present |
| **HIGH** | H2 | `code_availability_statement` | Code Availability section present |
| **HIGH** | H3 | `no_local_paths` | No absolute paths in manuscript |
| **HIGH** | H4 | `methods_parameters_complete` | All parameters and versions documented |
| **HIGH** | H5 | `discussion_limitations` | Dedicated Limitations paragraph (>=100 words) |
| **HIGH** | H6 | `results_no_overinterpretation` | No causal language for correlations |
| **HIGH** | H7 | `statistics_reported` | Exact p-values + effect sizes + confidence intervals |
| **HIGH** | H8 | `pseudoreplication_check` | Correct biological replicate unit |
| **MEDIUM** | M1 | `section_length_minimum` | Each section meets word count minimum |
| **MEDIUM** | M2 | `no_bullets_in_prose` | Natural prose paragraphs only (no bullet points) |
| **MEDIUM** | M3 | `figure_count_requirements` | Within journal figure limit |

### Gate Severity and Pipeline Behavior

| Severity | Count | Pipeline Impact | Resolution |
|----------|-------|-----------------|------------|
| **CRITICAL** | 5 | **BLOCK** -- pipeline cannot advance past `integrity_check` or `quality_check` | Must fix before proceeding |
| **HIGH** | 8 | **WARN** -- logged, must be explicitly accepted or remediated | Document if not fixed |
| **MEDIUM** | 3 | **ADVISORY** -- informational only | No resolution required |

### Post-Failure Workflow

```
Gate CRITICAL failure detected
  -> Pipeline BLOCKED
  -> integrity_checker emits integrity_report.json + integrity_report.md
  -> User runs diagnose-gate-failures
  -> team_orchestrator routes each failure to responsible agent:
        bibtex failures -> literature_reviewer
        claim-binding failures -> report_writer
        statistics failures -> statistician
        format failures -> report_writer
  -> After fixes, re-run integrity_check
  -> All decisions logged to checkpoint_ledger.jsonl
```

### Auto-Triggered CCG Quality Gates

For code changes during any paper workflow stage:

| Trigger | Quality Gate | Purpose |
|---------|-------------|---------|
| Code changes >30 lines | `/verify-change` -> `/verify-quality` -> `/verify-security` | Code quality |
| New module/package created | `/gen-docs` -> `/verify-module` | Documentation completeness |
| Security-related changes | `/verify-security` | Vulnerability scan |
| Multi-file coordination (>3 files) | `ccg:team-plan` -> `ccg:team-exec` | Multi-agent orchestration |

---

## Output Standards

### For Analysis Tasks
- Executable script (Python/R) with parameter documentation
- Result table (CSV/TSV) with column descriptions
- Figure file (PDF/SVG/TIFF, >=300 DPI, colorblind-friendly)
- Markdown report with: methods summary, key findings, assumptions, limitations
- Commands used and software versions (`session_info.txt`)

### For Writing Tasks
- Markdown manuscript section following IMRAD structure
- Each key claim annotated with supporting figure/table reference
- Claims evidence table: claim -> supporting artifact -> evidence strength -> limitation
- No bullet points in manuscript body -- natural prose paragraphs
- Methods-to-Code Traceability Matrix (mandatory before finalizing Methods)

### For Review Tasks
- Findings ordered by severity (Critical -> High -> Medium -> Low)
- Each finding includes: location, issue, recommendation, rationale
- Distinguish "must-fix" from "should-fix" from "optional"
- 5-reviewer simulation (EIC + 3 peer reviewers + Devil's Advocate)

---

## Scientific Writing Standards

1. **Objective language**: "showed/demonstrated/indicated" -- not "interesting/remarkable/surprising"
2. **Quantitative precision**: Report exact p-values (not "p<0.05"), effect sizes with confidence intervals (not "significant" alone)
3. **Humble claims**: Do not use "first/novel/paradigm-shifting" without extraordinary evidence
4. **Limitations mandatory**: Every Discussion must include a dedicated Limitations paragraph (>=100 words)
5. **Citation integrity**: Every citation must have a BibTeX entry and citation evidence record; key factual claims require >=2 independent sources
6. **Results vs. Discussion separation**: Results section reports findings with zero interpretation citations; Discussion interprets findings with literature context
7. **Parameter fidelity**: Every parameter value in the Methods text must match the value used in analysis code exactly (verified via traceability matrix)
8. **Figure captions standalone**: Readers should understand what each figure shows without referencing the main text
9. **Reproducibility**: Random seeds documented, software versions recorded, environment snapshot provided

---

## Project Structure Quick Reference

```
ResearchPaperWorkflow/
├── src/paper_workflow/          # Core Python package
│   ├── strategy/                # Topic, journal, feasibility, hypothesis
│   ├── engine/                  # Paper loop engine (18-stage state machine)
│   ├── supervision/             # Passport system + 41 integrity gates (v3.0)
│   ├── cli/                     # 12 CLI commands
│   └── workflow.py              # Unified orchestrator
├── .claude/                     # Agent/skill/team definitions
│   ├── SKILL_REGISTRY.md        # 28-skill mapping (READ THIS)
│   ├── skills/ (5)              # Framework skill workflow templates
│   ├── agents/ (10)             # Agent definition files
│   └── teams/ (1)               # Team configuration
├── config/                      # Externalized configuration
│   ├── default_config.yaml      # Master config
│   ├── journal_database.yaml    # 25 journals across 6 tiers
│   └── templates/               # Paper section templates
├── code_library/                # Reusable analysis code
│   ├── modules/                 # Full analysis modules
│   ├── snippets/                # I/O, logging, config utilities
│   ├── solutions/               # Common problem solutions
│   └── r/                       # R bioinformatics module
├── paper_writing/               # Paper writing SKILL.md
├── docs/                        # Documentation (ARCHITECTURE.md, QUICK_START.md)
├── tests/                       # Integration tests (test_all.py)
├── examples/                    # Example project
└── papers/                      # Generated paper projects (gitignored)
```

---

## Integration with AI Assistants

This framework is designed for AI coding assistants (Claude Code, Codex, etc.):

1. **AGENTS.md** (this file): Read on startup -- defines project rules, skills, agents, and gate protocol
2. **Skills**: Invoke via `Skill` tool for specialized workflows; 28 skills mapped with trigger words
3. **MCP Tools**: PubMed, Consensus, Context7 (library docs), fast-context (code search), grok-search/exa (web search), MiniMax (vision)
4. **Subagents**: Spawn via `TaskCreate` for parallel analysis, review, and execution
5. **Passport System**: State persisted in `papers/{paper_id}/` -- survives session restarts

---

## Six Paper Types Supported

| Type | Stages | Description |
|------|--------|-------------|
| `original_research` | All 18 | Full pipeline -- primary research article |
| `methods` | 14 | Methods/tool paper -- emphasizes verification + benchmarking |
| `review` | 13 | Literature review -- emphasizes search + synthesis |
| `clinical_research` | All 18 | Adds ethics gates, CONSORT/STROBE checklists |
| `data_resource` | 12 | Data/resource descriptor -- emphasizes data audit + availability |
| `brief_communication` | 14 | Short report -- condensed pipeline, stricter limits |

---

## Usage Patterns (Quick Decision Guide)

### Pattern 1: New Paper from Scratch
```
1. create-project (via CLI) -> project_passport.yaml created
2. Invoke deep-research for topic exploration
3. Invoke nature-academic-search for systematic literature search
4. Invoke academic-pipeline for full 18-stage orchestration
   OR invoke individual skills per phase as needed
```

### Pattern 2: From Existing Analysis Results
```
1. create-project and record existing artifacts
2. Invoke nature-figure for figure planning/generation
3. Invoke scientific-writing or nature-writing for IMRAD drafting
4. Invoke nature-polishing for language polish
5. Invoke academic-paper-reviewer for internal review
6. Invoke nature-data for data availability statement
```

### Pattern 3: Revision Cycle (Reviewer Comments Received)
```
1. Invoke nature-response for point-by-point rebuttal drafting
2. Invoke academic-paper (revision mode) for applying changes
3. Invoke academic-paper-reviewer (re-review mode) for verification
4. Invoke integrity_checker for final gate run
```

### Pattern 4: Literature Review
```
1. Invoke nature-academic-search for multi-database search
2. Invoke paper-glance for deep analysis of key papers
3. Invoke nature-reader for bilingual reading of critical papers
4. Invoke scientific-writing (lit-review mode) for synthesis writing
```

### Pattern 5: Journal Club / Group Meeting
```
1. Invoke paper-glance for comprehensive paper analysis
2. Invoke nature-reader for bilingual side-by-side reading
3. Invoke nature-paper2ppt for presentation generation
```

---

## Essential Commands (CLI)

```bash
# Create a new paper project
python -m paper_workflow.cli create-project --idea "Your idea" --field "keywords" --journal "Target Journal"

# Check pipeline status
python -m paper_workflow.cli status --paper <paper_id>

# Run the full pipeline
python -m paper_workflow.cli run-pipeline --paper <paper_id>

# Run a specific stage
python -m paper_workflow.cli run-stage --paper <paper_id> --stage write_results

# Diagnose gate failures
python -m paper_workflow.cli diagnose-gate-failures --paper <paper_id>

# Run tests
python tests/test_all.py
```

---

## Phase Report Generation Protocol

### When to Generate

A `PHASE_REPORT.md` is generated at these checkpoints:

1. **After any analysis phase completes** (success or graceful degradation) -- captures the state of all outputs at that point.
2. **Before any human checkpoint** -- gives the user a complete audit snapshot before they make a decision.
3. **After resolving errors** -- updated report reflects the resolved state.

### What to Include (8 Standard Sections)

Every PHASE_REPORT.md follows a fixed structure:

| # | Section | Content |
|---|---------|---------|
| 1 | Executive Summary | One-paragraph summary of all completed phases, total file count, errors resolved/deferred. |
| 2 | Analysis Methods & Parameters | Per-step: method description, key parameters with exact values, code file paths, key outputs, primary finding. |
| 3 | Results Inventory | Three sub-tables: (a) all generated figures with descriptions, (b) all tables with row counts, (c) all analysis scripts with language and status. |
| 4 | Key Biological Findings | Numbered findings, each with: title, description, confidence level (HIGH/MODERATE/LOW). |
| 5 | Analysis Completeness Audit | Three sub-tables: (a) COMPLETED analyses with output counts, (b) NOT COMPLETED / DEFERRED with blocker and mitigation, (c) Errors & Abnormal Results with ERR-XXX IDs. |
| 6 | Task Continuity | Table linking each completed phase to its work_log.md entry number, with status icons and timestamps. Includes "Next" pointer to the pending phase. |
| 7 | Parameters Quick Reference | Consolidated table of every analysis parameter (threshold, seed, method setting) and which phase used it. |
| 8 | Timestamp & Audit Trail | All phase start/end timestamps, total file count breakdown, error summary, completion percentage. |

### Automated vs Manual Sections

- **Automated** (generated by `PhaseReporter`): Sections 1, 2 (from code header comments), 3, 5, 6 (from work_log parsing), 7 (from RUN_MANIFEST.yaml), 8.
- **Manual** (require human or agent population): Section 4 (Key Biological Findings) and the Executive Summary narrative. The `PhaseReporter` class provides placeholders for these.

### Template

The canonical template is at `config/templates/PHASE_REPORT_TEMPLATE.md`. It uses `{placeholder}` variables for all dynamic fields.

---

## Error Tracking Protocol

### ERR-XXX ID Format

All errors, warnings, and anomalies receive a unique, sequential ID:

```
ERR-001, ERR-002, ERR-003, ..., ERR-999
```

The prefix is always `ERR-` followed by a zero-padded 3-digit number. IDs are never reused. Even if an error is resolved, its ID is permanently retired.

### Mandatory Fields (Every Error Entry)

| Field | Description |
|-------|-------------|
| **Phase** | Which analysis phase was running (e.g., `foundation_2_gsea`) |
| **Severity** | `Critical` / `Error` / `Warning` / `Info` |
| **Status** | `Open` / `Resolved` / `Deferred` / `Wont_Fix` |
| **Raised By** | Script path or `manual` |
| **Message** | Original error message verbatim |
| **Context** | What was being attempted when the error occurred |
| **Diagnosis** | Root cause analysis |
| **Resolution** | Fix applied or workaround used |
| **Prevention** | How to avoid this error in future runs |

### Entry Template

```markdown
### [ERR-XXX] YYYY-MM-DD HH:MM — Short Description

| Field         | Value                           |
|---------------|---------------------------------|
| **Phase**     | <phase_id>                      |
| **Severity**  | Critical / Error / Warning      |
| **Status**    | Open / Resolved / Deferred      |
| **Raised By** | <script path / manual>          |
| **Message**   | <original error message>        |
| **Context**   | <what was being attempted>      |
| **Diagnosis** | <root cause analysis>           |
| **Resolution**| <fix applied or workaround>     |
| **Prevention**| <how to avoid in future runs>   |
```

### Error Log Location

`results/error_log.md` — one per run. Contains an index table at the top followed by detailed entries.

### Severity Actions

| Severity | Pipeline Impact | Resolution |
|----------|----------------|------------|
| CRITICAL | BLOCK — cannot proceed | Fix before continuing |
| ERROR | Step failed, pipeline continues with mitigation | Resolve or defer; document mitigation |
| WARNING | Non-blocking issue, analysis may be suboptimal | Defer; address when possible |
| INFO | Notable observation | Log only |

### Cross-Reference

Every error in `error_log.md` is referenced in `PHASE_REPORT.md` section 5.3 (Errors & Abnormal Results). The Phase Report shows: ERR ID, description, severity, and resolution status.

---

## Checkpoint Update Protocol

### When to Update checkpoint.yaml

1. **After every phase completes** -- set `last_completed` to the phase that just finished, append its ID to `completed_steps`.
2. **Before any long-running computation** -- update `current_phase` so a crash leaves a clear resume point.
3. **After resolving any ERR-XXX error** -- update `recovery.resume_instructions` if the resolution changed the resume path.

### What to Update

| Field | Update Action |
|-------|--------------|
| `last_completed` | Set to the phase ID that just finished |
| `current_phase` | Set to `"awaiting_user_confirmation"` after a human checkpoint, or the next phase ID |
| `completed_steps` | Append the completed step ID (never remove entries) |
| `next_step` | Set to the ID of the next pending step |
| `state` | Update boolean flags (e.g., `qc_passed: true`, `deg_ready: true`) |
| `outputs.<phase_id>` | List all files created in that phase |
| `recovery.last_successful_checkpoint` | Set to the last phase that completed without errors |
| `recovery.checkpoint_files` | List critical output files needed to verify state on resume |
| `recovery.resume_instructions` | Write a one-sentence instruction for resuming from this checkpoint |

### State Variable Definitions

Standard boolean flags in `checkpoint.state`:

| Variable | Meaning |
|----------|---------|
| `data_loaded` | Raw data successfully loaded |
| `qc_passed` | Expression QC completed, no outlier samples |
| `deg_ready` | Differential expression results available |
| `enrichment_complete` | GO/KEGG/GSEA enrichment finished |
| `immune_complete` | Immune infiltration/deconvolution finished |
| `figures_complete` | All planned figures generated |
| `manuscript_ready` | All IMRAD sections drafted |

### Stale Checkpoint Detection

- On pipeline start, read `checkpoint.yaml` timestamp.
- If older than 24 hours, WARN and require explicit user confirmation before overwriting any state.
- Never auto-resume from a stale checkpoint without confirmation.

---

## Graceful Degradation Pattern (HAS_PACKAGE Flags)

### Core Principle

Every optional R package dependency is guarded by a `HAS_<PKG>` boolean flag. When a package is unavailable, the script degrades gracefully instead of crashing -- it skips the affected step, logs the reason, and continues with remaining steps.

### Standard Template

```r
# At the top of every R analysis script:
load_pkg <- function(pkg) {
  if (requireNamespace(pkg, quietly = TRUE)) {
    suppressPackageStartupMessages(library(pkg, character.only = TRUE))
    return(TRUE)
  } else {
    return(FALSE)
  }
}

HAS_WGCNA  <- load_pkg("WGCNA")
HAS_GSVA   <- load_pkg("GSVA")
HAS_LIMMA  <- load_pkg("limma")

cat("Package status:\n")
cat(sprintf("  WGCNA=%s | GSVA=%s | limma=%s\n", HAS_WGCNA, HAS_GSVA, HAS_LIMMA))
```

### Three Fallback Patterns

1. **Skip with log**: If package missing, skip the step entirely and emit a `[SKIP]` message with install instructions. The step shows as "Deferred" in the Phase Report.

2. **Multiple fallback paths** (try A, then B, then C): First try the full package. If unavailable, try a cached result. If that also fails, use an embedded minimal dataset. This is the msigdbr -> cached -> embedded pattern used in GSEA analysis.

3. **Base R fallback**: Replace a specialized package call with base R equivalents. Example: WGCNA `blockwiseModules()` -> base R `hclust()` + `cutree()`. The Phase Report notes this under "NOT COMPLETED / DEFERRED" with the fallback description.

### Degradation Log

At the end of each script, emit a machine-parseable degradation summary:

```
--- DEGRADATION_SUMMARY ---
DEGRADED|GSVA|Package not installed|Per-sample mean expression used
DEGRADED|limma|Package not installed|Python limma-trend used as alternative
--- END_DEGRADATION_SUMMARY ---
```

Each degraded step maps to:
- An ERR-XXX entry in `error_log.md` (severity: WARNING, status: DEFERRED or RESOLVED).
- A row in PHASE_REPORT.md section 5.2 (NOT COMPLETED / DEFERRED) with the blocker and mitigation.
- A `[FALLBACK]` log line in the phase's log file.

### Reusable Snippet

The generalized graceful fallback pattern is available at:
`code_library/snippets/graceful_fallback.R`

It includes all three fallback patterns with inline documentation, the `load_pkg()` helper, `check_required_packages()`, and the degradation log format.

---

*Last updated: 2026-06-18 | Framework version 1.0.1*
