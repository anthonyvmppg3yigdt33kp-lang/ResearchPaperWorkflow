"""Typed analysis-design contract used before execution."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


REQUIRED_METHOD_FIELDS = [
    "research_question",
    "primary_contrast",
    "data_type",
    "statistical_unit",
    "inclusion_exclusion",
    "covariates",
    "batch_or_confounder_plan",
    "normalization_or_preprocessing",
    "primary_methods",
    "validation_plan",
    "sensitivity_plan",
    "expected_outputs",
    "run_id",
    "user_approval",
]

UNRESOLVED_VALUES = {
    "requires_human_input",
    "requires_method_selection",
    "requires_modality_specific_preprocessing_plan",
    "not_declared",
    "not_provided",
}


@dataclass
class AnalysisDesign:
    """Machine-readable design for a bounded biomedical analysis run."""

    run_id: str
    goal: str
    modality: str
    research_question: str = ""
    primary_contrast: str = ""
    data_type: str = ""
    statistical_unit: str = "sample"
    inputs: list[str] = field(default_factory=list)
    inclusion_exclusion: list[str] = field(default_factory=list)
    covariates: list[str] = field(default_factory=list)
    batch_or_confounder_plan: str = ""
    normalization_or_preprocessing: list[str] = field(default_factory=list)
    primary_methods: list[str] = field(default_factory=list)
    validation_plan: list[str] = field(default_factory=list)
    sensitivity_plan: list[str] = field(default_factory=list)
    expected_outputs: list[str] = field(default_factory=list)
    user_approval: bool = False
    execution_status: str = "not_executed"
    execution_backend: str = "dry_run"
    group_column: str = "condition"
    sample_id_column: str = "sample_id"
    data_requirements: list[dict[str, Any]] = field(default_factory=list)
    environment_requirements: list[dict[str, Any]] = field(default_factory=list)
    module_candidates: list[dict[str, Any]] = field(default_factory=list)
    selected_modules: list[dict[str, Any]] = field(default_factory=list)
    analysis_graph: dict[str, Any] = field(default_factory=dict)
    figure_plan_bindings: list[dict[str, Any]] = field(default_factory=list)
    reviewer_risk: list[dict[str, Any]] = field(default_factory=list)
    raw: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AnalysisDesign":
        return cls(
            run_id=str(data.get("run_id", "")),
            goal=str(data.get("goal", "")),
            modality=str(data.get("modality", data.get("data_type", "general"))),
            research_question=str(data.get("research_question", data.get("goal", ""))),
            primary_contrast=str(data.get("primary_contrast", "requires_human_input")),
            data_type=str(data.get("data_type", data.get("modality", "general"))),
            statistical_unit=str(data.get("statistical_unit", "sample")),
            inputs=list(data.get("inputs", []) or []),
            inclusion_exclusion=list(data.get("inclusion_exclusion", []) or []),
            covariates=list(data.get("covariates", []) or []),
            batch_or_confounder_plan=str(data.get("batch_or_confounder_plan", "requires_human_input")),
            normalization_or_preprocessing=list(data.get("normalization_or_preprocessing", []) or []),
            primary_methods=list(data.get("primary_methods", []) or []),
            validation_plan=list(data.get("validation_plan", []) or []),
            sensitivity_plan=list(data.get("sensitivity_plan", []) or []),
            expected_outputs=list(data.get("expected_outputs", []) or []),
            user_approval=bool(data.get("user_approval", False)),
            execution_status=str(data.get("execution_status", "not_executed")),
            execution_backend=str(data.get("execution_backend", "dry_run")),
            group_column=str(data.get("group_column", "condition")),
            sample_id_column=str(data.get("sample_id_column", "sample_id")),
            data_requirements=list(data.get("data_requirements", []) or []),
            environment_requirements=list(data.get("environment_requirements", []) or []),
            module_candidates=list(data.get("module_candidates", []) or []),
            selected_modules=list(data.get("selected_modules", []) or []),
            analysis_graph=dict(data.get("analysis_graph", {}) or {}),
            figure_plan_bindings=list(data.get("figure_plan_bindings", []) or []),
            reviewer_risk=list(data.get("reviewer_risk", []) or []),
            raw=dict(data),
        )

    @classmethod
    def from_file(cls, path: Path) -> "AnalysisDesign":
        with Path(path).open("r", encoding="utf-8") as fh:
            data = yaml.safe_load(fh) or {}
        if not isinstance(data, dict):
            data = {}
        return cls.from_dict(data)

    def validate(self, require_approval: bool = False) -> tuple[bool, list[str]]:
        issues: list[str] = []
        if not self.run_id:
            issues.append("missing run_id")
        if not self.goal and not self.research_question:
            issues.append("missing goal or research_question")
        if not self.modality:
            issues.append("missing modality")
        if not self.statistical_unit:
            issues.append("missing statistical_unit")
        if require_approval and not self.user_approval:
            issues.append("user_approval is required for real execution")
        for field_name in REQUIRED_METHOD_FIELDS:
            if field_name == "user_approval":
                continue
            value = getattr(self, field_name, None)
            if value in ("", [], None):
                issues.append(f"missing or empty {field_name}")
            elif self._is_unresolved(value):
                issues.append(f"unresolved {field_name}")
        return not issues, issues

    @staticmethod
    def _is_unresolved(value: Any) -> bool:
        if isinstance(value, str):
            return value.strip() in UNRESOLVED_VALUES
        if isinstance(value, list):
            return bool(value) and all(
                isinstance(item, str) and item.strip() in UNRESOLVED_VALUES
                for item in value
            )
        return False

    def to_dict(self) -> dict[str, Any]:
        data = dict(self.raw)
        data.update({
            "run_id": self.run_id,
            "goal": self.goal,
            "modality": self.modality,
            "research_question": self.research_question,
            "primary_contrast": self.primary_contrast,
            "data_type": self.data_type,
            "statistical_unit": self.statistical_unit,
            "inputs": self.inputs,
            "inclusion_exclusion": self.inclusion_exclusion,
            "covariates": self.covariates,
            "batch_or_confounder_plan": self.batch_or_confounder_plan,
            "normalization_or_preprocessing": self.normalization_or_preprocessing,
            "primary_methods": self.primary_methods,
            "validation_plan": self.validation_plan,
            "sensitivity_plan": self.sensitivity_plan,
            "expected_outputs": self.expected_outputs,
            "user_approval": self.user_approval,
            "execution_status": self.execution_status,
            "execution_backend": self.execution_backend,
            "group_column": self.group_column,
            "sample_id_column": self.sample_id_column,
            "data_requirements": self.data_requirements,
            "environment_requirements": self.environment_requirements,
            "module_candidates": self.module_candidates,
            "selected_modules": self.selected_modules,
            "analysis_graph": self.analysis_graph,
            "figure_plan_bindings": self.figure_plan_bindings,
            "reviewer_risk": self.reviewer_risk,
        })
        return data
