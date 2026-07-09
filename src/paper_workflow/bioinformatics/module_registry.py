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

PRODUCTION_CAPABILITY_GRADES = {
    "production_capable_real_wrapper",
    "validated_workflow_pilot",
    "dry_run_contract",
    "adapter_contract",
    "scaffold_only",
    "planning_contract",
    "blocked_environment",
    "retired",
}

EXECUTION_EVIDENCE_LEVELS = {
    "real_project_data_validated",
    "official_tutorial_validated",
    "toy_real_tested",
    "dry_run_only",
    "contract_only",
    "no_execution_evidence",
}

STRATEGY_VISIBILITY = {
    "production_candidate",
    "exploratory_candidate",
    "planning_only",
    "hidden_from_production",
}

CLAIM_PERMISSIONS = {
    "workflow_test_only",
    "exploratory_only",
    "association_with_review",
    "no_claim",
}

ENVIRONMENT_STATUSES = {"pass", "degraded", "blocked", "unknown"}

FORBIDDEN_PRODUCTION_GRADES = {
    "adapter_contract",
    "scaffold_only",
    "planning_contract",
    "blocked_environment",
    "retired",
}


def _read_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh) or {}
    return data if isinstance(data, dict) else {}


def _normalize_modules(raw: Any) -> dict[str, dict[str, Any]]:
    if isinstance(raw, dict):
        return {str(k): _with_inferred_grade(str(k), dict(v or {})) for k, v in raw.items() if isinstance(v, dict)}
    if isinstance(raw, list):
        modules: dict[str, dict[str, Any]] = {}
        for item in raw:
            if not isinstance(item, dict):
                continue
            module_id = str(item.get("id") or item.get("module_id") or "")
            if module_id:
                modules[module_id] = _with_inferred_grade(module_id, dict(item))
        return modules
    return {}


def _with_inferred_grade(module_id: str, module: dict[str, Any]) -> dict[str, Any]:
    """Backfill v5 grading fields for older registry entries.

    The YAML registry is still the durable truth source; this inference keeps
    older test fixtures readable while CI pushes real files toward explicit
    declarations.
    """
    source_type = str((module.get("source") or {}).get("type", "")).lower()
    maturity = str(module.get("method_maturity", "")).lower()
    validation = str(module.get("validation_status", "")).lower()
    tags = {str(t).lower() for t in module.get("capability_tags", []) or []}
    if "production_capability_grade" not in module:
        if source_type == "adapter_contract" or "adapter_contract" in maturity:
            grade = "adapter_contract"
        elif source_type == "planning_contract" or "planning" in validation:
            grade = "planning_contract"
        elif "scaffold" in source_type or "scaffold" in maturity:
            grade = "scaffold_only"
        elif "dry" in validation or "dry-run" in tags:
            grade = "dry_run_contract"
        elif "tutorial" in validation or "pbmc3k" in tags:
            grade = "validated_workflow_pilot"
        elif "real-wrapper" in tags or "real" in maturity:
            grade = "production_capable_real_wrapper"
        else:
            grade = "validated_workflow_pilot"
        module["production_capability_grade"] = grade
    if "execution_evidence_level" not in module:
        grade = module["production_capability_grade"]
        if grade == "production_capable_real_wrapper":
            module["execution_evidence_level"] = "toy_real_tested"
        elif grade == "validated_workflow_pilot" and ("tutorial" in validation or "pbmc3k" in tags):
            module["execution_evidence_level"] = "official_tutorial_validated"
        elif grade in {"dry_run_contract", "adapter_contract"}:
            module["execution_evidence_level"] = "dry_run_only" if grade == "dry_run_contract" else "contract_only"
        else:
            module["execution_evidence_level"] = "no_execution_evidence"
    if "strategy_visibility" not in module:
        grade = module["production_capability_grade"]
        module["strategy_visibility"] = "planning_only" if grade in FORBIDDEN_PRODUCTION_GRADES or grade == "dry_run_contract" else "exploratory_candidate"
    if "claim_permission" not in module:
        boundary = str(module.get("claim_boundary", "")).lower()
        if "mechanism" in boundary or "clinical" in boundary:
            module["claim_permission"] = "no_claim"
        elif "workflow" in boundary or "tutorial" in boundary:
            module["claim_permission"] = "workflow_test_only"
        else:
            module["claim_permission"] = "exploratory_only"
    if "current_environment_status" not in module:
        module["current_environment_status"] = "unknown"
    module.setdefault("id", module_id)
    module.setdefault("module_id", module_id)
    return module


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
            "production_capability_grade",
            "execution_evidence_level",
            "strategy_visibility",
            "claim_permission",
            "current_environment_status",
        ]:
            if key not in module or module.get(key) in ("", None, [], {}):
                issues.append(f"missing {key}")
        self._validate_enum(module, "production_capability_grade", PRODUCTION_CAPABILITY_GRADES, issues)
        self._validate_enum(module, "execution_evidence_level", EXECUTION_EVIDENCE_LEVELS, issues)
        self._validate_enum(module, "strategy_visibility", STRATEGY_VISIBILITY, issues)
        self._validate_enum(module, "claim_permission", CLAIM_PERMISSIONS, issues)
        self._validate_enum(module, "current_environment_status", ENVIRONMENT_STATUSES, issues)
        source_path = ((module.get("source") or {}).get("path") or "")
        if source_path and not (self.project_root / source_path).exists():
            issues.append(f"source path missing: {source_path}")
        return issues

    def capability_summary(self) -> dict[str, Any]:
        by_modality: dict[str, int] = {}
        by_step: dict[str, int] = {}
        by_grade: dict[str, int] = {}
        by_visibility: dict[str, int] = {}
        executable = 0
        production_visible = 0
        for module in self.modules.values():
            modality = str(module.get("modality", "unknown"))
            step = str(module.get("step", "unknown"))
            grade = str(module.get("production_capability_grade", "unknown"))
            visibility = str(module.get("strategy_visibility", "unknown"))
            by_modality[modality] = by_modality.get(modality, 0) + 1
            by_step[step] = by_step.get(step, 0) + 1
            by_grade[grade] = by_grade.get(grade, 0) + 1
            by_visibility[visibility] = by_visibility.get(visibility, 0) + 1
            if (module.get("execution") or {}).get("type") in {"python", "rscript", "shell"}:
                executable += 1
            if self.is_production_visible(module):
                production_visible += 1
        return {
            "registry_path": str(self.registry_path),
            "registry_hash": self.content_hash(),
            "module_count": len(self.modules),
            "executable_module_count": executable,
            "production_visible_module_count": production_visible,
            "by_modality": by_modality,
            "by_step": by_step,
            "by_grade": by_grade,
            "by_visibility": by_visibility,
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

    @staticmethod
    def is_production_visible(module: dict[str, Any]) -> bool:
        grade = str(module.get("production_capability_grade", ""))
        visibility = str(module.get("strategy_visibility", ""))
        env_status = str(module.get("current_environment_status", "unknown"))
        return (
            grade not in FORBIDDEN_PRODUCTION_GRADES
            and visibility in {"production_candidate", "exploratory_candidate"}
            and env_status != "blocked"
        )

    @staticmethod
    def production_gate(module: dict[str, Any]) -> dict[str, Any]:
        grade = str(module.get("production_capability_grade", ""))
        visibility = str(module.get("strategy_visibility", ""))
        env_status = str(module.get("current_environment_status", "unknown"))
        reasons = []
        if grade in FORBIDDEN_PRODUCTION_GRADES:
            reasons.append(f"blocked_by_grade:{grade}")
        if visibility not in {"production_candidate", "exploratory_candidate"}:
            reasons.append(f"blocked_by_visibility:{visibility}")
        if env_status == "blocked":
            reasons.append("blocked_by_environment")
        return {
            "allowed": not reasons,
            "grade": grade,
            "strategy_visibility": visibility,
            "environment_status": env_status,
            "reasons": reasons,
        }

    @staticmethod
    def _validate_enum(module: dict[str, Any], key: str, allowed: set[str], issues: list[str]) -> None:
        value = str(module.get(key, ""))
        if value and value not in allowed:
            issues.append(f"{key} invalid: {value}")
