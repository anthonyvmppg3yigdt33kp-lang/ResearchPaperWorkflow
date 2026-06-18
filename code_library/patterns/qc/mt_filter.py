"""
MT Percentage Filter Pattern

Reusable pattern for filtering cells with high mitochondrial content.
Supports tissue-type specific thresholds.

Usage:
    from patterns.qc.mt_filter_pattern import MTFilter

    filterer = MTFilter()
    adata_filtered = filterer.apply(adata, tissue_type="ffpe")
"""
from __future__ import annotations

from typing import Optional

import scanpy as sc
from anndata import AnnData


class MTFilter:
    """
    Mitochondrial content filter with tissue-type specific thresholds.

    Thresholds:
    - fresh: MT% < 25%
    - ffpe: MT% < 40%
    - kidney_fresh: MT% < 25%
    - kidney_ffpe: MT% < 40%
    """

    DEFAULT_THRESHOLDS = {
        "fresh": 25,
        "ffpe": 40,
        "kidney_fresh": 25,
        "kidney_ffpe": 40,
        "brain": 20,
        "tumor": 30,
    }

    def __init__(self, custom_thresholds: Optional[dict] = None):
        """
        Initialize MT filter.

        Args:
            custom_thresholds: Override default thresholds
        """
        self.thresholds = self.DEFAULT_THRESHOLDS.copy()
        if custom_thresholds:
            self.thresholds.update(custom_thresholds)

    def calculate_mt_pct(self, adata: AnnData) -> AnnData:
        """
        Calculate mitochondrial percentage for each cell.

        Args:
            adata: AnnData object

        Returns:
            AnnData with mt_pct in obs
        """
        if "mt" in adata.var_names.str.lower():
            adata.var["mt"] = adata.var_names.str.lower().str.startswith("mt-")
        elif "MT" in adata.var_names:
            adata.var["mt"] = adata.var_names.str.startswith("MT-")
        else:
            # Try to identify MT genes
            adata.var["mt"] = adata.var_names.str.contains("^MT-", regex=True)

        adata.var["mt"] = adata.var["mt"].fillna(False)
        adata.obs["mt_pct"] = (adata[:, adata.var["mt"]].X.sum(axis=1) /
                                adata.X.sum(axis=1) * 100)

        return adata

    def apply(
        self,
        adata: AnnData,
        tissue_type: str = "fresh",
        threshold: Optional[float] = None,
        inplace: bool = False
    ) -> AnnData:
        """
        Filter cells based on mitochondrial content.

        Args:
            adata: AnnData object
            tissue_type: Tissue type for threshold selection
            threshold: Override automatic threshold
            inplace: Modify adata in place

        Returns:
            Filtered AnnData object
        """
        if not inplace:
            adata = adata.copy()

        # Calculate MT percentage
        adata = self.calculate_mt_pct(adata)

        # Determine threshold
        if threshold is None:
            threshold = self.thresholds.get(tissue_type, self.thresholds["fresh"])

        # Apply filter
        n_before = adata.n_obs
        adata = adata[adata.obs["mt_pct"] < threshold].copy()
        n_after = adata.n_obs
        retention = n_after / n_before if n_before > 0 else 0

        print(f"MT Filter: {n_before} -> {n_after} ({retention:.1%}) cells retained")
        print(f"Threshold: MT% < {threshold}% (tissue: {tissue_type})")

        return adata

    def sensitivity_analysis(
        self,
        adata: AnnData,
        tissue_type: str = "fresh",
        thresholds: Optional[list[float]] = None
    ) -> list[dict]:
        """
        Run sensitivity analysis across multiple thresholds.

        Args:
            adata: AnnData object
            tissue_type: Tissue type
            thresholds: List of thresholds to test

        Returns:
            List of results for each threshold
        """
        if thresholds is None:
            thresholds = [15, 20, 25, 30, 35, 40, 45, 50]

        adata = self.calculate_mt_pct(adata)
        results = []

        for thresh in thresholds:
            n_cells = (adata.obs["mt_pct"] < thresh).sum()
            retention = n_cells / adata.n_obs
            results.append({
                "threshold": thresh,
                "n_cells": n_cells,
                "retention": retention
            })

        return results


def filter_mt(
    adata: AnnData,
    tissue_type: str = "fresh",
    threshold: Optional[float] = None
) -> AnnData:
    """
    Convenience function for MT filtering.

    Args:
        adata: AnnData object
        tissue_type: Tissue type
        threshold: Override threshold

    Returns:
        Filtered AnnData
    """
    filterer = MTFilter()
    return filterer.apply(adata, tissue_type=tissue_type, threshold=threshold)
