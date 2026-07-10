"""Repository quality gates used by local preflight and GitHub Actions."""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from pathlib import Path
from typing import Any

import yaml


PRODUCTION_CAPABILITY_GRADES = {
    "production_capable_real_wrapper",
    "validated_workflow_pilot",
    "dry_run_contract",
    "adapter_contract",
    "scaffold_only",
    "planning_contract",
    "blocked_environment",
    "retired",
}

EXECUTION_EVIDENCE_LEVELS = {
    "real_project_data_validated",
    "official_tutorial_validated",
    "toy_real_tested",
    "dry_run_only",
    "contract_only",
    "no_execution_evidence",
}

STRATEGY_VISIBILITY = {
    "production_candidate",
    "exploratory_candidate",
    "planning_only",
    "hidden_from_production",
}

CLAIM_PERMISSIONS = {
    "workflow_test_only",
    "exploratory_only",
    "association_with_review",
    "no_claim",
}

ENVIRONMENT_STATUSES = {"pass", "degraded", "blocked", "unknown"}

FORBIDDEN_PRODUCTION_GRADES = {
    "adapter_contract",
    "scaffold_only",
    "planning_contract",
    "blocked_environment",
    "retired",
}


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
    "data",
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
    if parts & {".git", ".pytest_cache", "__pycache__", "papers", "data", "tmp", "output", "outputs", "logs", "node_modules"}:
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
    if not rules.get("require_module_registry", False):
        issues.append("execution_rules.require_module_registry must be true")
    if not rules.get("require_environment_registry", False):
        issues.append("execution_rules.require_environment_registry must be true")
    if not rules.get("require_analysis_graph_for_method_asset_execution", False):
        issues.append("execution_rules.require_analysis_graph_for_method_asset_execution must be true")
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


def validate_method_asset_registries(root: Path) -> list[str]:
    module_path = root / "code_library" / "module_registry.yaml"
    env_path = root / "code_library" / "environment_registry.yaml"
    issues: list[str] = []
    if not module_path.exists():
        issues.append("missing code_library/module_registry.yaml")
        return issues
    if not env_path.exists():
        issues.append("missing code_library/environment_registry.yaml")
    modules_data = load_yaml(module_path) or {}
    modules = modules_data.get("modules") or {}
    if not isinstance(modules, dict) or not modules:
        issues.append("module_registry must contain a non-empty modules mapping")
        return issues
    required = {
        "name", "modality", "step", "language", "source", "environment",
        "input_schema", "output_schema", "reviewer_risk", "claim_boundary",
        "validation_status", "method_maturity", "production_capability_grade",
        "execution_evidence_level", "strategy_visibility", "claim_permission",
        "current_environment_status",
    }
    for module_id, module in modules.items():
        if not isinstance(module, dict):
            issues.append(f"module_registry entry {module_id} is not a mapping")
            continue
        missing = sorted(required - set(module.keys()))
        if missing:
            issues.append(f"module_registry entry {module_id} missing fields: {missing}")
        source_path = ((module.get("source") or {}).get("path") or "")
        if source_path and not (root / source_path).exists():
            issues.append(f"module_registry entry {module_id} source path missing: {source_path}")
        _validate_enum(issues, module_id, module, "production_capability_grade", PRODUCTION_CAPABILITY_GRADES)
        _validate_enum(issues, module_id, module, "execution_evidence_level", EXECUTION_EVIDENCE_LEVELS)
        _validate_enum(issues, module_id, module, "strategy_visibility", STRATEGY_VISIBILITY)
        _validate_enum(issues, module_id, module, "claim_permission", CLAIM_PERMISSIONS)
        _validate_enum(issues, module_id, module, "current_environment_status", ENVIRONMENT_STATUSES)
        grade = str(module.get("production_capability_grade", ""))
        visibility = str(module.get("strategy_visibility", ""))
        env_status = str(module.get("current_environment_status", ""))
        if grade in FORBIDDEN_PRODUCTION_GRADES and visibility in {"production_candidate", "exploratory_candidate"}:
            issues.append(f"module_registry entry {module_id} forbidden grade is production visible: {grade}/{visibility}")
        if env_status == "blocked" and visibility in {"production_candidate", "exploratory_candidate"}:
            issues.append(f"module_registry entry {module_id} environment-blocked module is production visible")
    env_data = load_yaml(env_path) if env_path.exists() else {}
    envs = (env_data or {}).get("environments") or {}
    if env_path.exists() and not envs:
        issues.append("environment_registry must contain at least one environment")
    return issues


def validate_research_experience(root: Path) -> list[str]:
    issues: list[str] = []
    knowledge_path = root / "code_library" / "method_knowledge_base.yaml"
    intent_schema = root / "config" / "research_intent.schema.yaml"
    example_intent = root / "intents" / "examples" / "pbmc3k_t_subcluster_intent.yaml"
    for path in (knowledge_path, intent_schema, example_intent):
        if not path.exists():
            issues.append(f"missing researcher-experience contract: {path.relative_to(root).as_posix()}")
    if issues:
        return issues
    try:
        knowledge = load_yaml(knowledge_path) or {}
        intent = load_yaml(example_intent) or {}
    except Exception as exc:
        return [f"researcher-experience YAML parse failed: {type(exc).__name__}: {exc}"]
    methods = knowledge.get("methods") or []
    if not isinstance(methods, list) or not methods:
        issues.append("method_knowledge_base must contain methods")
    modules = (load_yaml(root / "code_library" / "module_registry.yaml") or {}).get("modules", {}) or {}
    required = {"id", "question_types", "solves", "not_for", "statistical_unit", "prerequisites", "module_ids", "reviewer_risks", "claim_boundary"}
    for method in methods:
        missing = sorted(required - set(method or {}))
        if missing:
            issues.append(f"method knowledge entry {method.get('id', '<missing>')} missing fields: {missing}")
        for module_id in method.get("module_ids", []) or []:
            if module_id not in modules:
                issues.append(f"method knowledge entry {method.get('id')} references missing module: {module_id}")
    if intent.get("schema_version") != "research_intent.v1":
        issues.append("example research intent must use research_intent.v1")
    return issues


def validate_version_consistency(root: Path) -> list[str]:
    issues: list[str] = []
    config = load_yaml(root / "config" / "default_config.yaml") or {}
    config_version = str(config.get("version", ""))
    pipeline_version = str((config.get("pipeline") or {}).get("version", ""))
    pyproject_text = (root / "pyproject.toml").read_text(encoding="utf-8")
    package_text = (root / "src" / "paper_workflow" / "__init__.py").read_text(encoding="utf-8")
    readme_text = (root / "README.md").read_text(encoding="utf-8")
    pyproject_match = re.search(r'^version\s*=\s*"([^"]+)"', pyproject_text, flags=re.MULTILINE)
    package_match = re.search(r'^__version__\s*=\s*"([^"]+)"', package_text, flags=re.MULTILINE)
    readme_match = re.search(r'^# ResearchPaperWorkflow v([^\s]+)', readme_text)
    versions = {
        "config": config_version,
        "pipeline": pipeline_version,
        "pyproject": pyproject_match.group(1) if pyproject_match else "missing",
        "package": package_match.group(1) if package_match else "missing",
        "readme": readme_match.group(1) if readme_match else "missing",
    }
    if len(set(versions.values())) != 1:
        issues.append(f"active version mismatch: {versions}")
    return issues


def validate_pbmc3k_real_evidence(root: Path) -> list[str]:
    summary_path = root / "validation" / "pbmc3k_v5_1" / "validation_summary.yaml"
    manifest_path = root / "validation" / "pbmc3k_v5_1" / "artifact_manifest.tsv"
    if not summary_path.exists() or not manifest_path.exists():
        return ["missing v5.1 PBMC3K real-execution evidence packet"]
    summary = load_yaml(summary_path) or {}
    issues: list[str] = []
    evaluation = summary.get("evaluation") or {}
    metrics = summary.get("scientific_metrics") or {}
    execution = summary.get("execution") or {}
    if summary.get("execution_mode") != "real" or summary.get("status") != "pass":
        issues.append("PBMC3K evidence must record a real execution pass")
    if summary.get("evidence_grade") != "workflow_test":
        issues.append("PBMC3K evidence must remain workflow_test grade")
    for key in ("workflow_completeness_status", "scientific_quality_status", "environment_status", "final_status"):
        if evaluation.get(key) != "pass":
            issues.append(f"PBMC3K evidence evaluation.{key} must be pass")
    if evaluation.get("source_map_valid") is not True or evaluation.get("bioinformatics_quality_status") != "pass":
        issues.append("PBMC3K evidence requires valid source maps and bioinformatics QA pass")
    if not isinstance(execution.get("total_runtime_seconds"), (int, float)) or execution.get("total_runtime_seconds", 0) <= 0:
        issues.append("PBMC3K evidence must record a positive runtime")
    fraction = metrics.get("subset_fraction")
    if not isinstance(fraction, (int, float)) or not 0 < fraction <= 0.9:
        issues.append("PBMC3K evidence subset_fraction must be within (0, 0.9]")
    if int(metrics.get("marker_rows", 0) or 0) <= 0 or int(metrics.get("program_rows", 0) or 0) <= 0:
        issues.append("PBMC3K evidence requires non-empty marker and program tables")
    text = summary_path.read_text(encoding="utf-8") + manifest_path.read_text(encoding="utf-8")
    if re.search(r"[A-Za-z]:[/\\]Users[/\\]", text, flags=re.IGNORECASE):
        issues.append("PBMC3K evidence packet contains a personal Windows path")
    with manifest_path.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle, delimiter="\t"))
    if len(rows) < 10:
        issues.append("PBMC3K evidence artifact manifest is unexpectedly small")
    for row in rows:
        if not re.fullmatch(r"[0-9a-f]{64}", str(row.get("sha256", ""))):
            issues.append(f"PBMC3K evidence has invalid SHA-256: {row.get('relative_path', '<unknown>')}")
    return issues


def _validate_enum(issues: list[str], module_id: str, module: dict[str, Any], key: str, allowed: set[str]) -> None:
    value = str(module.get(key, ""))
    if value and value not in allowed:
        issues.append(f"module_registry entry {module_id} invalid {key}: {value}")


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
        "method_asset_registries": validate_method_asset_registries(root),
        "researcher_experience": validate_research_experience(root),
        "version_consistency": validate_version_consistency(root),
        "pbmc3k_real_evidence": validate_pbmc3k_real_evidence(root),
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
