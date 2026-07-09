from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
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


def test_import_review_and_register_figure_style_without_module_registry_mutation():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        root.joinpath("AGENTS.md").write_text("# test\n", encoding="utf-8")
        root.joinpath("code_library").mkdir()
        root.joinpath("code_library", "module_registry.yaml").write_text(
            "modules: {}\n",
            encoding="utf-8",
        )
        local_source = root / "source"
        local_source.mkdir()
        (local_source / "plot.R").write_text(
            "library(ggplot2)\nmake_plot <- function(x) { plot(x) }\nmake_plot(1:3)\n",
            encoding="utf-8",
        )

        imported = run_cli(
            root,
            "import-code-source",
            "--local",
            str(local_source),
            "--source-id",
            "paper_style_demo",
            "--json",
        )
        assert imported.returncode == 0, imported.stdout + imported.stderr
        payload = json.loads(imported.stdout)
        assert payload["status"] == "imported_for_review"
        assert payload["parsed_count"] == 1
        assert payload["proposal_count"] == 1
        source_dir = root / "code_library" / "external_sources" / "paper_style_demo"
        assert (source_dir / "source_manifest.yaml").exists()
        assert (source_dir / "license_review.yaml").exists()
        assert (source_dir / "parsed_source_index.yaml").exists()
        assert (source_dir / "module_proposals.yaml").exists()
        manifest = yaml.safe_load((source_dir / "source_manifest.yaml").read_text(encoding="utf-8"))
        assert "silent executable module registration" in manifest["forbidden_use"]
        parsed = yaml.safe_load((source_dir / "parsed_source_index.yaml").read_text(encoding="utf-8"))
        assert parsed["scripts"][0]["functions"] == ["make_plot"]
        proposals = yaml.safe_load((source_dir / "module_proposals.yaml").read_text(encoding="utf-8"))
        assert proposals["registry_update_allowed"] is False
        assert proposals["proposals"][0]["source_path"] == "original/plot.R"

        reviewed = run_cli(root, "review-code-source", "--source-id", "paper_style_demo", "--json")
        assert reviewed.returncode == 0, reviewed.stdout + reviewed.stderr
        review = json.loads(reviewed.stdout)
        assert review["registry_update_allowed"] is False

        registered = run_cli(root, "register-figure-style", "--source-id", "paper_style_demo", "--json")
        assert registered.returncode == 0, registered.stdout + registered.stderr
        style = json.loads(registered.stdout)
        assert style["style_id"] == "paper_style_demo_figure_style_v1"

        listed = run_cli(root, "list-figure-styles", "--json")
        assert listed.returncode == 0, listed.stdout + listed.stderr
        styles = json.loads(listed.stdout)["styles"]
        assert "paper_style_demo_figure_style_v1" in styles
        assert (root / "code_library" / "module_registry.yaml").read_text(encoding="utf-8") == "modules: {}\n"
