"""Synthesize run source maps into claim-level evidence artifacts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml

from paper_workflow.bioinformatics.evidence_graph import (
    EvidenceClaim,
    classify_evidence_level,
    evidence_summary,
    next_validation_for,
)


def _read_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh) or {}
    return data if isinstance(data, dict) else {}


def _as_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value]
    if value:
        return [str(value)]
    return []


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


class EvidenceSynthesizer:
    """Build evidence matrices and reviewer-risk reports for a run."""

    def __init__(self, run_dir: Path):
        self.run_dir = Path(run_dir)
        self.paper_dir = self.run_dir.parents[2]

    def build_claims(self) -> list[EvidenceClaim]:
        figure_map = _read_yaml(self.run_dir / "figure_source_map.yaml")
        table_map = _read_yaml(self.run_dir / "table_source_map.yaml")
        claims: list[EvidenceClaim] = []
        counter = 1
        for kind, entries in [
            ("figure", figure_map.get("figures", []) or []),
            ("table", table_map.get("tables", []) or []),
        ]:
            for entry in entries:
                if not isinstance(entry, dict):
                    continue
                artifact_id = str(entry.get("figure_id") or entry.get("table_id") or f"{kind}_{counter}")
                path = str(entry.get("path", ""))
                method = str(entry.get("method", "method not declared"))
                level = classify_evidence_level(entry)
                boundary = str(entry.get("claim_boundary") or entry.get("module_claim_boundary") or "")
                risks = _as_list(entry.get("module_reviewer_risk") or entry.get("reviewer_risk"))
                text = f"{kind} {artifact_id} supports a {level} claim using {method}"
                claims.append(
                    EvidenceClaim(
                        claim_id=f"claim_{counter:04d}",
                        claim_text=text,
                        evidence_level=level,
                        supporting_nodes=_as_list(entry.get("node_id")),
                        supporting_artifacts=[path] if path else [],
                        statistical_unit=str(entry.get("statistical_unit", "")),
                        reviewer_risk=risks,
                        claim_boundary=boundary,
                        contradiction=str(entry.get("contradiction", "")),
                        next_validation_needed=next_validation_for(entry, level),
                    )
                )
                counter += 1
        return claims

    def synthesize(self, *, source_map_valid: bool, write_outputs: bool = False) -> dict[str, Any]:
        claims = self.build_claims()
        summary = evidence_summary(claims, source_map_valid=source_map_valid)
        if write_outputs:
            self.write_outputs(claims, summary)
        return {
            "summary": summary,
            "claims": [claim.to_dict() for claim in claims],
            "output_paths": {
                "evidence_matrix": "tables/evidence_matrix.tsv",
                "reviewer_risk_report": "review/reviewer_risk_report.md",
                "figure_storyline": "brief/FIGURE_STORYLINE.md",
                "claim_ledger": "claims/claim_ledger.jsonl",
            },
        }

    def write_outputs(self, claims: list[EvidenceClaim], summary: dict[str, Any]) -> None:
        rows = [
            [
                "claim_id",
                "evidence_level",
                "statistical_unit",
                "supporting_nodes",
                "supporting_artifacts",
                "claim_boundary",
                "next_validation_needed",
            ]
        ]
        for claim in claims:
            item = claim.to_dict()
            rows.append([
                item["claim_id"],
                item["evidence_level"],
                item["statistical_unit"],
                ";".join(item["supporting_nodes"]),
                ";".join(item["supporting_artifacts"]),
                item["claim_boundary"],
                item["next_validation_needed"],
            ])
        _write(self.run_dir / "tables" / "evidence_matrix.tsv", "\n".join("\t".join(row) for row in rows) + "\n")

        risk_lines = ["# Reviewer Risk Report", "", f"- Claim count: {summary['claim_count']}"]
        for claim in claims:
            item = claim.to_dict()
            risks = item["reviewer_risk"] or ["not_declared"]
            risk_lines.extend([
                "",
                f"## {item['claim_id']}",
                f"- Evidence level: {item['evidence_level']}",
                f"- Reviewer risk: {', '.join(risks)}",
                f"- Claim boundary: {item['claim_boundary'] or 'not_declared'}",
                f"- Next validation: {item['next_validation_needed']}",
            ])
        _write(self.run_dir / "review" / "reviewer_risk_report.md", "\n".join(risk_lines) + "\n")

        figure_lines = ["# Figure Storyline", ""]
        for claim in claims:
            item = claim.to_dict()
            if item["supporting_artifacts"]:
                figure_lines.append(
                    f"- {item['claim_id']}: {item['claim_text']} ({'; '.join(item['supporting_artifacts'])})"
                )
        _write(self.run_dir / "brief" / "FIGURE_STORYLINE.md", "\n".join(figure_lines) + "\n")

        ledger = "\n".join(json.dumps(claim.to_dict(), ensure_ascii=False) for claim in claims)
        _write(self.run_dir / "claims" / "claim_ledger.jsonl", (ledger + "\n") if ledger else "")
