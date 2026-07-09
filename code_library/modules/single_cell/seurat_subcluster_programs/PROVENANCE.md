# Provenance

- Module ID: `single_cell.seurat_subcluster_programs.v1`
- Source type: workflow built-in wrapper
- Upstream method context: official Seurat PBMC3K tutorial workflow
- Upstream URL: https://satijalab.org/seurat/articles/pbmc3k_tutorial.html
- Validation role: TargetTask workflow-test and exploratory subcluster program scoring
- Claim boundary: no disease, clinical, treatment-response, or causal immune-state claim

The wrapper records Seurat session information, source maps, marker columns,
program-score summaries, and a fail-closed subcluster QA report.
