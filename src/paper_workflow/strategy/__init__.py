"""
Strategy Layer — Research strategy, topic selection, journal targeting, feasibility, hypotheses.

Domain-agnostic: configured via config/default_config.yaml and config/journal_database.yaml.
"""
from paper_workflow.strategy.topic_selector import TopicSelector, ResearchTopic
from paper_workflow.strategy.journal_targeter import JournalTargeter, JournalTarget
from paper_workflow.strategy.feasibility import FeasibilityAssessor, FeasibilityReport
from paper_workflow.strategy.hypothesis_framework import HypothesisFramework, Hypothesis
from paper_workflow.strategy.research_strategy import ResearchStrategyManager, ResearchStrategy

__all__ = [
    "ResearchStrategyManager", "ResearchStrategy",
    "TopicSelector", "ResearchTopic",
    "JournalTargeter", "JournalTarget",
    "FeasibilityAssessor", "FeasibilityReport",
    "HypothesisFramework", "Hypothesis",
]
