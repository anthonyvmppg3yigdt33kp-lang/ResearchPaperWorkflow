"""Method knowledge and reusable local experience used by the planner."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


def _read_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return data if isinstance(data, dict) else {}


class ResearchKnowledge:
    def __init__(self, project_root: Path):
        self.project_root = Path(project_root)
        payload = _read_yaml(self.project_root / "code_library" / "method_knowledge_base.yaml")
        self.methods = list(payload.get("methods", []) or [])
        self.lessons = list(
            _read_yaml(self.project_root / "local_experience" / "tuning_lessons.yaml").get("lessons", []) or []
        )
        self.patterns = list(
            _read_yaml(self.project_root / "local_experience" / "project_pattern_registry.yaml").get("patterns", []) or []
        )

    def methods_for(self, question_types: list[str]) -> list[dict[str, Any]]:
        wanted = set(question_types)
        return [
            method for method in self.methods
            if wanted.intersection(str(item) for item in method.get("question_types", []) or [])
        ]

    def experience_for(self, question_types: list[str]) -> list[dict[str, Any]]:
        wanted = set(question_types)
        selected = []
        for lesson in self.lessons:
            applies = set(str(item) for item in lesson.get("applies_to", []) or [])
            if not applies or wanted.intersection(applies):
                selected.append(lesson)
        return selected

    def patterns_for(self, project_goal: str) -> list[dict[str, Any]]:
        return [
            pattern for pattern in self.patterns
            if not pattern.get("project_goals") or project_goal in (pattern.get("project_goals") or [])
        ]
