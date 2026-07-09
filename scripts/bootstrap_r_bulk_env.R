#!/usr/bin/env Rscript

cat("Bulk RNA-seq environment bootstrap plan\n")
cat("Run in an approved R session if packages are missing:\n")
cat("install.packages(c('BiocManager', 'WGCNA', 'pheatmap'))\n")
cat("BiocManager::install(c('DESeq2', 'edgeR', 'limma', 'fgsea', 'clusterProfiler', 'GSVA'))\n")
cat("Then verify with: Rscript scripts/check_r_bioc_environment.R --json\n")
