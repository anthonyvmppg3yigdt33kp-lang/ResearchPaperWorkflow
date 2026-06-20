"""
Paper Loop Engine — 19-stage paper pipeline with state management.

Loop model: observe -> decide -> run -> verify -> record -> mark_stale -> diagnose -> repeat
"""
from paper_workflow.engine.loop_engine import (
    PaperLoopEngine,
    StageDefinition,
    StageState,
    StageStatus,
    PipelineState,
)

__all__ = [
    "PaperLoopEngine", "StageDefinition", "StageState",
    "StageStatus", "PipelineState",
]
