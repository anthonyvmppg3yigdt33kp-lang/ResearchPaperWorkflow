"""Python TargetTask CI smoke for the PBMC3K v5 example."""

from __future__ import annotations

import argparse
import json
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from paper_workflow.target_task.orchestrator import TargetTaskOrchestrator  # noqa: E402


def run_smoke(repo_root: Path, output_root: Path | None = None) -> dict[str, Any]:
    temp_ctx = tempfile.TemporaryDirectory() if output_root is None else None
    root = output_root or Path(temp_ctx.name)
    try:
        if output_root and root.exists():
            shutil.rmtree(root)
        if root != repo_root:
            shutil.copytree(repo_root / "code_library", root / "code_library")
            shutil.copytree(repo_root / "config", root / "config")
            shutil.copytree(repo_root / "targets", root / "targets")
            shutil.copytree(repo_root / "src", root / "src")
        orchestrator = TargetTaskOrchestrator(root)
        target = root / "targets" / "examples" / "pbmc3k_t_subcluster_v5.yaml"
        validation = orchestrator.validate(target, require_packages=False)
        plan = orchestrator.plan(target)
        run = orchestrator.run(target, approved=False, execute=False)
        evaluation = orchestrator.evaluate(target)
        package = orchestrator.package(target)
        required = [
            Path(plan["run_dir"]) / "analysis_graph.yaml",
            Path(plan["run_dir"]) / "target_task_resolved.yaml",
            Path(plan["run_dir"]) / "strategy_decision.yaml",
            Path(plan["run_dir"]) / "qc" / "fail_closed_decision.yaml",
            Path(plan["run_dir"]) / "manuscript" / "results_skeleton.md",
        ]
        missing = [str(path) for path in required if not path.exists()]
        fake_pass = evaluation.get("status") == "pass" and evaluation.get("bioinformatics_quality_status") != "pass"
        return {
            "schema_version": "pbmc3k_target_task_ci.v1",
            "status": "pass" if validation["valid"] and not missing and not fake_pass else "fail",
            "validation_valid": validation["valid"],
            "plan": plan,
            "run_status": run.get("status"),
            "evaluation_status": evaluation.get("status"),
            "package_status": package.get("final_status"),
            "missing": missing,
            "fake_pass": fake_pass,
        }
    finally:
        if temp_ctx is not None:
            temp_ctx.cleanup()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--output-root", default="")
    args = parser.parse_args()
    repo_root = Path(__file__).resolve().parent.parent
    result = run_smoke(repo_root, Path(args.output_root).resolve() if args.output_root else None)
    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(f"PBMC3K TargetTask CI: {result['status']}")
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
