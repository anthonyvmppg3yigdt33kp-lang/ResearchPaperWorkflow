"""
Strategy Layer — Research strategy, topic selection, journal targeting, feasibility, hypotheses.
v3.0: Added ClinicalValueAssessor, ReportingGuidelineRouter, AnalysisPlanGenerator.

Domain-agnostic: configured via config/default_config.yaml and config/journal_database.yaml.
"""
from paper_workflow.strategy.topic_selector import TopicSelector, ResearchTopic
from paper_workflow.strategy.journal_targeter import JournalTargeter, JournalTarget
from paper_workflow.strategy.feasibility import FeasibilityAssessor, FeasibilityReport
from paper_workflow.strategy.hypothesis_framework import HypothesisFramework, Hypothesis, HypothesisLayer
from paper_workflow.strategy.research_strategy import ResearchStrategyManager, ResearchStrategy

# v3.0: New strategy modules
try:
    from paper_workflow.strategy.clinical_value import ClinicalValueAssessor, ClinicalValueMatrix
except ImportError:
    ClinicalValueAssessor = None
    ClinicalValueMatrix = None

try:
    from paper_workflow.strategy.reporting_router import ReportingGuidelineRouter, GuidelineChecklist
except ImportError:
    ReportingGuidelineRouter = None
    GuidelineChecklist = None

try:
    from paper_workflow.strategy.analysis_plan import AnalysisPlanGenerator, StatisticalAnalysisPlan
except ImportError:
    AnalysisPlanGenerator = None
    StatisticalAnalysisPlan = None

__all__ = [
    "ResearchStrategyManager", "ResearchStrategy",
    "TopicSelector", "ResearchTopic",
    "JournalTargeter", "JournalTarget",
    "FeasibilityAssessor", "FeasibilityReport",
    "HypothesisFramework", "Hypothesis", "HypothesisLayer",
    "ClinicalValueAssessor", "ClinicalValueMatrix",
    "ReportingGuidelineRouter", "GuidelineChecklist",
    "AnalysisPlanGenerator", "StatisticalAnalysisPlan",
]
