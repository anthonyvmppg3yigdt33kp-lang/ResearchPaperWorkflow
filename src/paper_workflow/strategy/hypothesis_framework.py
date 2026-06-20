"""
Hypothesis Framework — Structured hypothesis generation, tracking, and validation.

v3.0: Upgraded from single-layer PICO to 3-layer evidence structure:
  Layer 1 — Clinical Hypothesis (clinical claim, actionable decision)
  Layer 2 — Mechanistic Hypothesis (molecular/cellular mechanism)
  Layer 3 — Testable Hypothesis (statistically falsifiable prediction)

Each hypothesis MUST include: positive evidence, negative evidence,
alternative explanations, negative controls, sensitivity analyses,
and validation requirements.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Optional


class HypothesisLayer(Enum):
    CLINICAL = "clinical"
    MECHANISTIC = "mechanistic"
    TESTABLE = "testable"


class Falsifiability(Enum):
    STRONG = "strong"        # Clear null hypothesis, pre-registered analysis
    MODERATE = "moderate"    # Testable but post-hoc
    WEAK = "weak"            # Descriptive, not strictly falsifiable
    UNSPECIFIED = "unspecified"


@dataclass
class Hypothesis:
    """A single research hypothesis with 3-layer evidence tracking (v3.0).

    Each hypothesis now requires:
    - Layer designation (clinical/mechanistic/testable)
    - Falsifiability rating
    - Supporting AND contradicting evidence
    - Alternative explanations
    - Negative controls
    - Sensitivity analysis plan
    - Validation requirements (internal + external)
    """
    id: str
    statement: str
    layer: str = "testable"  # clinical, mechanistic, testable
    category: str = "primary"  # primary, secondary, exploratory
    type: str = "descriptive"  # descriptive, comparative, mechanistic, translational
    confidence: str = "hypothesis"
    falsifiability: str = "unspecified"

    # Evidence tracking (v3.0 enhanced)
    required_evidence: list[str] = field(default_factory=list)
    supporting_data: list[str] = field(default_factory=list)
    contradicting_data: list[str] = field(default_factory=list)
    alternative_explanations: list[str] = field(default_factory=list)
    negative_controls: list[str] = field(default_factory=list)

    # Validation requirements (v3.0 new)
    sensitivity_analyses: list[str] = field(default_factory=list)
    internal_validation: list[str] = field(default_factory=list)
    external_validation: list[str] = field(default_factory=list)

    # Cross-references
    related_clinical_hypothesis: str = ""  # id of parent clinical hypothesis
    related_mechanistic_hypothesis: str = ""  # id of parent mechanistic hypothesis
    related_figures: list[str] = field(default_factory=list)
    related_methods: list[str] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)

    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict:
        return {
            "id": self.id, "statement": self.statement, "layer": self.layer,
            "category": self.category, "type": self.type,
            "confidence": self.confidence, "falsifiability": self.falsifiability,
            "required_evidence": self.required_evidence,
            "supporting_data": self.supporting_data,
            "contradicting_data": self.contradicting_data,
            "alternative_explanations": self.alternative_explanations,
            "negative_controls": self.negative_controls,
            "sensitivity_analyses": self.sensitivity_analyses,
            "internal_validation": self.internal_validation,
            "external_validation": self.external_validation,
            "related_clinical_hypothesis": self.related_clinical_hypothesis,
            "related_mechanistic_hypothesis": self.related_mechanistic_hypothesis,
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

    def add_alternative_explanation(self, explanation: str) -> None:
        self.alternative_explanations.append(explanation)
        self.updated_at = datetime.now().isoformat()

    @property
    def evidence_ratio(self) -> float:
        """Ratio of supporting to total evidence (0.0-1.0)."""
        total = len(self.supporting_data) + len(self.contradicting_data)
        if total == 0:
            return 0.5
        return len(self.supporting_data) / total

    @property
    def is_falsifiable(self) -> bool:
        return self.falsifiability in ("strong", "moderate")


class HypothesisFramework:
    """Generates and manages research hypotheses with 3-layer evidence structure (v3.0).

    Layer 1 — Clinical: What clinical problem does this solve?
    Layer 2 — Mechanistic: What molecular/cellular mechanism explains it?
    Layer 3 — Testable: What specific, falsifiable prediction can we test?

    Each hypothesis is linked across layers via related_clinical_hypothesis
    and related_mechanistic_hypothesis fields, forming an evidence chain.
    """

    # v3.0: 3-layer templates replacing single-layer PICO templates
    TEMPLATES = {
        "clinical": [
            "In {population}, {molecular_feature} distinguishes {condition_a} from {condition_b}, "
            "enabling {clinical_decision} that is currently limited by {unmet_need}",
            "{intervention_or_marker} improves {clinical_outcome} in {population} "
            "by addressing {mechanism_gap} that current {gold_standard} cannot resolve",
        ],
        "mechanistic": [
            "{upstream_factor} regulates {downstream_effect} through {mediator} "
            "in {cell_type}, forming a {pathway} axis that explains {clinical_observation}",
            "{cell_type_a} communicates with {cell_type_b} via {ligand}-{receptor} signaling, "
            "creating a {spatial_context} niche that drives {phenotype}",
            "The {molecular_program} in {cell_population} is activated by {stimulus} "
            "and suppressed by {inhibitor}, indicating {regulatory_logic}",
        ],
        "testable": [
            "{feature} is significantly {direction} in {condition_a} vs {condition_b} "
            "(effect size ≥ {delta}, p < {alpha}, {covariates} adjusted)",
            "The association between {exposure} and {outcome} is mediated by {mediator} "
            "(indirect effect β ≠ 0), and not confounded by {confounder}",
            "{cell_population} abundance in {spatial_region} correlates with {clinical_variable} "
            "(Spearman ρ ≥ {rho}, FDR < 0.05), independent of {batch_effect}",
        ],
    }

    # v3.0: Mandatory evidence dimensions for every hypothesis
    EVIDENCE_DIMENSIONS = [
        "positive_evidence",       # Data supporting the hypothesis
        "negative_evidence",       # Data contradicting or failing to support
        "alternative_explanations", # Other interpretations of the same data
        "negative_controls",        # What result would falsify this hypothesis
        "sensitivity_analyses",     # Robustness checks
        "internal_validation",      # Within-dataset validation
        "external_validation",      # Independent cohort/platform validation
    ]

    def __init__(self, project_root: Optional[Path] = None, clinical_context: Optional[dict] = None):
        self.project_root = project_root or self._find_project_root()
        self.clinical_context = clinical_context or {}

    def _find_project_root(self) -> Path:
        current = Path(__file__).resolve().parent
        for _ in range(10):
            if (current / "AGENTS.md").exists() or (current / "CLAUDE.md").exists():
                return current
            current = current.parent
        return Path.cwd()

    def generate_hypotheses(self, topic: Any, feasibility: Any,
                            clinical_value: Optional[dict] = None) -> list[Hypothesis]:
        """Generate 3-layer structured hypotheses from research topic (v3.0).

        Layer 1 (Clinical): H-C1 — What clinical decision does this change?
        Layer 2 (Mechanistic): H-M1, H-M2 — What molecular mechanism explains it?
        Layer 3 (Testable): H-T1, H-T2 — What specific prediction can we falsify?

        Returns hypotheses linked across layers via related_*_hypothesis fields.
        """
        hypotheses = []
        keywords = topic.keywords if hasattr(topic, 'keywords') else []
        idea = topic.idea if hasattr(topic, 'idea') else str(topic)
        ctx = clinical_value or self.clinical_context

        # === LAYER 1: Clinical Hypothesis ===
        h_c1 = Hypothesis(
            id="H-C1", layer="clinical", category="primary", type="translational",
            falsifiability="moderate",
            statement=self._build_clinical(idea, keywords, ctx),
            required_evidence=[
                "Clinical outcome association with molecular feature",
                "Effect size clinically meaningful (e.g., OR≥2 or AUC≥0.75)",
                "Independent of known confounders",
                "Replicated in ≥1 independent cohort or cross-validation",
            ],
            alternative_explanations=[
                "Observed association due to confounding by indication",
                "Molecular feature is a consequence, not cause, of clinical state",
                "Selection bias in cohort assembly",
            ],
            negative_controls=[
                "Association absent in unrelated clinical condition",
                "No association with technical covariates (batch, RIN, etc.)",
            ],
            sensitivity_analyses=[
                "E-value for unmeasured confounding",
                "Leave-one-(hospital/center/cohort)-out analysis",
            ],
            internal_validation=["K-fold cross-validation", "Bootstrap CI stability"],
            external_validation=["Independent cohort with same clinical endpoint"],
            related_methods=["clinical_correlation", "machine_learning", "survival_analysis"],
        )
        hypotheses.append(h_c1)

        # === LAYER 2: Mechanistic Hypotheses ===
        h_m1 = Hypothesis(
            id="H-M1", layer="mechanistic", category="secondary", type="mechanistic",
            falsifiability="moderate",
            related_clinical_hypothesis="H-C1",
            statement=self._build_mechanistic_v3(idea, keywords, ctx, slot=1),
            required_evidence=[
                "Pathway/gene-set enrichment in relevant cell types",
                "Cell-cell communication inference (ligand-receptor pairs)",
                "Transcription factor regulon activity",
                "Spatial co-localization of key cell types (if spatial data)",
            ],
            alternative_explanations=[
                "Pathway signal reflects tissue composition, not regulation",
                "Ligand-receptor co-expression is stochastic, not functional",
                "Observed mechanism is downstream of primary cause",
            ],
            negative_controls=[
                "Pathway NOT enriched in irrelevant cell types",
                "Ligand-receptor pair NOT co-expressed in negative-control tissue",
            ],
            sensitivity_analyses=[
                "Multiple pathway database comparison (GO, KEGG, Reactome, MSigDB)",
                "Permutation-based null distribution for cell-cell communication",
            ],
            internal_validation=["Independent enrichment method (GSEA + over-representation)"],
            external_validation=["Public dataset with similar condition"],
            related_methods=["pathway_analysis", "cell_communication", "network_analysis",
                           "spatial_analysis", "transcription_factor_analysis"],
        )
        hypotheses.append(h_m1)

        h_m2 = Hypothesis(
            id="H-M2", layer="mechanistic", category="secondary", type="mechanistic",
            falsifiability="moderate",
            related_clinical_hypothesis="H-C1",
            statement=self._build_mechanistic_v3(idea, keywords, ctx, slot=2),
            required_evidence=[
                "Cell-type-specific gene expression patterns",
                "Differential abundance/proportion of key cell types",
                "Trajectory/pseudotime analysis showing state transitions",
                "Multi-omics integration (if available)",
            ],
            alternative_explanations=[
                "Cell-type proportion differences reflect sampling bias",
                "Gene expression differences are technical, not biological",
                "Cellular state is plastic, not a stable subpopulation",
            ],
            negative_controls=[
                "Cell-type proportions stable in control condition",
                "Marker expression specific to annotated cell type",
            ],
            sensitivity_analyses=[
                "Multiple cell-type annotation methods comparison",
                "Different resolution parameters for clustering",
            ],
            internal_validation=["Marker gene validation against reference atlas"],
            external_validation=["Cross-platform validation (scRNA + spatial)"],
            related_methods=["cell_type_annotation", "de_analysis", "trajectory_analysis",
                           "multi_omics_integration"],
        )
        hypotheses.append(h_m2)

        # === LAYER 3: Testable Hypotheses ===
        h_t1 = Hypothesis(
            id="H-T1", layer="testable", category="primary", type="comparative",
            falsifiability="strong",
            related_mechanistic_hypothesis="H-M1",
            statement=self._build_testable(idea, keywords, ctx, slot=1),
            required_evidence=[
                "Exact p-value with effect size and 95% CI",
                "Multiple testing corrected (FDR < 0.05)",
                "Covariate-adjusted (age, sex, batch)",
                "Power analysis confirming sample size adequacy",
            ],
            alternative_explanations=[
                "Significant result driven by outliers",
                "Batch effect not fully adjusted",
                "Multiple testing correction too conservative/liberal",
            ],
            negative_controls=[
                "Permutation test with shuffled labels",
                "Analysis in negative-control gene set",
            ],
            sensitivity_analyses=[
                "Non-parametric test confirmation",
                "Leave-one-sample-out stability",
                "Different covariate sets",
            ],
            internal_validation=["Split-half replication"],
            external_validation=["Same analysis in independent dataset"],
            related_methods=["de_analysis", "statistical_testing", "power_analysis"],
        )
        hypotheses.append(h_t1)

        h_t2 = Hypothesis(
            id="H-T2", layer="testable", category="secondary", type="comparative",
            falsifiability="strong",
            related_mechanistic_hypothesis="H-M2",
            statement=self._build_testable(idea, keywords, ctx, slot=2),
            required_evidence=[
                "Exact p-value with effect size and 95% CI",
                "Cell-type-level pseudobulk (NOT single-cell as unit)",
                "Independent replication in holdout samples",
                "Robust to alternative cell-type annotation",
            ],
            alternative_explanations=[
                "Cell-type proportion confounds DE result",
                "Doublet contamination inflates cell-type-specific signal",
                "Ambient RNA contaminates cell-type signature",
            ],
            negative_controls=[
                "Pseudobulk analysis with permuted cell-type labels",
                "Analysis excluding top-expressed ambient genes",
            ],
            sensitivity_analyses=[
                "Different pseudobulk aggregation methods",
                "Varying minimum cells-per-sample thresholds",
            ],
            internal_validation=["Within-cell-type consistency across samples"],
            external_validation=["Cross-study replication of cell-type signature"],
            related_methods=["pseudobulk_analysis", "cell_type_annotation", "de_analysis"],
        )
        hypotheses.append(h_t2)

        # H4: Exploratory translational (only if feasible)
        if feasibility and (hasattr(feasibility, 'overall_score') and feasibility.overall_score >= 3.0):
            h_t3 = Hypothesis(
                id="H-T3", layer="testable", category="exploratory", type="translational",
                falsifiability="weak",
                related_clinical_hypothesis="H-C1",
                statement="Identified molecular signatures may serve as potential biomarkers or therapeutic targets, "
                          "requiring prospective validation before clinical application",
                required_evidence=[
                    "Classification AUC ≥ 0.75 with 95% CI",
                    "Calibration curve (Brier score)",
                    "Decision curve analysis (net benefit)",
                    "Comparison with existing clinical scores",
                ],
                alternative_explanations=[
                    "Model learns batch/center, not biology",
                    "Performance inflation from data leakage",
                ],
                negative_controls=["Performance not better than clinical baseline"],
                sensitivity_analyses=["Nested CV vs simple CV", "External validation cohort"],
                internal_validation=["Nested cross-validation"],
                external_validation=["PROSCRIBED: must NOT claim clinical utility without prospective study"],
                related_methods=["machine_learning", "model_evaluation", "decision_curve_analysis"],
            )
            hypotheses.append(h_t3)

        return hypotheses

    def _build_clinical(self, idea: str, keywords: list[str], ctx: dict) -> str:
        population = ctx.get("population", "patients")
        unmet_need = ctx.get("unmet_need", "accurate molecular classification")
        clinical_decision = ctx.get("clinical_decision", "treatment stratification")
        gold_standard = ctx.get("gold_standard", "histopathological assessment")

        kw_lower = " ".join(keywords).lower() if keywords else idea.lower()
        if "aging" in idea.lower():
            return (f"Age-associated molecular changes in {ctx.get('tissue', 'tissue')} "
                    f"define functional decline trajectories that are not captured by "
                    f"{gold_standard}, limiting {clinical_decision} in {population}")
        elif any(w in kw_lower for w in ["disease", "vs", "versus", "compar"]):
            return (f"Molecular profiling of {ctx.get('tissue', 'diseased tissue')} "
                    f"identifies subtypes that explain differential {ctx.get('outcome', 'clinical outcomes')} "
                    f"beyond {gold_standard}, enabling {clinical_decision}")
        return (f"Systematic molecular characterization of {idea[:60]} reveals "
                f"clinically actionable subtypes addressing the unmet need for {unmet_need}")

    def _build_mechanistic_v3(self, idea: str, keywords: list[str], ctx: dict, slot: int = 1) -> str:
        kw_lower = " ".join(keywords).lower() if keywords else idea.lower()
        tissue = ctx.get("tissue", "the affected tissue")
        if slot == 1:
            if "aging" in idea.lower():
                return (f"Age-associated pathway alterations in specific cell types "
                        f"drive functional decline through altered intercellular communication "
                        f"and progressive loss of tissue homeostasis in {tissue}")
            elif "immune" in kw_lower:
                return (f"Immune cell infiltration and activation patterns drive "
                        f"tissue remodeling through cytokine-mediated signaling cascades "
                        f"that create a self-reinforcing inflammatory niche")
            return (f"Specific signaling pathways in identified cell populations "
                    f"drive the observed molecular phenotypes through coordinated "
                    f"transcriptional programs and paracrine signaling")
        else:
            if "aging" in idea.lower():
                return (f"Cell-type composition shifts and cell-state transitions "
                        f"in {tissue} reflect altered differentiation trajectories "
                        f"driven by age-dependent epigenetic and microenvironmental changes")
            return (f"Cellular heterogeneity within {tissue} defines functional "
                    f"subpopulations whose relative abundance and activation state "
                    f"determine tissue-level phenotype severity")

    def _build_testable(self, idea: str, keywords: list[str], ctx: dict, slot: int = 1) -> str:
        tissue = ctx.get("tissue", "the tissue")
        condition_a = ctx.get("condition_a", "Condition A")
        condition_b = ctx.get("condition_b", "Condition B")
        if slot == 1:
            return (f"Key molecular pathways are significantly dysregulated "
                    f"({ctx.get('effect_direction', 'upregulated')}, FDR<0.05, |log2FC|≥0.5) "
                    f"in {condition_a} compared to {condition_b}, "
                    f"after adjusting for age, sex, and batch effects")
        else:
            return (f"Specific cell populations show disproportionate changes "
                    f"in abundance and transcriptional state between conditions, "
                    f"with effect sizes exceeding technical variation "
                    f"(pseudobulk DE, FDR<0.05, |log2FC|≥1.0)")

    def validate_hypothesis(self, hypothesis: Hypothesis) -> dict:
        """Check if a hypothesis has sufficient evidence across all 7 dimensions (v3.0)."""
        result = {
            "hypothesis_id": hypothesis.id,
            "layer": hypothesis.layer,
            "current_confidence": hypothesis.confidence,
            "evidence_ratio": hypothesis.evidence_ratio,
            "supporting_count": len(hypothesis.supporting_data),
            "contradicting_count": len(hypothesis.contradicting_data),
            "alternative_explanations_count": len(hypothesis.alternative_explanations),
            "negative_controls_count": len(hypothesis.negative_controls),
            "required_evidence_met": [],
            "required_evidence_missing": [],
            "dimension_completeness": {},
            "auto_upgraded_to": None,
        }

        # Check required evidence
        for req in hypothesis.required_evidence:
            found = any(req.lower() in s.lower() for s in hypothesis.supporting_data)
            (result["required_evidence_met"] if found else result["required_evidence_missing"]).append(req)

        # Check dimension completeness
        dims = {
            "positive_evidence": len(hypothesis.supporting_data) > 0,
            "negative_evidence": len(hypothesis.contradicting_data) > 0,
            "alternative_explanations": len(hypothesis.alternative_explanations) > 0,
            "negative_controls": len(hypothesis.negative_controls) > 0,
            "sensitivity_analyses": len(hypothesis.sensitivity_analyses) > 0,
            "internal_validation": len(hypothesis.internal_validation) > 0,
            "external_validation": len(hypothesis.external_validation) > 0,
        }
        result["dimension_completeness"] = dims
        result["dimension_score"] = sum(1 for v in dims.values() if v) / len(dims)

        # Auto-upgrade confidence if all evidence dimensions met
        all_evidence_met = (len(result["required_evidence_missing"]) == 0
                           and len(hypothesis.contradicting_data) == 0
                           and len(hypothesis.supporting_data) >= len(hypothesis.required_evidence)
                           and result["dimension_score"] >= 0.7)
        if all_evidence_met:
            new_conf = "supported" if hypothesis.category != "primary" else "validated"
            hypothesis.update_confidence(new_conf)
            result["auto_upgraded_to"] = new_conf
        elif len(hypothesis.contradicting_data) > len(hypothesis.supporting_data):
            hypothesis.update_confidence("contradicted")
            result["auto_upgraded_to"] = "contradicted"

        return result

    def generate_evidence_chain(self, hypotheses: list[Hypothesis]) -> dict:
        """Generate cross-layer evidence chain linking clinical→mechanistic→testable."""
        chain = {"clinical": [], "mechanistic": [], "testable": [], "edges": []}
        for h in hypotheses:
            chain[h.layer].append(h.id)
            if h.related_clinical_hypothesis:
                chain["edges"].append({"from": h.related_clinical_hypothesis, "to": h.id, "layer": h.layer})
            if h.related_mechanistic_hypothesis:
                chain["edges"].append({"from": h.related_mechanistic_hypothesis, "to": h.id, "layer": h.layer})
        return chain
