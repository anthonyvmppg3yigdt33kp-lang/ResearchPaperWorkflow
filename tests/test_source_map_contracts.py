from __future__ import annotations

import tempfile
from pathlib import Path

import yaml

import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from paper_workflow.bioinformatics.analysis_graph import AnalysisGraph
from paper_workflow.bioinformatics.analysis_graph_executor import AnalysisGraphExecutor
from paper_workflow.outputs.source_map import SourceMapValidator


REPO_ROOT = Path(__file__).resolve().parent.parent


def test_source_map_validator_flags_missing_required_figure_fields():
    validator = SourceMapValidator()
    issues = validator.validate_figure_map({"figures": [{"figure_id": "umap", "path": "figures/umap.png"}]})

    assert "figure[0] missing source_data" in issues
    assert "figure[0] missing statistical_unit" in issues
    assert "figure[0] missing claim_boundary" in issues


def test_graph_source_map_aggregation_preserves_node_statistical_unit():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        paper = root / "papers" / "test_paper"
        run_dir = paper / "results" / "runs" / "pbmc3k_demo_20260708_v1"
        node_dir = run_dir / "nodes" / "seurat_basic_workflow"
        node_dir.mkdir(parents=True)
        (root / "AGENTS.md").write_text("# Test root\n", encoding="utf-8")
        (root / "src").mkdir()
        (root / "code_library").mkdir()
        (root / "code_library" / "module_registry.yaml").write_text(
            (REPO_ROOT / "code_library" / "module_registry.yaml").read_text(encoding="utf-8"),
            encoding="utf-8",
        )
        (root / "code_library" / "environment_registry.yaml").write_text(
            (REPO_ROOT / "code_library" / "environment_registry.yaml").read_text(encoding="utf-8"),
            encoding="utf-8",
        )
        module_src = REPO_ROOT / "code_library" / "modules" / "single_cell" / "seurat_pbmc3k_basic"
        module_dst = root / "code_library" / "modules" / "single_cell" / "seurat_pbmc3k_basic"
        module_dst.mkdir(parents=True)
        for name in ["main.R", "module.yaml", "env_profile.yaml", "PROVENANCE.md"]:
            (module_dst / name).write_text((module_src / name).read_text(encoding="utf-8"), encoding="utf-8")
        (node_dir / "figure_source_map.yaml").write_text(
            yaml.safe_dump(
                {
                    "schema_version": "node_source_map.v1",
                    "figures": [
                        {
                            "figure_id": "umap_clusters",
                            "path": "figures/umap_clusters.png",
                            "source_data": "objects/pbmc3k_seurat_basic.rds",
                            "script": "code_library/modules/single_cell/seurat_pbmc3k_basic/main.R",
                            "method": "Seurat UMAP visualization",
                            "statistical_unit": "cell",
                            "claim_boundary": "visualization-only exploratory structure",
                        }
                    ],
                },
                sort_keys=False,
            ),
            encoding="utf-8",
        )
        (node_dir / "table_source_map.yaml").write_text(
            yaml.safe_dump(
                {
                    "schema_version": "node_source_map.v1",
                    "tables": [
                        {
                            "table_id": "cluster_counts",
                            "path": "tables/cluster_counts.csv",
                            "source_inputs": "objects/pbmc3k_seurat_basic.rds",
                            "method": "table(Idents(pbmc)) after FindClusters",
                            "statistical_unit": "cell",
                        }
                    ],
                },
                sort_keys=False,
            ),
            encoding="utf-8",
        )
        record = {
            "node_id": "seurat_basic_workflow",
            "module_id": "single_cell.seurat_pbmc3k_basic.v1",
            "artifacts": [
                "results/runs/pbmc3k_demo_20260708_v1/nodes/seurat_basic_workflow/figure_source_map.yaml",
                "results/runs/pbmc3k_demo_20260708_v1/nodes/seurat_basic_workflow/table_source_map.yaml",
            ],
        }
        graph = AnalysisGraph(
            run_id="pbmc3k_demo_20260708_v1",
            research_question="PBMC3K workflow",
            primary_objective="workflow test",
            statistical_unit="cell",
            nodes=[],
        )

        status = AnalysisGraphExecutor(root)._write_aggregate_source_maps(graph, run_dir, paper, [record], [])
        figures = yaml.safe_load((run_dir / "figure_source_map.yaml").read_text(encoding="utf-8"))["figures"]
        tables = yaml.safe_load((run_dir / "table_source_map.yaml").read_text(encoding="utf-8"))["tables"]

        assert status["status"] == "pass"
        assert figures[0]["statistical_unit"] == "cell"
        assert figures[0]["source_data"] == "nodes/seurat_basic_workflow/objects/pbmc3k_seurat_basic.rds"
        assert figures[0]["node_id"] == "seurat_basic_workflow"
        assert figures[0]["module_claim_boundary"]
        assert tables[0]["statistical_unit"] == "cell"
