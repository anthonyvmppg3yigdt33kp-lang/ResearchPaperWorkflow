"""Meta-Workflow Module — Self-iteration and method lifecycle management (v3.0).

Components:
- MethodRadar: Scans PubMed/bioRxiv/arXiv/Equator/GitHub for new methods
- SkillSandbox: Benchmarks new methods on historical projects
- PostmortemLedger: Records reviewer feedback, suggests new gates
"""
from paper_workflow.meta.method_radar import MethodRadar, MethodSignal
from paper_workflow.meta.skill_sandbox import SkillSandbox, SandboxResult
from paper_workflow.meta.postmortem import PostmortemLedger, GateSuggestion

__all__ = [
    "MethodRadar", "MethodSignal",
    "SkillSandbox", "SandboxResult",
    "PostmortemLedger", "GateSuggestion",
]
