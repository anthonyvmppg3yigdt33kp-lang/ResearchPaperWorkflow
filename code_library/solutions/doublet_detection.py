"""
Doublet Detection Solution

Problem: Identifying and removing doublets from single-cell data.

Usage:
    from solutions.doublet_detection import DoubletFinder

    finder = DoubletFinder()
    adata = finder.detect(adata, expected_doublets=0.05)
"""
from __future__ import annotations

from typing import Optional
from pathlib import Path

import numpy as np
from anndata import AnnData


class DoubletFinder:
    """
    Detect doublets using multiple strategies.

    Methods:
    - Scrublet (Python)
    - DoubletFinder (R/Seurat)
    - Statistical detection (via co-localization)
    """

    def __init__(self, method: str = "scrublet"):
        self.method = method

    def detect(
        self,
        adata: AnnData,
        expected_doublets: float = 0.05,
        n_neighbors: int = 15,
    ) -> AnnData:
        """
        Detect doublets in AnnData object.

        Args:
            adata: AnnData object
            expected_doublets: Expected doublet rate (0.0-1.0)
            n_neighbors: Number of neighbors for neighbor graph

        Returns:
            AnnData with doublet predictions in adata.obs['doublet']
        """
        if self.method == "scrublet":
            return self._detect_scrublet(adata, expected_doublets, n_neighbors)
        elif self.method == "statistical":
            return self._detect_statistical(adata, n_neighbors)
        else:
            raise ValueError(f"Unknown method: {self.method}")

    def _detect_scrublet(
        self,
        adata: AnnData,
        expected_doublets: float,
        n_neighbors: int,
    ) -> AnnData:
        """Detect using Scrublet."""
        try:
            import scrublet as scr

            # Prepare counts matrix
            counts = adata.X

            # Initialize Scrublet
            scrub = scr.Scrublet(
                counts=counts,
                expected_doublet_rate=expected_doublets,
                n_neighbors=n_neighbors,
            )

            # Run detection
            doublet_scores, predicted_doublets = scrub.scrub_doublets(
                min_counts=2,
                min_cells=3,
                min_gene_vscore_pval=0.001,
            )

            # Store results
            adata.obs["doublet_score"] = doublet_scores
            adata.obs["doublet"] = predicted_doublets.astype(str)

            return adata

        except ImportError:
            print("Scrublet not installed, falling back to statistical method")
            return self._detect_statistical(adata, n_neighbors)

    def _detect_statistical(
        self,
        adata: AnnData,
        n_neighbors: int,
    ) -> AnnData:
        """Statistical doublet detection based on UMI counts and gene counts."""
        # Calculate simple metrics
        n_counts = np.asarray(adata.X.sum(axis=1)).flatten()
        n_genes = np.asarray((adata.X > 0).sum(axis=1)).flatten()

        # Doublets tend to have high counts AND high genes
        count_zscore = (n_counts - np.mean(n_counts)) / np.std(n_counts)
        gene_zscore = (n_genes - np.mean(n_genes)) / np.std(n_genes)

        # Combined score
        doublet_score = (count_zscore + gene_zscore) / 2

        adata.obs["doublet_score"] = doublet_score
        adata.obs["doublet"] = (doublet_score > 1.5).astype(str)

        return adata


def remove_doublets(adata: AnnData, path: Optional[Path] = None) -> AnnData:
    """
    Remove predicted doublets from AnnData.

    Args:
        adata: AnnData with doublet predictions
        path: Optional path to save filtered data

    Returns:
        AnnData without doublets
    """
    if "doublet" not in adata.obs:
        raise ValueError("No doublet predictions found. Run detect() first.")

    n_before = adata.n_obs
    adata = adata[adata.obs["doublet"] == "False"].copy()
    n_after = adata.n_obs

    print(f"Removed {n_before - n_after} doublets ({100*(n_before-n_after)/n_before:.1f}%)")

    if path:
        adata.write_h5ad(path)
        print(f"Saved to {path}")

    return adata
