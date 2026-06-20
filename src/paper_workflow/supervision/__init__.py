"""
Supervision Layer — Passport system, integrity gates, artifact tracking, evidence graph (v3.0).
"""
from paper_workflow.supervision.passport import PaperPassport, ArtifactEntry, CheckpointEntry, IntegrityEvent, ClaimEntry
from paper_workflow.supervision.integrity import IntegrityGateChecker, IntegrityReport, GateResult

# v3.0: Evidence graph
try:
    from paper_workflow.supervision.evidence_graph import EvidenceGraph, EvidenceNode, EvidenceEdge, build_evidence_graph_from_ledgers
except ImportError:
    EvidenceGraph = None
    EvidenceNode = None
    EvidenceEdge = None
    build_evidence_graph_from_ledgers = None

__all__ = [
    "PaperPassport", "ArtifactEntry", "CheckpointEntry", "IntegrityEvent", "ClaimEntry",
    "IntegrityGateChecker", "IntegrityReport", "GateResult",
    "EvidenceGraph", "EvidenceNode", "EvidenceEdge", "build_evidence_graph_from_ledgers",
]
