from pathlib import Path

import yaml

from paper_workflow.api import WorkflowAPI


REPO_ROOT = Path(__file__).resolve().parent.parent


def test_target_task_is_bound_to_workflow_truth_contract():
    contract = yaml.safe_load((REPO_ROOT / "workflow_contract.yaml").read_text(encoding="utf-8"))
    target = contract["target_task_contract"]

    assert target["fail_closed"] is True
    assert target["truth_bridge"]["run_analysis"]["requires_real_execution"] is True
    assert target["truth_bridge"]["write_results"]["requires_fail_closed_pass"] is True
    assert "qc/fail_closed_decision.yaml" in target["required_outputs"]
    result = WorkflowAPI(REPO_ROOT).validate_contract()
    assert result["valid"], result
    assert result["counts"]["target_task_required_outputs"] >= 12
