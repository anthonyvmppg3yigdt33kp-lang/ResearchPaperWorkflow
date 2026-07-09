# Seurat PBMC3K Basic Workflow

This module is a parameterized, auditable wrapper around the official Seurat PBMC3K tutorial workflow. Researchers can open `main.R` to inspect the full R code path: 10X matrix discovery, `Read10X`, `CreateSeuratObject`, mitochondrial percentage calculation, QC filtering, normalization, variable-feature selection, scaling, PCA, neighbor graph construction, clustering, UMAP, marker feature plotting, source-map writing, and session information export.

Use this asset for workflow validation and tutorial-fixture execution. It is not evidence for a disease mechanism, clinical association, or project-specific biological claim. Real project use requires replacing PBMC3K with project data, reviewing QC thresholds, and recording data registry/source-map provenance.
