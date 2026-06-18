---
name: paper-writing
description: "Domain-agnostic research paper writing skill covering the full lifecycle: planning, IMRAD drafting, methods templating, figure specification, literature citation, revision, and submission. Integrates with Paper Loop Engine (10-stage pipeline). Triggers on: write paper, research paper, draft manuscript, paper workflow, IMRAD, methods section, figure specs, citation workflow, revise manuscript, submission checklist, journal selection, 写论文, 学术论文, 论文写作, 方法部分, 图表规范, 引用流程, 修改论文, 投稿清单, 期刊选择."
metadata:
  version: "1.0"
  last_updated: "2026-06-18"
  depends_on: "deep-research, academic-paper, academic-paper-reviewer, academic-pipeline"
  paper_loop_stages: "1-10"
---

# Paper Writing Skill v1.0 -- Domain-Agnostic Research Paper Workflow

A comprehensive, domain-agnostic skill for research paper writing that spans the full lifecycle from ideation to submission. Integrates with the **Paper Loop Engine** (10-stage academic pipeline) and provides structured workflows for IMRAD drafting, methods documentation, figure preparation, literature citation, revision handling, and journal submission.

## Quick Start

**Minimal command:**
```
Write a research paper on [topic]
```

**Execution flow:**
1. Intake & Configuration -- paper type, discipline, target journal, citation format, output format
2. IMRAD Structure Planning -- outline, word allocation, evidence mapping
3. Methods Documentation -- code-to-text reconciliation, parameter traceability
4. Figure Preparation -- specification, export targets, accessibility compliance
5. Literature Citation -- search, format, cross-check
6. Drafting -- section-by-section, register-appropriate prose
7. Revision Cycle -- reviewer response, change tracking
8. Pre-Submission Checklist -- completeness, compliance, reproducibility
9. Journal Selection Support -- decision table, impact/scope/fit scoring

---

## Trigger Conditions

### Trigger Keywords

**English**: write paper, research paper, draft manuscript, paper workflow, IMRAD, methods section, figure specifications, citation workflow, revise manuscript, submission checklist, journal selection, paper outline, write abstract, literature review, scientific writing, academic writing, manuscript preparation, paper revision, response to reviewers, cover letter, data availability, code availability, reproducibility, reporting guidelines, peer review

**Chinese**: 写论文, 学术论文, 论文写作, 方法部分, 图表规范, 引用流程, 修改论文, 投稿清单, 期刊选择, 论文大纲, 写摘要, 文献综述, 科研写作, 论文润色, 审稿回复, 投稿信, 数据可用性, 代码可用性, 可重复性, 报告指南, 同行评审

### Non-Trigger Scenarios

| Scenario | Use Instead |
|----------|-------------|
| Literature search only (no writing) | `deep-research` or `nature-academic-search` |
| Paper review only (no writing) | `academic-paper-reviewer` |
| End-to-end pipeline orchestration | `academic-pipeline` |
| Figure creation only (no paper text) | `nature-figure` |
| Citation format check only | `academic-paper` (citation-check mode) |
| Language polishing only | `nature-polishing` or `academic-paper-polish` |

---

## Paper Loop Engine Integration

This skill integrates with the **Paper Loop Engine** -- a 10-stage state machine that orchestrates the full research-to-publication lifecycle. The engine is defined by `academic-pipeline` and coordinates `deep-research`, `academic-paper`, and `academic-paper-reviewer` into a seamless workflow with mandatory quality gates.

### Stage Mapping

| Loop Stage | Name | What This Skill Provides | Engine Action |
|------------|------|--------------------------|---------------|
| 1 | RESEARCH | Literature search strategy, gap analysis | `deep-research` dispatched |
| 2 | WRITE | IMRAD templates, methods docs, figure specs | `academic-paper` dispatched |
| 2.5 | INTEGRITY | Reference cross-check, data traceability matrix | Integrity verification agent |
| 3 | REVIEW | Structured review criteria, scoring rubrics | `academic-paper-reviewer` dispatched (5 reviewers) |
| 4 | REVISE | Revision workflow, change tracking, response letter | `academic-paper` (revision mode) |
| 3' | RE-REVIEW | Response completeness check, residual issues | Re-review verification |
| 4' | RE-REVISE | Final revision pass (max 1 round) | `academic-paper` (revision mode) |
| 4.5 | FINAL INTEGRITY | 100% citation + data verification | Final integrity check (must PASS) |
| 5 | FINALIZE | Format conversion, cover letter, submission package | Format-convert + PDF compilation |
| 6 | PROCESS SUMMARY | Collaboration record, lessons learned | Auto-generated process document |

### Handoff Data Contracts

This skill produces and consumes the following standardized artifacts across loop stages:

| Artifact | Produced By Stage | Consumed By Stage | Schema |
|----------|-------------------|-------------------|--------|
| RQ Brief | 1 (RESEARCH) | 2 (WRITE) | Research question, scope, key concepts |
| Bibliography | 1 (RESEARCH) | 2 (WRITE), 2.5 (INTEGRITY) | DOI, title, authors, year, journal, verified |
| Paper Draft | 2 (WRITE) | 2.5 (INTEGRITY), 3 (REVIEW) | Full manuscript with embedded data traces |
| Integrity Report | 2.5 (INTEGRITY) | 3 (REVIEW) | Reference validity, data accuracy, originality |
| Review Reports | 3 (REVIEW) | 4 (REVISE) | 5-reviewer scores, verdict, revision items |
| Revision Roadmap | 3 (REVIEW) | 4 (REVISE) | Prioritized change list with difficulty estimates |
| Response Letter | 4 (REVISE) | 3' (RE-REVIEW) | Point-by-point response with change locations |
| Final Package | 5 (FINALIZE) | Submission | LaTeX/PDF/DOCX + cover letter + supplements |

---

## IMRAD Workflow

The core writing workflow follows the Introduction-Methods-Results-and-Discussion structure, adaptable to all empirical research disciplines.

### Phase 0: Configuration Interview

Before writing begins, resolve these 9 configuration items:

| # | Item | Options / Default |
|---|------|-------------------|
| 1 | Paper Type | IMRAD / Literature Review / Theoretical / Case Study / Policy Brief / Conference |
| 2 | Discipline | Any (life sciences, physical sciences, social sciences, engineering, humanities) |
| 3 | Target Journal | Optional; if specified, format to journal requirements |
| 4 | Citation Format | APA 7.0 (default) / Vancouver / Chicago / MLA / IEEE / Journal-specific |
| 5 | Output Format | LaTeX+PDF (default) / DOCX / Markdown / Combined |
| 6 | Language | English (default) / Chinese / Bilingual sections |
| 7 | Bilingual Abstract | Yes (default) / EN-only / ZH-only |
| 8 | Word Count Target | 4000-8000 (default: 6000) |
| 9 | Existing Materials | None / Data only / Partial draft / Full draft for revision |

### Phase 1: IMRAD Structure Planning

#### Section Architecture

```
1. Title Page
2. Abstract (structured: Background, Methods, Results, Conclusions)
   Keywords (5-7)
3. Introduction
   3.1 Background & Context
   3.2 Problem Statement
   3.3 Research Gap Identification
   3.4 Research Questions / Hypotheses
   3.5 Significance
4. Methods
   4.1 Study Design
   4.2 Data Sources / Sample
   4.3 Variables & Measures
   4.4 Statistical / Analytical Approach
   4.5 Software & Computational Environment
   4.6 Reproducibility Statement
5. Results
   5.1 Descriptive Overview
   5.2 Primary Analysis (aligned with RQ1)
   5.3 Secondary Analyses (RQ2, RQ3, ...)
   5.4 Sensitivity / Robustness Checks
6. Discussion
   6.1 Summary of Key Findings
   6.2 Comparison with Prior Literature
   6.3 Mechanistic / Theoretical Interpretation
   6.4 Implications
   6.5 Limitations
   6.6 Future Directions
7. Conclusion
8. Data Availability Statement
9. Code Availability Statement
10. AI Disclosure
11. References
12. Supplementary Materials (if applicable)
```

#### Word Allocation Table (6,000-word default)

| Section | Percentage | Words (6000) | Words (4000) | Words (8000) |
|---------|-----------|-------------|-------------|-------------|
| Introduction | 15% | 900 | 600 | 1200 |
| Methods | 20% | 1200 | 800 | 1600 |
| Results | 25% | 1500 | 1000 | 2000 |
| Discussion | 30% | 1800 | 1200 | 2400 |
| Conclusion | 5% | 300 | 200 | 400 |
| Abstract | 5% | 300 | 200 | 400 |

#### Evidence Mapping (Before Writing)

For each Results sub-section, complete this mapping:

```
Results Sub-section: [Title, e.g., "Differential Expression Analysis"]
  Aligned RQ: [e.g., RQ1]
  Key Finding (1 sentence): [e.g., "842 genes were differentially expressed (FDR < 0.05, |log2FC| > 1)"]
  Supporting Evidence:
    - Figure [N]: [description, file path]
    - Table [N]: [description, file path]
    - Statistical Test: [name, statistic, p-value, effect size, CI]
    - Data Source: [file path or analysis script + line number]
  Discussion Tie-in: [Which Discussion sub-section interprets this finding]
```

### Phase 2: Methods Template

The Methods section is the reproducibility backbone. Every claim must be traceable to actual code or protocol.

#### Methods Section Template

```markdown
## Methods

### Study Design
[Type of study: e.g., case-control, cohort, cross-sectional, computational analysis]
[Justification for design choice]
[Temporal scope: data collection period or analysis date range]

### Data Sources
[Data origin: public repository (accession number), institutional collection, simulation]
[Inclusion / exclusion criteria with rationale]
[Final sample size and composition]
[For public data: full citation + accession + retrieval date]

### Variable Definitions
[Primary outcome variable: definition + measurement method]
[Primary exposure / predictor: definition + measurement method]
[Covariates: full list with justification for inclusion]
[Derived variables: computation method with formula or code reference]

### Statistical Analysis
#### Preprocessing
[Transformation: log, normalization, scaling -- with parameters]
[Quality control thresholds: specific values, not ranges]
[Outlier handling: method + threshold + justification]

#### Primary Analysis
[Test name, software package, version, function call signature]
[Key parameters with values used (NOT defaults -- confirmed from code)]
[Effect size metric + confidence interval method]
[Multiple testing correction method + threshold]

#### Secondary / Sensitivity Analyses
[Each additional analysis: purpose + method + parameters]
[Robustness check description]

### Software & Environment
| Software/Package | Version | Purpose | Citation |
|-----------------|---------|---------|----------|
| [e.g., R] | [e.g., 4.3.1] | Statistical computing | R Core Team (2023) |
| [e.g., Seurat] | [e.g., 5.0.1] | Single-cell analysis | Hao et al. (2024) |

### Random Seed & Reproducibility
All random seeds were fixed: [specific seed values, one per analysis step].
Analysis scripts are available at [repository URL].
The computational environment is captured in [environment.yml / renv.lock / Dockerfile].

### Reporting Guidelines Compliance
This study follows [CONSORT / STROBE / PRISMA / STREGA / TRIPOD / other] reporting guidelines.
[Checklist reference or supplement file path]
```

#### Methods-to-Code Traceability Matrix (MANDATORY)

Create this matrix before finalizing Methods. Every parameter value in the text must be exactly the value used in code.

| Methods Sentence | Parameter | Code Value | Code File:Line | Match? |
|-----------------|-----------|------------|----------------|--------|
| "Soft-thresholding power was set to 20" | `power` | `20` | `wgcna.R:45` | YES |
| "Genes with FDR < 0.05 and |fold change| > 1 were considered significant" | `fdr_threshold` | `0.05` | `de_analysis.R:128` | YES |
| | `fc_threshold` | `1.0` | `de_analysis.R:129` | YES |

**Rule**: If any cell in the "Match?" column is NO, fix either the text or the code before proceeding.

### Phase 3: Figure Specifications

#### Figure Planning Table (Complete Before Drafting)

| Fig # | Panel | Conclusion (1 sentence) | Data Source | Chart Type | Export Specs | Color Palette |
|-------|-------|------------------------|-------------|------------|-------------|---------------|
| 1 | A | [What the reader should conclude] | `results/table1.csv` | Boxplot | 1200x900, 300 DPI, TIFF | viridis |
| 1 | B | [Conclusion] | `results/heatmap_data.csv` | Heatmap | 1200x900, 300 DPI, TIFF | RdBu |

#### Figure Export Specifications

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| Resolution | 300 DPI minimum (600 DPI for line art) | Journal requirements |
| Format | TIFF (preferred) or PDF (vector) | Lossless; most journals accept |
| Color Mode | RGB for digital; CMYK for print (check journal) | Print vs. online |
| Font Size | 8-10 pt in final figure | Readability at journal column width |
| Text Font | Arial / Helvetica / sans-serif | Universal availability |
| Panel Labels | Uppercase bold (A, B, C...) at top-left of each panel | Journal convention |
| Color Palette | Colorblind-safe (viridis, cividis, Okabe-Ito) | Accessibility compliance |

#### Figure Caption Template

```
Figure [N]. [Concise title describing what the figure shows -- not what it means].
(A) [Panel A description: what is shown, sample size, conditions].
(B) [Panel B description].
[Statistical notation: test used, p-value threshold, error bar definition].
Abbreviations: [define all abbreviations used in figure].
```

#### Accessibility Checklist (Per Figure)

```
□ Colorblind-safe palette used (simulate: protanopia, deuteranopia, tritanopia)
□ No red-green only encoding for critical distinctions
□ Symbols differ by shape AND color (not color alone)
□ All text >= 8 pt at final size
□ Error bars defined in caption
□ Scale bars / axis labels present and readable
□ White space balanced across panels
```

### Phase 4: Literature Citation Workflow

#### Citation Pipeline

```
1. SEARCH
   ├── Primary: PubMed (biomedical) / Semantic Scholar (cross-disciplinary) / arXiv (CS/physics)
   ├── Supplementary: Web search for gray literature, policy docs, preprints
   └── Output: .nbib / .ris / .bib file

2. SCREEN
   ├── Title/abstract screening against inclusion criteria
   ├── Full-text retrieval for passing entries
   └── Output: Annotated bibliography

3. FORMAT
   ├── Select target format: APA 7 / Vancouver / Chicago / MLA / IEEE / Journal-specific
   ├── Convert all entries to target format
   └── Output: Formatted .bib or reference list

4. CITE
   ├── Insert in-text citations at claim level (not paragraph level)
   ├── Each factual claim gets >= 1 citation
   ├── Key claims get >= 2 independent sources
   └── Output: Draft with embedded citations

5. VERIFY (mandatory -- cannot skip)
   ├── Cross-check: every in-text citation has a reference list entry
   ├── Cross-check: every reference list entry is cited in text (zero orphans)
   ├── DOI verification: all DOIs resolve to correct papers
   ├── Ghost citation check: no fabricated or hallucinated references
   └── Output: Citation Audit Report
```

#### Citation Placement Rules

| Claim Type | Citation Strategy |
|------------|-------------------|
| Established fact ("X is known to cause Y") | >= 2 independent sources |
| Specific finding from one study | Single citation with context ("Smith et al. (2023) found...") |
| Methodological choice | Citation to original method paper + justification |
| Controversial / debated claim | Multiple citations showing both sides |
| Your own novel finding | No citation (it is your contribution) |
| Numerical claim from external source | Citation + page/figure/table reference |

#### Citation Format Quick Reference

| Format | In-Text | Reference List | Common In |
|---------|---------|---------------|-----------|
| APA 7 | (Author, Year) | Alphabetical, hanging indent | Social sciences, education |
| Vancouver | [1] or superscript | Numbered by appearance | Biomedical, life sciences |
| Chicago (Author-Date) | (Author Year) | Alphabetical | Humanities, some social sciences |
| IEEE | [1] | Numbered by appearance | Engineering, CS |
| MLA 9 | (Author Page) | Alphabetical, Works Cited | Literature, humanities |

### Phase 5: Revision Workflow

#### Intake: Parse Reviewer Comments

```
For each reviewer comment, extract:
1. Reviewer ID: R1 / R2 / R3
2. Severity: MAJOR / MINOR / EDITORIAL / POSITIVE
3. Core Request (1 sentence)
4. Section(s) Affected
5. Verbatim Quote
```

#### Decision Framework: Accept vs. Reject vs. Negotiate

| Reviewer Comment Is... | Default Strategy | When to Override |
|------------------------|------------------|------------------|
| Factually correct, improves paper | ACCEPT -- make the change | Never |
| Based on misunderstanding | CLARIFY -- improve text clarity | If misunderstanding reflects a real reader, accept the clarification |
| School-of-thought disagreement | NEGOTIATE -- explain position respectfully | If reviewer is demonstrably wrong, reject with evidence |
| Requests analysis beyond scope | NEGOTIATE -- acknowledge as future direction | If feasible with reasonable effort, consider accepting |
| Vague, unactionable | CLARIFY -- ask specific question in response | If you can infer intent, address the inferred concern |
| Contradicts another reviewer | NEGOTIATE -- explain the contradiction, state your choice | EIC decision prevails; defer to EIC guidance |

#### Response Letter Template

```
Dear Editor,

We thank you and the reviewers for the careful evaluation of our manuscript
[Manuscript ID]. Below we provide a point-by-point response. Reviewer comments
are in italics; our responses follow in plain text. All changes are marked in
the revised manuscript [with tracked changes / highlighted in blue].

---
Reviewer 1
---

Comment 1: [Verbatim quote]

Response: [Explanation of what you did and why. If you disagree, explain
respectfully with evidence.]

Changes made: [Specific location: Section X, Paragraph Y, Lines Z-W.
Quote the new text or summarize the change.]

---
[Repeat for each comment]
---

We believe these revisions have substantially improved the manuscript and
hope it is now suitable for publication in [Journal Name].

Sincerely,
[Corresponding Author]
```

#### Revision Tracking Table

| ID | Reviewer | Severity | Comment Summary | Decision | Action Taken | Location of Change | Status |
|----|----------|----------|-----------------|----------|-------------|--------------------|--------|
| R1-C1 | R1 | MAJOR | Add sensitivity analysis | ACCEPT | Added bootstrap CI | Methods 4.4, Results 5.4 | DONE |
| R2-C3 | R2 | MINOR | Clarify exclusion criteria | ACCEPT | Added flowchart | Methods 4.2, Fig S1 | DONE |
| R3-C2 | R3 | MAJOR | Use alternative method | REJECT (with evidence) | Explained in response letter | N/A | DELIBERATE_LIMITATION |

Status values: `DONE` | `DELIBERATE_LIMITATION` | `DEFERRED_TO_EIC` | `PENDING`

### Phase 6: Pre-Submission Checklist

#### Completeness

```
□ Title: <= 25 words, descriptive, no abbreviations
□ Abstract: structured, word count within journal limit
□ Keywords: 5-7, MeSH terms where applicable
□ All sections present per journal requirements
□ All figures cited in text (sequential order: Fig 1, Fig 2, ...)
□ All tables cited in text (sequential order: Table 1, Table 2, ...)
□ All supplementary materials cited in main text
□ Reference list complete, formatted correctly, zero orphans
□ Author list: all contributors meet ICMJE criteria
□ Affiliations: current and correct for all authors
□ Corresponding author: marked, email correct
□ ORCID IDs: included for all authors (if journal requires)
□ Running title: <= 50 characters (if required)
□ Word count: within journal limit (excluding abstract, references, figure legends)
```

#### Figure & Table Compliance

```
□ All figures: >= 300 DPI, correct format (TIFF/PDF/EPS per journal)
□ All figures: colorblind-safe palette verified
□ All figure captions: standalone (reader can understand without main text)
□ All tables: editable format (not images), per journal style
□ All tables: footnotes explain all abbreviations and symbols
□ Multi-panel figures: panels labeled (A, B, C...) consistently
□ Scale bars present on all micrographs/images
```

#### Data & Code Availability

```
□ Data Availability Statement present and complete
□ Public data: accession numbers verified and accessible
□ Restricted data: access procedure described
□ Code Availability Statement present
□ Code repository: public, with DOI (Zenodo/Figshare)
□ README: installation, usage, expected output, runtime estimate
□ Dependencies: version-pinned (renv.lock / conda-lock / requirements.txt)
□ Random seeds: documented and accessible
□ All paths: relative, not absolute
□ LICENSE file present (MIT / GPL / Apache 2.0)
```

#### Ethics & Disclosures

```
□ Ethics approval statement (if human/animal subjects)
□ Informed consent statement (if human subjects)
□ Conflict of Interest disclosure for all authors
□ Funding statement with grant numbers
□ Author Contributions (CRediT taxonomy recommended)
□ AI Disclosure: tools used, how used, human verification confirmed
□ Clinical Trial Registration number (if applicable)
```

#### Submission Package

```
□ Cover letter: customized to target journal
□ Manuscript file: blinded or unblinded per journal policy
□ Figures: separate files or embedded per journal policy
□ Supplementary materials: organized, cross-referenced
□ Response to Reviewers (if revision)
□ Suggested Reviewers (if journal requires)
□ Excluded Reviewers (optional, with justification)
```

---

## Journal Selection Decision Table

### Scoring Framework

Rate each candidate journal on these 7 dimensions (1-5 scale):

| Dimension | Weight | Description |
|-----------|--------|-------------|
| Scope Fit | 25% | How well does your paper match the journal's stated scope? |
| Impact Level | 20% | Journal impact factor, CiteScore, or field-specific ranking |
| Audience Reach | 15% | Does this journal reach your intended readers? |
| Review Timeline | 15% | Average time from submission to first decision |
| Acceptance Rate | 10% | Realistic chance of acceptance? |
| Open Access | 10% | OA options, APCs, funder compliance |
| Prestige / Career Value | 5% | Value for tenure, promotion, grant applications |

### Journal Tier Reference

| Tier | Impact Factor Range (approx.) | Examples (domain-agnostic) | Typical Acceptance Rate | Typical Review Time |
|------|------------------------------|---------------------------|------------------------|---------------------|
| Flagship | >20 | Nature, Science, Cell, NEJM, Lancet | 5-10% | 2-4 months |
| Top Field | 8-20 | Nature Genetics, Cell Reports, BMJ, PNAS | 10-20% | 2-4 months |
| Strong Field | 4-8 | eLife, PLOS Biology, Development, JBC | 20-35% | 2-4 months |
| Solid Specialty | 2-4 | PLOS ONE, PeerJ, BMC series, Scientific Reports | 35-55% | 1-3 months |
| Regional / Niche | <2 | Regional journals, new OA journals | 40-70% | 1-3 months |

### Decision Matrix Template

```
Paper Title: [Title]
Paper Type: [IMRAD / Review / Methods / Brief Report]
Discipline: [Field]

| Journal | Scope Fit (25%) | Impact (20%) | Audience (15%) | Timeline (15%) | Accept Rate (10%) | OA (10%) | Prestige (5%) | WEIGHTED TOTAL |
|---------|----------------|--------------|----------------|----------------|--------------------|----------|----------------|----------------|
| [Journal A] | 4 | 5 | 4 | 3 | 2 | 4 | 5 | 3.95 |
| [Journal B] | 5 | 3 | 4 | 4 | 3 | 5 | 3 | 3.90 |
| [Journal C] | 3 | 4 | 3 | 5 | 4 | 4 | 3 | 3.55 |

Top Pick: [Journal B] -- best scope fit with acceptable impact and strong OA compliance
Stretch Target: [Journal A] -- higher impact, lower acceptance rate, submit if time permits
Safety: [Journal C] -- fastest review, highest acceptance, solid field reputation
```

### Journal Selection Workflow

```
1. Define your paper's core contribution (1 sentence)
2. List 5-10 candidate journals by:
   a. Checking where you cite most frequently (reference list analysis)
   b. Searching journal databases (JCR, Scopus, DOAJ)
   c. Asking mentors / colleagues
3. Score each candidate on the 7 dimensions
4. Rank by weighted total
5. Select Top Pick, Stretch Target, and Safety
6. Read the Guide for Authors for your Top Pick
7. Format manuscript to Top Pick's requirements BEFORE writing
   (formatting after writing costs time and introduces errors)
```

---

## Integration with Other Skills

```
paper-writing + deep-research          -> Literature-backed paper with verified citations
paper-writing + academic-paper         -> Full 12-agent writing pipeline with formatting
paper-writing + academic-paper-reviewer -> Pre-submission peer review simulation
paper-writing + academic-pipeline      -> End-to-end 10-stage workflow with integrity gates
paper-writing + nature-figure          -> Publication-quality figures with colorblind-safe palettes
paper-writing + nature-polishing       -> Language polishing to journal standards
paper-writing + nature-citation        -> Nature/CNS-format citation insertion
paper-writing + nature-data            -> Data availability statement preparation
paper-writing + nature-response        -> Point-by-point reviewer response letter
paper-writing + scientific-writing     -> IMRAD prose with reporting guideline compliance
```

---

## Quality Standards

### Writing Quality
1. Every claim has evidence support (citation or data) -- ZERO unsupported assertions
2. Full paragraphs throughout -- never bullet points in final manuscript
3. Consistent academic register appropriate to discipline
4. Logical transitions between sections and paragraphs
5. Word count within +/-10% of target

### Methods Reproducibility
6. Every parameter value in Methods matches code exactly (Methods-to-Code Traceability Matrix must be 100% YES)
7. Software versions specified for all computational tools
8. Random seeds documented
9. Data accession numbers verified and accessible

### Citation Integrity
10. Zero ghost citations (fabricated references)
11. Zero orphan citations (cited but not in reference list)
12. Zero dangling references (in reference list but not cited)
13. All DOIs resolve to correct papers
14. Citation format consistent throughout

### Figure Quality
15. All figures >= 300 DPI at final size
16. All figures use colorblind-safe palettes
17. All captions are standalone (understandable without main text)
18. Panel labels consistent (uppercase bold, same position)

### Submission Readiness
19. Cover letter customized (not generic)
20. All checklists (reporting guideline, submission) completed
21. Data and code availability statements present
22. AI disclosure statement present

---

## Failure Paths & Recovery

| Scenario | Detection | Recovery |
|----------|-----------|----------|
| Methods-text-to-code mismatch | Traceability matrix reveals mismatch | Fix text or code; re-run analysis if code changed |
| Ghost citation detected | DOI verification fails | Search for real paper; if none exists, remove claim or find alternative source |
| Figure resolution too low | Pre-submission checklist | Re-export figure at correct DPI |
| Word count over limit by >20% | Word allocation check | Target verbose sections (Discussion most common offender); trim |
| Missing ethics statement | Completeness checklist | Add statement; if human subjects and no IRB, note as limitation |
| Code not reproducible | Fresh environment test | Debug environment; pin all dependency versions; add Dockerfile |
| Reviewer comment missed in response | Response completeness check | Add missing response; re-check all comments |
| Target journal changed mid-writing | Scope mismatch | Re-format; adjust word count, citation style, figure count per new journal |

---

## Templates

| Template | Purpose | Location |
|----------|---------|----------|
| IMRAD Structure | Section-by-section skeleton with word allocation | `templates/imrad_template.md` |
| Methods Section | Full methods template with code traceability | `templates/methods_template.md` |
| Figure Planning | Figure specifications table + caption template | `templates/figure_planning_template.md` |
| Response Letter | Point-by-point reviewer response | `templates/response_letter_template.md` |
| Submission Checklist | Comprehensive pre-submission verification | `templates/submission_checklist_template.md` |
| Journal Decision Matrix | 7-dimension journal scoring table | `templates/journal_decision_template.md` |
| Cover Letter | Customizable journal submission cover letter | `templates/cover_letter_template.md` |
| Revision Tracking | Reviewer comment tracking with status | `templates/revision_tracking_template.md` |

---

## References

| Reference | Purpose |
|-----------|---------|
| `references/imrad_structure_patterns.md` | 6 paper structure patterns with word allocations |
| `references/citation_formats.md` | Full specification for APA 7, Vancouver, Chicago, MLA, IEEE |
| `references/figure_standards.md` | Journal figure requirements, colorblind-safe palettes, export specs |
| `references/reporting_guidelines.md` | CONSORT, STROBE, PRISMA, STREGA, TRIPOD checklists |
| `references/journal_guide_database.md` | Guide for Authors summaries for major journals |
| `references/methods_writing_guide.md` | Discipline-specific methods conventions |
| `references/submission_checklist_master.md` | Master checklist covering all journal types |

---

## Output Language

Follows the user's language. Academic terminology retained in English. Bilingual abstracts (zh-TW/EN) provided when appropriate.

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-06-18 | Initial release: IMRAD workflow, methods template with code traceability, figure specifications, literature citation pipeline, revision workflow, pre-submission checklist, journal selection decision table, Paper Loop Engine integration (10 stages), 8 templates, 7 reference files |
