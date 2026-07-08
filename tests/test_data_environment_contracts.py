from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from paper_workflow.bioinformatics.analysis_graph import AnalysisGraph
from paper_workflow.bioinformatics.data_registry import DataRegistry
from paper_workflow.bioinformatics.environment_registry import EnvironmentRegistry


REPO_ROOT = Path(__file__).resolve().parent.parent


def make_root():
    tmp = tempfile.TemporaryDirectory()
    root = Path(tmp.name)
    (root / "AGENTS.md").write_text("# Test root\n", encoding="utf-8")
    (root / "src").mkdir()
    (root / "code_library").mkdir()
    (root / "code_library" / "environment_registry.yaml").write_text(
        (REPO_ROOT / "code_library" / "environment_registry.yaml").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    return tmp, root


def test_environment_lock_required_blocks_r_seurat_without_lock_file():
    tmp, root = make_root()
    try:
        status = EnvironmentRegistry(root).validate_environment(
            "r_seurat_v5",
            language="R",
            require_lock=True,
            require_packages=False,
        )

        assert status["status"] == "blocked"
        assert status["lock_file_present"] is False
        assert status["reproducibility_grade"] == "degraded"
        assert any("lock file required" in issue for issue in status["issues"])
    finally:
        tmp.cleanup()


def test_environment_without_required_lock_is_degraded_but_usable_for_exploration():
    tmp, root = make_root()
    try:
        status = EnvironmentRegistry(root).validate_environment(
            "r_seurat_v5",
            language="R",
            require_lock=False,
            require_packages=False,
        )

        assert status["status"] == "pass"
        assert status["reproducibility_grade"] == "degraded"
    finally:
        tmp.cleanup()


def test_environment_cli_validate_env_reports_module_environment():
    env = dict(os.environ)
    env["PYTHONPATH"] = str(REPO_ROOT / "src") + os.pathsep + env.get("PYTHONPATH", "")
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "paper_workflow.cli.main",
            "validate-env",
            "--module",
            "single_cell.seurat_pbmc3k_basic.v1",
            "--require-lock",
            "--skip-packages",
            "--json",
        ],
        cwd=str(REPO_ROOT),
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )

    assert completed.returncode == 0
    payload = yaml.safe_load(completed.stdout)
    assert payload["env_id"] == "r_seurat_v5"
    assert payload["environment"]["status"] == "blocked"


def test_data_registry_validates_tutorial_fixture_and_file_hashes():
    with tempfile.TemporaryDirectory() as tmp:
        paper = Path(tmp) / "papers" / "test_paper"
        data_dir = paper / "data" / "raw" / "pbmc3k"
        registry_dir = paper / "data" / "data_registry"
        data_dir.mkdir(parents=True)
        registry_dir.mkdir(parents=True)
        (data_dir / "matrix.mtx").write_text("%%MatrixMarket matrix coordinate integer general\n", encoding="utf-8")
        (registry_dir / "datasets.yaml").write_text(
            yaml.safe_dump(
                {
                    "schema_version": "data_registry.v1",
                    "datasets": [
                        {
                            "dataset_id": "sc_pbmc3k",
                            "modality": "single_cell",
                            "role": "tutorial_fixture",
                            "path": "data/raw/pbmc3k",
                            "format": "10x_mtx",
                            "immutable": True,
                            "source": {"type": "public_tutorial", "origin_url": "https://satijalab.org/seurat/"},
                            "statistical_unit": {"primary": "cell", "inference_allowed_at": ["cell_visualization"]},
                            "sample_mapping": {"status": "not_required_for_tutorial"},
                            "batch_variables": [],
                        }
                    ],
                },
                sort_keys=False,
            ),
            encoding="utf-8",
        )
        graph = AnalysisGraph(
            run_id="pbmc3k_demo_20260708_v1",
            research_question="PBMC3K tutorial workflow",
            primary_objective="workflow test",
            statistical_unit="cell",
            nodes=[],
        )

        registry = DataRegistry(paper)
        status = registry.validate_for_execution(graph)
        rows = registry.write_file_manifest()

        assert status["status"] == "pass"
        assert status["evidence_grade"] == "workflow_test"
        assert rows[0]["sha256"]
        assert (registry.file_manifest_path).exists()


def test_data_registry_blocks_group_inference_without_sample_mapping():
    with tempfile.TemporaryDirectory() as tmp:
        paper = Path(tmp) / "papers" / "test_paper"
        data_dir = paper / "data" / "raw" / "counts"
        registry_dir = paper / "data" / "data_registry"
        data_dir.mkdir(parents=True)
        registry_dir.mkdir(parents=True)
        (data_dir / "counts.csv").write_text("gene,A,B\nX,1,2\n", encoding="utf-8")
        (registry_dir / "datasets.yaml").write_text(
            yaml.safe_dump(
                {
                    "schema_version": "data_registry.v1",
                    "datasets": [
                        {
                            "dataset_id": "bulk_counts",
                            "modality": "bulk_rnaseq",
                            "role": "discovery",
                            "path": "data/raw/counts",
                            "format": "csv",
                            "immutable": True,
                            "sample_mapping": {"status": "missing"},
                        }
                    ],
                },
                sort_keys=False,
            ),
            encoding="utf-8",
        )
        graph = AnalysisGraph(
            run_id="bulk_de_20260709_v1",
            research_question="case vs control differential expression",
            primary_objective="group inference by condition",
            statistical_unit="sample",
            nodes=[],
        )

        status = DataRegistry(paper).validate_for_execution(graph)

        assert status["status"] == "blocked"
        assert any("sample mapping missing" in issue for issue in status["issues"])
