# =============================================================================
# Graceful Fallback Pattern — HAS_PACKAGE Flags for R Analysis Scripts
# Research Paper Workflow Framework
# =============================================================================
#
# Purpose: Every optional R package dependency is guarded by a HAS_<PKG> boolean
# flag. When a package is unavailable, the script degrades gracefully instead of
# crashing — it skips the affected step, logs the reason, and continues with
# remaining steps. All skipped steps are documented for the Phase Report.
#
# This pattern ensures:
#   1. Analysis scripts survive partial R environments (e.g., missing Bioconductor packages)
#   2. All degradations are explicitly logged for audit trail
#   3. The Phase Report can distinguish "not attempted" from "failed"
#   4. Re-running after installing missing packages picks up all steps
#
# =============================================================================
# USAGE PATTERN
# =============================================================================
#
# 1. Define load_pkg() helper at the top of every R script
# 2. Guard every optional package with HAS_<PKG> <- load_pkg("pkgname")
# 3. Check HAS_<PKG> before using the package; provide fallback or skip
# 4. Log all degradations to both console (for agent parsing) and log file
#
# =============================================================================
# TEMPLATE — Copy this block to the top of every R analysis script
# =============================================================================

# --- Package loading with graceful degradation ---
load_pkg <- function(pkg) {
  if (requireNamespace(pkg, quietly = TRUE)) {
    suppressPackageStartupMessages(library(pkg, character.only = TRUE))
    return(TRUE)
  } else {
    return(FALSE)
  }
}

# --- Guard each optional package ---
HAS_WGCNA    <- load_pkg("WGCNA")
HAS_GSVA     <- load_pkg("GSVA")
HAS_LIMMA    <- load_pkg("limma")
HAS_DESEQ2   <- load_pkg("DESeq2")
HAS_CLUSTER  <- load_pkg("clusterProfiler")
HAS_ORGDB    <- load_pkg("org.Hs.eg.db")
HAS_MSIGDBR  <- FALSE
tryCatch({
  suppressPackageStartupMessages(library(msigdbr))
  HAS_MSIGDBR <- TRUE
}, error = function(e) NULL)

# --- Always-load packages (fail if missing) ---
suppressPackageStartupMessages({
  library(ggplot2)
  library(dplyr)
  library(tidyr)
  library(tibble)
})

# --- Log package availability ---
cat("Package status:\n")
cat(sprintf("  Core:     ggplot2,dplyr,tidyr — REQUIRED\n"))
cat(sprintf("  Optional: WGCNA=%s | GSVA=%s | limma=%s | DESeq2=%s | clusterProfiler=%s | org.Hs.eg.db=%s | msigdbr=%s\n",
            HAS_WGCNA, HAS_GSVA, HAS_LIMMA, HAS_DESEQ2, HAS_CLUSTER, HAS_ORGDB, HAS_MSIGDBR))

# =============================================================================
# PATTERN 1: Skip step with log message
# =============================================================================
#
# if (HAS_GSVA) {
#   # Full GSVA analysis
#   gsva_results <- gsva(expr_mat, gene_sets, method = "gsva")
#   cat("  GSVA scoring complete:", nrow(gsva_results), "gene sets\n")
# } else {
#   cat("  [SKIP] GSVA not available — install BiocManager::install('GSVA') then rerun.\n")
#   cat("  [FALLBACK] Using per-sample mean expression as pathway score.\n")
#   gsva_results <- compute_mean_pathway_scores(expr_mat, gene_sets)
# }

# =============================================================================
# PATTERN 2: Multiple fallback paths (try A, then B, then C)
# =============================================================================
#
# gene_sets <- NULL
# if (HAS_MSIGDBR) {
#   # Path A: Download from msigdbr
#   gene_sets <- try_get_msigdbr()
# }
# if (is.null(gene_sets) && file.exists("cached_gene_sets.rds")) {
#   # Path B: Load cached
#   gene_sets <- readRDS("cached_gene_sets.rds")
# }
# if (is.null(gene_sets)) {
#   # Path C: Embedded minimal set
#   gene_sets <- EMBEDDED_HALLMARK_SETS
#   cat("  [FALLBACK] Using embedded gene sets (offline-capable).\n")
# }

# =============================================================================
# PATTERN 3: WGCNA fallback to base R hclust
# =============================================================================
#
# if (HAS_WGCNA) {
#   # Full WGCNA pipeline
#   net <- blockwiseModules(datExpr, power = power, ...)
#   modules <- net$colors
#   hub_genes <- chooseTopHubInEachModule(datExpr, modules)
# } else {
#   # Base R fallback: hierarchical clustering + cutree
#   cat("  [FALLBACK] WGCNA not available — using base R hclust + cutree.\n")
#   dist_mat <- as.dist(1 - cor(t(datExpr), method = "pearson"))
#   hc <- hclust(dist_mat, method = "ward.D2")
#   modules <- cutree(hc, k = 8)
#   # Intra-modular connectivity for hub ranking
#   hub_genes <- sapply(unique(modules), function(m) {
#     genes_in_module <- names(modules)[modules == m]
#     kME <- sapply(genes_in_module, function(g) {
#       mean(abs(cor(datExpr[g, ], t(datExpr[genes_in_module, ]))))
#     })
#     names(which.max(kME))
#   })
# }

# =============================================================================
# PATTERN 4: Degradation log for Phase Report integration
# =============================================================================
#
# degradations <- list()
#
# if (!HAS_WGCNA) {
#   degradations <- c(degradations, list(list(
#     package = "WGCNA",
#     reason  = "Package 'impute' dependency missing",
#     fallback = "base R hclust + cutree",
#     impact  = "No TOM-based module detection; hub ranking uses intra-modular connectivity"
#   )))
# }
#
# # Emit machine-parseable degradation summary at end of script
# if (length(degradations) > 0) {
#   cat("\n--- DEGRADATION_SUMMARY ---\n")
#   for (d in degradations) {
#     cat(sprintf("DEGRADED|%s|%s|%s\n", d$package, d$reason, d$fallback))
#   }
#   cat("--- END_DEGRADATION_SUMMARY ---\n")
# }

# =============================================================================
# INTEGRATION WITH error_log.md
# =============================================================================
#
# Each degradation should produce an ERR-XXX entry in the error log:
#
#   ### [ERR-00N] YYYY-MM-DD HH:MM — <Package> not installed
#   | Field         | Value                           |
#   |---------------|---------------------------------|
#   | **Phase**     | <phase_id>                      |
#   | **Severity**  | Warning                         |
#   | **Status**    | Deferred / Resolved             |
#   | **Raised By** | <script_path>                   |
#   | **Message**   | `there is no package called '<pkg>'` |
#   | **Context**   | <what was being attempted>      |
#   | **Diagnosis** | Package not installed in R library |
#   | **Resolution**| <fallback applied or deferred>  |
#   | **Prevention**| Run 00_package_lock.R before analysis; install missing packages |

# =============================================================================
# QUICK CHECK FUNCTION — call at script start
# =============================================================================

check_required_packages <- function(pkg_list) {
  """Check a list of packages and return a named logical vector.

  Args:
    pkg_list: Character vector of package names.

  Returns:
    Named logical vector: TRUE = available, FALSE = missing.
    Also prints a status table to console.
  """
  status <- sapply(pkg_list, function(p) {
    requireNamespace(p, quietly = TRUE)
  })
  names(status) <- pkg_list

  cat("\n--- PACKAGE CHECK ---\n")
  for (pkg in names(status)) {
    marker <- if (status[pkg]) "[OK]" else "[MISS]"
    cat(sprintf("  %s %s\n", marker, pkg))
  }
  cat(sprintf("  Available: %d/%d\n", sum(status), length(status)))
  cat("--- END PACKAGE CHECK ---\n")

  return(status)
}
