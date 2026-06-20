"""
Postmortem Ledger — Records reviewer feedback and auto-generates gate improvements.

v3.0: Every submission, rejection, and revision is recorded. Reviewer criticisms
are mined to suggest new quality gates, closing the self-improvement loop.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

import yaml


@dataclass
class GateSuggestion:
    suggested_gate_name: str
    severity: str  # critical, high, medium
    description: str
    trigger_reviewer_comment: str
    proposed_check_method: str
    source_submission_id: str = ""
    suggested_at: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class SubmissionRecord:
    submission_id: str
    journal: str
    manuscript_title: str
    submitted_at: str = ""
    decision: str = "pending"  # pending, desk_reject, review, major_revision, minor_revision, accept
    decision_date: str = ""
    reviews: list[dict] = field(default_factory=list)
    postmortem_complete: bool = False


class PostmortemLedger:
    """Records submission outcomes and extracts gate improvements from reviewer feedback.

    Key workflow:
    1. record_submission() → submission_id
    2. record_decision() → updates submission with decision and reviews
    3. extract_gate_suggestions() → parse review criticisms into new gate proposals
    4. generate_postmortem_report() → comprehensive post-submission analysis
    """

    # Common reviewer criticism patterns → gate suggestions
    CRITICISM_GATE_MAP = {
        "pseudoreplication": ("patient_level_independence", "critical",
                             "Statistical unit is patient, not cell/spot"),
        "batch effect": ("batch_confounding_audit", "high",
                        "Disease not confounded with batch"),
        "external validation": ("external_validation_or_limitation", "critical",
                               "External validation or explicit limitation"),
        "multiple testing": ("multiple_testing_control", "critical",
                            "Multiple testing correction specified"),
        "missing data": ("missing_data_strategy", "high",
                        "Missing data handling described"),
        "causal language": ("results_no_overinterpretation", "high",
                           "No causal claims for correlational results"),
        "cell annotation": ("cell_annotation_evidence", "high",
                           "Cell annotation supported by multiple evidence types"),
        "pseudobulk": ("de_pseudobulk_required", "high",
                      "Pseudobulk or mixed models for single-cell DE"),
        "data leakage": ("train_test_leakage_check", "critical",
                        "No leakage between train and test sets"),
        "calibration": ("model_calibration_reported", "high",
                       "Calibration metrics for prediction models"),
        "feature importance": ("explainability_sanity_check", "high",
                              "SHAP not interpreted as causal"),
        "deployment claim": ("deployment_claim_limited", "high",
                            "No clinical deployment claim without prospective study"),
        "sample overlap": ("sample_overlap_check", "critical",
                          "No sample overlap between cohorts"),
        "ethics": ("ethics_irb_or_public_exemption", "critical",
                  "Ethics approval or public data exemption documented"),
        "confounding": ("batch_confounding_audit", "high",
                       "Condition not confounded with technical variables"),
    }

    def __init__(self, paper_dir: Path, ledger_path: Optional[Path] = None):
        self.paper_dir = Path(paper_dir)
        self.ledger_path = ledger_path or (self.paper_dir / "postmortem_ledger.jsonl")
        self.submissions: dict[str, SubmissionRecord] = {}
        self._load()

    def record_submission(self, journal: str, manuscript_title: str,
                          date: str = "") -> str:
        sid = f"sub_{journal.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d%H%M')}"
        record = SubmissionRecord(
            submission_id=sid, journal=journal,
            manuscript_title=manuscript_title,
            submitted_at=date or datetime.now().isoformat(),
        )
        self.submissions[sid] = record
        self._save()
        return sid

    def record_decision(self, submission_id: str, decision: str,
                        reviews: list[dict], date: str = "") -> SubmissionRecord:
        if submission_id not in self.submissions:
            raise KeyError(f"Submission {submission_id} not found")
        record = self.submissions[submission_id]
        record.decision = decision
        record.decision_date = date or datetime.now().isoformat()
        record.reviews = reviews
        self._save()
        return record

    def extract_gate_suggestions(self, submission_id: str) -> list[GateSuggestion]:
        """Parse reviewer criticisms and suggest new quality gates."""
        if submission_id not in self.submissions:
            return []
        record = self.submissions[submission_id]
        suggestions = []

        all_comments = []
        for review in record.reviews:
            all_comments.append(review.get("general_comments", ""))
            for comment in review.get("specific_comments", []):
                all_comments.append(str(comment))

        combined = " ".join(all_comments).lower()

        for pattern, (gate_name, severity, desc) in self.CRITICISM_GATE_MAP.items():
            if pattern in combined:
                suggestions.append(GateSuggestion(
                    suggested_gate_name=gate_name,
                    severity=severity,
                    description=desc,
                    trigger_reviewer_comment=f"Reviewer mentioned: '{pattern}'",
                    proposed_check_method=f"scan_for_{pattern}_issues",
                    source_submission_id=submission_id,
                ))

        return suggestions

    def generate_postmortem_report(self, submission_id: str,
                                    output_path: Optional[Path] = None) -> Path:
        """Generate a comprehensive post-mortem analysis for a submission."""
        if submission_id not in self.submissions:
            raise KeyError(f"Submission {submission_id} not found")

        record = self.submissions[submission_id]
        gate_suggestions = self.extract_gate_suggestions(submission_id)

        path = output_path or (self.paper_dir / f"postmortem_{submission_id}.md")
        lines = [
            f"# Postmortem Report — {submission_id}",
            "",
            f"**Journal**: {record.journal}",
            f"**Decision**: {record.decision}",
            f"**Date**: {record.decision_date}",
            "",
            "## Reviewer Feedback Summary",
            f"Number of reviews: {len(record.reviews)}",
            "",
            "## Suggested New Quality Gates",
        ]

        if gate_suggestions:
            for gs in gate_suggestions:
                lines.append(f"- **{gs.suggested_gate_name}** ({gs.severity})")
                lines.append(f"  - Trigger: {gs.trigger_reviewer_comment}")
                lines.append(f"  - Check: {gs.proposed_check_method}")
        else:
            lines.append("No new gate suggestions extracted.")

        lines += [
            "",
            "## Lessons Learned",
            "- Review all gate suggestions above",
            "- Consider adding new gates to config/default_config.yaml",
            "- Update method cards if reviewer suggested alternative methods",
            "",
            f"*Generated: {datetime.now().isoformat()}*",
        ]

        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        return path

    def update_deprecated_methods(self, deprecated_path: Path) -> None:
        """Read deprecated_methods.yaml and mark obsolete methods."""
        if deprecated_path.exists():
            with open(deprecated_path, "r", encoding="utf-8") as f:
                deprecated = yaml.safe_load(f)
            # Log deprecated methods to ledger
            for method in deprecated.get("deprecated_methods", []):
                self._log_deprecation(method)

    def _log_deprecation(self, method: dict) -> None:
        """Log a method deprecation event."""
        import json
        event = {
            "event_type": "method_deprecated",
            "method_id": method.get("method_id", ""),
            "deprecated_date": method.get("deprecated_date", ""),
            "reason": method.get("reason", ""),
            "superseded_by": method.get("superseded_by", ""),
            "recorded_at": datetime.now().isoformat(),
        }
        with open(self.ledger_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(event, ensure_ascii=False) + "\n")

    def _save(self) -> None:
        import json
        with open(self.ledger_path, "w", encoding="utf-8") as f:
            for record in self.submissions.values():
                f.write(json.dumps({
                    "submission_id": record.submission_id,
                    "journal": record.journal,
                    "decision": record.decision,
                    "decision_date": record.decision_date,
                }, ensure_ascii=False) + "\n")

    def _load(self) -> None:
        import json
        if self.ledger_path.exists():
            with open(self.ledger_path, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        try:
                            data = json.loads(line)
                            sid = data.get("submission_id", "")
                            if sid:
                                self.submissions[sid] = SubmissionRecord(
                                    submission_id=sid,
                                    journal=data.get("journal", ""),
                                    manuscript_title="",
                                    decision=data.get("decision", "pending"),
                                    decision_date=data.get("decision_date", ""),
                                    postmortem_complete=True,
                                )
                        except (json.JSONDecodeError, KeyError):
                            continue
