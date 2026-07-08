from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from paper_workflow.analysis import AnalysisDesign, run_analysis_adapter
from paper_workflow.bioinformatics.module_registry import ModuleRegistry
from paper_workflow.bioinformatics.module_selector import MethodSelector
from paper_workflow.outputs.result_run_manager import ResultRunManager


REPO_ROOT = Path(__file__).resolve().parent.parent


def make_paper_dir():
    tmp = tempfile.TemporaryDirectory()
    root = Path(tmp.name)
    paper = root / "papers" / "pbmc3k_demo"
    paper.mkdir(parents=True)
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
    return tmp, root, paper


def test_module_registry_exposes_valid_seurat_method_asset():
    registry = ModuleRegistry(REPO_ROOT)
    module = registry.get("single_cell.seurat_pbmc3k_basic.v1")

    assert module["modality"] == "single_cell"
    assert module["execution"]["type"] == "rscript"
    assert registry.validate_module("single_cell.seurat_pbmc3k_basic.v1") == []
    summary = registry.capability_summary()
    assert summary["executable_module_count"] >= 1
    assert summary["by_modality"]["single_cell"] >= 1


def test_method_selector_scores_pbmc_single_cell_module():
    selector = MethodSelector(REPO_ROOT)
    selected = selector.select(
        goal="Run the official Seurat PBMC3K single-cell QC, PCA, UMAP, and marker visualization workflow.",
        modalities=["scrna"],
        max_modules=3,
    )

    assert selected
    assert selected[0]["id"] == "single_cell.seurat_pbmc3k_basic.v1"
    assert selected[0]["method_selection_score"]["biological_fit"] == 1.0


def test_write_analysis_design_creates_graph_and_selection_report():
    tmp, _, paper = make_paper_dir()
    try:
        manager = ResultRunManager(paper)
        design = manager.write_analysis_design(
            run_id="pbmc3k_demo_20260708_v1",
            goal="Plan a Seurat PBMC3K single-cell tutorial workflow.",
            modality="scrna",
            inputs=["data/raw/pbmc3k/filtered_gene_bc_matrices/hg19"],
            primary_contrast="tutorial fixture; no disease contrast",
            from_code_library=True,
        )
        run_dir = manager.run_path("pbmc3k_demo_20260708_v1")

        assert design["analysis_graph"]["nodes"]
        assert design["selected_modules"][0]["module_id"] == "single_cell.seurat_pbmc3k_basic.v1"
        assert (run_dir / "analysis_graph.yaml").exists()
        assert (run_dir / "method_selection_report.md").exists()
    finally:
        tmp.cleanup()


def test_analysis_graph_adapter_dry_run_writes_node_manifest():
    tmp, _, paper = make_paper_dir()
    try:
        manager = ResultRunManager(paper)
        manager.write_analysis_design(
            run_id="pbmc3k_demo_20260708_v1",
            goal="Plan a Seurat PBMC3K single-cell tutorial workflow.",
            modality="scrna",
            inputs=["data/raw/pbmc3k/filtered_gene_bc_matrices/hg19"],
            primary_contrast="tutorial fixture; no disease contrast",
            from_code_library=True,
        )
        run_dir = manager.run_path("pbmc3k_demo_20260708_v1")
        design = AnalysisDesign.from_file(run_dir / "analysis_design.yaml")

        result = run_analysis_adapter(design, run_dir, execute=False)
        manifest = yaml.safe_load((run_dir / "run_manifest.yaml").read_text(encoding="utf-8"))

        assert result.status == "dry_run_completed"
        assert result.adapter == "analysis_graph_executor"
        assert manifest["analysis_adapter"] == "analysis_graph_executor"
        assert manifest["nodes"][0]["status"] == "dry_run_completed"
        assert (run_dir / "nodes" / "seurat_basic_workflow" / "node_manifest.yaml").exists()
        assert (run_dir / "figure_source_map.yaml").exists()
        assert (run_dir / "table_source_map.yaml").exists()
    finally:
        tmp.cleanup()


def test_cli_list_capabilities_returns_scored_method_asset():
    env = dict(os.environ)
    env["PYTHONPATH"] = str(REPO_ROOT / "src") + os.pathsep + env.get("PYTHONPATH", "")
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "paper_workflow.cli.main",
            "list-capabilities",
            "--question",
            "Seurat PBMC3K single-cell QC and UMAP",
            "--modality",
            "scrna",
            "--json",
        ],
        cwd=str(REPO_ROOT),
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )

    assert completed.returncode == 0, completed.stdout + completed.stderr
    payload = json.loads(completed.stdout)
    assert payload["selected_modules"][0]["id"] == "single_cell.seurat_pbmc3k_basic.v1"
