"""
Research Paper Workflow Framework — Domain-agnostic paper workflow system.

Four-layer architecture:
    Strategy Layer  — Topic selection, journal targeting, feasibility, hypotheses
    Decision Layer  — Skills dispatcher, MCP router, Paper Loop Engine
    Execution Layer — Pipeline orchestration, quality gates, CLI
    Supervision Layer — Passport system, integrity gates, stale detection

Usage:
    from paper_workflow import PaperWorkflow
    wf = PaperWorkflow(project_root=".", paper_id="my_paper")
    wf.initialize(idea="...", field="...", journal="Genome Biology")
    wf.run()
"""

__version__ = "4.5.0"
__author__ = "Research Paper Workflow Framework"

from paper_workflow.workflow import PaperWorkflow, WorkflowState, create_and_run_paper
from paper_workflow.api import WorkflowAPI
from paper_workflow.ai_harness import AIWorkflowHarness
from paper_workflow.utils.config_loader import ConfigLoader
from paper_workflow.outputs import StageResult, ArtifactRecord, StageStatus, RESULT_SCHEMA_VERSION

__all__ = [
    "PaperWorkflow",
    "WorkflowAPI",
    "AIWorkflowHarness",
    "WorkflowState",
    "create_and_run_paper",
    "ConfigLoader",
    "StageResult",
    "ArtifactRecord",
    "StageStatus",
    "RESULT_SCHEMA_VERSION",
    "__version__",
]
