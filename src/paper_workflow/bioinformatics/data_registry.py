"""Data registry helpers for capability-aware planning."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


def _read_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh) or {}
    return data if isinstance(data, dict) else {}


class DataRegistry:
    """Read paper-scoped data inventory without loading raw matrices."""

    def __init__(self, paper_dir: Path):
        self.paper_dir = Path(paper_dir)
        self.inventory_path = self.paper_dir / "data" / "data_inventory.yaml"
        self.input_inventory_path = self.paper_dir / "data" / "data_inventory_input.yaml"
        self.inventory = _read_yaml(self.inventory_path) or _read_yaml(self.input_inventory_path)

    def exists(self) -> bool:
        return self.inventory_path.exists() or self.input_inventory_path.exists()

    def modalities(self) -> list[str]:
        explicit = self.inventory.get("data_types") or self.inventory.get("modalities") or []
        values = [str(v).lower().replace("-", "_") for v in explicit if v]
        for item in self.inventory.get("files_found", []) or self.inventory.get("files", []) or []:
            path = str(item.get("path", "") if isinstance(item, dict) else item).lower()
            if any(token in path for token in ("scrna", "single", "cellranger", "pbmc", "h5ad", "matrix.mtx")):
                values.append("single_cell")
            elif "spatial" in path or "visium" in path:
                values.append("spatial")
            elif "rna" in path or "count" in path:
                values.append("bulk_rnaseq")
        return sorted(set(values))

    def summary(self) -> dict[str, Any]:
        return {
            "inventory_path": str(self.inventory_path if self.inventory_path.exists() else self.input_inventory_path),
            "exists": self.exists(),
            "modalities": self.modalities(),
            "statistical_unit": self.inventory.get("statistical_unit", "not_declared"),
            "n_samples": self.inventory.get("n_samples", self.inventory.get("n_patients", 0)),
            "batch_variables": list(self.inventory.get("batch_variables", []) or []),
            "status": self.inventory.get("status", "not_declared"),
        }
