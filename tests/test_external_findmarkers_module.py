from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest
import yaml


REPO_ROOT = Path(__file__).resolve().parent.parent


def test_findmarkers_module_contract_files_exist_and_parse():
    module_dir = REPO_ROOT / "code_library" / "modules" / "single_cell" / "seurat_findmarkers_group_de"
    for rel in [
        "main.R",
        "R/functions.R",
        "module.yaml",
        "env_profile.yaml",
        "README.md",
        "PROVENANCE.md",
        "tests/toy_input_manifest.yaml",
        "tests/expected_outputs.yaml",
    ]:
        assert (module_dir / rel).exists()
    expected = yaml.safe_load((module_dir / "tests" / "expected_outputs.yaml").read_text(encoding="utf-8"))
    assert "tables/findmarkers_results.csv" in expected["required_outputs"]


def test_findmarkers_module_dry_run_outputs(tmp_path: Path):
    rscript = shutil.which("Rscript")
    if not rscript:
        pytest.skip("Rscript is not available")
    script = REPO_ROOT / "code_library" / "modules" / "single_cell" / "seurat_findmarkers_group_de" / "main.R"
    completed = subprocess.run(
        [rscript, str(script), "--dry-run", "--out", str(tmp_path), "--run-id", "findmarkers_dry_run"],
        cwd=str(REPO_ROOT),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        timeout=60,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert (tmp_path / "tables" / "findmarkers_results.csv").exists()
    assert (tmp_path / "qc" / "group_size_sample_mapping.csv").exists()
    assert "Cell-level marker" in (tmp_path / "table_source_map.yaml").read_text(encoding="utf-8")
