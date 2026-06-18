"""
Research Strategy Manager — Top-level strategy orchestration.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

import yaml

from paper_workflow.strategy.topic_selector import TopicSelector, ResearchTopic
from paper_workflow.strategy.journal_targeter import JournalTargeter, JournalTarget
from paper_workflow.strategy.feasibility import FeasibilityAssessor, FeasibilityReport
from paper_workflow.strategy.hypothesis_framework import HypothesisFramework, Hypothesis


@dataclass
class ResearchStrategy:
    """Complete research strategy for a paper project."""
    strategy_id: str
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    topic: Optional[ResearchTopic] = None
    journal_target: Optional[JournalTarget] = None
    feasibility: Optional[FeasibilityReport] = None
    hypotheses: list[Hypothesis] = field(default_factory=list)
    timeline_weeks: int = 8
    phases: list[dict] = field(default_factory=list)
    risks: list[dict] = field(default_factory=list)
    dependencies: list[dict] = field(default_factory=list)
    status: str = "draft"
    decisions: list[dict] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "strategy_id": self.strategy_id, "created_at": self.created_at,
            "topic": self.topic.to_dict() if self.topic else None,
            "journal_target": self.journal_target.to_dict() if self.journal_target else None,
            "feasibility": self.feasibility.to_dict() if self.feasibility else None,
            "hypotheses": [h.to_dict() for h in self.hypotheses],
            "timeline_weeks": self.timeline_weeks, "phases": self.phases,
            "risks": self.risks, "dependencies": self.dependencies,
            "status": self.status, "decisions": self.decisions,
        }


class ResearchStrategyManager:
    """Top-level strategy orchestrator for research paper projects."""

    DEFAULT_PHASES = [
        {"week": 1, "phase": "Project Modeling", "tasks": ["Define project context", "Set up passport", "Configure journal"]},
        {"week": 2, "phase": "Data Audit & Pipeline", "tasks": ["Data quality audit", "Minimum reproducible pipeline"]},
        {"week": 3, "phase": "Preliminary Results", "tasks": ["Core analysis", "Mechanism hypotheses"]},
        {"week": 4, "phase": "Figure Planning", "tasks": ["Design Figure 1-6", "Identify missing analyses"]},
        {"week": 5, "phase": "Supplementary Analysis", "tasks": ["Missing analyses", "Statistical validation"]},
        {"week": 6, "phase": "Results Draft", "tasks": ["Write Results", "Claims-evidence table"]},
        {"week": 7, "phase": "Full Manuscript", "tasks": ["Write all sections", "Generate LaTeX/PDF"]},
        {"week": 8, "phase": "Pre-submission Review", "tasks": ["Integrity gates", "Internal review", "Final polish"]},
    ]

    def __init__(self, project_root: Optional[Path] = None):
        self.project_root = project_root or self._find_project_root()
        self.topic_selector = TopicSelector()
        self.journal_targeter = JournalTargeter(project_root)
        self.feasibility_assessor = FeasibilityAssessor(project_root)
        self.hypothesis_framework = HypothesisFramework(project_root)

    def _find_project_root(self) -> Path:
        current = Path(__file__).resolve().parent
        for _ in range(10):
            if (current / "AGENTS.md").exists() or (current / "CLAUDE.md").exists():
                return current
            current = current.parent
        return Path.cwd()

    def create_strategy(self, idea: str, field: str, target_journal: Optional[str] = None,
                        timeline_weeks: int = 8) -> ResearchStrategy:
        """Create a complete research strategy from an initial idea."""
        strategy_id = self._generate_id(idea)
        strategy = ResearchStrategy(strategy_id=strategy_id, timeline_weeks=timeline_weeks,
                                    phases=self.DEFAULT_PHASES[:timeline_weeks])
        strategy.topic = self.topic_selector.select_topic(idea, field)
        strategy.journal_target = (self.journal_targeter.resolve_journal(target_journal)
                                   if target_journal
                                   else self.journal_targeter.recommend_journal(strategy.topic))
        strategy.feasibility = self.feasibility_assessor.assess(strategy.topic, strategy.journal_target)
        strategy.hypotheses = self.hypothesis_framework.generate_hypotheses(strategy.topic, strategy.feasibility)
        strategy.risks = self._assess_risks(strategy)
        strategy.dependencies = self._map_dependencies()
        strategy.status = "ready"
        return strategy

    def _generate_id(self, idea: str) -> str:
        slug = "_".join(idea.lower().split()[:5])
        slug = "".join(c for c in slug if c.isalnum() or c == "_")
        return f"strat-{slug}-{datetime.now().strftime('%Y%m%d-%H%M')}"

    def _assess_risks(self, strategy: ResearchStrategy) -> list[dict]:
        risks = []
        if strategy.feasibility and strategy.feasibility.data_score < 0.6:
            risks.append({"id": "risk-data", "category": "data", "severity": "high",
                          "description": "Data quality below threshold", "mitigation": "Additional QC, sensitivity analysis"})
        if strategy.topic and strategy.topic.estimated_sample_size:
            n = strategy.topic.estimated_sample_size
            if n < 6:
                risks.append({"id": "risk-sample", "category": "statistical", "severity": "high" if n < 3 else "medium",
                              "description": f"Small sample size (n={n})", "mitigation": "Effect size emphasis, non-parametric methods"})
        if strategy.journal_target and strategy.feasibility and strategy.feasibility.journal_fit_score < 0.5:
            risks.append({"id": "risk-journal", "category": "publication", "severity": "medium",
                          "description": "Scope may not match target journal", "mitigation": "Consider alternatives or expand scope"})
        return risks

    def _map_dependencies(self) -> list[dict]:
        return [
            {"from": "data_audit", "to": "core_analysis", "type": "hard"},
            {"from": "core_analysis", "to": "figure_planning", "type": "hard"},
            {"from": "figure_planning", "to": "results_writing", "type": "hard"},
            {"from": "literature_review", "to": "introduction", "type": "soft"},
            {"from": "results_writing", "to": "discussion", "type": "hard"},
            {"from": "all_sections", "to": "integrity_check", "type": "hard"},
            {"from": "integrity_check", "to": "internal_review", "type": "hard"},
        ]

    def save_strategy(self, strategy: ResearchStrategy, path: Optional[Path] = None) -> Path:
        if path is None:
            strategy_dir = self.project_root / "strategy"
            strategy_dir.mkdir(parents=True, exist_ok=True)
            path = strategy_dir / f"{strategy.strategy_id}.yaml"
        with open(path, "w", encoding="utf-8") as f:
            yaml.dump(strategy.to_dict(), f, allow_unicode=True, default_flow_style=False)
        return path

    def print_summary(self, strategy: ResearchStrategy) -> str:
        lines = ["=" * 60, f"Research Strategy: {strategy.strategy_id}", "=" * 60, ""]
        if strategy.topic:
            lines += [f"Topic: {strategy.topic.idea[:80]}", f"Field: {strategy.topic.field}",
                      f"Innovation: {strategy.topic.innovation_level}/5 | Scope: {strategy.topic.scope}", ""]
        if strategy.journal_target:
            lines += [f"Journal: {strategy.journal_target.name} (IF {strategy.journal_target.impact_factor})",
                      f"Fit: {strategy.journal_target.fit_score}/5", ""]
        if strategy.feasibility:
            lines += [f"Feasibility: {strategy.feasibility.overall_score}/5 | Go/No-Go: {strategy.feasibility.go_no_go}", ""]
        lines += [f"Hypotheses: {len(strategy.hypotheses)} | Risks: {len(strategy.risks)}",
                  f"Timeline: {strategy.timeline_weeks} weeks | Status: {strategy.status}", "=" * 60]
        return "\n".join(lines)
