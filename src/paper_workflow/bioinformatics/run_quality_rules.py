"""Bioinformatics-specific run quality checks."""

from __future__ import annotations

import csv
import re
from pathlib import Path
from typing import Any

import yaml


WINDOWS_PERSONAL_PATH_RE = re.compile(r"[A-Za-z]:[\\/](?:Users|Documents and Settings)[\\/][^\\/\s]+", re.IGNORECASE)
PROJECT_TERM_RE = re.compile(r"\b(?:LUAD|LUSC|NSCLC|Tumou?r|BH)\b")

QUALITY_STATUS_RANK = {
    "pass": 0,
    "needs_review": 1,
    "needs_fix": 2,
    "blocked": 3,
}


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
    REQUIRED_SUBCLUSTER_MARKER_COLUMNS = {
        "gene",
        "cluster",
        "p_val",
        "avg_log2FC",
        "pct.1",
        "pct.2",
        "p_val_adj",
    }
    REQUIRED_SUBCLUSTER_FIGURES = (
        "figures/tcell_subset_umap.png",
        "figures/resolution_grid_umap.png",
        "figures/subcluster_marker_heatmap.png",
        "figures/program_score_violin.png",
        "figures/program_score_dotplot.png",
    )

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
            checks.append(self._check("data_registry_hash", False, "run_manifest.yaml missing data_registry_hash", "needs_fix"))
            next_plan["human_review_items"].append("declare and validate paper-scoped data registry before production execution")
        status = self._overall_status(checks)
        fail_closed = self._fail_closed_decision(status, checks)
        report = {
            "schema_version": "bioinformatics_quality_report.v1",
            "run_id": self.run_dir.name,
            "status": status,
            "final_status_allowed": status == "pass",
            "fail_closed_reasons": fail_closed["reasons"],
            "checks": checks,
            "summary": {
                "pass_count": len([item for item in checks if item["status"] == "pass"]),
                "issue_count": len([item for item in checks if item["status"] != "pass"]),
                "blocked_count": len([item for item in checks if item["status"] == "blocked"]),
                "needs_fix_count": len([item for item in checks if item["status"] == "needs_fix"]),
                "needs_review_count": len([item for item in checks if item["status"] == "needs_review"]),
            },
        }
        if status != "pass":
            next_plan["current_run_status"] = status
        if write_outputs:
            write_yaml(self.run_dir / "qc" / "bioinformatics_quality_report.yaml", report)
            write_yaml(self.run_dir / "qc" / "next_analysis_plan.yaml", next_plan)
            write_yaml(self.run_dir / "qc" / "fail_closed_decision.yaml", fail_closed)
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
            if "seurat_subcluster_programs" in module_id:
                checks.extend(self._check_subcluster_node(node_id, artifacts, next_plan))
        return checks

    def _check_findmarkers_node(self, node_id: str, artifacts: list[Path], next_plan: dict[str, Any]) -> list[dict[str, Any]]:
        checks = []
        results = self._artifact_path(artifacts, "tables/findmarkers_results.csv")
        checks.append(self._check(f"{node_id}.findmarkers_results_exists", bool(results and results.exists()), "missing tables/findmarkers_results.csv", "needs_fix"))
        if results and results.exists():
            rows, columns = self._read_csv(results)
            checks.append(self._check(f"{node_id}.findmarkers_results_nonempty", len(rows) > 0, "findmarkers_results.csv is empty", "needs_fix"))
            missing = sorted(self.REQUIRED_FINDMARKERS_COLUMNS - set(columns))
            checks.append(self._check(f"{node_id}.findmarkers_required_columns", not missing, f"missing columns: {', '.join(missing)}", "needs_fix"))
            if "p_val_adj" in columns:
                valid = all(self._is_fdr(row.get("p_val_adj", "")) for row in rows if row.get("p_val_adj", "") != "")
                checks.append(self._check(f"{node_id}.findmarkers_p_val_adj_range", valid, "p_val_adj values must be numeric between 0 and 1", "needs_fix"))
            if "avg_log2FC" in columns:
                non_na = any(str(row.get("avg_log2FC", "")).lower() not in {"", "na", "nan"} for row in rows)
                checks.append(self._check(f"{node_id}.findmarkers_avg_log2fc_non_na", non_na, "avg_log2FC is entirely missing/NA", "needs_fix"))
        checks.append(self._check(f"{node_id}.session_info_exists", bool(self._artifact_path(artifacts, "logs/sessionInfo.txt")), "missing logs/sessionInfo.txt", "needs_fix"))
        checks.append(self._check(f"{node_id}.group_size_report_exists", bool(self._artifact_path(artifacts, "qc/group_size_sample_mapping.csv")), "missing group size/sample mapping report", "needs_review"))
        next_plan["recommended_next_modules"].append("replicate-aware pseudobulk DE if sample_id mapping is available")
        return checks

    def _check_limma_node(self, node_id: str, artifacts: list[Path], next_plan: dict[str, Any]) -> list[dict[str, Any]]:
        checks = []
        results = self._artifact_path(artifacts, "tables/limma_voom_results.csv")
        checks.append(self._check(f"{node_id}.limma_results_exists", bool(results and results.exists()), "missing tables/limma_voom_results.csv", "needs_fix"))
        if results and results.exists():
            rows, columns = self._read_csv(results)
            checks.append(self._check(f"{node_id}.limma_results_nonempty", len(rows) > 0, "limma_voom_results.csv is empty", "needs_fix"))
            checks.append(self._check(f"{node_id}.limma_adj_p_present", "adj.P.Val" in columns, "missing adj.P.Val column", "needs_fix"))
        checks.append(self._check(f"{node_id}.design_summary_exists", bool(self._artifact_path(artifacts, "qc/design_summary.csv")), "missing qc/design_summary.csv", "needs_fix"))
        next_plan["recommended_next_modules"].append("ranked-gene enrichment after DE table review")
        return checks

    def _check_subcluster_node(self, node_id: str, artifacts: list[Path], next_plan: dict[str, Any]) -> list[dict[str, Any]]:
        checks = []
        markers = self._artifact_path(artifacts, "tables/subcluster_markers.csv")
        checks.append(self._check(f"{node_id}.subcluster_markers_exists", bool(markers), "missing tables/subcluster_markers.csv", "blocked"))
        if markers:
            rows, columns = self._read_csv(markers)
            missing = sorted(self.REQUIRED_SUBCLUSTER_MARKER_COLUMNS - set(columns))
            checks.append(self._check(f"{node_id}.subcluster_markers_nonempty", bool(rows), "subcluster_markers.csv is empty", "blocked"))
            checks.append(self._check(f"{node_id}.subcluster_marker_columns", not missing, f"missing columns: {', '.join(missing)}", "blocked"))
            if "p_val_adj" in columns:
                valid_fdr = all(self._is_fdr(row.get("p_val_adj", "")) for row in rows if row.get("p_val_adj", "") != "")
                checks.append(self._check(f"{node_id}.subcluster_marker_fdr_range", valid_fdr, "p_val_adj values must be numeric between 0 and 1", "blocked"))

        programs = self._artifact_path(artifacts, "tables/program_score_summary.csv")
        checks.append(self._check(f"{node_id}.program_score_summary_exists", bool(programs), "missing tables/program_score_summary.csv", "blocked"))
        if programs:
            rows, columns = self._read_csv(programs)
            required = {"subcluster", "program", "mean_score", "median_score", "n_cells"}
            missing = sorted(required - set(columns))
            valid_scores = bool(rows) and all(self._is_number(row.get("mean_score", "")) for row in rows)
            checks.append(self._check(f"{node_id}.program_score_summary_nonempty", bool(rows), "program_score_summary.csv is empty", "blocked"))
            checks.append(self._check(f"{node_id}.program_score_columns", not missing, f"missing columns: {', '.join(missing)}", "blocked"))
            checks.append(self._check(f"{node_id}.program_scores_numeric", valid_scores, "program mean_score values are missing or non-numeric", "blocked"))

        resolutions = self._artifact_path(artifacts, "tables/resolution_summary.csv")
        checks.append(self._check(f"{node_id}.resolution_summary_exists", bool(resolutions), "missing tables/resolution_summary.csv", "needs_fix"))
        if resolutions:
            rows, columns = self._read_csv(resolutions)
            selected_count = sum(str(row.get("selected", "")).lower() in {"true", "1", "yes"} for row in rows)
            valid_clusters = all(self._is_number(row.get("n_subclusters", "")) and float(row["n_subclusters"]) >= 2 for row in rows)
            checks.append(self._check(f"{node_id}.resolution_grid_has_multiple_values", len(rows) >= 2, "resolution_summary.csv must contain at least two tested resolutions", "needs_fix"))
            checks.append(self._check(f"{node_id}.resolution_summary_columns", {"resolution", "n_subclusters", "selected"}.issubset(columns), "resolution_summary.csv missing required columns", "needs_fix"))
            checks.append(self._check(f"{node_id}.resolution_single_selection", selected_count == 1, "resolution_summary.csv must identify exactly one selected resolution", "needs_fix"))
            checks.append(self._check(f"{node_id}.resolution_cluster_counts", valid_clusters, "each tested resolution must contain at least two subclusters", "needs_fix"))

        quality_path = self._artifact_path(artifacts, "qc/subcluster_quality_report.yaml")
        quality = read_yaml(quality_path) if quality_path else {}
        quality_status = str(quality.get("status", "missing"))
        checks.append(self._check(f"{node_id}.subcluster_quality_pass", quality_status == "pass", f"subcluster quality status is {quality_status}", "blocked"))
        subset_cells = self._numeric_value(quality.get("subset_cells"))
        input_cells = self._numeric_value(quality.get("input_cells"))
        subcluster_count = self._numeric_value(quality.get("subcluster_count"))
        subset_fraction = self._numeric_value(quality.get("subset_fraction"))
        checks.append(self._check(f"{node_id}.subset_cells_positive", subset_cells is not None and subset_cells > 0, "subcluster QC must report a positive subset cell count", "blocked"))
        checks.append(self._check(f"{node_id}.subcluster_count_valid", subcluster_count is not None and subcluster_count >= 2, "subcluster QC must report at least two subclusters", "blocked"))
        checks.append(self._check(f"{node_id}.input_cell_count_valid", input_cells is not None and subset_cells is not None and input_cells >= subset_cells, "subcluster QC must report an input cell count not smaller than the subset", "needs_fix"))
        checks.append(self._check(f"{node_id}.subset_fraction_valid", subset_fraction is not None and 0 < subset_fraction <= 1, "subcluster QC must report subset_fraction between 0 and 1", "needs_fix"))
        checks.append(self._check(f"{node_id}.subset_not_near_global", subset_fraction is not None and subset_fraction <= 0.9, "marker-driven subset contains more than 90% of input cells; review subset specificity", "needs_review"))
        checks.append(self._check(f"{node_id}.subset_rule_documented", bool(str(quality.get("subset_rule", "")).strip()), "subcluster QC missing subset_rule", "needs_fix"))
        if "marker" in str(quality.get("subset_rule", "")).lower():
            anchor_count = self._numeric_value(quality.get("min_anchor_markers"))
            checks.append(self._check(f"{node_id}.anchor_markers_documented", bool(str(quality.get("anchor_markers", "")).strip()), "marker-driven subset QC missing anchor_markers", "needs_fix"))
            checks.append(self._check(f"{node_id}.anchor_threshold_valid", anchor_count is not None and anchor_count >= 1, "marker-driven subset QC missing a positive min_anchor_markers threshold", "needs_fix"))
        checks.append(self._check(f"{node_id}.subcluster_object_exists", bool(self._artifact_path(artifacts, "objects/subcluster_seurat.rds")), "missing objects/subcluster_seurat.rds", "needs_fix"))
        checks.append(self._check(f"{node_id}.session_info_exists", bool(self._artifact_path(artifacts, "logs/sessionInfo.txt")), "missing logs/sessionInfo.txt", "needs_fix"))
        for figure in self.REQUIRED_SUBCLUSTER_FIGURES:
            figure_name = Path(figure).stem
            checks.append(self._check(f"{node_id}.{figure_name}_exists", bool(self._artifact_path(artifacts, figure)), f"missing or empty {figure}", "needs_fix"))
        next_plan["recommended_next_modules"].append("review subcluster stability and biological annotation before downstream differential claims")
        return checks

    def _check_source_maps(self, next_plan: dict[str, Any]) -> list[dict[str, Any]]:
        checks = []
        for name, key in [("figure_source_map.yaml", "figures"), ("table_source_map.yaml", "tables")]:
            data = read_yaml(self.run_dir / name)
            if not data:
                checks.append(self._check(f"{name}.exists", False, f"missing {name}", "needs_fix"))
                next_plan["human_review_items"].append(f"create {name} before evidence synthesis")
                continue
            items = data.get(key, []) if isinstance(data, dict) else []
            missing = [idx for idx, item in enumerate(items or []) if isinstance(item, dict) and not item.get("claim_boundary")]
            checks.append(self._check(f"{name}.claim_boundary_complete", not missing, f"{name} entries missing claim_boundary: {missing}", "needs_fix"))
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
            self._check("no_windows_personal_path_leak", not leaked_paths, f"path leaks: {', '.join(leaked_paths)}", "blocked"),
            self._check("adapted_external_module_no_hardcoded_disease_terms", not project_terms, f"project terms in external artifacts: {', '.join(project_terms)}", "needs_review"),
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
    def _is_number(value: str) -> bool:
        try:
            parsed = float(value)
        except (TypeError, ValueError):
            return False
        return parsed == parsed and parsed not in {float("inf"), float("-inf")}

    @staticmethod
    def _numeric_value(value: Any) -> float | None:
        try:
            parsed = float(value)
        except (TypeError, ValueError):
            return None
        if parsed != parsed or parsed in {float("inf"), float("-inf")}:
            return None
        return parsed

    @staticmethod
    def _overall_status(checks: list[dict[str, Any]]) -> str:
        status = "pass"
        for item in checks:
            current = str(item.get("status", "pass"))
            if QUALITY_STATUS_RANK.get(current, 0) > QUALITY_STATUS_RANK[status]:
                status = current
        return status

    def _fail_closed_decision(self, status: str, checks: list[dict[str, Any]]) -> dict[str, Any]:
        reasons = [
            {
                "check": item.get("name", ""),
                "status": item.get("status", ""),
                "message": item.get("message", ""),
            }
            for item in checks
            if item.get("status") != "pass"
        ]
        return {
            "schema_version": "fail_closed_decision.v1",
            "run_id": self.run_dir.name,
            "bioinformatics_quality_status": status,
            "final_status_must_not_be_pass": status != "pass",
            "reasons": reasons,
        }

    @staticmethod
    def _check(name: str, passed: bool, message: str, fail_status: str = "needs_review") -> dict[str, Any]:
        status = "pass" if passed else fail_status
        return {"name": name, "status": status, "message": "" if passed else message}
