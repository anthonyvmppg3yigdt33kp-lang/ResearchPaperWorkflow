from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import yaml


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


def test_adapt_method_block_cli_generates_scaffold_without_registry_mutation(tmp_path: Path):
    root = tmp_path
    (root / "AGENTS.md").write_text("# test\n", encoding="utf-8")
    (root / "code_library" / "external_sources" / "source1").mkdir(parents=True)
    (root / "code_library" / "module_registry.yaml").write_text("modules: {}\n", encoding="utf-8")
    block = {
        "block_id": "block1",
        "source_file": "original/script.R",
        "line_start": 10,
        "line_end": 14,
        "detected_calls": ["FindMarkers"],
        "reviewer_risk": ["cell-level tests are exploratory"],
        "claim_boundary": "Cell-level marker/differential expression is exploratory unless biological replicate-aware inference is documented.",
        "status": "requires_human_review",
    }
    (root / "code_library" / "external_sources" / "source1" / "method_blocks.yaml").write_text(
        yaml.safe_dump({"source_id": "source1", "method_blocks": [block]}, sort_keys=False),
        encoding="utf-8",
    )
    (root / "code_library" / "external_sources" / "source1" / "license_review.yaml").write_text(
        "status: pending_human_review\n",
        encoding="utf-8",
    )

    completed = run_cli(
        root,
        "adapt-method-block",
        "--source-id",
        "source1",
        "--block-id",
        "block1",
        "--module-id",
        "external.source1.findmarkers.v1",
        "--family",
        "seurat_findmarkers_group_de",
        "--approved-review",
        "--json",
    )

    assert completed.returncode == 0, completed.stdout + completed.stderr
    payload = json.loads(completed.stdout)
    module_dir = Path(payload["module_dir"])
    assert payload["registry_mutated"] is False
    assert (module_dir / "main.R").exists()
    assert (module_dir / "R" / "functions.R").exists()
    assert (module_dir / "PROVENANCE.md").exists()
    reusable_text = (module_dir / "main.R").read_text(encoding="utf-8") + (module_dir / "R" / "functions.R").read_text(encoding="utf-8")
    assert "LUAD" not in reusable_text
    assert (root / "code_library" / "module_registry.yaml").read_text(encoding="utf-8") == "modules: {}\n"
