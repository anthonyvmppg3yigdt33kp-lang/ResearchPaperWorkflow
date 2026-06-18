# =============================================================================
# R Package Version Lock — {project_name}
# Generated: {date}
# Purpose: Record R environment for reproducibility per journal requirements.
#
# Usage:
#   1. Edit required_packages below to list packages used by your project.
#   2. Run: Rscript code_library/snippets/package_lock.R
#   3. Outputs:
#      - logs/00_session_info.log    (full sessionInfo)
#      - R_VERSION_LOCK.csv          (version table of required packages)
#      - Console: install status for each required package
#
# This file is a generalized template. Copy it to your run's code/ directory
# and customize required_packages. Paths use dirname() relative to script
# location — no hardcoded absolute paths needed after you place the script.
# =============================================================================

# --- REQUIRED PACKAGES (edit this list for your project) ---
required_packages <- c(
  # RNA-seq / differential expression
  "limma", "edgeR", "DESeq2",
  # Enrichment analysis
  "clusterProfiler", "org.Hs.eg.db", "enrichplot", "DOSE",
  # GSEA / GSVA
  "fgsea", "GSVA", "msigdbr",
  # Visualization
  "ggplot2", "pheatmap", "EnhancedVolcano", "ggrepel",
  "factoextra", "RColorBrewer",
  # Data manipulation
  "dplyr", "tidyr", "tibble",
  # WGCNA
  "WGCNA", "dynamicTreeCut",
  # Single-cell / spatial
  "Seurat", "SeuratObject",
  # Bioconductor infrastructure
  "BiocManager"
)

# --- Locate run directory relative to this script ---
# Assumes: this script is at <run_dir>/code/00_package_lock.R
#          or at <project_root>/code_library/snippets/package_lock.R
SCRIPT_DIR <- tryCatch(
  dirname(sys.frame(1)$ofile),
  error = function(e) getwd()
)

# If called from code_library/snippets/, write to current working directory
# If called from a run's code/, write to the run directory's parent
if (basename(dirname(SCRIPT_DIR)) == "snippets") {
  # Using the template directly — write outputs to cwd
  OUTPUT_DIR <- file.path(getwd(), "env_lock_output")
  dir.create(OUTPUT_DIR, showWarnings = FALSE, recursive = TRUE)
  dir.create(file.path(OUTPUT_DIR, "logs"), showWarnings = FALSE, recursive = TRUE)
} else {
  # In a run directory: code/00_package_lock.R -> run_dir/
  OUTPUT_DIR <- dirname(SCRIPT_DIR)
  dir.create(file.path(OUTPUT_DIR, "logs"), showWarnings = FALSE, recursive = TRUE)
}

# --- Check installed packages ---
installed <- as.data.frame(installed.packages()[, c("Package", "Version", "Built")])
rownames(installed) <- NULL

cat("============================================\n")
cat("  R Environment Lock — {project_name}        \n")
cat("============================================\n\n")

cat(sprintf("R Version: %s\n", R.version$version.string))
cat(sprintf("Platform:  %s\n", R.version$platform))
cat(sprintf("Date:      %s\n\n", Sys.time()))

cat("--- Required Packages Status ---\n")
for (pkg in required_packages) {
  if (pkg %in% installed$Package) {
    ver <- installed$Version[installed$Package == pkg]
    cat(sprintf("  [OK]   %-30s v%s\n", pkg, ver))
  } else {
    cat(sprintf("  [MISS] %-30s — NOT INSTALLED\n", pkg))
  }
}

cat(sprintf("\nTotal installed packages: %d\n", nrow(installed)))
cat(sprintf("Required packages available: %d/%d\n",
            sum(required_packages %in% installed$Package),
            length(required_packages)))

# --- Save full session info ---
sink(file.path(OUTPUT_DIR, "logs", "00_session_info.log"))
cat(sprintf("Session Info — %s\n\n", Sys.time()))
sessionInfo()
sink()

cat(sprintf("\nSession info saved to %s\n",
    normalizePath(file.path(OUTPUT_DIR, "logs", "00_session_info.log"))))

# --- Write version lock file ---
lock_file <- file.path(OUTPUT_DIR, "R_VERSION_LOCK.csv")
all_pkgs <- installed[installed$Package %in% required_packages, ]
# Also record packages that weren't found
missing_pkgs <- setdiff(required_packages, installed$Package)
if (length(missing_pkgs) > 0) {
  missing_rows <- data.frame(
    Package = missing_pkgs,
    Version = "NOT_INSTALLED",
    Built   = NA,
    stringsAsFactors = FALSE
  )
  all_pkgs <- rbind(all_pkgs, missing_rows)
}
write.csv(all_pkgs, lock_file, row.names = FALSE)
cat(sprintf("Version lock saved to %s (%d packages, %d missing)\n",
    normalizePath(lock_file), nrow(all_pkgs), length(missing_pkgs)))

# --- Summary for CI / agent parsing ---
cat("\n--- PACKAGE_LOCK_SUMMARY ---\n")
cat(sprintf("R_VERSION=%s\n", R.version$version.string))
cat(sprintf("INSTALLED=%d\n", sum(required_packages %in% installed$Package)))
cat(sprintf("MISSING=%d\n", length(missing_pkgs)))
if (length(missing_pkgs) > 0) {
  cat(sprintf("MISSING_LIST=%s\n", paste(missing_pkgs, collapse = ",")))
}
cat("--- END_PACKAGE_LOCK_SUMMARY ---\n")
