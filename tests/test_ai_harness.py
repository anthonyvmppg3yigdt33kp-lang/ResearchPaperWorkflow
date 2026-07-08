from __future__ import annotations

import tempfile
from pathlib import Path

from paper_workflow.ai_harness import AIWorkflowHarness
from paper_workflow.api import WorkflowAPI


def _root(tmpdir: str) -> Path:
    root = Path(tmpdir)
    (root / "AGENTS.md").write_text("# Test Project\n", encoding="utf-8")
    return root


def test_validate_contract_checks_ai_harness_routes():
    repo_root = Path(__file__).resolve().parent.parent
    result = WorkflowAPI(repo_root).validate_contract()

    assert result["valid"], result
    assert result["counts"]["ai_harness_routes"] == 5
    assert result["counts"]["ai_harness_commands"] == 20


def test_ai_harness_dry_run_routes_static_check_without_state_change():
    repo_root = Path(__file__).resolve().parent.parent
    harness = AIWorkflowHarness(repo_root)

    result = harness.handle_request("静态检查一下全局配置和 harness 接线", dry_run=True)

    assert result["intent"] == "validate_contract"
    assert result["status"] == "planned"
    assert not result["executed"]
    assert "validate-contract" in result["plan"]["equivalent_cli_command"]
    assert "--json" in result["plan"]["model_harness_command"]


def test_ai_harness_routes_five_user_situations():
    with tempfile.TemporaryDirectory() as tmpdir:
        root = _root(tmpdir)
        paper_dir = root / "papers" / "paper_demo"
        paper_dir.mkdir(parents=True)
        (paper_dir / "project_passport.yaml").write_text(
            "paper_id: paper_demo\npipeline_state: clean\nidea: demo\n",
            encoding="utf-8",
        )
        harness = AIWorkflowHarness(root)

        assert harness.handle_request("我还没起步，请先帮我建立课题工作流", dry_run=True)["intent"] == "create_project"
        assert harness.handle_request("我已有方向，需要选题调研和文献空白分析", paper_id="paper_demo", dry_run=True)["intent"] == "run_pipeline"
        assert harness.handle_request("I have a direction and need topic research", paper_id="paper_demo", dry_run=True)["intent"] == "run_pipeline"
        assert harness.handle_request("我已有选题和数据，请进入 SAP、数据审计和分析计划", paper_id="paper_demo", dry_run=True)["intent"] == "run_pipeline"
        assert harness.handle_request("我已有部分进展，需要把散乱材料接入工作流并检查缺口", paper_id="paper_demo", dry_run=True)["intent"] == "validate_workflow"
        assert harness.handle_request("我已有多数材料，需要论文撰写和投稿包整理", paper_id="paper_demo", dry_run=True)["intent"] == "run_pipeline"


def test_ai_harness_creates_project_from_natural_language():
    with tempfile.TemporaryDirectory() as tmpdir:
        root = _root(tmpdir)
        harness = AIWorkflowHarness(root)

        result = harness.handle_request(
            "我还没有起步，想做肾癌糖尿病相关的单细胞和空间转录组课题，目标期刊 Genome Biology，4 周内完成。",
        )

        assert result["intent"] == "create_project"
        assert result["status"] == "ok"
        assert result["executed"]
        assert result["result"]["paper_id"]
        assert (root / "papers" / result["result"]["paper_id"] / "project_passport.yaml").exists()
        assert "项目已创建" in result["user_facing_reply"]


def test_ai_harness_runs_one_pipeline_stage_per_model_turn():
    with tempfile.TemporaryDirectory() as tmpdir:
        root = _root(tmpdir)
        harness = AIWorkflowHarness(root)
        created = harness.handle_request(
            "创建一个临床生信课题：single-cell biomarkers for kidney disease，目标期刊 Genome Biology",
            field="bioinformatics, clinical, single-cell",
            journal="Genome Biology",
        )
        paper_id = created["result"]["paper_id"]

        run = harness.handle_request(
            "请继续推进工作流一步",
            paper_id=paper_id,
            max_stages=1,
        )

        assert run["intent"] == "run_pipeline"
        assert run["status"] == "ok"
        assert "--paper" in run["plan"]["model_harness_command"]
        assert "--max-stages" in run["plan"]["model_harness_command"]
        stages = [event["stage"] for event in run["result"]["events"] if event["event"] == "stage"]
        assert stages == ["target_journal"]
        assert run["result"]["events"][-1] == {"event": "max_stages_reached", "max_stages": 1}
