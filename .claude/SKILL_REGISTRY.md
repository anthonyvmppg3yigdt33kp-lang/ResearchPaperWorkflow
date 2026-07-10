# Skill Registry -- Research Paper Workflow Framework

**Version**: 5.1.0 | **Last Updated**: 2026-07-10 | **Total Skills Mapped**: 31

> v5.1 operating addendum: `research_intent.v1` is the researcher-facing entry
> contract. It produces a scientific assessment, method comparison,
> Figure-first plan, TargetTask, and dashboard before any approved execution.
> TargetTask remains the fail-closed production kernel, while the 20-stage
> PaperLoop remains the manuscript lifecycle truth chain. The legacy skill map
> below is retained for stage routing. Stage 15
> `aigc_humanizer_review` runs after `assemble_manuscript` and before
> `integrity_check`. It is owned by `aigc_humanizer_reviewer` and uses
> `ai-writing-detection`, `humanizer`, and the bundled
> `aigc_humanizer_review` skill. The quality gate set is now 44 gates,
> including `aigc_artifact_scan`, `aigc_style_signal_density`, and
> `humanizer_revision_trace`.

Comprehensive skill-to-stage mapping for the 20-stage Paper Loop Engine, 13 agents, and 3 collaborative teams. Every installable skill in the user's environment is mapped to at least one pipeline stage with trigger conditions, input/output contracts, and agent integration.

---

## Table of Contents

1. [Paper Loop Stages Quick Reference](#paper-loop-stages-quick-reference)
2. [Skill-to-Stage Mapping Table](#skill-to-stage-mapping-table)
3. [Skill Integration Profiles](#skill-integration-profiles)
4. [Skill Chain Diagrams](#skill-chain-diagrams)
5. [Agent-Skill Assignment Matrix](#agent-skill-assignment-matrix)
6. [Team-Skill Composition](#team-skill-composition)
7. [Cross-Cutting Skills](#cross-cutting-skills)
8. [Trigger Keyword Index](#trigger-keyword-index)

---

## Paper Loop Stages Quick Reference

### 20-Stage Pipeline (paper_loop.md)

| Phase | # | Stage ID | Description | Layer | Agent |
|-------|---|----------|-------------|-------|-------|
| **1. Research & Planning** | 1 | `select_topic` | Topic selection & feasibility | Strategy | `research_strategist` |
| | 2 | `target_journal` | Journal targeting & requirements | Strategy | `research_strategist` |
| | 3 | `literature_search` | Systematic literature search & synthesis | Strategy | `literature_reviewer` |
| | 4 | `formulate_hypotheses` | Hypothesis formulation & study design | Strategy | `research_strategist` |
| | 5 | `design_analysis_plan` | Freeze statistical analysis plan before primary analysis | Strategy | `statistician` |
| **2. Data & Methods** | 6 | `data_audit` | Data quality audit & metadata validation | Execution | `data_auditor` |
| | 7 | `figure_planning` | Figure & table planning | Execution | `figure_planner` |
| | 8 | `run_analysis` | Execute data analysis pipeline | Execution | `analysis_executor` |
| | 9 | `verify_methods` | Methods verification & reproducibility | Execution | `pipeline_engineer` |
| **3. Writing** | 10 | `write_methods` | Write Methods section | Execution | `report_writer` |
| | 11 | `write_results` | Write Results section | Execution | `report_writer` |
| | 12 | `write_introduction` | Write Introduction section | Decision | `report_writer` |
| | 13 | `write_discussion` | Write Discussion section | Decision | `report_writer` |
| **4. Assembly & Review** | 14 | `assemble_manuscript` | Assemble full manuscript | Decision | `report_writer` |
| | 15 | `aigc_humanizer_review` | AIGC text hygiene scan and humanizer revision pass | Decision | `aigc_humanizer_reviewer` |
| | 16 | `integrity_check` | Run 44 integrity gates | Decision | `integrity_checker` |
| **5. Revision** | 17 | `internal_review` | Internal peer review simulation | Supervision | `team_orchestrator` |
| | 18 | `apply_revision` | Apply targeted revisions | Supervision | `report_writer` |
| | 19 | `re_review` | Post-revision re-review | Supervision | `team_orchestrator` |
| **6. Finalize** | 20 | `finalize` | Final quality check & export | Supervision | `integrity_checker` |

### 10-Stage Academic Pipeline (paper_writing/SKILL.md, academic-pipeline)

| # | Stage | Engine Action |
|---|-------|---------------|
| 1 | RESEARCH | `deep-research` dispatched |
| 2 | WRITE | `academic-paper` dispatched |
| 2.5 | INTEGRITY | Integrity verification agent |
| 3 | REVIEW | `academic-paper-reviewer` (5 reviewers) |
| 4 | REVISE | `academic-paper` (revision mode) |
| 3' | RE-REVIEW | Re-review verification |
| 4' | RE-REVISE | Final revision pass (max 1 round) |
| 4.5 | FINAL INTEGRITY | Final integrity check (must PASS) |
| 5 | FINALIZE | Format-convert + PDF compilation |
| 6 | PROCESS SUMMARY | Auto-generated process document |

---

## Skill-to-Stage Mapping Table

### Primary Mapping

| # | Skill | 20-Stage Mapping (Primary) | 10-Stage Mapping | Category | Priority |
|---|-------|---------------------------|------------------|----------|----------|
| 1 | `academic-paper` | 9,10,11,12,13,16 | 2 (WRITE), 4 (REVISE) | Core Writing | CRITICAL |
| 2 | `academic-paper-polish` | 9,10,11,12,13,16,18 | 2 (WRITE), 4 (REVISE), 5 (FINALIZE) | Language | HIGH |
| 3 | `academic-paper-reviewer` | 14,15,17 | 3 (REVIEW), 3' (RE-REVIEW) | Quality | CRITICAL |
| 4 | `academic-pipeline` | 1-18 (full pipeline) | 1-6 (orchestrator) | Orchestration | CRITICAL |
| 5 | `scientific-writing` | 9,10,11,12,16 | 2 (WRITE), 4 (REVISE) | Core Writing | CRITICAL |
| 6 | `humanizer` | 9,10,11,12,13,16,18 | 2,4,5 | Language | MEDIUM |
| 7 | `nature-writing` | 9,10,11,12,13 | 2 (WRITE) | Core Writing | HIGH |
| 8 | `nature-polishing` | 9,10,11,12,13,16,18 | 2,4,5 | Language | HIGH |
| 9 | `nature-figure` | 6,7,13 | 2 (WRITE) | Figures | HIGH |
| 10 | `nature-citation` | 3,11,12,13 | 1 (RESEARCH), 2 (WRITE) | References | HIGH |
| 11 | `nature-reader` | 3 (literature digestion) | 1 (RESEARCH) | Research | MEDIUM |
| 12 | `nature-response` | 15,16,17 | 4 (REVISE), 3' (RE-REVIEW) | Revision | HIGH |
| 13 | `nature-data` | 8,9,13,18 | 2 (WRITE), 5 (FINALIZE) | Compliance | HIGH |
| 14 | `nature-paper2ppt` | 18 (post-finalize) | 5 (FINALIZE) | Dissemination | LOW |
| 15 | `nature-academic-search` | 3 | 1 (RESEARCH) | Research | HIGH |
| 16 | `deep-research` | 1,2,3,4 | 1 (RESEARCH) | Research | CRITICAL |
| 17 | `paper-glance` | 3,15 | 1 (RESEARCH), 3 (REVIEW) | Research/Review | MEDIUM |
| 18 | `summarize` | 3 | 1 (RESEARCH) | Research | LOW |
| 19 | `ai-writing-detection` | 13,14,18 | 2.5 (INTEGRITY), 4.5 (FINAL INTEGRITY) | Quality | MEDIUM |
| 20 | `remove-ai-flavor` | 9,10,11,12,13,16 | 2,4 | Language | LOW |
| 21 | `research-paper-writing` | 9,10,11,12 | 2 (WRITE) | Core Writing | MEDIUM |
| 22 | `tavily-research` | 1,2,3 | 1 (RESEARCH) | Research | MEDIUM |
| 23 | `find-skills` | 1 (pre-pipeline) | N/A | Meta | LOW |
| 24 | `ccg` (all subskills) | 7,8,14,17,18 | 2.5,4.5 | Quality | HIGH |
| 25 | `wgcna-analyst` | 7 | 2 (WRITE) | Analysis | DOMAIN |
| 26 | `darwin-skill` | Meta (skill optimization) | N/A | Meta | LOW |
| 27 | `skill-creator` | Meta (skill creation) | N/A | Meta | LOW |
| 28 | `agent-browser` | 2 (journal research), 3 | 1 (RESEARCH) | Research | LOW |

### Priority Legend

| Priority | Meaning |
|----------|---------|
| **CRITICAL** | Pipeline cannot complete without this skill |
| **HIGH** | Strongly recommended; significant quality degradation without it |
| **MEDIUM** | Valuable enhancement; pipeline completes without it |
| **LOW** | Optional / situational / post-pipeline |
| **DOMAIN** | Required only for specific research domains |

---

## Skill Integration Profiles

### 1. `academic-paper` -- 12-Agent Academic Paper Writing Pipeline

| Property | Value |
|----------|-------|
| **Paper Loop Stages** | 9 (`write_methods`), 10 (`write_results`), 11 (`write_introduction`), 12 (`write_discussion`), 13 (`assemble_manuscript`), 16 (`apply_revision`) |
| **Category** | Core Writing |
| **Priority** | CRITICAL |
| **Integrated Agent** | `report_writer` |

**When to Invoke:**
- User says "write paper", "academic paper", "guide my paper", "draft manuscript", "section writing"
- User requests any IMRAD section writing from scratch
- User requests format conversion (LaTeX to DOCX, Markdown to PDF)
- User requests citation format checking or AI disclosure statements

**Modes:**
| Mode | Stage(s) | Description |
|------|----------|-------------|
| `full` | 9-13 | Complete paper from outline to assembled manuscript |
| `plan` | Pre-9 | Generate structured IMRAD outline before writing |
| `outline` | Pre-9 | Bullet-point skeleton for approval |
| `revision` | 16 | Targeted revision from reviewer comments |
| `revision-coach` | 16 | Coaching mode for self-directed revision |
| `abstract` | 13 | Standalone abstract generation/writing |
| `lit-review` | 3,11 | Literature review section drafting |
| `format-convert` | 13,18 | LaTeX/Markdown/DOCX/PDF conversion |
| `citation-check` | 14 | Citation completeness verification |
| `disclosure` | 13,18 | AI disclosure statement generation |

**Input Contract:**
- Research question / hypothesis (from stages 1-4)
- Analysis results and figures (from stages 5-8)
- Target journal configuration
- Paper type specification
- Citation format preference
- Existing draft (for revision mode)

**Output Contract:**
- Complete manuscript sections (Markdown/LaTeX)
- Claims-to-evidence binding table
- Formatted manuscript file (.tex, .docx, .pdf)
- Citation audit report

---

### 2. `academic-paper-polish` -- Academic Prose Polishing

| Property | Value |
|----------|-------|
| **Paper Loop Stages** | 9,10,11,12,13,16,18 |
| **Category** | Language & Style |
| **Priority** | HIGH |
| **Integrated Agent** | `report_writer` |

**When to Invoke:**
- After initial draft completion (stages 9-13)
- Before assemble_manuscript (stage 13)
- After apply_revision (stage 16)
- During finalize (stage 18)

**Input:** Raw or rough manuscript section text
**Output:** Polished academic prose with improved fluency, consistent register, and discipline-appropriate vocabulary

**Integration Pattern:**
```
write_methods (9) → academic-paper-polish → write_results (10) → academic-paper-polish → ...
→ assemble_manuscript (13) → academic-paper-polish (full pass)
```

---

### 3. `academic-paper-reviewer` -- Multi-Perspective Paper Review

| Property | Value |
|----------|-------|
| **Paper Loop Stages** | 14 (`integrity_check`), 15 (`internal_review`), 17 (`re_review`) |
| **Category** | Quality Assurance |
| **Priority** | CRITICAL |
| **Integrated Agent** | `integrity_checker` |

**When to Invoke:**
- After integrity_check passes (stage 14 → 15 transition)
- Before apply_revision to generate revision targets
- After apply_revision for re_review (stage 17)
- Anytime user says "review my paper", "peer review", "simulate review"

**Reviewer Personas (5):**
1. **Editor-in-Chief (EIC)** -- Overall merit, novelty, fit
2. **Reviewer 1** -- Domain expert, deep methodological scrutiny
3. **Reviewer 2** -- Cross-disciplinary perspective, clarity, accessibility
4. **Reviewer 3** -- Statistical rigor, data integrity
5. **Devil's Advocate** -- Finds weaknesses others miss, challenges assumptions

**Modes:**
| Mode | Use Case |
|------|----------|
| `full` | Complete 5-reviewer simulation |
| `re-review` | Verify previous comments are addressed |
| `quick` | Rapid assessment (EIC only) |
| `methodology` | Methods-only deep dive |
| `socratic` | Guided self-review questions |
| `calibration` | Measure reviewer accuracy against known outcomes |

**Input:** Assembled manuscript + figures + supplementary materials
**Output:** 5 structured review reports + EIC decision letter + revision priority matrix

---

### 4. `academic-pipeline` -- Full 10-Stage Orchestrator

| Property | Value |
|----------|-------|
| **Paper Loop Stages** | 1-18 (full lifecycle orchestrator) |
| **Category** | Orchestration |
| **Priority** | CRITICAL |
| **Integrated Agent** | `team_orchestrator` |

**When to Invoke:**
- "academic pipeline", "research to paper", "full paper workflow"
- "paper pipeline", "end-to-end paper"
- "research-to-publication", "complete paper workflow"

**Pipeline Stages Orchestrated:**
```
RESEARCH → WRITE → INTEGRITY → REVIEW → REVISE → RE-REVIEW → RE-REVISE → FINAL INTEGRITY → FINALIZE → PROCESS SUMMARY
```

**Input:** Research idea + domain + target journal
**Output:** Submission-ready manuscript package + process documentation

**Key Feature:** Mandatory integrity verification at two points (pre-review and pre-finalize). No stage advances without gate clearance.

---

### 5. `scientific-writing` -- IMRAD Scientific Manuscript Writing

| Property | Value |
|----------|-------|
| **Paper Loop Stages** | 9,10,11,12,16 |
| **Category** | Core Writing |
| **Priority** | CRITICAL |
| **Integrated Agent** | `report_writer` |

**When to Invoke:**
- Writing any IMRAD section from results/analysis outputs
- User says "write methods section", "draft results", "scientific manuscript"
- Chinese: "写方法", "写结果", "写讨论"

**Two-Stage Process:**
1. Section outline with key points + research-lookup for evidence
2. Convert to flowing prose paragraphs (never bullet points in final output)

**Supported Structures:** IMRAD standard; adaptable to journal-specific variations

**Reporting Guidelines:** CONSORT, STROBE, PRISMA, STREGA, TRIPOD

**Input:** Analysis results, figures, hypotheses, literature synthesis
**Output:** Complete prose sections with inline citations, figure/table references, and evidence annotations

---

### 6. `humanizer` -- Remove AI-Generated Writing Signs

| Property | Value |
|----------|-------|
| **Paper Loop Stages** | 9,10,11,12,13,16,18 |
| **Category** | Language & Style |
| **Priority** | MEDIUM |
| **Integrated Agent** | `report_writer` |

**When to Invoke:**
- After AI-assisted drafting to naturalize prose
- Before internal review (stage 15)
- Before finalize (stage 18)
- Anytime user says "remove AI signs", "make it sound human", "naturalize"

**Patterns Detected & Fixed:**
- Inflated symbolism and promotional language
- Superficial "-ing" analyses
- Vague attributions ("studies show", "it is believed")
- Em dash overuse
- Rule of three constructions
- AI vocabulary words ("delve", "tapestry", "landscape", "crucial")
- Excessive conjunctive phrases

**Input:** Draft manuscript text (any section)
**Output:** Naturalized academic prose preserving all factual claims and citations

---

### 7. `nature-writing` -- Nature-Style Manuscript Drafting

| Property | Value |
|----------|-------|
| **Paper Loop Stages** | 9,10,11,12,13 |
| **Category** | Core Writing (Nature/CNS style) |
| **Priority** | HIGH |
| **Integrated Agent** | `report_writer` |

**When to Invoke:**
- Target journal is Nature/CNS-family
- User provides claims/results/figures and wants a complete section draft
- "写Nature风格论文", "Nature-style manuscript"
- Also triggers on general academic writing when no journal is specified

**Key Distinction from `scientific-writing`:**
`nature-writing` drafts from raw claims/results/notes (bottom-up), while `scientific-writing` is more structured (top-down outline-first). Both produce IMRAD prose.

**Input:** Author-provided claims, results summary, figures, notes, or Chinese draft
**Output:** Nature-leaning complete manuscript sections with argument flow

---

### 8. `nature-polishing` -- Nature-Leaning English Prose Polish

| Property | Value |
|----------|-------|
| **Paper Loop Stages** | 9,10,11,12,13,16,18 |
| **Category** | Language & Style (Nature/CNS quality) |
| **Priority** | HIGH |
| **Integrated Agent** | `report_writer` |

**When to Invoke:**
- Polishing existing draft to Nature-level English
- Translating Chinese academic draft to publication-quality English
- LaTeX layout/typesetting fixes
- "润色", "改写", "学术英语", "英文润色"
- Also triggers on general academic writing without "Nature" keyword

**Key Feature:** Uses curated patterns from actual Nature/Nature Communications articles + Academic Phrasebank

**Input:** Manuscript paragraph, abstract, introduction, results, discussion, conclusion, title, or methods section
**Output:** Polished Nature-leaning English prose; optional LaTeX layout fixes

---

### 9. `nature-figure` -- Submission-Grade Figure Workflow

| Property | Value |
|----------|-------|
| **Paper Loop Stages** | 6 (`figure_planning`), 7 (`run_analysis`), 13 (`assemble_manuscript`) |
| **Category** | Figures & Visualization |
| **Priority** | HIGH |
| **Integrated Agent** | `figure_planner` |

**When to Invoke:**
- Creating new manuscript figures from data
- Revising/auditing existing figures for journal compliance
- "论文配图", "科研绘图", "画图", "作图", "出图"
- Also triggers on general academic figure requests without "Nature" keyword

**Backends:** Python (matplotlib/seaborn) or R (ggplot2/patchwork/ComplexHeatmap)

**Workflow:**
1. Define figure's conclusion (what should the reader conclude?)
2. Plan evidence logic (what data supports this conclusion?)
3. Set export targets (resolution, format, color space)
4. Assess review risks (alternative interpretations?)
5. Generate → Preview → Export → QA

**Output Specs:**
- 300+ DPI (600 DPI for line art)
- TIFF/PDF/SVG formats
- Colorblind-safe palettes (viridis, cividis, Okabe-Ito)
- CMYK for print, RGB for online

---

### 10. `nature-citation` -- Nature/CNS Citation Insertion

| Property | Value |
|----------|-------|
| **Paper Loop Stages** | 3 (`literature_search`), 11 (`write_introduction`), 12 (`write_discussion`), 13 (`assemble_manuscript`) |
| **Category** | References & Citations |
| **Priority** | HIGH |
| **Integrated Agent** | `literature_reviewer` |

**When to Invoke:**
- Adding citations to a manuscript paragraph
- Finding Nature/CNS support for specific claims
- "分段引用", "自动给出引用", "补引用", "找引用"
- Also triggers on general academic citation needs without "Nature" keyword

**Scope:** Nature Portfolio journals, AAAS Science family, Cell Press (flagship + subjournals)

**Input:** Manuscript text passage needing citations
**Output:** Text with inline citations mapped to verified references; export in EndNote/RIS/ENW/Zotero RDF

---

### 11. `nature-reader` -- Chinese-English Side-by-Side Paper Reader

| Property | Value |
|----------|-------|
| **Paper Loop Stages** | 3 (understanding existing literature) |
| **Category** | Research & Comprehension |
| **Priority** | MEDIUM |
| **Integrated Agent** | `literature_reviewer` |

**When to Invoke:**
- Reading/translating a PDF paper for literature survey
- Building a bilingual paper reader for team reference
- "读论文", "精读论文", "论文翻译", "文献翻译"
- Also triggers on general paper-reading requests without "Nature" keyword

**Input:** PDF, DOI, arXiv ID, publisher HTML, or pasted text
**Output:** Chinese-English side-by-side Markdown with figures/tables in position, source anchors for every block

---

### 12. `nature-response` -- Reviewer Response Letter

| Property | Value |
|----------|-------|
| **Paper Loop Stages** | 15 (`internal_review`), 16 (`apply_revision`), 17 (`re_review`) |
| **Category** | Revision & Response |
| **Priority** | HIGH |
| **Integrated Agent** | `report_writer` (for response drafting), `integrity_checker` (for response review) |

**When to Invoke:**
- Reviewer comments or editor decision letter received
- Drafting point-by-point response
- "审稿意见回复", "逐点回复", "修回信", "rebuttal letter"
- Also triggers on general peer-review response needs without "Nature" keyword

**Input:** Reviewer comments, editor decision letter, revised manuscript
**Output:** Structured point-by-point response letter with change locations

---

### 13. `nature-data` -- Data Availability Statement Preparation

| Property | Value |
|----------|-------|
| **Paper Loop Stages** | 8 (`verify_methods`), 9 (`write_methods`), 13 (`assemble_manuscript`), 18 (`finalize`) |
| **Category** | Compliance & Reproducibility |
| **Priority** | HIGH |
| **Integrated Agent** | `pipeline_engineer`, `report_writer` |

**When to Invoke:**
- Preparing data availability statement for submission
- Auditing existing statement for completeness
- "数据可用性声明", "数据共享", "代码可用性"
- Also triggers on general data-statement needs without "Nature" keyword

**Input:** Data sources, accession numbers, repository information
**Output:** Nature-ready Data Availability statement, data citation records, FAIR metadata checklist

---

### 14. `nature-paper2ppt` -- Paper-to-Presentation Conversion

| Property | Value |
|----------|-------|
| **Paper Loop Stages** | 18 (post-finalize, dissemination) |
| **Category** | Dissemination |
| **Priority** | LOW |
| **Integrated Agent** | `report_writer` (uses manuscript output) |

**When to Invoke:**
- "论文做PPT", "组会PPT", "文献汇报", "学术汇报"
- Building presentation from finished paper
- Also triggers on general academic presentation requests without "Nature" keyword

**Input:** Paper PDF, preprint, article text, abstract, or figure legends
**Output:** Chinese PPTX with paper story flow, selected figures, speaker notes

---

### 15. `nature-academic-search` -- Multi-Source Literature Search

| Property | Value |
|----------|-------|
| **Paper Loop Stages** | 3 (`literature_search`) |
| **Category** | Research |
| **Priority** | HIGH |
| **Integrated Agent** | `literature_reviewer` |

**When to Invoke:**
- Systematic literature search across multiple databases
- Citation file management (.nbib/.ris/.bib conversion)
- Reference management (BibTeX, related articles, ID conversion)
- "文献检索", "查文献", "找文献", "文献综述检索"
- Also triggers on general literature-search needs without "Nature" keyword

**MCP Tools Used:** PubMed, CrossRef, arXiv, Scopus, ScienceDirect

**Input:** Search query, database preferences, filters
**Output:** Organized citation library (.bib), search strategy documentation, deduplicated reference list

---

### 16. `deep-research` -- Enterprise-Grade Multi-Source Research

| Property | Value |
|----------|-------|
| **Paper Loop Stages** | 1 (`select_topic`), 2 (`target_journal`), 3 (`literature_search`), 4 (`formulate_hypotheses`) |
| **Category** | Research |
| **Priority** | CRITICAL |
| **Integrated Agent** | `research_strategist`, `literature_reviewer` |

**When to Invoke:**
- "deep research", "comprehensive analysis", "research report"
- "compare X vs Y", "analyze trends", "state of the art"
- Phase 1 of pipeline (topic, gap, feasibility)

**Features:**
- Multi-source synthesis with citation tracking
- Source credibility scoring
- Structured reports with confidence levels
- Cross-verification of key claims

**Input:** Research question or topic
**Output:** Citation-backed research report with source credibility scores, gap analysis, and trend synthesis

**NOT for:** Simple lookups, debugging, or questions answerable with 1-2 searches

---

### 17. `paper-glance` -- Universal Paper Processing

| Property | Value |
|----------|-------|
| **Paper Loop Stages** | 3 (literature digestion), 15 (internal review -- paper analysis) |
| **Category** | Research / Review |
| **Priority** | MEDIUM |
| **Integrated Agent** | `literature_reviewer`, `integrity_checker` |

**When to Invoke:**
- User uploads a paper PDF or pastes paper text
- "帮我看这篇论文", "paper analysis", "analyze this paper"
- Chinese: "论文", "paper", "文献", "arxiv"
- **MUST trigger on any PDF upload or paper text paste**

**Functions:**
- Deep analysis report (methods, findings, strengths, weaknesses)
- Mind map generation
- Review comments (simulated peer review)
- Promotional script generation
- Podcast audio generation

**Input:** Paper PDF, pasted text, or URL
**Output:** Multi-format analysis deliverables

---

### 18. `summarize` -- Text/Transcript Summarization

| Property | Value |
|----------|-------|
| **Paper Loop Stages** | 3 (quick paper digestion during literature search) |
| **Category** | Research |
| **Priority** | LOW |
| **Integrated Agent** | `literature_reviewer` |

**When to Invoke:**
- Quick summarization of a paper, podcast, or transcript
- Fallback for "transcribe this YouTube/video"
- During literature screening for rapid relevance assessment

**Input:** URL, podcast file, or local text file
**Output:** Concise summary/extraction

---

### 19. `ai-writing-detection` -- AI Writing Pattern Detection

| Property | Value |
|----------|-------|
| **Paper Loop Stages** | 13 (`assemble_manuscript`), 14 (`integrity_check`), 18 (`finalize`) |
| **Category** | Quality Assurance |
| **Priority** | MEDIUM |
| **Integrated Agent** | `integrity_checker` |

**When to Invoke:**
- Checking manuscript for AI-generated patterns before submission
- Understanding detection patterns (educational use)
- During integrity check to flag potential AI writing artifacts

**Output:** Detection pattern report with vocabulary lists, structural patterns, model-specific fingerprints, and false positive prevention guidance

---

### 20. `remove-ai-flavor` -- Chinese AI-Flavor Removal

| Property | Value |
|----------|-------|
| **Paper Loop Stages** | 9,10,11,12,13,16 (Chinese-language paper variants) |
| **Category** | Language & Style (Chinese-specific) |
| **Priority** | LOW |
| **Integrated Agent** | `report_writer` |

**When to Invoke:**
- Chinese-language academic writing (公众号, 自媒体, 演讲稿)
- "去AI味", "去除AI痕迹", "不像AI写的"
- NOT for English academic papers (use `humanizer`)

**Target Patterns:** Template-like writing, buzzword stacking, em dash abuse, bullet stacking, forced bolding

---

### 21. `research-paper-writing` -- ML/CV/NLP Paper Writing

| Property | Value |
|----------|-------|
| **Paper Loop Stages** | 9,10,11,12 |
| **Category** | Core Writing (CS domain-specific) |
| **Priority** | MEDIUM |
| **Integrated Agent** | `report_writer` |

**When to Invoke:**
- Writing ML/CV/NLP conference/journal papers
- Drafting/revising Abstract, Introduction, Related Work, Method, Experiments, Conclusion
- Polishing figures/tables for CS venues
- Self-review before CS conference submission

**Key Difference from `scientific-writing`:** Tailored for CS paper structure (Related Work instead of integrated literature review, Experiments section, claim-support alignment for reviewer-facing presentation)

---

### 22. `tavily-research` -- AI-Powered Research with Citations

| Property | Value |
|----------|-------|
| **Paper Loop Stages** | 1,2,3 |
| **Category** | Research |
| **Priority** | MEDIUM |
| **Integrated Agent** | `research_strategist`, `literature_reviewer` |

**When to Invoke:**
- "research", "investigate", "analyze in depth", "compare X vs Y"
- "market analysis", "literature review" (general, non-biomedical)
- Cross-disciplinary research where multiple source types are needed

**Input:** Research question or comparison topic
**Output:** Structured multi-source report with explicit citations (30-120 seconds)

**Note:** For biomedical literature, prefer `nature-academic-search` (PubMed-backed). `tavily-research` is better for cross-disciplinary or non-academic research.

---

### 23. `find-skills` -- Skill Discovery & Installation

| Property | Value |
|----------|-------|
| **Paper Loop Stages** | Pre-pipeline (environment setup) |
| **Category** | Meta |
| **Priority** | LOW |
| **Integrated Agent** | `team_orchestrator` |

**When to Invoke:**
- "how do I do X", "find a skill for X"
- "is there a skill that can..."
- Extending framework capabilities

---

### 24. `ccg` -- Quality Gates & Multi-Agent Orchestration

| Property | Value |
|----------|-------|
| **Paper Loop Stages** | 7 (`run_analysis` -- code quality), 8 (`verify_methods` -- reproducibility), 14 (`integrity_check`), 17 (`re_review`), 18 (`finalize`) |
| **Category** | Quality Assurance |
| **Priority** | HIGH |
| **Integrated Agent** | `integrity_checker`, `analysis_executor`, `pipeline_engineer` |

**Subskills Used in Paper Workflow:**

| CCG Subskill | Paper Loop Usage |
|-------------|-----------------|
| `ccg:review` | Code review during `run_analysis` (stage 7) |
| `ccg:test` | Test generation for analysis code |
| `ccg:commit` | Version control for analysis scripts |
| `ccg:debug` | Debug analysis pipeline failures |
| `ccg:team-plan` | Multi-agent coordination for complex analysis |
| `ccg:team-exec` | Parallel execution of independent analysis tasks |
| `ccg:team-review` | Cross-model review of analysis outputs |
| `ccg:workflow` | Full multi-model dev workflow (for analysis code) |

**Auto-Trigger Rules:**
- Code changes >30 lines → `/verify-change` → `/verify-quality`
- New module created → `/gen-docs` → `/verify-module`
- Security changes → `/verify-security`

---

### 25. `wgcna-analyst` -- WGCNA Analysis Specialist

| Property | Value |
|----------|-------|
| **Paper Loop Stages** | 7 (`run_analysis`) |
| **Category** | Analysis (Domain: Bioinformatics) |
| **Priority** | DOMAIN |
| **Integrated Agent** | `analysis_executor` |

**When to Invoke (Auto-Trigger Keywords):**
- WGCNA, 共表达网络, co-expression network
- 模块分析, module analysis
- pickSoftThreshold, blockwiseModules, 软阈值
- hub gene, hub基因, 特征基因, module eigengene
- module-trait, 模块-性状, 免疫浸润+WGCNA
- TOM矩阵, scale-free topology, signedKME

**Input:** Expression matrix, trait data
**Output:** Module assignments, hub genes, module-trait correlations, visualizations, downstream ML-ready feature lists

---

### 26. `darwin-skill` -- Autonomous Skill Optimizer

| Property | Value |
|----------|-------|
| **Paper Loop Stages** | Meta (skill quality improvement) |
| **Category** | Meta |
| **Priority** | LOW |
| **Integrated Agent** | N/A (operates on skills, not papers) |

**When to Invoke:**
- "优化skill", "skill评分", "自动优化"
- "skill质量检查", "skill review", "skill打分"

---

### 27. `skill-creator` -- Skill Creation & Modification

| Property | Value |
|----------|-------|
| **Paper Loop Stages** | Meta (framework extension) |
| **Category** | Meta |
| **Priority** | LOW |
| **Integrated Agent** | N/A (operates on skills, not papers) |

**When to Invoke:**
- Creating new domain-specific skills for the framework
- Modifying existing skill behavior
- Benchmarking skill performance

---

### 28. `agent-browser` -- Web Automation for Research

| Property | Value |
|----------|-------|
| **Paper Loop Stages** | 2 (journal website research), 3 (web-based literature sources) |
| **Category** | Research |
| **Priority** | LOW |
| **Integrated Agent** | `research_strategist` |

**When to Invoke:**
- Journal Guide for Authors page interaction
- Submission portal navigation
- Web-based database queries not covered by MCP tools

---

## Skill Chain Diagrams

### Chain 1: Full Topic-to-Submission Pipeline (28 Skills)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    RESEARCH PAPER WORKFLOW — SKILL CHAIN                     │
│                    Full 18-Stage Pipeline with Skill Mapping                 │
└─────────────────────────────────────────────────────────────────────────────┘

PHASE 1: RESEARCH & PLANNING (Stages 1-4)
═══════════════════════════════════════════

  [User Idea]
      │
      ▼
  ┌─────────────┐     ┌──────────────────┐     ┌─────────────────────┐
  │ find-skills  │────▶│  deep-research   │────▶│ nature-academic-    │
  │ (discovery)  │     │  (gap analysis)  │     │ search (literature) │
  └─────────────┘     └──────────────────┘     └─────────────────────┘
                              │                          │
                              ▼                          ▼
                      ┌──────────────┐          ┌──────────────┐
                      │tavily-research│          │ nature-reader │
                      │(cross-domain) │          │(paper digest) │
                      └──────────────┘          └──────────────┘
                              │                          │
                              ▼                          ▼
                      ┌──────────────┐          ┌──────────────┐
                      │  summarize   │          │ paper-glance  │
                      │ (quick scan) │          │(deep analysis)│
                      └──────────────┘          └──────────────┘
                                                       │
                                                       ▼
                                              ┌─────────────────┐
                                              │ agent-browser   │
                                              │(journal portals)│
                                              └─────────────────┘

PHASE 2: DATA & METHODS (Stages 5-8)
════════════════════════════════════

  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
  │  ccg:review  │     │nature-figure │     │  wgcna-      │
  │  ccg:debug   │◀───▶│(figure plan) │     │  analyst     │
  │  ccg:test    │     └──────────────┘     │(if WGCNA)    │
  └──────────────┘            │             └──────────────┘
                              ▼                     │
                      ┌──────────────┐              │
                      │  ccg:commit  │              │
                      │(version ctrl)│              │
                      └──────────────┘              │
                              │                     │
                              ▼                     ▼
                      ┌──────────────────────────────────┐
                      │         ccg:team-exec             │
                      │  (parallel analysis execution)    │
                      └──────────────────────────────────┘

PHASE 3: WRITING (Stages 9-12)
═══════════════════════════════

  ┌────────────────┐
  │ academic-paper  │◀────── Paper Loop Engine Dispatch
  │  (12-agent)     │
  └──────┬─────────┘
         │
         ├──▶ scientific-writing (IMRAD prose)
         │         │
         │         ├──▶ research-paper-writing (ML/CV/NLP variant)
         │         │
         │         └──▶ nature-writing (Nature/CNS style)
         │
         ├──▶ nature-citation (reference insertion)
         │
         └──▶ nature-data (data availability statement)
                      │
                      ▼
  ┌──────────────────────────────────────────────────────┐
  │               LANGUAGE POLISHING LAYER               │
  │                                                      │
  │  ┌──────────────────┐  ┌──────────────┐             │
  │  │nature-polishing   │  │  humanizer   │             │
  │  │(Nature-leaning)   │  │(AI sign rem) │             │
  │  └──────────────────┘  └──────────────┘             │
  │                                                      │
  │  ┌──────────────────┐  ┌──────────────┐             │
  │  │academic-paper-    │  │remove-ai-    │             │
  │  │polish (standard)  │  │flavor (ZH)   │             │
  │  └──────────────────┘  └──────────────┘             │
  └──────────────────────────────────────────────────────┘

PHASE 4: ASSEMBLY & REVIEW (Stages 13-15)
═════════════════════════════════════════

  ┌───────────────────┐
  │ academic-paper     │──▶ assemble_manuscript (13)
  │ (format-convert)   │
  └───────────────────┘
            │
            ▼
  ┌───────────────────────────────┐
  │    INTEGRITY CHECK (14)       │
  │                               │
  │  ┌───────────────────────┐    │
  │  │ai-writing-detection   │    │
  │  │(AI pattern scan)      │    │
  │  └───────────────────────┘    │
  │                               │
  │  ┌───────────────────────┐    │
  │  │ccg:team-review        │    │
  │  │(cross-model audit)    │    │
  │  └───────────────────────┘    │
  └───────────────────────────────┘
            │
            ▼
  ┌───────────────────────────────┐
  │    INTERNAL REVIEW (15)       │
  │                               │
  │  ┌───────────────────────┐    │
  │  │academic-paper-reviewer│    │
  │  │(5-reviewer simulation)│    │
  │  └───────────────────────┘    │
  │                               │
  │  ┌───────────────────────┐    │
  │  │paper-glance           │    │
  │  │(alternative review)   │    │
  │  └───────────────────────┘    │
  └───────────────────────────────┘

PHASE 5: REVISION (Stages 16-17)
═════════════════════════════════

  ┌───────────────────┐
  │ nature-response   │──────▶ Draft response letter
  │(rebuttal draft)   │
  └───────────────────┘
            │
            ▼
  ┌───────────────────┐
  │ academic-paper     │──────▶ apply_revision (16)
  │ (revision mode)    │
  └───────────────────┘
            │
            ▼
  ┌───────────────────────────────┐
  │ academic-paper-reviewer       │──────▶ re_review (17)
  │ (re-review mode)              │
  └───────────────────────────────┘

PHASE 6: FINALIZE (Stage 18)
═════════════════════════════

  ┌──────────────────────────────────────────────────────┐
  │                 FINAL QUALITY GATES                   │
  │                                                      │
  │  ┌────────────┐  ┌────────────┐  ┌────────────────┐ │
  │  │ccg:review  │  │ humanizer  │  │nature-polishing│ │
  │  │(final code)│  │(final text)│  │(final prose)   │ │
  │  └────────────┘  └────────────┘  └────────────────┘ │
  │                                                      │
  │  ┌──────────────────────────────────────────────┐    │
  │  │         academic-paper (format-convert)       │    │
  │  │         → LaTeX/PDF/DOCX final output         │    │
  │  └──────────────────────────────────────────────┘    │
  └──────────────────────────────────────────────────────┘
            │
            ▼
  ┌───────────────────┐     ┌───────────────────┐
  │ nature-paper2ppt  │     │  nature-data      │
  │(presentation gen) │     │(final DA audit)   │
  └───────────────────┘     └───────────────────┘
            │                       │
            ▼                       ▼
  ┌─────────────────────────────────────────────────┐
  │              SUBMISSION PACKAGE                  │
  │  Manuscript + Figures + Supplementary + Cover    │
  │  Letter + Data Statement + Code Statement        │
  │  + Response Letter (if revision)                 │
  └─────────────────────────────────────────────────┘
```

### Chain 2: Research-Only Path (Stages 1-4)

```
deep-research ──▶ nature-academic-search ──▶ tavily-research
       │                    │                      │
       ▼                    ▼                      ▼
  gap analysis       citation library        cross-domain check
       │                    │                      │
       └────────────────────┼──────────────────────┘
                            ▼
                      paper-glance ──▶ nature-reader ──▶ summarize
                            │
                            ▼
                  Literature Synthesis Report
```

### Chain 3: Writing-Only Path (Stages 9-13, from existing results)

```
Analysis Results + Figures
          │
          ▼
  scientific-writing ──▶ nature-writing ──▶ research-paper-writing
          │                    │                      │
          └────────────────────┼──────────────────────┘
                               ▼
                        academic-paper
                    (12-agent writing pipeline)
                               │
                    ┌──────────┼──────────┐
                    ▼          ▼          ▼
            nature-citation  nature-data  nature-figure
                    │          │          │
                    └──────────┼──────────┘
                               ▼
                    ┌─────────────────────┐
                    │  POLISHING TRIAGE   │
                    │                     │
                    │  Nature target?      │
                    │  ├─ YES → nature-polishing
                    │  └─ NO  → academic-paper-polish
                    │                     │
                    │  AI-assisted draft?  │
                    │  ├─ YES → humanizer  │
                    │  └─ NO  → skip       │
                    │                     │
                    │  Chinese text?       │
                    │  ├─ YES → remove-ai-flavor
                    │  └─ NO  → skip       │
                    └─────────────────────┘
                               │
                               ▼
                    Assembled Manuscript
```

### Chain 4: Review-to-Revision Path (Stages 14-17)

```
Assembled Manuscript
          │
          ▼
  integrity_check (14)
          │
          ├── ai-writing-detection (scan)
          ├── ccg:team-review (code audit)
          └── academic-paper (citation-check mode)
          │
          ▼
  internal_review (15)
          │
          ├── academic-paper-reviewer (5 reviewers)
          └── paper-glance (alternative analysis)
          │
          ▼
  Review Reports + Revision Priority Matrix
          │
          ▼
  nature-response (draft rebuttal)
          │
          ▼
  apply_revision (16)
          │
          └── academic-paper (revision mode)
          │       │
          │       ├── scientific-writing (rewrite sections)
          │       ├── nature-polishing (re-polish)
          │       └── humanizer (re-naturalize)
          │
          ▼
  re_review (17)
          │
          └── academic-paper-reviewer (re-review mode)
          │
          ▼
  [If pass] → finalize (18)
  [If fail] → apply_revision (16) [max 5 rounds]
```

### Chain 5: Domain-Specific Analysis Integration

```
                    run_analysis (7)
                          │
        ┌─────────────────┼─────────────────┐
        ▼                 ▼                 ▼
  ┌──────────┐    ┌──────────────┐   ┌──────────────┐
  │ wgcna-   │    │  ccg:team-   │   │  ccg:debug   │
  │ analyst  │    │  exec        │   │  (failures)  │
  │(WGCNA)   │    │(parallelize) │   └──────────────┘
  └──────────┘    └──────────────┘
        │                 │
        ▼                 ▼
  ┌──────────────────────────────────────────┐
  │         RESEARCH DOMAIN ROUTING          │
  │                                          │
  │  Bioinformatics → statistical_testing    │
  │       + pathway_inference                │
  │       + multi_omics                      │
  │                                          │
  │  Spatial → spatial_analysis              │
  │       + figure_planning                  │
  │                                          │
  │  ML/AI → research-paper-writing          │
  │       + statistical_testing              │
  │                                          │
  │  Clinical → statistical_testing          │
  │       + scientific-writing               │
  │       (CONSORT/STROBE compliance)        │
  └──────────────────────────────────────────┘
```

---

## Agent-Skill Assignment Matrix

| Agent | Primary Skills | Secondary Skills | Tool Permissions |
|-------|---------------|-----------------|-----------------|
| **research_strategist** | `deep-research`, `tavily-research` | `find-skills`, `agent-browser` | MCP search tools, no code execution |
| **literature_reviewer** | `nature-academic-search`, `deep-research` | `nature-reader`, `paper-glance`, `summarize`, `nature-citation` | PubMed, Consensus, Exa, Grok MCP tools |
| **data_auditor** | `ccg:review` | `nature-data` | Rscript, Python, Read, Grep (no Write) |
| **figure_planner** | `nature-figure` | -- | `nature-figure`, Read (no code execution) |
| **analysis_executor** | `wgcna-analyst` (if WGCNA), `ccg:team-exec` | `ccg:debug`, `ccg:test` | Rscript, Python, Read, Write, Glob, Grep |
| **pipeline_engineer** | `ccg:workflow`, `ccg:commit` | `nature-data` | Docker, conda, pip, R, Python |
| **statistician** | `ccg:review` | `scientific-writing` (statistical sections) | Rscript, Python, Read (no Write) |
| **report_writer** | `academic-paper`, `scientific-writing`, `nature-writing` | `nature-polishing`, `academic-paper-polish`, `humanizer`, `nature-citation`, `nature-data`, `nature-response`, `research-paper-writing`, `remove-ai-flavor` | Skill tools, Read, Write (no code execution) |
| **integrity_checker** | `academic-paper-reviewer`, `ai-writing-detection` | `paper-glance`, `nature-response`, `ccg:team-review` | Read, Grep, Glob, MCP tools (no Write, no code execution) |
| **team_orchestrator** | `academic-pipeline` | `ccg:team-plan`, `find-skills` | Task tools, no code execution |
| **multi_omics_integrator** | `ccg:team-exec` | `wgcna-analyst` | Rscript, Python, Read, Write, Glob, Grep |

---

## Team-Skill Composition

### Team: `paper_writing_team` (8+1 agents)

| Role | Agent | Skills |
|------|-------|--------|
| Coordinator | `team_orchestrator` | `academic-pipeline`, `ccg:team-plan` |
| Research | `research_strategist` | `deep-research`, `tavily-research` |
| Literature | `literature_reviewer` | `nature-academic-search`, `nature-reader`, `paper-glance` |
| Data Audit | `data_auditor` | `ccg:review` |
| Figures | `figure_planner` | `nature-figure` |
| Analysis | `analysis_executor` | `wgcna-analyst`, `ccg:team-exec` |
| Pipeline | `pipeline_engineer` | `ccg:workflow`, `nature-data` |
| Writing | `report_writer` | `academic-paper`, `scientific-writing`, `nature-writing`, `nature-polishing`, `humanizer` |
| Quality | `integrity_checker` | `academic-paper-reviewer`, `ai-writing-detection` |

### Team Output Structure
```
papers/{paper_id}/
├── project_passport.yaml
├── artifact_ledger.jsonl
├── checkpoint_ledger.jsonl
├── integrity_ledger.jsonl
├── manuscript/
│   ├── abstract.md, introduction.md, methods.md
│   ├── results.md, discussion.md
│   ├── manuscript_full.tex, manuscript_full.pdf
│   └── claims_evidence_table.csv
├── references/
│   ├── library.bib
│   └── citation_evidence.csv
├── integrity/
│   ├── integrity_report.json, integrity_report.md
│   └── integrity_ledger.jsonl
├── review/
│   ├── reviewer_reports/
│   ├── review_summary.md
│   └── commitment_ledger.csv
└── submission/
    ├── final.pdf, final.docx
    ├── cover_letter.md
    └── supplementary_package.zip
```

---

## Cross-Cutting Skills

Skills that operate across multiple phases without direct stage binding:

| Skill | Cross-Cutting Function |
|-------|----------------------|
| `ccg:commit` | Version control throughout all code-producing stages |
| `ccg:context` | Decision logging and project memory across the full pipeline |
| `find-skills` | Pre-pipeline capability discovery |
| `darwin-skill` | Continuous improvement of all framework skills |
| `skill-creator` | Extending framework with new domain-specific skills |
| `claude-hud:setup` | Development environment configuration |
| `update-config` | Framework configuration management |

---

## Trigger Keyword Index

### English Keywords → Skill Mapping

| Keyword / Phrase | Primary Skill | Stage(s) |
|-----------------|---------------|----------|
| write paper, academic paper, 写论文, 學術論文 | `academic-paper` | 9-13,16 |
| polish, language editing, proofreading, 润色 | `academic-paper-polish` / `nature-polishing` | 9-13,16,18 |
| review paper, peer review, referee report | `academic-paper-reviewer` | 14,15,17 |
| research to paper, full paper workflow, end-to-end | `academic-pipeline` | 1-18 |
| scientific writing, IMRAD, methods section, reporting guidelines | `scientific-writing` | 9-12 |
| remove AI signs, naturalize, human-written | `humanizer` | 9-13,16,18 |
| Nature writing, Nature-style, Nature manuscript | `nature-writing` | 9-13 |
| Nature polish, academic English, 英文润色 | `nature-polishing` | 9-13,16,18 |
| scientific figure, journal figure, 论文配图, 科研绘图 | `nature-figure` | 6,7,13 |
| add citations, Nature citation, 分段引用, 补引用 | `nature-citation` | 3,11,12,13 |
| translate paper, read paper, 读论文, 精读论文 | `nature-reader` | 3 |
| reviewer response, rebuttal, 审稿意见回复, 修回信 | `nature-response` | 15,16,17 |
| data availability, data sharing, 数据可用性 | `nature-data` | 8,9,13,18 |
| paper to PPT, 论文做PPT, 组会PPT | `nature-paper2ppt` | 18 |
| literature search, 文献检索, 查文献, 找文献 | `nature-academic-search` | 3 |
| deep research, comprehensive analysis, research report | `deep-research` | 1-4 |
| analyze paper, paper analysis, 帮我看论文, PDF upload | `paper-glance` | 3,15 |
| summarize, summary, digest | `summarize` | 3 |
| AI writing detection, check for AI | `ai-writing-detection` | 13,14,18 |
| remove AI flavor (Chinese), 去AI味 | `remove-ai-flavor` | 9-13,16 |
| ML paper, CV paper, conference paper | `research-paper-writing` | 9-12 |
| research, investigate, market analysis | `tavily-research` | 1-3 |
| find skill, install skill, how do I | `find-skills` | Pre-1 |
| WGCNA, co-expression, 共表达网络, 模块分析 | `wgcna-analyst` | 7 |
| code review, quality gate, verify | `ccg:review` | 7,8,14,17 |
| run pipeline, execute analysis | `ccg:team-exec` | 7 |

### Chinese Keywords → Skill Mapping

| Chinese | Skill |
|---------|-------|
| 写论文, 学术论文, 引导我写论文 | `academic-paper` |
| 论文润色, 语言润色, 英文润色 | `nature-polishing` / `academic-paper-polish` |
| 审稿, 同行评审, 审稿意见 | `academic-paper-reviewer` |
| 论文流水线, 端到端论文 | `academic-pipeline` |
| 科研写作, 方法部分, 写方法, 写结果 | `scientific-writing` |
| 去除AI痕迹, 更自然, 不像AI写的 | `humanizer` |
| 论文配图, 科研绘图, 画图, 作图 | `nature-figure` |
| 加引用, 找引用, 配文献, 引用文献 | `nature-citation` |
| 读论文, 论文翻译, 文献翻译, 帮我读这篇文章 | `nature-reader` |
| 审稿意见回复, 逐点回复, 修回信, 大修回复 | `nature-response` |
| 数据可用性声明, 数据共享, 代码可用性 | `nature-data` |
| 论文做PPT, 组会PPT, 文献汇报, 学术汇报 | `nature-paper2ppt` |
| 文献检索, 查文献, 找文献, 参考文献管理 | `nature-academic-search` |
| 深度研究, 调研, 综合分析 | `deep-research` |
| 帮我看这篇论文, 文献分析 | `paper-glance` |
| AI痕迹检测, 查AI | `ai-writing-detection` |
| 去AI味, 不像AI写的 (中文) | `remove-ai-flavor` |
| 共表达网络, 模块分析, 软阈值, hub基因 | `wgcna-analyst` |

---

## Integration Rules

### Rule 1: Skill Dispatch Priority
When multiple skills match a user request, dispatch in this priority order:
1. Domain-specific analysis skills (`wgcna-analyst`) -- most specific
2. Pipeline orchestrator (`academic-pipeline`) -- if "end-to-end" / "full workflow"
3. Core writing skills (`academic-paper`, `scientific-writing`, `nature-writing`)
4. Research skills (`deep-research`, `nature-academic-search`)
5. Quality skills (`academic-paper-reviewer`, `ai-writing-detection`)
6. Language skills (`nature-polishing`, `humanizer`, `academic-paper-polish`)
7. Meta skills (`find-skills`, `skill-creator`)

### Rule 2: Skill Chain Integrity
- NEVER chain `academic-paper` after `academic-pipeline` -- the pipeline already dispatches it internally
- ALWAYS run `academic-paper-reviewer` after `integrity_check` passes (stage 14 before 15)
- ALWAYS run `nature-data` before `assemble_manuscript` (stage 13) when targeting Nature journals
- ALWAYS run `nature-polishing` or `academic-paper-polish` after `apply_revision` (stage 16)

### Rule 3: Journal-Targeted Skill Selection
| Target Journal Tier | Writing Skill | Polishing Skill | Citation Skill |
|--------------------|---------------|-----------------|----------------|
| Nature/CNS Flagship | `nature-writing` | `nature-polishing` | `nature-citation` |
| Nature Communications / Science Advances | `nature-writing` | `nature-polishing` | `nature-citation` |
| Top Field (IF 8-20) | `scientific-writing` | `nature-polishing` | `nature-academic-search` |
| Strong Field (IF 4-8) | `scientific-writing` | `academic-paper-polish` | `nature-academic-search` |
| Solid Specialty (IF 2-4) | `scientific-writing` | `academic-paper-polish` | `nature-academic-search` |
| CS Conference/Journal | `research-paper-writing` | `academic-paper-polish` | `nature-academic-search` |

### Rule 4: Language-Level Skill Pipeline
```
Draft (raw) → Structural Polish → Language Polish → AI-Sign Removal → Final Prose

  Draft:       academic-paper / scientific-writing / nature-writing / research-paper-writing
  Structural:  nature-polishing (restructure mode)
  Language:    nature-polishing / academic-paper-polish
  AI Removal:  humanizer (English) / remove-ai-flavor (Chinese)
  Final:       integrity_check gate M2 (no_bullets_in_prose)
```

---

## Skill-to-Gate Mapping

Each skill directly supports specific integrity gates:

| Skill | Gates Supported |
|-------|----------------|
| `academic-paper` (citation-check mode) | C1 (bibtex), C2 (citation traceability), C3 (results no cite) |
| `academic-paper-reviewer` | H6 (overinterpretation), H7 (statistics), H8 (pseudoreplication) |
| `nature-citation` | C1, C2 |
| `nature-data` | H1 (data availability), H2 (code availability) |
| `nature-figure` | C5 (figure references), M3 (figure count) |
| `nature-polishing` | M2 (no bullets), M1 (section length) |
| `humanizer` | M2 (no bullets -- prose quality) |
| `ai-writing-detection` | M2 (no AI-pattern bullets) |
| `ccg:review` | H3 (no local paths), H4 (parameters complete) |

---

## File Manifest

```
ResearchPaperWorkflow/.claude/
├── SKILL_REGISTRY.md          ← THIS FILE (28 external skills mapped)
├── skills/ (5 framework skills)
│   ├── paper_loop.md          → Pipeline engine definition (stages 1-18)
│   ├── topic_research.md      → Research strategy wrapper (stages 1,2,4)
│   ├── figure_planning.md     → Figure planning wrapper (stage 6)
│   ├── paper_writing.md       → Writing wrapper (stages 9-13,16,18)
│   └── revision_routing.md    → Revision routing wrapper (stages 15-17)
├── agents/ (10 agent definitions)
│   ├── research_strategist.md → Strategy agent (stages 1,2,4)
│   ├── literature_reviewer.md → Literature agent (stage 3)
│   ├── data_auditor.md        → Data quality agent (stage 5)
│   ├── figure_planner.md      → Figure design agent (stage 6)
│   ├── pipeline_engineer.md   → Reproducibility agent (stage 8)
│   ├── statistician.md        → Statistics audit agent (cross-cutting)
│   ├── report_writer.md       → Writing agent (stages 9-13,16,18)
│   ├── integrity_checker.md   → Quality agent (stages 14,15,17,18)
│   ├── team_orchestrator.md   → Coordination agent (all stages)
│   └── multi_omics_integrator.md → Multi-omics agent (stage 7)
└── teams/ (1 team)
    └── paper_writing_team.md  → 9+1 agent team configuration
```

---

*Registry maintained by the Research Paper Workflow Framework. Skills marked CRITICAL are required for pipeline completion. Update this registry when new skills are installed or existing skills change their trigger conditions.*
