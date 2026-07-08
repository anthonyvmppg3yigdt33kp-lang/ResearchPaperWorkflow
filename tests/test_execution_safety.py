from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from paper_workflow.analysis import AnalysisDesign, run_analysis_adapter
from paper_workflow.bioinformatics.analysis_graph import AnalysisGraph, AnalysisGraphNode
from paper_workflow.bioinformatics.analysis_graph_executor import AnalysisGraphExecutor
from paper_workflow.outputs.result_run_manager import ResultRunManager


REPO_ROOT = Path(__file__).resolve().parent.parent


def make_method_asset_project():
    tmp = tempfile.TemporaryDirectory()
    root = Path(tmp.name)
    paper = root / "papers" / "test_paper"
    paper.mkdir(parents=True)
    (root / "AGENTS.md").write_text("# Test root\n", encoding="utf-8")
    (root / "src").mkdir()
    (root / "code_library").mkdir()
    for name in ["module_registry.yaml", "environment_registry.yaml"]:
        (root / "code_library" / name).write_text(
            (REPO_ROOT / "code_library" / name).read_text(encoding="utf-8"),
            encoding="utf-8",
        )
    module_src = REPO_ROOT / "code_library" / "modules" / "single_cell" / "seurat_pbmc3k_basic"
    module_dst = root / "code_library" / "modules" / "single_cell" / "seurat_pbmc3k_basic"
    module_dst.mkdir(parents=True)
    for name in ["main.R", "module.yaml", "env_profile.yaml", "PROVENANCE.md"]:
        (module_dst / name).write_text((module_src / name).read_text(encoding="utf-8"), encoding="utf-8")
    return tmp, root, paper


def prepare_graph_run(paper: Path, run_id: str = "pbmc3k_demo_20260708_v1") -> Path:
    manager = ResultRunManager(paper)
    manager.write_analysis_design(
        run_id=run_id,
        goal="Plan a Seurat PBMC3K single-cell tutorial workflow.",
        modality="scrna",
        inputs=["data/raw/pbmc3k/filtered_gene_bc_matrices/hg19"],
        primary_contrast="tutorial fixture; no disease contrast",
        from_code_library=True,
    )
    return manager.run_path(run_id)


def test_run_analysis_execute_requires_approval():
    tmp, root, paper = make_method_asset_project()
    try:
        run_id = "pbmc3k_demo_20260708_v1"
        prepare_graph_run(paper, run_id=run_id)
        env = dict(os.environ)
        env["PYTHONPATH"] = str(REPO_ROOT / "src") + os.pathsep + env.get("PYTHONPATH", "")

        completed = subprocess.run(
            [
                sys.executable,
                "-m",
                "paper_workflow.cli.main",
                "run-analysis",
                "--paper",
                "test_paper",
                "--run-id",
                run_id,
                "--execute",
            ],
            cwd=str(root),
            env=env,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )

        assert completed.returncode != 0
        assert "--execute requires --approved" in completed.stderr + completed.stdout
    finally:
        tmp.cleanup()


def test_run_analysis_adapter_blocks_unapproved_real_execution():
    tmp, _, paper = make_method_asset_project()
    try:
        run_dir = prepare_graph_run(paper)
        design = AnalysisDesign.from_file(run_dir / "analysis_design.yaml")
        design.user_approval = False

        result = run_analysis_adapter(design, run_dir, execute=True)

        assert result.status == "blocked"
        assert result.adapter == "approval_gate"
        assert "user_approval is required" in result.errors[0]
    finally:
        tmp.cleanup()


def test_graph_executor_records_blocked_manifest_without_approval():
    tmp, root, paper = make_method_asset_project()
    try:
        run_dir = paper / "results" / "runs" / "blocked_graph"
        run_dir.mkdir(parents=True)
        graph = AnalysisGraph(
            run_id="blocked_graph",
            research_question="Run PBMC3K graph",
            primary_objective="Test approval gate",
            statistical_unit="cell",
            execution_policy={"require_user_approval": True},
            nodes=[
                AnalysisGraphNode(
                    node_id="seurat_basic_workflow",
                    module_id="single_cell.seurat_pbmc3k_basic.v1",
                )
            ],
        )

        result = AnalysisGraphExecutor(root).run(graph, run_dir, execute=True, approval=False)
        manifest = yaml.safe_load((run_dir / "run_manifest.yaml").read_text(encoding="utf-8"))

        assert result.status == "blocked"
        assert result.metrics["node_count"] == 0
        assert manifest["execution_status"] == "blocked"
        assert "user_approval_required" in manifest["block_reason"]
        assert manifest["approval_required"] is True
        assert manifest["approval_granted"] is False
        assert "analysis graph execution requires explicit user approval" in manifest["errors"]
    finally:
        tmp.cleanup()
