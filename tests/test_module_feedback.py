from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import yaml

from paper_workflow.bioinformatics.module_feedback import ModuleFeedbackManager


REPO_ROOT = Path(__file__).resolve().parent.parent


def run_cli(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    env = dict(os.environ)
    env["PYTHONPATH"] = str(REPO_ROOT / "src") + os.pathsep + env.get("PYTHONPATH", "")
    return subprocess.run(
        [sys.executable, "-m", "paper_workflow.cli.main", *args],
        cwd=str(root),
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def test_module_feedback_ledger_proposal_and_approval_do_not_mutate_registry():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        root.joinpath("AGENTS.md").write_text("# test\n", encoding="utf-8")
        root.joinpath("code_library").mkdir()
        registry = root / "code_library" / "module_registry.yaml"
        registry.write_text("modules: {}\n", encoding="utf-8")
        run_dir = root / "papers" / "paper_a" / "results" / "runs" / "demo_20260709_v1"
        run_dir.mkdir(parents=True)
        (run_dir / "inputs_manifest.yaml").write_text("inputs: []\n", encoding="utf-8")
        (run_dir / "parameters.yaml").write_text("parameters: {}\n", encoding="utf-8")
        (run_dir / "run_manifest.yaml").write_text(
            "status: dry_run_completed\n"
            "nodes:\n"
            "  - module_id: single_cell.seurat_pbmc3k_basic.v1\n"
            "    status: dry_run_completed\n"
            "    artifacts: [node_manifest.yaml]\n"
            "    warnings: [environment lock missing]\n"
            "    errors: []\n"
            "    environment: {status: pass}\n",
            encoding="utf-8",
        )

        manager = ModuleFeedbackManager(root)
        records = manager.record_run(
            paper_id="paper_a",
            run_id="demo_20260709_v1",
            run_dir=run_dir,
            adapter_result={"adapter": "analysis_graph_executor", "metrics": {"runtime_seconds": 0.1}},
            evaluation={"status": "degraded_exploratory", "source_map_valid": True},
        )
        assert records[0]["status"] == "degraded"
        assert manager.ledger_path.exists()

        summarized = run_cli(
            root,
            "summarize-module-usage",
            "--module",
            "single_cell.seurat_pbmc3k_basic.v1",
            "--json",
        )
        assert summarized.returncode == 0, summarized.stdout + summarized.stderr
        summary = json.loads(summarized.stdout)
        assert summary["usage_count"] == 1
        assert summary["status_counts"]["degraded"] == 1

        proposed = run_cli(root, "propose-module-improvement", "--run-id", "demo_20260709_v1", "--json")
        assert proposed.returncode == 0, proposed.stdout + proposed.stderr
        proposal = json.loads(proposed.stdout)
        assert proposal["registry_mutation"] == "not_performed"
        proposal_path = Path(proposal["path"])
        assert proposal_path.exists()

        rejected_apply = run_cli(root, "apply-module-improvement", "--proposal", proposal_path.name, "--json")
        assert rejected_apply.returncode != 0

        approved = run_cli(
            root,
            "apply-module-improvement",
            "--proposal",
            proposal_path.name,
            "--approved",
            "--json",
        )
        assert approved.returncode == 0, approved.stdout + approved.stderr
        approved_payload = json.loads(approved.stdout)
        assert approved_payload["status"] == "approved_for_manual_implementation"
        assert yaml.safe_load(proposal_path.read_text(encoding="utf-8"))["registry_mutation"] == "not_performed"
        assert registry.read_text(encoding="utf-8") == "modules: {}\n"
