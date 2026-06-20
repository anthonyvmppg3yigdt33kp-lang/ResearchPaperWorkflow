"""
Statistical Analysis Plan Generator — Pre-specifies analysis before execution.

v3.0: Used in the new design_analysis_plan stage (S4.5) — statistician involved
BEFORE data audit and figure planning. Generates frozen SAP.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

import yaml


@dataclass
class StatisticalAnalysisPlan:
    plan_id: str
    paper_id: str = ""
    version: str = "1.0"
    frozen: bool = False
    frozen_at: str = ""
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    # Endpoints
    primary_endpoint: dict = field(default_factory=dict)
    secondary_endpoints: list[dict] = field(default_factory=list)
    exploratory_endpoints: list[dict] = field(default_factory=list)

    # Design
    statistical_unit: str = "patient"
    covariates: list[str] = field(default_factory=list)
    batch_effect_strategy: str = "include_as_covariate"
    multiple_testing_strategy: str = "FDR"
    missing_data_strategy: str = "complete_case"

    # Analysis details
    subgroup_analyses: list[dict] = field(default_factory=list)
    sensitivity_analyses: list[dict] = field(default_factory=list)
    negative_controls: list[dict] = field(default_factory=list)
    external_validation_plan: dict = field(default_factory=dict)

    # Documentation
    sample_size_rationale: str = ""
    power_analysis: dict = field(default_factory=dict)
    exploratory_vs_confirmatory: dict = field(default_factory=dict)
    software_planned: list[str] = field(default_factory=list)
    deviations_policy: str = "All unplanned analyses will be explicitly marked as exploratory"

    def to_dict(self) -> dict:
        return {
            "plan_id": self.plan_id, "paper_id": self.paper_id,
            "version": self.version, "frozen": self.frozen,
            "frozen_at": self.frozen_at, "created_at": self.created_at,
            "primary_endpoint": self.primary_endpoint,
            "secondary_endpoints": self.secondary_endpoints,
            "exploratory_endpoints": self.exploratory_endpoints,
            "statistical_unit": self.statistical_unit,
            "covariates": self.covariates,
            "batch_effect_strategy": self.batch_effect_strategy,
            "multiple_testing_strategy": self.multiple_testing_strategy,
            "missing_data_strategy": self.missing_data_strategy,
            "subgroup_analyses": self.subgroup_analyses,
            "sensitivity_analyses": self.sensitivity_analyses,
            "negative_controls": self.negative_controls,
            "external_validation_plan": self.external_validation_plan,
            "sample_size_rationale": self.sample_size_rationale,
            "power_analysis": self.power_analysis,
            "exploratory_vs_confirmatory": self.exploratory_vs_confirmatory,
            "software_planned": self.software_planned,
            "deviations_policy": self.deviations_policy,
        }


class AnalysisPlanGenerator:
    """Generates pre-specified Statistical Analysis Plans (SAP).

    Design principle: SAP must be FROZEN before any primary analysis runs.
    Post-hoc analyses must be explicitly marked as exploratory.
    """

    DEFAULT_COVARIATES = ["age", "sex"]
    DEFAULT_BATCH_VARS = ["batch", "sequencing_run", "center"]

    def __init__(self, project_root: Optional[Path] = None):
        self.project_root = project_root or Path.cwd()

    def generate(self, hypotheses: list, study_design: Optional[dict] = None,
                 data_inventory: Optional[dict] = None) -> StatisticalAnalysisPlan:
        """Generate a comprehensive SAP from hypotheses and study design."""
        sd = study_design or {}
        di = data_inventory or {}

        plan = StatisticalAnalysisPlan(
            plan_id=f"SAP_{datetime.now().strftime('%Y%m%d')}",
            paper_id=sd.get("paper_id", ""),
            statistical_unit=self._determine_unit(di),
            covariates=self._plan_covariates(di),
            batch_effect_strategy=self._plan_batch_strategy(di),
            sample_size_rationale=self._plan_sample_size(di),
        )

        # Define endpoints from hypotheses
        primary, secondary, exploratory = self._define_endpoints(hypotheses, sd)
        plan.primary_endpoint = primary
        plan.secondary_endpoints = secondary
        plan.exploratory_endpoints = exploratory

        # Plan analyses
        plan.subgroup_analyses = self._plan_subgroups(sd)
        plan.sensitivity_analyses = self._plan_sensitivity(hypotheses)
        plan.negative_controls = self._plan_negative_controls(hypotheses)
        plan.external_validation_plan = self._plan_validation(sd)

        # Mark each analysis as confirmatory or exploratory
        plan.exploratory_vs_confirmatory = {
            "primary": "confirmatory",
            "secondary": "confirmatory_with_correction",
            "subgroup": "exploratory" if not sd.get("pre_specified_subgroups") else "confirmatory",
            "sensitivity": "exploratory",
            "negative_controls": "confirmatory",
        }

        return plan

    def _define_endpoints(self, hypotheses: list, study_design: dict) -> tuple:
        primary = {"name": "", "variable": "", "measurement_method": "",
                   "analysis_metric": "", "timepoint": "baseline"}
        secondary = []
        exploratory = []

        for h in hypotheses:
            if hasattr(h, 'category') and h.category == "primary" and hasattr(h, 'layer') and h.layer == "testable":
                primary["name"] = h.statement[:120] if hasattr(h, 'statement') else str(h)[:120]
                primary["variable"] = study_design.get("primary_outcome", "outcome_variable")
                primary["analysis_metric"] = "difference" if "between" in str(h).lower() else "association"
            elif hasattr(h, 'category') and h.category == "secondary":
                secondary.append({"name": getattr(h, 'statement', str(h))[:120],
                                 "variable": "", "analysis_metric": "association"})
            else:
                h_text = getattr(h, 'statement', str(h))[:120] if hasattr(h, 'statement') else str(h)[:120]
                exploratory.append({"name": h_text, "variable": "", "confirmatory": False})

        return primary, secondary, exploratory

    def _determine_unit(self, data_inventory: dict) -> str:
        return data_inventory.get("statistical_unit", data_inventory.get("unit", "patient"))

    def _plan_covariates(self, data_inventory: dict) -> list[str]:
        covariates = list(self.DEFAULT_COVARIATES)
        batch_vars = data_inventory.get("batch_variables", [])
        for bv in batch_vars:
            if bv not in covariates:
                covariates.append(bv)
        return covariates

    def _plan_batch_strategy(self, data_inventory: dict) -> str:
        if data_inventory.get("batch_variables"):
            return "include_as_covariate_in_all_models"
        return "not_applicable"

    def _plan_sample_size(self, data_inventory: dict) -> str:
        n = data_inventory.get("n_samples", data_inventory.get("n_patients", 0))
        if n > 0:
            return f"Available sample: n={n}. Post-hoc power analysis planned."
        return "Sample size to be confirmed after data audit"

    def _plan_subgroups(self, study_design: dict) -> list[dict]:
        subgroups = []
        pre_specified = study_design.get("pre_specified_subgroups", [])
        for sg in pre_specified:
            subgroups.append({"variable": sg, "rationale": "Pre-specified in study protocol",
                            "interaction_test": True})
        return subgroups

    def _plan_sensitivity(self, hypotheses: list) -> list[dict]:
        analyses = [
            {"name": "Leave-one-out stability", "what_is_tested": "Influential sample effects",
             "method": "Leave-one-sample-out, compare effect sizes"},
            {"name": "Non-parametric confirmation", "what_is_tested": "Distributional assumptions",
             "method": "Wilcoxon/Spearman as non-parametric alternative"},
            {"name": "E-value computation", "what_is_tested": "Unmeasured confounding",
             "method": "E-value for point estimate and CI limit"},
        ]
        return analyses

    def _plan_negative_controls(self, hypotheses: list) -> list[dict]:
        return [
            {"name": "Permutation test", "expected_result": "Null distribution centered at zero",
             "method": "Shuffle group labels 1000x, recompute test statistic"},
            {"name": "Negative control gene set", "expected_result": "No enrichment",
             "method": "Test against genes not expressed in tissue of interest"},
        ]

    def _plan_validation(self, study_design: dict) -> dict:
        return {
            "planned": study_design.get("external_validation_planned", False),
            "cohort_source": study_design.get("validation_cohort", ""),
            "sample_size": study_design.get("validation_n", 0),
            "key_endpoints": ["primary_endpoint"],
        }

    def freeze(self, plan: StatisticalAnalysisPlan) -> StatisticalAnalysisPlan:
        """Freeze the SAP — no further modifications allowed."""
        plan.frozen = True
        plan.frozen_at = datetime.now().isoformat()
        plan.version = f"{plan.version}-frozen"
        return plan

    def export_yaml(self, plan: StatisticalAnalysisPlan, output_path: Path) -> Path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            yaml.dump(plan.to_dict(), f, allow_unicode=True, default_flow_style=False)
        return output_path
