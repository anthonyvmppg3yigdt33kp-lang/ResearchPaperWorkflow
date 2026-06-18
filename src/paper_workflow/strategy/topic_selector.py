"""
Topic Selector — Domain-agnostic research topic identification and refinement.

Converts natural language research ideas into structured topics with
scope boundaries, innovation assessment, and gap analysis.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional


@dataclass
class ResearchTopic:
    """Structured research topic definition."""

    idea: str
    field: str
    scope: str = "focused"
    innovation_level: int = 3
    keywords: list[str] = field(default_factory=list)
    research_questions: list[str] = field(default_factory=list)
    knowledge_gaps: list[str] = field(default_factory=list)
    estimated_sample_size: Optional[int] = None
    data_types: list[str] = field(default_factory=list)
    methods_required: list[str] = field(default_factory=list)
    related_work: list[dict] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict:
        return {
            "idea": self.idea, "field": self.field, "scope": self.scope,
            "innovation_level": self.innovation_level, "keywords": self.keywords,
            "research_questions": self.research_questions,
            "knowledge_gaps": self.knowledge_gaps,
            "estimated_sample_size": self.estimated_sample_size,
            "data_types": self.data_types, "methods_required": self.methods_required,
            "related_work": self.related_work, "created_at": self.created_at,
        }


class TopicSelector:
    """Selects and refines research topics for paper projects."""

    INNOVATION_RUBRIC = {
        1: "Incremental: replicates known findings with new dataset",
        2: "Extension: applies established methods to new context",
        3: "Integration: combines multiple data types or methods",
        4: "Novel method: introduces new analytical approach",
        5: "Breakthrough: paradigm-shifting discovery or method",
    }

    SCOPE_DEFINITIONS = {
        "preliminary": "Initial exploration, proof-of-concept",
        "focused": "Single clear hypothesis, 1-2 data types",
        "comprehensive": "Multiple hypotheses, multi-omics integration",
        "resource": "Data/resource generation, atlas building",
    }

    def __init__(self, domain_keywords: Optional[dict[str, list[str]]] = None):
        self.domain_keywords = domain_keywords or self._default_keywords()

    @staticmethod
    def _default_keywords() -> dict[str, list[str]]:
        return {
            "bioinformatics": ["computational", "pipeline", "algorithm", "machine learning", "integration", "deconvolution"],
            "genomics": ["genome", "transcriptome", "epigenome", "variant", "gene expression", "regulation"],
            "single-cell": ["scRNA-seq", "single-cell", "cell atlas", "heterogeneity", "trajectory", "cell type"],
            "spatial": ["spatial transcriptomics", "tissue architecture", "spatial domain", "niche", "cell communication"],
            "clinical": ["biomarker", "diagnosis", "prognosis", "therapy", "clinical outcome", "patient"],
            "immunology": ["immune", "inflammation", "T cell", "macrophage", "cytokine", "microenvironment"],
            "aging": ["aging", "senescence", "longevity", "age-related", "SASP", "rejuvenation"],
            "oncology": ["tumor", "cancer", "metastasis", "oncogene", "tumor microenvironment"],
        }

    def select_topic(self, idea: str, field: str) -> ResearchTopic:
        """Refine a research idea into a structured topic."""
        keywords = self._extract_keywords(field)
        questions = self._generate_questions(idea, field)
        gaps = self._identify_gaps(idea, field, keywords)
        innovation = self._assess_innovation(idea, keywords)
        scope = self._determine_scope(idea, keywords)
        data_types = self._identify_data_types(keywords)
        methods = self._identify_methods(keywords)

        return ResearchTopic(
            idea=idea, field=field, scope=scope,
            innovation_level=innovation, keywords=keywords,
            research_questions=questions, knowledge_gaps=gaps,
            data_types=data_types, methods_required=methods,
        )

    def _extract_keywords(self, field: str) -> list[str]:
        keywords = []
        field_lower = field.lower()
        for category, terms in self.domain_keywords.items():
            if category.lower() in field_lower:
                keywords.extend(terms[:3])
        keywords.extend([f.strip() for f in field.split(",")])
        return list(dict.fromkeys(keywords))

    def _generate_questions(self, idea: str, field: str) -> list[str]:
        questions = []
        idea_lower = idea.lower()
        if any(w in idea_lower for w in ["map", "atlas", "landscape"]):
            questions.append(f"What is the {field.split(',')[0].strip()} landscape of this system?")
        if any(w in idea_lower for w in ["aging", "disease", "vs", "versus", "comparison"]):
            questions.append("How does the molecular profile differ between conditions?")
        if any(w in idea_lower for w in ["mechanism", "pathway", "signaling"]):
            questions.append("What molecular mechanisms drive the observed differences?")
        if any(w in idea_lower for w in ["biomarker", "diagnosis", "prognosis", "therapy", "clinical"]):
            questions.append("What are the clinical/translational implications?")
        if not questions:
            questions = [
                f"What is the {field.split(',')[0].strip()} profile of {idea[:50]}?",
                "What factors drive the observed patterns?",
                "What are the biological and clinical implications?",
            ]
        return questions

    def _identify_gaps(self, idea: str, field: str, keywords: list[str]) -> list[str]:
        gaps = []
        field_lower = field.lower()
        if "spatial" in field_lower:
            gaps.append("Lack of spatial resolution in existing transcriptomic studies")
        if "aging" in field_lower:
            gaps.append("Molecular mechanisms of aging in this tissue remain unclear")
        if "single-cell" in field_lower:
            gaps.append("Cell-type-specific changes not resolved in bulk studies")
        if "multi-omics" in field_lower:
            gaps.append("Multi-omics integration framework not established")
        gaps.append("Need for systematic analysis with reproducible pipeline")
        return gaps

    def _assess_innovation(self, idea: str, keywords: list[str]) -> int:
        score = 2
        signals = {"first": 1, "novel": 1, "new method": 1, "multi-omics": 0.5,
                   "integration": 0.5, "atlas": 0.5, "mechanism": 0.5, "clinical": 0.5}
        for signal, weight in signals.items():
            if signal in idea.lower():
                score += weight
        return min(5, max(1, round(score)))

    def _determine_scope(self, idea: str, keywords: list[str]) -> str:
        idea_lower = idea.lower()
        if any(w in idea_lower for w in ["atlas", "resource", "landscape", "comprehensive"]):
            return "resource"
        elif any(w in idea_lower for w in ["multi-omics", "integration", "multi-modal"]):
            return "comprehensive"
        elif any(w in idea_lower for w in ["pilot", "preliminary", "exploratory"]):
            return "preliminary"
        return "focused"

    def _identify_data_types(self, keywords: list[str]) -> list[str]:
        mapping = {"spatial": "Spatial transcriptomics", "scrna": "scRNA-seq",
                   "scRNA": "scRNA-seq", "bulk": "Bulk RNA-seq", "atac": "scATAC-seq",
                   "proteomics": "Proteomics", "clinical": "Clinical metadata",
                   "imaging": "Histology/Immunofluorescence"}
        data_types = []
        for kw in keywords:
            for key, dtype in mapping.items():
                if key.lower() in kw.lower() and dtype not in data_types:
                    data_types.append(dtype)
        return data_types or ["Transcriptomics", "Clinical metadata"]

    def _identify_methods(self, keywords: list[str]) -> list[str]:
        methods = ["Quality control and filtering", "Dimensionality reduction",
                   "Clustering and annotation", "Differential analysis"]
        mapping = {"spatial": "Spatial domain analysis", "deconvolution": "Deconvolution",
                   "pathway": "Pathway enrichment", "communication": "Cell-cell communication",
                   "trajectory": "Trajectory analysis", "machine learning": "ML classification",
                   "integration": "Multi-omics integration", "network": "Network analysis"}
        for kw in keywords:
            for key, method in mapping.items():
                if key.lower() in kw.lower() and method not in methods:
                    methods.append(method)
        methods.append("Statistical testing with multiple-testing correction")
        return methods
