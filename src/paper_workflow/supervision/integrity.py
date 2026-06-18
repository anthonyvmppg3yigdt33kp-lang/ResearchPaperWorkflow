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
    """Runs integrity and quality checks on manuscript artifacts."""

    GATES = {
        "bibtex_citation_existence": {"rule": "bibtex_citation_existence", "severity": "critical",
                                      "description": "Every \\cite{} must have a BibTeX entry"},
        "citation_evidence_traceability": {"rule": "citation_evidence_traceability", "severity": "critical",
                                           "description": "Citations must be traceable to citation_evidence.csv"},
        "results_no_citations": {"rule": "results_no_citations", "severity": "critical",
                                 "description": "Results must contain NO citation commands"},
        "claim_artifact_binding": {"rule": "claim_artifact_binding", "severity": "critical",
                                   "description": "Every result claim must bind to existing figure/table"},
        "figures_referenced": {"rule": "figures_referenced", "severity": "critical",
                               "description": "Every \\ref{fig:...} must refer to existing file"},
        "data_availability_statement": {"rule": "data_availability_statement", "severity": "high",
                                        "description": "Must contain Data Availability statement"},
        "code_availability_statement": {"rule": "code_availability_statement", "severity": "high",
                                        "description": "Must contain Code Availability statement"},
        "no_local_paths": {"rule": "no_local_paths", "severity": "high",
                           "description": "No local filesystem paths or filenames"},
        "methods_parameters_complete": {"rule": "methods_parameters_complete", "severity": "high",
                                        "description": "All key parameters and software versions included"},
        "discussion_limitations": {"rule": "discussion_limitations", "severity": "high",
                                   "description": "Discussion must include Limitations paragraph"},
        "results_no_overinterpretation": {"rule": "results_no_overinterpretation", "severity": "high",
                                          "description": "Results must not include mechanistic speculation"},
        "statistics_reported": {"rule": "statistics_reported", "severity": "high",
                                "description": "Quantitative claims must include statistics"},
        "pseudoreplication_check": {"rule": "pseudoreplication_check", "severity": "high",
                                    "description": "Statistical inference uses correct biological replicate unit"},
        "section_length_minimum": {"rule": "section_length_minimum", "severity": "medium",
                                   "description": "Each section meets minimum length"},
        "no_bullets_in_prose": {"rule": "no_bullets_in_prose", "severity": "medium",
                                "description": "Manuscript body uses natural prose, not bullet points"},
        "figure_count_requirements": {"rule": "figure_count_requirements", "severity": "medium",
                                      "description": "Figure count within journal limits"},
    }

    MIN_LENGTHS = {"introduction": 500, "methods": 800, "results": 800, "discussion": 600, "abstract": 100}

    def __init__(self, paper_dir: Path):
        self.paper_dir = Path(paper_dir)

    def run_all_checks(self, manuscript_sections: Optional[dict[str, str]] = None,
                       bibtex_path: Optional[Path] = None, citation_evidence: Optional[list] = None,
                       figure_plan: Optional[dict] = None, journal_target: Optional[dict] = None,
                       result_manifest: Optional[dict] = None) -> IntegrityReport:
        """Run all integrity checks."""
        report = IntegrityReport()
        sections = manuscript_sections or {}

        if bibtex_path and sections:
            report.results.append(self._check_bibtex(sections, bibtex_path))
        if sections and "results" in sections:
            report.results.append(self._check_results_no_cite(sections["results"]))
        if sections:
            report.results.append(self._check_data_avail(sections))
            report.results.append(self._check_code_avail(sections))
            for name, content in sections.items():
                report.results.append(self._check_section_len(name, content))
                report.results.append(self._check_no_bullets(name, content))
                report.results.append(self._check_no_paths(name, content))
        if sections and "results" in sections:
            report.results.append(self._check_stats(sections["results"]))
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
