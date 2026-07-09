"""Evidence-bound reporting for TargetTask runs."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from paper_workflow.outputs.result_run_manager import read_yaml, utc_now, write_yaml


def write_target_reports(run_dir: Path, target: dict[str, Any], evaluation: dict[str, Any]) -> dict[str, str]:
    """Write manuscript-facing reports without exceeding the evidence boundary."""
    run_dir = Path(run_dir)
    paths = {
        "evidence_matrix": run_dir / "tables" / "evidence_matrix.tsv",
        "figure_storyline": run_dir / "brief" / "FIGURE_STORYLINE.md",
        "methods_draft": run_dir / "manuscript" / "methods_draft.md",
        "results_skeleton": run_dir / "manuscript" / "results_skeleton.md",
        "claim_boundary": run_dir / "claim_boundary_ledger.yaml",
        "claim_ledger": run_dir / "claims" / "claim_ledger.jsonl",
        "reviewer_risk": run_dir / "review" / "reviewer_risk_report.md",
    }
    for path in paths.values():
        path.parent.mkdir(parents=True, exist_ok=True)

    figure_map = read_yaml(run_dir / "figure_source_map.yaml")
    table_map = read_yaml(run_dir / "table_source_map.yaml")
    rows = _evidence_rows(figure_map, table_map)
    with paths["evidence_matrix"].open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(
            fh,
            delimiter="\t",
            fieldnames=["kind", "id", "path", "method", "statistical_unit", "claim_boundary", "source"],
        )
        writer.writeheader()
        writer.writerows(rows)

    paths["figure_storyline"].write_text(_figure_storyline(target, rows, evaluation), encoding="utf-8")
    paths["methods_draft"].write_text(_methods_draft(target, run_dir, evaluation), encoding="utf-8")
    paths["results_skeleton"].write_text(_results_skeleton(target, rows, evaluation), encoding="utf-8")
    write_yaml(paths["claim_boundary"], _claim_boundary_ledger(target, evaluation))
    with paths["claim_ledger"].open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps({"created_at": utc_now(), **row}, ensure_ascii=False, sort_keys=True) + "\n")
    paths["reviewer_risk"].write_text(_reviewer_risk_report(target, evaluation), encoding="utf-8")
    return {key: str(path) for key, path in paths.items()}


def _evidence_rows(figure_map: dict[str, Any], table_map: dict[str, Any]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for item in figure_map.get("figures", []) or []:
        if not isinstance(item, dict):
            continue
        rows.append({
            "kind": "figure",
            "id": str(item.get("figure_id", "")),
            "path": str(item.get("path", "")),
            "method": str(item.get("method", "")),
            "statistical_unit": str(item.get("statistical_unit", "")),
            "claim_boundary": str(item.get("claim_boundary", "")),
            "source": str(item.get("source_data", "")),
        })
    for item in table_map.get("tables", []) or []:
        if not isinstance(item, dict):
            continue
        rows.append({
            "kind": "table",
            "id": str(item.get("table_id", "")),
            "path": str(item.get("path", "")),
            "method": str(item.get("method", "")),
            "statistical_unit": str(item.get("statistical_unit", "")),
            "claim_boundary": str(item.get("claim_boundary", "")),
            "source": str(item.get("source_inputs", "")),
        })
    return rows


def _figure_storyline(target: dict[str, Any], rows: list[dict[str, str]], evaluation: dict[str, Any]) -> str:
    lines = [
        "# Figure Storyline",
        "",
        f"Target: {target.get('title', '')}",
        f"Evidence grade: {target.get('evidence_grade', '')}",
        f"Final status: {evaluation.get('status', evaluation.get('final_status', 'unknown'))}",
        "",
        "## Panels",
        "",
    ]
    figures = [row for row in rows if row["kind"] == "figure"]
    if not figures:
        lines.append("No figure can be promoted because no valid figure source map entry is available.")
    for row in figures:
        lines.extend([
            f"- {row['id']}: {row['method']}",
            f"  Boundary: {row['claim_boundary'] or 'not declared'}",
        ])
    return "\n".join(lines) + "\n"


def _methods_draft(target: dict[str, Any], run_dir: Path, evaluation: dict[str, Any]) -> str:
    params = target.get("parameters", {}) if isinstance(target.get("parameters"), dict) else {}
    lines = [
        "# Methods Draft",
        "",
        f"Target task `{target.get('target_id', '')}` used `{target.get('data', {}).get('dataset_id', '')}` as a `{target.get('evidence_grade', '')}` dataset.",
        f"Claim boundary: {target.get('claim_boundary', '')}",
        "",
        "The planned workflow records QC, normalization, PCA/UMAP/clustering, T-cell-like subsetting, subcluster reanalysis, marker detection, and program scoring parameters in the TargetTask contract.",
        f"QC thresholds: {params.get('qc', 'see target_task_resolved.yaml')}",
        f"Subclustering: {params.get('subclustering', 'see target_task_resolved.yaml')}",
        f"Marker detection: {params.get('marker_detection', 'see target_task_resolved.yaml')}",
        "",
        f"Run evidence path: {run_dir.name}/run_manifest.yaml; evaluation status: {evaluation.get('status', 'unknown')}.",
    ]
    return "\n".join(lines) + "\n"


def _results_skeleton(target: dict[str, Any], rows: list[dict[str, str]], evaluation: dict[str, Any]) -> str:
    final_status = str(evaluation.get("status", evaluation.get("final_status", "")))
    lines = ["# Results Skeleton", ""]
    if final_status != "pass":
        lines.extend([
            "No conclusion paragraph is generated because the fail-closed evaluation did not pass.",
            f"Current final status: {final_status or 'unknown'}",
            "",
            "Allowed statement: the TargetTask produced a blocked or incomplete workflow-validation packet that identifies the missing evidence gates.",
        ])
        return "\n".join(lines) + "\n"
    lines.extend([
        "The PBMC3K workflow-validation TargetTask completed with pass status.",
        "Results are limited to tutorial workflow validation and exploratory T-cell-like subcluster structure.",
        f"Evidence entries available: {len(rows)}",
        "Unsupported conclusions: disease mechanism, clinical biomarker, treatment response, or causal immune state.",
    ])
    return "\n".join(lines) + "\n"


def _claim_boundary_ledger(target: dict[str, Any], evaluation: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "claim_boundary_ledger.v1",
        "target_id": target.get("target_id", ""),
        "evidence_grade": target.get("evidence_grade", ""),
        "claim_boundary": target.get("claim_boundary", ""),
        "forbidden_claims": (target.get("analysis_goal") or {}).get("forbidden_claims", []),
        "scientific_claim_permission": "exploratory_only" if evaluation.get("status") == "pass" else "no_claim_until_fail_closed_passes",
        "updated_at": utc_now(),
    }


def _reviewer_risk_report(target: dict[str, Any], evaluation: dict[str, Any]) -> str:
    risks = [
        "PBMC3K is an official tutorial fixture and cannot support disease, clinical, or mechanistic claims.",
        "Cell-level marker tests are exploratory unless biological replicate-aware inference is documented.",
        "UMAP is a visualization and cannot by itself establish biological conclusions.",
    ]
    lines = [
        "# Reviewer Risk Report",
        "",
        f"Target: {target.get('target_id', '')}",
        f"Final status: {evaluation.get('status', 'unknown')}",
        "",
    ]
    for risk in risks:
        lines.append(f"- {risk}")
    return "\n".join(lines) + "\n"
