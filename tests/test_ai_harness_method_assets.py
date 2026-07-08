from __future__ import annotations

import shutil
import tempfile
from pathlib import Path

from paper_workflow.ai_harness import AIWorkflowHarness


REPO_ROOT = Path(__file__).resolve().parent.parent


def _method_asset_root(tmpdir: str) -> Path:
    root = Path(tmpdir)
    (root / "AGENTS.md").write_text("# Test Project\n", encoding="utf-8")
    paper_dir = root / "papers" / "paper_demo"
    paper_dir.mkdir(parents=True)
    (paper_dir / "project_passport.yaml").write_text(
        "paper_id: paper_demo\npipeline_state: clean\nidea: demo\n",
        encoding="utf-8",
    )
    shutil.copytree(REPO_ROOT / "code_library", root / "code_library")
    shutil.copytree(REPO_ROOT / "config", root / "config")
    return root


def test_ai_harness_plans_code_library_analysis_without_execution():
    with tempfile.TemporaryDirectory() as tmpdir:
        root = _method_asset_root(tmpdir)
        harness = AIWorkflowHarness(root)

        result = harness.handle_request(
            "根据我的 code library 给这个 paper 规划一个单细胞分析方案，不要执行",
            paper_id="paper_demo",
            dry_run=True,
        )

        assert result["intent"] == "plan_analysis"
        assert result["route"]["mode"] == "analysis_design_mode"
        assert not result["executed"]
        assert result["status"] == "planned"
        command = result["plan"]["equivalent_cli_command"]
        assert "plan-analysis" in command
        assert "--from-code-library" in command
        assert "--modality \"scrna\"" in command


def test_ai_harness_blocks_analysis_execution_without_explicit_approval():
    with tempfile.TemporaryDirectory() as tmpdir:
        root = _method_asset_root(tmpdir)
        harness = AIWorkflowHarness(root)

        result = harness.handle_request(
            "执行这个分析 run_id method_asset_20260709_v1",
            paper_id="paper_demo",
            dry_run=True,
        )

        assert result["intent"] == "run_analysis"
        assert result["status"] == "needs_input"
        assert "explicit_user_approval" in result["result"]["required"]


def test_ai_harness_lists_method_asset_capabilities():
    with tempfile.TemporaryDirectory() as tmpdir:
        root = _method_asset_root(tmpdir)
        harness = AIWorkflowHarness(root)

        result = harness.handle_request(
            "有哪些分析可用，尤其是 PBMC 单细胞 Seurat?",
            paper_id="paper_demo",
        )

        assert result["intent"] == "list_capabilities"
        assert result["status"] == "ok"
        assert result["result"]["selected_modules"]
        assert result["result"]["selected_modules"][0]["id"] == "single_cell.seurat_pbmc3k_basic.v1"
