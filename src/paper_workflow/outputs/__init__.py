"""Output layer — Standardized stage results, artifacts, and status tracking."""

from paper_workflow.outputs.stage_result import (
    StageResult,
    ArtifactRecord,
    StageStatus,
    ExecutionMode,
    RESULT_SCHEMA_VERSION,
)
from paper_workflow.outputs.result_run_manager import ResultRunManager, RunEvaluation

__all__ = [
    "StageResult",
    "ArtifactRecord",
    "StageStatus",
    "ExecutionMode",
    "RESULT_SCHEMA_VERSION",
    "ResultRunManager",
    "RunEvaluation",
]
