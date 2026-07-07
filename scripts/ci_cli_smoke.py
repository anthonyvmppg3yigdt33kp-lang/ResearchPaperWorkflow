"""CLI smoke test used by CI and local release preflight."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any


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


def write_fixture(root: Path) -> None:
    paper = root / "papers" / "test_paper"
    data = paper / "data" / "pilot"
    data.mkdir(parents=True, exist_ok=True)
    (root / "AGENTS.md").write_text("# CI smoke\n", encoding="utf-8")
    (paper / "project_passport.yaml").write_text(
        "paper_id: test_paper\npipeline_state: stale_stages\n",
        encoding="utf-8",
    )
    (data / "counts.csv").write_text(
        "gene,A1,A2,A3,B1,B2,B3\n"
        "CXCL13,120,130,125,10,12,9\n"
        "MS4A1,95,90,100,30,28,35\n"
        "XBP1,8,9,7,100,105,110\n"
        "PRDM1,12,11,10,90,95,93\n"
        "ACTB,50,52,48,51,49,50\n",
        encoding="utf-8-sig",
    )
    (data / "metadata.csv").write_text(
        "sample_id,condition,batch\n"
        "A1,IgG4_ROD,b1\n"
        "A2,IgG4_ROD,b1\n"
        "A3,IgG4_ROD,b2\n"
        "B1,MALT_L,b1\n"
        "B2,MALT_L,b2\n"
        "B3,MALT_L,b2\n",
        encoding="utf-8-sig",
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Run ResearchPaperWorkflow CLI smoke")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--keep-temp", action="store_true")
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parent.parent
    env = dict(os.environ)
    env["PYTHONPATH"] = str(repo_root / "src") + os.pathsep + env.get("PYTHONPATH", "")

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        write_fixture(root)
        commands = [
            [
                sys.executable, "-m", "paper_workflow.cli.main",
                "plan-analysis",
                "--paper", "test_paper",
                "--run-id", "bulk_de_20260707_v1",
                "--goal", "Pilot bulk RNA-seq execution test.",
                "--modality", "bulk_rnaseq",
                "--input", "data/pilot/counts.csv",
                "--input", "data/pilot/metadata.csv",
                "--primary-contrast", "IgG4_ROD vs MALT_L",
                "--execution-backend", "python_builtin_pilot",
                "--set-current",
            ],
            [
                sys.executable, "-m", "paper_workflow.cli.main",
                "run-analysis",
                "--paper", "test_paper",
                "--run-id", "bulk_de_20260707_v1",
                "--execute",
                "--approved",
                "--backend", "python_builtin_pilot",
                "--set-current",
            ],
            [
                sys.executable, "-m", "paper_workflow.cli.main",
                "evaluate-run",
                "--paper", "test_paper",
                "--run-id", "bulk_de_20260707_v1",
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
                if args.json:
                    print(json.dumps({"status": "fail", "outputs": outputs}, indent=2, ensure_ascii=False))
                else:
                    print(completed.stdout)
                    print(completed.stderr, file=sys.stderr)
                return completed.returncode

        run_dir = root / "papers" / "test_paper" / "results" / "runs" / "bulk_de_20260707_v1"
        required = [
            run_dir / "run_manifest.yaml",
            run_dir / "evaluation_report.yaml",
            run_dir / "tables" / "differential_expression_pilot.csv",
            run_dir / "figures" / "volcano_plot.svg",
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
        if args.json:
            print(json.dumps(result, indent=2, ensure_ascii=False))
        else:
            print(f"CLI smoke status: {result['status']}")
            print(f"Run dir: {run_dir}")
            if missing:
                print("Missing:")
                for item in missing:
                    print(f"  - {item}")
        if args.keep_temp:
            print(f"Temporary root retained until process exit: {root}")
        return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    sys.exit(main())

