from __future__ import annotations

import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from paper_workflow.bioinformatics.run_quality_rules import BioinformaticsRunQualityRules


def write_yaml(path: Path, data: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")


def test_bioinformatics_quality_rules_pass_findmarkers_run(tmp_path: Path):
    paper = tmp_path / "papers" / "test_paper"
    run_dir = paper / "results" / "runs" / "findmarkers_20260709_v1"
    node_dir = run_dir / "nodes" / "findmarkers"
    (node_dir / "tables").mkdir(parents=True)
    (node_dir / "qc").mkdir()
    (node_dir / "logs").mkdir()
    (node_dir / "figures").mkdir()
    (node_dir / "tables" / "findmarkers_results.csv").write_text(
        "gene,p_val,avg_log2FC,pct.1,pct.2,p_val_adj,ident_1,ident_2,group_column,subset_column,subset_value\n"
        "GENE1,0.01,1.2,0.5,0.2,0.05,A,B,condition,,\n",
        encoding="utf-8",
    )
    (node_dir / "tables" / "findmarkers_summary.csv").write_text("run_id,n_genes\nx,1\n", encoding="utf-8")
    (node_dir / "qc" / "group_size_sample_mapping.csv").write_text("group,n_cells\nA,10\nB,12\n", encoding="utf-8")
    (node_dir / "logs" / "sessionInfo.txt").write_text("R session\n", encoding="utf-8")
    (node_dir / "figures" / "findmarkers_volcano.png").write_bytes(b"png")
    artifact_prefix = "results/runs/findmarkers_20260709_v1/nodes/findmarkers"
    write_yaml(
        run_dir / "run_manifest.yaml",
        {
            "status": "completed",
            "data_registry_hash": "abc",
            "nodes": [
                {
                    "node_id": "findmarkers",
                    "module_id": "single_cell.seurat_findmarkers_group_de.v1",
                    "status": "completed",
                    "artifacts": [
                        f"{artifact_prefix}/tables/findmarkers_results.csv",
                        f"{artifact_prefix}/tables/findmarkers_summary.csv",
                        f"{artifact_prefix}/qc/group_size_sample_mapping.csv",
                        f"{artifact_prefix}/logs/sessionInfo.txt",
                        f"{artifact_prefix}/figures/findmarkers_volcano.png",
                    ],
                }
            ],
        },
    )
    write_yaml(
        run_dir / "figure_source_map.yaml",
        {"figures": [{"figure_id": "v", "path": "nodes/findmarkers/figures/findmarkers_volcano.png", "claim_boundary": "exploratory"}]},
    )
    write_yaml(
        run_dir / "table_source_map.yaml",
        {"tables": [{"table_id": "t", "path": "nodes/findmarkers/tables/findmarkers_results.csv", "claim_boundary": "exploratory"}]},
    )

    result = BioinformaticsRunQualityRules(run_dir).evaluate(write_outputs=True)

    assert result["report"]["status"] == "pass"
    assert (run_dir / "qc" / "bioinformatics_quality_report.yaml").exists()
    assert (run_dir / "qc" / "next_analysis_plan.yaml").exists()
