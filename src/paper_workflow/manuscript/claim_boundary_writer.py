"""Claim-boundary ledger generation from run evaluation evidence."""

from __future__ import annotations

from typing import Any

from paper_workflow.outputs.result_run_manager import utc_now


def build_claim_boundary_ledger(target: dict[str, Any], evaluation: dict[str, Any]) -> dict[str, Any]:
    """Return the manuscript claim permissions allowed by current evidence."""
    final_status = str(evaluation.get("status", "unknown"))
    return {
        "schema_version": "claim_boundary_ledger.v1",
        "target_id": target.get("target_id", ""),
        "evidence_grade": target.get("evidence_grade", ""),
        "claim_boundary": target.get("claim_boundary", ""),
        "forbidden_claims": (target.get("analysis_goal") or {}).get("forbidden_claims", []),
        "scientific_claim_permission": "exploratory_only" if final_status == "pass" else "no_claim_until_fail_closed_passes",
        "final_status": final_status,
        "updated_at": utc_now(),
    }
