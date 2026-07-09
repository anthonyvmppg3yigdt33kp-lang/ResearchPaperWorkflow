from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest
import yaml


REPO_ROOT = Path(__file__).resolve().parent.parent


def test_seurat_subcluster_module_contract_is_registered():
    module = yaml.safe_load((REPO_ROOT / "code_library" / "modules" / "single_cell" / "seurat_subcluster_programs" / "module.yaml").read_text(encoding="utf-8"))

    assert module["id"] == "single_cell.seurat_subcluster_programs.v1"
    assert module["production_capability_grade"] == "production_capable_real_wrapper"
    assert module["execution_evidence_level"] == "official_tutorial_validated"
    assert "claim_boundary" in module


def test_seurat_subcluster_wrapper_dry_run_writes_required_artifacts(tmp_path: Path):
    rscript = shutil.which("Rscript")
    if not rscript:
        pytest.skip("Rscript is not available")
    script = REPO_ROOT / "code_library" / "modules" / "single_cell" / "seurat_subcluster_programs" / "main.R"
    out = tmp_path / "subcluster"
    result = subprocess.run(
        [rscript, str(script), "--out", str(out), "--run-id", "subcluster_smoke_20260709_v1", "--dry-run"],
        cwd=str(REPO_ROOT),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    for rel in [
        "tables/subcluster_cell_counts.csv",
        "tables/subcluster_markers.csv",
        "tables/program_score_summary.csv",
        "figure_source_map.yaml",
        "table_source_map.yaml",
        "logs/sessionInfo.txt",
    ]:
        assert (out / rel).exists(), rel
