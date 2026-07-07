from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import yaml

from paper_workflow.ai_harness import AIWorkflowHarness
from paper_workflow.routing.mode_resolver import ModeResolver
from paper_workflow.routing.tool_doctor import ToolDoctor


REPO_ROOT = Path(__file__).resolve().parent.parent


def test_mode_resolver_maps_vague_request_to_quick_status():
    route = ModeResolver(REPO_ROOT).resolve_route("全面扫描一下项目，先不要改文件")

    assert route["mode"] == "exploration_mode"
    assert route["profile"] == "quick_status"
    assert route["active_stages"] == []
    assert "run_analysis" in route["deferred_stages"]


def test_mode_resolver_maps_new_analysis_to_design_mode():
    route = ModeResolver(REPO_ROOT).resolve_route("Design a bulk RNA-seq differential expression analysis")

    assert route["mode"] == "analysis_design_mode"
    assert route["profile"] == "analysis_design"
    assert route["analysis_allowed"] is False
    assert "run analysis code" in route["forbidden_actions"]


def test_mode_resolver_maps_approved_bounded_analysis_to_execution_mode():
    route = ModeResolver(REPO_ROOT).resolve_route("Approved bounded command: run analysis for bulk_de_20260707_v1")

    assert route["mode"] == "execution_mode"
    assert route["execution_allowed"] is True
    assert route["analysis_allowed"] is True
    assert route["profile"] == "exploratory_omics"


def test_exploratory_journal_policy_defers_final_target():
    route = ModeResolver(REPO_ROOT).resolve_route("探索性单细胞和空间转录组项目，先评估方向")

    policy = route["journal_policy"]
    assert policy["candidate_journal_class_only"] is True
    assert policy["final_target_journal_required_now"] is False
    assert policy["defer_final_target_journal_to"] == ["evidence_maturation", "submission_closeout"]


def test_explicit_target_journal_is_still_allowed_early():
    route = ModeResolver(REPO_ROOT).resolve_route(
        "Create a project for kidney single-cell biomarkers, target journal Genome Biology"
    )

    policy = route["journal_policy"]
    assert policy["explicit_target_journal"] == "Genome Biology"
    assert policy["final_target_journal_allowed_now"] is True
    assert policy["final_target_journal_required_now"] is True


def test_ai_harness_fuzzy_exploration_does_not_activate_pipeline_or_project_creation(tmp_path):
    root = tmp_path
    (root / "AGENTS.md").write_text("# Test Project\n", encoding="utf-8")
    (root / "config").mkdir()
    (root / "config" / "workflow_modes.yaml").write_text(
        (REPO_ROOT / "config" / "workflow_modes.yaml").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    harness = AIWorkflowHarness(root)

    result = harness.handle_request("全面优化和扫描我的项目，先只读定位问题", dry_run=True)

    assert result["route"]["mode"] == "exploration_mode"
    assert result["route"]["profile"] == "quick_status"
    assert result["intent"] == "list_papers"
    assert result["intent"] not in {"run_pipeline", "create_project"}


def test_route_task_cli_returns_mode_profile_and_deferred_stages():
    env = dict(os.environ)
    env["PYTHONPATH"] = str(REPO_ROOT / "src") + os.pathsep + env.get("PYTHONPATH", "")
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "paper_workflow.cli.main",
            "route-task",
            "--request",
            "Design a scRNA-seq analysis plan",
            "--json",
        ],
        cwd=str(REPO_ROOT),
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )

    assert completed.returncode == 0, completed.stdout + completed.stderr
    payload = json.loads(completed.stdout)
    assert payload["mode"] == "analysis_design_mode"
    assert payload["profile"] == "analysis_design"
    assert "run_analysis" in payload["deferred_stages"]


def test_tool_doctor_reports_fast_context_fallback_and_repo_agents():
    report = ToolDoctor(REPO_ROOT).run()

    assert report["status"] in {"pass", "degraded"}
    assert report["tools"]["fast_context"]["mcp_tool"] == "mcp__fast-context__fast_context_search"
    assert "rg --line-number" in report["fallback_policy"]["semantic_code_search"][1]
    assert report["skills"]["missing_bundled_sources"] == []
    assert report["skills"]["missing_agent_skill_mirrors"] == []
    assert report["agents"]["missing_agent_files"] == []


def test_workflow_contract_declares_run_scoped_manifest_resolver():
    contract = yaml.safe_load((REPO_ROOT / "workflow_contract.yaml").read_text(encoding="utf-8"))
    run_analysis = contract["stages"]["run_analysis"]

    assert run_analysis["required_outputs"] == ["results/run_manifest.yaml"]
    assert run_analysis["dynamic_required_outputs"]["active_run_pointer"] == "results/current_run.yaml"
    assert "results/runs/<active_run_id>/run_manifest.yaml" in run_analysis["dynamic_required_outputs"]["run_scoped_outputs"]
    assert contract["journal_timing_policy"]["exploratory_project"]["early_field"] == "candidate_journal_class"
