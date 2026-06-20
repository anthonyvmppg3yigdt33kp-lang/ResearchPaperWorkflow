"""
Method Radar — Scans scientific literature and repositories for new methods.

v3.0: Monthly scanner for new bioinformatics methods, reporting guidelines,
and analysis tools. Feeds into SkillSandbox for evaluation before integration.

Sources: PubMed, bioRxiv, arXiv (q-bio, stat.ML), EQUATOR Network, GitHub trending.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional


@dataclass
class MethodSignal:
    """A detected new method, tool, or guideline."""
    name: str
    source: str  # pubmed, biorxiv, arxiv, equator, github
    url: str
    published_date: str
    relevance_score: float = 0.0
    category: str = ""  # qc, de, clustering, integration, ml, visualization, guideline
    abstract_summary: str = ""
    detected_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict:
        return {
            "name": self.name, "source": self.source, "url": self.url,
            "published_date": self.published_date,
            "relevance_score": self.relevance_score,
            "category": self.category, "abstract_summary": self.abstract_summary,
            "detected_at": self.detected_at,
        }


class MethodRadar:
    """Scans for new methods across scientific sources.

    Designed to be run monthly (via cron or manual trigger).
    Results feed into SkillSandbox for evaluation.
    """

    # Search queries for each source
    QUERIES = {
        "pubmed": [
            '(bioinformatics[Title/Abstract] AND method[Title/Abstract] AND "202"[Date - Publication])',
            '(single-cell[Title/Abstract] OR spatial transcriptomics[Title/Abstract]) AND method[Title]',
            '(machine learning[Title] AND genomics[Title/Abstract]) AND benchmark[Title/Abstract]',
            '(reporting guideline[Title] OR checklist[Title]) AND ("202"[Date - Publication])',
        ],
        "biorxiv_keywords": [
            "bioinformatics method", "single-cell tool", "spatial transcriptomics",
            "benchmarking study", "reporting guideline",
        ],
        "github_topics": [
            "single-cell", "spatial-transcriptomics", "bioinformatics-pipeline",
            "machine-learning-genomics", "causal-inference",
        ],
    }

    CATEGORIES = ["qc", "dimensionality_reduction", "clustering", "de",
                  "cell_communication", "pathway", "trajectory", "integration",
                  "ml", "statistics", "visualization", "guideline"]

    def __init__(self):
        self.signals: list[MethodSignal] = []

    def scan_all(self) -> list[MethodSignal]:
        """Run all scans. In production, this would make API calls to each source."""
        self.signals = []
        self.signals.extend(self.scan_pubmed())
        self.signals.extend(self.scan_biorxiv())
        self.signals.extend(self.scan_equator())
        return self.signals

    def scan_pubmed(self, max_results: int = 50) -> list[MethodSignal]:
        """Search PubMed for new bioinformatics methods."""
        signals = []
        for query in self.QUERIES["pubmed"][:2]:
            signals.append(MethodSignal(
                name=f"PubMed search: {query[:80]}",
                source="pubmed", url=f"https://pubmed.ncbi.nlm.nih.gov/?term={query[:60]}",
                published_date=datetime.now().strftime("%Y-%m"),
                category="pending_classification",
                abstract_summary="Requires PubMed MCP search to populate results",
            ))
        return signals

    def scan_biorxiv(self) -> list[MethodSignal]:
        """Search bioRxiv for new method preprints."""
        signals = []
        for kw in self.QUERIES["biorxiv_keywords"][:3]:
            signals.append(MethodSignal(
                name=f"bioRxiv search: {kw}",
                source="biorxiv",
                url=f"https://www.biorxiv.org/search/{kw.replace(' ', '+')}",
                published_date=datetime.now().strftime("%Y-%m"),
                category="pending_classification",
                abstract_summary="Requires bioRxiv API call to populate results",
            ))
        return signals

    def scan_equator(self) -> list[MethodSignal]:
        """Check EQUATOR Network for new/updated reporting guidelines."""
        return [
            MethodSignal(
                name="EQUATOR Network — New/updated guidelines",
                source="equator",
                url="https://www.equator-network.org/reporting-guidelines/",
                published_date=datetime.now().strftime("%Y-%m"),
                category="guideline",
                abstract_summary="Check for new or updated reporting guidelines monthly",
                relevance_score=0.8,
            ),
        ]

    def rank_by_relevance(self, signals: list[MethodSignal],
                          project_domain: str = "") -> list[MethodSignal]:
        """Rank signals by relevance to a specific project domain."""
        domain_keywords = {
            "spatial_transcriptomics": ["spatial", "transcriptom", "visium", "merfish", "stereo"],
            "single_cell": ["single-cell", "scrna", "scatac", "cell type", "cluster"],
            "mendelian_randomization": ["mendelian", "instrumental variable", "causal", "gwas"],
            "multi_omics": ["multi-omic", "integration", "proteom", "metabolom"],
        }
        keywords = domain_keywords.get(project_domain, [])
        for sig in signals:
            sig.relevance_score = sum(
                0.25 for kw in keywords if kw.lower() in sig.name.lower() + sig.abstract_summary.lower()
            )
        return sorted(signals, key=lambda s: s.relevance_score, reverse=True)

    def generate_report(self, output_path: Optional[Path] = None) -> Path:
        """Generate a markdown radar report."""
        path = output_path or Path(f"method_radar_{datetime.now().strftime('%Y%m%d')}.md")
        lines = [
            f"# Method Radar Report — {datetime.now().strftime('%Y-%m-%d')}",
            "", f"**Total signals**: {len(self.signals)}",
            "", "## By Category", "",
        ]
        for cat in self.CATEGORIES:
            cat_signals = [s for s in self.signals if s.category == cat]
            if cat_signals:
                lines.append(f"### {cat} ({len(cat_signals)})")
                for s in cat_signals[:5]:
                    lines.append(f"- [{s.name}]({s.url}) — {s.source} ({s.published_date})")
                lines.append("")

        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        return path
