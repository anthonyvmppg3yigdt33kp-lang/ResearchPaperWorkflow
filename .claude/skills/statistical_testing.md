---
name: statistical_testing
description: Statistical testing framework — differential expression, hypothesis testing, power analysis, multiple testing correction, effect size estimation, regression modeling. 统计检验。触发词：statistic, test, p-value, power analysis, regression, effect size, differential expression, 统计检验, 假设检验.
version: "1.0"
paper_loop_stages: "7"
agent: analysis_executor, statistician
type: skill
---

# Statistical Testing Skill

Statistical analysis for bioinformatics and clinical research. Executed during Stage 7 (`run_analysis`) with async cross-validation by `statistician` agent.

## Pipeline Position
Stage 7 (`run_analysis`) — executed by `analysis_executor`, async-audited by `statistician`.

## Statistical Methods

### 1. Differential Expression Analysis
| Method | Package | Use Case |
|--------|---------|----------|
| Wilcoxon rank-sum | `Seurat::FindMarkers` | Single-cell, non-parametric, default |
| DESeq2 | `DESeq2` | Bulk RNA-seq, negative binomial |
| edgeR | `edgeR` | Bulk RNA-seq, empirical Bayes |
| limma-trend / voom | `limma` | Microarray / RNA-seq, linear models |
| MAST | `MAST` | Single-cell, hurdle model |
| t-test / ANOVA | `stats` | Simple two-group / multi-group comparison |

### 2. Multiple Testing Correction
| Method | Package | Notes |
|--------|---------|-------|
| Bonferroni | `stats::p.adjust` | Most conservative |
| Benjamini-Hochberg (FDR) | `stats::p.adjust` | Default for genomics |
| Benjamini-Yekutieli | `stats::p.adjust` | For dependent tests |
| IHW (Independent Hypothesis Weighting) | `IHW` | Increases power vs. BH |

### 3. Effect Size Estimation
| Metric | Use Case | Reporting |
|--------|----------|-----------|
| Cohen's d | Two-group comparison | d + 95% CI |
| Log2 Fold Change | Differential expression | log2FC + SE |
| Odds Ratio (OR) | Logistic regression, case-control | OR + 95% CI |
| Hazard Ratio (HR) | Survival analysis | HR + 95% CI |
| Beta coefficient (beta) | Linear regression | beta + SE + CI |
| Eta-squared / R-squared | ANOVA / variance explained | eta^2 or R^2 |

### 4. Power Analysis
```r
# Two-group t-test
power.t.test(n=NULL, delta=0.5, sd=1, sig.level=0.05, power=0.8)

# Differential expression
# Use ssizeRNA or PROPER for RNA-seq specific power
```

### 5. Statistical Assumptions Checking
| Test | Assumption Checked |
|------|--------------------|
| Shapiro-Wilk | Normality of residuals |
| Levene's / Bartlett's | Homogeneity of variance |
| Variance Inflation Factor (VIF) | Multicollinearity in regression |
| Durbin-Watson | Autocorrelation of residuals |
| Cook's distance | Influential observations |

## Reporting Standards

Every statistical result must include:
1. **Test name** (e.g., "two-sided Wilcoxon rank-sum test")
2. **Test statistic** (e.g., W = 1234)
3. **Exact p-value** (e.g., p = 0.0032, NOT p < 0.05)
4. **Effect size** with confidence interval (e.g., Cohen's d = 0.78, 95% CI [0.45, 1.11])
5. **Sample size** per group (e.g., n = 42 per group)
6. **Multiple testing correction** method and threshold (e.g., FDR < 0.05, Benjamini-Hochberg)
7. **Software + version** (e.g., R 4.3.1, stats v4.3.1)

## Output Files

```
papers/{paper_id}/results/
+-- statistical/
    +-- differential_expression.csv    # DE results with statistics
    +-- effect_sizes.csv               # Effect sizes per comparison
    +-- power_analysis.md              # Power analysis report
    +-- statistical_report.md          # Methods + assumptions + caveats
    +-- assumption_checks.pdf          # Diagnostic plots
```

## Integration

See `analysis_executor.md` and `statistician.md` for agent specifications. See `integrity.py` Gate H7 for statistics reporting requirements.
