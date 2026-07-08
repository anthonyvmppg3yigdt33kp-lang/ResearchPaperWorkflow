"""CI smoke for method-asset graph planning and dry-run execution."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any


RUN_ID = "pbmc3k_demo_20260708_v1"


def run_cmd(cmd: list[str], cwd: Path, env: dict[str, str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        cwd=str(cwd),
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def copy_method_assets(repo_root: Path, root: Path) -> None:
    (root / "AGENTS.md").write_text("# graph dry-run CI\n", encoding="utf-8")
    (root / "src").mkdir(parents=True, exist_ok=True)
    paper = root / "papers" / "test_paper"
    paper.mkdir(parents=True, exist_ok=True)
    (paper / "project_passport.yaml").write_text(
        "paper_id: test_paper\npipeline_state: stale_stages\n",
        encoding="utf-8",
    )
    (paper / "data" / "raw" / "pbmc3k").mkdir(parents=True, exist_ok=True)
    (root / "code_library").mkdir(exist_ok=True)
    shutil.copy2(repo_root / "code_library" / "module_registry.yaml", root / "code_library" / "module_registry.yaml")
    shutil.copy2(repo_root / "code_library" / "environment_registry.yaml", root / "code_library" / "environment_registry.yaml")
    shutil.copytree(repo_root / "code_library" / "modules", root / "code_library" / "modules", dirs_exist_ok=True)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run graph dry-run CI smoke")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--output-root", help="Optional persistent root for CI artifacts")
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parent.parent
    env = dict(os.environ)
    env["PYTHONPATH"] = str(repo_root / "src") + os.pathsep + env.get("PYTHONPATH", "")
    temp_ctx = tempfile.TemporaryDirectory() if not args.output_root else None
    try:
        root = Path(args.output_root) if args.output_root else Path(temp_ctx.name)
        if args.output_root and root.exists():
            shutil.rmtree(root)
        root.mkdir(parents=True, exist_ok=True)
        copy_method_assets(repo_root, root)
        commands = [
            [
                sys.executable, "-m", "paper_workflow.cli.main",
                "list-capabilities",
                "--question", "Seurat PBMC3K single-cell QC and UMAP",
                "--modality", "scrna",
                "--json",
            ],
            [
                sys.executable, "-m", "paper_workflow.cli.main",
                "plan-analysis",
                "--paper", "test_paper",
                "--run-id", RUN_ID,
                "--goal", "Seurat PBMC3K single-cell QC and UMAP graph dry-run.",
                "--modality", "scrna",
                "--input", "data/raw/pbmc3k",
                "--from-code-library",
                "--set-current",
            ],
            [
                sys.executable, "-m", "paper_workflow.cli.main",
                "run-analysis",
                "--paper", "test_paper",
                "--run-id", RUN_ID,
            ],
            [
                sys.executable, "-m", "paper_workflow.cli.main",
                "evaluate-run",
                "--paper", "test_paper",
                "--run-id", RUN_ID,
                "--write-report",
                "--json",
            ],
        ]
        outputs: list[dict[str, Any]] = []
        for cmd in commands:
            completed = run_cmd(cmd, root, env)
            outputs.append({
                "command": " ".join(cmd),
                "returncode": completed.returncode,
                "stdout": completed.stdout,
                "stderr": completed.stderr,
            })
            if completed.returncode != 0:
                print(json.dumps({"status": "fail", "outputs": outputs}, indent=2, ensure_ascii=False))
                return completed.returncode

        run_dir = root / "papers" / "test_paper" / "results" / "runs" / RUN_ID
        required = [
            run_dir / "run_manifest.yaml",
            run_dir / "analysis_graph.yaml",
            run_dir / "method_selection_report.md",
            run_dir / "evaluation_report.yaml",
            run_dir / "figure_source_map.yaml",
            run_dir / "table_source_map.yaml",
        ]
        missing = [str(path) for path in required if not path.exists()]
        result = {
            "status": "pass" if not missing else "fail",
            "run_dir": str(run_dir),
            "missing": missing,
            "outputs": outputs,
        }
        print(json.dumps(result, indent=2, ensure_ascii=False) if args.json else f"Graph dry-run status: {result['status']}")
        return 0 if result["status"] == "pass" else 1
    finally:
        if temp_ctx is not None:
            temp_ctx.cleanup()


if __name__ == "__main__":
    sys.exit(main())
