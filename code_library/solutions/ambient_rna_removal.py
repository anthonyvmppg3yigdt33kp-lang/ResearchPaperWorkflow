"""
Ambient RNA Removal Solution

Problem: Removing ambient RNA contamination from single-cell/nuclear data.

Usage:
    from solutions.ambient_rna_removal import AmbientCorrector

    corrector = AmbientCorrector()
    adata = corrector.correct(adata, background_samples)
"""
from __future__ import annotations

from typing import Optional
import numpy as np
from anndata import AnnData


class AmbientCorrector:
    """
    Remove ambient RNA contamination usingSoupX or similar methods.

    Supports:
    - Simple ambient correction
    - SoupX-style correction (if soupx available)
    - Reference-based correction
    """

    def __init__(self, method: str = "simple"):
        self.method = method

    def correct(
        self,
        adata: AnnData,
        background_adata: Optional[AnnData] = None,
        contamination_fraction: float = 0.1,
    ) -> AnnData:
        """
        Correct ambient RNA contamination.

        Args:
            adata: AnnData with expression data
            background_adata: AnnData from empty/droplet background
            contamination_fraction: Estimated contamination fraction

        Returns:
            Corrected AnnData
        """
        if not adata.isbacked:
            adata = adata.copy()

        if self.method == "simple":
            return self._simple_correction(adata, contamination_fraction)
        elif self.method == "soupx" and background_adata is not None:
            return self._soupx_correction(adata, background_adata)
        else:
            print(f"Method {self.method} not available, using simple correction")
            return self._simple_correction(adata, contamination_fraction)

    def _simple_correction(
        self,
        adata: AnnData,
        contamination_fraction: float,
    ) -> AnnData:
        """
        Simple ambient correction by subtracting scaled background.

        This is a simplified approach. For proper SoupX correction,
        provide background_adata.
        """
        X = adata.X

        # Simple model: X_corrected = X - contamination_fraction * background
        # Assuming uniform contamination
        corrected = X * (1 - contamination_fraction)

        # Ensure non-negative
        corrected = np.maximum(corrected, 0)

        adata.X = corrected
        adata.obs["ambient_contamination_fraction"] = contamination_fraction

        return adata

    def _soupx_correction(
        self,
        adata: AnnData,
        background_adata: AnnData,
    ) -> AnnData:
        """
        SoupX-style ambient correction.

        Estimates contamination fraction per cluster and subtracts accordingly.
        """
        # Calculate contamination fraction per cluster
        clusters = adata.obs.get("cluster", None)
        if clusters is None:
            return self._simple_correction(adata, 0.1)

        contamination_fractions = {}

        for cluster in clusters.unique():
            cluster_mask = clusters == cluster
            cluster_genes = adata[cluster_mask].X.mean(axis=0)
            background_genes = background_adata.X.mean(axis=0)

            # Simple ratio estimation
            with np.errstate(divide='ignore', invalid='ignore'):
                ratio = np.nan_to_num(cluster_genes / (background_genes + 1e-6), 0)
                contamination_fractions[cluster] = np.percentile(ratio, 10) / (1 + np.percentile(ratio, 10))

        # Apply per-cluster correction
        X = adata.X.copy()
        for cluster, frac in contamination_fractions.items():
            cluster_mask = clusters == cluster
            X[cluster_mask] = X[cluster_mask] * (1 - frac)

        adata.X = np.maximum(X, 0)
        adata.obs["ambient_contamination_fraction"] = adata.obs["cluster"].map(contamination_fractions)

        return adata


def quick_correct(adata: AnnData, contamination: float = 0.1) -> AnnData:
    """Quick ambient correction with fixed contamination fraction."""
    corrector = AmbientCorrector(method="simple")
    return corrector.correct(adata, contamination_fraction=contamination)
