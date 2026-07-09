from __future__ import annotations

import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from paper_workflow.target_task.orchestrator import TargetTaskOrchestrator


REPO_ROOT = Path(__file__).resolve().parent.parent


def copy_target_fixture(tmp_path: Path) -> Path:
    root = tmp_path / "repo"
    shutil.copytree(REPO_ROOT / "code_library", root / "code_library")
    shutil.copytree(REPO_ROOT / "targets", root / "targets")
    shutil.copytree(REPO_ROOT / "config", root / "config")
    return root


def test_target_task_plan_and_dry_run_package_fail_closed(tmp_path: Path):
    root = copy_target_fixture(tmp_path)
    target = root / "targets" / "examples" / "pbmc3k_t_subcluster_v5.yaml"
    orchestrator = TargetTaskOrchestrator(root)

    validation = orchestrator.validate(target, require_packages=False)
    plan = orchestrator.plan(target)
    run = orchestrator.run(target, approved=False, execute=False)
    evaluation = orchestrator.evaluate(target)
    package = orchestrator.package(target)

    run_dir = Path(plan["run_dir"])
    assert validation["valid"] is True
    assert (run_dir / "analysis_graph.yaml").exists()
    assert (run_dir / "strategy_decision.yaml").exists()
    assert (run_dir / "qc" / "fail_closed_decision.yaml").exists()
    assert (run_dir / "manuscript" / "results_skeleton.md").exists()
    assert run["status"] != "pass" or evaluation["bioinformatics_quality_status"] == "pass"
    assert package["scientific_claim_permission"] in {"exploratory_only", "no_claim_until_fail_closed_passes"}
