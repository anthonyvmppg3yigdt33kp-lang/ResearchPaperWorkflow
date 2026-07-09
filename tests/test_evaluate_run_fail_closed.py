from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from paper_workflow.outputs.result_run_manager import ResultRunManager


def test_evaluate_run_writes_fail_closed_decision_for_incomplete_run(tmp_path: Path):
    paper = tmp_path / "papers" / "fail_closed"
    paper.mkdir(parents=True)
    (paper / "project_passport.yaml").write_text("paper_id: fail_closed\npipeline_state: test\n", encoding="utf-8")
    manager = ResultRunManager(paper)
    manager.create_run("fail_closed_20260709_v1")

    evaluation = manager.evaluate_run("fail_closed_20260709_v1", write_report=True).to_dict()
    run_dir = manager.run_path("fail_closed_20260709_v1")

    assert evaluation["status"] == "needs_fix"
    assert evaluation["evaluation_status"]["final_status"] == "needs_fix"
    assert evaluation["fail_closed_reasons"]
    assert (run_dir / "qc" / "fail_closed_decision.yaml").exists()
