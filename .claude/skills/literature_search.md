---
name: literature_search
description: Systematic literature search across PubMed, CrossRef, arXiv, Scopus, and ScienceDirect. Citation management (.nbib/.ris/.bib conversion), MeSH search strategy, reference deduplication, and evidence synthesis. 文献检索，引文管理。触发词：literature, search, citation, bibliography, PRISMA, systematic review, 文献检索, 引文.
version: "1.0"
paper_loop_stages: "3"
agent: literature_reviewer
type: skill
---

# Literature Search Skill

Orchestrates Stage 3 of the paper loop. Performs systematic literature searches across multiple databases, manages citations, and synthesizes evidence.

## Pipeline Position
Stage 3 (`literature_search`) — depends on Stage 1 (`select_topic`), can run in parallel with Stage 2 (`target_journal`).

## Search Databases

| Database | Tool | Coverage |
|----------|------|----------|
| PubMed | `mcp__pubmed__search_articles` | Biomedical & life sciences |
| Consensus | `mcp__consensus__search` | 200M+ peer-reviewed papers, cross-disciplinary |
| Semantic Scholar | via consensus MCP | AI, CS, interdisciplinary |
| arXiv | via consensus MCP | Physics, math, CS, quantitative biology |
| Scopus / ScienceDirect | `nature-academic-search` | Broad scientific coverage |

## Search Strategy

1. **PICO Framework**: Define Population, Intervention/Exposure, Comparison, Outcome
2. **MeSH Terms**: Map keywords to Medical Subject Headings (for biomedical searches)
3. **Boolean Logic**: Combine terms with AND/OR/NOT; use field tags ([Title], [Author], [Journal])
4. **Filters**: Publication date range, study type, language, peer-reviewed only
5. **Snowballing**: Forward/backward citation tracking from seed papers

## Output Files

```
papers/{paper_id}/references/
+-- library.bib                  # Complete BibTeX library
+-- citation_evidence.csv         # Citation-to-claim traceability
+-- search_strategy.md            # Documented search methodology
+-- prisma_flowchart.md           # PRISMA flow diagram (if systematic review)
```

## Integration

See `literature_reviewer.md` for full agent specification. See `paper_loop.md` for stage sequencing.
