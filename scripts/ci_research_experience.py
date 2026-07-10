"""Smoke-test the researcher intent layer without running biological analysis."""

from __future__ import annotations

import argparse
import json
import shutil
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from paper_workflow.ai_harness import AIWorkflowHarness  # noqa: E402
from paper_workflow.research_intent import ResearchWorkflowOrchestrator  # noqa: E402


REPO_ROOT = Path(__file__).resolve().parent.parent


def run(root: Path) -> dict[str, object]:
    for name in ("code_library", "config", "local_experience", "intents", "targets"):
        shutil.copytree(REPO_ROOT / name, root / name, dirs_exist_ok=True)
    (root / "AGENTS.md").write_text("# CI research experience root\n", encoding="utf-8")
    intent = root / "intents" / "examples" / "pbmc3k_t_subcluster_intent.yaml"
    orchestrator = ResearchWorkflowOrchestrator(root)
    validation = orchestrator.validate(intent)
    started = orchestrator.start(intent)
    harness = AIWorkflowHarness(root).handle_request(f'科研启动 "{intent}"', dry_run=True)
    plan = started.get("research_plan") or {}
    expected = [
        Path(str((plan.get("artifacts") or {}).get("scientific_assessment", ""))),
        Path(str((plan.get("artifacts") or {}).get("strategy_simulation", ""))),
        Path(str((plan.get("artifacts") or {}).get("figure_plan_markdown", ""))),
        Path(str(plan.get("target_task", ""))),
        Path(str((started.get("dashboard") or {}).get("dashboard_markdown", ""))),
    ]
    missing = [str(path) for path in expected if not path.exists()]
    status = "pass" if validation.get("valid") and started.get("status") == "planned" and harness.get("intent") == "research_intent" and not missing else "fail"
    return {
        "schema_version": "research_experience_smoke.v1",
        "status": status,
        "validation": validation,
        "selected_modules": plan.get("selected_modules", []),
        "dashboard_status": (started.get("dashboard") or {}).get("current_status"),
        "harness_intent": harness.get("intent"),
        "harness_mode": (harness.get("route") or {}).get("mode"),
        "missing": missing,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-root", default="")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    if args.output_root:
        root = Path(args.output_root).resolve()
        root.mkdir(parents=True, exist_ok=True)
        result = run(root)
    else:
        with tempfile.TemporaryDirectory() as tmpdir:
            result = run(Path(tmpdir))
    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(f"Research experience smoke: {result['status']}")
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
