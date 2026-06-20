"""
Clinical Value Assessor — Evaluates whether a research topic has genuine clinical value.

v3.0: Used in select_topic stage BEFORE feasibility assessment.
Outputs clinical_value_matrix.yaml — the foundational document for evidence-centric architecture.

Key question: Does this research change a clinical decision, or just describe biology?
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

import yaml


@dataclass
class ClinicalValueMatrix:
    """Comprehensive clinical value assessment for a research topic."""

    # Core clinical context
    clinical_scenario: str = ""
    unmet_need: str = ""
    gold_standard: str = ""
    decision_bottleneck: str = ""
    actionable_decision: str = ""
    target_population: str = ""

    # Evidence assessment
    translational_pathway: str = ""
    minimum_publishable_evidence: str = ""
    maximum_publishable_evidence: str = ""
    competing_approaches: list[str] = field(default_factory=list)
    evidence_gap: str = ""

    # Scoring (0-5 scale)
    clinical_impact_score: float = 0.0
    novelty_score: float = 0.0
    feasibility_score: float = 0.0
    overall_score: float = 0.0

    # Recommendations
    recommendation: str = ""  # PROCEED / RECONSIDER / LOW_CLINICAL_VALUE
    risk_factors: list[str] = field(default_factory=list)
    mitigation_strategies: list[str] = field(default_factory=list)

    assessed_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict:
        return {
            "clinical_scenario": self.clinical_scenario,
            "unmet_need": self.unmet_need,
            "gold_standard": self.gold_standard,
            "decision_bottleneck": self.decision_bottleneck,
            "actionable_decision": self.actionable_decision,
            "target_population": self.target_population,
            "translational_pathway": self.translational_pathway,
            "minimum_publishable_evidence": self.minimum_publishable_evidence,
            "maximum_publishable_evidence": self.maximum_publishable_evidence,
            "competing_approaches": self.competing_approaches,
            "evidence_gap": self.evidence_gap,
            "clinical_impact_score": self.clinical_impact_score,
            "novelty_score": self.novelty_score,
            "feasibility_score": self.feasibility_score,
            "overall_score": self.overall_score,
            "recommendation": self.recommendation,
            "risk_factors": self.risk_factors,
            "mitigation_strategies": self.mitigation_strategies,
            "assessed_at": self.assessed_at,
        }


class ClinicalValueAssessor:
    """Evaluates research topic clinical value across impact, novelty, and feasibility dimensions.

    Design principle: If clinical_impact_score < 2.0, the topic is flagged as LOW_CLINICAL_VALUE
    and the researcher is advised to reconsider or strengthen the clinical framing.
    """

    # Clinical impact rubric (0-5)
    IMPACT_RUBRIC = {
        5: "Changes clinical guidelines or standard of care",
        4: "Directly informs a specific clinical decision with measurable benefit",
        3: "Addresses a recognized clinical gap with plausible impact pathway",
        2: "Provides biological insight potentially relevant to clinical practice",
        1: "Descriptive biology with distant/uncertain clinical relevance",
        0: "No identifiable clinical connection",
    }

    # Novelty rubric (0-5)
    NOVELTY_RUBRIC = {
        5: "First-in-class: no prior study addresses this question",
        4: "Significantly advances beyond published work with new methodology or data type",
        3: "Incremental but meaningful advance over existing literature",
        2: "Replication or confirmation with minor extensions",
        1: "Well-studied question with marginal novelty",
        0: "Already conclusively answered in literature",
    }

    def __init__(self, clinical_context: Optional[dict] = None):
        self.clinical_context = clinical_context or {}

    def assess(self, topic: Any) -> ClinicalValueMatrix:
        """Assess clinical value of a research topic.

        Extracts clinical context from topic idea, keywords, and domain.
        Returns ClinicalValueMatrix with scores and recommendation.
        """
        matrix = ClinicalValueMatrix()

        # Extract topic properties
        idea = getattr(topic, "idea", str(topic))
        keywords = getattr(topic, "keywords", [])
        domain = getattr(topic, "domain", "")
        kw_lower = " ".join(keywords).lower() if keywords else idea.lower()

        # Fill clinical context from topic + provided context
        ctx = self.clinical_context
        matrix.clinical_scenario = ctx.get("clinical_scenario", f"Research on {idea[:80]}")
        matrix.unmet_need = ctx.get("unmet_need", self._infer_unmet_need(kw_lower))
        matrix.gold_standard = ctx.get("gold_standard", self._infer_gold_standard(kw_lower, domain))
        matrix.decision_bottleneck = ctx.get("decision_bottleneck",
            f"Current {matrix.gold_standard} does not provide molecular-level resolution")
        matrix.actionable_decision = ctx.get("actionable_decision",
            self._infer_actionable_decision(kw_lower))
        matrix.target_population = ctx.get("target_population", "Patients requiring molecular stratification")
        matrix.translational_pathway = ctx.get("translational_pathway",
            "Biomarker discovery → retrospective validation → prospective validation → clinical implementation")
        matrix.evidence_gap = ctx.get("evidence_gap",
            f"No validated molecular classifier exists to guide {matrix.actionable_decision}")

        # Score dimensions
        matrix.clinical_impact_score = self._score_clinical_impact(matrix)
        matrix.novelty_score = self._score_novelty(topic)
        matrix.feasibility_score = self._score_feasibility(topic)
        matrix.overall_score = self._compute_overall(matrix)

        # Generate recommendation
        matrix.recommendation = self._generate_recommendation(matrix)
        matrix.risk_factors = self._identify_risks(matrix, topic)
        matrix.mitigation_strategies = self._suggest_mitigations(matrix.risk_factors)

        return matrix

    def _infer_unmet_need(self, kw_lower: str) -> str:
        if any(w in kw_lower for w in ["diagnos", "classif", "subtype", "biomark"]):
            return "Accurate molecular diagnosis/classification beyond histopathology"
        if any(w in kw_lower for w in ["prognos", "surviv", "outcome", "predict"]):
            return "Reliable prognostic/predictive biomarkers to guide treatment intensity"
        if any(w in kw_lower for w in ["therap", "drug", "treat", "target"]):
            return "Identifiable therapeutic targets for precision intervention"
        if any(w in kw_lower for w in ["mechan", "pathway", "signal"]):
            return "Mechanistic understanding to enable rational therapeutic development"
        return "Molecular characterization to address an unmet clinical need"

    def _infer_gold_standard(self, kw_lower: str, domain: str) -> str:
        if "spatial" in kw_lower or "histolog" in kw_lower:
            return "Histopathological assessment (H&E/IHC)"
        if "imag" in kw_lower or "mri" in kw_lower or "radiology" in kw_lower:
            return "Radiological assessment"
        if "eeg" in kw_lower or "seeg" in kw_lower:
            return "Electrophysiological monitoring"
        return "Clinical assessment and standard laboratory tests"

    def _infer_actionable_decision(self, kw_lower: str) -> str:
        if any(w in kw_lower for w in ["diagnos", "classif"]):
            return "Molecular diagnosis and subtype classification"
        if any(w in kw_lower for w in ["prognos", "predict"]):
            return "Risk stratification and treatment planning"
        if any(w in kw_lower for w in ["therap", "target"]):
            return "Selection of targeted therapy"
        return "Precision medicine decision-making"

    def _score_clinical_impact(self, matrix: ClinicalValueMatrix) -> float:
        """Score clinical impact based on decision change potential, population, and outcome severity."""
        score = 2.0  # Default: biological insight with potential relevance

        # Upgrade for clear clinical decision
        if matrix.actionable_decision and matrix.unmet_need:
            score += 1.0
        # Upgrade for specific target population
        if matrix.target_population and "requiring" not in matrix.target_population.lower():
            score += 0.5
        # Upgrade for clear evidence gap
        if matrix.evidence_gap and "no validated" in matrix.evidence_gap.lower():
            score += 0.5
        # Upgrade if gold standard is clearly inadequate
        if matrix.decision_bottleneck and "does not" in matrix.decision_bottleneck.lower():
            score += 0.5

        return min(5.0, score)

    def _score_novelty(self, topic: Any) -> float:
        """Score novelty based on literature gap and methodological innovation."""
        score = 2.5  # Default: moderate novelty
        idea = getattr(topic, "idea", str(topic)).lower()
        keywords = getattr(topic, "keywords", [])

        # Check for novelty signals
        novel_signals = ["single-cell", "spatial", "multi-omics", "integration",
                        "first", "novel", "new", "unprecedented", "atlas"]
        method_signals = ["deep learning", "neural network", "transformer",
                         "graph", "causal", "mendelian"]

        signal_count = sum(1 for s in novel_signals if s in idea or any(s in kw.lower() for kw in keywords))
        method_count = sum(1 for s in method_signals if s in idea)

        score += signal_count * 0.3 + method_count * 0.5
        return min(5.0, score)

    def _score_feasibility(self, topic: Any) -> float:
        """Score feasibility based on data availability and methodological tractability."""
        feasibility = getattr(topic, "feasibility_score", None)
        if feasibility is not None:
            return float(feasibility)
        return 3.0  # Default: moderately feasible

    def _compute_overall(self, matrix: ClinicalValueMatrix) -> float:
        """Compute weighted overall score."""
        return round(
            0.40 * matrix.clinical_impact_score +
            0.30 * matrix.novelty_score +
            0.30 * matrix.feasibility_score, 2
        )

    def _generate_recommendation(self, matrix: ClinicalValueMatrix) -> str:
        """Generate Go/No-Go recommendation."""
        if matrix.clinical_impact_score < 2.0:
            return "LOW_CLINICAL_VALUE — Reconsider clinical framing or select different topic"
        if matrix.overall_score >= 4.0:
            return "STRONG_PROCEED — High clinical value with feasible path to publication"
        if matrix.overall_score >= 3.0:
            return "PROCEED — Adequate clinical value; strengthen clinical framing in Introduction"
        if matrix.overall_score >= 2.0:
            return "RECONSIDER — Marginal clinical value; explicit justification required to proceed"
        return "DO_NOT_PROCEED — Insufficient clinical value for high-impact medical journal"

    def _identify_risks(self, matrix: ClinicalValueMatrix, topic: Any) -> list[str]:
        """Identify key risks to clinical impact."""
        risks = []
        if matrix.clinical_impact_score < 3.0:
            risks.append("Low clinical impact — paper may be viewed as purely descriptive")
        if matrix.novelty_score < 3.0:
            risks.append("Limited novelty — risk of 'me-too' paper rejection")
        keywords = getattr(topic, "keywords", [])
        kw_lower = " ".join(keywords).lower() if keywords else ""
        if "public data" in kw_lower or "publicly available" in kw_lower:
            risks.append("Public data only — need strong clinical framing to justify value")
        if not any(w in kw_lower for w in ["validation", "external", "independent"]):
            risks.append("No external validation planned — downgrade clinical claims accordingly")
        return risks

    def _suggest_mitigations(self, risks: list[str]) -> list[str]:
        """Suggest mitigation strategies for identified risks."""
        mitigations = []
        for risk in risks:
            if "clinical impact" in risk.lower():
                mitigations.append("Strengthen Introduction with explicit clinical decision context")
            if "novelty" in risk.lower():
                mitigations.append("Highlight methodological innovation or novel data integration")
            if "public data" in risk.lower():
                mitigations.append("Add independent validation cohort or external dataset")
            if "validation" in risk.lower():
                mitigations.append("Plan external validation OR explicitly acknowledge as limitation")
        return mitigations

    def export_yaml(self, matrix: ClinicalValueMatrix, output_path: Path) -> Path:
        """Export clinical value matrix to YAML file."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            yaml.dump(matrix.to_dict(), f, allow_unicode=True, default_flow_style=False)
        return output_path
