"""Generate reviewed module scaffolds from extracted method blocks."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import yaml

from paper_workflow.bioinformatics.code_source_importer import read_yaml, utc_now, write_yaml
from paper_workflow.bioinformatics.method_depersonalizer import assert_no_project_terms


def adapt_method_block(
    *,
    project_root: Path,
    source_id: str,
    block_id: str,
    module_id: str,
    family: str,
    approved_review: bool = False,
    register: bool = False,
) -> dict[str, Any]:
    """Write an external adapted-module scaffold without mutating the registry."""
    project_root = Path(project_root)
    source_dir = project_root / "code_library" / "external_sources" / source_id
    blocks_data = read_yaml(source_dir / "method_blocks.yaml")
    blocks = list(blocks_data.get("method_blocks", []) or [])
    block = next((item for item in blocks if str(item.get("block_id")) == block_id), None)
    if block is None:
        raise FileNotFoundError(f"method block not found: {source_id}/{block_id}")
    if not approved_review:
        raise PermissionError("--approved-review is required before adapting a method block scaffold")

    module_name = _module_name(module_id)
    module_dir = project_root / "code_library" / "modules" / "external" / source_id / module_name
    module_dir.mkdir(parents=True, exist_ok=True)
    (module_dir / "R").mkdir(exist_ok=True)
    (module_dir / "tests").mkdir(exist_ok=True)

    if "findmarkers" in family.lower() or "seurat" in family.lower():
        main_text, functions_text, metadata = _findmarkers_templates(module_id, source_id, block)
    elif "limma" in family.lower() or "voom" in family.lower():
        main_text, functions_text, metadata = _limma_templates(module_id, source_id, block)
    else:
        main_text, functions_text, metadata = _generic_templates(module_id, source_id, block)

    reusable_terms = assert_no_project_terms(main_text + "\n" + functions_text)
    if reusable_terms:
        raise ValueError(f"generated scaffold contains project-specific reusable logic terms: {', '.join(reusable_terms)}")

    (module_dir / "main.R").write_text(main_text, encoding="utf-8")
    (module_dir / "R" / "functions.R").write_text(functions_text, encoding="utf-8")
    write_yaml(module_dir / "module.yaml", metadata["module_yaml"])
    write_yaml(module_dir / "env_profile.yaml", metadata["env_profile"])
    (module_dir / "README.md").write_text(metadata["readme"], encoding="utf-8")
    (module_dir / "PROVENANCE.md").write_text(metadata["provenance"], encoding="utf-8")
    write_yaml(module_dir / "tests" / "toy_input_manifest.yaml", metadata["toy_input"])
    write_yaml(module_dir / "tests" / "expected_outputs.yaml", metadata["expected_outputs"])

    registry_patch = ""
    license_review = read_yaml(source_dir / "license_review.yaml")
    if register:
        if license_review.get("status") != "approved_for_adaptation":
            raise PermissionError("license_review.yaml must be approved_for_adaptation before --register can generate a registry patch")
        registry_patch = str(module_dir / "registry_patch.yaml")
        write_yaml(module_dir / "registry_patch.yaml", {"modules": {module_id: metadata["registry_entry"]}, "generated_at": utc_now()})

    return {
        "source_id": source_id,
        "block_id": block_id,
        "module_id": module_id,
        "family": family,
        "module_dir": str(module_dir),
        "registry_mutated": False,
        "registry_patch": registry_patch,
        "status": "adapted_scaffold_created",
    }


def _module_name(module_id: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", module_id).strip("_")


def _common_metadata(module_id: str, source_id: str, block: dict[str, Any], family: str, env_id: str, artifacts: list[str]) -> dict[str, Any]:
    claim_boundary = str(block.get("claim_boundary") or "Reviewed external method block; claim requires validated execution.")
    module_yaml = {
        "id": module_id,
        "source_id": source_id,
        "source_block_id": block.get("block_id", ""),
        "family": family,
        "status": "adapted_scaffold_requires_tests",
        "claim_boundary": claim_boundary,
    }
    env_profile = {
        "env_id": env_id,
        "status": "declared",
        "package_policy": "check_at_runtime",
    }
    toy_input = {
        "inputs": [
            {"name": "toy_input", "status": "dry_run_fixture", "publication_evidence": False},
        ],
        "source_block": block.get("block_id", ""),
    }
    expected_outputs = {
        "required_outputs": ["outputs_manifest.yaml", "node_manifest.yaml", *artifacts],
        "publication_grade": False,
    }
    return {
        "module_yaml": module_yaml,
        "env_profile": env_profile,
        "toy_input": toy_input,
        "expected_outputs": expected_outputs,
        "readme": (
            f"# {module_id}\n\n"
            "Adapted scaffold generated from a reviewed external method block. "
            "It is intentionally parameterized and does not copy project-specific "
            "disease labels into reusable logic. Promotion to the main registry "
            "requires human license/provenance approval and adapter tests.\n"
        ),
        "provenance": (
            f"# Provenance\n\n- Source ID: `{source_id}`\n"
            f"- Source file: `{block.get('source_file', '')}`\n"
            f"- Lines: {block.get('line_start')}--{block.get('line_end')}\n"
            f"- Detected calls: {', '.join(str(v) for v in block.get('detected_calls', []) or []) or 'none'}\n"
            f"- Review status: `{block.get('status', 'requires_human_review')}`\n"
        ),
    }


def _findmarkers_templates(module_id: str, source_id: str, block: dict[str, Any]) -> tuple[str, str, dict[str, Any]]:
    metadata = _common_metadata(
        module_id,
        source_id,
        block,
        "seurat_findmarkers_group_de",
        "r_seurat_v5",
        ["tables/findmarkers_results.csv", "tables/findmarkers_summary.csv", "figure_source_map.yaml", "table_source_map.yaml"],
    )
    main_text = """#!/usr/bin/env Rscript
args_full <- commandArgs(trailingOnly = FALSE)
file_arg <- grep("^--file=", args_full, value = TRUE)
script_path <- if (length(file_arg) > 0) sub("^--file=", "", file_arg[[1]]) else "main.R"
source(file.path(dirname(normalizePath(script_path, winslash = "/", mustWork = TRUE)), "R", "functions.R"))
run_seurat_findmarkers_group_de_cli(commandArgs(trailingOnly = TRUE))
"""
    functions_text = _findmarkers_functions_r()
    metadata["registry_entry"] = {
        "id": module_id,
        "name": "External Seurat FindMarkers group DE scaffold",
        "modality": "single_cell",
        "step": "seurat_findmarkers_group_de",
        "language": "r",
        "source": {"type": "external_adapted_scaffold", "path": f"code_library/modules/external/{source_id}/{_module_name(module_id)}/main.R", "origin": source_id, "license": "requires_human_review"},
        "environment": {"env_id": "r_seurat_v5", "required_packages": ["Seurat", "SeuratObject", "Matrix", "ggplot2"]},
        "input_schema": {"required": [{"name": "seurat_rds", "type": "seurat_rds"}, {"name": "group_column", "type": "metadata_column"}, {"name": "ident_1", "type": "group_value"}, {"name": "ident_2", "type": "group_value"}]},
        "output_schema": {"artifacts": metadata["expected_outputs"]["required_outputs"]},
        "reviewer_risk": block.get("reviewer_risk", []),
        "claim_boundary": block.get("claim_boundary", ""),
        "validation_status": "adapted_scaffold_requires_tests",
        "method_maturity": "scaffold",
    }
    return main_text, functions_text, metadata


def _limma_templates(module_id: str, source_id: str, block: dict[str, Any]) -> tuple[str, str, dict[str, Any]]:
    metadata = _common_metadata(
        module_id,
        source_id,
        block,
        "limma_voom_de",
        "r_bulk_rnaseq",
        ["tables/limma_voom_results.csv", "figures/limma_voom_volcano.png", "figure_source_map.yaml", "table_source_map.yaml"],
    )
    main_text = """#!/usr/bin/env Rscript
args_full <- commandArgs(trailingOnly = FALSE)
file_arg <- grep("^--file=", args_full, value = TRUE)
script_path <- if (length(file_arg) > 0) sub("^--file=", "", file_arg[[1]]) else "main.R"
source(file.path(dirname(normalizePath(script_path, winslash = "/", mustWork = TRUE)), "R", "functions.R"))
run_limma_voom_de_cli(commandArgs(trailingOnly = TRUE))
"""
    functions_text = _limma_functions_r()
    return main_text, functions_text, metadata


def _generic_templates(module_id: str, source_id: str, block: dict[str, Any]) -> tuple[str, str, dict[str, Any]]:
    metadata = _common_metadata(module_id, source_id, block, "generic_reviewed_method", "python_builtin", ["outputs_manifest.yaml"])
    main_text = """#!/usr/bin/env Rscript
args <- commandArgs(trailingOnly = TRUE)
get_arg <- function(flag, default = "") {
  idx <- which(args == flag)
  if (length(idx) == 0 || idx[length(idx)] == length(args)) {
    return(default)
  }
  args[idx[length(idx)] + 1]
}
out_dir <- get_arg("--out", "generic_scaffold_out")
run_id <- get_arg("--run-id", "generic_scaffold")
dir.create(out_dir, recursive = TRUE, showWarnings = FALSE)
if ("--dry-run" %in% args) {
  writeLines(c(
    "schema_version: generic_scaffold_outputs.v1",
    paste0("run_id: ", run_id),
    "status: dry_run_completed",
    "outputs: []"
  ), file.path(out_dir, "outputs_manifest.yaml"))
  writeLines(c(
    "schema_version: generic_scaffold_node.v1",
    paste0("run_id: ", run_id),
    "status: dry_run_completed",
    "claim_boundary: scaffold only; real execution requires manual implementation"
  ), file.path(out_dir, "node_manifest.yaml"))
  quit(status = 0)
}
stop("generic scaffold requires manual implementation before execution")
"""
    functions_text = "# Generic scaffold placeholder. Add reviewed parameterized functions here.\n"
    return main_text, functions_text, metadata


def _findmarkers_functions_r() -> str:
    path = Path(__file__).resolve().parents[3] / "code_library" / "modules" / "single_cell" / "seurat_findmarkers_group_de" / "R" / "functions.R"
    return path.read_text(encoding="utf-8") if path.exists() else "run_seurat_findmarkers_group_de_cli <- function(args) stop('template unavailable')\n"


def _limma_functions_r() -> str:
    path = Path(__file__).resolve().parents[3] / "code_library" / "modules" / "bulk_rnaseq" / "limma_voom_de_real" / "R" / "functions.R"
    return path.read_text(encoding="utf-8") if path.exists() else "run_limma_voom_de_cli <- function(args) stop('template unavailable')\n"
