"""Create a Methods draft from TargetTask evidence without adding claims."""

from __future__ import annotations

from pathlib import Path
from typing import Any


def build_methods_draft(target: dict[str, Any], run_dir: Path, evaluation: dict[str, Any]) -> str:
    """Render a concise, evidence-bound Methods draft for a run."""
    params = target.get("parameters", {}) if isinstance(target.get("parameters"), dict) else {}
    data = target.get("data", {}) if isinstance(target.get("data"), dict) else {}
    lines = [
        "# Methods Draft",
        "",
        f"Target task `{target.get('target_id', '')}` used `{data.get('dataset_id', '')}` as a `{target.get('evidence_grade', '')}` dataset.",
        f"Claim boundary: {target.get('claim_boundary', '')}",
        "",
        "The workflow records QC, normalization, dimensional reduction, clustering, subcluster reanalysis, marker detection, program scoring, source maps, and session information in a run-scoped TargetTask packet.",
        f"QC thresholds: {params.get('qc', 'see target_task_resolved.yaml')}",
        f"Subclustering: {params.get('subclustering', 'see target_task_resolved.yaml')}",
        f"Marker detection: {params.get('marker_detection', 'see target_task_resolved.yaml')}",
        "",
        f"Run evidence path: {Path(run_dir).name}/run_manifest.yaml; evaluation status: {evaluation.get('status', 'unknown')}.",
    ]
    return "\n".join(lines) + "\n"
