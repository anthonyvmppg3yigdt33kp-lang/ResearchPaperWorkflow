"""Productivity and fail-closed performance ledger for release gates."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


DEFAULT_WEIGHTS = {
    "fail_closed": 20,
    "target_task_entry": 15,
    "research_intent_layer": 10,
    "production_module_ratio": 15,
    "environment_truth": 15,
    "seurat_validation": 15,
    "external_code_wrapper": 10,
    "documentation_truth": 10,
}


def score_productivity(criteria: dict[str, bool], weights: dict[str, int] | None = None) -> dict[str, Any]:
    """Score binary release criteria on a 100-point productivity scale."""
    weights = dict(weights or DEFAULT_WEIGHTS)
    scored = []
    total = 0
    achieved = 0
    for key, weight in weights.items():
        passed = bool(criteria.get(key, False))
        total += int(weight)
        achieved += int(weight) if passed else 0
        scored.append({"criterion": key, "weight": int(weight), "passed": passed})
    score = round((achieved / total) * 100, 1) if total else 0.0
    return {
        "schema_version": "productivity_scorecard.v1",
        "score_type": "release_gate_completion",
        "interpretation": "Binary engineering release gates; not a scientific productivity or publication-readiness score.",
        "score": score,
        "target_score": 75,
        "status": "pass" if score >= 75 else "needs_fix",
        "criteria": scored,
    }


class PerformanceLedger:
    """Persist release-gate scorecards for audits and CI."""

    def __init__(self, path: Path):
        self.path = Path(path)

    def write(self, criteria: dict[str, bool], weights: dict[str, int] | None = None) -> dict[str, Any]:
        result = score_productivity(criteria, weights)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("w", encoding="utf-8") as fh:
            yaml.safe_dump(result, fh, allow_unicode=True, sort_keys=False)
        return result
