# Seurat PBMC3K Basic Workflow Provenance

- Official tutorial: https://satijalab.org/seurat/articles/pbmc3k_tutorial.html
- Tutorial data URL: https://cf.10xgenomics.com/samples/cell/pbmc3k/pbmc3k_filtered_gene_bc_matrices.tar.gz
- Local wrapper: `main.R`
- Boundary: this module validates the workflow's method-asset planning and execution path. PBMC3K tutorial outputs are not project-specific biological evidence.

The wrapper preserves the tutorial's core sequence: read 10X data, create a Seurat object, calculate mitochondrial percentage, filter cells, normalize, select variable features, scale, run PCA, cluster, run UMAP, and plot marker features. It adds command-line parameters, scoped output directories, source maps, and session information.
