#!/usr/bin/env Rscript

args <- commandArgs(trailingOnly = TRUE)
extra <- args[args != "--json"]
packages <- if (length(extra) > 0) extra else c("DESeq2", "edgeR", "limma", "WGCNA", "fgsea", "clusterProfiler", "GSVA", "ggplot2")
missing <- packages[!vapply(packages, requireNamespace, quietly = TRUE, FUN.VALUE = logical(1))]
status <- if (length(missing) == 0) "pass" else "blocked"
arr <- function(x) paste0("[", paste(sprintf('\"%s\"', x), collapse = ","), "]")
if ("--json" %in% args) {
  cat(paste0(
    "{",
    "\"schema_version\":\"r_bioc_environment_check.v1\",",
    "\"status\":\"", status, "\",",
    "\"required_packages\":", arr(packages), ",",
    "\"missing_packages\":", arr(missing),
    "}\n"
  ))
} else {
  cat("R/Bioconductor environment status:", status, "\n")
  if (length(missing) > 0) cat("Missing:", paste(missing, collapse = ", "), "\n")
}
quit(status = if (status == "pass") 0 else 1)
