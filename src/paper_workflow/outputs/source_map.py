"""Source-map validation for run-scoped scientific artifacts."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


def read_source_map(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh) or {}
    return data if isinstance(data, dict) else {}


class SourceMapValidator:
    """Validate figure/table provenance fields used by run evaluation."""

    required_figure_fields = [
        "figure_id",
        "path",
        "source_data",
        "script",
        "method",
        "statistical_unit",
        "claim_boundary",
    ]

    required_table_fields = [
        "table_id",
        "path",
        "source_inputs",
        "method",
        "statistical_unit",
    ]

    def validate_figure_map(self, data: dict[str, Any]) -> list[str]:
        issues: list[str] = []
        figures = data.get("figures", [])
        if figures is None:
            figures = []
        if not isinstance(figures, list):
            return ["figure source map 'figures' must be a list"]
        for idx, figure in enumerate(figures):
            if not isinstance(figure, dict):
                issues.append(f"figure[{idx}] must be a mapping")
                continue
            for field in self.required_figure_fields:
                if not figure.get(field):
                    issues.append(f"figure[{idx}] missing {field}")
        return issues

    def validate_table_map(self, data: dict[str, Any]) -> list[str]:
        issues: list[str] = []
        tables = data.get("tables", [])
        if tables is None:
            tables = []
        if not isinstance(tables, list):
            return ["table source map 'tables' must be a list"]
        for idx, table in enumerate(tables):
            if not isinstance(table, dict):
                issues.append(f"table[{idx}] must be a mapping")
                continue
            for field in self.required_table_fields:
                if not table.get(field):
                    issues.append(f"table[{idx}] missing {field}")
        return issues

    def validate_run(self, run_dir: Path) -> dict[str, Any]:
        figure_map = read_source_map(run_dir / "figure_source_map.yaml")
        table_map = read_source_map(run_dir / "table_source_map.yaml")
        issues = []
        if not figure_map:
            issues.append("missing figure_source_map.yaml")
        else:
            issues.extend(self.validate_figure_map(figure_map))
        if not table_map:
            issues.append("missing table_source_map.yaml")
        else:
            issues.extend(self.validate_table_map(table_map))
        return {
            "status": "pass" if not issues else "needs_fix",
            "issue_count": len(issues),
            "issues": issues,
            "figure_count": len(figure_map.get("figures", []) or []) if figure_map else 0,
            "table_count": len(table_map.get("tables", []) or []) if table_map else 0,
        }
