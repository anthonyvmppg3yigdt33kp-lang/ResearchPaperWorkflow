from __future__ import annotations

import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from paper_workflow.target_task.schema import validate_target_task


REPO_ROOT = Path(__file__).resolve().parent.parent


def test_pbmc3k_target_task_schema_is_valid():
    target = yaml.safe_load((REPO_ROOT / "targets" / "examples" / "pbmc3k_t_subcluster_v5.yaml").read_text(encoding="utf-8"))
    result = validate_target_task(target)

    assert result["valid"] is True
    assert result["required_envs"] == ["r_seurat_v5"]
    assert "subcluster_reanalysis" in result["resolved_steps"]


def test_target_task_missing_claim_boundary_is_invalid():
    target = yaml.safe_load((REPO_ROOT / "targets" / "examples" / "pbmc3k_t_subcluster_v5.yaml").read_text(encoding="utf-8"))
    target.pop("claim_boundary")

    result = validate_target_task(target)

    assert result["valid"] is False
    assert "missing top-level field: claim_boundary" in result["issues"]
