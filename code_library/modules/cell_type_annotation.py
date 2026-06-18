"""
Cell type annotation module — marker-based annotation.

Status: MINIMAL. Full implementation (CellTypist, scANVI, consensus voting) deferred.
For reference-based annotation, use the CellTypist path (default in cluster.smk).
"""

import pandas as pd


def marker_based_annotation(adata, marker_dict=None, cluster_key="leiden"):
    """
    Minimal marker-based cell type annotation using cluster marker genes.

    Args:
        adata: AnnData object with clusters computed
        marker_dict: Optional dict of {cell_type: [marker_genes]}
        cluster_key: Key in adata.obs for cluster labels (default: "leiden")

    Returns:
        adata with adata.obs["cell_type"] and adata.obs["cell_type_confidence"]
    """
    import scanpy as sc

    if marker_dict is None:
        raise ValueError(
            "marker_dict is required for marker-based annotation. "
            "Provide a dict of {cell_type: [gene_list]} for known kidney cell types."
        )

    # Rank genes per cluster
    sc.tl.rank_genes_groups(adata, cluster_key, method="wilcoxon")

    # Simple assignment: highest-scoring marker match per cluster
    clusters = adata.obs[cluster_key].cat.categories
    cell_types = list(marker_dict.keys())

    cluster_to_ct = {}
    confidences = {}

    for cluster in clusters:
        best_score = 0
        best_ct = "Unknown"
        for ct, genes in marker_dict.items():
            genes_present = [g for g in genes if g in adata.var_names]
            if not genes_present:
                continue
            expr = adata[adata.obs[cluster_key] == cluster, genes_present].X
            if hasattr(expr, "toarray"):
                expr = expr.toarray()
            mean_expr = expr.mean(axis=0).mean()
            if mean_expr > best_score:
                best_score = mean_expr
                best_ct = ct
        cluster_to_ct[cluster] = best_ct
        confidences[cluster] = min(best_score / 10.0, 1.0)

    adata.obs["cell_type"] = [
        cluster_to_ct.get(c, "Unknown") for c in adata.obs[cluster_key]
    ]
    adata.obs["cell_type_confidence"] = [
        confidences.get(c, 0.0) for c in adata.obs[cluster_key]
    ]

    return adata
