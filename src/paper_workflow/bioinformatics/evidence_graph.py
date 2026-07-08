"""Run-scoped evidence graph for bioinformatics method assets."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


VALID_EVIDENCE_LEVELS = {"observation", "association", "validated", "hypothesis"}


@dataclass(frozen=True)
class EvidenceClaim:
    """A publication-facing claim candidate derived from run source maps."""

    claim_id: str
    claim_text: str
    evidence_level: str
    supporting_nodes: list[str] = field(default_factory=list)
    supporting_artifacts: list[str] = field(default_factory=list)
    statistical_unit: str = ""
    reviewer_risk: list[str] = field(default_factory=list)
    claim_boundary: str = ""
    contradiction: str = ""
    next_validation_needed: str = ""

    def to_dict(self) -> dict[str, Any]:
        level = self.evidence_level if self.evidence_level in VALID_EVIDENCE_LEVELS else "hypothesis"
        return {
            "claim_id": self.claim_id,
            "claim_text": self.claim_text,
            "evidence_level": level,
            "supporting_nodes": self.supporting_nodes,
            "supporting_artifacts": self.supporting_artifacts,
            "statistical_unit": self.statistical_unit,
            "reviewer_risk": self.reviewer_risk,
            "claim_boundary": self.claim_boundary,
            "contradiction": self.contradiction,
            "next_validation_needed": self.next_validation_needed,
        }


def classify_evidence_level(entry: dict[str, Any]) -> str:
    """Classify a source-map item into a conservative evidence level."""
    text = " ".join(
        str(entry.get(key, ""))
        for key in ["figure_id", "table_id", "method", "claim_boundary", "module_id"]
    ).lower()
    risk_text = " ".join(str(item).lower() for item in entry.get("module_reviewer_risk", []) or [])
    if any(token in text or token in risk_text for token in ["hypothesis", "ligand", "colocalization", "communication"]):
        return "hypothesis"
    if any(token in text for token in ["marker", "feature plot", "visualization", "qc", "pilot"]):
        return "observation"
    if any(token in text for token in ["differential", "pseudobulk", "deseq2", "limma", "wgcna", "fgsea"]):
        return "association"
    if str(entry.get("statistical_unit", "")).lower() in {"sample", "patient", "donor"}:
        return "association"
    return "hypothesis"


def next_validation_for(entry: dict[str, Any], evidence_level: str) -> str:
    """Return the next validation needed before a claim is promoted."""
    text = " ".join(
        str(entry.get(key, ""))
        for key in ["figure_id", "table_id", "method", "claim_boundary", "module_id"]
    ).lower()
    if evidence_level == "hypothesis":
        if any(token in text for token in ["spatial", "ligand", "communication", "colocalization", "nichenet", "cellchat"]):
            return "orthogonal validation and reviewed ligand/reference provenance"
        return "independent validation before manuscript-level inference"
    if evidence_level == "observation":
        return "sample-level statistical test or independent validation"
    if "wgcna" in text or "pathway" in text or "fgsea" in text:
        return "independent cohort or perturbation validation for mechanism claims"
    return "human reviewer check of design, statistical unit, and source maps"


def evidence_summary(claims: list[EvidenceClaim], *, source_map_valid: bool) -> dict[str, Any]:
    """Summarize claim readiness for evaluate-run output."""
    dicts = [claim.to_dict() for claim in claims]
    publication_candidates = [
        claim for claim in dicts
        if claim["evidence_level"] in {"association", "validated"}
        and not claim.get("contradiction")
        and source_map_valid
    ]
    hypothesis_only = [claim for claim in dicts if claim["evidence_level"] == "hypothesis"]
    blocked = [
        claim for claim in dicts
        if not source_map_valid or claim.get("contradiction")
    ]
    return {
        "claim_count": len(dicts),
        "publication_candidate_claims": len(publication_candidates),
        "hypothesis_only_claims": len(hypothesis_only),
        "blocked_claims": len(blocked),
        "evidence_levels": {
            level: len([claim for claim in dicts if claim["evidence_level"] == level])
            for level in sorted(VALID_EVIDENCE_LEVELS)
        },
    }
