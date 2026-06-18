---
name: multi_omics
description: Multi-omics integrative analysis — MOFA, DIABLO, mixOmics, cross-omics correlation, factor analysis, multi-modal data fusion. 多组学整合分析。触发词：multi-omics, integration, MOFA, DIABLO, cross-omics, multi-modal, 多组学, 整合分析, 多模态.
version: "1.0"
paper_loop_stages: "7"
agent: multi_omics_integrator, analysis_executor
type: skill
---

# Multi-Omics Integration Skill

Integrative analysis of multiple omics data types (transcriptomics, proteomics, metabolomics, epigenomics, genomics). Executed during Stage 7 (`run_analysis`).

## Pipeline Position
Stage 7 (`run_analysis`) — executed by `multi_omics_integrator` (primary) or `analysis_executor` (fallback) when research domain = multi-omics.

## Integration Methods

### 1. Factor Analysis
| Method | Package | Description |
|--------|---------|-------------|
| MOFA / MOFA2 | `MOFA2` | Multi-Omics Factor Analysis — unsupervised, discovers latent factors across omics |
| DIABLO | `mixOmics` | Supervised integration with discriminant analysis |
| sGCCA | `mixOmics` | Sparse Generalized Canonical Correlation Analysis |
| JIVE | `r.jive` | Joint and Individual Variation Explained |

### 2. Correlation-Based
| Method | Package | Description |
|--------|---------|-------------|
| Cross-omics correlation | `stats::cor` + custom | Spearman/Pearson correlation between omics features |
| Sparse CCA | `PMA` | Sparse Canonical Correlation Analysis |
| WGCNA (multi-omics) | `WGCNA` | Consensus modules across omics data types |

### 3. Network-Based
| Method | Package | Description |
|--------|---------|-------------|
| Multi-omics networks | `igraph` + custom | Merged correlation networks colored by omics type |
| iOmicsPASS | `iOmicsPASS` | Signature-based network integration |
| SNF | `SNFtool` | Similarity Network Fusion |

### 4. Machine Learning Integration
| Method | Package | Description |
|--------|---------|-------------|
| Multi-modal autoencoders | `keras` / `torch` | Deep learning joint latent space |
| Multi-omics random forest | `randomForest` / `ranger` | Feature importance across omics |
| XGBoost multi-view | `xgboost` | Tree-based feature fusion |

## Domain Routing

The `multi_omics_integrator` agent is dispatched when:
- Research domain YAML contains "multi-omics" keyword
- Multiple data types are declared in `data_inventory.yaml`
- `run_analysis` stage spec includes multi-omics analysis steps

## Code Library Integration

The R module `code_library/r/bioinformatics_analysis.R` provides:
- `run_mofa()` — MOFA2 with factor count auto-selection
- `run_diablo()` — DIABLO supervised integration
- `cross_omics_correlation()` — Pairwise correlation between omics layers

## Output Files

```
papers/{paper_id}/results/
+-- multi_omics/
    +-- mofa_factors.csv            # Factor scores per sample
    +-- mofa_weights.csv            # Feature weights per factor
    +-- diablo_results.rds          # DIABLO model object
    +-- cross_omics_correlations.csv # Cross-omics feature correlations
    +-- integration_report.md        # Human-readable integration summary
    +-- factor_heatmap.pdf           # Factor-by-omics heatmap
    +-- variance_explained.pdf       # Variance explained per factor
```

## Integration

See `multi_omics_integrator.md` for full agent specification. See `analysis_executor.md` for standard analysis execution. See `paper_loop.md` for stage sequencing.
