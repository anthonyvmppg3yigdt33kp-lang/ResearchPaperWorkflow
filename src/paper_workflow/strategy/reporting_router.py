"""
Reporting Guideline Router — Maps paper type to EQUATOR Network reporting guideline.

v3.0: Used in target_journal stage. Generates compliance checklist automatically.
Covers: STROBE, TRIPOD+AI, PRISMA, CONSORT, STARD, ARRIVE, STROBE-MR, FAIR.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import ClassVar, Optional

import yaml


@dataclass
class GuidelineChecklist:
    guideline_name: str
    version: str
    paper_type: str
    total_items: int
    items: list[dict] = field(default_factory=list)
    official_url: str = ""
    completed_count: int = 0
    compliance_percentage: float = 0.0
    generated_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict:
        return {
            "guideline_name": self.guideline_name, "version": self.version,
            "paper_type": self.paper_type, "total_items": self.total_items,
            "items": self.items, "official_url": self.official_url,
            "completed_count": self.completed_count,
            "compliance_percentage": self.compliance_percentage,
            "generated_at": self.generated_at,
        }


class ReportingGuidelineRouter:
    """Routes paper types to appropriate EQUATOR Network reporting guidelines.

    v3.0 design principle: Reporting guideline selection should happen at project
    creation time (target_journal stage), not at submission time. The checklist
    then gates each stage.
    """

    GUIDELINE_MAP: ClassVar[dict] = {
        ("original_research", "observational"): ("STROBE", "2007"),
        ("original_research", "cohort"): ("STROBE", "2007"),
        ("original_research", "case_control"): ("STROBE", "2007"),
        ("original_research", "cross_sectional"): ("STROBE", "2007"),
        ("original_research", "clinical_trial"): ("CONSORT", "2025"),
        ("original_research", "rct"): ("CONSORT", "2025"),
        ("original_research", "diagnostic"): ("STARD", "2015"),
        ("original_research", "prediction_model"): ("TRIPOD+AI", "2024"),
        ("original_research", "mendelian_randomization"): ("STROBE-MR", "2021"),
        ("systematic_review", "meta_analysis"): ("PRISMA", "2020"),
        ("systematic_review", None): ("PRISMA", "2020"),
        ("methods", None): ("FAIR", "2016"),
        ("data_resource", None): ("FAIR", "2016"),
        ("animal_study", None): ("ARRIVE", "2.0"),
        ("clinical_research", None): ("STROBE", "2007"),
    }

    URL_MAP: ClassVar[dict] = {
        "STROBE": "https://www.strobe-statement.org/",
        "TRIPOD+AI": "https://www.tripod-statement.org/",
        "PRISMA": "https://www.prisma-statement.org/",
        "CONSORT": "https://www.consort-spirit.org/",
        "STARD": "https://www.equator-network.org/reporting-guidelines/stard/",
        "ARRIVE": "https://arriveguidelines.org/",
        "STROBE-MR": "https://www.strobe-mr.org/",
        "FAIR": "https://www.go-fair.org/fair-principles/",
    }

    STROBE_ITEMS = [
        (1, "Title & Abstract", "Indicate study design; provide informative summary", True),
        (2, "Introduction", "Background/rationale", True),
        (3, "Introduction", "Objectives including prespecified hypotheses", True),
        (4, "Methods", "Study design — present key elements early", True),
        (5, "Methods", "Setting, locations, relevant dates", True),
        (6, "Methods", "Eligibility criteria, sources, selection methods", True),
        (7, "Methods", "Clearly define outcomes, exposures, predictors, confounders", True),
        (8, "Methods", "Data sources and measurement details for each variable", True),
        (9, "Methods", "Describe efforts to address potential bias sources", True),
        (10, "Methods", "Explain how study size was arrived at", True),
        (11, "Methods", "Explain handling of quantitative variables", True),
        (12, "Methods", "Statistical methods including confounding control", True),
        (13, "Results", "Numbers of individuals at each study stage", True),
        (14, "Results", "Descriptive characteristics of study participants", True),
        (15, "Results", "Outcome events or summary measures", True),
        (16, "Results", "Unadjusted and adjusted estimates with precision", True),
        (17, "Results", "Other analyses (subgroups, interactions, sensitivity)", False),
        (18, "Discussion", "Summarise key results with reference to objectives", True),
        (19, "Discussion", "Discuss limitations", True),
        (20, "Discussion", "Cautious interpretation considering all evidence", True),
        (21, "Discussion", "Discuss generalisability", True),
        (22, "Other", "Funding source and role of funders", True),
    ]

    TRIPOD_AI_ITEMS = [
        (1, "Title", "Identify as developing/evaluating multivariable prediction model", True),
        (2, "Abstract", "Structured abstract per TRIPOD+AI for Abstracts", True),
        (3, "Introduction", "Healthcare context and rationale", True),
        (4, "Introduction", "Study objectives (development, validation, or both)", True),
        (5, "Methods", "Data sources and study design", True),
        (6, "Methods", "Participants — eligibility, setting, recruitment", True),
        (7, "Methods", "Data preparation — cleaning, feature engineering", True),
        (8, "Methods", "Outcome definition including time horizon", True),
        (9, "Methods", "Predictors — definition, measurement, timing", True),
        (10, "Methods", "Sample size — justification or power calculation", True),
        (11, "Methods", "Model development — algorithms, tuning, feature selection", True),
        (12, "Methods", "Model performance — discrimination, calibration, overall", True),
        (13, "Methods", "Model evaluation — internal/external validation", True),
        (14, "Methods", "Performance across subgroups (fairness)", True),
        (15, "Methods", "Model output and clinical utility assessment", True),
        (16, "Methods", "Transparency — model specification, interpretability", True),
        (17, "Methods", "Software, packages, versions, random seeds", True),
        (18, "Open Science", "Data and code availability statements", True),
        (19, "PPI", "Patient and public involvement in study design", False),
        (20, "Results", "Participant flow and characteristics", True),
        (21, "Results", "Model development results — selected predictors, hyperparameters", True),
        (22, "Results", "Model specification — final model form", True),
        (23, "Results", "Model performance — discrimination, calibration", True),
        (24, "Results", "Model evaluation — external validation performance", True),
        (25, "Discussion", "Limitations including bias assessment (PROBAST+AI)", True),
        (26, "Discussion", "Interpretation — clinical implications", True),
        (27, "Discussion", "Implications for practice and future research", True),
    ]

    STROBE_MR_ITEMS = [
        (1, "Title & Abstract", "Indicate MR as study design", True),
        (2, "Introduction", "Scientific rationale, justify MR approach", True),
        (3, "Introduction", "Prespecified causal hypotheses under specific assumptions", True),
        (4, "Methods", "Data sources — setting, participants, genetic variants, phenotypes", True),
        (5, "Methods", "Explicitly state IV assumptions: relevance, independence, exclusion restriction", True),
        (6, "Methods", "Main analysis — IV methods, handling of variants, effect measures", True),
        (7, "Methods", "Assessment of assumptions — F-statistic, heterogeneity, pleiotropy", True),
        (8, "Methods", "Sensitivity analyses — MR-Egger, weighted median, MR-PRESSO, etc.", True),
        (9, "Methods", "Software, packages, pre-registration", True),
        (10, "Results", "Descriptive data — participant numbers, summary statistics", True),
        (11, "Results", "Main MR results with effect sizes and confidence intervals", True),
        (12, "Results", "Sensitivity analysis results — heterogeneity, pleiotropy tests", True),
        (13, "Discussion", "Key results and limitations including IV assumption validity", True),
        (14, "Discussion", "Causal interpretation consistent with MR assumptions", True),
        (15, "Discussion", "Generalisability and clinical/public health implications", True),
        (16, "Other", "Funding, data availability, conflicts of interest", True),
    ]

    def __init__(self):
        pass

    def route(self, paper_type: str, study_design: Optional[dict] = None) -> GuidelineChecklist:
        """Route paper type to appropriate reporting guideline and generate checklist."""
        design_type = study_design.get("design_type", "") if study_design else ""

        # Find best match
        guideline_name, version = "STROBE", "2007"  # Default
        for (pt, dt), (gn, gv) in self.GUIDELINE_MAP.items():
            if pt == paper_type and (dt is None or dt == design_type):
                guideline_name, version = gn, gv
                break

        # Generate items based on guideline
        if guideline_name == "STROBE":
            items = self._build_items(self.STROBE_ITEMS)
        elif guideline_name == "TRIPOD+AI":
            items = self._build_items(self.TRIPOD_AI_ITEMS)
        elif guideline_name == "STROBE-MR":
            items = self._build_items(self.STROBE_MR_ITEMS)
        elif guideline_name == "PRISMA":
            items = self._build_prisma_items()
        elif guideline_name == "CONSORT":
            items = self._build_consort_items()
        elif guideline_name == "STARD":
            items = self._build_stard_items()
        elif guideline_name == "ARRIVE":
            items = self._build_arrive_items()
        elif guideline_name == "FAIR":
            items = self._build_fair_items()
        else:
            items = self._build_items(self.STROBE_ITEMS)

        total = len(items)
        required = sum(1 for i in items if i.get("required", True))

        return GuidelineChecklist(
            guideline_name=guideline_name, version=version,
            paper_type=paper_type, total_items=total, items=items,
            official_url=self.URL_MAP.get(guideline_name, ""),
        )

    def _build_items(self, items: list[tuple]) -> list[dict]:
        return [{"item_number": n, "section": s, "description": d,
                 "required": r, "status": "pending"} for n, s, d, r in items]

    def _build_prisma_items(self) -> list[dict]:
        prisma = [
            (1, "Title", "Identify as systematic review", True),
            (2, "Abstract", "Structured per PRISMA 2020 for Abstracts", True),
            (3, "Introduction", "Rationale", True),
            (4, "Introduction", "Objectives", True),
            (5, "Methods", "Eligibility criteria", True),
            (6, "Methods", "Information sources and search strategy", True),
            (7, "Methods", "Selection process", True),
            (8, "Methods", "Data collection process", True),
            (9, "Methods", "Data items", True),
            (10, "Methods", "Risk of bias assessment", True),
            (11, "Methods", "Effect measures", True),
            (12, "Methods", "Synthesis methods", True),
            (13, "Methods", "Reporting bias assessment", True),
            (14, "Methods", "Certainty assessment", True),
            (15, "Results", "Study selection flow diagram", True),
            (16, "Results", "Study characteristics", True),
            (17, "Results", "Risk of bias in studies", True),
            (18, "Results", "Results of individual studies", True),
            (19, "Results", "Results of syntheses", True),
            (20, "Results", "Reporting biases", True),
            (21, "Results", "Certainty of evidence", True),
            (22, "Discussion", "General interpretation", True),
            (23, "Discussion", "Limitations of evidence and review", True),
            (24, "Discussion", "Implications", True),
            (25, "Other", "Registration and protocol", True),
            (26, "Other", "Support and competing interests", True),
            (27, "Other", "Data/code availability", True),
        ]
        return self._build_items(prisma)

    def _build_consort_items(self) -> list[dict]:
        return self._build_items([
            (1, "Title & Abstract", "Identify as randomized trial", True),
            (2, "Open Science", "Trial registration details", True),
            (3, "Open Science", "Protocol and SAP access", True),
            (4, "Open Science", "Data sharing statement", True),
            (5, "Open Science", "Funding sources and role", True),
            (6, "Introduction", "Scientific background and rationale", True),
            (7, "Introduction", "Specific objectives related to benefits and harms", True),
            (8, "Methods", "Trial design description", True),
            (9, "Methods", "Changes to methods after commencement", False),
            (10, "Methods", "Eligibility criteria", True),
            (11, "Methods", "Settings and locations", True),
            (12, "Methods", "Interventions with replication detail", True),
            (13, "Methods", "Outcomes — prespecified primary and secondary", True),
            (14, "Methods", "Sample size determination", True),
            (15, "Methods", "Randomization — sequence generation, allocation concealment", True),
            (16, "Methods", "Blinding details", True),
            (17, "Methods", "Statistical methods for primary/secondary/harms", True),
            (18, "Results", "Participant flow diagram", True),
            (19, "Results", "Recruitment period and follow-up", True),
            (20, "Results", "Baseline characteristics", True),
            (21, "Results", "Numbers analyzed per group (ITT)", True),
            (22, "Results", "Outcomes — effect sizes with precision", True),
            (23, "Results", "Harms results", True),
            (24, "Discussion", "Limitations", True),
            (25, "Discussion", "Interpretation — benefits and harms", True),
            (26, "Discussion", "Generalisability", True),
        ])

    def _build_stard_items(self) -> list[dict]:
        return self._build_items([
            (1, "Title & Abstract", "Identify as diagnostic accuracy study", True),
            (2, "Abstract", "Structured per STARD 2015 for Abstracts", True),
            (3, "Introduction", "Clinical background, index test role", True),
            (4, "Introduction", "Study objectives and hypotheses", True),
            (5, "Methods", "Data collection timing (prospective/retrospective)", True),
            (6, "Methods", "Eligibility criteria", True),
            (7, "Methods", "Participant identification basis", True),
            (8, "Methods", "Setting and timing of recruitment", True),
            (9, "Methods", "Whether consecutive/random/convenience series", True),
            (10, "Methods", "Index test — sufficient detail for replication", True),
            (11, "Methods", "Reference standard — rationale and detail", True),
            (12, "Methods", "Blinding of index test and reference standard assessors", True),
            (13, "Methods", "Methods for estimating diagnostic accuracy", True),
            (14, "Methods", "Handling of indeterminate/missing results", True),
            (15, "Methods", "Sample size determination", True),
            (16, "Results", "Participant flow diagram", True),
            (17, "Results", "Baseline characteristics", True),
            (18, "Results", "Distribution of disease severity and alternative diagnoses", True),
            (19, "Results", "Cross-tabulation of index vs. reference", True),
            (20, "Results", "Diagnostic accuracy with 95% CIs", True),
            (21, "Discussion", "Limitations", True),
            (22, "Discussion", "Implications for practice", True),
            (23, "Other", "Registration and protocol", True),
            (24, "Other", "Funding source", True),
        ])

    def _build_arrive_items(self) -> list[dict]:
        return self._build_items([
            (1, "Study Design", "Groups compared including controls, experimental unit", True),
            (2, "Sample Size", "Exact n per group; how sample size decided", True),
            (3, "Inclusion/Exclusion", "Criteria for including/excluding animals/data", True),
            (4, "Randomisation", "Method and strategy to minimise confounders", True),
            (5, "Blinding", "Who was blinded during experiment and assessment", True),
            (6, "Outcome Measures", "Clearly defined, primary for hypothesis-testing", True),
            (7, "Statistical Methods", "Methods per analysis, assumptions assessment", True),
            (8, "Experimental Animals", "Species, strain, sex, age, weight, health status", True),
            (9, "Experimental Procedures", "What, how, when, how often, where, why", True),
            (10, "Results", "Summary statistics per group, effect size with CI", True),
            (11, "Ethical Statement", "Ethical review permissions, guidelines", True),
            (12, "Interpretation", "Interpretation considering objectives and limitations", True),
            (13, "Generalisability", "Comment on translation to other species/systems", False),
            (14, "Protocol Registration", "Where protocol can be accessed", False),
            (15, "Data Access", "Where data can be accessed", True),
            (16, "Declaration", "Competing interests and funding", True),
        ])

    def _build_fair_items(self) -> list[dict]:
        return self._build_items([
            (1, "Findable", "Data assigned globally unique persistent identifier (DOI)", True),
            (2, "Findable", "Data described with rich metadata", True),
            (3, "Findable", "Metadata include data identifier", True),
            (4, "Findable", "Data registered in searchable resource (GEO/SRA/Zenodo)", True),
            (5, "Accessible", "Data retrievable by identifier using standard protocol", True),
            (6, "Accessible", "Metadata accessible even when data unavailable", True),
            (7, "Interoperable", "Data use formal, shared language (standard formats)", True),
            (8, "Interoperable", "Data use FAIR vocabularies (gene symbols, ontology terms)", True),
            (9, "Interoperable", "Data include qualified references to other data", True),
            (10, "Reusable", "Data richly described with accurate attributes", True),
            (11, "Reusable", "Data released with clear usage license (CC-BY, CC0)", True),
            (12, "Reusable", "Data associated with detailed provenance", True),
            (13, "Reusable", "Data meet domain-relevant community standards", True),
        ])

    def export_yaml(self, checklist: GuidelineChecklist, output_path: Path) -> Path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            yaml.dump(checklist.to_dict(), f, allow_unicode=True, default_flow_style=False)
        return output_path
