"""Build figure storylines from source-map evidence."""

from __future__ import annotations

from typing import Any


def build_figure_storyline(target: dict[str, Any], evidence_rows: list[dict[str, str]], evaluation: dict[str, Any]) -> str:
    """Render panel-level figure notes with explicit claim boundaries."""
    lines = [
        "# Figure Storyline",
        "",
        f"Target: {target.get('title', '')}",
        f"Evidence grade: {target.get('evidence_grade', '')}",
        f"Final status: {evaluation.get('status', 'unknown')}",
        "",
        "## Panels",
        "",
    ]
    figures = [row for row in evidence_rows if row.get("kind") == "figure"]
    if not figures:
        lines.append("No figure can be promoted because no valid figure source map entry is available.")
    for row in figures:
        lines.extend([
            f"- {row.get('id', '')}: {row.get('method', '')}",
            f"  Boundary: {row.get('claim_boundary', '') or 'not declared'}",
        ])
    return "\n".join(lines) + "\n"
