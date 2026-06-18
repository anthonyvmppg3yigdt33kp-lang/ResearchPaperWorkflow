"""
Feasibility Assessor — Data, methods, journal fit, and timeline evaluation.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Optional


@dataclass
class FeasibilityReport:
    """Feasibility assessment report."""
    overall_score: float = 0.0
    data_score: float = 0.0
    methods_score: float = 0.0
    journal_fit_score: float = 0.0
    timeline_feasible: bool = True
    data_concerns: list[str] = field(default_factory=list)
    methods_concerns: list[str] = field(default_factory=list)
    journal_concerns: list[str] = field(default_factory=list)
    timeline_concerns: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)
    go_no_go: str = "go"
    assessed_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict:
        return {
            "overall_score": self.overall_score, "data_score": self.data_score,
            "methods_score": self.methods_score, "journal_fit_score": self.journal_fit_score,
            "timeline_feasible": self.timeline_feasible,
            "data_concerns": self.data_concerns, "methods_concerns": self.methods_concerns,
            "journal_concerns": self.journal_concerns, "timeline_concerns": self.timeline_concerns,
            "recommendations": self.recommendations, "go_no_go": self.go_no_go,
            "assessed_at": self.assessed_at,
        }


class FeasibilityAssessor:
    """Assesses research feasibility across data, methods, journal fit, and timeline."""

    def __init__(self, project_root: Optional[Path] = None):
        self.project_root = project_root or self._find_project_root()

    def _find_project_root(self) -> Path:
        current = Path(__file__).resolve().parent
        for _ in range(10):
            if (current / "AGENTS.md").exists() or (current / "CLAUDE.md").exists():
                return current
            current = current.parent
        return Path.cwd()

    def assess(self, topic: Any, journal: Any) -> FeasibilityReport:
        """Comprehensive feasibility assessment."""
        report = FeasibilityReport()
        report.data_score, report.data_concerns = self._assess_data(topic)
        report.methods_score, report.methods_concerns = self._assess_methods(topic)
        report.journal_fit_score, report.journal_concerns = self._assess_journal_fit(topic, journal)
        report.timeline_feasible, report.timeline_concerns = self._assess_timeline(topic)
        report.overall_score = round(
            report.data_score * 0.35 + report.methods_score * 0.30
            + report.journal_fit_score * 0.20
            + (5.0 if report.timeline_feasible else 2.0) * 0.15, 1)
        report.go_no_go = self._decide_go_no_go(report)
        report.recommendations = self._generate_recommendations(report)
        return report

    def _assess_data(self, topic: Any) -> tuple[float, list[str]]:
        concerns = []
        score = 3.0
        if not topic.data_types:
            return 1.0, ["No data types specified"]
        score += min(2.0, len(topic.data_types) * 0.5)
        if topic.estimated_sample_size:
            n = topic.estimated_sample_size
            if n < 3:
                concerns.append(f"Very small sample size (n={n})")
                score -= 1.5
            elif n < 6:
                concerns.append(f"Small sample size (n={n}) — limited power")
                score -= 0.5
            else:
                score += 0.5
        return min(5.0, max(1.0, round(score, 1))), concerns

    def _assess_methods(self, topic: Any) -> tuple[float, list[str]]:
        concerns = []
        score = 3.0
        established = {"quality control": 0.5, "dimensionality reduction": 0.5,
                       "clustering": 0.5, "differential": 0.5, "pathway": 0.5,
                       "spatial": 0.3, "deconvolution": 0.3}
        methods_text = " ".join(topic.methods_required).lower()
        for method, weight in established.items():
            if method in methods_text:
                score += weight
        if "novel" in methods_text:
            concerns.append("Novel method requires additional validation")
            score -= 0.5
        return min(5.0, max(1.0, round(score, 1))), concerns

    def _assess_journal_fit(self, topic: Any, journal: Any) -> tuple[float, list[str]]:
        concerns = []
        score = float(getattr(journal, 'fit_score', 3))
        if hasattr(journal, 'impact_factor') and hasattr(topic, 'innovation_level'):
            if journal.impact_factor >= 20 and topic.innovation_level < 3:
                concerns.append(f"Innovation level ({topic.innovation_level}/5) may be insufficient for {journal.name}")
                score -= 1.0
        estimated_figures = len(topic.methods_required) // 2 + 2
        if hasattr(journal, 'figure_limit') and estimated_figures > journal.figure_limit:
            concerns.append(f"Estimated {estimated_figures} figures exceeds limit of {journal.figure_limit}")
            score -= 0.5
        return min(5.0, max(1.0, round(score, 1))), concerns

    def _assess_timeline(self, topic: Any) -> tuple[bool, list[str]]:
        concerns = []
        required_weeks = 4 + (2 if len(topic.data_types) > 2 else 0) + (2 if len(topic.methods_required) > 5 else 0)
        feasible = required_weeks <= 12
        if not feasible:
            concerns.append(f"Estimated {required_weeks} weeks exceeds 12-week limit")
        return feasible, concerns

    def _decide_go_no_go(self, report: FeasibilityReport) -> str:
        if report.overall_score >= 3.5: return "go"
        elif report.overall_score >= 2.5: return "conditional_go"
        return "no_go"

    def _generate_recommendations(self, report: FeasibilityReport) -> list[str]:
        recs = []
        if report.data_score < 3.0: recs.append("Improve data quality or supplement with external data")
        if report.methods_score < 3.0: recs.append("Validate methods on test data before full analysis")
        if report.journal_fit_score < 3.0: recs.append("Consider alternative target journals")
        if not report.timeline_feasible: recs.append("Reduce scope or extend timeline")
        if report.go_no_go == "conditional_go": recs.append("Proceed with caution — address concerns first")
        if not recs: recs.append("Proceed — feasibility looks good")
        return recs
