"""Create a Results skeleton that respects fail-closed evaluation."""

from __future__ import annotations

from typing import Any


def build_results_skeleton(target: dict[str, Any], evidence_rows: list[dict[str, str]], evaluation: dict[str, Any]) -> str:
    """Render only conclusions allowed by the final run status."""
    final_status = str(evaluation.get("status", "unknown"))
    lines = ["# Results Skeleton", ""]
    if final_status != "pass":
        lines.extend([
            "No conclusion paragraph is generated because the fail-closed evaluation did not pass.",
            f"Current final status: {final_status}",
            "",
            "Allowed statement: the TargetTask produced a blocked or incomplete workflow-validation packet that identifies the missing evidence gates.",
        ])
        return "\n".join(lines) + "\n"
    lines.extend([
        f"The `{target.get('target_id', '')}` workflow-validation TargetTask completed with pass status.",
        "Results are limited to tutorial workflow validation and exploratory subcluster structure.",
        f"Evidence entries available: {len(evidence_rows)}",
        "Unsupported conclusions: disease mechanism, clinical biomarker, treatment response, or causal immune state.",
    ])
    return "\n".join(lines) + "\n"
