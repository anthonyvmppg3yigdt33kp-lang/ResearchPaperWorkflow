"""Run-scoped result management for paper projects.

This module keeps exploratory and production analysis outputs discoverable by
requiring a stable ``results/runs/<run_id>/`` layout plus a small
``results/current_run.yaml`` pointer.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

import yaml

from paper_workflow.bioinformatics.analysis_graph import build_graph_from_selected_modules
from paper_workflow.bioinformatics.module_selector import MethodSelector, render_selection_report
from paper_workflow.outputs.source_map import SourceMapValidator


RUN_ID_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_-]*_[0-9]{8}_v[0-9]+$")
REQUIRES_HUMAN_INPUT = "requires_human_input"


def utc_now() -> str:
    """Return an ISO-8601 UTC timestamp."""
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def read_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh) or {}
    if not isinstance(data, dict):
        return {}
    return data


def write_yaml(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        yaml.safe_dump(data, fh, allow_unicode=True, sort_keys=False)


@dataclass
class RunEvaluation:
    """Lightweight quality summary for a result run."""

    run_id: str
    run_path: str
    status: str
    missing_required_files: list[str]
    output_file_count: int
    output_size_bytes: int
    has_figure_source_map: bool
    has_table_source_map: bool
    manifest_status: str
    node_count: int = 0
    completed_node_count: int = 0
    blocked_node_count: int = 0
    failed_node_count: int = 0
    has_analysis_graph: bool = False
    has_method_selection_report: bool = False
    has_node_manifests: bool = False
    has_environment_report: bool = False
    has_data_registry_hash: bool = False
    source_map_valid: bool = False
    source_map_issue_count: int = 0
    source_map_issues: list[str] = None
    stderr_warning_count: int = 0
    claim_boundary_complete: bool = False
    reproducibility_grade: str = "not_evaluated"
    evidence_grade: str = "exploratory"
    reviewer_risk_count: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "run_path": self.run_path,
            "status": self.status,
            "missing_required_files": self.missing_required_files,
            "output_file_count": self.output_file_count,
            "output_size_bytes": self.output_size_bytes,
            "has_figure_source_map": self.has_figure_source_map,
            "has_table_source_map": self.has_table_source_map,
            "manifest_status": self.manifest_status,
            "node_count": self.node_count,
            "completed_node_count": self.completed_node_count,
            "blocked_node_count": self.blocked_node_count,
            "failed_node_count": self.failed_node_count,
            "has_analysis_graph": self.has_analysis_graph,
            "has_method_selection_report": self.has_method_selection_report,
            "has_node_manifests": self.has_node_manifests,
            "has_environment_report": self.has_environment_report,
            "has_data_registry_hash": self.has_data_registry_hash,
            "source_map_valid": self.source_map_valid,
            "source_map_issue_count": self.source_map_issue_count,
            "source_map_issues": self.source_map_issues or [],
            "stderr_warning_count": self.stderr_warning_count,
            "claim_boundary_complete": self.claim_boundary_complete,
            "reproducibility_grade": self.reproducibility_grade,
            "evidence_grade": self.evidence_grade,
            "reviewer_risk_count": self.reviewer_risk_count,
        }


class ResultRunManager:
    """Create, point to, and evaluate run-scoped result directories."""

    REQUIRED_RUN_FILES = [
        "run_manifest.yaml",
        "parameters.yaml",
        "inputs_manifest.yaml",
        "outputs_manifest.yaml",
    ]

    def __init__(self, paper_dir: Path):
        self.paper_dir = Path(paper_dir)
        self.results_dir = self.paper_dir / "results"
        self.runs_dir = self.results_dir / "runs"
        self.current_run_file = self.results_dir / "current_run.yaml"
        self.current_pointer_dir = self.results_dir / "current"

    @staticmethod
    def validate_run_id(run_id: str) -> None:
        if not RUN_ID_RE.match(run_id):
            raise ValueError(
                "run_id must match <project_or_analysis>_<YYYYMMDD>_v<N>, "
                "for example bulk_de_20260707_v1"
            )

    def run_path(self, run_id: str) -> Path:
        self.validate_run_id(run_id)
        return self.runs_dir / run_id

    def create_run(
        self,
        run_id: str,
        mode: str = "analysis_design_mode",
        status: str = "prepared",
        notes: str = "",
        allow_existing: bool = False,
    ) -> dict[str, Any]:
        """Create a new run directory with baseline manifests."""
        run_dir = self.run_path(run_id)
        if run_dir.exists() and not allow_existing:
            raise FileExistsError(f"Run already exists: {run_dir}")

        for subdir in ["logs", "qc", "tables", "figures"]:
            (run_dir / subdir).mkdir(parents=True, exist_ok=True)

        manifest = {
            "schema_version": "1.0.0",
            "run_id": run_id,
            "mode": mode,
            "status": status,
            "created_at": utc_now(),
            "paper_dir": str(self.paper_dir),
            "outputs_generated": [],
            "notes": notes,
        }
        if not (run_dir / "run_manifest.yaml").exists():
            write_yaml(run_dir / "run_manifest.yaml", manifest)

        for name, payload in {
            "parameters.yaml": {"parameters": {}, "created_at": utc_now()},
            "inputs_manifest.yaml": {"inputs": [], "created_at": utc_now()},
            "outputs_manifest.yaml": {"outputs": [], "created_at": utc_now()},
        }.items():
            path = run_dir / name
            if not path.exists():
                write_yaml(path, payload)

        intent = run_dir / "intent_packet.md"
        if not intent.exists():
            intent.write_text(
                "# Intent Packet\n\n"
                f"- Mode: `{mode}`\n"
                f"- Run ID: `{run_id}`\n"
                f"- Status: `{status}`\n"
                f"- Created: `{manifest['created_at']}`\n"
                f"- Notes: {notes or 'not_provided'}\n",
                encoding="utf-8",
            )

        return manifest

    def set_current_run(
        self,
        run_id: str,
        status: str = "prepared",
        user_approved: bool = False,
        notes: str = "",
        source_manifest: str = "run_manifest.yaml",
    ) -> dict[str, Any]:
        """Update ``results/current_run.yaml`` and the lightweight pointer file."""
        run_dir = self.run_path(run_id)
        if not run_dir.exists():
            raise FileNotFoundError(f"Run does not exist: {run_dir}")

        previous = read_yaml(self.current_run_file)
        current = {
            "paper_id": self.paper_dir.name,
            "active_run_id": run_id,
            "active_run_path": str(run_dir),
            "status": status,
            "workflow_truth": str(self.paper_dir / "project_passport.yaml"),
            "updated_at": utc_now(),
            "source_manifest": str(run_dir / source_manifest),
            "supporting_runs": [],
            "previous_current": previous.get("active_run_id", ""),
            "user_approved": bool(user_approved),
            "notes": notes,
        }
        write_yaml(self.current_run_file, current)

        self.current_pointer_dir.mkdir(parents=True, exist_ok=True)
        (self.current_pointer_dir / "RUN_POINTER.txt").write_text(
            str(run_dir),
            encoding="utf-8",
        )
        return current

    def get_current_run(self) -> dict[str, Any]:
        return read_yaml(self.current_run_file)

    def write_analysis_design(
        self,
        run_id: str,
        goal: str,
        modality: str,
        inputs: Optional[list[str]] = None,
        forbidden_actions: Optional[list[str]] = None,
        primary_contrast: str = REQUIRES_HUMAN_INPUT,
        group_column: str = "condition",
        sample_id_column: str = "sample_id",
        execution_backend: str = "dry_run",
        from_code_library: bool = False,
    ) -> dict[str, Any]:
        """Write a dry-run analysis design skeleton without executing analysis."""
        run_dir = self.run_path(run_id)
        if not run_dir.exists():
            self.create_run(run_id, mode="analysis_design_mode")

        selected_modules: list[dict[str, Any]] = []
        graph_payload: dict[str, Any] = {}
        normalized_modality = modality.lower().replace("-", "_")
        graph_requested = from_code_library or normalized_modality in {
            "scrna",
            "single_cell",
            "single_cell_rna",
            "multiomics",
            "multi_omics",
            "spatial",
        }
        if graph_requested:
            project_root = self.paper_dir.parents[1]
            selector = MethodSelector(project_root=project_root, paper_dir=self.paper_dir)
            selected_modules = selector.select(goal=goal, modalities=[modality], max_modules=4)
            if selected_modules:
                graph = build_graph_from_selected_modules(
                    run_id=run_id,
                    goal=goal,
                    selected_modules=selected_modules,
                    input_dir=(inputs or [""])[0] if inputs else "",
                    statistical_unit="sample",
                )
                graph_payload = graph.to_dict()
                graph.write(run_dir / "analysis_graph.yaml")
                (run_dir / "method_selection_report.md").write_text(
                    render_selection_report(goal, selected_modules),
                    encoding="utf-8",
                )

        design = {
            "schema_version": "1.0.0",
            "run_id": run_id,
            "mode": "analysis_design_mode",
            "goal": goal,
            "modality": modality,
            "research_question": goal,
            "primary_contrast": primary_contrast,
            "data_type": modality,
            "statistical_unit": "sample",
            "inputs": inputs or [],
            "inclusion_exclusion": [REQUIRES_HUMAN_INPUT],
            "covariates": [],
            "batch_or_confounder_plan": REQUIRES_HUMAN_INPUT,
            "normalization_or_preprocessing": self._default_preprocessing(modality),
            "primary_methods": self._default_methods(modality),
            "validation_plan": ["human review before execution", "run manifest review"],
            "sensitivity_plan": [REQUIRES_HUMAN_INPUT],
            "expected_outputs": self._default_expected_outputs(modality),
            "user_approval": False,
            "execution_backend": execution_backend,
            "group_column": group_column,
            "sample_id_column": sample_id_column,
            "data_requirements": [
                {
                    "role": "primary_input",
                    "path": item,
                    "status": "declared" if item else "not_declared",
                }
                for item in (inputs or [])
            ],
            "environment_requirements": [
                {
                    "env_id": str((module.get("environment") or {}).get("env_id", "")),
                    "module_id": str(module.get("id") or module.get("module_id", "")),
                    "status": (module.get("method_selection_score") or {}).get("environment_status", "unknown"),
                }
                for module in selected_modules
            ],
            "module_candidates": [
                {
                    "module_id": str(module.get("id") or module.get("module_id", "")),
                    "score": (module.get("method_selection_score") or {}).get("total"),
                    "environment": (module.get("method_selection_score") or {}).get("environment_status"),
                    "claim_boundary": module.get("claim_boundary", ""),
                }
                for module in selected_modules
            ],
            "selected_modules": [
                {
                    "module_id": str(module.get("id") or module.get("module_id", "")),
                    "step": module.get("step", ""),
                    "language": module.get("language", ""),
                    "source_path": (module.get("source") or {}).get("path", ""),
                }
                for module in selected_modules
            ],
            "analysis_graph": graph_payload.get("analysis_graph", {}),
            "data_bindings": graph_payload.get("data_bindings", {}),
            "execution_policy": graph_payload.get("execution_policy", {}),
            "figure_plan_bindings": [
                {
                    "module_id": str(module.get("id") or module.get("module_id", "")),
                    "figures": module.get("figure_outputs", []) or [],
                }
                for module in selected_modules
            ],
            "reviewer_risk": [
                {
                    "module_id": str(module.get("id") or module.get("module_id", "")),
                    "risks": module.get("reviewer_risk", []) or [],
                    "boundary": module.get("claim_boundary", ""),
                }
                for module in selected_modules
            ],
            "forbidden_actions": forbidden_actions or [
                "run analysis before approval",
                "install packages during agent phase",
                "write outside results/runs/<run_id>/",
            ],
            "required_human_checkpoint": True,
            "execution_status": "not_executed",
            "created_at": utc_now(),
        }
        write_yaml(run_dir / "analysis_design.yaml", design)
        return design

    @staticmethod
    def _default_preprocessing(modality: str) -> list[str]:
        if modality == "bulk_rnaseq":
            return ["count matrix validation", "sample metadata validation", "library-size normalization"]
        if modality == "scrna":
            return ["cell QC", "normalization", "variable feature selection", "PCA/UMAP", "feature visualization"]
        if modality == "spatial":
            return ["spatial QC", "coordinate validation"]
        return ["requires_modality_specific_preprocessing_plan"]

    @staticmethod
    def _default_methods(modality: str) -> list[str]:
        if modality == "bulk_rnaseq":
            return ["DESeq2 negative-binomial GLM", "Benjamini-Hochberg FDR"]
        if modality == "scrna":
            return ["method asset selected from code_library/module_registry.yaml"]
        if modality == "spatial":
            return ["Squidpy or Seurat spatial workflow selected after data audit"]
        return ["requires_method_selection"]

    @staticmethod
    def _default_expected_outputs(modality: str) -> list[str]:
        if modality == "bulk_rnaseq":
            return [
                "differential expression table",
                "normalization/QC report",
                "volcano plot",
                "DEG heatmap",
                "run manifest",
            ]
        if modality == "scrna":
            return [
                "qc metrics table",
                "filtered Seurat object",
                "PCA/UMAP plots",
                "marker feature plots",
                "session info",
                "run manifest",
            ]
        return ["run manifest", "parameters", "outputs manifest", "quality report"]

    def evaluate_run(self, run_id: str, write_report: bool = False) -> RunEvaluation:
        """Evaluate baseline completeness of a run directory."""
        run_dir = self.run_path(run_id)
        if not run_dir.exists():
            raise FileNotFoundError(f"Run does not exist: {run_dir}")

        missing = [
            name for name in self.REQUIRED_RUN_FILES
            if not (run_dir / name).exists()
        ]
        files = [p for p in run_dir.rglob("*") if p.is_file()]
        total_size = sum(p.stat().st_size for p in files)
        manifest = read_yaml(run_dir / "run_manifest.yaml")
        manifest_status = str(manifest.get("status", "missing"))
        nodes = list(manifest.get("nodes", []) or [])
        completed_nodes = [n for n in nodes if n.get("status") == "completed"]
        blocked_nodes = [n for n in nodes if n.get("status") == "blocked"]
        failed_nodes = [n for n in nodes if n.get("status") in {"failed", "error"}]
        node_manifest_count = len(list((run_dir / "nodes").glob("*/*node_manifest.yaml"))) if (run_dir / "nodes").exists() else 0
        source_status = SourceMapValidator().validate_run(run_dir)
        stderr_warning_count = 0
        for stderr_path in run_dir.rglob("stderr.log"):
            text = stderr_path.read_text(encoding="utf-8", errors="replace").lower()
            stderr_warning_count += text.count("warning")
        has_analysis_graph = (run_dir / "analysis_graph.yaml").exists() or bool(manifest.get("analysis_graph"))
        reproducibility_grade = str(manifest.get("environment_reproducibility_grade", "not_evaluated"))
        data_status = manifest.get("data_status") if isinstance(manifest.get("data_status"), dict) else {}
        evidence_grade = str(data_status.get("evidence_grade", manifest.get("evidence_grade", "exploratory")))
        reviewer_risk_count = 0
        for record in nodes:
            module_risk = record.get("module_reviewer_risk", [])
            if isinstance(module_risk, list):
                reviewer_risk_count += len(module_risk)
        for source_map_name in ["figure_source_map.yaml", "table_source_map.yaml"]:
            source_map = read_yaml(run_dir / source_map_name)
            for key in ["figures", "tables"]:
                for item in source_map.get(key, []) or []:
                    risk = item.get("module_reviewer_risk") or item.get("reviewer_risk") or []
                    reviewer_risk_count += len(risk) if isinstance(risk, list) else int(bool(risk))

        if manifest_status == "blocked" or manifest.get("execution_status") == "blocked" or blocked_nodes or failed_nodes:
            status = "blocked"
        elif missing or source_status["status"] != "pass":
            status = "needs_fix"
        elif has_analysis_graph and reproducibility_grade == "degraded":
            status = "degraded_exploratory"
        else:
            status = "pass"

        evaluation = RunEvaluation(
            run_id=run_id,
            run_path=str(run_dir),
            status=status,
            missing_required_files=missing,
            output_file_count=len(files),
            output_size_bytes=total_size,
            has_figure_source_map=(run_dir / "figure_source_map.yaml").exists(),
            has_table_source_map=(run_dir / "table_source_map.yaml").exists(),
            manifest_status=manifest_status,
            node_count=len(nodes),
            completed_node_count=len(completed_nodes),
            blocked_node_count=len(blocked_nodes),
            failed_node_count=len(failed_nodes),
            has_analysis_graph=has_analysis_graph,
            has_method_selection_report=(run_dir / "method_selection_report.md").exists(),
            has_node_manifests=bool(nodes) and node_manifest_count >= len(nodes),
            has_environment_report=bool(manifest.get("environment_registry") or manifest.get("node_environment")),
            has_data_registry_hash=bool(manifest.get("data_registry_hash")),
            source_map_valid=source_status["status"] == "pass",
            source_map_issue_count=int(source_status["issue_count"]),
            source_map_issues=list(source_status["issues"]),
            stderr_warning_count=stderr_warning_count,
            claim_boundary_complete=not any("claim_boundary" in issue for issue in source_status["issues"]),
            reproducibility_grade=reproducibility_grade,
            evidence_grade=evidence_grade,
            reviewer_risk_count=reviewer_risk_count,
        )
        if write_report:
            write_yaml(run_dir / "evaluation_report.yaml", evaluation.to_dict())
        return evaluation

    def brief_status(self) -> dict[str, Any]:
        """Return a compact status packet for progress reporting."""
        passport = read_yaml(self.paper_dir / "project_passport.yaml")
        brief_path = self.paper_dir / "brief" / "STAGE_SUMMARY.md"
        return {
            "paper_id": self.paper_dir.name,
            "paper_dir": str(self.paper_dir),
            "pipeline_state": passport.get("pipeline_state", "unknown"),
            "current_run": self.get_current_run(),
            "brief_path": str(brief_path) if brief_path.exists() else "",
            "truth_source": str(self.paper_dir / "project_passport.yaml"),
        }
