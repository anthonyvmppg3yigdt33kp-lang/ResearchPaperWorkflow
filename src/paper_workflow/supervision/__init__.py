"""
Supervision Layer — Passport system, integrity gates, artifact tracking.
"""
from paper_workflow.supervision.passport import PaperPassport, ArtifactEntry, CheckpointEntry, IntegrityEvent
from paper_workflow.supervision.integrity import IntegrityGateChecker, IntegrityReport, GateResult

__all__ = [
    "PaperPassport", "ArtifactEntry", "CheckpointEntry", "IntegrityEvent",
    "IntegrityGateChecker", "IntegrityReport", "GateResult",
]
