"""Capability-aware method selection for analysis graph planning."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

from paper_workflow.bioinformatics.data_registry import DataRegistry
from paper_workflow.bioinformatics.environment_registry import EnvironmentRegistry
from paper_workflow.bioinformatics.module_registry import ModuleRegistry


SCRNA_ALIASES = {"scrna", "sc_rna", "single_cell", "single_cell_rna", "single-cell"}


class MethodSelector:
    """Select modules based on data fit, code maturity, environment, and reviewer value."""

    def __init__(self, project_root: Path, paper_dir: Optional[Path] = None):
        self.project_root = Path(project_root)
        self.paper_dir = Path(paper_dir) if paper_dir else None
        self.modules = ModuleRegistry(self.project_root)
        self.environments = EnvironmentRegistry(self.project_root)
        self.data = DataRegistry(self.paper_dir) if self.paper_dir else None
        self._environment_cache: dict[tuple[str, str], dict[str, Any]] = {}

    def select(
        self,
        *,
        goal: str,
        modalities: list[str],
        max_modules: int = 6,
    ) -> list[dict[str, Any]]:
        normalized = [self._normalize_modality(m) for m in modalities if m]
        candidates: list[dict[str, Any]] = []
        for modality in normalized or ["general"]:
            candidates.extend(self.modules.list_modules(modality=modality))
        if not candidates and "single_cell" in normalized:
            candidates.extend(self.modules.list_modules(tags=["single-cell"]))

        scored = []
        for module in candidates:
            score = self.score_module(module, goal=goal)
            payload = dict(module)
            payload["method_selection_score"] = score
            scored.append(payload)
        scored.sort(key=lambda item: item["method_selection_score"]["total"], reverse=True)
        return scored[:max_modules]

    def score_module(self, module: dict[str, Any], goal: str = "") -> dict[str, Any]:
        goal_lower = goal.lower()
        tags = {str(t).lower() for t in module.get("capability_tags", []) or []}
        modality = str(module.get("modality", "")).lower()
        env_id = str((module.get("environment") or {}).get("env_id", ""))
        language = str(module.get("language", ""))
        cache_key = (env_id, language.lower())
        if cache_key not in self._environment_cache:
            self._environment_cache[cache_key] = self.environments.validate_environment(env_id, language=language)
        env_status = self._environment_cache[cache_key]
        validation = str(module.get("validation_status", "")).lower()
        maturity = str(module.get("method_maturity", "")).lower()
        reviewer_value = module.get("reviewer_value", []) or []
        risk = module.get("reviewer_risk", []) or []

        biological_fit = 0.65
        if "single" in goal_lower and ("single-cell" in tags or modality == "single_cell"):
            biological_fit = 0.95
        if "pbmc" in goal_lower and "pbmc3k" in tags:
            biological_fit = 1.0
        data_modalities = self.data.modalities() if self.data else []
        data_fit = 0.75 if not data_modalities else (0.95 if modality in data_modalities else 0.45)
        environment_ready = 1.0 if env_status["status"] == "pass" else 0.25
        code_maturity = 0.9 if "validated" in validation or "validated" in maturity else 0.65
        figure_value = min(1.0, 0.55 + 0.1 * len(module.get("figure_outputs", []) or []))
        reviewer_risk = min(1.0, 0.15 + 0.12 * len(risk))
        expected_evidence_gain = min(1.0, 0.5 + 0.08 * len(reviewer_value) + 0.05 * len(tags))
        total = (
            biological_fit * 0.22
            + data_fit * 0.16
            + environment_ready * 0.18
            + code_maturity * 0.16
            + figure_value * 0.12
            + expected_evidence_gain * 0.12
            + (1.0 - reviewer_risk) * 0.04
        )
        return {
            "biological_fit": round(biological_fit, 3),
            "data_fit": round(data_fit, 3),
            "environment_ready": round(environment_ready, 3),
            "code_maturity": round(code_maturity, 3),
            "figure_value": round(figure_value, 3),
            "reviewer_risk": round(reviewer_risk, 3),
            "expected_evidence_gain": round(expected_evidence_gain, 3),
            "compute_cost": module.get("compute_cost", "unknown"),
            "token_cost": module.get("token_cost", "low"),
            "total": round(total, 3),
            "environment_status": env_status["status"],
            "environment_issues": env_status["issues"],
        }

    @staticmethod
    def _normalize_modality(modality: str) -> str:
        text = modality.lower().replace("-", "_")
        if text in SCRNA_ALIASES:
            return "single_cell"
        if text in {"multiomics", "multi_omics", "multi_modal"}:
            return "multi_omics"
        return text


def render_selection_report(goal: str, selected: list[dict[str, Any]]) -> str:
    lines = [
        "# Method Selection Report",
        "",
        f"Goal: {goal}",
        "",
        "## Selected Modules",
        "",
    ]
    if not selected:
        lines.append("No compatible method assets were found in `code_library/module_registry.yaml`.")
        return "\n".join(lines) + "\n"
    for module in selected:
        score = module.get("method_selection_score", {})
        risks = module.get("reviewer_risk", []) or ["not_declared"]
        outputs = module.get("figure_outputs", []) or []
        lines.extend([
            f"### {module.get('id') or module.get('module_id')}",
            "",
            f"- Name: {module.get('name', '')}",
            f"- Modality/step: {module.get('modality', '')} / {module.get('step', '')}",
            f"- Total score: {score.get('total', 'not_scored')}",
            f"- Environment: {score.get('environment_status', 'unknown')}",
            f"- Reviewer risks: {', '.join(str(r) for r in risks)}",
            f"- Figure outputs: {', '.join(str(o) for o in outputs) if outputs else 'not_declared'}",
            f"- Claim boundary: {module.get('claim_boundary', 'not_declared')}",
            "",
        ])
    return "\n".join(lines)
