"""TargetTask orchestration for v5 production-kernel workflows."""

from paper_workflow.target_task.loader import load_target_task
from paper_workflow.target_task.orchestrator import TargetTaskOrchestrator

__all__ = ["TargetTaskOrchestrator", "load_target_task"]
