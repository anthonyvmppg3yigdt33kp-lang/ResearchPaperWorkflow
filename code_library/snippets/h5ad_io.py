"""
H5AD I/O Snippet - Standard h5ad read/write with compatibility handling.

Usage:
    from snippets.h5ad_io import read_h5ad_safe, write_h5ad_safe
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional

import scanpy as sc
from anndata import AnnData


def read_h5ad_safe(
    path: str,
    backed: bool = False,
    **kwargs
) -> AnnData:
    """
    Safely read h5ad file with error handling.

    Args:
        path: Path to h5ad file
        backed: If True, use backed mode
        **kwargs: Additional arguments to scanpy.read_h5ad

    Returns:
        AnnData object

    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If file is corrupted
    """
    path = Path(path)

    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    try:
        if backed:
            return sc.read_h5ad(path, backed=backed, **kwargs)
        else:
            return sc.read_h5ad(path, **kwargs)
    except Exception as e:
        raise ValueError(f"Error reading {path}: {e}")


def write_h5ad_safe(
    adata: AnnData,
    path: str,
    compression: str = "gzip",
    **kwargs
) -> None:
    """
    Safely write h5ad file with compatibility handling.

    Args:
        adata: AnnData object
        path: Output path
        compression: Compression method
        **kwargs: Additional arguments to adata.write_h5ad

    Raises:
        ValueError: If write fails
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    try:
        adata.write_h5ad(path, compression=compression, **kwargs)
    except Exception as e:
        # Try without compression if that fails
        if compression != "gzip":
            raise ValueError(f"Error writing {path} with compression {compression}: {e}")

        # Try without compression
        try:
            adata.write_h5ad(path, compression=None, **kwargs)
        except Exception as e2:
            raise ValueError(f"Error writing {path}: {e2}")


def validate_h5ad(path: str) -> dict:
    """
    Validate h5ad file structure.

    Args:
        path: Path to h5ad file

    Returns:
        Dict with validation results
    """
    path = Path(path)

    if not path.exists():
        return {"valid": False, "error": "File not found"}

    try:
        adata = sc.read_h5ad(path)
        return {
            "valid": True,
            "n_obs": adata.n_obs,
            "n_vars": adata.n_vars,
            "shape": adata.shape,
            "layers": list(adata.layers.keys()) if adata.layers else [],
            "obs_columns": list(adata.obs.columns),
            "var_columns": list(adata.var.columns),
        }
    except Exception as e:
        return {"valid": False, "error": str(e)}
