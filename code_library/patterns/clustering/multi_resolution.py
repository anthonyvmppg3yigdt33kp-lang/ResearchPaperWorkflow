"""
Cell Filter Pattern - Gene and count based cell filtering.

Usage:
    from patterns.qc.cell_filter_pattern import CellFilter

    filterer = CellFilter()
    adata_filtered = filterer.apply(adata, min_genes=200, min_cells=3)
"""
from __future__ import annotations

from typing import Optional

import scanpy as sc
from anndata import AnnData


class CellFilter:
    """
    Filter cells based on gene count and count depth.

    Criteria:
    - min_genes: Minimum number of genes expressed
    - min_cells: Minimum number of cells for gene to be included
    - min_counts: Minimum total counts per cell
    """

    def __init__(
        self,
        min_genes: int = 200,
        min_cells: int = 3,
        min_counts: Optional[int] = None
    ):
        self.min_genes = min_genes
        self.min_cells = min_cells
        self.min_counts = min_counts

    def calculate_metrics(self, adata: AnnData) -> AnnData:
        """
        Calculate cell QC metrics.

        Args:
            adata: AnnData object

        Returns:
            AnnData with metrics in obs
        """
        adata.obs["n_genes"] = (adata.X > 0).sum(axis=1)
        adata.obs["n_counts"] = adata.X.sum(axis=1)
        return adata

    def apply(
        self,
        adata: AnnData,
        min_genes: Optional[int] = None,
        min_cells: Optional[int] = None,
        min_counts: Optional[int] = None,
        inplace: bool = False
    ) -> AnnData:
        """
        Apply cell filters.

        Args:
            adata: AnnData object
            min_genes: Override minimum genes
            min_cells: Override minimum cells for genes
            min_counts: Override minimum counts
            inplace: Modify in place

        Returns:
            Filtered AnnData
        """
        if not inplace:
            adata = adata.copy()

        # Calculate metrics
        adata = self.calculate_metrics(adata)

        # Determine thresholds
        min_g = min_genes if min_genes is not None else self.min_genes
        min_c = min_cells if min_cells is not None else self.min_cells
        min_cnt = min_counts if min_counts is not None else self.min_counts

        # Apply filters
        n_before = adata.n_obs

        # Filter by gene count
        adata = adata[adata.obs["n_genes"] >= min_g].copy()

        # Filter by counts if specified
        if min_cnt is not None:
            adata = adata[adata.obs["n_counts"] >= min_cnt].copy()

        n_after = adata.n_obs
        retention = n_after / n_before if n_before > 0 else 0

        print(f"Cell Filter: {n_before} -> {n_after} ({retention:.1%}) cells retained")
        print(f"  min_genes >= {min_g}, min_counts >= {min_cnt}")

        return adata

    def filter_genes(
        self,
        adata: AnnData,
        min_cells: Optional[int] = None,
        inplace: bool = False
    ) -> AnnData:
        """
        Filter genes by minimum cell count.

        Args:
            adata: AnnData object
            min_cells: Minimum cells expressing gene
            inplace: Modify in place

        Returns:
            AnnData with filtered genes
        """
        min_c = min_cells if min_cells is not None else self.min_cells

        if not inplace:
            adata = adata.copy()

        n_var_before = adata.n_vars
        sc.pp.filter_genes(adata, min_cells=min_c)
        n_var_after = adata.n_vars

        print(f"Gene Filter: {n_var_before} -> {n_var_after} genes retained")
        print(f"  min_cells >= {min_c}")

        return adata


def filter_cells(
    adata: AnnData,
    min_genes: int = 200,
    min_counts: Optional[int] = None
) -> AnnData:
    """
    Convenience function for cell filtering.

    Args:
        adata: AnnData object
        min_genes: Minimum genes per cell
        min_counts: Minimum counts per cell

    Returns:
        Filtered AnnData
    """
    filterer = CellFilter(min_genes=min_genes, min_counts=min_counts)
    return filterer.apply(adata)
