from __future__ import annotations

import shutil
from pathlib import Path

from paper_workflow.ai_harness import AIWorkflowHarness


REPO_ROOT = Path(__file__).resolve().parent.parent


def copy_target_fixture(tmp_path: Path) -> tuple[Path, Path]:
    # GitHub Actions paths contain "runner"; embedded path text is not a command.
    root = tmp_path / "runner" / "repo"
    shutil.copytree(REPO_ROOT / "code_library", root / "code_library")
    shutil.copytree(REPO_ROOT / "targets", root / "targets")
    shutil.copytree(REPO_ROOT / "config", root / "config")
    shutil.copytree(REPO_ROOT / "local_experience", root / "local_experience")
    shutil.copytree(REPO_ROOT / "intents", root / "intents")
    (root / "AGENTS.md").write_text("# test\n", encoding="utf-8")
    return root, root / "targets" / "examples" / "pbmc3k_t_subcluster_v5.yaml"


def test_ai_harness_routes_and_validates_target_task(tmp_path: Path):
    root, target = copy_target_fixture(tmp_path)
    harness = AIWorkflowHarness(root)

    planned = harness.handle_request(f'目标任务 validate "{target}"', dry_run=True)
    executed = harness.handle_request(f'目标任务 validate "{target}"')

    assert planned["intent"] == "target_task"
    assert planned["route"]["mode"] == "exploration_mode"
    assert 'target "validate"' in planned["plan"]["equivalent_cli_command"]
    assert executed["executed"] is True
    assert executed["status"] == "ok"
    assert executed["result"]["valid"] is True


def test_ai_harness_blocks_target_real_execution_without_approval(tmp_path: Path):
    root, target = copy_target_fixture(tmp_path)
    harness = AIWorkflowHarness(root)

    result = harness.handle_request(f'执行目标任务 "{target}" --execute')

    assert result["intent"] == "target_task"
    assert result["route"]["mode"] == "execution_mode"
    assert result["status"] == "needs_input"
    assert "explicit_user_approval" in result["result"]["required"]


def test_ai_harness_routes_research_intent_to_scientific_planner(tmp_path: Path):
    root, _ = copy_target_fixture(tmp_path)
    intent = root / "intents" / "examples" / "pbmc3k_t_subcluster_intent.yaml"
    harness = AIWorkflowHarness(root)

    planned = harness.handle_request(f'科研启动 "{intent}"', dry_run=True)
    executed = harness.handle_request(f'科研启动 "{intent}"')

    assert planned["intent"] == "research_intent"
    assert planned["route"]["mode"] == "analysis_design_mode"
    assert planned["route"]["profile"] == "analysis_design"
    assert planned["route"]["output_contract"] != "chat_or_brief_only"
    assert 'research "start"' in planned["plan"]["equivalent_cli_command"]
    assert executed["status"] == "ok"
    assert executed["result"]["research_plan"]["ready_for_target_plan"] is True
