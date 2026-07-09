"""Analysis graph contract for multi-omics method-asset orchestration."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass
class AnalysisGraphNode:
    node_id: str
    module_id: str
    depends_on: list[str] = field(default_factory=list)
    inputs: dict[str, Any] = field(default_factory=dict)
    parameters: dict[str, Any] = field(default_factory=dict)
    outputs: list[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AnalysisGraphNode":
        return cls(
            node_id=str(data.get("node_id", "")),
            module_id=str(data.get("module_id", "")),
            depends_on=list(data.get("depends_on", []) or []),
            inputs=dict(data.get("inputs", {}) or {}),
            parameters=dict(data.get("parameters", {}) or {}),
            outputs=list(data.get("outputs", []) or []),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "node_id": self.node_id,
            "module_id": self.module_id,
            "depends_on": self.depends_on,
            "inputs": self.inputs,
            "parameters": self.parameters,
            "outputs": self.outputs,
        }


@dataclass
class AnalysisGraph:
    run_id: str
    research_question: str
    primary_objective: str
    statistical_unit: str
    nodes: list[AnalysisGraphNode]
    data_bindings: dict[str, Any] = field(default_factory=dict)
    execution_policy: dict[str, Any] = field(default_factory=dict)
    schema_version: str = "analysis_graph.v1"

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AnalysisGraph":
        graph_data = data.get("analysis_graph", data)
        raw_nodes = graph_data.get("nodes", []) if isinstance(graph_data, dict) else []
        return cls(
            run_id=str(data.get("run_id", graph_data.get("run_id", ""))),
            research_question=str(data.get("research_question", "")),
            primary_objective=str(data.get("primary_objective", data.get("goal", ""))),
            statistical_unit=str(data.get("statistical_unit", "sample")),
            data_bindings=dict(data.get("data_bindings", {}) or {}),
            execution_policy=dict(data.get("execution_policy", {}) or {}),
            nodes=[AnalysisGraphNode.from_dict(item) for item in raw_nodes if isinstance(item, dict)],
            schema_version=str(data.get("schema_version", "analysis_graph.v1")),
        )

    @classmethod
    def from_file(cls, path: Path) -> "AnalysisGraph":
        with Path(path).open("r", encoding="utf-8") as fh:
            data = yaml.safe_load(fh) or {}
        return cls.from_dict(data if isinstance(data, dict) else {})

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "run_id": self.run_id,
            "research_question": self.research_question,
            "primary_objective": self.primary_objective,
            "statistical_unit": self.statistical_unit,
            "data_bindings": self.data_bindings,
            "analysis_graph": {"nodes": [node.to_dict() for node in self.nodes]},
            "execution_policy": self.execution_policy,
        }

    def write(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as fh:
            yaml.safe_dump(self.to_dict(), fh, allow_unicode=True, sort_keys=False)

    def validate(self) -> list[str]:
        issues = []
        seen: set[str] = set()
        for node in self.nodes:
            if not node.node_id:
                issues.append("node missing node_id")
            if not node.module_id:
                issues.append(f"node {node.node_id or '<unknown>'} missing module_id")
            if node.node_id in seen:
                issues.append(f"duplicate node_id: {node.node_id}")
            seen.add(node.node_id)
            for dep in node.depends_on:
                if dep not in seen and dep not in {n.node_id for n in self.nodes}:
                    issues.append(f"node {node.node_id} depends on unknown node {dep}")
        try:
            self.topological_nodes()
        except ValueError as exc:
            issues.append(str(exc))
        return issues

    def topological_nodes(self) -> list[AnalysisGraphNode]:
        by_id = {node.node_id: node for node in self.nodes}
        visiting: set[str] = set()
        visited: set[str] = set()
        ordered: list[AnalysisGraphNode] = []

        def visit(node_id: str) -> None:
            if node_id in visited:
                return
            if node_id in visiting:
                raise ValueError(f"cycle detected at node: {node_id}")
            if node_id not in by_id:
                raise ValueError(f"unknown dependency: {node_id}")
            visiting.add(node_id)
            for dep in by_id[node_id].depends_on:
                visit(dep)
            visiting.remove(node_id)
            visited.add(node_id)
            ordered.append(by_id[node_id])

        for node in self.nodes:
            visit(node.node_id)
        return ordered


def _normalize_input_name(name: str) -> str:
    return str(name).strip().lower().lstrip("-").replace("-", "_").replace(" ", "_")


def _schema_entries(schema: dict[str, Any], key: str) -> list[dict[str, Any]]:
    entries = []
    raw = schema.get(key, []) if isinstance(schema, dict) else []
    for item in raw or []:
        if isinstance(item, dict):
            name = str(item.get("name") or item.get("id") or item.get("role") or "")
            if not name:
                continue
            entries.append(
                {
                    "name": name,
                    "type": str(item.get("type", "")),
                    "description": str(item.get("description", "")),
                    "required": key == "required",
                }
            )
        else:
            name = str(item)
            if name:
                entries.append({"name": name, "type": "", "description": "", "required": key == "required"})
    return entries


def build_data_bindings(input_paths: list[str] | None = None, input_dir: str = "") -> dict[str, Any]:
    paths = [str(path) for path in (input_paths or []) if str(path)]
    if input_dir and input_dir not in paths:
        paths.insert(0, str(input_dir))
    bindings: dict[str, Any] = {}
    if paths:
        bindings["input_paths"] = paths
        bindings["primary_input"] = paths[0]
        bindings["input_dir"] = paths[0]
        bindings["single_cell"] = paths[0]
        bindings["count_matrix"] = paths[0]
        bindings["count_matrix_csv"] = paths[0]
    if len(paths) > 1:
        bindings["metadata"] = paths[1]
        bindings["sample_metadata"] = paths[1]
        bindings["sample_metadata_csv"] = paths[1]
    return bindings


def build_node_input_contract(
    module: dict[str, Any],
    parameters: dict[str, Any],
    data_bindings: dict[str, Any],
) -> dict[str, Any]:
    """Bind a module's input schema to concrete node parameters or data paths."""
    schema = module.get("input_schema") or {}
    contract: dict[str, Any] = {}
    for entry in _schema_entries(schema, "required") + _schema_entries(schema, "optional"):
        name = entry["name"]
        key = _normalize_input_name(name)
        value, source = _resolve_input_value(key, parameters, data_bindings)
        status = "bound" if value not in ("", None, []) else ("optional_unbound" if not entry["required"] else "unresolved")
        contract[key] = {
            **entry,
            "binding_key": key,
            "value": value if status == "bound" else "",
            "binding_source": source,
            "status": status,
        }
    return contract


def unresolved_required_inputs(inputs: dict[str, Any]) -> list[str]:
    missing = []
    for key, item in (inputs or {}).items():
        if not isinstance(item, dict):
            continue
        if bool(item.get("required")) and item.get("status") != "bound":
            missing.append(str(item.get("name") or key))
    return missing


def _resolve_input_value(
    key: str,
    parameters: dict[str, Any],
    data_bindings: dict[str, Any],
) -> tuple[Any, str]:
    aliases = {
        "input": ["input", "input_dir", "primary_input", "single_cell"],
        "input_dir": ["input_dir", "primary_input", "single_cell"],
        "seurat_object": ["seurat_object", "input", "input_dir", "primary_input", "single_cell"],
        "seurat_rds": ["seurat_rds", "input", "input_dir", "primary_input"],
        "pseudobulk_rds": ["pseudobulk_rds", "input", "primary_input"],
        "count_matrix": ["count_matrix", "count_matrix_csv", "counts", "primary_input"],
        "count_matrix_csv": ["count_matrix_csv", "count_matrix", "primary_input"],
        "counts": ["counts", "count_matrix", "primary_input"],
        "metadata": ["metadata", "sample_metadata", "sample_metadata_csv"],
        "sample_metadata": ["sample_metadata", "metadata", "sample_metadata_csv"],
        "sample_metadata_csv": ["sample_metadata_csv", "sample_metadata", "metadata"],
    }
    candidates = [key, *aliases.get(key, [])]
    for candidate in candidates:
        if candidate in parameters and parameters[candidate] not in ("", None, []):
            return parameters[candidate], f"parameters.{candidate}"
    for candidate in candidates:
        if candidate in data_bindings and data_bindings[candidate] not in ("", None, []):
            return data_bindings[candidate], f"data_bindings.{candidate}"
    return "", "unbound"


def build_graph_from_selected_modules(
    *,
    run_id: str,
    goal: str,
    selected_modules: list[dict[str, Any]],
    input_dir: str = "",
    input_paths: list[str] | None = None,
    statistical_unit: str = "sample",
) -> AnalysisGraph:
    nodes: list[AnalysisGraphNode] = []
    prior_id = ""
    data_bindings = build_data_bindings(input_paths=input_paths, input_dir=input_dir)
    for idx, module in enumerate(selected_modules, start=1):
        module_id = str(module.get("id") or module.get("module_id"))
        step = str(module.get("step") or f"step{idx}").replace(" ", "_")
        node_id = f"{step}_{idx}" if step in {node.node_id for node in nodes} else step
        default_parameters = dict(module.get("default_parameters", {}) or {})
        if data_bindings.get("input_dir") and "input_dir" not in default_parameters:
            default_parameters["input_dir"] = data_bindings["input_dir"]
        node_inputs = build_node_input_contract(module, default_parameters, data_bindings)
        nodes.append(
            AnalysisGraphNode(
                node_id=node_id,
                module_id=module_id,
                depends_on=[prior_id] if prior_id and module.get("chain_after_previous", False) else list(module.get("depends_on", []) or []),
                inputs=node_inputs,
                parameters=default_parameters,
                outputs=list(module.get("output_schema", {}).get("artifacts", []) or []),
            )
        )
        prior_id = node_id
    return AnalysisGraph(
        run_id=run_id,
        research_question=goal,
        primary_objective=goal,
        statistical_unit=statistical_unit,
        data_bindings=data_bindings,
        execution_policy={
            "require_user_approval": True,
            "require_data_registry": True,
            "require_env_lock": True,
            "require_node_input_bindings": True,
            "write_scope": f"results/runs/{run_id}/",
            "raw_data_mutation": "forbidden",
        },
        nodes=nodes,
    )
