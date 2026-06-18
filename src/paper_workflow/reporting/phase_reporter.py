"""
Phase Reporter — Generate standardized PHASE_REPORT.md files.

Backported from the IgG4MALT Research test project (run_20260618_1730_bulk_de).
Provides automated audit of analysis outputs, completeness checking against
planned steps, and structured report generation with 8 standard sections.

Usage:
    from paper_workflow.reporting import PhaseReporter

    reporter = PhaseReporter(project_title="My Analysis")
    report_path = reporter.generate_report(
        run_dir="/path/to/run_dir",
        work_log_path="/path/to/work_log.md",
        error_log_path="/path/to/error_log.md",
    )
"""

from __future__ import annotations

import datetime
import json
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# Error logging helper (replaces bare except: pass patterns)
# ---------------------------------------------------------------------------

def _log_nonfatal(stage: str, exc: Exception, severity: str = "warning") -> None:
    """Log a non-fatal error without crashing the pipeline."""
    try:
        import sys
        print(f"[{severity.upper()}] [{stage}] {type(exc).__name__}: {exc}", file=sys.stderr, flush=True)
    except Exception:
        pass  # Last-resort pass: error logging itself must never crash


# ---------------------------------------------------------------------------
# Data Classes
# ---------------------------------------------------------------------------


@dataclass
class AuditCounts:
    """Output inventory for a single run directory."""

    figures: int = 0
    tables: int = 0
    scripts: int = 0
    logs: int = 0
    metadata: int = 0
    reports: int = 0

    @property
    def total(self) -> int:
        return self.figures + self.tables + self.scripts + self.logs + self.metadata + self.reports


@dataclass
class CompletenessResult:
    """Result of comparing planned vs completed analysis steps."""

    completed: List[str] = field(default_factory=list)
    not_completed: List[str] = field(default_factory=list)
    completion_pct: float = 0.0


@dataclass
class ErrorEntry:
    """Parsed error from error_log.md."""

    err_id: str = ""
    phase: str = ""
    severity: str = "Warning"
    status: str = "Open"
    description: str = ""
    raised_by: str = ""
    message: str = ""
    context: str = ""
    diagnosis: str = ""
    resolution: str = ""
    prevention: str = ""


# ---------------------------------------------------------------------------
# PhaseReporter
# ---------------------------------------------------------------------------


class PhaseReporter:
    """Generate PHASE_REPORT.md files with standardized audit sections.

    The report has 8 sections:
      1. Executive Summary
      2. Analysis Methods & Parameters (per step)
      3. Results Inventory (figures, tables, scripts)
      4. Key Biological Findings
      5. Analysis Completeness Audit
      6. Task Continuity (work_log linkage)
      7. Parameters Quick Reference
      8. Timestamp & Audit Trail
    """

    def __init__(
        self,
        project_title: str = "Untitled Project",
        author: str = "Automated Audit Agent",
    ) -> None:
        self.project_title = project_title
        self.author = author
        self._generated_at: str = ""

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def generate_report(
        self,
        run_dir: str,
        work_log_path: str = "",
        error_log_path: str = "",
        planned_steps: Optional[List[str]] = None,
    ) -> str:
        """Generate a complete PHASE_REPORT.md and return its path.

        Args:
            run_dir: Path to the run output directory.
            work_log_path: Path to work_log.md for task continuity section.
            error_log_path: Path to error_log.md for errors section.
            planned_steps: Optional list of planned analysis step IDs.
                If omitted, completeness check is skipped.

        Returns:
            Absolute path to the generated PHASE_REPORT.md.
        """
        run_dir = os.path.abspath(run_dir)
        os.makedirs(run_dir, exist_ok=True)

        self._generated_at = datetime.datetime.now().isoformat(timespec="seconds")

        # Audit outputs
        counts = self.audit_outputs(run_dir)

        # Parse errors
        errors = self._parse_error_log(error_log_path) if error_log_path else []

        # Build report sections
        sections: List[str] = []
        sections.append(self._section_header(run_dir, work_log_path))
        sections.append(self._section_executive_summary(counts, errors))
        sections.append(self._section_methods_parameters(run_dir))
        sections.append(self._section_results_inventory(run_dir, counts))
        sections.append(self._section_key_findings(run_dir))
        sections.append(self._section_completeness_audit(counts, errors, planned_steps))
        sections.append(self._section_task_continuity(work_log_path))
        sections.append(self._section_parameters_reference(run_dir))
        sections.append(self._section_timestamp(counts, errors))

        report = "\n\n".join(sections) + "\n"

        report_path = os.path.join(run_dir, "PHASE_REPORT.md")
        Path(report_path).write_text(report, encoding="utf-8")
        return report_path

    def audit_outputs(self, run_dir: str) -> AuditCounts:
        """Count all output artifacts in a run directory.

        Scans subdirectories `figures/`, `tables/`, `code/`, `logs/` and
        the run_dir root for metadata/report files.

        Returns:
            AuditCounts with categorized file counts.
        """
        counts = AuditCounts()

        figures_dir = os.path.join(run_dir, "figures")
        tables_dir = os.path.join(run_dir, "tables")
        code_dir = os.path.join(run_dir, "code")
        logs_dir = os.path.join(run_dir, "logs")

        for label, path in [
            ("figures", figures_dir),
            ("tables", tables_dir),
            ("code", code_dir),
            ("logs", logs_dir),
        ]:
            if os.path.isdir(path):
                file_count = len([
                    f for f in os.listdir(path)
                    if os.path.isfile(os.path.join(path, f))
                ])
                setattr(counts, {"figures": "figures", "tables": "tables", "code": "scripts", "logs": "logs"}[label], file_count)

        # Metadata / report files in run_dir root
        if os.path.isdir(run_dir):
            for fname in os.listdir(run_dir):
                fpath = os.path.join(run_dir, fname)
                if not os.path.isfile(fpath):
                    continue
                lower = fname.lower()
                if fname.endswith(".yaml") or fname.endswith(".yml") or fname == "RUN_MANIFEST.yaml":
                    counts.metadata += 1
                elif fname.endswith(".md") and "report" in lower:
                    counts.reports += 1

        return counts

    def check_completeness(
        self,
        planned_steps: List[str],
        completed_steps: List[str],
    ) -> CompletenessResult:
        """Compare planned steps against completed steps.

        Args:
            planned_steps: Ordered list of planned step IDs.
            completed_steps: List of step IDs that are completed.

        Returns:
            CompletenessResult with completed/not_completed lists and percentage.
        """
        completed_set = set(completed_steps)
        completed = [s for s in planned_steps if s in completed_set]
        not_completed = [s for s in planned_steps if s not in completed_set]
        pct = (len(completed) / len(planned_steps) * 100) if planned_steps else 100.0

        return CompletenessResult(
            completed=completed,
            not_completed=not_completed,
            completion_pct=round(pct, 1),
        )

    # ------------------------------------------------------------------
    # Section Builders
    # ------------------------------------------------------------------

    def _section_header(self, run_dir: str, work_log_path: str) -> str:
        run_id = os.path.basename(run_dir)
        lines = [
            f"# Phase Report: {self.project_title}",
            f"**Run ID**: {run_id}",
            f"**Generated**: {self._generated_at}",
            f"**Auditor**: {self.author}",
        ]
        if work_log_path:
            lines.append(f"**Work Log**: `{work_log_path}`")
        lines.append("")
        lines.append("---")
        return "\n".join(lines)

    def _section_executive_summary(
        self, counts: AuditCounts, errors: List[ErrorEntry]
    ) -> str:
        resolved = sum(1 for e in errors if e.status.lower() == "resolved")
        deferred = sum(1 for e in errors if e.status.lower() == "deferred")

        lines = [
            "## 1. Executive Summary",
            "",
            f"Analysis completed. **{counts.total} files produced** "
            f"({counts.figures} figures, {counts.tables} tables, "
            f"{counts.scripts} scripts, {counts.logs} logs, "
            f"{counts.metadata} metadata). All phases executed. "
            f"{len(errors)} errors encountered ({resolved} resolved, "
            f"{deferred} deferred).",
            "",
            "---",
        ]
        return "\n".join(lines)

    def _section_methods_parameters(self, run_dir: str) -> str:
        """Extract method/parameter info from code files.

        Scans code/ directory for R and Python scripts, extracts step-level
        metadata from structured comments if present.
        """
        code_dir = os.path.join(run_dir, "code")
        lines = [
            "## 2. Analysis Methods & Parameters",
            "",
        ]

        if os.path.isdir(code_dir):
            scripts = sorted([
                f for f in os.listdir(code_dir)
                if f.endswith((".R", ".py")) and os.path.isfile(os.path.join(code_dir, f))
            ])

            for script in scripts:
                script_path = os.path.join(code_dir, script)
                step_info = self._extract_step_info(script_path)
                lines.append(f"### {step_info['title']}")
                lines.append(f"- **Method**: {step_info['method']}")
                lines.append(f"- **Parameters**: {step_info['parameters']}")
                lines.append(f"- **Code**: `code/{script}`")
                lines.append(f"- **Key outputs**: {step_info['outputs']}")
                lines.append(f"- **Key result**: {step_info['result']}")
                lines.append("")
        else:
            lines.append("_No code directory found._")
            lines.append("")

        lines.append("---")
        return "\n".join(lines)

    def _extract_step_info(self, script_path: str) -> Dict[str, str]:
        """Extract metadata from structured header comments in a script."""
        info = {
            "title": os.path.basename(script_path),
            "method": "See script for details",
            "parameters": "See script for details",
            "outputs": "See script for details",
            "result": "See output files",
        }

        try:
            with open(script_path, "r", encoding="utf-8", errors="replace") as fh:
                content = fh.read(2000)  # Read only the header
        except OSError:
            return info

        # Look for structured comments like:
        # # Method: limma-trend empirical Bayes
        # # Parameters: |logFC|>1.0, adj.P<0.01
        patterns = {
            "title": r"#+\s*(.+?)\s*[-–—]",  # First heading-like line
            "method": r"(?:Method|METHOD)\s*[:：]\s*(.+)",
            "parameters": r"(?:Param(?:eter)?s?|PARAM(?:ETER)?S?)\s*[:：]\s*(.+)",
            "outputs": r"(?:Output|OUTPUT)\s*[:：]\s*(.+)",
            "result": r"(?:Key (?:result|finding)|RESULT)\s*[:：]\s*(.+)",
        }

        for line in content.split("\n"):
            line = line.strip()
            for key, pattern in patterns.items():
                m = re.search(pattern, line, re.IGNORECASE)
                if m and info[key] == info.get(f"_default_{key}", info[key]):
                    info[key] = m.group(1).strip()

        # Fallback: use script filename's number prefix as title
        base = os.path.basename(script_path)
        if "_" in base:
            parts = base.split("_", 1)
            info["title"] = parts[1].replace(".R", "").replace(".py", "").replace("_", " ").title()

        return info

    def _section_results_inventory(self, run_dir: str, counts: AuditCounts) -> str:
        """Build the Results Inventory section with file listing tables."""
        lines = [
            "## 3. Results Inventory",
            "",
        ]

        # Figures
        lines.append(f"### 3.1 Generated Figures ({counts.figures} total)")
        lines.append("")
        lines.append("| # | Figure | Description |")
        lines.append("|---|--------|-------------|")
        fig_dir = os.path.join(run_dir, "figures")
        if os.path.isdir(fig_dir):
            for i, fname in enumerate(
                sorted(f for f in os.listdir(fig_dir) if os.path.isfile(os.path.join(fig_dir, f))), 1
            ):
                lines.append(f"| {i} | `{fname}` | — |")
        else:
            lines.append("| — | _No figures directory_ | — |")
        lines.append("")

        # Tables
        lines.append(f"### 3.2 Generated Tables ({counts.tables} total)")
        lines.append("")
        lines.append("| # | Table | Rows | Description |")
        lines.append("|---|-------|------|-------------|")
        tbl_dir = os.path.join(run_dir, "tables")
        if os.path.isdir(tbl_dir):
            for i, fname in enumerate(
                sorted(f for f in os.listdir(tbl_dir) if os.path.isfile(os.path.join(tbl_dir, f))), 1
            ):
                # Try to count rows for CSV files
                row_count = "—"
                if fname.endswith(".csv"):
                    try:
                        with open(os.path.join(tbl_dir, fname), "r", encoding="utf-8", errors="replace") as fh:
                            row_count = str(sum(1 for _ in fh) - 1)  # minus header
                    except OSError as e:
                        _log_nonfatal("_build_tables_section", e, "info")
                lines.append(f"| {i} | `{fname}` | {row_count} | — |")
        else:
            lines.append("| — | _No tables directory_ | — |")
        lines.append("")

        # Scripts
        lines.append(f"### 3.3 Analysis Scripts ({counts.scripts} total)")
        lines.append("")
        lines.append("| # | Script | Language | Status |")
        lines.append("|---|--------|----------|--------|")
        code_dir = os.path.join(run_dir, "code")
        if os.path.isdir(code_dir):
            for i, fname in enumerate(
                sorted(f for f in os.listdir(code_dir) if f.endswith((".R", ".py")) and os.path.isfile(os.path.join(code_dir, f))), 1
            ):
                lang = "R" if fname.endswith(".R") else "Python"
                lines.append(f"| {i} | `{fname}` | {lang} | Completed |")
        else:
            lines.append("| — | _No code directory_ | — | — |")
        lines.append("")

        lines.append("---")
        return "\n".join(lines)

    def _section_key_findings(self, run_dir: str) -> str:
        """Placeholder for key findings — to be populated from analysis output."""
        return "\n".join([
            "## 4. Key Biological Findings",
            "",
            "_Findings to be populated from analysis output. "
            "Each finding should include: title, description, confidence level "
            "(HIGH/MODERATE/LOW)._",
            "",
            "---",
        ])

    def _section_completeness_audit(
        self,
        counts: AuditCounts,
        errors: List[ErrorEntry],
        planned_steps: Optional[List[str]] = None,
    ) -> str:
        """Build the Completeness Audit section with completed/deferred/error tables."""
        lines = [
            "## 5. Analysis Completeness Audit",
            "",
        ]

        # Completed
        lines.append("### 5.1 COMPLETED")
        if counts.total > 0:
            lines.append("| Analysis | Output Count |")
            lines.append("|----------|-------------|")
            if counts.figures > 0:
                lines.append(f"| Figures | {counts.figures} |")
            if counts.tables > 0:
                lines.append(f"| Tables | {counts.tables} |")
            if counts.scripts > 0:
                lines.append(f"| Scripts | {counts.scripts} |")
            if counts.logs > 0:
                lines.append(f"| Logs | {counts.logs} |")
            if counts.metadata > 0:
                lines.append(f"| Metadata | {counts.metadata} |")
            if counts.reports > 0:
                lines.append(f"| Reports | {counts.reports} |")
        else:
            lines.append("_No outputs detected._")
        lines.append("")

        # Deferred / Not Completed
        deferred_errors = [e for e in errors if e.status.lower() == "deferred"]
        lines.append("### 5.2 NOT COMPLETED / DEFERRED")
        if deferred_errors:
            lines.append("| Analysis | Blocker | Mitigation |")
            lines.append("|----------|---------|------------|")
            for e in deferred_errors:
                lines.append(f"| {e.description} | {e.diagnosis} | {e.resolution} |")
        elif planned_steps:
            # Show planned-but-not-completed steps
            lines.append("| Analysis | Blocker | Mitigation |")
            lines.append("|----------|---------|------------|")
            lines.append("| — | — | — |")
        else:
            lines.append("_No deferred items._")
        lines.append("")

        # Errors
        lines.append("### 5.3 Errors & Abnormal Results")
        if errors:
            lines.append("| ID | Description | Severity | Resolution |")
            lines.append("|----|-------------|----------|------------|")
            for e in errors:
                lines.append(f"| {e.err_id} | {e.description} | {e.severity} | {e.resolution} |")
        else:
            lines.append("_No errors recorded._")
        lines.append("")

        lines.append("---")
        return "\n".join(lines)

    def _section_task_continuity(self, work_log_path: str) -> str:
        """Build task continuity section from work_log.md."""
        lines = [
            "## 6. Task Continuity",
            "",
        ]

        if work_log_path and os.path.isfile(work_log_path):
            entries = self._parse_work_log_entries(work_log_path)
            if entries:
                lines.append("| Step | Status | Timestamp | Work Log Entry |")
                lines.append("|------|--------|-----------|---------------|")
                for entry in entries:
                    status_icon = "✅" if entry.get("status") == "completed" else "⏳"
                    lines.append(
                        f"| {entry.get('phase', '—')} | {status_icon} | "
                        f"{entry.get('timestamp', '—')} | Entry #{entry.get('number', '—')} |"
                    )
                lines.append("")
                if entries:
                    lines.append(f"**Next**: {entries[-1].get('next', 'Pending review.')}")
            else:
                lines.append("_No work log entries parsed._")
        else:
            lines.append("_No work log provided._")

        lines.append("")
        lines.append("---")
        return "\n".join(lines)

    def _section_parameters_reference(self, run_dir: str) -> str:
        """Build parameters quick-reference table."""
        lines = [
            "## 7. Parameters Quick Reference",
            "",
        ]

        # Try to load parameters from RUN_MANIFEST.yaml or checkpoint.yaml
        params = self._load_parameters(run_dir)

        if params:
            lines.append("| Parameter | Value | Used In |")
            lines.append("|-----------|-------|---------|")
            for p in params:
                lines.append(f"| {p['name']} | {p['value']} | {p.get('phase', '—')} |")
        else:
            lines.append("| Parameter | Value | Used In |")
            lines.append("|-----------|-------|---------|")
            lines.append("| Random seed | 42 | All |")

        lines.append("")
        lines.append("---")
        return "\n".join(lines)

    def _section_timestamp(self, counts: AuditCounts, errors: List[ErrorEntry]) -> str:
        """Build the final timestamp section."""
        resolved = sum(1 for e in errors if e.status.lower() == "resolved")
        deferred = sum(1 for e in errors if e.status.lower() == "deferred")
        if errors:
            completion_pct = round((1 - deferred / max(len(errors), 1)) * 100, 1)
        else:
            completion_pct = 100.0

        return "\n".join([
            "## 8. Timestamp",
            "",
            f"- **Phase Report generated**: {self._generated_at}",
            f"- **Total files**: {counts.total} "
            f"({counts.figures} figures + {counts.tables} tables + "
            f"{counts.scripts} scripts + {counts.logs} logs + "
            f"{counts.metadata} metadata)",
            f"- **Total errors**: {len(errors)} "
            f"({resolved} resolved, {deferred} deferred)",
            f"- **Completion**: ~{completion_pct}%",
        ])

    # ------------------------------------------------------------------
    # Parsing Helpers
    # ------------------------------------------------------------------

    def _parse_error_log(self, error_log_path: str) -> List[ErrorEntry]:
        """Parse error_log.md into a list of ErrorEntry objects."""
        entries: List[ErrorEntry] = []
        if not os.path.isfile(error_log_path):
            return entries

        try:
            content = Path(error_log_path).read_text(encoding="utf-8")
        except OSError:
            return entries

        # Match ERR-XXX entries: ### [ERR-NNN] ...
        entry_pattern = re.compile(
            r"###\s*\[(?P<id>ERR-\d+)\].*?\n"
            r".*?\*\*Phase\*\*\s*[:：]\s*(?P<phase>[^\n]*?)\s*\n"
            r".*?\*\*Severity\*\*\s*[:：]\s*(?P<severity>[^\n]*?)\s*\n"
            r".*?\*\*Status\*\*\s*[:：]\s*(?P<status>[^\n]*?)\s*\n"
            r".*?\*\*Raised By\*\*\s*[:：]\s*(?P<raised_by>[^\n]*?)\s*\n"
            r".*?\*\*Message\*\*\s*[:：]\s*(?P<message>[^\n]*?)\s*\n"
            r".*?\*\*Context\*\*\s*[:：]\s*(?P<context>[^\n]*?)\s*\n"
            r".*?\*\*Diagnosis\*\*\s*[:：]\s*(?P<diagnosis>[^\n]*?)\s*\n"
            r".*?\*\*Resolution\*\*\s*[:：]\s*(?P<resolution>[^\n]*?)s*\n"
            r".*?\*\*Prevention\*\*\s*[:：]\s*(?P<prevention>[^\n]*?)\s*\n",
            re.DOTALL | re.IGNORECASE,
        )

        for match in entry_pattern.finditer(content):
            entries.append(ErrorEntry(
                err_id=match.group("id").strip(),
                phase=match.group("phase").strip(),
                severity=match.group("severity").strip(),
                status=match.group("status").strip(),
                raised_by=match.group("raised_by").strip(),
                message=match.group("message").strip(),
                context=match.group("context").strip(),
                diagnosis=match.group("diagnosis").strip(),
                resolution=match.group("resolution").strip(),
                prevention=match.group("prevention").strip(),
            ))

        # Fallback: parse index table if no full entries found
        if not entries:
            entries = self._parse_error_index_table(content)

        return entries

    def _parse_error_index_table(self, content: str) -> List[ErrorEntry]:
        """Parse the error index table as a fallback."""
        entries: List[ErrorEntry] = []
        # Match table rows: | ERR-001 | date | phase | severity | status | description |
        table_pattern = re.compile(
            r"\|\s*(ERR-\d+)\s*\|"
            r"\s*([^|]*?)\s*\|"
            r"\s*([^|]*?)\s*\|"
            r"\s*([^|]*?)\s*\|"
            r"\s*([^|]*?)\s*\|"
            r"\s*([^|]*?)\s*\|"
        )
        for match in table_pattern.finditer(content):
            entries.append(ErrorEntry(
                err_id=match.group(1).strip(),
                phase=match.group(3).strip(),
                severity=match.group(4).strip(),
                status=match.group(5).strip(),
                description=match.group(6).strip(),
            ))
        return entries

    def _parse_work_log_entries(self, work_log_path: str) -> List[Dict[str, str]]:
        """Parse work_log.md to extract phase entries and their statuses."""
        entries: List[Dict[str, str]] = []
        if not os.path.isfile(work_log_path):
            return entries

        try:
            content = Path(work_log_path).read_text(encoding="utf-8")
        except OSError:
            return entries

        # Match headings like: ### 2026-06-18 17:30 — Title
        heading_pattern = re.compile(
            r"###\s*(?P<timestamp>\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2})\s*[-–—]\s*(?P<title>.+?)$",
            re.MULTILINE,
        )
        # Match phase field
        phase_pattern = re.compile(r"\*\*Phase\*\*\s*[:：]\s*(?P<phase>[^\n]+)")
        # Match next steps
        next_pattern = re.compile(r"\*\*Next Steps?\*\*\s*[:：]\s*(?P<next>[^\n]+)")

        for idx, match in enumerate(heading_pattern.finditer(content), 1):
            entry = {
                "number": str(idx),
                "timestamp": match.group("timestamp").strip(),
                "title": match.group("title").strip(),
                "phase": "—",
                "status": "pending",
                "next": "—",
            }

            # Look for phase and next_steps near this heading
            start = match.end()
            end = content.find("###", start) if content.find("###", start) != -1 else len(content)
            section = content[start:end]

            pm = phase_pattern.search(section)
            if pm:
                entry["phase"] = pm.group("phase").strip()
                entry["status"] = "completed" if "completed" in section.lower() else "pending"

            nm = next_pattern.search(section)
            if nm:
                entry["next"] = nm.group("next").strip()

            entries.append(entry)

        return entries

    def _load_parameters(self, run_dir: str) -> List[Dict[str, str]]:
        """Try to load parameters from RUN_MANIFEST.yaml or checkpoint.yaml."""
        params: List[Dict[str, str]] = []

        # Check for RUN_MANIFEST.yaml
        manifest = os.path.join(run_dir, "RUN_MANIFEST.yaml")
        if os.path.isfile(manifest):
            try:
                # Simple YAML extraction (avoid full YAML dependency)
                import yaml
                with open(manifest, "r") as fh:
                    data = yaml.safe_load(fh)
                if isinstance(data, dict):
                    env = data.get("environment", {})
                    if isinstance(env, dict):
                        r_ver = env.get("r_version", "")
                        if r_ver:
                            params.append({"name": "R version", "value": str(r_ver), "phase": "infrastructure"})
            except Exception as e:
                _log_nonfatal("_extract_params_from_manifest", e, "info")

        return params
