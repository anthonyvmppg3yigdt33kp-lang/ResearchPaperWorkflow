from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from paper_workflow.analysis import AnalysisDesign, run_analysis_adapter
from paper_workflow.bioinformatics.environment_registry import EnvironmentRegistry
from paper_workflow.bioinformatics.module_registry import ModuleRegistry
from paper_workflow.bioinformatics.module_selector import MethodSelector
from paper_workflow.outputs.result_run_manager import ResultRunManager


REPO_ROOT = Path(__file__).resolve().parent.parent
BATCH7_SINGLE_CELL_MODULES = [
    "single_cell.seurat_qc.v1",
    "single_cell.seurat_integration_harmony.v1",
    "single_cell.seurat_clustering_umap.v1",
    "single_cell.marker_feature_plot.v1",
    "single_cell.pseudobulk_aggregate.v1",
    "single_cell.pseudobulk_deseq2.v1",
]
BATCH8_BULK_MODULES = [
    "bulk_rnaseq.deseq2_de.v1",
    "bulk_rnaseq.limma_voom_de.v1",
    "bulk_rnaseq.wgcna.v1",
    "bulk_rnaseq.fgsea_enrichment.v1",
    "bulk_rnaseq.immune_deconvolution_adapter.v1",
]
BATCH9_SPATIAL_MODULES = [
    "spatial.seurat_spatial_qc.v1",
    "spatial.spatial_feature_plot.v1",
    "spatial.spatial_domain_detection.v1",
    "spatial.deconvolution_cell2location_or_rctd.v1",
    "spatial.spatial_ligand_receptor.v1",
]
BATCH9_COMMUNICATION_MODULES = [
    "single_cell.cellchat_communication.v1",
    "single_cell.nichenet_ligand_target.v1",
]
BATCH9_SOURCE_MAP_FIELDS = {
    "coordinate_system",
    "spot_cell_bin_unit",
    "tissue_section",
    "sample_id",
    "deconvolution_reference",
    "method_version",
}


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


def test_module_registry_includes_batch7_single_cell_assets():
    registry = ModuleRegistry(REPO_ROOT)
    modules = registry.list_modules(modality="scrna")
    ids = {module["id"] for module in modules}

    assert len(modules) >= 7
    assert "single_cell.seurat_pbmc3k_basic.v1" in ids
    for module_id in BATCH7_SINGLE_CELL_MODULES:
        assert module_id in ids
        assert registry.validate_module(module_id) == []


def test_batch7_module_directories_have_contract_files():
    required = [
        "module.yaml",
        "env_profile.yaml",
        "main.R",
        "README.md",
        "tests/toy_input_manifest.yaml",
        "tests/expected_outputs.yaml",
    ]
    for module_id in BATCH7_SINGLE_CELL_MODULES:
        module = ModuleRegistry(REPO_ROOT).get(module_id)
        module_dir = REPO_ROOT / module["source"]["path"]
        module_dir = module_dir.parent
        for rel in required:
            assert (module_dir / rel).exists(), f"{module_id} missing {rel}"


def test_batch7_single_cell_wrappers_support_direct_dry_run():
    rscript = shutil.which("Rscript") or EnvironmentRegistry(REPO_ROOT).resolve_runner("r_seurat_v5", language="r")
    if not rscript or not Path(rscript).exists():
        pytest.skip("Rscript is not available for direct R wrapper dry-run")

    registry = ModuleRegistry(REPO_ROOT)
    for module_id in BATCH7_SINGLE_CELL_MODULES:
        module = registry.get(module_id)
        script = REPO_ROOT / module["source"]["path"]
        expected_path = script.parent / "tests" / "expected_outputs.yaml"
        expected = yaml.safe_load(expected_path.read_text(encoding="utf-8")) or {}
        with tempfile.TemporaryDirectory() as tmpdir:
            completed = subprocess.run(
                [
                    rscript,
                    str(script),
                    "--dry-run",
                    "--out",
                    tmpdir,
                    "--run-id",
                    f"toy_{module_id.split('.')[-2]}",
                ],
                cwd=str(REPO_ROOT),
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
                timeout=60,
            )
            assert completed.returncode == 0, completed.stdout + completed.stderr
            for rel in expected["required_outputs"]:
                assert (Path(tmpdir) / rel).exists(), f"{module_id} did not write {rel}"


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


def test_write_analysis_design_respects_module_limit():
    tmp, _, paper = make_paper_dir()
    try:
        manager = ResultRunManager(paper)
        design = manager.write_analysis_design(
            run_id="pbmc3k_single_module_20260709_v1",
            goal="Plan a Seurat PBMC3K single-cell tutorial workflow.",
            modality="scrna",
            inputs=["data/raw/pbmc3k/filtered_gene_bc_matrices/hg19"],
            primary_contrast="tutorial fixture; no disease contrast",
            from_code_library=True,
            module_limit=1,
        )

        assert design["module_selection"]["module_limit"] == 1
        assert len(design["selected_modules"]) == 1
        assert len(design["analysis_graph"]["nodes"]) == 1
        assert design["selected_modules"][0]["module_id"] == "single_cell.seurat_pbmc3k_basic.v1"
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


def test_cli_list_modules_returns_batch7_single_cell_assets():
    env = dict(os.environ)
    env["PYTHONPATH"] = str(REPO_ROOT / "src") + os.pathsep + env.get("PYTHONPATH", "")
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "paper_workflow.cli.main",
            "list-modules",
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
    ids = {module["id"] for module in payload["modules"]}
    assert len(ids) >= 7
    for module_id in BATCH7_SINGLE_CELL_MODULES:
        assert module_id in ids


def test_module_registry_includes_batch8_bulk_assets():
    registry = ModuleRegistry(REPO_ROOT)
    modules = registry.list_modules(modality="bulk_rnaseq")
    ids = {module["id"] for module in modules}

    assert len(modules) >= 6
    assert "bulk_rnaseq.python_builtin_pilot.v1" in ids
    for module_id in BATCH8_BULK_MODULES:
        assert module_id in ids
        assert registry.validate_module(module_id) == []


def test_batch8_bulk_module_directories_have_contract_files():
    required = [
        "module.yaml",
        "env_profile.yaml",
        "main.R",
        "README.md",
        "tests/toy_input_manifest.yaml",
        "tests/expected_outputs.yaml",
    ]
    registry = ModuleRegistry(REPO_ROOT)
    for module_id in BATCH8_BULK_MODULES:
        module = registry.get(module_id)
        module_dir = (REPO_ROOT / module["source"]["path"]).parent
        for rel in required:
            assert (module_dir / rel).exists(), f"{module_id} missing {rel}"


def test_batch8_bulk_wrappers_support_direct_dry_run():
    rscript = shutil.which("Rscript") or EnvironmentRegistry(REPO_ROOT).resolve_runner("r_bulk_rnaseq", language="r")
    if not rscript or not Path(rscript).exists():
        pytest.skip("Rscript is not available for direct bulk wrapper dry-run")

    registry = ModuleRegistry(REPO_ROOT)
    for module_id in BATCH8_BULK_MODULES:
        module = registry.get(module_id)
        script = REPO_ROOT / module["source"]["path"]
        expected_path = script.parent / "tests" / "expected_outputs.yaml"
        expected = yaml.safe_load(expected_path.read_text(encoding="utf-8")) or {}
        with tempfile.TemporaryDirectory() as tmpdir:
            completed = subprocess.run(
                [
                    rscript,
                    str(script),
                    "--dry-run",
                    "--out",
                    tmpdir,
                    "--run-id",
                    f"toy_{module_id.split('.')[-2]}",
                ],
                cwd=str(REPO_ROOT),
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
                timeout=60,
            )
            assert completed.returncode == 0, completed.stdout + completed.stderr
            for rel in expected["required_outputs"]:
                assert (Path(tmpdir) / rel).exists(), f"{module_id} did not write {rel}"


def test_bulk_method_selection_includes_publication_oriented_assets():
    selector = MethodSelector(REPO_ROOT)
    selected = selector.select(
        goal="Plan publication-oriented bulk RNA-seq DESeq2 limma WGCNA and fgsea analysis.",
        modalities=["bulk_rnaseq"],
        max_modules=4,
    )
    ids = {module["id"] for module in selected}

    assert ids - {"bulk_rnaseq.python_builtin_pilot.v1"}
    assert any(module_id in ids for module_id in {"bulk_rnaseq.deseq2_de.v1", "bulk_rnaseq.limma_voom_de.v1"})


def test_module_registry_includes_batch9_spatial_and_communication_assets():
    registry = ModuleRegistry(REPO_ROOT)
    spatial_modules = registry.list_modules(modality="spatial")
    single_cell_modules = registry.list_modules(modality="scrna")
    spatial_ids = {module["id"] for module in spatial_modules}
    single_cell_ids = {module["id"] for module in single_cell_modules}

    assert len(spatial_modules) >= 5
    for module_id in BATCH9_SPATIAL_MODULES:
        assert module_id in spatial_ids
        assert registry.validate_module(module_id) == []
    for module_id in BATCH9_COMMUNICATION_MODULES:
        assert module_id in single_cell_ids
        assert registry.validate_module(module_id) == []


def test_batch9_spatial_and_communication_directories_have_contract_files():
    required = [
        "module.yaml",
        "env_profile.yaml",
        "main.R",
        "README.md",
        "tests/toy_input_manifest.yaml",
        "tests/expected_outputs.yaml",
    ]
    registry = ModuleRegistry(REPO_ROOT)
    for module_id in BATCH9_SPATIAL_MODULES + BATCH9_COMMUNICATION_MODULES:
        module = registry.get(module_id)
        module_dir = (REPO_ROOT / module["source"]["path"]).parent
        for rel in required:
            assert (module_dir / rel).exists(), f"{module_id} missing {rel}"


def test_batch9_spatial_and_communication_wrappers_support_direct_dry_run():
    rscript = shutil.which("Rscript") or EnvironmentRegistry(REPO_ROOT).resolve_runner("r_spatial_omics", language="r")
    if not rscript or not Path(rscript).exists():
        pytest.skip("Rscript is not available for direct spatial wrapper dry-run")

    registry = ModuleRegistry(REPO_ROOT)
    for module_id in BATCH9_SPATIAL_MODULES + BATCH9_COMMUNICATION_MODULES:
        module = registry.get(module_id)
        script = REPO_ROOT / module["source"]["path"]
        expected_path = script.parent / "tests" / "expected_outputs.yaml"
        expected = yaml.safe_load(expected_path.read_text(encoding="utf-8")) or {}
        with tempfile.TemporaryDirectory() as tmpdir:
            completed = subprocess.run(
                [
                    rscript,
                    str(script),
                    "--dry-run",
                    "--out",
                    tmpdir,
                    "--run-id",
                    f"toy_{module_id.split('.')[-2]}",
                ],
                cwd=str(REPO_ROOT),
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
                timeout=60,
            )
            assert completed.returncode == 0, completed.stdout + completed.stderr
            for rel in expected["required_outputs"]:
                assert (Path(tmpdir) / rel).exists(), f"{module_id} did not write {rel}"
            source_map = yaml.safe_load((Path(tmpdir) / "figure_source_map.yaml").read_text(encoding="utf-8"))
            figure = source_map["figures"][0]
            assert BATCH9_SOURCE_MAP_FIELDS.issubset(figure.keys())
            assert "hypothesis-generating" in (Path(tmpdir) / "node_manifest.yaml").read_text(encoding="utf-8")


def test_cli_list_capabilities_returns_spatial_assets_with_claim_boundaries():
    env = dict(os.environ)
    env["PYTHONPATH"] = str(REPO_ROOT / "src") + os.pathsep + env.get("PYTHONPATH", "")
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "paper_workflow.cli.main",
            "list-capabilities",
            "--question",
            "空间转录组细胞通讯和空间共定位",
            "--modality",
            "spatial",
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
    ids = {module["id"] for module in payload["selected_modules"]}
    risks = {
        str(risk)
        for module in payload["selected_modules"]
        for risk in module.get("reviewer_risk", [])
    }
    assert ids & set(BATCH9_SPATIAL_MODULES)
    assert "spatial overlap does not prove causality" in risks
    assert "orthogonal validation required for mechanism claims" in risks
