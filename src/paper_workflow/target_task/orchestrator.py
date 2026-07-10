"""TargetTask planning, execution, evaluation, and packaging."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from paper_workflow.bioinformatics.analysis_graph import build_graph_from_selected_modules
from paper_workflow.bioinformatics.analysis_graph_executor import AnalysisGraphExecutor
from paper_workflow.bioinformatics.environment_registry import EnvironmentRegistry
from paper_workflow.bioinformatics.module_registry import ModuleRegistry
from paper_workflow.outputs.result_run_manager import ResultRunManager, read_yaml, utc_now, write_yaml
from paper_workflow.target_task.loader import load_target_task
from paper_workflow.target_task.reporting import write_target_reports
from paper_workflow.target_task.schema import validate_target_task


PBMC3K_MODULES = [
    "single_cell.seurat_pbmc3k_basic.v1",
    "single_cell.seurat_subcluster_programs.v1",
]


class TargetTaskOrchestrator:
    """Turn a TargetTask YAML into an auditable run-scoped workflow."""

    def __init__(self, project_root: Path):
        self.project_root = Path(project_root)
        self.registry = ModuleRegistry(self.project_root)
        self.environments = EnvironmentRegistry(self.project_root)

    def validate(self, target_path: Path | str, *, require_packages: bool = False) -> dict[str, Any]:
        target = load_target_task(target_path)
        schema = validate_target_task(target)
        required_envs = schema["required_envs"]
        env_reports = [
            self.environments.validate_environment(env_id, require_packages=require_packages)
            for env_id in required_envs
        ]
        required_modules = self._required_modules(target)
        module_reports = []
        for module_id in required_modules:
            module = self.registry.get(module_id)
            module_reports.append({
                "module_id": module_id,
                "exists": bool(module),
                "production_gate": self.registry.production_gate(module) if module else {"allowed": False, "reasons": ["module_missing"]},
                "issues": self.registry.validate_module(module_id) if module else [f"module not found: {module_id}"],
            })
        blocked_envs = [item for item in env_reports if item["status"] == "blocked"]
        return {
            "schema_version": "target_task_validation.v1",
            "target": str(target_path),
            "valid": bool(schema["valid"] and all(item["exists"] for item in module_reports)),
            "schema_issues": schema["issues"],
            "warnings": schema["warnings"],
            "target_id": schema["target_id"],
            "resolved_steps": schema["resolved_steps"],
            "required_modules": required_modules,
            "required_envs": required_envs,
            "environment_status": "blocked" if blocked_envs else "pass",
            "environment_reports": env_reports,
            "module_reports": module_reports,
            "claim_boundary": "present" if target.get("claim_boundary") else "missing",
        }

    def plan(self, target_path: Path | str) -> dict[str, Any]:
        target = load_target_task(target_path)
        validation = self.validate(target_path)
        if not validation["valid"]:
            raise ValueError("; ".join(validation["schema_issues"] + [issue for m in validation["module_reports"] for issue in m["issues"]]))
        paper_dir = self._paper_dir(target)
        self._ensure_paper_layout(paper_dir, target)
        manager = ResultRunManager(paper_dir)
        run_id = str(target["target_id"])
        manager.create_run(run_id, mode="analysis_design_mode", status="prepared", allow_existing=True)
        run_dir = manager.run_path(run_id)

        modules = self._selected_modules(target)
        data_path = self._resolved_input_path(target, paper_dir)
        graph_input_path = self._paper_relative_or_text(paper_dir, data_path)
        graph = build_graph_from_selected_modules(
            run_id=run_id,
            goal=str((target.get("analysis_goal") or {}).get("primary_goal", target.get("title", ""))),
            selected_modules=modules,
            input_paths=[graph_input_path],
            input_dir=graph_input_path,
            statistical_unit="cell",
            parameter_overrides=self._module_parameter_overrides(target),
        )
        graph.execution_policy.update({
            "require_user_approval": True,
            "require_data_registry": True,
            "require_env_lock": True,
            "require_node_input_bindings": True,
            "fail_closed": True,
        })
        graph.write(run_dir / "analysis_graph.yaml")
        write_yaml(run_dir / "target_task_resolved.yaml", self._resolved_target(target, data_path, modules))
        write_yaml(run_dir / "strategy_decision.yaml", self._strategy_decision(target, modules))
        self._write_data_registry(paper_dir, target, data_path)
        (run_dir / "method_selection_report.md").write_text(self._method_selection_report(target, modules), encoding="utf-8")
        manifest = read_yaml(run_dir / "run_manifest.yaml")
        manifest.update({
            "schema_version": "target_task_run.v1",
            "run_id": run_id,
            "target_task": self._project_relative_or_text(Path(target_path)),
            "status": "prepared",
            "mode": "analysis_design_mode",
            "evidence_grade": target.get("evidence_grade", "workflow_test"),
            "claim_boundary": target.get("claim_boundary", ""),
            "analysis_graph": "analysis_graph.yaml",
            "data_registry": "data/data_registry/datasets.yaml",
            "outputs_generated": [
                "analysis_graph.yaml",
                "target_task_resolved.yaml",
                "strategy_decision.yaml",
                "method_selection_report.md",
            ],
        })
        write_yaml(run_dir / "run_manifest.yaml", manifest)
        return {
            "status": "planned",
            "target_id": run_id,
            "paper_dir": str(paper_dir),
            "run_dir": str(run_dir),
            "analysis_graph": str(run_dir / "analysis_graph.yaml"),
            "strategy_decision": str(run_dir / "strategy_decision.yaml"),
        }

    def run(self, target_path: Path | str, *, approved: bool = False, execute: bool = False) -> dict[str, Any]:
        if execute and not approved:
            raise PermissionError("--execute requires --approved for TargetTask real execution")
        plan = self.plan(target_path)
        target = load_target_task(target_path)
        paper_dir = Path(plan["paper_dir"])
        run_dir = Path(plan["run_dir"])
        run_id = str(target["target_id"])
        if execute:
            env_validation = self.validate(target_path, require_packages=True)
            if env_validation["environment_status"] == "blocked":
                self._write_blocked_run(run_dir, target, env_validation)
                evaluation = ResultRunManager(paper_dir).evaluate_run(run_id, write_report=True).to_dict()
                report_paths = write_target_reports(run_dir, target, evaluation)
                return {
                    "status": "blocked",
                    "run_id": run_id,
                    "block_reason": "environment_blocked",
                    "environment_reports": env_validation["environment_reports"],
                    "evaluation": evaluation,
                    "reports": report_paths,
                }

        graph = build_graph_from_selected_modules(
            run_id=run_id,
            goal=str((target.get("analysis_goal") or {}).get("primary_goal", target.get("title", ""))),
            selected_modules=self._selected_modules(target),
            input_paths=[self._paper_relative_or_text(paper_dir, self._resolved_input_path(target, paper_dir))],
            input_dir=self._paper_relative_or_text(paper_dir, self._resolved_input_path(target, paper_dir)),
            statistical_unit="cell",
            parameter_overrides=self._module_parameter_overrides(target),
        )
        graph.execution_policy.update(read_yaml(run_dir / "analysis_graph.yaml").get("execution_policy", {}))
        result = AnalysisGraphExecutor(self.project_root).run(graph, run_dir, execute=execute, approval=approved)
        evaluation = ResultRunManager(paper_dir).evaluate_run(run_id, write_report=True).to_dict()
        report_paths = write_target_reports(run_dir, target, evaluation)
        report_paths_for_manifest = {
            key: self._project_relative_or_text(Path(value)) for key, value in report_paths.items()
        }
        write_yaml(
            run_dir / "target_run_report.yaml",
            {
                "schema_version": "target_task_run_report.v1",
                "target_id": run_id,
                "graph_run": result.to_dict(),
                "evaluation_status": evaluation.get("evaluation_status", {}),
                "reports": report_paths_for_manifest,
                "updated_at": utc_now(),
            },
        )
        return {
            "status": evaluation.get("status", result.status),
            "run_id": run_id,
            "graph_run": result.to_dict(),
            "evaluation": evaluation,
            "reports": report_paths,
        }

    def evaluate(self, target_path: Path | str, *, fail_closed: bool = True) -> dict[str, Any]:
        target = load_target_task(target_path)
        paper_dir = self._paper_dir(target)
        run_id = str(target["target_id"])
        evaluation = ResultRunManager(paper_dir).evaluate_run(run_id, write_report=True).to_dict()
        if fail_closed and evaluation.get("bioinformatics_quality_status") != "pass" and evaluation["status"] == "pass":
            evaluation["status"] = "needs_fix"
            evaluation.setdefault("evaluation_status", {})["final_status"] = "needs_fix"
        return evaluation

    def package(self, target_path: Path | str) -> dict[str, Any]:
        target = load_target_task(target_path)
        paper_dir = self._paper_dir(target)
        run_dir = ResultRunManager(paper_dir).run_path(str(target["target_id"]))
        evaluation = ResultRunManager(paper_dir).evaluate_run(str(target["target_id"]), write_report=True).to_dict()
        package_manifest = {
            "schema_version": "target_task_package.v1",
            "target_id": target["target_id"],
            "run_dir": self._project_relative_or_text(run_dir),
            "final_status": evaluation.get("status", "unknown"),
            "evidence_grade": target.get("evidence_grade", ""),
            "scientific_claim_permission": "exploratory_only" if evaluation.get("status") == "pass" else "no_claim_until_fail_closed_passes",
            "required_artifacts": self._required_package_artifacts(run_dir),
            "updated_at": utc_now(),
        }
        write_yaml(run_dir / "target_task_package.yaml", package_manifest)
        return package_manifest

    def _required_modules(self, target: dict[str, Any]) -> list[str]:
        workflow_steps = [str(step) for step in ((target.get("workflow") or {}).get("steps", []) or [])]
        if "subcluster_reanalysis" in workflow_steps or "PBMC3K" in str(target.get("title", "")):
            return PBMC3K_MODULES
        return list((target.get("workflow") or {}).get("required_modules", []) or [])

    def _selected_modules(self, target: dict[str, Any]) -> list[dict[str, Any]]:
        modules = []
        for module_id in self._required_modules(target):
            module = self.registry.get(module_id)
            if module_id == "single_cell.seurat_pbmc3k_basic.v1":
                module.setdefault("output_bindings", {})["seurat_rds"] = "objects/pbmc3k_seurat_basic.rds"
            modules.append(module)
        return modules

    def _module_parameter_overrides(self, target: dict[str, Any]) -> dict[str, dict[str, Any]]:
        """Map researcher-facing parameter groups to concrete module arguments."""
        parameters = target.get("parameters") or {}
        explicit = parameters.get("module_overrides") or {}
        overrides: dict[str, dict[str, Any]] = {
            str(module_id): dict(values or {})
            for module_id, values in explicit.items()
            if isinstance(values, dict)
        }

        basic_id = "single_cell.seurat_pbmc3k_basic.v1"
        basic = overrides.setdefault(basic_id, {})
        basic.update(self._normalized_parameters(parameters.get("qc") or {}))
        basic.update(self._normalized_parameters(parameters.get("clustering") or {}))

        subcluster_id = "single_cell.seurat_subcluster_programs.v1"
        subcluster = overrides.setdefault(subcluster_id, {})
        subcluster.update(self._normalized_parameters(parameters.get("subclustering") or {}))

        subset = parameters.get("t_cell_subset") or {}
        subset_aliases = {
            "minimum_detected_markers": "min_subset_markers",
            "anchor_markers": "subset_anchor_markers",
            "minimum_detected_anchors": "min_anchor_markers",
        }
        for key, value in subset.items():
            subcluster[subset_aliases.get(str(key), str(key))] = self._command_value(value)

        marker = parameters.get("marker_detection") or {}
        supported_tests = {"wilcox", "bimod", "roc", "t", "negbinom", "poisson", "lr", "mast", "deseq2"}
        for key, value in marker.items():
            normalized_key = str(key)
            if normalized_key == "method":
                # FindAllMarkers describes the operation; test.use still defaults to wilcox.
                if str(value).lower() in supported_tests:
                    subcluster["marker_method"] = value
                continue
            if normalized_key in {"test", "test_use", "test.use"}:
                subcluster["marker_method"] = value
                continue
            subcluster[normalized_key] = self._command_value(value)

        programs = (parameters.get("program_scoring") or {}).get("programs") or parameters.get("programs") or {}
        if programs:
            subcluster["program_spec"] = self._program_spec(programs)

        required = set(self._required_modules(target))
        return {module_id: values for module_id, values in overrides.items() if module_id in required and values}

    @classmethod
    def _normalized_parameters(cls, values: dict[str, Any]) -> dict[str, Any]:
        return {str(key): cls._command_value(value) for key, value in values.items()}

    @staticmethod
    def _command_value(value: Any) -> Any:
        if isinstance(value, bool):
            return str(value).lower()
        if isinstance(value, (list, tuple)):
            return ",".join(str(item) for item in value)
        return value

    @classmethod
    def _program_spec(cls, programs: dict[str, Any]) -> str:
        return ";".join(
            f"{name}={cls._command_value(genes)}"
            for name, genes in programs.items()
            if str(name).strip() and genes
        )

    def _paper_dir(self, target: dict[str, Any]) -> Path:
        target_id = str(target.get("target_id", "target_task"))
        paper_id = re.sub(r"_\d{8}_v\d+$", "", target_id)
        return self.project_root / "papers" / paper_id

    def _ensure_paper_layout(self, paper_dir: Path, target: dict[str, Any]) -> None:
        paper_dir.mkdir(parents=True, exist_ok=True)
        passport = paper_dir / "project_passport.yaml"
        if not passport.exists():
            write_yaml(
                passport,
                {
                    "paper_id": paper_dir.name,
                    "pipeline_state": "target_task_workflow_test",
                    "target_task": target.get("target_id", ""),
                    "evidence_grade": target.get("evidence_grade", "workflow_test"),
                    "created_at": utc_now(),
                },
            )

    def _resolved_input_path(self, target: dict[str, Any], paper_dir: Path) -> Path:
        input_path = Path(str((target.get("data") or {}).get("input_path", "")))
        project_candidate = self.project_root / input_path
        paper_candidate = paper_dir / input_path
        if project_candidate.exists():
            return project_candidate.resolve()
        if paper_candidate.exists():
            return paper_candidate.resolve()
        return project_candidate.resolve()

    def _write_data_registry(self, paper_dir: Path, target: dict[str, Any], data_path: Path) -> None:
        data = target.get("data") or {}
        rel_path = self._paper_relative_or_text(paper_dir, data_path)
        write_yaml(
            paper_dir / "data" / "data_registry" / "datasets.yaml",
            {
                "schema_version": "data_registry.v1",
                "status": "declared",
                "datasets": [
                    {
                        "dataset_id": data.get("dataset_id", "target_dataset"),
                        "modality": data.get("modality", "single_cell"),
                        "format": data.get("format", ""),
                        "path": rel_path,
                        "immutable": bool(data.get("immutable", True)),
                        "role": data.get("role", "tutorial_fixture"),
                        "sample_mapping": {"status": "not_required_for_tutorial"},
                    }
                ],
            },
        )

    def _resolved_target(self, target: dict[str, Any], data_path: Path, modules: list[dict[str, Any]]) -> dict[str, Any]:
        return {
            "schema_version": "target_task_resolved.v1",
            "target_id": target.get("target_id", ""),
            "title": target.get("title", ""),
            "claim_boundary": target.get("claim_boundary", ""),
            "evidence_grade": target.get("evidence_grade", ""),
            "resolved_input_path": self._project_relative_or_text(data_path),
            "required_modules": [module.get("id") or module.get("module_id") for module in modules],
            "quality_gates": target.get("quality_gates", {}),
            "parameters": target.get("parameters", {}),
            "module_parameter_overrides": self._module_parameter_overrides(target),
            "resolved_at": utc_now(),
        }

    def _strategy_decision(self, target: dict[str, Any], modules: list[dict[str, Any]]) -> dict[str, Any]:
        recommended = []
        blocked_by_grade = []
        blocked_by_environment = []
        for module in modules:
            gate = self.registry.production_gate(module)
            item = {
                "module": module.get("id") or module.get("module_id"),
                "grade": module.get("production_capability_grade", ""),
                "claim_permission": module.get("claim_permission", ""),
                "reason": "required by TargetTask workflow",
            }
            if gate["allowed"]:
                recommended.append(item)
            else:
                blocked_by_grade.append({**item, "blockers": gate["reasons"]})
            if module.get("current_environment_status") == "blocked":
                blocked_by_environment.append(item)
        return {
            "schema_version": "strategy_decision.v1",
            "current_goal": (target.get("analysis_goal") or {}).get("primary_goal", target.get("title", "")),
            "recommended_now": recommended,
            "deferred_until_environment_ready": blocked_by_environment,
            "planning_only": [],
            "blocked_by_environment": blocked_by_environment,
            "blocked_by_grade": blocked_by_grade,
            "forbidden_as_primary": [
                {"module": "bulk_rnaseq.wgcna.v1", "reason": "WGCNA does not replace primary group DE"},
            ],
            "downstream_allowed": [
                {"module": "bulk_rnaseq.fgsea_enrichment.v1", "prerequisite": "ranked_gene_statistic exists"},
            ],
        }

    def _method_selection_report(self, target: dict[str, Any], modules: list[dict[str, Any]]) -> str:
        lines = [
            "# TargetTask Method Selection Report",
            "",
            f"Target: {target.get('target_id', '')}",
            f"Goal: {(target.get('analysis_goal') or {}).get('primary_goal', '')}",
            "",
        ]
        for module in modules:
            gate = self.registry.production_gate(module)
            lines.extend([
                f"## {module.get('id') or module.get('module_id')}",
                "",
                f"- Production grade: {module.get('production_capability_grade', '')}",
                f"- Evidence level: {module.get('execution_evidence_level', '')}",
                f"- Strategy visibility: {module.get('strategy_visibility', '')}",
                f"- Claim permission: {module.get('claim_permission', '')}",
                f"- Gate: {'allowed' if gate['allowed'] else 'blocked'}",
                f"- Gate reasons: {', '.join(gate['reasons']) or 'none'}",
                f"- Claim boundary: {module.get('claim_boundary', '')}",
                "",
            ])
        return "\n".join(lines)

    def _write_blocked_run(self, run_dir: Path, target: dict[str, Any], validation: dict[str, Any]) -> None:
        manifest = read_yaml(run_dir / "run_manifest.yaml")
        manifest.update({
            "schema_version": "target_task_run.v1",
            "run_id": target.get("target_id", ""),
            "mode": "execution_mode",
            "status": "blocked",
            "execution_status": "blocked",
            "block_reason": "environment_blocked",
            "environment_reports": validation.get("environment_reports", []),
            "errors": [
                issue
                for report in validation.get("environment_reports", [])
                for issue in report.get("issues", [])
            ],
            "updated_at": utc_now(),
        })
        write_yaml(run_dir / "run_manifest.yaml", manifest)
        write_yaml(
            run_dir / "qc" / "next_analysis_plan.yaml",
            {
                "schema_version": "next_analysis_plan.v1",
                "current_run_status": "blocked",
                "blocking_issues": manifest["errors"] or ["environment blocked"],
                "recommended_next_modules": [],
                "human_review_items": ["install missing packages or rerun with a compatible environment"],
            },
        )

    def _required_package_artifacts(self, run_dir: Path) -> list[dict[str, Any]]:
        required = [
            "run_manifest.yaml",
            "analysis_graph.yaml",
            "target_task_resolved.yaml",
            "strategy_decision.yaml",
            "evaluation_report.yaml",
            "qc/bioinformatics_quality_report.yaml",
            "qc/fail_closed_decision.yaml",
            "qc/next_analysis_plan.yaml",
            "tables/evidence_matrix.tsv",
            "brief/FIGURE_STORYLINE.md",
            "manuscript/methods_draft.md",
            "manuscript/results_skeleton.md",
            "figure_source_map.yaml",
            "table_source_map.yaml",
        ]
        return [{"path": item, "exists": (run_dir / item).exists()} for item in required]

    def _project_relative_or_text(self, path: Path) -> str:
        try:
            return str(path.resolve().relative_to(self.project_root.resolve())).replace("\\", "/")
        except ValueError:
            return str(path).replace("\\", "/")

    @staticmethod
    def _paper_relative_or_text(paper_dir: Path, path: Path) -> str:
        try:
            return str(path.resolve().relative_to(paper_dir.resolve())).replace("\\", "/")
        except ValueError:
            try:
                return str(Path("..") / ".." / path.resolve().relative_to(paper_dir.parent.parent.resolve())).replace("\\", "/")
            except ValueError:
                return str(path).replace("\\", "/")
