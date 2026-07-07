"""Analysis design schemas and bounded execution adapters."""

from paper_workflow.analysis.design import AnalysisDesign
from paper_workflow.analysis.adapters import AdapterRunResult, run_analysis_adapter

__all__ = [
    "AnalysisDesign",
    "AdapterRunResult",
    "run_analysis_adapter",
]

