from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from paper_workflow.manuscript import build_claim_boundary_ledger, build_figure_storyline, build_methods_draft, build_results_skeleton


def test_results_skeleton_refuses_conclusions_when_fail_closed_not_pass(tmp_path: Path):
    target = {
        "target_id": "pbmc3k_t_subcluster_20260709_v1",
        "title": "PBMC3K validation",
        "evidence_grade": "official_tutorial_workflow_test",
        "claim_boundary": "tutorial only",
        "data": {"dataset_id": "seurat_official_pbmc3k"},
        "analysis_goal": {"forbidden_claims": ["disease mechanism"]},
    }
    evaluation = {"status": "needs_fix"}
    rows = [{"kind": "figure", "id": "f1", "method": "UMAP", "claim_boundary": "tutorial only"}]

    assert "No conclusion paragraph" in build_results_skeleton(target, rows, evaluation)
    assert "Claim boundary: tutorial only" in build_methods_draft(target, tmp_path, evaluation)
    assert "Boundary: tutorial only" in build_figure_storyline(target, rows, evaluation)
    assert build_claim_boundary_ledger(target, evaluation)["scientific_claim_permission"] == "no_claim_until_fail_closed_passes"
