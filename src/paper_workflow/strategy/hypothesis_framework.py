"""
Hypothesis Framework — Structured hypothesis generation, tracking, and validation.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Optional


@dataclass
class Hypothesis:
    """A single research hypothesis with evidence tracking."""
    id: str
    statement: str
    category: str  # primary, secondary, exploratory
    type: str  # descriptive, comparative, mechanistic, translational
    confidence: str = "hypothesis"
    required_evidence: list[str] = field(default_factory=list)
    supporting_data: list[str] = field(default_factory=list)
    contradicting_data: list[str] = field(default_factory=list)
    related_figures: list[str] = field(default_factory=list)
    related_methods: list[str] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict:
        return {
            "id": self.id, "statement": self.statement, "category": self.category,
            "type": self.type, "confidence": self.confidence,
            "required_evidence": self.required_evidence,
            "supporting_data": self.supporting_data,
            "contradicting_data": self.contradicting_data,
            "related_figures": self.related_figures,
            "related_methods": self.related_methods,
            "limitations": self.limitations,
            "created_at": self.created_at, "updated_at": self.updated_at,
        }

    def update_confidence(self, new_confidence: str) -> None:
        self.confidence = new_confidence
        self.updated_at = datetime.now().isoformat()

    def add_evidence(self, evidence: str, supports: bool = True) -> None:
        if supports:
            self.supporting_data.append(evidence)
        else:
            self.contradicting_data.append(evidence)
        self.updated_at = datetime.now().isoformat()


class HypothesisFramework:
    """Generates and manages research hypotheses."""

    TEMPLATES = {
        "descriptive": [
            "The {system} exhibits distinct {feature} patterns across {condition} conditions",
        ],
        "comparative": [
            "{feature} is significantly different between {condition_a} and {condition_b}",
            "The magnitude of {change} correlates with {clinical_variable}",
        ],
        "mechanistic": [
            "{upstream_factor} regulates {downstream_effect} through {mediator}",
            "{cell_type_a} communicates with {cell_type_b} via {ligand}-{receptor} axis",
        ],
        "translational": [
            "{molecular_feature} serves as a biomarker for {clinical_outcome}",
        ],
    }

    def __init__(self, project_root: Optional[Path] = None):
        self.project_root = project_root or self._find_project_root()

    def _find_project_root(self) -> Path:
        current = Path(__file__).resolve().parent
        for _ in range(10):
            if (current / "AGENTS.md").exists() or (current / "CLAUDE.md").exists():
                return current
            current = current.parent
        return Path.cwd()

    def generate_hypotheses(self, topic: Any, feasibility: Any) -> list[Hypothesis]:
        """Generate structured hypotheses from research topic."""
        hypotheses = []
        keywords = topic.keywords
        idea = topic.idea

        # H1: Primary descriptive/comparative
        hypotheses.append(Hypothesis(
            id="H1", category="primary", type="descriptive",
            statement=self._build_primary(idea, keywords),
            required_evidence=["Spatial/expression maps of key features",
                             "Statistical test results with effect sizes"],
            related_methods=["quality_control", "clustering", "annotation", "de_analysis"],
        ))

        # H2: Mechanistic
        hypotheses.append(Hypothesis(
            id="H2", category="secondary", type="mechanistic",
            statement=self._build_mechanistic(idea, keywords),
            required_evidence=["Pathway enrichment results",
                             "Cell-cell communication analysis", "Literature support"],
            related_methods=["pathway_analysis", "cell_communication", "network_analysis"],
        ))

        # H3: Cell-type/feature-specific
        hypotheses.append(Hypothesis(
            id="H3", category="secondary", type="comparative",
            statement="Specific cell populations show disproportionate vulnerability to condition-associated changes",
            required_evidence=["Cell-type-specific marker expression",
                             "Differential abundance analysis", "Per-cell-type pathway scores"],
            related_methods=["cell_type_annotation", "de_analysis", "pathway_analysis"],
        ))

        # H4: Exploratory/translational
        if feasibility and feasibility.overall_score >= 3.0:
            hypotheses.append(Hypothesis(
                id="H4", category="exploratory", type="translational",
                statement="Identified molecular signatures may serve as potential biomarkers or therapeutic targets",
                required_evidence=["Correlation with clinical variables",
                                 "External validation", "Classification performance metrics"],
                related_methods=["machine_learning", "clinical_correlation"],
            ))

        return hypotheses

    def _build_primary(self, idea: str, keywords: list[str]) -> str:
        kw_lower = " ".join(keywords).lower()
        if "aging" in idea.lower():
            return "Molecular profiling reveals age-associated changes in tissue architecture and cellular composition"
        elif "disease" in idea.lower() or "vs" in idea.lower():
            return "Molecular differences between conditions identify disease-specific signatures"
        return f"Systematic analysis reveals distinct molecular organization of {idea[:40]}..."

    def _build_mechanistic(self, idea: str, keywords: list[str]) -> str:
        kw_lower = " ".join(keywords).lower()
        if "aging" in idea.lower():
            return "Age-associated pathway alterations in specific cell types drive functional decline through altered intercellular communication"
        elif "immune" in kw_lower:
            return "Immune cell infiltration and activation patterns drive tissue remodeling through cytokine-mediated signaling"
        return "Specific signaling pathways in identified cell populations drive the observed molecular phenotypes"

    def validate_hypothesis(self, hypothesis: Hypothesis) -> dict:
        """Check if a hypothesis has sufficient evidence."""
        result = {
            "hypothesis_id": hypothesis.id,
            "current_confidence": hypothesis.confidence,
            "supporting_count": len(hypothesis.supporting_data),
            "contradicting_count": len(hypothesis.contradicting_data),
            "required_evidence_met": [],
            "required_evidence_missing": [],
        }
        for req in hypothesis.required_evidence:
            found = any(req.lower() in s.lower() for s in hypothesis.supporting_data)
            (result["required_evidence_met"] if found else result["required_evidence_missing"]).append(req)
        if (len(result["required_evidence_missing"]) == 0
                and len(hypothesis.contradicting_data) == 0
                and len(hypothesis.supporting_data) >= len(hypothesis.required_evidence)):
            new_conf = "supported" if hypothesis.category != "primary" else "validated"
            hypothesis.update_confidence(new_conf)
            result["auto_upgraded_to"] = new_conf
        return result
