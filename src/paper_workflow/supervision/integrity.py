"""
Integrity Gates — Automated manuscript quality and integrity checks.

16 rules across 3 severity levels. Critical failures block pipeline progress.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional


@dataclass
class GateResult:
    rule: str
    severity: str
    passed: bool
    message: str = ""
    details: dict = field(default_factory=dict)
    checked_at: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class IntegrityReport:
    report_id: str = field(default_factory=lambda: f"ir_{datetime.now().strftime('%Y%m%d%H%M%S')}")
    paper_id: str = ""
    checked_at: str = field(default_factory=lambda: datetime.now().isoformat())
    results: list[GateResult] = field(default_factory=list)
    passed: bool = True
    critical_failures: int = 0
    high_failures: int = 0
    medium_failures: int = 0
    low_failures: int = 0

    @property
    def has_critical_failures(self) -> bool:
        return self.critical_failures > 0

    @property
    def blocks_pipeline(self) -> bool:
        return self.has_critical_failures

    def to_dict(self) -> dict:
        return {"report_id": self.report_id, "paper_id": self.paper_id,
                "checked_at": self.checked_at, "passed": self.passed,
                "critical_failures": self.critical_failures, "high_failures": self.high_failures,
                "medium_failures": self.medium_failures, "low_failures": self.low_failures,
                "results": [{"rule": r.rule, "severity": r.severity, "passed": r.passed,
                             "message": r.message, "details": r.details} for r in self.results]}


class IntegrityGateChecker:
    """Runs integrity and quality checks on manuscript artifacts (v3.0).

    v3.0 expands from 16 to 41 gates across 7 categories:
      A. Citation & Claim (5 gates, v2 legacy)
      B. Clinical Design (5 gates, v3 new)
      C. Data & Bias (5 gates, v3 new)
      D. Statistics & Models (5 gates, v3 new)
      E. Single-Cell & Spatial Omics (5 gates, v3 new)
      F. AI / Machine Learning (5 gates, v3 new)
      G. Format & Completeness (11 gates, v2 legacy + v3 upgrades)
    """

    # =========================================================================
    # v3.0: 41 gates total (16 original + 25 new medical evidence gates)
    # =========================================================================
    GATES = {
        # ---- A. Citation & Claim Integrity (5 CRITICAL, v2 legacy) ----
        "bibtex_citation_existence": {"rule": "bibtex_citation_existence", "severity": "critical",
                                      "category": "citation_claim",
                                      "description": "Every \\cite{} must have a BibTeX entry"},
        "citation_evidence_traceability": {"rule": "citation_evidence_traceability", "severity": "critical",
                                           "category": "citation_claim",
                                           "description": "Citations must be traceable to citation_evidence.csv"},
        "results_no_citations": {"rule": "results_no_citations", "severity": "critical",
                                 "category": "citation_claim",
                                 "description": "Results must contain NO citation commands"},
        "claim_artifact_binding": {"rule": "claim_artifact_binding", "severity": "critical",
                                   "category": "citation_claim",
                                   "description": "Every result claim must bind to existing figure/table/artifact"},
        "figures_referenced": {"rule": "figures_referenced", "severity": "critical",
                               "category": "citation_claim",
                               "description": "Every figure must be referenced in manuscript"},

        # ---- B. Clinical Design Gates (5 CRITICAL, v3 new) ----
        "study_design_declared": {"rule": "study_design_declared", "severity": "critical",
                                  "category": "clinical_design",
                                  "description": "Study design explicitly declared (cohort/case-control/cross-sectional/diagnostic/RCT)"},
        "clinical_question_actionable": {"rule": "clinical_question_actionable", "severity": "high",
                                         "category": "clinical_design",
                                         "description": "Research question maps to a specific clinical decision or mechanism gap"},
        "inclusion_exclusion_complete": {"rule": "inclusion_exclusion_complete", "severity": "critical",
                                         "category": "clinical_design",
                                         "description": "Inclusion and exclusion criteria fully specified"},
        "endpoint_definition_complete": {"rule": "endpoint_definition_complete", "severity": "critical",
                                         "category": "clinical_design",
                                         "description": "Primary and secondary endpoints clearly defined with measurement methods"},
        "ethics_irb_or_public_exemption": {"rule": "ethics_irb_or_public_exemption", "severity": "critical",
                                           "category": "clinical_design",
                                           "description": "IRB/ethics approval, informed consent, or public data exemption documented"},

        # ---- C. Data & Bias Gates (5 CRITICAL, v3 new) ----
        "patient_level_independence": {"rule": "patient_level_independence", "severity": "critical",
                                       "category": "data_bias",
                                       "description": "Statistical unit is patient/donor, NOT cell/spot/ROI (pseudoreplication v3 upgrade)"},
        "batch_confounding_audit": {"rule": "batch_confounding_audit", "severity": "high",
                                    "category": "data_bias",
                                    "description": "Disease group NOT completely confounded with batch/center/platform"},
        "missing_data_strategy": {"rule": "missing_data_strategy", "severity": "high",
                                  "category": "data_bias",
                                  "description": "Missing data handling strategy explicitly stated"},
        "train_test_leakage_check": {"rule": "train_test_leakage_check", "severity": "critical",
                                     "category": "data_bias",
                                     "description": "No information leakage between training and test/validation sets"},
        "sample_overlap_check": {"rule": "sample_overlap_check", "severity": "critical",
                                 "category": "data_bias",
                                 "description": "No sample overlap between discovery and validation cohorts (MR/GWAS/ML)"},

        # ---- D. Statistics & Model Gates (5 HIGH, v3 new) ----
        "statistical_analysis_plan_exists": {"rule": "statistical_analysis_plan_exists", "severity": "critical",
                                             "category": "statistics_model",
                                             "description": "Statistical Analysis Plan (SAP) frozen before primary analysis"},
        "effect_size_ci_reported": {"rule": "effect_size_ci_reported", "severity": "high",
                                    "category": "statistics_model",
                                    "description": "Every quantitative claim includes effect size AND confidence interval (not just p-value)"},
        "multiple_testing_control": {"rule": "multiple_testing_control", "severity": "critical",
                                     "category": "statistics_model",
                                     "description": "Multiple testing correction explicitly stated (FDR/Bonferroni/hierarchical)"},
        "model_calibration_reported": {"rule": "model_calibration_reported", "severity": "high",
                                       "category": "statistics_model",
                                       "description": "Prediction models report calibration (calibration curve, Brier score)"},
        "external_validation_or_limitation": {"rule": "external_validation_or_limitation", "severity": "critical",
                                              "category": "statistics_model",
                                              "description": "External validation performed OR conclusion explicitly downgraded"},

        # ---- E. Single-Cell & Spatial Omics Gates (5 HIGH, v3 new) ----
        "cell_annotation_evidence": {"rule": "cell_annotation_evidence", "severity": "high",
                                     "category": "sc_spatial_omics",
                                     "description": "Cell-type annotation supported by markers, reference mapping, AND manual review"},
        "spatial_region_registration": {"rule": "spatial_region_registration", "severity": "high",
                                        "category": "sc_spatial_omics",
                                        "description": "Spatial regions registered to pathology/imaging/electrophysiology where applicable"},
        "de_pseudobulk_required": {"rule": "de_pseudobulk_required", "severity": "high",
                                   "category": "sc_spatial_omics",
                                   "description": "Single-cell DE uses pseudobulk or mixed models, NOT cell-level tests as independent"},
        "integration_batch_risk": {"rule": "integration_batch_risk", "severity": "high",
                                   "category": "sc_spatial_omics",
                                   "description": "Integration method (Harmony/scVI/CCA) assessed for removing true biological variation"},
        "ligand_receptor_overclaim_check": {"rule": "ligand_receptor_overclaim_check", "severity": "high",
                                            "category": "sc_spatial_omics",
                                            "description": "Cell-cell communication results NOT overclaimed as causal interactions"},

        # ---- F. AI / Machine Learning Gates (5 HIGH, v3 new) ----
        "baseline_model_comparison": {"rule": "baseline_model_comparison", "severity": "high",
                                      "category": "ai_ml",
                                      "description": "ML model compared against traditional statistical baseline or clinical score"},
        "nested_cv_or_external_test": {"rule": "nested_cv_or_external_test", "severity": "critical",
                                       "category": "ai_ml",
                                       "description": "Nested cross-validation OR independent external test set used (not simple CV for small n)"},
        "calibration_decision_curve": {"rule": "calibration_decision_curve", "severity": "high",
                                       "category": "ai_ml",
                                       "description": "Clinical prediction models report calibration AND decision curve analysis (net benefit)"},
        "explainability_sanity_check": {"rule": "explainability_sanity_check", "severity": "high",
                                        "category": "ai_ml",
                                        "description": "SHAP/feature importance NOT interpreted as causal effects"},
        "deployment_claim_limited": {"rule": "deployment_claim_limited", "severity": "high",
                                     "category": "ai_ml",
                                     "description": "No clinical deployment claimed without prospective validation"},

        # ---- G. Format & Completeness (6 HIGH/MEDIUM, v2 legacy) ----
        "data_availability_statement": {"rule": "data_availability_statement", "severity": "high",
                                        "category": "format",
                                        "description": "Must contain Data Availability statement"},
        "code_availability_statement": {"rule": "code_availability_statement", "severity": "high",
                                        "category": "format",
                                        "description": "Must contain Code Availability statement"},
        "no_local_paths": {"rule": "no_local_paths", "severity": "high",
                           "category": "format",
                           "description": "No local filesystem paths or filenames in manuscript"},
        "methods_parameters_complete": {"rule": "methods_parameters_complete", "severity": "high",
                                        "category": "format",
                                        "description": "All key parameters and software versions included"},
        "discussion_limitations": {"rule": "discussion_limitations", "severity": "high",
                                   "category": "format",
                                   "description": "Discussion must include Limitations paragraph"},
        "results_no_overinterpretation": {"rule": "results_no_overinterpretation", "severity": "high",
                                          "category": "format",
                                          "description": "Results must not include mechanistic speculation or causal overclaim"},
        "statistics_reported": {"rule": "statistics_reported", "severity": "high",
                                "category": "format",
                                "description": "Quantitative claims must include test name, statistic, exact p-value, effect size, CI"},
        "pseudoreplication_check": {"rule": "pseudoreplication_check", "severity": "critical",
                                    "category": "format",
                                    "description": "Statistical unit matches biological replicate (upgraded to CRITICAL in v3)"},
        "section_length_minimum": {"rule": "section_length_minimum", "severity": "medium",
                                   "category": "format",
                                   "description": "Each section meets journal minimum length"},
        "no_bullets_in_prose": {"rule": "no_bullets_in_prose", "severity": "medium",
                                "category": "format",
                                "description": "Manuscript body uses natural prose, not bullet points"},
        "figure_count_requirements": {"rule": "figure_count_requirements", "severity": "medium",
                                      "category": "format",
                                      "description": "Figure count within journal limits"},
    }

    MIN_LENGTHS = {"introduction": 500, "methods": 800, "results": 800, "discussion": 600, "abstract": 100}

    # v3.0: Category-to-stage mapping for targeted gate activation
    CATEGORY_STAGE_MAP = {
        "citation_claim": ["write_introduction", "write_discussion", "assemble_manuscript", "integrity_check"],
        "clinical_design": ["select_topic", "formulate_hypotheses", "design_analysis_plan", "data_audit"],
        "data_bias": ["data_audit", "design_analysis_plan", "verify_methods", "integrity_check"],
        "statistics_model": ["design_analysis_plan", "verify_methods", "write_results", "integrity_check"],
        "sc_spatial_omics": ["data_audit", "run_analysis", "verify_methods", "write_methods"],
        "ai_ml": ["run_analysis", "verify_methods", "write_results", "integrity_check"],
        "format": ["write_methods", "write_results", "write_discussion", "assemble_manuscript", "integrity_check"],
    }

    def __init__(self, paper_dir: Path):
        self.paper_dir = Path(paper_dir)

    def run_all_checks(self, manuscript_sections: Optional[dict[str, str]] = None,
                       bibtex_path: Optional[Path] = None, citation_evidence: Optional[list] = None,
                       figure_plan: Optional[dict] = None, journal_target: Optional[dict] = None,
                       result_manifest: Optional[dict] = None,
                       # v3.0 new inputs
                       study_design: Optional[dict] = None,
                       data_inventory: Optional[dict] = None,
                       statistical_plan: Optional[dict] = None,
                       model_evaluation: Optional[dict] = None,
                       omics_metadata: Optional[dict] = None,
                       claim_ledger: Optional[list] = None,
                       active_categories: Optional[list[str]] = None,
                       ) -> IntegrityReport:
        """Run all integrity checks (v3.0 — 36 gates across 7 categories).

        New v3.0 inputs:
        - study_design: STUDY_PROTOCOL.yaml data for clinical design gates
        - data_inventory: data_inventory.yaml for data/bias gates
        - statistical_plan: STATISTICAL_ANALYSIS_PLAN.yaml for statistics gates
        - model_evaluation: Model performance metrics for AI/ML gates
        - omics_metadata: scRNA-seq/spatial metadata for omics gates
        - claim_ledger: CLAIM_LEDGER.csv for claim-artifact binding
        - active_categories: Limit checks to specific categories (None = all)
        """
        report = IntegrityReport()
        sections = manuscript_sections or {}
        cats = active_categories or list(self.CATEGORY_STAGE_MAP.keys())

        # ---- A. Citation & Claim ----
        if "citation_claim" in cats:
            if bibtex_path and sections:
                report.results.append(self._check_bibtex(sections, bibtex_path))
            if sections and "results" in sections:
                report.results.append(self._check_results_no_cite(sections["results"]))
            if figure_plan and sections:
                report.results.append(self._check_figures_refed(figure_plan, sections))
            if claim_ledger and sections:
                report.results.append(self._check_claim_binding(claim_ledger))

        # ---- B. Clinical Design Gates (v3.0) ----
        if "clinical_design" in cats:
            report.results.append(self._check_study_design_declared(sections, study_design))
            report.results.append(self._check_clinical_question(sections, study_design))
            report.results.append(self._check_inclusion_exclusion(sections, study_design))
            report.results.append(self._check_endpoint_definition(sections, study_design))
            report.results.append(self._check_ethics_statement(sections, study_design))

        # ---- C. Data & Bias Gates (v3.0) ----
        if "data_bias" in cats:
            report.results.append(self._check_patient_independence(sections, data_inventory))
            report.results.append(self._check_batch_confounding(sections, data_inventory))
            report.results.append(self._check_missing_data_strategy(sections, statistical_plan))
            report.results.append(self._check_train_test_leakage(sections, model_evaluation))
            report.results.append(self._check_sample_overlap(sections, data_inventory))

        # ---- D. Statistics & Model Gates (v3.0) ----
        if "statistics_model" in cats:
            report.results.append(self._check_sap_exists(statistical_plan))
            report.results.append(self._check_effect_size_ci(sections))
            report.results.append(self._check_multiple_testing(sections, statistical_plan))
            report.results.append(self._check_model_calibration(sections, model_evaluation))
            report.results.append(self._check_external_validation(sections, model_evaluation))

        # ---- E. Single-Cell & Spatial Omics Gates (v3.0) ----
        if "sc_spatial_omics" in cats:
            report.results.append(self._check_cell_annotation_evidence(sections, omics_metadata))
            report.results.append(self._check_spatial_registration(sections, omics_metadata))
            report.results.append(self._check_pseudobulk_de(sections, omics_metadata))
            report.results.append(self._check_integration_batch(sections, omics_metadata))
            report.results.append(self._check_lr_overclaim(sections))

        # ---- F. AI/ML Gates (v3.0) ----
        if "ai_ml" in cats:
            report.results.append(self._check_baseline_comparison(sections, model_evaluation))
            report.results.append(self._check_nested_cv(sections, model_evaluation))
            report.results.append(self._check_decision_curve(sections, model_evaluation))
            report.results.append(self._check_explainability(sections))
            report.results.append(self._check_deployment_claim(sections))

        # ---- G. Format & Completeness (v2 legacy + v3 upgrades) ----
        if "format" in cats:
            if sections:
                report.results.append(self._check_data_avail(sections))
                report.results.append(self._check_code_avail(sections))
                for name, content in sections.items():
                    report.results.append(self._check_section_len(name, content))
                    report.results.append(self._check_no_bullets(name, content))
                    report.results.append(self._check_no_paths(name, content))
            if sections and "results" in sections:
                report.results.append(self._check_stats(sections["results"]))
                report.results.append(self._check_overinterpretation(sections["results"]))
            if sections and "discussion" in sections:
                report.results.append(self._check_limitations(sections["discussion"]))
            if sections and "methods" in sections:
                report.results.append(self._check_methods_params(sections["methods"]))
            if data_inventory:
                report.results.append(self._check_pseudorep(data_inventory))
            if figure_plan:
                report.results.append(self._check_fig_count(figure_plan, journal_target))

        for r in report.results:
            if not r.passed:
                report.passed = False
                sev = r.severity
                if sev == "critical": report.critical_failures += 1
                elif sev == "high": report.high_failures += 1
                elif sev == "medium": report.medium_failures += 1
                else: report.low_failures += 1
        return report

    def _check_bibtex(self, sections: dict[str, str], bibtex_path: Path) -> GateResult:
        if not bibtex_path.exists():
            return GateResult(rule="bibtex_citation_existence", severity="critical", passed=False,
                              message=f"BibTeX file not found: {bibtex_path}")
        bibtex = bibtex_path.read_text(encoding="utf-8", errors="ignore")
        bib_keys = set(re.findall(r'@\w+\{([^,]+),', bibtex))
        all_text = " ".join(sections.values())
        cited = set(re.findall(r'\\cite\{([^}]+)\}', all_text))
        cited.update(re.findall(r'\\citep\{([^}]+)\}', all_text))
        cited.update(re.findall(r'\\citet\{([^}]+)\}', all_text))
        missing = cited - bib_keys
        if missing:
            return GateResult(rule="bibtex_citation_existence", severity="critical", passed=False,
                              message=f"{len(missing)} citation keys missing from BibTeX",
                              details={"missing_keys": list(missing)})
        return GateResult(rule="bibtex_citation_existence", severity="critical", passed=True,
                          message=f"All {len(cited)} citation keys found")

    def _check_results_no_cite(self, text: str) -> GateResult:
        cites = re.findall(r'\\cite\{([^}]+)\}', text)
        cites.extend(re.findall(r'\\citep\{([^}]+)\}', text))
        cites.extend(re.findall(r'\\citet\{([^}]+)\}', text))
        if cites:
            return GateResult(rule="results_no_citations", severity="critical", passed=False,
                              message=f"Results contains {len(cites)} citation(s)", details={"citations": cites})
        return GateResult(rule="results_no_citations", severity="critical", passed=True,
                          message="Results is citation-free")

    def _check_data_avail(self, sections: dict[str, str]) -> GateResult:
        all_text = " ".join(sections.values()).lower()
        found = any(ind in all_text for ind in ["data availability", "accession number", "geo:", "repository"])
        return GateResult(rule="data_availability_statement", severity="high", passed=found,
                          message="Statement found" if found else "Missing data availability statement")

    def _check_code_avail(self, sections: dict[str, str]) -> GateResult:
        all_text = " ".join(sections.values()).lower()
        found = any(ind in all_text for ind in ["code availability", "github", "zenodo", "software availability"])
        return GateResult(rule="code_availability_statement", severity="high", passed=found,
                          message="Statement found" if found else "Missing code availability statement")

    def _check_section_len(self, name: str, content: str) -> GateResult:
        min_len = self.MIN_LENGTHS.get(name, 200)
        wc = len(content.split())
        passed = wc >= min_len
        return GateResult(rule="section_length_minimum", severity="medium", passed=passed,
                          message=f"[{name}] {wc} words (min: {min_len})",
                          details={"section": name, "word_count": wc, "min_required": min_len})

    def _check_no_bullets(self, name: str, content: str) -> GateResult:
        bullets = [l for l in content.split("\n") if l.strip().startswith(("- ", "* ", "+ ", "1. "))]
        passed = len(bullets) == 0
        return GateResult(rule="no_bullets_in_prose", severity="medium", passed=passed,
                          message=f"[{name}] OK" if passed else f"[{name}] {len(bullets)} bullet lines found")

    def _check_no_paths(self, name: str, content: str) -> GateResult:
        patterns = [r'[A-Z]:\\', r'/home/', r'/Users/', r'\.h5ad', r'\.rds', r'results/runs/', r'\.py\b', r'\.R\b']
        violations = []
        for pat in patterns:
            violations.extend(re.findall(pat, content)[:3])
        passed = len(violations) == 0
        return GateResult(rule="no_local_paths", severity="high", passed=passed,
                          message=f"[{name}] OK" if passed else f"[{name}] {len(violations)} local paths found",
                          details={"violations": violations} if violations else {})

    def _check_stats(self, text: str) -> GateResult:
        has_p = bool(re.search(r'[pP]\s*[<=>]\s*0\.\d+', text))
        has_eff = bool(re.search(r'(β|OR|HR|RR|d|r)\s*=', text))
        missing = []
        if not has_p: missing.append("exact p-values")
        if not has_eff: missing.append("effect sizes")
        return GateResult(rule="statistics_reported", severity="high", passed=len(missing) == 0,
                          message="Complete" if not missing else f"Missing: {', '.join(missing)}",
                          details={"has_pvalue": has_p, "has_effect": has_eff})

    def _check_fig_count(self, figure_plan: dict, journal: Optional[dict]) -> GateResult:
        count = len(figure_plan.get("figures", []))
        max_fig = journal.get("figure_limit", 6) if journal else 6
        passed = count <= max_fig
        return GateResult(rule="figure_count_requirements", severity="medium", passed=passed,
                          message=f"{count} figures (limit: {max_fig})",
                          details={"count": count, "max": max_fig})

    # =========================================================================
    # v3.0: Claim binding check (upgraded from v2)
    # =========================================================================
    def _check_claim_binding(self, claim_ledger: list) -> GateResult:
        unbound = [c for c in claim_ledger if not c.get("artifact_path") and not c.get("figure_ref")]
        if unbound:
            return GateResult(rule="claim_artifact_binding", severity="critical", passed=False,
                            message=f"{len(unbound)} claims lack artifact binding",
                            details={"unbound_claim_ids": [c.get("claim_id", "?") for c in unbound[:10]]})
        return GateResult(rule="claim_artifact_binding", severity="critical", passed=True,
                         message=f"All {len(claim_ledger)} claims bound to artifacts")

    def _check_figures_refed(self, figure_plan: dict, sections: dict) -> GateResult:
        all_text = " ".join(sections.values())
        unreferenced = []
        for fig in figure_plan.get("figures", []):
            fig_id = fig.get("id", "")
            if fig_id and fig_id not in all_text:
                unreferenced.append(fig_id)
        if unreferenced:
            return GateResult(rule="figures_referenced", severity="critical", passed=False,
                            message=f"{len(unreferenced)} figures not referenced", details={"unreferenced": unreferenced})
        return GateResult(rule="figures_referenced", severity="critical", passed=True,
                         message="All figures referenced")

    def _check_overinterpretation(self, text: str) -> GateResult:
        overclaim_patterns = [
            r'(prove|proves|proven)\s', r'definitively\s(demonstrat|show)',
            r'establish\scausal', r'first\sever', r'novel\smechanism',
        ]
        violations = []
        for pat in overclaim_patterns:
            matches = re.findall(pat, text, re.IGNORECASE)
            violations.extend(matches)
        passed = len(violations) <= 1  # Allow at most 1 minor overclaim
        return GateResult(rule="results_no_overinterpretation", severity="high", passed=passed,
                         message="OK" if passed else f"{len(violations)} potential overclaims: {violations[:3]}",
                         details={"overclaims": violations})

    def _check_limitations(self, text: str) -> GateResult:
        has_limitations = bool(re.search(r'(limitation|limitations|caveat|caveats|not\s+without)', text, re.IGNORECASE))
        return GateResult(rule="discussion_limitations", severity="high", passed=has_limitations,
                         message="Limitations found" if has_limitations else "Missing limitations paragraph")

    def _check_methods_params(self, text: str) -> GateResult:
        has_version = bool(re.search(r'(version|v\d+\.\d+)', text, re.IGNORECASE))
        has_seed = bool(re.search(r'(seed|set\.seed|random_state)', text, re.IGNORECASE))
        missing = []
        if not has_version: missing.append("software versions")
        if not has_seed: missing.append("random seed")
        return GateResult(rule="methods_parameters_complete", severity="high", passed=len(missing) == 0,
                         message="Complete" if not missing else f"Missing: {', '.join(missing)}",
                         details={"has_version": has_version, "has_seed": has_seed})

    def _check_pseudorep(self, data_inventory: dict) -> GateResult:
        unit = data_inventory.get("statistical_unit", "")
        n_patients = data_inventory.get("n_patients", 0)
        n_observations = data_inventory.get("n_observations", 0)
        if n_patients and n_observations and n_observations > n_patients * 2:
            return GateResult(rule="pseudoreplication_check", severity="critical", passed=False,
                            message=f"Observations ({n_observations}) >> patients ({n_patients}); verify statistical unit",
                            details={"n_patients": n_patients, "n_observations": n_observations, "unit": unit})
        return GateResult(rule="pseudoreplication_check", severity="critical", passed=True,
                         message=f"Statistical unit appears appropriate ({unit or 'patient-level'})")

    # =========================================================================
    # v3.0: Clinical Design Gate Methods (Category B)
    # =========================================================================
    def _check_study_design_declared(self, sections: dict, study_design: Optional[dict]) -> GateResult:
        design_types = ["cohort", "case-control", "cross-sectional", "randomized", "diagnostic",
                       "prognostic", "predictive", "mechanistic", "methodological", "systematic review"]
        all_text = " ".join(sections.values()).lower()
        sd = study_design or {}
        declared = sd.get("design_type", "")
        found_in_text = any(dt in all_text for dt in design_types)
        if declared or found_in_text:
            return GateResult(rule="study_design_declared", severity="critical", passed=True,
                            message=f"Design declared: {declared or 'found in text'}")
        return GateResult(rule="study_design_declared", severity="critical", passed=False,
                         message="Study design NOT explicitly declared in title/abstract/methods")

    def _check_clinical_question(self, sections: dict, study_design: Optional[dict]) -> GateResult:
        sd = study_design or {}
        has_clinical_q = sd.get("clinical_question") or sd.get("unmet_need") or sd.get("actionable_decision")
        if has_clinical_q:
            return GateResult(rule="clinical_question_actionable", severity="high", passed=True,
                            message="Clinical question linked to actionable decision")
        return GateResult(rule="clinical_question_actionable", severity="high", passed=False,
                         message="No explicit clinical decision/mechanism gap stated",
                         details={"recommendation": "Add clinical_value_matrix.yaml to project"})

    def _check_inclusion_exclusion(self, sections: dict, study_design: Optional[dict]) -> GateResult:
        all_text = " ".join(sections.values()).lower()
        sd = study_design or {}
        has_incl = sd.get("inclusion_criteria") or ("inclusion criteria" in all_text) or ("eligible" in all_text)
        has_excl = sd.get("exclusion_criteria") or ("exclusion criteria" in all_text) or ("excluded" in all_text)
        if has_incl and has_excl:
            return GateResult(rule="inclusion_exclusion_complete", severity="critical", passed=True,
                            message="Inclusion and exclusion criteria documented")
        missing = []
        if not has_incl: missing.append("inclusion criteria")
        if not has_excl: missing.append("exclusion criteria")
        return GateResult(rule="inclusion_exclusion_complete", severity="critical", passed=False,
                         message=f"Missing: {', '.join(missing)}")

    def _check_endpoint_definition(self, sections: dict, study_design: Optional[dict]) -> GateResult:
        sd = study_design or {}
        has_primary = sd.get("primary_endpoint") or sd.get("primary_outcome")
        has_secondary = sd.get("secondary_endpoints") or sd.get("secondary_outcomes")
        if has_primary:
            return GateResult(rule="endpoint_definition_complete", severity="critical", passed=True,
                            message=f"Primary endpoint defined{f' (+{len(has_secondary) if isinstance(has_secondary, list) else 1} secondary)' if has_secondary else ''}")
        all_text = " ".join(sections.values()).lower()
        if "primary outcome" in all_text or "primary endpoint" in all_text:
            return GateResult(rule="endpoint_definition_complete", severity="critical", passed=True,
                            message="Endpoints described in text")
        return GateResult(rule="endpoint_definition_complete", severity="critical", passed=False,
                         message="Primary endpoint NOT explicitly defined")

    def _check_ethics_statement(self, sections: dict, study_design: Optional[dict]) -> GateResult:
        all_text = " ".join(sections.values()).lower()
        sd = study_design or {}
        has_irb = sd.get("irb_approval") or sd.get("ethics_approval") or \
                  any(term in all_text for term in ["irb", "ethics committee", "ethical approval",
                                                    "institutional review board", "declaration of helsinki"])
        has_public = sd.get("public_data_exemption") or \
                     any(term in all_text for term in ["publicly available", "open access", "geo:", "arrayexpress"])
        if has_irb or has_public:
            return GateResult(rule="ethics_irb_or_public_exemption", severity="critical", passed=True,
                            message="Ethics statement present" if has_irb else "Public data exemption documented")
        return GateResult(rule="ethics_irb_or_public_exemption", severity="critical", passed=False,
                         message="No IRB/ethics approval or public data exemption found")

    # =========================================================================
    # v3.0: Data & Bias Gate Methods (Category C)
    # =========================================================================
    def _check_patient_independence(self, sections: dict, data_inventory: Optional[dict]) -> GateResult:
        di = data_inventory or {}
        unit = di.get("statistical_unit", "")
        n_patients = di.get("n_patients", di.get("n_samples", 0))
        n_cells = di.get("n_cells", di.get("n_spots", 0))
        if n_cells and n_patients and n_cells > n_patients * 100:
            return GateResult(rule="patient_level_independence", severity="critical", passed=False,
                            message=f"Potential pseudoreplication: {n_cells} observations from {n_patients} patients",
                            details={"n_patients": n_patients, "n_cells": n_cells,
                                     "recommendation": "Use pseudobulk or mixed models with patient random effect"})
        return GateResult(rule="patient_level_independence", severity="critical", passed=True,
                         message=f"Patient-level independence appears maintained (unit: {unit or 'implied patient'})")

    def _check_batch_confounding(self, sections: dict, data_inventory: Optional[dict]) -> GateResult:
        di = data_inventory or {}
        batch_vars = di.get("batch_variables", [])
        design_vars = di.get("design_variables", [])
        confounding = di.get("batch_design_confounding", None)
        if confounding is False:
            return GateResult(rule="batch_confounding_audit", severity="high", passed=True,
                            message="Batch NOT confounded with design")
        if confounding is True:
            return GateResult(rule="batch_confounding_audit", severity="high", passed=False,
                            message="CRITICAL: Batch confounded with condition — results may be artifacts",
                            details={"batch_vars": batch_vars, "design_vars": design_vars})
        if batch_vars:
            return GateResult(rule="batch_confounding_audit", severity="high", passed=True,
                            message=f"Batch variables ({batch_vars}) identified; confounding assessment needed")
        return GateResult(rule="batch_confounding_audit", severity="high", passed=True,
                         message="No batch variables flagged (manual verification recommended)")

    def _check_missing_data_strategy(self, sections: dict, statistical_plan: Optional[dict]) -> GateResult:
        sp = statistical_plan or {}
        strategy = sp.get("missing_data_strategy", "")
        all_text = " ".join(sections.values()).lower()
        has_strategy = strategy or any(term in all_text for term in [
            "missing data", "missing values", "imputation", "complete case",
            "multiple imputation", "missing at random", "missing completely at random"])
        if has_strategy:
            return GateResult(rule="missing_data_strategy", severity="high", passed=True,
                            message=f"Missing data strategy: {strategy or 'described in text'}")
        return GateResult(rule="missing_data_strategy", severity="high", passed=False,
                         message="No missing data handling strategy specified")

    def _check_train_test_leakage(self, sections: dict, model_evaluation: Optional[dict]) -> GateResult:
        me = model_evaluation or {}
        has_split = me.get("train_test_split") or me.get("cv_strategy") or me.get("nested_cv")
        leakage_checked = me.get("leakage_check", me.get("data_leakage_assessed"))
        if not has_split:
            return GateResult(rule="train_test_leakage_check", severity="critical", passed=True,
                            message="No ML model detected; gate skipped")
        if leakage_checked:
            return GateResult(rule="train_test_leakage_check", severity="critical", passed=True,
                            message="Train/test leakage explicitly checked")
        return GateResult(rule="train_test_leakage_check", severity="critical", passed=False,
                         message="ML model present but train/test leakage NOT explicitly assessed",
                         details={"recommendation": "Document split strategy: by patient, not by observation"})

    def _check_sample_overlap(self, sections: dict, data_inventory: Optional[dict]) -> GateResult:
        di = data_inventory or {}
        cohorts = di.get("cohorts", [])
        if len(cohorts) < 2:
            return GateResult(rule="sample_overlap_check", severity="critical", passed=True,
                            message="Single cohort; overlap check N/A")
        overlap = di.get("sample_overlap_detected")
        if overlap is False:
            return GateResult(rule="sample_overlap_check", severity="critical", passed=True,
                            message=f"No sample overlap detected across {len(cohorts)} cohorts")
        if overlap is True:
            return GateResult(rule="sample_overlap_check", severity="critical", passed=False,
                            message="Sample overlap detected between discovery and validation cohorts",
                            details={"cohorts": cohorts})
        return GateResult(rule="sample_overlap_check", severity="critical", passed=False,
                         message=f"Multiple cohorts ({len(cohorts)}) but overlap NOT assessed",
                         details={"recommendation": "Check for overlapping sample IDs or genetic correlation"})

    # =========================================================================
    # v3.0: Statistics & Model Gate Methods (Category D)
    # =========================================================================
    def _check_sap_exists(self, statistical_plan: Optional[dict]) -> GateResult:
        if statistical_plan and statistical_plan.get("frozen", False):
            return GateResult(rule="statistical_analysis_plan_exists", severity="critical", passed=True,
                            message="Statistical Analysis Plan frozen before primary analysis")
        if statistical_plan:
            return GateResult(rule="statistical_analysis_plan_exists", severity="critical", passed=False,
                             message="SAP exists but NOT marked as frozen (pre-specified)")
        return GateResult(rule="statistical_analysis_plan_exists", severity="critical", passed=False,
                         message="No Statistical Analysis Plan found — create before primary analysis")

    def _check_effect_size_ci(self, sections: dict) -> GateResult:
        all_text = " ".join(sections.values())
        has_ci = bool(re.search(r'(confidence\s+interval|CI\s*[=:]?\s*\[?\d|95%\s*CI)', all_text, re.IGNORECASE))
        has_eff = bool(re.search(r'(β|beta|OR|HR|RR|Cohen|hedges|effect\s+size|log2FC|mean\s+difference)', all_text, re.IGNORECASE))
        if has_ci and has_eff:
            return GateResult(rule="effect_size_ci_reported", severity="high", passed=True,
                            message="Effect sizes and confidence intervals reported")
        missing = []
        if not has_eff: missing.append("effect sizes")
        if not has_ci: missing.append("confidence intervals")
        return GateResult(rule="effect_size_ci_reported", severity="high", passed=False,
                         message=f"Missing: {', '.join(missing)}")

    def _check_multiple_testing(self, sections: dict, statistical_plan: Optional[dict]) -> GateResult:
        all_text = " ".join(sections.values()).lower()
        sp = statistical_plan or {}
        has_correction = sp.get("multiple_testing_correction") or \
                        any(term in all_text for term in ["fdr", "bonferroni", "bh", "benjamini",
                                                          "multiple testing correction", "family-wise",
                                                          "false discovery rate", "hierarchical testing"])
        if has_correction:
            return GateResult(rule="multiple_testing_control", severity="critical", passed=True,
                            message="Multiple testing correction explicitly stated")
        return GateResult(rule="multiple_testing_control", severity="critical", passed=False,
                         message="No multiple testing correction method specified")

    def _check_model_calibration(self, sections: dict, model_evaluation: Optional[dict]) -> GateResult:
        me = model_evaluation or {}
        has_model = me.get("model_type") or me.get("auc") or me.get("predictions")
        if not has_model:
            return GateResult(rule="model_calibration_reported", severity="high", passed=True,
                            message="No prediction model detected; gate skipped")
        has_calib = me.get("calibration_reported") or me.get("brier_score") or me.get("calibration_curve")
        if has_calib:
            return GateResult(rule="model_calibration_reported", severity="high", passed=True,
                            message="Model calibration reported")
        return GateResult(rule="model_calibration_reported", severity="high", passed=False,
                         message="Prediction model present but calibration NOT reported",
                         details={"recommendation": "Report calibration curve and Brier score"})

    def _check_external_validation(self, sections: dict, model_evaluation: Optional[dict]) -> GateResult:
        me = model_evaluation or {}
        has_ext = me.get("external_validation") or me.get("independent_cohort")
        has_limitation = me.get("no_external_validation_acknowledged")
        all_text = " ".join(sections.values()).lower()
        limitation_in_text = any(term in all_text for term in [
            "external validation", "independent cohort", "without external validation",
            "limited by the lack of external", "require external validation"])
        if has_ext:
            return GateResult(rule="external_validation_or_limitation", severity="critical", passed=True,
                            message="External validation performed")
        if has_limitation or limitation_in_text:
            return GateResult(rule="external_validation_or_limitation", severity="critical", passed=True,
                            message="Lack of external validation acknowledged as limitation")
        return GateResult(rule="external_validation_or_limitation", severity="critical", passed=False,
                         message="No external validation AND limitation not acknowledged",
                         details={"recommendation": "Either add external validation or explicitly downgrade conclusions"})

    # =========================================================================
    # v3.0: Single-Cell & Spatial Omics Gate Methods (Category E)
    # =========================================================================
    def _check_cell_annotation_evidence(self, sections: dict, omics_metadata: Optional[dict]) -> GateResult:
        om = omics_metadata or {}
        if not om:
            return GateResult(rule="cell_annotation_evidence", severity="high", passed=True,
                            message="No single-cell data detected; gate skipped")
        has_markers = om.get("marker_genes") or om.get("annotation_method")
        has_reference = om.get("reference_atlas") or om.get("reference_mapping")
        has_review = om.get("manual_review") or om.get("annotation_validated")
        evidence_count = sum([bool(has_markers), bool(has_reference), bool(has_review)])
        if evidence_count >= 2:
            return GateResult(rule="cell_annotation_evidence", severity="high", passed=True,
                            message=f"Cell annotation supported by {evidence_count}/3 evidence types")
        return GateResult(rule="cell_annotation_evidence", severity="high", passed=False,
                         message=f"Cell annotation evidence: {evidence_count}/3 (need ≥2 of: markers, reference, review)")

    def _check_spatial_registration(self, sections: dict, omics_metadata: Optional[dict]) -> GateResult:
        om = omics_metadata or {}
        if not om or not om.get("spatial_data", False):
            return GateResult(rule="spatial_region_registration", severity="high", passed=True,
                            message="No spatial data detected; gate skipped")
        has_registration = om.get("pathology_registration") or om.get("imaging_registration") or \
                          om.get("electrophysiology_registration") or om.get("region_annotation_method")
        if has_registration:
            return GateResult(rule="spatial_region_registration", severity="high", passed=True,
                            message="Spatial regions registered to reference modality")
        return GateResult(rule="spatial_region_registration", severity="high", passed=False,
                         message="Spatial data present but region registration to pathology/imaging NOT documented")

    def _check_pseudobulk_de(self, sections: dict, omics_metadata: Optional[dict]) -> GateResult:
        om = omics_metadata or {}
        de_method = om.get("de_method", "").lower()
        if not de_method:
            return GateResult(rule="de_pseudobulk_required", severity="high", passed=True,
                            message="No single-cell DE detected; gate skipped")
        pseudobulk_methods = ["pseudobulk", "muscat", "dream", "mixed model", "glmm", "nebula",
                             "mast", "lmer", "deseq2 pseudobulk", "edger pseudobulk"]
        is_pseudobulk = any(m in de_method for m in pseudobulk_methods)
        if is_pseudobulk:
            return GateResult(rule="de_pseudobulk_required", severity="high", passed=True,
                            message=f"DE method ({de_method}) uses pseudobulk or mixed model")
        cell_level_methods = ["wilcoxon", "t-test", "logreg", "bimod"]
        if any(m in de_method for m in cell_level_methods):
            return GateResult(rule="de_pseudobulk_required", severity="high", passed=False,
                            message=f"DE method ({de_method}) uses cell as replicate — use pseudobulk instead",
                            details={"recommendation": "Aggregate counts to donor-level before DE testing"})
        return GateResult(rule="de_pseudobulk_required", severity="high", passed=True,
                         message=f"DE method ({de_method}) — verify biological replicate unit")

    def _check_integration_batch(self, sections: dict, omics_metadata: Optional[dict]) -> GateResult:
        om = omics_metadata or {}
        if not om or not om.get("integrated", False):
            return GateResult(rule="integration_batch_risk", severity="high", passed=True,
                            message="No multi-sample integration detected; gate skipped")
        method = om.get("integration_method", "")
        assessed = om.get("integration_batch_assessed", False)
        if assessed:
            return GateResult(rule="integration_batch_risk", severity="high", passed=True,
                            message=f"Integration ({method}) batch risk assessed")
        return GateResult(rule="integration_batch_risk", severity="high", passed=False,
                         message=f"Integration ({method}) performed but batch effect on biological variation NOT assessed",
                         details={"recommendation": "Compare pre/post integration: cell-type proportions, marker expression, cluster composition"})

    def _check_lr_overclaim(self, sections: dict) -> GateResult:
        all_text = " ".join(sections.values()).lower()
        overclaim_patterns = [
            r'(cell\s+communication|crosstalk|ligand.receptor).{0,50}(cause|drive|induce|trigger|control)',
            r'(prove|establish).{0,30}(cell.cell|intercellular|communication)',
        ]
        violations = []
        for pat in overclaim_patterns:
            violations.extend(re.findall(pat, all_text))
        if violations:
            return GateResult(rule="ligand_receptor_overclaim_check", severity="high", passed=False,
                            message=f"{len(violations)} potential ligand-receptor overclaims (co-expression ≠ causal interaction)",
                            details={"matches": violations[:3]})
        return GateResult(rule="ligand_receptor_overclaim_check", severity="high", passed=True,
                         message="No ligand-receptor overclaim detected")

    # =========================================================================
    # v3.0: AI/ML Gate Methods (Category F)
    # =========================================================================
    def _check_baseline_comparison(self, sections: dict, model_evaluation: Optional[dict]) -> GateResult:
        me = model_evaluation or {}
        if not me or not me.get("model_type"):
            return GateResult(rule="baseline_model_comparison", severity="high", passed=True,
                            message="No ML model detected; gate skipped")
        has_baseline = me.get("baseline_model") or me.get("compared_to_clinical") or me.get("baseline_auc")
        if has_baseline:
            return GateResult(rule="baseline_model_comparison", severity="high", passed=True,
                            message="ML model compared against baseline/clinical standard")
        return GateResult(rule="baseline_model_comparison", severity="high", passed=False,
                         message="ML model NOT compared against traditional statistical model or clinical score",
                         details={"recommendation": "Compare against logistic regression, clinical risk score, or established benchmark"})

    def _check_nested_cv(self, sections: dict, model_evaluation: Optional[dict]) -> GateResult:
        me = model_evaluation or {}
        if not me or not me.get("model_type"):
            return GateResult(rule="nested_cv_or_external_test", severity="critical", passed=True,
                            message="No ML model detected; gate skipped")
        cv_strategy = me.get("cv_strategy", "")
        n_samples = me.get("n_samples", 999)
        has_nested = "nested" in cv_strategy.lower() or me.get("nested_cv", False)
        has_external = me.get("external_test_set", False) or me.get("independent_cohort")
        if has_nested or has_external or n_samples > 1000:
            return GateResult(rule="nested_cv_or_external_test", severity="critical", passed=True,
                            message=f"Valid validation: {'nested CV' if has_nested else 'external test' if has_external else f'large n={n_samples}'}")
        if n_samples < 200:
            return GateResult(rule="nested_cv_or_external_test", severity="critical", passed=False,
                            message=f"Small sample (n={n_samples}) with simple CV — use nested CV or external test",
                            details={"recommendation": "Simple CV inflates performance estimates in small samples"})
        return GateResult(rule="nested_cv_or_external_test", severity="critical", passed=True,
                         message=f"CV strategy: {cv_strategy} (n={n_samples})")

    def _check_decision_curve(self, sections: dict, model_evaluation: Optional[dict]) -> GateResult:
        me = model_evaluation or {}
        if not me or not me.get("clinical_model", False):
            return GateResult(rule="calibration_decision_curve", severity="high", passed=True,
                            message="No clinical prediction model detected; gate skipped")
        has_dca = me.get("decision_curve_analysis") or me.get("net_benefit_reported")
        if has_dca:
            return GateResult(rule="calibration_decision_curve", severity="high", passed=True,
                            message="Decision curve analysis reported")
        return GateResult(rule="calibration_decision_curve", severity="high", passed=False,
                         message="Clinical model present but decision curve analysis (net benefit) NOT reported")

    def _check_explainability(self, sections: dict) -> GateResult:
        all_text = " ".join(sections.values()).lower()
        causal_claims_with_shap = re.findall(
            r'(shap|feature\s+importance|saliency).{0,100}(cause|causal|mechanism|drive|responsible)',
            all_text)
        if causal_claims_with_shap:
            return GateResult(rule="explainability_sanity_check", severity="high", passed=False,
                            message=f"{len(causal_claims_with_shap)} instances where SHAP/importance interpreted as causal",
                            details={"recommendation": "Feature importance ≠ causal effect. Use causal inference methods."})
        return GateResult(rule="explainability_sanity_check", severity="high", passed=True,
                         message="No causal overinterpretation of feature importance detected")

    def _check_deployment_claim(self, sections: dict) -> GateResult:
        all_text = " ".join(sections.values()).lower()
        deployment_claims = re.findall(
            r'(clinical\s+tool|deploy|clinical\s+utility|bedside|ready\s+for\s+clinical|translational\s+impact)',
            all_text)
        has_prospective = "prospective" in all_text or "external validation" in all_text
        if deployment_claims and not has_prospective:
            return GateResult(rule="deployment_claim_limited", severity="high", passed=False,
                            message=f"{len(deployment_claims)} deployment claims without prospective validation",
                            details={"claims": deployment_claims[:3],
                                     "recommendation": "Do NOT claim clinical deployability without prospective study"})
        return GateResult(rule="deployment_claim_limited", severity="high", passed=True,
                         message="No unqualified deployment claims detected")

    def generate_markdown_report(self, report: IntegrityReport) -> str:
        lines = ["# Integrity Gate Report", "",
                 f"**Report ID**: {report.report_id} | **Checked**: {report.checked_at}", "",
                 "## Summary", "",
                 f"| Critical | High | Medium | Low |",
                 f"|----------|------|--------|-----|",
                 f"| **{report.critical_failures}** | {report.high_failures} | {report.medium_failures} | {report.low_failures} |",
                 "", f"**Pipeline Blocked**: {'YES' if report.blocks_pipeline else 'No'}", "",
                 "## Detailed Results", ""]
        sev_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        for r in sorted(report.results, key=lambda r: (sev_order.get(r.severity, 4), not r.passed)):
            icon = "[PASS]" if r.passed else "[FAIL]"
            lines.append(f"- {icon} **{r.severity.upper()}** — {r.rule}: {r.message}")
        if report.critical_failures > 0:
            lines += ["", "## Action Required", "",
                      "Critical failures must be resolved before proceeding.",
                      "Run `diagnose-gate-failures` to generate a revision plan."]
        return "\n".join(lines)
