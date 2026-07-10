"""Create a small, path-safe evidence packet from a real PBMC3K TargetTask run."""

from __future__ import annotations

import argparse
import csv
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml


SUBCLUSTER_NODE = "nodes/seurat_subcluster_programs"
EVIDENCE_FILES = [
    "analysis_graph.yaml",
    "run_manifest.yaml",
    "evaluation_report.yaml",
    "qc/bioinformatics_quality_report.yaml",
    "qc/fail_closed_decision.yaml",
    "performance/node_timing.yaml",
    "performance/output_size_report.yaml",
    "performance/performance_ledger.tsv",
    f"{SUBCLUSTER_NODE}/node_manifest.yaml",
    f"{SUBCLUSTER_NODE}/qc/subcluster_quality_report.yaml",
    f"{SUBCLUSTER_NODE}/tables/subcluster_markers.csv",
    f"{SUBCLUSTER_NODE}/tables/program_score_summary.csv",
    f"{SUBCLUSTER_NODE}/tables/marker_program_mapping.csv",
    f"{SUBCLUSTER_NODE}/tables/resolution_summary.csv",
    f"{SUBCLUSTER_NODE}/logs/sessionInfo.txt",
    f"{SUBCLUSTER_NODE}/figures/tcell_subset_umap.png",
    f"{SUBCLUSTER_NODE}/figures/subcluster_marker_heatmap.png",
    f"{SUBCLUSTER_NODE}/figures/program_score_dotplot.png",
]


def read_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def csv_rows(path: Path) -> tuple[int, list[str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        rows = sum(1 for _ in reader)
        return rows, list(reader.fieldnames or [])


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def capture(run_dir: Path, output_dir: Path) -> dict[str, Any]:
    run_dir = run_dir.resolve()
    evaluation = read_yaml(run_dir / "evaluation_report.yaml")
    quality = read_yaml(run_dir / "qc" / "bioinformatics_quality_report.yaml")
    subcluster = read_yaml(run_dir / SUBCLUSTER_NODE / "qc" / "subcluster_quality_report.yaml")
    graph = read_yaml(run_dir / "analysis_graph.yaml")
    timing = read_yaml(run_dir / "performance" / "node_timing.yaml")
    node_parameters = {
        node.get("module_id", ""): node.get("parameters", {})
        for node in ((graph.get("analysis_graph") or {}).get("nodes", []) or [])
    }
    marker_rows, marker_columns = csv_rows(run_dir / SUBCLUSTER_NODE / "tables" / "subcluster_markers.csv")
    program_rows, program_columns = csv_rows(run_dir / SUBCLUSTER_NODE / "tables" / "program_score_summary.csv")
    mapping_rows, _ = csv_rows(run_dir / SUBCLUSTER_NODE / "tables" / "marker_program_mapping.csv")
    resolution_rows, _ = csv_rows(run_dir / SUBCLUSTER_NODE / "tables" / "resolution_summary.csv")
    evaluation_status = evaluation.get("evaluation_status") or {}
    if evaluation.get("status") != "pass" or quality.get("status") != "pass":
        raise ValueError("real validation capture requires evaluation and bioinformatics QA pass")
    if evaluation.get("evidence_grade") != "workflow_test":
        raise ValueError("PBMC3K validation must remain workflow_test evidence")
    if evaluation.get("source_map_valid") is not True:
        raise ValueError("PBMC3K validation requires valid source maps")

    output_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = output_dir / "artifact_manifest.tsv"
    artifact_rows = []
    for relative in EVIDENCE_FILES:
        path = run_dir / relative
        if not path.is_file() or path.stat().st_size <= 0:
            raise FileNotFoundError(f"required validation artifact missing or empty: {relative}")
        artifact_rows.append({
            "relative_path": relative,
            "size_bytes": path.stat().st_size,
            "sha256": sha256(path),
        })
    with manifest_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["relative_path", "size_bytes", "sha256"], delimiter="\t")
        writer.writeheader()
        writer.writerows(artifact_rows)

    session_lines = (run_dir / SUBCLUSTER_NODE / "logs" / "sessionInfo.txt").read_text(
        encoding="utf-8", errors="replace"
    ).splitlines()
    r_version = next((line for line in session_lines if line.startswith("R version ")), "not_recorded")
    platform = next((line for line in session_lines if line.startswith("Platform:")), "not_recorded")
    subcluster_parameters = node_parameters.get("single_cell.seurat_subcluster_programs.v1", {})
    basic_parameters = node_parameters.get("single_cell.seurat_pbmc3k_basic.v1", {})
    summary = {
        "schema_version": "pbmc3k_real_validation.v1",
        "release": "5.1.0",
        "captured_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "run_id": run_dir.name,
        "execution_mode": "real",
        "command": "paper-workflow research analyze --intent intents/examples/pbmc3k_t_subcluster_intent.yaml --approved --execute",
        "status": evaluation.get("status"),
        "evaluation": {
            "workflow_completeness_status": evaluation_status.get("workflow_completeness_status"),
            "scientific_quality_status": evaluation_status.get("scientific_quality_status"),
            "environment_status": evaluation_status.get("environment_status"),
            "final_status": evaluation_status.get("final_status"),
            "source_map_valid": evaluation.get("source_map_valid"),
            "bioinformatics_quality_status": evaluation.get("bioinformatics_quality_status"),
        },
        "evidence_grade": evaluation.get("evidence_grade"),
        "claim_boundary": "Official PBMC3K workflow validation only; no disease, clinical, treatment, or causal claim.",
        "environment": {"r_version": r_version, "platform": platform},
        "execution": {
            "node_count": evaluation.get("node_count"),
            "completed_node_count": evaluation.get("completed_node_count"),
            "total_runtime_seconds": timing.get("total_runtime_seconds"),
            "output_file_count": evaluation.get("output_file_count"),
            "output_size_bytes": evaluation.get("output_size_bytes"),
        },
        "scientific_metrics": {
            "input_cells": subcluster.get("input_cells"),
            "subset_cells": subcluster.get("subset_cells"),
            "subset_fraction": subcluster.get("subset_fraction"),
            "subset_rule": subcluster.get("subset_rule"),
            "anchor_markers": subcluster.get("anchor_markers"),
            "min_anchor_markers": subcluster.get("min_anchor_markers"),
            "subcluster_count": subcluster.get("subcluster_count"),
            "selected_resolution": subcluster.get("selected_resolution"),
            "selection_reason": subcluster.get("selection_reason"),
            "marker_rows": marker_rows,
            "marker_columns": marker_columns,
            "program_rows": program_rows,
            "program_columns": program_columns,
            "program_mapping_rows": mapping_rows,
            "resolution_rows": resolution_rows,
        },
        "executed_parameters": {
            "qc": {
                "min_features": basic_parameters.get("min_features"),
                "max_features": basic_parameters.get("max_features"),
                "max_mt": basic_parameters.get("max_mt"),
            },
            "subcluster": {
                "min_subset_markers": subcluster_parameters.get("min_subset_markers"),
                "subset_anchor_markers": subcluster_parameters.get("subset_anchor_markers"),
                "min_anchor_markers": subcluster_parameters.get("min_anchor_markers"),
                "resolutions": subcluster_parameters.get("resolutions"),
                "marker_method": subcluster_parameters.get("marker_method"),
                "program_spec": subcluster_parameters.get("program_spec"),
            },
        },
        "artifact_manifest": "artifact_manifest.tsv",
        "large_outputs_committed": False,
    }
    with (output_dir / "validation_summary.yaml").open("w", encoding="utf-8") as handle:
        yaml.safe_dump(summary, handle, allow_unicode=True, sort_keys=False)
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", required=True)
    parser.add_argument("--out-dir", default="validation/pbmc3k_v5_1")
    args = parser.parse_args()
    summary = capture(Path(args.run_dir), Path(args.out_dir))
    print(yaml.safe_dump(summary, allow_unicode=True, sort_keys=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
