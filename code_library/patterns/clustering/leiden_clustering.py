"""
Leiden Clustering Pattern - Leiden clustering with automatic resolution selection.

Usage:
    from patterns.clustering.leiden_clustering import LeidenClusterer

    clusterer = LeidenClusterer()
    adata = clusterer.cluster(adata, resolutions=[0.2, 0.4, 0.6, 0.8])
"""
from __future__ import annotations

from typing import Optional

import numpy as np
import scanpy as sc
from anndata import AnnData


class LeidenClusterer:
    """
    Leiden clustering with multi-resolution and automatic selection.

    Uses silhouette score to select optimal resolution.
    """

    def __init__(
        self,
        resolutions: list[float] = None,
        silhouette_min: float = 0.3,
        n_neighbors: int = 15,
        metric: str = "euclidean"
    ):
        self.resolutions = resolutions or [0.2, 0.4, 0.6, 0.8, 1.0]
        self.silhouette_min = silhouette_min
        self.n_neighbors = n_neighbors
        self.metric = metric

    def cluster(
        self,
        adata: AnnData,
        resolutions: Optional[list[float]] = None,
        n_neighbors: Optional[int] = None,
        metric: Optional[str] = None,
        inplace: bool = False
    ) -> AnnData:
        """
        Perform Leiden clustering at multiple resolutions.

        Args:
            adata: AnnData object (should have PCA computed)
            resolutions: List of resolutions to test
            n_neighbors: Number of neighbors for graph construction
            metric: Distance metric
            inplace: Modify in place

        Returns:
            AnnData with clustering results
        """
        if not inplace:
            adata = adata.copy()

        resolutions = resolutions or self.resolutions
        n_neighbors = n_neighbors or self.n_neighbors
        metric = metric or self.metric

        # Compute neighborhood graph if needed
        if "connectivities" not in adata.obsp:
            sc.pp.neighbors(adata, n_neighbors=n_neighbors, metric=metric)

        # Run clustering at each resolution
        results = []
        for res in resolutions:
            adata_temp = adata.copy()
            sc.tl.leiden(adata_temp, resolution=res, key_added=f"leiden_{res}")

            # Calculate silhouette score
            sil_score = self._calculate_silhouette(adata_temp, f"leiden_{res}")

            results.append({
                "resolution": res,
                "n_clusters": adata_temp.obs[f"leiden_{res}"].nunique(),
                "silhouette": sil_score,
                "adata": adata_temp
            })

            print(f"Resolution {res}: {adata_temp.obs[f'leiden_{res}'].nunique()} clusters, "
                  f"silhouette={sil_score:.3f}")

        # Select best resolution
        best = max(results, key=lambda x: x["silhouette"])

        print(f"\nSelected resolution: {best['resolution']} "
              f"(silhouette={best['silhouette']:.3f})")

        # Copy best clustering to adata
        res_col = f"leiden_{best['resolution']}"
        adata.obs["leiden"] = best["adata"].obs[res_col]
        adata.obs["leiden"] = adata.obs["leiden"].astype(str)

        # Store multi-resolution results
        for res in resolutions:
            adata.obs[f"leiden_{res}"] = best["adata"].obs[f"leiden_{res}"].astype(str)

        adata.uns["leiden_resolutions"] = resolutions
        adata.uns["leiden_best_resolution"] = best["resolution"]

        return adata

    def _calculate_silhouette(
        self,
        adata: AnnData,
        cluster_col: str,
        embedding_key: str = "X_pca"
    ) -> float:
        """
        Calculate silhouette score for clustering.

        Args:
            adata: AnnData object
            cluster_col: Column name with cluster labels
            embedding_key: Key for embedding (e.g., "X_pca", "X_umap")

        Returns:
            Mean silhouette score
        """
        try:
            from sklearn.metrics import silhouette_score

            if embedding_key not in adata.obsm:
                return 0.0

            labels = adata.obs[cluster_col].astype(str)
            if labels.nunique() < 2:
                return 0.0

            X = adata.obsm[embedding_key]
            if X.shape[0] != len(labels):
                return 0.0

            score = silhouette_score(X, labels)
            return float(score)
        except ImportError:
            # sklearn not available, return placeholder
            return 0.0
        except Exception:
            return 0.0

    def select_resolution(
        self,
        adata: AnnData,
        target_silhouette: float = None
    ) -> float:
        """
        Select optimal resolution based on silhouette score.

        Args:
            adata: AnnData with multi-resolution clustering
            target_silhouette: Target silhouette score

        Returns:
            Selected resolution
        """
        if target_silhouette is None:
            target_silhouette = self.silhouette_min

        best_res = None
        best_score = -1

        for res in self.resolutions:
            col = f"leiden_{res}"
            if col not in adata.obs:
                continue

            score = self._calculate_silhouette(adata, col)
            if score > best_score:
                best_score = score
                best_res = res

        return best_res


def leiden_cluster(
    adata: AnnData,
    resolutions: list[float] = None,
    **kwargs
) -> AnnData:
    """
    Convenience function for Leiden clustering.

    Args:
        adata: AnnData object
        resolutions: List of resolutions
        **kwargs: Additional arguments

    Returns:
        AnnData with clustering
    """
    clusterer = LeidenClusterer(resolutions=resolutions)
    return clusterer.cluster(adata, **kwargs)
