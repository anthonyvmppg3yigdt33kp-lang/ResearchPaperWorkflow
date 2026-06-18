"""
Journal Targeter — Domain-agnostic journal selection and compliance checking.

Loads journal profiles from config/journal_database.yaml.
Supports exact match, fuzzy match, and topic-based recommendation.
"""
from __future__ import annotations

from dataclasses import dataclass, field, fields
from pathlib import Path
from typing import Any, Optional

import yaml


@dataclass
class JournalTarget:
    """Target journal profile."""

    name: str
    full_name: str = ""
    impact_factor: float = 0.0
    category: str = ""
    format_type: str = "LaTeX"
    citation_style: str = "Vancouver"
    abstract_word_limit: int = 250
    figure_limit: int = 6
    main_text_word_limit: int = 5000
    requires_data_availability: bool = True
    requires_code_availability: bool = True
    open_access: bool = False
    submission_system: str = ""
    special_requirements: list[str] = field(default_factory=list)
    fit_score: int = 3
    fit_reasoning: str = ""

    _valid_fields: set = field(default=None, init=False, repr=False)

    def __post_init__(self):
        if JournalTarget._valid_fields is None:
            JournalTarget._valid_fields = {f.name for f in fields(JournalTarget)}

    @classmethod
    def _filter_fields(cls, data: dict) -> dict:
        if cls._valid_fields is None:
            cls._valid_fields = {f.name for f in fields(cls)}
        return {k: v for k, v in data.items() if k in cls._valid_fields}

    def to_dict(self) -> dict:
        return {
            "name": self.name, "full_name": self.full_name,
            "impact_factor": self.impact_factor, "category": self.category,
            "format_type": self.format_type, "citation_style": self.citation_style,
            "abstract_word_limit": self.abstract_word_limit,
            "figure_limit": self.figure_limit,
            "main_text_word_limit": self.main_text_word_limit,
            "requires_data_availability": self.requires_data_availability,
            "requires_code_availability": self.requires_code_availability,
            "open_access": self.open_access,
            "submission_system": self.submission_system,
            "special_requirements": self.special_requirements,
            "fit_score": self.fit_score, "fit_reasoning": self.fit_reasoning,
        }


class JournalTargeter:
    """
    Selects target journals and resolves journal-specific requirements.

    Loads journal database from config/journal_database.yaml.
    Falls back to built-in defaults if config not found.
    """

    def __init__(self, project_root: Optional[Path] = None, config_path: Optional[Path] = None):
        self.project_root = project_root or self._find_project_root()
        self.config_path = config_path or (self.project_root / "config" / "journal_database.yaml")
        self._database = self._load_database()

    def _find_project_root(self) -> Path:
        current = Path(__file__).resolve().parent
        for _ in range(10):
            if (current / "AGENTS.md").exists() or (current / "CLAUDE.md").exists():
                return current
            current = current.parent
        return Path.cwd()

    def _load_database(self) -> dict:
        """Load journal database from YAML config."""
        if self.config_path.exists():
            with open(self.config_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
                if data and "journals" in data:
                    return data["journals"]
        return self._default_database()

    @staticmethod
    def _default_database() -> dict:
        """Minimal built-in journal database."""
        return {
            "Nature Genetics": {
                "full_name": "Nature Genetics", "impact_factor": 30.0,
                "category": "high-impact", "format_type": "LaTeX",
                "citation_style": "Vancouver", "abstract_word_limit": 150,
                "figure_limit": 6, "main_text_word_limit": 3000,
                "requires_data_availability": True, "requires_code_availability": True,
                "open_access": False, "submission_system": "Editorial Manager",
                "special_requirements": ["Structured abstract", "Reporting Summary"],
                "scope_keywords": ["genetics", "genomics", "transcriptomics", "gene regulation"],
            },
            "Genome Biology": {
                "full_name": "Genome Biology", "impact_factor": 12.0,
                "category": "specialty-high", "format_type": "LaTeX",
                "citation_style": "Vancouver", "abstract_word_limit": 250,
                "figure_limit": 8, "main_text_word_limit": 5000,
                "requires_data_availability": True, "requires_code_availability": True,
                "open_access": True, "submission_system": "Editorial Manager",
                "special_requirements": ["Open access", "Reviewer suggestion"],
                "scope_keywords": ["genomics", "transcriptomics", "bioinformatics", "single-cell", "spatial"],
            },
            "Nature Communications": {
                "full_name": "Nature Communications", "impact_factor": 16.0,
                "category": "high-impact-open", "format_type": "LaTeX",
                "citation_style": "Vancouver", "abstract_word_limit": 150,
                "figure_limit": 10, "main_text_word_limit": 5000,
                "requires_data_availability": True, "requires_code_availability": True,
                "open_access": True, "submission_system": "Editorial Manager",
                "special_requirements": ["Open access (APC)", "Reporting summary"],
                "scope_keywords": ["all sciences", "multidisciplinary", "genomics"],
            },
            "Bioinformatics": {
                "full_name": "Bioinformatics (Oxford)", "impact_factor": 5.0,
                "category": "methods", "format_type": "LaTeX",
                "citation_style": "Vancouver", "abstract_word_limit": 250,
                "figure_limit": 8, "main_text_word_limit": 5000,
                "requires_data_availability": True, "requires_code_availability": True,
                "open_access": False, "submission_system": "ScholarOne",
                "special_requirements": ["Software/tool available", "Supplementary data"],
                "scope_keywords": ["bioinformatics", "computational biology", "software", "methods"],
            },
            "Communications Biology": {
                "full_name": "Communications Biology", "impact_factor": 6.0,
                "category": "specialty-open", "format_type": "LaTeX",
                "citation_style": "Vancouver", "abstract_word_limit": 150,
                "figure_limit": 8, "main_text_word_limit": 4000,
                "requires_data_availability": True, "requires_code_availability": True,
                "open_access": True, "submission_system": "Editorial Manager",
                "special_requirements": ["Open access (APC)"],
                "scope_keywords": ["biology", "genomics", "bioinformatics"],
            },
        }

    @property
    def database(self) -> dict:
        return self._database

    def resolve_journal(self, name: str) -> JournalTarget:
        """Resolve a journal by name (exact or fuzzy match)."""
        if name in self._database:
            return JournalTarget(name=name, **JournalTarget._filter_fields(self._database[name]))

        name_lower = name.lower()
        for jname, jdata in self._database.items():
            if (name_lower in jname.lower()
                    or jdata.get("full_name", "").lower() in name_lower):
                return JournalTarget(name=jname, **JournalTarget._filter_fields(jdata))

        return JournalTarget(
            name=name, full_name=name, fit_score=1,
            fit_reasoning=f"Journal '{name}' not in database. Verify requirements manually.",
        )

    def recommend_journal(self, topic: Any) -> JournalTarget:
        """Recommend best-fit journal for a research topic."""
        best_journal = None
        best_score = -1
        topic_keywords = set(k.lower() for k in topic.keywords)

        for jname, jdata in self._database.items():
            score = self._calculate_fit(topic_keywords, topic.innovation_level, jdata)
            if score > best_score:
                best_score = score
                best_journal = jname

        if best_journal:
            journal = JournalTarget(name=best_journal, **JournalTarget._filter_fields(self._database[best_journal]))
            journal.fit_score = best_score
            journal.fit_reasoning = self._get_fit_reasoning(best_score, topic, journal)
            return journal

        return JournalTarget(name="Communications Biology", fit_score=2,
                             fit_reasoning="Default fallback — no clear match found")

    def _calculate_fit(self, topic_keywords: set, innovation: int, jdata: dict) -> int:
        score = 1
        scope_keywords = set(k.lower() for k in jdata.get("scope_keywords", []))
        overlap = topic_keywords & scope_keywords
        score += min(2, len(overlap))
        if jdata.get("impact_factor", 0) >= 20 and innovation >= 3:
            score += 1
        elif 8 <= jdata.get("impact_factor", 0) < 20 and innovation >= 2:
            score += 1
        elif jdata.get("impact_factor", 0) < 8:
            score += 1
        if jdata.get("open_access", False):
            score += 0.5
        return min(5, max(1, round(score)))

    def _get_fit_reasoning(self, score: int, topic: Any, journal: JournalTarget) -> str:
        prefix = {5: "Excellent fit", 4: "Strong fit", 3: "Good fit", 2: "Moderate fit"}.get(score, "Weak fit")
        parts = [f"{prefix} for {journal.name} (IF {journal.impact_factor}, {journal.category})"]
        if journal.open_access:
            parts.append("— Open access")
        return " ".join(parts)

    def get_compliance_checklist(self, journal: JournalTarget) -> list[dict]:
        """Generate compliance checklist for target journal."""
        checklist = [
            {"item": "Abstract word limit", "requirement": f"≤ {journal.abstract_word_limit} words", "category": "format"},
            {"item": "Figure limit", "requirement": f"≤ {journal.figure_limit} main figures", "category": "format"},
            {"item": "Main text word limit", "requirement": f"≤ {journal.main_text_word_limit} words", "category": "format"},
            {"item": "Citation style", "requirement": journal.citation_style, "category": "format"},
            {"item": "Data availability", "requirement": "Required" if journal.requires_data_availability else "Optional", "category": "ethics"},
            {"item": "Code availability", "requirement": "Required" if journal.requires_code_availability else "Optional", "category": "ethics"},
            {"item": "Format type", "requirement": journal.format_type, "category": "format"},
        ]
        for req in journal.special_requirements:
            checklist.append({"item": req, "requirement": "Required", "category": "special"})
        return checklist

    def list_journals(self, category: Optional[str] = None) -> list[dict]:
        """List available journals, optionally filtered by category."""
        journals = []
        for name, data in self._database.items():
            if category and data.get("category") != category:
                continue
            journals.append({
                "name": name, "full_name": data.get("full_name", ""),
                "impact_factor": data.get("impact_factor", 0),
                "category": data.get("category", ""),
                "open_access": data.get("open_access", False),
            })
        return sorted(journals, key=lambda j: j["impact_factor"], reverse=True)
