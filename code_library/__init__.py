"""
Code Library — Reusable analysis patterns, snippets, solutions, and modules.

Index of available patterns:
  patterns/qc/mt_filter.py         — MT% filtering with tissue-specific thresholds
  patterns/clustering/leiden_clustering.py — Leiden clustering with silhouette auto-select
  patterns/clustering/multi_resolution.py  — Multi-resolution clustering comparison
  snippets/h5ad_io.py              — Safe h5ad read/write with validation
  snippets/logging_setup.py        — Structured logging configuration
  snippets/yaml_config.py          — YAML config loader
  solutions/doublet_detection.py   — Scrublet + statistical doublet detection
  solutions/ambient_rna_removal.py — SoupX + simple ambient RNA correction
  solutions/ensembl_to_symbol.py   — Ensembl ID → gene symbol conversion
  modules/cell_type_annotation.py  — Marker-based cell type annotation
  r/bioinformatics_analysis.R      — R module: Seurat, DE, WGCNA, GSVA, visualization

Usage:
    from code_library.patterns.qc.mt_filter import MTFilter
    from code_library.patterns.clustering.leiden_clustering import LeidenClusterer
    from code_library.snippets.h5ad_io import read_h5ad_safe, write_h5ad_safe
    from code_library.solutions.doublet_detection import DoubletFinder
    from code_library.modules.cell_type_annotation import marker_based_annotation
"""

__all__ = [
    "mt_filter", "leiden_clustering", "multi_resolution",
    "h5ad_io", "logging_setup", "yaml_config",
    "doublet_detection", "ambient_rna_removal", "ensembl_to_symbol",
    "cell_type_annotation", "bioinformatics_analysis",
]
