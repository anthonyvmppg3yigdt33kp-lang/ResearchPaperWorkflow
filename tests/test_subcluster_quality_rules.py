from __future__ import annotations

from pathlib import Path

import yaml

from paper_workflow.bioinformatics.run_quality_rules import BioinformaticsRunQualityRules


def build_subcluster_run(tmp_path: Path, *, empty_programs: bool = False) -> Path:
    paper = tmp_path / "paper"
    run_dir = paper / "results" / "runs" / "subcluster_20260710_v1"
    node = run_dir / "nodes" / "subcluster"
    for name in ("tables", "figures", "objects", "qc", "logs"):
        (node / name).mkdir(parents=True, exist_ok=True)

    (node / "tables" / "subcluster_markers.csv").write_text(
        "gene,cluster,p_val,avg_log2FC,pct.1,pct.2,p_val_adj\nIL7R,0,0.001,1.2,0.8,0.2,0.01\n",
        encoding="utf-8",
    )
    program_rows = "" if empty_programs else "0,naive_memory_like,0.5,0.4,10\n"
    (node / "tables" / "program_score_summary.csv").write_text(
        "subcluster,program,mean_score,median_score,n_cells\n" + program_rows,
        encoding="utf-8",
    )
    (node / "tables" / "resolution_summary.csv").write_text(
        "resolution,n_subclusters,selected,selection_reason\n0.2,2,FALSE,plateau\n0.4,3,TRUE,plateau\n",
        encoding="utf-8",
    )
    (node / "qc" / "subcluster_quality_report.yaml").write_text(
        "schema_version: subcluster_quality_report.v1\nstatus: pass\ninput_cells: 100\nsubset_cells: 40\nsubset_fraction: 0.4\nsubcluster_count: 2\nsubset_rule: at least 2 declared markers and 2 lineage anchors detected\nmin_subset_markers: 2\nanchor_markers: CD3D,CD3E,NKG7,GNLY\nmin_anchor_markers: 2\n",
        encoding="utf-8",
    )
    (node / "objects" / "subcluster_seurat.rds").write_bytes(b"rds")
    (node / "logs" / "sessionInfo.txt").write_text("R 4.5\n", encoding="utf-8")
    figures = [
        "tcell_subset_umap.png",
        "resolution_grid_umap.png",
        "subcluster_marker_heatmap.png",
        "program_score_violin.png",
        "program_score_dotplot.png",
    ]
    for figure in figures:
        (node / "figures" / figure).write_bytes(b"png")

    artifact_prefix = "results/runs/subcluster_20260710_v1/nodes/subcluster"
    artifacts = [
        f"{artifact_prefix}/tables/subcluster_markers.csv",
        f"{artifact_prefix}/tables/program_score_summary.csv",
        f"{artifact_prefix}/tables/resolution_summary.csv",
        f"{artifact_prefix}/qc/subcluster_quality_report.yaml",
        f"{artifact_prefix}/objects/subcluster_seurat.rds",
        f"{artifact_prefix}/logs/sessionInfo.txt",
        *[f"{artifact_prefix}/figures/{name}" for name in figures],
    ]
    (run_dir / "run_manifest.yaml").write_text(
        yaml.safe_dump({
            "status": "completed",
            "data_registry_hash": "sha256:test",
            "nodes": [{
                "node_id": "subcluster",
                "module_id": "single_cell.seurat_subcluster_programs.v1",
                "status": "completed",
                "artifacts": artifacts,
            }],
        }, sort_keys=False),
        encoding="utf-8",
    )
    (run_dir / "figure_source_map.yaml").write_text(
        yaml.safe_dump({"figures": [{"figure_id": "f", "claim_boundary": "exploratory"}]}),
        encoding="utf-8",
    )
    (run_dir / "table_source_map.yaml").write_text(
        yaml.safe_dump({"tables": [{"table_id": "t", "claim_boundary": "exploratory"}]}),
        encoding="utf-8",
    )
    return run_dir


def test_subcluster_quality_rules_pass_complete_artifacts(tmp_path: Path):
    result = BioinformaticsRunQualityRules(build_subcluster_run(tmp_path)).evaluate()

    assert result["report"]["status"] == "pass"
    names = {check["name"] for check in result["report"]["checks"]}
    assert "subcluster.program_scores_numeric" in names
    assert "subcluster.resolution_single_selection" in names


def test_subcluster_quality_rules_block_empty_program_scores(tmp_path: Path):
    result = BioinformaticsRunQualityRules(build_subcluster_run(tmp_path, empty_programs=True)).evaluate()

    assert result["report"]["status"] == "blocked"
    failed = {check["name"] for check in result["report"]["checks"] if check["status"] != "pass"}
    assert "subcluster.program_score_summary_nonempty" in failed
