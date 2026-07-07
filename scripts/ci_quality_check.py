"""Repository quality gates used by local preflight and GitHub Actions."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import yaml


REQUIRED_MODES = {
    "exploration_mode",
    "analysis_design_mode",
    "execution_mode",
    "closeout_audit_mode",
    "ppt_briefing_mode",
    "retrospective_mode",
}

REQUIRED_PROFILES = {
    "quick_status",
    "exploratory_omics",
    "analysis_design",
    "evidence_maturation",
    "manuscript_build",
    "submission_closeout",
}

REQUIRED_ANALYSIS_FIELDS = {
    "research_question",
    "primary_contrast",
    "data_type",
    "statistical_unit",
    "inclusion_exclusion",
    "covariates",
    "batch_or_confounder_plan",
    "normalization_or_preprocessing",
    "primary_methods",
    "validation_plan",
    "sensitivity_plan",
    "expected_outputs",
    "run_id",
    "user_approval",
}

EXCLUDED_DIRS = {
    ".git",
    ".pytest_cache",
    "__pycache__",
    "papers",
    "results",
    "tmp",
    "output",
    "outputs",
    "logs",
    "node_modules",
    "code_library/external_repos",
    "code_library/external_skill_sources",
}


def load_yaml(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def is_excluded(path: Path, root: Path) -> bool:
    rel = path.relative_to(root).as_posix()
    parts = set(path.relative_to(root).parts)
    if parts & {".git", ".pytest_cache", "__pycache__", "papers", "tmp", "output", "outputs", "logs", "node_modules"}:
        return True
    return any(rel == item or rel.startswith(item + "/") for item in EXCLUDED_DIRS)


def iter_yaml_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for folder in [root / "config", root / ".github" / "workflows"]:
        if not folder.exists():
            continue
        files.extend(folder.rglob("*.yaml"))
        files.extend(folder.rglob("*.yml"))
    return sorted(set(files))


def validate_yaml_parse(root: Path) -> list[str]:
    issues: list[str] = []
    for path in iter_yaml_files(root):
        try:
            load_yaml(path)
        except Exception as exc:  # pragma: no cover - exact parser exceptions vary
            issues.append(f"YAML parse failed: {path.relative_to(root)}: {type(exc).__name__}: {exc}")
    return issues


def validate_workflow_modes(root: Path) -> list[str]:
    path = root / "config" / "workflow_modes.yaml"
    if not path.exists():
        return ["missing config/workflow_modes.yaml"]
    data = load_yaml(path) or {}
    modes = set((data.get("modes") or {}).keys())
    profiles = set((data.get("profiles") or {}).keys())
    issues = []
    missing_modes = sorted(REQUIRED_MODES - modes)
    missing_profiles = sorted(REQUIRED_PROFILES - profiles)
    if missing_modes:
        issues.append(f"workflow_modes missing modes: {missing_modes}")
    if missing_profiles:
        issues.append(f"workflow_modes missing profiles: {missing_profiles}")
    default_route = data.get("default_route") or {}
    if default_route.get("fuzzy_request") != "exploration_mode":
        issues.append("workflow_modes default_route.fuzzy_request must be exploration_mode")
    return issues


def validate_result_policy(root: Path) -> list[str]:
    path = root / "config" / "result_write_policy.yaml"
    if not path.exists():
        return ["missing config/result_write_policy.yaml"]
    data = load_yaml(path) or {}
    layout = data.get("required_layout") or {}
    issues = []
    if layout.get("run_root") != "results/runs/<run_id>/":
        issues.append("result_write_policy required_layout.run_root mismatch")
    if layout.get("current_run_file") != "results/current_run.yaml":
        issues.append("result_write_policy required_layout.current_run_file mismatch")
    if "current_run_schema" not in data:
        issues.append("result_write_policy missing current_run_schema")
    return issues


def validate_analysis_contract(root: Path) -> list[str]:
    path = root / "config" / "bioinformatics_method_contract.yaml"
    if not path.exists():
        return ["missing config/bioinformatics_method_contract.yaml"]
    data = load_yaml(path) or {}
    fields = set(data.get("analysis_design_required_fields") or [])
    missing = sorted(REQUIRED_ANALYSIS_FIELDS - fields)
    if missing:
        return [f"bioinformatics_method_contract missing analysis fields: {missing}"]
    rules = data.get("execution_rules") or {}
    issues = []
    if not rules.get("require_design_before_execution", False):
        issues.append("execution_rules.require_design_before_execution must be true")
    if not rules.get("forbid_agent_phase_package_install", False):
        issues.append("execution_rules.forbid_agent_phase_package_install must be true")
    return issues


def validate_code_library_registry(root: Path) -> list[str]:
    path = root / "config" / "code_library_registry.yaml"
    if not path.exists():
        return ["missing config/code_library_registry.yaml"]
    data = load_yaml(path) or {}
    issues: list[str] = []
    policy = data.get("ingestion_policy") or {}
    if policy.get("default_strategy") != "dependency_or_adapter_first":
        issues.append("code_library_registry ingestion_policy.default_strategy must be dependency_or_adapter_first")
    if not policy.get("forbid_dataset_mirroring", False):
        issues.append("code_library_registry must forbid dataset mirroring")
    capabilities = data.get("capabilities") or []
    if not isinstance(capabilities, list) or len(capabilities) < 8:
        issues.append("code_library_registry must contain at least 8 curated capability entries")
        return issues
    required = {"id", "source", "area", "use_class", "capability_tags", "initial_decision", "local_status"}
    ids: set[str] = set()
    for idx, entry in enumerate(capabilities):
        if not isinstance(entry, dict):
            issues.append(f"code_library_registry entry {idx} is not a mapping")
            continue
        missing = sorted(required - set(entry.keys()))
        if missing:
            issues.append(f"code_library_registry entry {entry.get('id', idx)} missing fields: {missing}")
        entry_id = str(entry.get("id", ""))
        if entry_id in ids:
            issues.append(f"code_library_registry duplicate id: {entry_id}")
        ids.add(entry_id)
        tags = entry.get("capability_tags") or []
        if not isinstance(tags, list) or not tags:
            issues.append(f"code_library_registry entry {entry_id} must have non-empty capability_tags")
    return issues


def validate_large_files(root: Path, max_bytes: int) -> list[str]:
    issues: list[str] = []
    for path in root.rglob("*"):
        if not path.is_file() or is_excluded(path, root):
            continue
        size = path.stat().st_size
        if size > max_bytes:
            rel = path.relative_to(root).as_posix()
            issues.append(f"large file exceeds {max_bytes} bytes: {rel} ({size})")
    return issues


def run_checks(root: Path, max_bytes: int) -> dict[str, Any]:
    checks = {
        "yaml_parse": validate_yaml_parse(root),
        "workflow_modes": validate_workflow_modes(root),
        "result_write_policy": validate_result_policy(root),
        "bioinformatics_method_contract": validate_analysis_contract(root),
        "code_library_registry": validate_code_library_registry(root),
        "large_files": validate_large_files(root, max_bytes),
    }
    issue_count = sum(len(v) for v in checks.values())
    return {
        "root": str(root),
        "status": "pass" if issue_count == 0 else "fail",
        "issue_count": issue_count,
        "checks": checks,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="ResearchPaperWorkflow CI quality gate")
    parser.add_argument("--root", default=".", help="Repository root")
    parser.add_argument("--max-bytes", type=int, default=25_000_000)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    result = run_checks(Path(args.root).resolve(), args.max_bytes)
    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(f"CI quality status: {result['status']} ({result['issue_count']} issue(s))")
        for check, issues in result["checks"].items():
            print(f"- {check}: {'pass' if not issues else 'fail'}")
            for issue in issues:
                print(f"  - {issue}")
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    sys.exit(main())
