"""
Evidence Graph — Core v3.0 evidence-centric architecture.

Traces every manuscript claim back to data, code, statistical test, and artifact.
This is the foundation of the evidence-centric upgrade: every claim in a paper
must be traceable through this graph.

Claim → Statistical Evidence → Artifact → Code → Parameter
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional


@dataclass
class EvidenceNode:
    """A node in the evidence graph — can be a claim, artifact, figure, code file, or parameter."""
    node_id: str
    node_type: str  # claim, artifact, figure, code, parameter, statistical_result, table
    label: str
    confidence: str = "hypothesis"  # validated, supported, hypothesis, contradicted
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {"node_id": self.node_id, "node_type": self.node_type,
                "label": self.label, "confidence": self.confidence,
                "metadata": self.metadata}


@dataclass
class EvidenceEdge:
    """A directed edge in the evidence graph."""
    source_id: str
    target_id: str
    relationship: str  # supports, contradicts, derived_from, computed_by, visualized_in, parameterized_by
    strength: str = "moderate"  # strong, moderate, weak

    def to_dict(self) -> dict:
        return {"source_id": self.source_id, "target_id": self.target_id,
                "relationship": self.relationship, "strength": self.strength}


class EvidenceGraph:
    """Manages the evidence graph for a paper project (v3.0).

    Provides full traceability from manuscript claim → statistical result →
    analysis artifact → code file → parameter value — enabling reviewer
    defense at the granularity of individual claims.
    """

    def __init__(self, paper_dir: Path):
        self.paper_dir = Path(paper_dir)
        self.nodes: dict[str, EvidenceNode] = {}
        self.edges: list[EvidenceEdge] = []

    # ---- Node management ----
    def add_claim(self, claim_id: str, text: str, section: str,
                  confidence: str = "hypothesis") -> EvidenceNode:
        node = EvidenceNode(node_id=claim_id, node_type="claim", label=text[:200],
                           confidence=confidence, metadata={"section": section})
        self.nodes[claim_id] = node
        return node

    def add_artifact(self, artifact_path: str, artifact_hash: str = "",
                     stage: str = "") -> EvidenceNode:
        node = EvidenceNode(node_id=artifact_path, node_type="artifact",
                           label=Path(artifact_path).name,
                           metadata={"hash": artifact_hash, "stage": stage})
        self.nodes[artifact_path] = node
        return node

    def add_figure(self, figure_id: str, figure_path: str = "") -> EvidenceNode:
        node = EvidenceNode(node_id=figure_id, node_type="figure",
                           label=figure_id, metadata={"path": figure_path})
        self.nodes[figure_id] = node
        return node

    def add_code(self, code_file: str, line_range: str = "") -> EvidenceNode:
        code_id = f"{code_file}:{line_range}" if line_range else code_file
        node = EvidenceNode(node_id=code_id, node_type="code",
                           label=Path(code_file).name,
                           metadata={"file": code_file, "line_range": line_range})
        self.nodes[code_id] = node
        return node

    # ---- Edge creation ----
    def bind_to_artifact(self, claim_id: str, artifact_path: str,
                          artifact_hash: str = "") -> EvidenceEdge:
        if artifact_path not in self.nodes:
            self.add_artifact(artifact_path, artifact_hash)
        edge = EvidenceEdge(source_id=claim_id, target_id=artifact_path,
                           relationship="derived_from", strength="strong")
        self.edges.append(edge)
        return edge

    def bind_to_statistics(self, claim_id: str, stat_test: str,
                            stat_value: str = "", p_value: str = "",
                            effect_size: str = "", ci: str = "") -> EvidenceEdge:
        stat_id = f"stat_{claim_id}"
        stat_label = f"{stat_test}: {stat_value} (p={p_value})"[:200]
        node = EvidenceNode(node_id=stat_id, node_type="statistical_result",
                           label=stat_label,
                           metadata={"test": stat_test, "value": stat_value,
                                    "p_value": p_value, "effect_size": effect_size, "ci": ci})
        self.nodes[stat_id] = node
        edge = EvidenceEdge(source_id=claim_id, target_id=stat_id,
                           relationship="derived_from", strength="strong")
        self.edges.append(edge)
        return edge

    def bind_to_figure(self, claim_id: str, figure_id: str) -> EvidenceEdge:
        if figure_id not in self.nodes:
            self.add_figure(figure_id)
        edge = EvidenceEdge(source_id=claim_id, target_id=figure_id,
                           relationship="visualized_in", strength="moderate")
        self.edges.append(edge)
        return edge

    def bind_to_code(self, artifact_path: str, code_file: str,
                      line_range: str = "") -> EvidenceEdge:
        code_id = f"{code_file}:{line_range}" if line_range else code_file
        if code_id not in self.nodes:
            self.add_code(code_file, line_range)
        edge = EvidenceEdge(source_id=artifact_path, target_id=code_id,
                           relationship="computed_by", strength="strong")
        self.edges.append(edge)
        return edge

    def bind_to_parameter(self, code_file: str, param_name: str,
                           param_value: str) -> EvidenceEdge:
        param_id = f"{code_file}::{param_name}"
        if param_id not in self.nodes:
            node = EvidenceNode(node_id=param_id, node_type="parameter",
                               label=f"{param_name}={param_value}",
                               metadata={"code_file": code_file, "name": param_name,
                                        "value": param_value})
            self.nodes[param_id] = node
        code_id = next((nid for nid, n in self.nodes.items()
                       if n.node_type == "code" and code_file in nid), None)
        if code_id:
            edge = EvidenceEdge(source_id=code_id, target_id=param_id,
                               relationship="parameterized_by", strength="strong")
            self.edges.append(edge)
            return edge
        return EvidenceEdge(source_id="", target_id=param_id, relationship="orphan")

    # ---- Query methods ----
    def trace_claim(self, claim_id: str) -> dict:
        """Full evidence trace for a claim: claim → stats → artifact → code → parameter."""
        if claim_id not in self.nodes:
            return {"error": f"Claim {claim_id} not found"}

        trace = {
            "claim": self.nodes[claim_id].to_dict(),
            "statistical_evidence": [],
            "artifacts": [],
            "figures": [],
            "code": [],
            "parameters": [],
            "chain_completeness": {"score": 0.0, "missing_links": []},
        }

        # BFS from claim through edges
        visited: set[str] = set()
        queue = [claim_id]
        while queue:
            current = queue.pop(0)
            if current in visited:
                continue
            visited.add(current)

            for edge in self.edges:
                if edge.source_id == current:
                    target = self.nodes.get(edge.target_id)
                    if not target:
                        continue
                    if target.node_type == "statistical_result":
                        trace["statistical_evidence"].append(target.to_dict())
                    elif target.node_type == "artifact":
                        trace["artifacts"].append(target.to_dict())
                    elif target.node_type == "figure":
                        trace["figures"].append(target.to_dict())
                    elif target.node_type == "code":
                        trace["code"].append(target.to_dict())
                    elif target.node_type == "parameter":
                        trace["parameters"].append(target.to_dict())
                    queue.append(edge.target_id)

        # Score completeness
        score = 0.0
        missing = []
        if trace["statistical_evidence"]: score += 0.25
        else: missing.append("statistical_evidence")
        if trace["artifacts"]: score += 0.25
        else: missing.append("artifacts")
        if trace["figures"]: score += 0.15
        if trace["code"]: score += 0.20
        else: missing.append("code")
        if trace["parameters"]: score += 0.15
        trace["chain_completeness"] = {"score": round(score, 2), "missing_links": missing}

        return trace

    def get_unsupported_claims(self) -> list[str]:
        """Claims with no artifact binding (no edge to artifact or figure)."""
        supported = set()
        for edge in self.edges:
            if edge.relationship in ("derived_from", "visualized_in"):
                supported.add(edge.source_id)
        return [nid for nid, n in self.nodes.items()
                if n.node_type == "claim" and nid not in supported]

    def get_weak_chain_claims(self) -> list[str]:
        """Claims with weak or contradictory evidence."""
        weak = []
        for nid, n in self.nodes.items():
            if n.node_type == "claim" and n.confidence in ("hypothesis", "contradicted"):
                weak.append(nid)
        return weak

    def validate_graph(self) -> dict:
        """Validate graph integrity: no orphan claims, no circular edges, all artifacts hashed."""
        issues = []

        # Orphan claims
        orphans = self.get_unsupported_claims()
        if orphans:
            issues.append({"type": "orphan_claims", "count": len(orphans),
                          "claim_ids": orphans[:10]})

        # Circular check (simple DFS)
        for edge in self.edges:
            if edge.source_id == edge.target_id:
                issues.append({"type": "self_loop", "edge": edge.to_dict()})

        # Artifacts without hash
        for nid, n in self.nodes.items():
            if n.node_type == "artifact" and not n.metadata.get("hash"):
                issues.append({"type": "unhashed_artifact", "artifact_id": nid})

        return {"valid": len(issues) == 0, "issues": issues, "issue_count": len(issues),
                "total_nodes": len(self.nodes), "total_edges": len(self.edges)}

    # ---- Export ----
    def export_json(self, output_path: Optional[Path] = None) -> Path:
        """Export evidence graph as JSON."""
        path = output_path or (self.paper_dir / "evidence_graph.json")
        graph = {
            "paper_id": self.paper_dir.name,
            "generated_at": datetime.now().isoformat(),
            "nodes": [n.to_dict() for n in self.nodes.values()],
            "edges": [e.to_dict() for e in self.edges],
            "summary": {
                "total_nodes": len(self.nodes),
                "total_edges": len(self.edges),
                "unsupported_claims": len(self.get_unsupported_claims()),
                "weak_chain_claims": len(self.get_weak_chain_claims()),
                "validation": self.validate_graph(),
            },
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(graph, f, indent=2, ensure_ascii=False)
        return path

    def export_graphviz(self, output_path: Optional[Path] = None) -> Path:
        """Export evidence graph as Graphviz DOT format for visualization."""
        path = output_path or (self.paper_dir / "evidence_graph.dot")
        lines = ["digraph EvidenceGraph {", '  rankdir=LR;',
                 '  node [shape=box, style=filled];', '']

        # Node styling by type
        colors = {"claim": "lightyellow", "artifact": "lightblue", "figure": "lightgreen",
                  "code": "lightgray", "parameter": "lavender",
                  "statistical_result": "lightsalmon", "table": "lightcyan"}

        for nid, n in self.nodes.items():
            color = colors.get(n.node_type, "white")
            label = n.label.replace('"', '\\"')[:100]
            lines.append(f'  "{nid}" [label="{n.node_type}: {label}", fillcolor={color}];')

        lines.append("")
        for edge in self.edges:
            style = "solid" if edge.strength == "strong" else "dashed"
            lines.append(f'  "{edge.source_id}" -> "{edge.target_id}" '
                        f'[label="{edge.relationship}", style={style}];')

        lines.append("}")
        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        return path


def build_evidence_graph_from_ledgers(claim_ledger_csv: Path,
                                       artifact_ledger_jsonl: Path,
                                       paper_dir: Path) -> EvidenceGraph:
    """Build an EvidenceGraph from existing claim and artifact ledgers."""
    import csv
    graph = EvidenceGraph(paper_dir)

    # Load claims from CSV
    if claim_ledger_csv.exists():
        with open(claim_ledger_csv, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                cid = row.get("claim_id", "")
                if not cid:
                    continue
                graph.add_claim(cid, row.get("claim_text", ""),
                               row.get("section", ""), row.get("confidence", "hypothesis"))
                if row.get("artifact_path"):
                    graph.bind_to_artifact(cid, row["artifact_path"],
                                          row.get("artifact_hash", ""))
                if row.get("figure_ref"):
                    graph.bind_to_figure(cid, row["figure_ref"])
                if row.get("stat_test"):
                    graph.bind_to_statistics(cid, row["stat_test"],
                                            row.get("stat_value", ""),
                                            row.get("p_value", ""),
                                            row.get("effect_size", ""))

    # Load artifacts from JSONL
    if artifact_ledger_jsonl.exists():
        with open(artifact_ledger_jsonl, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    entry = json.loads(line)
                    graph.add_artifact(entry.get("path", ""),
                                      entry.get("hash_sha256", ""),
                                      entry.get("stage", ""))

    return graph
