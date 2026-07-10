"""Validation and normalization for researcher-facing intent files."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import yaml


PROJECT_ID_RE = re.compile(r"^[a-z][a-z0-9_-]{2,80}$")
SUPPORTED_GOALS = {"discovery", "validation", "mechanistic", "translational", "workflow_test"}
REQUIRED_TOP_LEVEL = {
    "schema_version",
    "project_id",
    "title",
    "question",
    "project_goal",
    "claim_boundary",
    "data",
    "expected_outputs",
}


def load_research_intent(path: Path | str) -> dict[str, Any]:
    intent_path = Path(path)
    if not intent_path.exists():
        raise FileNotFoundError(f"Research intent file not found: {intent_path}")
    data = yaml.safe_load(intent_path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise ValueError(f"Research intent must be a YAML mapping: {intent_path}")
    return data


def validate_research_intent(data: dict[str, Any]) -> dict[str, Any]:
    issues: list[str] = []
    warnings: list[str] = []
    missing = sorted(key for key in REQUIRED_TOP_LEVEL if data.get(key) in (None, "", [], {}))
    issues.extend(f"missing top-level field: {key}" for key in missing)
    if str(data.get("schema_version", "")) != "research_intent.v1":
        issues.append("schema_version must be research_intent.v1")

    project_id = str(data.get("project_id", ""))
    if project_id and not PROJECT_ID_RE.fullmatch(project_id):
        issues.append("project_id must match ^[a-z][a-z0-9_-]{2,80}$")
    project_goal = str(data.get("project_goal", ""))
    if project_goal and project_goal not in SUPPORTED_GOALS:
        issues.append(f"project_goal must be one of {sorted(SUPPORTED_GOALS)}")

    data_block = data.get("data") if isinstance(data.get("data"), dict) else {}
    for key in ("dataset_id", "modality", "format", "input_path"):
        if not data_block.get(key):
            issues.append(f"data.{key} is required")
    modality = normalize_modality(str(data_block.get("modality", "")))
    if modality not in {"single_cell", "bulk_rnaseq", "spatial", "multiomics", "general"}:
        issues.append(f"unsupported data.modality: {data_block.get('modality', '')}")

    expected = data.get("expected_outputs") if isinstance(data.get("expected_outputs"), dict) else {}
    if not any(expected.get(key) for key in ("figures", "tables", "reports")):
        issues.append("expected_outputs must declare at least one figure, table, or report")

    question = str(data.get("question", "")).lower()
    asks_group_inference = any(token in question for token in ("disease", "control", "versus", " vs ", "组间", "疾病", "对照", "差异"))
    if asks_group_inference and modality == "single_cell":
        if not data_block.get("sample_id_column"):
            warnings.append("single-cell group inference lacks data.sample_id_column; sample-level pseudobulk cannot be confirmed")
        if data_block.get("biological_replicates") not in {True, "true", "documented"}:
            warnings.append("biological replicates are not documented; cell-level DE must remain exploratory")
    if project_goal in {"mechanistic", "translational"}:
        validation = (data.get("constraints") or {}).get("orthogonal_validation")
        if not validation:
            warnings.append("mechanistic or translational goal lacks constraints.orthogonal_validation")

    return {
        "valid": not issues,
        "issues": issues,
        "warnings": warnings,
        "project_id": project_id,
        "modality": modality,
        "project_goal": project_goal,
    }


def normalize_modality(value: str) -> str:
    compact = value.lower().replace("-", "_").replace(" ", "_")
    aliases = {
        "scrna": "single_cell",
        "scrna_seq": "single_cell",
        "single_cell_rna": "single_cell",
        "single_cell_rna_seq": "single_cell",
        "bulk": "bulk_rnaseq",
        "rna_seq": "bulk_rnaseq",
        "spatial_transcriptomics": "spatial",
        "multi_omics": "multiomics",
    }
    return aliases.get(compact, compact or "general")
