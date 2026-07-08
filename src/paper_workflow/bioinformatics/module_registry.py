"""Method-asset registry for code_library modules.

The legacy plugin registry answers "which files exist?". This registry answers
"which method assets can the planner choose, execute, audit, and improve?".
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Optional

import yaml


def _read_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh) or {}
    return data if isinstance(data, dict) else {}


def _normalize_modules(raw: Any) -> dict[str, dict[str, Any]]:
    if isinstance(raw, dict):
        return {str(k): dict(v or {}) for k, v in raw.items() if isinstance(v, dict)}
    if isinstance(raw, list):
        modules: dict[str, dict[str, Any]] = {}
        for item in raw:
            if not isinstance(item, dict):
                continue
            module_id = str(item.get("id") or item.get("module_id") or "")
            if module_id:
                modules[module_id] = dict(item)
        return modules
    return {}


@dataclass(frozen=True)
class ModuleQuery:
    """Filters for method-asset discovery."""

    modality: str = ""
    step: str = ""
    language: str = ""
    tags: tuple[str, ...] = ()


class ModuleRegistry:
    """Read and query ``code_library/module_registry.yaml``."""

    def __init__(self, project_root: Path, registry_path: Optional[Path] = None):
        self.project_root = Path(project_root)
        self.registry_path = registry_path or self.project_root / "code_library" / "module_registry.yaml"
        self.data = _read_yaml(self.registry_path)
        self.modules = _normalize_modules(self.data.get("modules", {}))

    def reload(self) -> None:
        self.data = _read_yaml(self.registry_path)
        self.modules = _normalize_modules(self.data.get("modules", {}))

    def exists(self) -> bool:
        return self.registry_path.exists()

    def content_hash(self) -> str:
        if not self.registry_path.exists():
            return ""
        return hashlib.sha256(self.registry_path.read_bytes()).hexdigest()

    def get(self, module_id: str) -> dict[str, Any]:
        return dict(self.modules.get(module_id, {}))

    def list_modules(
        self,
        *,
        modality: str = "",
        step: str = "",
        language: str = "",
        tags: Optional[Iterable[str]] = None,
    ) -> list[dict[str, Any]]:
        query = ModuleQuery(
            modality=modality.lower().replace("-", "_"),
            step=step.lower().replace("-", "_"),
            language=language.lower(),
            tags=tuple(t.lower() for t in (tags or ())),
        )
        results = []
        for module_id, module in self.modules.items():
            if not self._matches(module, query):
                continue
            payload = dict(module)
            payload.setdefault("id", module_id)
            payload.setdefault("module_id", module_id)
            results.append(payload)
        return sorted(results, key=lambda item: (item.get("modality", ""), item.get("step", ""), item.get("id", "")))

    def validate_module(self, module_id: str) -> list[str]:
        module = self.modules.get(module_id)
        if not module:
            return [f"module not found: {module_id}"]
        issues = []
        for key in [
            "name",
            "modality",
            "step",
            "language",
            "source",
            "input_schema",
            "output_schema",
            "environment",
            "reviewer_risk",
            "claim_boundary",
            "validation_status",
            "method_maturity",
        ]:
            if key not in module or module.get(key) in ("", None, [], {}):
                issues.append(f"missing {key}")
        source_path = ((module.get("source") or {}).get("path") or "")
        if source_path and not (self.project_root / source_path).exists():
            issues.append(f"source path missing: {source_path}")
        return issues

    def capability_summary(self) -> dict[str, Any]:
        by_modality: dict[str, int] = {}
        by_step: dict[str, int] = {}
        executable = 0
        for module in self.modules.values():
            modality = str(module.get("modality", "unknown"))
            step = str(module.get("step", "unknown"))
            by_modality[modality] = by_modality.get(modality, 0) + 1
            by_step[step] = by_step.get(step, 0) + 1
            if (module.get("execution") or {}).get("type") in {"python", "rscript", "shell"}:
                executable += 1
        return {
            "registry_path": str(self.registry_path),
            "registry_hash": self.content_hash(),
            "module_count": len(self.modules),
            "executable_module_count": executable,
            "by_modality": by_modality,
            "by_step": by_step,
        }

    @staticmethod
    def _matches(module: dict[str, Any], query: ModuleQuery) -> bool:
        if query.modality:
            module_modality = str(module.get("modality", "")).lower().replace("-", "_")
            aliases = [module_modality] + [str(a).lower().replace("-", "_") for a in module.get("modality_aliases", []) or []]
            if query.modality not in aliases:
                return False
        if query.step:
            module_step = str(module.get("step", "")).lower().replace("-", "_")
            if query.step != module_step:
                return False
        if query.language and query.language != str(module.get("language", "")).lower():
            return False
        if query.tags:
            module_tags = {str(t).lower() for t in module.get("capability_tags", []) or []}
            if not set(query.tags).issubset(module_tags):
                return False
        return True
