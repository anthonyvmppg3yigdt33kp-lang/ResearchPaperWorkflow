"""Schema checks for TargetTask contracts."""

from __future__ import annotations

import re
from typing import Any


RUN_ID_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_-]*_[0-9]{8}_v[0-9]+$")

REQUIRED_TOP_LEVEL = [
    "schema_version",
    "target_id",
    "title",
    "mode",
    "evidence_grade",
    "claim_boundary",
    "data",
    "environment",
    "analysis_goal",
    "workflow",
    "quality_gates",
    "outputs",
]

FORBIDDEN_DEFAULT_CLAIMS = {
    "disease mechanism",
    "clinical biomarker",
    "treatment response",
    "causal immune state",
}


def validate_target_task(data: dict[str, Any]) -> dict[str, Any]:
    issues: list[str] = []
    warnings: list[str] = []
    for key in REQUIRED_TOP_LEVEL:
        if key not in data or data.get(key) in ("", None, [], {}):
            issues.append(f"missing top-level field: {key}")
    target_id = str(data.get("target_id", ""))
    if target_id and not RUN_ID_RE.match(target_id):
        issues.append("target_id must match <name>_<YYYYMMDD>_v<N>")
    if str(data.get("schema_version", "")) != "target_task.v1":
        issues.append("schema_version must be target_task.v1")
    if not str(data.get("claim_boundary", "")).strip():
        issues.append("claim_boundary is required")

    data_block = data.get("data") if isinstance(data.get("data"), dict) else {}
    for key in ["dataset_id", "modality", "format", "input_path", "role"]:
        if not data_block.get(key):
            issues.append(f"data.{key} is required")

    env_block = data.get("environment") if isinstance(data.get("environment"), dict) else {}
    required_envs = env_block.get("required_envs") or []
    if not isinstance(required_envs, list) or not required_envs:
        issues.append("environment.required_envs must be a non-empty list")

    workflow = data.get("workflow") if isinstance(data.get("workflow"), dict) else {}
    steps = workflow.get("steps") or []
    if not isinstance(steps, list) or not steps:
        issues.append("workflow.steps must be a non-empty list")

    quality = data.get("quality_gates") if isinstance(data.get("quality_gates"), dict) else {}
    for key in [
        "fail_closed",
        "require_session_info",
        "require_source_maps",
        "require_claim_boundary",
        "require_no_personal_paths",
    ]:
        if quality.get(key) is not True:
            issues.append(f"quality_gates.{key} must be true for v5 TargetTask execution")

    goal = data.get("analysis_goal") if isinstance(data.get("analysis_goal"), dict) else {}
    forbidden_claims = {str(item).lower() for item in goal.get("forbidden_claims", []) or []}
    missing_forbidden = sorted(FORBIDDEN_DEFAULT_CLAIMS - forbidden_claims)
    if missing_forbidden:
        warnings.append(f"analysis_goal.forbidden_claims missing recommended boundaries: {missing_forbidden}")

    return {
        "valid": not issues,
        "issues": issues,
        "warnings": warnings,
        "target_id": target_id,
        "resolved_steps": steps,
        "required_envs": required_envs,
    }
