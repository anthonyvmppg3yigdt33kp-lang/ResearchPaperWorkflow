"""Paper-scoped data registry helpers for method-asset execution."""

from __future__ import annotations

import hashlib
import json
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
    """Read paper-scoped data truth without loading raw matrices into memory."""

    def __init__(self, paper_dir: Path):
        self.paper_dir = Path(paper_dir)
        self.inventory_path = self.paper_dir / "data" / "data_inventory.yaml"
        self.input_inventory_path = self.paper_dir / "data" / "data_inventory_input.yaml"
        self.registry_path = self.paper_dir / "data" / "data_registry" / "datasets.yaml"
        self.file_manifest_path = self.paper_dir / "data" / "data_registry" / "file_manifest.jsonl"
        self.inventory = _read_yaml(self.inventory_path) or _read_yaml(self.input_inventory_path)
        self.registry = _read_yaml(self.registry_path)

    def exists(self) -> bool:
        return self.registry_path.exists() or self.inventory_path.exists() or self.input_inventory_path.exists()

    def content_hash(self) -> str:
        path = self.registry_path if self.registry_path.exists() else (self.inventory_path if self.inventory_path.exists() else self.input_inventory_path)
        if not path.exists():
            return ""
        return hashlib.sha256(path.read_bytes()).hexdigest()

    def load_datasets(self) -> list[dict[str, Any]]:
        datasets = self.registry.get("datasets", [])
        if isinstance(datasets, list):
            return [dict(item) for item in datasets if isinstance(item, dict)]
        return []

    def list_modalities(self) -> list[str]:
        values = [str(item.get("modality", "")).lower().replace("-", "_") for item in self.load_datasets() if item.get("modality")]
        values.extend(self.modalities())
        return sorted(set(v for v in values if v))

    def modalities(self) -> list[str]:
        explicit = self.inventory.get("data_types") or self.inventory.get("modalities") or []
        values = [str(v).lower().replace("-", "_") for v in explicit if v]
        for item in self.inventory.get("files_found", []) or self.inventory.get("files", []) or []:
            path = str(item.get("path", "") if isinstance(item, dict) else item).lower()
            modality = self._infer_modality(path)
            if modality:
                values.append(modality)
        return sorted(set(values))

    def resolve_input(self, binding: str | dict[str, Any]) -> dict[str, Any]:
        if isinstance(binding, dict):
            dataset_id = str(binding.get("dataset_id", ""))
            path_text = str(binding.get("path", ""))
        else:
            dataset_id = ""
            path_text = str(binding)
        for dataset in self.load_datasets():
            if dataset_id and dataset.get("dataset_id") == dataset_id:
                return dataset
            if path_text and str(dataset.get("path", "")).replace("\\", "/") == path_text.replace("\\", "/"):
                return dataset
        return {"dataset_id": dataset_id, "path": path_text, "status": "not_declared"}

    def validate_sample_mapping(self, required: bool = False) -> dict[str, Any]:
        issues = []
        datasets = self.load_datasets()
        mapping_statuses = []
        for dataset in datasets:
            mapping = dataset.get("sample_mapping") or {}
            status = str(mapping.get("status", "missing"))
            mapping_statuses.append(status)
            if required and status not in {"declared", "not_required_for_tutorial"}:
                issues.append(f"sample mapping missing for dataset: {dataset.get('dataset_id', '<unknown>')}")
        if required and not datasets:
            issues.append("sample mapping required but no data registry datasets declared")
        return {
            "required": required,
            "statuses": mapping_statuses,
            "status": "pass" if not issues else "blocked",
            "issues": issues,
        }

    def validate_raw_immutable(self) -> dict[str, Any]:
        issues = [
            f"raw dataset not marked immutable: {dataset.get('dataset_id', '<unknown>')}"
            for dataset in self.load_datasets()
            if not bool(dataset.get("immutable", False))
        ]
        return {"status": "pass" if not issues else "blocked", "issues": issues}

    def compute_file_manifest(self) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        for dataset in self.load_datasets():
            dataset_path = self.paper_dir / str(dataset.get("path", ""))
            declared_files = dataset.get("files", []) or []
            if declared_files:
                for item in declared_files:
                    if not isinstance(item, dict):
                        continue
                    rel = str(item.get("path", ""))
                    path = self.paper_dir / rel
                    rows.append(self._file_row(path, rel, dataset))
                continue
            if dataset_path.is_file():
                rows.append(self._file_row(dataset_path, self._safe_relative_path(dataset_path), dataset))
            elif dataset_path.is_dir():
                for path in sorted(p for p in dataset_path.rglob("*") if p.is_file()):
                    rows.append(self._file_row(path, self._safe_relative_path(path), dataset))
        return rows

    def write_file_manifest(self) -> list[dict[str, Any]]:
        rows = self.compute_file_manifest()
        self.file_manifest_path.parent.mkdir(parents=True, exist_ok=True)
        with self.file_manifest_path.open("w", encoding="utf-8") as fh:
            for row in rows:
                fh.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
        return rows

    def validate_for_execution(self, graph: Any) -> dict[str, Any]:
        datasets = self.load_datasets()
        issues = []
        warnings = []
        if not self.registry_path.exists():
            issues.append("data registry missing: data/data_registry/datasets.yaml")
        if not datasets:
            issues.append("no datasets declared in data registry")
        immutable = self.validate_raw_immutable()
        issues.extend(immutable["issues"])
        group_required = self._group_inference_requested(graph)
        sample_mapping = self.validate_sample_mapping(required=group_required)
        issues.extend(sample_mapping["issues"])
        file_manifest = self.compute_file_manifest() if datasets else []
        missing_files = [row["path"] for row in file_manifest if not row.get("exists")]
        if missing_files:
            issues.extend([f"declared data file missing: {path}" for path in missing_files[:10]])
        tutorial_only = bool(datasets) and all(str(d.get("role", "")) == "tutorial_fixture" for d in datasets)
        if tutorial_only and not group_required:
            warnings.append("tutorial fixture data can support workflow tests but not disease inference")
        status = "pass" if not issues else "blocked"
        return {
            "status": status,
            "issues": issues,
            "warnings": warnings,
            "data_registry": str(self.registry_path),
            "data_registry_hash": self.content_hash(),
            "dataset_count": len(datasets),
            "modalities": self.list_modalities(),
            "sample_mapping": sample_mapping,
            "raw_immutable": immutable,
            "input_manifest": {"files": file_manifest},
            "evidence_grade": "workflow_test" if tutorial_only else ("analysis_ready" if status == "pass" else "blocked"),
        }

    def summary(self) -> dict[str, Any]:
        return {
            "inventory_path": str(self.inventory_path if self.inventory_path.exists() else self.input_inventory_path),
            "registry_path": str(self.registry_path),
            "exists": self.exists(),
            "modalities": self.list_modalities(),
            "statistical_unit": self.inventory.get("statistical_unit", "not_declared"),
            "n_samples": self.inventory.get("n_samples", self.inventory.get("n_patients", 0)),
            "batch_variables": list(self.inventory.get("batch_variables", []) or []),
            "status": self.registry.get("status", self.inventory.get("status", "not_declared")),
        }

    @staticmethod
    def _infer_modality(path: str) -> str:
        lower = path.lower()
        if any(token in lower for token in ("scrna", "single", "cellranger", "pbmc", "h5ad", "matrix.mtx")):
            return "single_cell"
        if "spatial" in lower or "visium" in lower:
            return "spatial"
        if "rna" in lower or "count" in lower:
            return "bulk_rnaseq"
        return ""

    def _file_row(self, path: Path, rel: str, dataset: dict[str, Any]) -> dict[str, Any]:
        exists = path.exists()
        return {
            "path": rel.replace("\\", "/"),
            "sha256": self._sha256(path) if exists and path.is_file() else "",
            "size_bytes": path.stat().st_size if exists and path.is_file() else 0,
            "exists": exists,
            "dataset_id": dataset.get("dataset_id", ""),
            "modality": dataset.get("modality", self._infer_modality(rel)),
            "format": dataset.get("format", ""),
            "role": dataset.get("role", ""),
        }

    @staticmethod
    def _sha256(path: Path) -> str:
        h = hashlib.sha256()
        with path.open("rb") as fh:
            for chunk in iter(lambda: fh.read(1024 * 1024), b""):
                h.update(chunk)
        return h.hexdigest()

    def _safe_relative_path(self, path: Path) -> str:
        try:
            return str(path.relative_to(self.paper_dir)).replace("\\", "/")
        except ValueError:
            try:
                return str(path.resolve().relative_to(self.paper_dir.parent.parent.resolve())).replace("\\", "/")
            except ValueError:
                return str(Path("external_data") / path.name).replace("\\", "/")

    @staticmethod
    def _group_inference_requested(graph: Any) -> bool:
        text = " ".join([
            str(getattr(graph, "primary_objective", "")),
            str(getattr(graph, "research_question", "")),
            str(getattr(graph, "statistical_unit", "")),
        ]).lower()
        return any(token in text for token in [" vs ", " versus ", "condition", "disease", "case", "control", "group"])
