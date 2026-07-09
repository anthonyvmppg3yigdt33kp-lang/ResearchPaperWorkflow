"""Bioinformatics-specific run quality checks."""

from __future__ import annotations

import csv
import re
from pathlib import Path
from typing import Any

import yaml


WINDOWS_PERSONAL_PATH_RE = re.compile(r"[A-Za-z]:[\\/](?:Users|Documents and Settings)[\\/][^\\/\s]+", re.IGNORECASE)
PROJECT_TERM_RE = re.compile(r"\b(?:LUAD|LUSC|NSCLC|Tumou?r|BH)\b")


def read_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh) or {}
    return data if isinstance(data, dict) else {}


def write_yaml(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        yaml.safe_dump(data, fh, allow_unicode=True, sort_keys=False)


class BioinformaticsRunQualityRules:
    """Evaluate run artifacts beyond generic manifest/source-map existence."""

    REQUIRED_FINDMARKERS_COLUMNS = {
        "gene",
        "p_val",
        "avg_log2FC",
        "pct.1",
        "pct.2",
        "p_val_adj",
        "ident_1",
        "ident_2",
        "group_column",
        "subset_column",
        "subset_value",
    }

    def __init__(self, run_dir: Path):
        self.run_dir = Path(run_dir)

    def evaluate(self, write_outputs: bool = False) -> dict[str, Any]:
        manifest = read_yaml(self.run_dir / "run_manifest.yaml")
        checks: list[dict[str, Any]] = []
        next_plan = {
            "current_run_status": manifest.get("status", "unknown"),
            "passed_modules": [],
            "failed_modules": [],
            "recommended_next_modules": [],
            "blocking_issues": [],
            "human_review_items": [],
        }
        checks.extend(self._check_node_artifacts(manifest, next_plan))
        checks.extend(self._check_source_maps(next_plan))
        checks.extend(self._check_text_leaks(next_plan))
        if not manifest.get("data_registry_hash"):
            checks.append(self._check("data_registry_hash", False, "run_manifest.yaml missing data_registry_hash"))
            next_plan["human_review_items"].append("declare and validate paper-scoped data registry before production execution")
        status = "pass" if all(item["status"] == "pass" for item in checks) else "needs_review"
        report = {
            "schema_version": "bioinformatics_quality_report.v1",
            "run_id": self.run_dir.name,
            "status": status,
            "checks": checks,
            "summary": {
                "pass_count": len([item for item in checks if item["status"] == "pass"]),
                "issue_count": len([item for item in checks if item["status"] != "pass"]),
            },
        }
        if status != "pass":
            next_plan["current_run_status"] = status
        if write_outputs:
            write_yaml(self.run_dir / "qc" / "bioinformatics_quality_report.yaml", report)
            write_yaml(self.run_dir / "qc" / "next_analysis_plan.yaml", next_plan)
        return {"report": report, "next_analysis_plan": next_plan}

    def _check_node_artifacts(self, manifest: dict[str, Any], next_plan: dict[str, Any]) -> list[dict[str, Any]]:
        checks = []
        for node in manifest.get("nodes", []) or []:
            module_id = str(node.get("module_id", ""))
            node_id = str(node.get("node_id", ""))
            node_status = str(node.get("status", ""))
            if node_status == "completed":
                next_plan["passed_modules"].append(module_id)
            elif node_status == "blocked":
                next_plan["failed_modules"].append(module_id)
            artifacts = [self.run_dir.parents[2] / rel for rel in node.get("artifacts", []) or []]
            if "findmarkers" in module_id:
                checks.extend(self._check_findmarkers_node(node_id, artifacts, next_plan))
            if "limma_voom" in module_id:
                checks.extend(self._check_limma_node(node_id, artifacts, next_plan))
        return checks

    def _check_findmarkers_node(self, node_id: str, artifacts: list[Path], next_plan: dict[str, Any]) -> list[dict[str, Any]]:
        checks = []
        results = self._artifact_path(artifacts, "tables/findmarkers_results.csv")
        checks.append(self._check(f"{node_id}.findmarkers_results_exists", bool(results and results.exists()), "missing tables/findmarkers_results.csv"))
        if results and results.exists():
            rows, columns = self._read_csv(results)
            checks.append(self._check(f"{node_id}.findmarkers_results_nonempty", len(rows) > 0, "findmarkers_results.csv is empty"))
            missing = sorted(self.REQUIRED_FINDMARKERS_COLUMNS - set(columns))
            checks.append(self._check(f"{node_id}.findmarkers_required_columns", not missing, f"missing columns: {', '.join(missing)}"))
            if "p_val_adj" in columns:
                valid = all(self._is_fdr(row.get("p_val_adj", "")) for row in rows if row.get("p_val_adj", "") != "")
                checks.append(self._check(f"{node_id}.findmarkers_p_val_adj_range", valid, "p_val_adj values must be numeric between 0 and 1"))
            if "avg_log2FC" in columns:
                non_na = any(str(row.get("avg_log2FC", "")).lower() not in {"", "na", "nan"} for row in rows)
                checks.append(self._check(f"{node_id}.findmarkers_avg_log2fc_non_na", non_na, "avg_log2FC is entirely missing/NA"))
        checks.append(self._check(f"{node_id}.session_info_exists", bool(self._artifact_path(artifacts, "logs/sessionInfo.txt")), "missing logs/sessionInfo.txt"))
        checks.append(self._check(f"{node_id}.group_size_report_exists", bool(self._artifact_path(artifacts, "qc/group_size_sample_mapping.csv")), "missing group size/sample mapping report"))
        next_plan["recommended_next_modules"].append("replicate-aware pseudobulk DE if sample_id mapping is available")
        return checks

    def _check_limma_node(self, node_id: str, artifacts: list[Path], next_plan: dict[str, Any]) -> list[dict[str, Any]]:
        checks = []
        results = self._artifact_path(artifacts, "tables/limma_voom_results.csv")
        checks.append(self._check(f"{node_id}.limma_results_exists", bool(results and results.exists()), "missing tables/limma_voom_results.csv"))
        if results and results.exists():
            rows, columns = self._read_csv(results)
            checks.append(self._check(f"{node_id}.limma_results_nonempty", len(rows) > 0, "limma_voom_results.csv is empty"))
            checks.append(self._check(f"{node_id}.limma_adj_p_present", "adj.P.Val" in columns, "missing adj.P.Val column"))
        checks.append(self._check(f"{node_id}.design_summary_exists", bool(self._artifact_path(artifacts, "qc/design_summary.csv")), "missing qc/design_summary.csv"))
        next_plan["recommended_next_modules"].append("ranked-gene enrichment after DE table review")
        return checks

    def _check_source_maps(self, next_plan: dict[str, Any]) -> list[dict[str, Any]]:
        checks = []
        for name, key in [("figure_source_map.yaml", "figures"), ("table_source_map.yaml", "tables")]:
            data = read_yaml(self.run_dir / name)
            items = data.get(key, []) if isinstance(data, dict) else []
            missing = [idx for idx, item in enumerate(items or []) if isinstance(item, dict) and not item.get("claim_boundary")]
            checks.append(self._check(f"{name}.claim_boundary_complete", not missing, f"{name} entries missing claim_boundary: {missing}"))
            if missing:
                next_plan["human_review_items"].append(f"complete claim_boundary fields in {name}")
        return checks

    def _check_text_leaks(self, next_plan: dict[str, Any]) -> list[dict[str, Any]]:
        leaked_paths = []
        project_terms = []
        for path in self.run_dir.rglob("*"):
            if not path.is_file() or path.suffix.lower() not in {".yaml", ".yml", ".csv", ".txt", ".md", ".log"}:
                continue
            if path.name == "evaluation_report.yaml":
                continue
            text = path.read_text(encoding="utf-8", errors="replace")
            if WINDOWS_PERSONAL_PATH_RE.search(text):
                leaked_paths.append(str(path.relative_to(self.run_dir)).replace("\\", "/"))
            if PROJECT_TERM_RE.search(text) and "external" in text.lower():
                project_terms.append(str(path.relative_to(self.run_dir)).replace("\\", "/"))
        if leaked_paths:
            next_plan["blocking_issues"].append("remove Windows personal paths from run artifacts")
        if project_terms:
            next_plan["human_review_items"].append("review adapted external module artifacts for project-specific disease terms")
        return [
            self._check("no_windows_personal_path_leak", not leaked_paths, f"path leaks: {', '.join(leaked_paths)}"),
            self._check("adapted_external_module_no_hardcoded_disease_terms", not project_terms, f"project terms in external artifacts: {', '.join(project_terms)}"),
        ]

    def _artifact_path(self, artifacts: list[Path], suffix: str) -> Path | None:
        suffix = suffix.replace("\\", "/")
        for path in artifacts:
            normalized = str(path).replace("\\", "/")
            if normalized.endswith(suffix) and path.exists() and path.stat().st_size > 0:
                return path
        candidate = self.run_dir / suffix
        if candidate.exists() and candidate.stat().st_size > 0:
            return candidate
        return None

    @staticmethod
    def _read_csv(path: Path) -> tuple[list[dict[str, str]], list[str]]:
        with path.open("r", encoding="utf-8", newline="") as fh:
            reader = csv.DictReader(fh)
            rows = list(reader)
            columns = list(reader.fieldnames or [])
        return rows, columns

    @staticmethod
    def _is_fdr(value: str) -> bool:
        try:
            parsed = float(value)
        except ValueError:
            return False
        return 0 <= parsed <= 1

    @staticmethod
    def _check(name: str, passed: bool, message: str) -> dict[str, Any]:
        return {"name": name, "status": "pass" if passed else "needs_review", "message": "" if passed else message}
