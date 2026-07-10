import json
import os
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent


def run_script(script: str) -> subprocess.CompletedProcess[str]:
    env = dict(os.environ)
    env["PYTHONPATH"] = str(REPO_ROOT / "src") + os.pathsep + env.get("PYTHONPATH", "")
    return subprocess.run(
        [sys.executable, str(REPO_ROOT / "scripts" / script), "--json"],
        cwd=str(REPO_ROOT),
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def test_ci_quality_check_passes_current_repo():
    result = run_script("ci_quality_check.py")
    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(result.stdout)
    assert payload["status"] == "pass"
    assert payload["checks"]["workflow_modes"] == []


def test_ci_module_grade_audit_passes_current_repo():
    result = run_script("ci_module_grade_audit.py")
    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(result.stdout)
    assert payload["status"] == "pass"
    assert payload["production_visible_module_count"] >= 3


def test_ci_supervision_failure_cases_pass():
    result = run_script("ci_supervision_failure_cases.py")
    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(result.stdout)
    assert payload["status"] == "pass"


def test_ci_pbmc3k_target_task_smoke_passes():
    result = run_script("ci_pbmc3k_target_task.py")
    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(result.stdout)
    assert payload["status"] == "pass"
    assert payload["fake_pass"] is False


def test_ci_research_experience_smoke_passes():
    result = run_script("ci_research_experience.py")
    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(result.stdout)
    assert payload["status"] == "pass"
    assert payload["harness_intent"] == "research_intent"
    assert payload["missing"] == []


def test_ci_performance_budget_passes():
    result = run_script("ci_performance_budget.py")
    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(result.stdout)
    assert payload["status"] == "pass"
    assert payload["score"] >= 75


def test_ci_cli_smoke_produces_bulk_pilot_package():
    result = run_script("ci_cli_smoke.py")
    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(result.stdout)
    assert payload["status"] == "pass"
    assert payload["missing"] == []


def test_ci_graph_dry_run_produces_method_asset_package():
    result = run_script("ci_graph_dry_run.py")
    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(result.stdout)
    assert payload["status"] == "pass"
    assert payload["missing"] == []
    assert payload["run_dir"].endswith("pbmc3k_demo_20260708_v1")
    assert "Status: dry_run_completed" in payload["outputs"][2]["stdout"]
    assert "\"status\": \"blocked\"" in payload["outputs"][3]["stdout"]


def test_ci_workflow_declares_production_preflight_jobs():
    workflow = (REPO_ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
    for job in [
        "python-tests:",
        "method-asset-schema:",
        "cli-smoke-bulk:",
        "cli-smoke-graph-dry-run:",
        "target-task-pbmc3k:",
        "researcher-experience:",
        "r-method-contract:",
        "security-light:",
    ]:
        assert job in workflow
    assert "ci_module_grade_audit.py --strict" in workflow
    assert "ci_supervision_failure_cases.py" in workflow
    assert "ci_performance_budget.py --json" in workflow
    assert "ci_research_experience.py" in workflow
    assert "actions/upload-artifact@v4" in workflow
