"""
Agent Protocols Module — Autonomous analysis functions for multi-agent coordination.

Provides structured, error-safe wrappers around code_library patterns that return
dict-based results consumable by agents (no raw AnnData objects cross agent boundaries).

Protocols
---------
* ``run_qc_pipeline``     — MT% filtering via MTFilter
* ``run_clustering``       — Leiden clustering with silhouette auto-select
* ``run_doublet_detection`` — Doublet detection (Scrublet / statistical)
* ``run_cell_annotation``  — Marker-based cell type annotation
* ``get_agent_toolkit``    — Returns the function set for a given agent role
* ``execute_analysis``     — Generic dispatcher: protocol_name -> function

All functions accept either a file path (``str``) or an ``anndata.AnnData`` object.
Results are always plain dicts with a ``success`` key and never raise.
"""

from __future__ import annotations

import logging
import sys
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any, Optional, Union

import numpy as np

# ---------------------------------------------------------------------------
# Ensure the project root (where code_library/ lives) is on sys.path.
# The src/paper_workflow package is installed from src/, but code_library/
# sits at the project root and may not be importable without this fallback.
# ---------------------------------------------------------------------------
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

# ---------------------------------------------------------------------------
# Logger
# ---------------------------------------------------------------------------
_logger: Optional[logging.Logger] = None


def _get_logger() -> logging.Logger:
    """Lazily initialise a structured logger for agent protocols."""
    global _logger
    if _logger is None:
        try:
            from code_library.snippets.logging_setup import get_logger
            _logger = get_logger("agent_protocols")
        except ImportError:
            _logger = logging.getLogger("agent_protocols")
            _logger.setLevel(logging.INFO)
            if not _logger.handlers:
                h = logging.StreamHandler(sys.stdout)
                h.setFormatter(logging.Formatter(
                    "%(asctime)s | %(levelname)-8s | %(message)s"
                ))
                _logger.addHandler(h)
    return _logger


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _load_adata(adata_path: Union[str, "AnnData"]) -> "AnnData":  # noqa: F821
    """Accept a path or an AnnData, return an AnnData.

    Raises ``FileNotFoundError`` or ``ValueError`` on failure — callers
    should wrap in try/except.
    """
    # Lazy import so the module is importable without anndata installed.
    from anndata import AnnData

    if isinstance(adata_path, AnnData):
        return adata_path

    if isinstance(adata_path, (str, Path)):
        from code_library.snippets.h5ad_io import read_h5ad_safe
        return read_h5ad_safe(str(adata_path))

    raise TypeError(
        f"adata_path must be str, Path, or AnnData, got {type(adata_path).__name__}"
    )


def _make_error(
    func_name: str,
    exc: Exception,
    params: dict[str, Any],
) -> dict[str, Any]:
    """Build a standardised error result dict."""
    _get_logger().error(
        "%s failed: %s",
        func_name, exc,
        extra={"params": str(params)},
    )
    return {
        "success": False,
        "function": func_name,
        "error": f"{type(exc).__name__}: {exc}",
        "traceback": traceback.format_exc(),
        "params_logged": params,
        "timestamp": datetime.now().isoformat(),
    }


def _make_success(
    func_name: str,
    metrics: dict[str, Any],
    params: dict[str, Any],
) -> dict[str, Any]:
    """Build a standardised success result dict."""
    _get_logger().info(
        "%s completed — %s",
        func_name,
        ", ".join(f"{k}={v}" for k, v in metrics.items()),
        extra=params,
    )
    return {
        "success": True,
        "function": func_name,
        "metrics": metrics,
        "timestamp": datetime.now().isoformat(),
    }


# =============================================================================
# Protocol 1 — QC Pipeline (MT filtering)
# =============================================================================

def run_qc_pipeline(
    adata_path: Union[str, "AnnData"],  # noqa: F821
    tissue_type: str = "fresh",
    output_dir: Optional[str] = None,
) -> dict[str, Any]:
    """Run mitochondrial-content QC filtering.

    Uses ``code_library.patterns.qc.mt_filter.MTFilter`` with
    tissue-type-specific thresholds.

    Parameters
    ----------
    adata_path:
        Path to an ``.h5ad`` file or an in-memory ``AnnData``.
    tissue_type:
        One of ``fresh``, ``ffpe``, ``kidney_fresh``, ``kidney_ffpe``,
        ``brain``, ``tumor``.  Defaults to ``fresh`` (25 % cut-off).
    output_dir:
        If provided and *adata_path* is a file path, write the filtered
        AnnData to ``<output_dir>/qc_filtered.h5ad``.

    Returns
    -------
    dict
        ``{success, function, metrics: {n_before, n_after, retention_pct,
        mt_threshold, tissue_type}, timestamp}``
        On failure, ``success`` is ``False`` and ``error`` / ``traceback``
        are present.
    """
    params = {
        "tissue_type": tissue_type,
        "output_dir": output_dir,
        "adata_path_type": "AnnData" if not isinstance(adata_path, (str, Path)) else str(adata_path),
    }
    _get_logger().info("run_qc_pipeline starting — tissue_type=%s", tissue_type)

    try:
        from code_library.patterns.qc.mt_filter import MTFilter

        adata = _load_adata(adata_path)
        n_before = adata.n_obs

        filterer = MTFilter()
        mt_threshold = filterer.thresholds.get(tissue_type, filterer.thresholds["fresh"])
        adata_filtered = filterer.apply(adata, tissue_type=tissue_type, inplace=False)

        n_after = adata_filtered.n_obs
        retention_pct = round(n_after / n_before * 100, 2) if n_before > 0 else 0.0

        # Optionally write output
        if output_dir is not None and isinstance(adata_path, (str, Path)):
            out_path = Path(output_dir) / "qc_filtered.h5ad"
            try:
                from code_library.snippets.h5ad_io import write_h5ad_safe
                write_h5ad_safe(adata_filtered, str(out_path))
                _get_logger().info("QC output written to %s", out_path)
            except Exception as write_exc:
                _get_logger().warning("Failed to write QC output: %s", write_exc)

        metrics = {
            "n_before": n_before,
            "n_after": n_after,
            "retention_pct": retention_pct,
            "mt_threshold": mt_threshold,
            "tissue_type": tissue_type,
        }
        return _make_success("run_qc_pipeline", metrics, params)

    except Exception as exc:
        return _make_error("run_qc_pipeline", exc, params)


# =============================================================================
# Protocol 2 — Leiden Clustering
# =============================================================================

def run_clustering(
    adata_path: Union[str, "AnnData"],  # noqa: F821
    resolutions: Optional[list[float]] = None,
    n_neighbors: int = 15,
) -> dict[str, Any]:
    """Run Leiden clustering with automatic resolution selection.

    Uses ``code_library.patterns.clustering.leiden_clustering.LeidenClusterer``.
    Silhouette score is used to select the best resolution.

    **Precondition**: the AnnData should have PCA computed (``adata.obsm["X_pca"]``).
    If not present, silhouette scores will be 0.0 and the default resolution wins.

    Parameters
    ----------
    adata_path:
        Path to ``.h5ad`` or an in-memory ``AnnData``.
    resolutions:
        Resolutions to evaluate. Defaults to ``[0.2, 0.4, 0.6, 0.8, 1.0]``.
    n_neighbors:
        Neighbors for the kNN graph (default 15).

    Returns
    -------
    dict
        ``{success, function, metrics: {best_resolution, n_clusters,
        silhouette_scores: {res: score, ...}, resolutions_tested,
        n_neighbors}, timestamp}``
    """
    if resolutions is None:
        resolutions = [0.2, 0.4, 0.6, 0.8, 1.0]

    params = {
        "resolutions": resolutions,
        "n_neighbors": n_neighbors,
        "adata_path_type": "AnnData" if not isinstance(adata_path, (str, Path)) else str(adata_path),
    }
    _get_logger().info(
        "run_clustering starting — resolutions=%s, n_neighbors=%d",
        resolutions, n_neighbors,
    )

    try:
        from code_library.patterns.clustering.leiden_clustering import LeidenClusterer

        adata = _load_adata(adata_path)

        clusterer = LeidenClusterer(
            resolutions=resolutions,
            n_neighbors=n_neighbors,
        )
        adata = clusterer.cluster(adata, resolutions=resolutions, n_neighbors=n_neighbors)

        best_res = adata.uns.get("leiden_best_resolution", resolutions[0])
        n_clusters = adata.obs["leiden"].nunique()

        # Collect silhouette scores per resolution
        silhouette_scores: dict[str, float] = {}
        for res in resolutions:
            col = f"leiden_{res}"
            if col in adata.obs:
                sil = clusterer._calculate_silhouette(adata, col)
                silhouette_scores[str(res)] = round(float(sil), 4)

        metrics = {
            "best_resolution": float(best_res) if isinstance(best_res, (int, float, np.floating)) else best_res,
            "n_clusters": int(n_clusters),
            "silhouette_scores": silhouette_scores,
            "resolutions_tested": len(resolutions),
            "n_neighbors": n_neighbors,
        }
        return _make_success("run_clustering", metrics, params)

    except Exception as exc:
        return _make_error("run_clustering", exc, params)


# =============================================================================
# Protocol 3 — Doublet Detection
# =============================================================================

def run_doublet_detection(
    adata_path: Union[str, "AnnData"],  # noqa: F821
    method: str = "scrublet",
    expected_doublets: float = 0.05,
) -> dict[str, Any]:
    """Detect doublets in single-cell data.

    Uses ``code_library.solutions.doublet_detection.DoubletFinder``.
    Falls back from Scrublet to statistical detection if the ``scrublet``
    package is not installed.

    Parameters
    ----------
    adata_path:
        Path to ``.h5ad`` or an in-memory ``AnnData``.
    method:
        ``"scrublet"`` (default) or ``"statistical"``.
    expected_doublets:
        Expected doublet rate (0.0-1.0). Default 0.05 (5 %).

    Returns
    -------
    dict
        ``{success, function, metrics: {n_doublets, pct_doublets, method,
        n_total, mean_doublet_score}, timestamp}``
    """
    params = {
        "method": method,
        "expected_doublets": expected_doublets,
        "adata_path_type": "AnnData" if not isinstance(adata_path, (str, Path)) else str(adata_path),
    }
    _get_logger().info(
        "run_doublet_detection starting — method=%s, expected=%.3f",
        method, expected_doublets,
    )

    try:
        from code_library.solutions.doublet_detection import DoubletFinder

        adata = _load_adata(adata_path)
        n_total = adata.n_obs

        finder = DoubletFinder(method=method)
        adata = finder.detect(adata, expected_doublets=expected_doublets)

        # Count doublets
        if "doublet" in adata.obs:
            doublet_col = adata.obs["doublet"]
            # Scrublet returns bool / str "True"/"False"; statistical returns str
            if doublet_col.dtype == bool or doublet_col.dtype == np.bool_:
                n_doublets = int(doublet_col.sum())
            else:
                n_doublets = int((doublet_col == "True").sum())
        else:
            n_doublets = 0

        pct_doublets = round(n_doublets / n_total * 100, 2) if n_total > 0 else 0.0

        mean_score = 0.0
        if "doublet_score" in adata.obs:
            scores = adata.obs["doublet_score"]
            mean_score = round(float(np.mean(scores)), 4)

        # Detect whether scrublet was actually used or fell back
        actual_method = method
        if method == "scrublet" and "doublet_score" in adata.obs:
            # Statistical fallback gives z-score-ish values centered near 0;
            # Scrublet scores are 0-1.  Heuristic: if max > 2, likely statistical.
            max_s = float(adata.obs["doublet_score"].max())
            if max_s > 2.5:
                actual_method = "statistical (scrublet fallback)"

        metrics = {
            "n_doublets": int(n_doublets),
            "pct_doublets": pct_doublets,
            "method": actual_method,
            "n_total": n_total,
            "mean_doublet_score": mean_score,
        }
        return _make_success("run_doublet_detection", metrics, params)

    except Exception as exc:
        return _make_error("run_doublet_detection", exc, params)


# =============================================================================
# Protocol 4 — Cell Type Annotation
# =============================================================================

def run_cell_annotation(
    adata_path: Union[str, "AnnData"],  # noqa: F821
    marker_dict: dict[str, list[str]],
    cluster_key: str = "leiden",
) -> dict[str, Any]:
    """Annotate cell types using marker-based scoring.

    Uses ``code_library.modules.cell_type_annotation.marker_based_annotation``.

    Parameters
    ----------
    adata_path:
        Path to ``.h5ad`` or an in-memory ``AnnData``.  Must have clusters
        computed under ``adata.obs[cluster_key]``.
    marker_dict:
        Mapping of cell type names to lists of marker genes.
        Example: ``{"T cell": ["CD3D", "CD3E"], "B cell": ["CD19", "MS4A1"]}``
    cluster_key:
        Column in ``adata.obs`` holding cluster labels (default ``"leiden"``).

    Returns
    -------
    dict
        ``{success, function, metrics: {cell_types_found, annotation_summary:
        {cluster: cell_type, ...}, n_cell_types, n_clusters, method,
        cluster_key}, timestamp}``
    """
    params = {
        "n_markers": sum(len(v) for v in marker_dict.values()),
        "cell_types_queried": list(marker_dict.keys()),
        "cluster_key": cluster_key,
        "adata_path_type": "AnnData" if not isinstance(adata_path, (str, Path)) else str(adata_path),
    }
    _get_logger().info(
        "run_cell_annotation starting — cell_types=%s, cluster_key=%s",
        list(marker_dict.keys()), cluster_key,
    )

    try:
        from code_library.modules.cell_type_annotation import marker_based_annotation

        adata = _load_adata(adata_path)

        if cluster_key not in adata.obs:
            return {
                "success": False,
                "function": "run_cell_annotation",
                "error": f"cluster_key '{cluster_key}' not found in adata.obs columns: {list(adata.obs.columns)}",
                "params_logged": params,
                "timestamp": datetime.now().isoformat(),
            }

        adata = marker_based_annotation(adata, marker_dict=marker_dict, cluster_key=cluster_key)

        # Build annotation summary
        cell_types_found = sorted(set(
            str(ct) for ct in adata.obs.get("cell_type", [])
        ))

        annotation_summary: dict[str, str] = {}
        if cluster_key in adata.obs and "cell_type" in adata.obs:
            for cluster in sorted(adata.obs[cluster_key].unique()):
                mask = adata.obs[cluster_key] == cluster
                ct_vals = adata.obs.loc[mask, "cell_type"]
                if len(ct_vals) > 0:
                    annotation_summary[str(cluster)] = str(ct_vals.iloc[0])

        metrics = {
            "cell_types_found": cell_types_found,
            "annotation_summary": annotation_summary,
            "n_cell_types": len(cell_types_found),
            "n_clusters": len(annotation_summary),
            "method": "marker_based_annotation",
            "cluster_key": cluster_key,
        }
        return _make_success("run_cell_annotation", metrics, params)

    except Exception as exc:
        return _make_error("run_cell_annotation", exc, params)


# =============================================================================
# Agent Toolkit Registry
# =============================================================================

_AGENT_TOOLKITS: dict[str, dict[str, Any]] = {
    "analysis_executor": {
        "run_qc_pipeline": run_qc_pipeline,
        "run_clustering": run_clustering,
        "run_doublet_detection": run_doublet_detection,
        "run_cell_annotation": run_cell_annotation,
    },
    "qc_specialist": {
        "run_qc_pipeline": run_qc_pipeline,
        "run_doublet_detection": run_doublet_detection,
    },
    "clustering_specialist": {
        "run_clustering": run_clustering,
        "run_cell_annotation": run_cell_annotation,
    },
    "full_pipeline": {
        "run_qc_pipeline": run_qc_pipeline,
        "run_clustering": run_clustering,
        "run_doublet_detection": run_doublet_detection,
        "run_cell_annotation": run_cell_annotation,
    },
}


def get_agent_toolkit(agent_name: str) -> dict[str, Any]:
    """Return the set of protocol functions available to an agent.

    Parameters
    ----------
    agent_name:
        Agent role identifier.  Recognised values:

        - ``"analysis_executor"`` — full analysis suite (QC + clustering +
          doublet detection + cell annotation)
        - ``"qc_specialist"`` — QC pipeline + doublet detection only
        - ``"clustering_specialist"`` — clustering + cell annotation only
        - ``"full_pipeline"`` — all four protocols

    Returns
    -------
    dict
        ``{function_name: callable, ...}``.  Unknown agent names receive the
        ``analysis_executor`` toolkit as a safe default.
    """
    toolkit = _AGENT_TOOLKITS.get(agent_name)
    if toolkit is None:
        _get_logger().warning(
            "Unknown agent_name '%s', falling back to analysis_executor toolkit",
            agent_name,
        )
        toolkit = _AGENT_TOOLKITS["analysis_executor"]
    return dict(toolkit)  # shallow copy so callers can't mutate the registry


# =============================================================================
# Protocol Dispatcher
# =============================================================================

_PROTOCOL_REGISTRY: dict[str, Any] = {
    "qc_pipeline": run_qc_pipeline,
    "clustering": run_clustering,
    "doublet_detection": run_doublet_detection,
    "cell_annotation": run_cell_annotation,
    # Aliases
    "qc": run_qc_pipeline,
    "run_qc": run_qc_pipeline,
    "leiden": run_clustering,
    "run_leiden": run_clustering,
    "doublets": run_doublet_detection,
    "annotate": run_cell_annotation,
    "cell_type": run_cell_annotation,
}


def execute_analysis(protocol_name: str, **kwargs: Any) -> dict[str, Any]:
    """Generic dispatcher — route a protocol name to the correct function.

    Parameters
    ----------
    protocol_name:
        One of the registered protocol names (see ``_PROTOCOL_REGISTRY``).
        Case-insensitive; common aliases are supported.
    **kwargs:
        Forwarded to the target function.  At minimum, ``adata_path`` is
        required for every protocol.

    Returns
    -------
    dict
        Structured result with ``success``, ``function``, ``metrics`` (or
        ``error``), and ``timestamp``.  Always returns a dict, never raises.

    Raises
    ------
    ValueError
        If *protocol_name* is not recognised.
    """
    _get_logger().info(
        "execute_analysis dispatched — protocol=%s, kwargs_keys=%s",
        protocol_name, list(kwargs.keys()),
    )

    func = _PROTOCOL_REGISTRY.get(protocol_name.lower())
    if func is None:
        known = sorted(set(_PROTOCOL_REGISTRY.keys()))
        msg = (
            f"Unknown protocol '{protocol_name}'. "
            f"Known protocols: {known}"
        )
        _get_logger().error(msg)
        return {
            "success": False,
            "function": "execute_analysis",
            "error": msg,
            "params_logged": {"protocol_name": protocol_name, "kwargs_keys": list(kwargs.keys())},
            "timestamp": datetime.now().isoformat(),
        }

    try:
        result = func(**kwargs)
        # If the wrapped function itself raised and returned an error,
        # execute_analysis still returns it as-is (it is already a dict).
        return result
    except TypeError as exc:
        # E.g. missing required argument
        return {
            "success": False,
            "function": f"execute_analysis -> {protocol_name}",
            "error": f"TypeError: {exc}",
            "params_logged": {"protocol_name": protocol_name, "kwargs_keys": list(kwargs.keys())},
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as exc:
        return {
            "success": False,
            "function": f"execute_analysis -> {protocol_name}",
            "error": f"{type(exc).__name__}: {exc}",
            "traceback": traceback.format_exc(),
            "params_logged": {"protocol_name": protocol_name, "kwargs_keys": list(kwargs.keys())},
            "timestamp": datetime.now().isoformat(),
        }
