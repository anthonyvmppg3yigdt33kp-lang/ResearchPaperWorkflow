#!/usr/bin/env Rscript

args <- commandArgs(trailingOnly = TRUE)
out <- if (length(args) > 0) args[[1]] else file.path("data", "raw", "pbmc3k")
url <- "https://cf.10xgenomics.com/samples/cell/pbmc3k/pbmc3k_filtered_gene_bc_matrices.tar.gz"
dir.create(out, recursive = TRUE, showWarnings = FALSE)
archive <- file.path(out, "pbmc3k_filtered_gene_bc_matrices.tar.gz")
if (!file.exists(archive)) {
  download.file(url, archive, mode = "wb", quiet = FALSE)
}
untar(archive, exdir = out)
cat("PBMC3K data available under:", normalizePath(out, winslash = "/", mustWork = TRUE), "\n")
