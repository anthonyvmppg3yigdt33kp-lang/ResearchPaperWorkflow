---
name: pathway_inference
description: Pathway enrichment analysis — GSVA, GSEA, clusterProfiler, GO, KEGG, Reactome, WikiPathways, MSigDB. Gene set analysis and network biology. 通路富集分析。触发词：pathway, enrichment, GO, KEGG, GSEA, gene set, Reactome, 通路, 富集, 功能注释.
version: "1.0"
paper_loop_stages: "7"
agent: analysis_executor
type: skill
---

# Pathway Inference Skill

Pathway enrichment and gene set analysis for transcriptomics, proteomics, and multi-omics data. Executed during Stage 7 (`run_analysis`).

## Pipeline Position
Stage 7 (`run_analysis`) — executed by `analysis_executor` after differential expression analysis.

## Analysis Methods

### 1. Over-Representation Analysis (ORA)
- **clusterProfiler**: `enrichGO()`, `enrichKEGG()`, `enrichPathway()` (Reactome)
- **enrichR**: Web-based multi-database enrichment
- Input: List of significant genes (by FDR threshold)

### 2. Gene Set Enrichment Analysis (GSEA)
- **fgsea**: Fast pre-ranked GSEA using adaptive multi-level split Monte Carlo
- **clusterProfiler**: `GSEA()` with pre-ranked gene list
- Input: Ranked gene list (by log2FC, t-statistic, or signed p-value)

### 3. Gene Set Variation Analysis (GSVA)
- **GSVA**: Sample-level pathway enrichment scores (non-parametric, no phenotype needed)
- **ssGSEA**: Single-sample GSEA variant
- Input: Expression matrix + gene set database

### 4. Gene Set Databases
| Database | Package | Contents |
|----------|---------|----------|
| GO (Gene Ontology) | `org.*.eg.db` + `GO.db` | BP, MF, CC terms |
| KEGG | `KEGG.db` / KEGG REST API | Metabolic and signaling pathways |
| Reactome | `ReactomePA` | Curated biological pathways |
| MSigDB | `msigdbr` | Hallmark, C2-C8 collections |
| WikiPathways | `rWikiPathways` | Community-curated pathways |

## Code Library Integration

The R module `code_library/r/bioinformatics_analysis.R` provides:
- `run_gsva()` — GSVA with graceful degradation (HAS_GSVA flag)
- `run_fgsea()` — Fast GSEA with pre-ranked gene lists
- `run_clusterprofiler_go()` — GO enrichment with multiple testing correction
- `run_clusterprofiler_kegg()` — KEGG enrichment

## Graceful Degradation

All pathway methods use the `HAS_PACKAGE` pattern:
```r
HAS_GSVA  <- load_pkg("GSVA")
HAS_CLUSTERPROFILER <- load_pkg("clusterProfiler")

if (HAS_GSVA) {
  gsva_results <- run_gsva(expr_matrix, gene_sets)
} else {
  cat("[SKIP] GSVA not available. Install with: BiocManager::install('GSVA')\n")
  gsva_results <- NULL  # flagged as DEFERRED in Phase Report
}
```

## Output Files

```
papers/{paper_id}/results/
+-- pathway/
    +-- gsea_results.csv            # GSEA results table
    +-- gsva_scores.csv             # Per-sample pathway scores
    +-- go_enrichment.csv           # GO enrichment results
    +-- kegg_enrichment.csv         # KEGG enrichment results
    +-- pathway_heatmap.pdf         # GSVA heatmap visualization
    +-- enrichment_dotplot.pdf      # clusterProfiler dotplot
    +-- pathway_report.md           # Human-readable pathway summary
```

## Integration

See `analysis_executor.md` for full agent specification. See `paper_loop.md` for stage sequencing.
