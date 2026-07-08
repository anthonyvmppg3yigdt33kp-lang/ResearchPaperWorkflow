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


def build_graph_from_selected_modules(
    *,
    run_id: str,
    goal: str,
    selected_modules: list[dict[str, Any]],
    input_dir: str = "",
    statistical_unit: str = "sample",
) -> AnalysisGraph:
    nodes: list[AnalysisGraphNode] = []
    prior_id = ""
    for idx, module in enumerate(selected_modules, start=1):
        module_id = str(module.get("id") or module.get("module_id"))
        step = str(module.get("step") or f"step{idx}").replace(" ", "_")
        node_id = f"{step}_{idx}" if step in {node.node_id for node in nodes} else step
        default_parameters = dict(module.get("default_parameters", {}) or {})
        if input_dir and "input_dir" not in default_parameters:
            default_parameters["input_dir"] = input_dir
        nodes.append(
            AnalysisGraphNode(
                node_id=node_id,
                module_id=module_id,
                depends_on=[prior_id] if prior_id and module.get("chain_after_previous", False) else list(module.get("depends_on", []) or []),
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
        data_bindings={"single_cell": input_dir} if input_dir else {},
        execution_policy={
            "require_user_approval": True,
            "require_env_lock": True,
            "write_scope": f"results/runs/{run_id}/",
            "raw_data_mutation": "forbidden",
        },
        nodes=nodes,
    )
