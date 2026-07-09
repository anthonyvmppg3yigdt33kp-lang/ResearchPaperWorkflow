"""Optional evidence-packet support for strategy-level method advice."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


class LiteratureMethodAdvisor:
    """Read a human- or search-agent-authored method evidence packet."""

    def __init__(self, paper_dir: Path | None = None):
        self.paper_dir = Path(paper_dir) if paper_dir else None

    def load_packet(self) -> dict[str, Any]:
        if not self.paper_dir:
            return {}
        path = self.paper_dir / "research_plan" / "method_evidence_packet.yaml"
        if not path.exists():
            return {}
        with path.open("r", encoding="utf-8") as fh:
            data = yaml.safe_load(fh) or {}
        return data if isinstance(data, dict) else {}

    def method_notes(self, method_family: str) -> list[str]:
        packet = self.load_packet()
        entries = packet.get("methods", []) if isinstance(packet, dict) else []
        notes = []
        for entry in entries or []:
            if not isinstance(entry, dict):
                continue
            family = str(entry.get("family") or entry.get("method_family") or "").lower()
            if family and family in method_family.lower():
                summary = entry.get("evidence_summary") or entry.get("note") or entry.get("recommendation")
                if summary:
                    notes.append(str(summary))
        return notes


def default_method_guidance(question_type: str) -> dict[str, Any]:
    """Return conservative strategy guidance for common bioinformatics intents."""
    if question_type == "cell_type_de":
        return {
            "recommended_methods": ["pseudobulk DE when biological replicates and sample_id mapping are available", "FindMarkers only for exploratory cell-level marker screening"],
            "not_recommended_methods": ["WGCNA as a replacement for primary group DE", "standalone enrichment without a valid ranked gene table"],
            "minimum_data_requirements": ["sample_id mapping", "group labels", "cell type or cluster labels", "replicate review"],
            "statistical_unit": "sample for inference; cell only for exploratory marker screening",
            "next_step_plan": ["audit metadata for sample_id and group columns", "prefer pseudobulk DE for inferential disease contrasts", "use FindMarkers outputs with explicit exploratory claim boundary"],
        }
    if question_type == "bulk_de":
        return {
            "recommended_methods": ["DESeq2 or limma-voom with sample-level design"],
            "not_recommended_methods": ["cell-level tests", "pathway enrichment before DE/ranking"],
            "minimum_data_requirements": ["raw count matrix", "sample metadata", "primary contrast", "replicates"],
            "statistical_unit": "sample",
            "next_step_plan": ["validate count matrix/sample metadata alignment", "fit primary DE model", "run enrichment only after ranked statistic exists"],
        }
    if question_type == "communication":
        return {
            "recommended_methods": ["CellChat or NicheNet as hypothesis-generating follow-up"],
            "not_recommended_methods": ["communication inference as direct mechanism proof"],
            "minimum_data_requirements": ["validated cell groups", "reviewed ligand-receptor or ligand-target database"],
            "statistical_unit": "cell group or sample-aware aggregate, depending on method",
            "next_step_plan": ["verify grouping", "record database version", "label claims as hypotheses"],
        }
    return {
        "recommended_methods": [],
        "not_recommended_methods": [],
        "minimum_data_requirements": [],
        "statistical_unit": "not_declared",
        "next_step_plan": [],
    }
