---
name: spatial_analysis
description: Spatial transcriptomics analysis — deconvolution, spatial domain detection, spatially variable gene (SVG) detection, spatial statistics, and region segmentation. 空间转录组分析。触发词：spatial, stereo-seq, visium, deconvolution, spatial domain, SVG, 空间转录组, 解卷积.
version: "1.0"
paper_loop_stages: "7"
agent: analysis_executor
type: skill
---

# Spatial Analysis Skill

Specialized analysis for spatially-resolved transcriptomics data (Stereo-seq, Visium, Slide-seq, MERFISH, Xenium, CosMx). Executed during Stage 7 (`run_analysis`).

## Pipeline Position
Stage 7 (`run_analysis`) — executed by `analysis_executor` when research domain = spatial transcriptomics.

## Analysis Methods

### 1. Spatial Deconvolution
- **Reference-based**: RCTD, SPOTlight, cell2location, SpatialDWLS
- **Reference-free**: STdeconvolve, STRIDE
- **SpecWeight NNLS + Anatomical Prior + Sinkhorn-Knopp** (preferred pipeline)

### 2. Spatial Domain Detection
- **Graph-based**: Spatial neighborhood graph + Leiden/Louvain clustering
- **Bayesian**: BayesSpace spatial enhancement + clustering
- **Deep learning**: SpaGCN, STAGATE
- **Morphological**: Graph-based region segmentation with edge detection

### 3. Spatially Variable Gene Detection
- **Statistical**: SpatialDE, SPARK-X, nnSVG
- **Permutation-based**: Moran's I, Geary's C
- **Trendsceek**: Non-parametric spatial trend detection

### 4. Spatial Statistics
- **Ligand-Receptor**: CellChat, NicheNet, COMMOT (spatial-aware)
- **Colocalization**: Spatial cross-correlation, Morisita-Horn overlap
- **Boundary analysis**: Differential expression across spatial boundaries

## Code Library Integration

The `code_library/` provides reusable patterns for spatial analysis:
- `patterns/clustering/leiden_clustering.py` — Leiden clustering with silhouette auto-select
- `patterns/clustering/multi_resolution.py` — Multi-resolution comparison
- `modules/cell_type_annotation.py` — Marker-based annotation
- `solutions/doublet_detection.py` — Scrublet + statistical doublet detection

## Output Files

```
papers/{paper_id}/results/
+-- spatial/
    +-- deconvolution_proportions.csv   # Per-spot cell type proportions
    +-- spatial_domains.csv             # Domain assignments per spot
    +-- svg_results.csv                 # Spatially variable gene statistics
    +-- domain_boundaries.geojson       # Spatial boundary coordinates
    +-- ligand_receptor_interactions.csv # Spatial LR analysis
```

## Integration

See `analysis_executor.md` for full agent specification. See `paper_loop.md` for stage sequencing.
