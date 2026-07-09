#!/usr/bin/env Rscript

cat("Pseudobulk DESeq2 environment bootstrap plan\n")
cat("Run in an approved R session if packages are missing:\n")
cat("install.packages(c('BiocManager', 'Matrix', 'ggplot2'))\n")
cat("BiocManager::install(c('DESeq2'))\n")
cat("Then verify with: Rscript scripts/check_r_bioc_environment.R DESeq2 Matrix ggplot2 --json\n")
