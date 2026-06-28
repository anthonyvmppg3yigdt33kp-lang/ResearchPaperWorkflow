"""
Paper Loop Engine: 20-stage paper pipeline with state management.

Loop model: observe -> decide -> run -> verify -> record -> mark_stale -> diagnose -> repeat
"""
from paper_workflow.engine.loop_engine import (
    PaperLoopEngine,
    StageDefinition,
    StageState,
    StageStatus,
    PipelineState,
)
from paper_workflow.engine.agent_harness import AgentHarness

__all__ = [
    "PaperLoopEngine", "StageDefinition", "StageState",
    "StageStatus", "PipelineState", "AgentHarness",
]
