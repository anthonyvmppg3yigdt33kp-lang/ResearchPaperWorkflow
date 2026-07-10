"""Execute approved analysis graphs with source maps and per-node manifests."""

from __future__ import annotations

import csv
import subprocess
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path
from time import perf_counter
from typing import Any

import yaml

from paper_workflow.bioinformatics.analysis_graph import AnalysisGraph, build_node_input_contract, unresolved_required_inputs
from paper_workflow.bioinformatics.data_registry import DataRegistry
from paper_workflow.bioinformatics.environment_registry import EnvironmentRegistry
from paper_workflow.bioinformatics.module_registry import ModuleRegistry
from paper_workflow.outputs.source_map import SourceMapValidator, read_source_map
from paper_workflow.outputs.result_run_manager import read_yaml, utc_now, write_yaml


@dataclass
class GraphRunResult:
    status: str
    run_id: str
    artifacts: list[dict[str, str]]
    metrics: dict[str, Any]
    warnings: list[str]
    errors: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "run_id": self.run_id,
            "artifacts": self.artifacts,
            "metrics": self.metrics,
            "warnings": self.warnings,
            "errors": self.errors,
        }


def _find_project_root(path: Path) -> Path:
    current = Path(path).resolve()
    for candidate in [current, *current.parents]:
        if (candidate / "AGENTS.md").exists() and (candidate / "src").exists():
            return candidate
    return current


def _artifact(path: Path, paper_dir: Path, stage: str = "run_analysis") -> dict[str, str]:
    suffix = path.suffix.lower()
    mime = "text/plain"
    if suffix in {".yaml", ".yml"}:
        mime = "application/yaml"
    elif suffix == ".md":
        mime = "text/markdown"
    elif suffix == ".csv":
        mime = "text/csv"
    elif suffix in {".png", ".jpg", ".jpeg"}:
        mime = f"image/{suffix[1:].replace('jpg', 'jpeg')}"
    elif suffix == ".pdf":
        mime = "application/pdf"
    elif suffix == ".rds":
        mime = "application/octet-stream"
    return {"path": str(path.relative_to(paper_dir)).replace("\\", "/"), "mime_type": mime, "source_stage": stage}


class AnalysisGraphExecutor:
    """Run a graph node-by-node without mutating raw data."""

    def __init__(self, project_root: Path):
        self.project_root = _find_project_root(project_root)
        self.modules = ModuleRegistry(self.project_root)
        self.environments = EnvironmentRegistry(self.project_root)

    def run(
        self,
        graph: AnalysisGraph,
        run_dir: Path,
        execute: bool = False,
        approval: bool = False,
    ) -> GraphRunResult:
        start = perf_counter()
        run_dir = Path(run_dir)
        paper_dir = run_dir.parents[2]
        artifacts: list[dict[str, str]] = []
        warnings: list[str] = []
        errors: list[str] = []

        graph.write(run_dir / "analysis_graph.yaml")
        artifacts.append(_artifact(run_dir / "analysis_graph.yaml", paper_dir))
        graph_issues = graph.validate()
        if graph_issues:
            errors.extend(graph_issues)

        data_registry = DataRegistry(paper_dir)
        data_status = data_registry.validate_for_execution(graph)
        require_data_registry = bool(graph.execution_policy.get("require_data_registry", True))
        if execute and require_data_registry and data_status["status"] != "pass":
            errors.extend(data_status.get("issues", []) or ["data registry validation failed"])
        warnings.extend(data_status.get("warnings", []) or [])

        approval_required = bool(graph.execution_policy.get("require_user_approval", True))
        block_reasons = []
        if execute and approval_required and not approval:
            block_reasons.append("user_approval_required")
            errors.append("analysis graph execution requires explicit user approval")
        if execute and require_data_registry and data_status["status"] != "pass":
            block_reasons.append("data_registry_invalid")

        node_records = []
        node_metrics = []
        if not errors:
            for node in graph.topological_nodes():
                node_started_at = utc_now()
                node_start = perf_counter()
                record = self._run_node(graph, node.to_dict(), run_dir, paper_dir, execute=execute)
                record["started_at"] = node_started_at
                record["completed_at"] = utc_now()
                record["runtime_seconds"] = round(perf_counter() - node_start, 6)
                node_dir = run_dir / "nodes" / str(record.get("node_id", "node"))
                record["input_size_bytes"] = self._input_size_bytes(record.get("input_contract", {}))
                record["output_size_bytes"] = self._tree_size_bytes(node_dir)
                self._write_node_manifest(node_dir, paper_dir, record)
                node_metrics.append({
                    "node_id": record.get("node_id", ""),
                    "module_id": record.get("module_id", ""),
                    "start_time": record["started_at"],
                    "end_time": record["completed_at"],
                    "runtime_seconds": record["runtime_seconds"],
                    "input_size_bytes": record["input_size_bytes"],
                    "output_size_bytes": record["output_size_bytes"],
                    "status": record.get("status", "unknown"),
                })
                node_records.append(record)
                warnings.extend(record.get("warnings", []) or [])
                errors.extend(record.get("errors", []) or [])
                for rel in record.get("artifacts", []) or []:
                    artifacts.append(_artifact(paper_dir / rel, paper_dir))

        for path in self._write_performance_artifacts(run_dir, graph.run_id, node_metrics):
            artifacts.append(_artifact(path, paper_dir))

        source_map_status = self._write_aggregate_source_maps(graph, run_dir, paper_dir, node_records, artifacts)
        artifacts.append(_artifact(run_dir / "figure_source_map.yaml", paper_dir))
        artifacts.append(_artifact(run_dir / "table_source_map.yaml", paper_dir))

        status = "blocked" if errors else ("completed" if execute else "dry_run_completed")
        env_grades = [
            str((record.get("environment") or {}).get("reproducibility_grade", "unknown"))
            for record in node_records
            if record.get("environment")
        ]
        reproducibility_grade = "locked" if env_grades and all(grade == "locked" for grade in env_grades) else (
            "degraded" if env_grades else "not_evaluated"
        )
        manifest = read_yaml(run_dir / "run_manifest.yaml")
        output_paths = [a["path"] for a in artifacts]
        manifest.update({
            "schema_version": "analysis_graph_run.v1",
            "run_id": graph.run_id,
            "mode": "execution_mode" if execute else "analysis_design_mode",
            "status": status,
            "analysis_adapter": "analysis_graph_executor",
            "execution_status": status,
            "executed_at": utc_now(),
            "dry_run": not execute,
            "paper_dir": self._project_relative_path(paper_dir),
            "analysis_graph": "analysis_graph.yaml",
            "approval_required": approval_required,
            "approval_granted": bool(approval),
            "module_registry": self._project_relative_path(self.modules.registry_path),
            "module_registry_hash": self.modules.content_hash(),
            "environment_registry": self._project_relative_path(self.environments.registry_path),
            "environment_registry_hash": self.environments.content_hash(),
            "environment_reproducibility_grade": reproducibility_grade,
            "data_registry": self._sanitize_for_manifest(data_status).get("data_registry", ""),
            "data_registry_hash": data_status.get("data_registry_hash", ""),
            "input_manifest": data_status.get("input_manifest", {}),
            "data_status": self._sanitize_for_manifest(data_status),
            "source_map_status": source_map_status,
            "nodes": [self._sanitize_for_manifest(record) for record in node_records],
            "node_environment": [record.get("environment", {}) for record in node_records if record.get("environment")],
            "outputs_generated": output_paths,
            "warnings": warnings,
            "errors": errors,
        })
        if block_reasons:
            manifest["block_reason"] = ";".join(block_reasons)
        write_yaml(run_dir / "run_manifest.yaml", manifest)
        artifacts.append(_artifact(run_dir / "run_manifest.yaml", paper_dir))
        write_yaml(
            run_dir / "outputs_manifest.yaml",
            {
                "schema_version": "analysis_graph_outputs.v1",
                "run_id": graph.run_id,
                "execution_mode": "real" if execute else "dry_run",
                "outputs": [{"path": path, "status": "generated"} for path in output_paths],
                "updated_at": utc_now(),
            },
        )
        artifacts.append(_artifact(run_dir / "outputs_manifest.yaml", paper_dir))
        metrics = {
            "runtime_seconds": round(perf_counter() - start, 6),
            "node_count": len(node_records),
            "executed_node_count": len([n for n in node_records if n.get("status") == "completed"]),
            "blocked_node_count": len([n for n in node_records if n.get("status") == "blocked"]),
        }
        return GraphRunResult(status=status, run_id=graph.run_id, artifacts=artifacts, metrics=metrics, warnings=warnings, errors=errors)

    def _write_performance_artifacts(
        self,
        run_dir: Path,
        run_id: str,
        node_metrics: list[dict[str, Any]],
    ) -> list[Path]:
        performance_dir = run_dir / "performance"
        performance_dir.mkdir(parents=True, exist_ok=True)
        timing_path = performance_dir / "node_timing.yaml"
        size_path = performance_dir / "output_size_report.yaml"
        ledger_path = performance_dir / "performance_ledger.tsv"
        write_yaml(timing_path, {
            "schema_version": "node_timing.v1",
            "run_id": run_id,
            "total_runtime_seconds": round(sum(float(item.get("runtime_seconds", 0)) for item in node_metrics), 6),
            "nodes": node_metrics,
        })
        write_yaml(size_path, {
            "schema_version": "output_size_report.v1",
            "run_id": run_id,
            "total_input_size_bytes": sum(int(item.get("input_size_bytes", 0)) for item in node_metrics),
            "total_output_size_bytes": sum(int(item.get("output_size_bytes", 0)) for item in node_metrics),
            "nodes": [
                {
                    "node_id": item.get("node_id", ""),
                    "input_size_bytes": item.get("input_size_bytes", 0),
                    "output_size_bytes": item.get("output_size_bytes", 0),
                }
                for item in node_metrics
            ],
        })
        fields = [
            "node_id", "module_id", "start_time", "end_time", "runtime_seconds",
            "input_size_bytes", "output_size_bytes", "status",
        ]
        with ledger_path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields, delimiter="\t")
            writer.writeheader()
            writer.writerows({field: item.get(field, "") for field in fields} for item in node_metrics)
        return [timing_path, size_path, ledger_path]

    def _input_size_bytes(self, input_contract: dict[str, Any]) -> int:
        total = 0
        seen: set[Path] = set()
        for item in (input_contract or {}).values():
            if not isinstance(item, dict) or item.get("status") != "bound":
                continue
            value = item.get("value")
            if value in ("", None, []):
                continue
            path = Path(str(value))
            if not path.is_absolute():
                path = self.project_root / path
            try:
                resolved = path.resolve()
            except OSError:
                continue
            if resolved in seen or not resolved.exists():
                continue
            seen.add(resolved)
            total += self._tree_size_bytes(resolved)
        return total

    @staticmethod
    def _tree_size_bytes(path: Path) -> int:
        try:
            if path.is_file():
                return path.stat().st_size
            if path.is_dir():
                return sum(item.stat().st_size for item in path.rglob("*") if item.is_file())
        except OSError:
            return 0
        return 0

    def _run_node(
        self,
        graph: AnalysisGraph,
        node: dict[str, Any],
        run_dir: Path,
        paper_dir: Path,
        *,
        execute: bool,
    ) -> dict[str, Any]:
        node_id = str(node.get("node_id", "node"))
        module_id = str(node.get("module_id", ""))
        module = self.modules.get(module_id)
        node_dir = run_dir / "nodes" / node_id
        node_dir.mkdir(parents=True, exist_ok=True)
        logs_dir = node_dir / "logs"
        logs_dir.mkdir(exist_ok=True)
        record = {
            "node_id": node_id,
            "module_id": module_id,
            "status": "planned",
            "artifacts": [],
            "warnings": [],
            "errors": [],
        }
        write_yaml(node_dir / "parameters.yaml", {"node": node, "module": module_id, "updated_at": utc_now()})
        record["artifacts"].append(str((node_dir / "parameters.yaml").relative_to(paper_dir)).replace("\\", "/"))

        if not module:
            record["status"] = "blocked"
            record["errors"].append(f"module not found: {module_id}")
            self._write_node_manifest(node_dir, paper_dir, record)
            return record

        production_gate = self.modules.production_gate(module)
        record["production_gate"] = production_gate
        if not production_gate["allowed"]:
            message = "module is not allowed in an executable production graph: " + ", ".join(production_gate["reasons"])
            if execute:
                record["status"] = "blocked"
                record["errors"].append(message)
                self._write_node_manifest(node_dir, paper_dir, record)
                return record
            record["warnings"].append(message)

        parameters = self._node_parameters(graph, node, module, paper_dir, run_dir)
        input_contract = build_node_input_contract(module, parameters, graph.data_bindings)
        record["input_contract"] = input_contract
        missing_inputs = unresolved_required_inputs(input_contract)
        if missing_inputs:
            message = f"required node inputs unresolved: {', '.join(missing_inputs)}"
            if execute and bool(graph.execution_policy.get("require_node_input_bindings", True)):
                record["status"] = "blocked"
                record["errors"].append(message)
                self._write_node_manifest(node_dir, paper_dir, record)
                return record
            record["warnings"].append(message)
        write_yaml(
            node_dir / "parameters.yaml",
            {
                "node": node,
                "module": module_id,
                "parameters": parameters,
                "input_contract": input_contract,
                "updated_at": utc_now(),
            },
        )

        env_id = str((module.get("environment") or {}).get("env_id", ""))
        require_env_lock = bool(graph.execution_policy.get("require_env_lock", False))
        env_status = self.environments.validate_environment(
            env_id,
            language=str(module.get("language", "")),
            require_lock=require_env_lock,
            require_packages=execute,
        )
        record["environment"] = env_status
        if env_status["status"] != "pass":
            if execute:
                record["status"] = "blocked"
                record["errors"].extend(env_status["issues"])
                self._write_node_manifest(node_dir, paper_dir, record)
                return record
            record["warnings"].extend(env_status["issues"])

        if not execute:
            record["status"] = "dry_run_completed"
            record["warnings"].append("node was planned but not executed; pass --execute with approval for real execution")
            self._write_node_manifest(node_dir, paper_dir, record)
            return record

        execution = module.get("execution") or {}
        exec_type = str(execution.get("type", "")).lower()
        if exec_type not in {"rscript", "python", "shell", "bash", "jupyter", "notebook", "ipynb"}:
            record["status"] = "blocked"
            record["errors"].append(f"unsupported execution type for graph executor: {exec_type or 'not_declared'}")
            self._write_node_manifest(node_dir, paper_dir, record)
            return record

        runner_language = self._runner_language(exec_type, str(module.get("language", "")))
        runner = env_status.get("runner") or self.environments.resolve_runner(env_id, language=runner_language)
        script_rel = str((module.get("source") or {}).get("path") or execution.get("script") or "")
        script_path = self.project_root / script_rel
        if not script_path.exists():
            record["status"] = "blocked"
            record["errors"].append(f"module script missing: {script_rel}")
            self._write_node_manifest(node_dir, paper_dir, record)
            return record
        if not runner:
            record["status"] = "blocked"
            record["errors"].append(f"runner unavailable for environment: {env_id}")
            self._write_node_manifest(node_dir, paper_dir, record)
            return record

        arg_template = list(execution.get("args", []) or [])
        replacements = {
            "run_id": graph.run_id,
            "node_id": node_id,
            "node_dir": self._project_relative_path(node_dir),
            "project_root": str(self.project_root),
            **{k: str(v) for k, v in parameters.items()},
        }
        args = []
        for item in arg_template:
            try:
                args.append(str(item).format(**replacements))
            except KeyError as exc:
                record["status"] = "blocked"
                record["errors"].append(f"command argument placeholder has no bound value: {exc.args[0]}")
                self._write_node_manifest(node_dir, paper_dir, record)
                return record
        script_arg = self._project_relative_path(script_path)
        command, command_issue = self._build_command(exec_type, str(runner), script_path, script_arg, args, node_dir)
        if command_issue:
            record["status"] = "blocked"
            record["errors"].append(command_issue)
            self._write_node_manifest(node_dir, paper_dir, record)
            return record
        record["execution_type"] = exec_type
        record["script"] = script_rel
        record["command"] = command
        timeout = int(execution.get("timeout_seconds", 1800))
        completed = subprocess.run(
            command,
            cwd=str(self.project_root),
            text=True,
            encoding="utf-8",
            errors="replace",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            timeout=timeout,
        )
        (logs_dir / "stdout.log").write_text(completed.stdout or "", encoding="utf-8")
        (logs_dir / "stderr.log").write_text(completed.stderr or "", encoding="utf-8")
        record["artifacts"].extend([
            str((logs_dir / "stdout.log").relative_to(paper_dir)).replace("\\", "/"),
            str((logs_dir / "stderr.log").relative_to(paper_dir)).replace("\\", "/"),
        ])
        record["exit_code"] = completed.returncode
        if completed.returncode == 0:
            record["status"] = "completed"
            for path in node_dir.rglob("*"):
                if path.is_file() and path.name not in {"node_manifest.yaml", "parameters.yaml"}:
                    rel = str(path.relative_to(paper_dir)).replace("\\", "/")
                    if rel not in record["artifacts"]:
                        record["artifacts"].append(rel)
        else:
            record["status"] = "blocked"
            record["errors"].append(f"node command failed with exit code {completed.returncode}")
        self._write_node_manifest(node_dir, paper_dir, record)
        return record

    def _node_parameters(
        self,
        graph: AnalysisGraph,
        node: dict[str, Any],
        module: dict[str, Any],
        paper_dir: Path,
        run_dir: Path,
    ) -> dict[str, Any]:
        parameters = dict(module.get("default_parameters", {}) or {})
        parameters.update(node.get("parameters", {}) or {})
        for key, item in (node.get("inputs", {}) or {}).items():
            if not isinstance(item, dict) or item.get("status") != "bound":
                continue
            value = item.get("value")
            if value not in ("", None, []):
                parameters.setdefault(str(key), value)
        for key in [
            "input_dir",
            "input",
            "count_matrix",
            "count_matrix_csv",
            "metadata",
            "sample_metadata",
            "sample_metadata_csv",
            "seurat_object",
            "seurat_rds",
            "pseudobulk_rds",
            "ranked_genes",
            "ranked_gene_statistic",
            "differential_expression_table",
            "gene_sets",
            "gene_set_collection",
        ]:
            if key not in parameters and graph.data_bindings.get(key):
                parameters[key] = graph.data_bindings[key]
        if "input_dir" not in parameters and graph.data_bindings.get("single_cell"):
            parameters["input_dir"] = graph.data_bindings["single_cell"]
        path_like = {
            "input_dir",
            "input",
            "count_matrix",
            "count_matrix_csv",
            "metadata",
            "sample_metadata",
            "sample_metadata_csv",
            "seurat_object",
            "seurat_rds",
            "pseudobulk_rds",
            "ranked_genes",
            "ranked_gene_statistic",
            "differential_expression_table",
            "gene_sets",
            "gene_set_collection",
        }
        for key in path_like:
            value = parameters.get(key)
            if value in ("", None, []):
                continue
            path = Path(str(value))
            if not path.is_absolute():
                if str(value).replace("\\", "/").startswith("nodes/"):
                    parameters[key] = self._project_relative_path(run_dir / path)
                else:
                    parameters[key] = self._project_relative_path(paper_dir / path)
            else:
                parameters[key] = self._project_relative_path(path)
        if "ranked_genes" not in parameters and parameters.get("ranked_gene_statistic"):
            parameters["ranked_genes"] = parameters["ranked_gene_statistic"]
        return parameters

    @staticmethod
    def _runner_language(exec_type: str, module_language: str) -> str:
        if exec_type == "rscript":
            return "r"
        if exec_type in {"python", "jupyter", "notebook", "ipynb"}:
            return "python"
        return module_language.lower()

    @staticmethod
    def _build_command(
        exec_type: str,
        runner: str,
        script_path: Path,
        script_arg: str,
        args: list[str],
        node_dir: Path,
    ) -> tuple[list[str], str]:
        if exec_type == "rscript":
            return [runner, script_arg, *args], ""
        if exec_type == "python":
            python_runner = runner or sys.executable or shutil.which("python") or ""
            if not python_runner:
                return [], "python runner unavailable"
            return [python_runner, script_arg, *args], ""
        if exec_type in {"shell", "bash"}:
            suffix = script_path.suffix.lower()
            if suffix == ".ps1":
                shell_runner = shutil.which("pwsh") or shutil.which("powershell") or runner
                if not shell_runner:
                    return [], "PowerShell runner unavailable for shell method asset"
                return [shell_runner, "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", script_arg, *args], ""
            shell_runner = runner or shutil.which("bash") or shutil.which("sh") or ""
            if not shell_runner:
                return [], "shell runner unavailable"
            return [shell_runner, script_arg, *args], ""
        if exec_type in {"jupyter", "notebook", "ipynb"}:
            jupyter_runner = shutil.which("jupyter") or runner
            if not jupyter_runner:
                return [], "jupyter runner unavailable"
            output_path = node_dir / "executed_notebook.ipynb"
            return [
                jupyter_runner,
                "nbconvert",
                "--to",
                "notebook",
                "--execute",
                script_arg,
                "--output",
                output_path.name,
                "--output-dir",
                str(node_dir),
            ], ""
        return [], f"unsupported execution type for graph executor: {exec_type or 'not_declared'}"

    def _write_node_manifest(self, node_dir: Path, paper_dir: Path, record: dict[str, Any]) -> None:
        write_yaml(node_dir / "node_manifest.yaml", {**self._sanitize_for_manifest(record), "updated_at": utc_now()})
        rel = str((node_dir / "node_manifest.yaml").relative_to(paper_dir)).replace("\\", "/")
        if rel not in record["artifacts"]:
            record["artifacts"].append(rel)

    def _write_aggregate_source_maps(
        self,
        graph: AnalysisGraph,
        run_dir: Path,
        paper_dir: Path,
        node_records: list[dict[str, Any]],
        artifacts: list[dict[str, str]],
    ) -> dict[str, Any]:
        figures = []
        tables = []
        for record in node_records:
            module = self.modules.get(str(record.get("module_id", ""))) or {}
            context = {
                "node_id": record.get("node_id", ""),
                "module_id": record.get("module_id", ""),
                "module_claim_boundary": module.get("claim_boundary", ""),
                "module_reviewer_risk": module.get("reviewer_risk", []) or [],
            }
            node_map_found = False
            for rel in record.get("artifacts", []) or []:
                path = paper_dir / rel
                if path.name == "figure_source_map.yaml":
                    node_map_found = True
                    data = read_source_map(path)
                    figures.extend(self._with_node_context(data.get("figures", []) or [], context, run_dir, path.parent, "figure"))
                elif path.name == "table_source_map.yaml":
                    node_map_found = True
                    data = read_source_map(path)
                    tables.extend(self._with_node_context(data.get("tables", []) or [], context, run_dir, path.parent, "table"))
            if node_map_found:
                continue
            for rel in record.get("artifacts", []) or []:
                suffix = Path(rel).suffix.lower()
                run_rel = self._run_relative_path(rel, run_dir)
                if suffix in {".png", ".pdf", ".svg", ".jpg", ".jpeg"}:
                    figures.append({
                        **context,
                        "figure_id": Path(rel).stem,
                        "path": run_rel,
                        "source_data": "node input and parameters",
                        "script": record.get("module_id", ""),
                        "method": "module-declared analysis graph node",
                        "statistical_unit": graph.statistical_unit,
                        "claim_boundary": module.get("claim_boundary", "workflow-generated analysis artifact; interpret with module risk notes"),
                        "source_map_quality": "incomplete_fallback",
                    })
                elif suffix in {".csv", ".tsv"}:
                    tables.append({
                        **context,
                        "table_id": Path(rel).stem,
                        "path": run_rel,
                        "source_inputs": "node input and parameters",
                        "method": record.get("module_id", ""),
                        "statistical_unit": graph.statistical_unit,
                        "claim_boundary": module.get("claim_boundary", "workflow-generated analysis table; interpret with module risk notes"),
                        "source_map_quality": "incomplete_fallback",
                    })
        write_yaml(run_dir / "figure_source_map.yaml", {"schema_version": "analysis_graph_source_map.v1", "figures": figures})
        write_yaml(run_dir / "table_source_map.yaml", {"schema_version": "analysis_graph_source_map.v1", "tables": tables})
        status = SourceMapValidator().validate_run(run_dir)
        return status

    @staticmethod
    def _run_relative_path(rel: str, run_dir: Path) -> str:
        prefix = f"results/runs/{run_dir.name}/"
        if rel.startswith(prefix):
            return rel[len(prefix):]
        return rel

    def _with_node_context(
        self,
        items: list[Any],
        context: dict[str, Any],
        run_dir: Path,
        node_dir: Path,
        kind: str,
    ) -> list[dict[str, Any]]:
        enriched = []
        node_rel = str(node_dir.relative_to(run_dir)).replace("\\", "/")
        path_fields = ["path", "source_data"] if kind == "figure" else ["path", "source_inputs"]
        for item in items:
            if not isinstance(item, dict):
                continue
            entry = {**item, **context, "source_map_quality": "node_declared"}
            if not entry.get("claim_boundary"):
                entry["claim_boundary"] = (
                    context.get("module_claim_boundary")
                    or f"workflow-generated {kind}; interpret with module risk notes"
                )
            for field in path_fields:
                value = entry.get(field)
                if isinstance(value, str):
                    entry[field] = self._prefix_node_path(value, node_rel)
                elif isinstance(value, list):
                    entry[field] = [
                        self._prefix_node_path(v, node_rel) if isinstance(v, str) else v
                        for v in value
                    ]
            enriched.append(entry)
        return enriched

    @staticmethod
    def _prefix_node_path(value: str, node_rel: str) -> str:
        if not value or value.startswith(("results/", "nodes/", "/", "\\")) or ":" in value[:3]:
            return value.replace("\\", "/")
        return f"{node_rel}/{value}".replace("\\", "/")

    def _project_relative_path(self, path: Path) -> str:
        try:
            resolved = Path(path).resolve()
            return str(resolved.relative_to(self.project_root.resolve())).replace("\\", "/")
        except (OSError, ValueError):
            return str(path).replace("\\", "/")

    def _sanitize_for_manifest(self, value: Any) -> Any:
        if isinstance(value, dict):
            return {key: self._sanitize_for_manifest(item) for key, item in value.items()}
        if isinstance(value, list):
            return [self._sanitize_for_manifest(item) for item in value]
        if isinstance(value, str):
            return self._sanitize_path_text(value)
        return value

    def _sanitize_path_text(self, value: str) -> str:
        try:
            path = Path(value)
            if path.is_absolute():
                return self._project_relative_path(path)
        except (OSError, ValueError):
            pass
        return value.replace("\\", "/")
