"""Compact researcher-facing status view over run-scoped workflow evidence."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from paper_workflow.research_intent.schema import load_research_intent


def read_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return data if isinstance(data, dict) else {}


class ResearchDashboard:
    def __init__(self, project_root: Path):
        self.project_root = Path(project_root)

    def refresh(self, intent_path: Path | str) -> dict[str, Any]:
        intent = load_research_intent(intent_path)
        project_id = str(intent["project_id"])
        paper_dir = self.project_root / "papers" / project_id
        plan_dir = paper_dir / "research_plan"
        assessment = read_yaml(plan_dir / "scientific_assessment.yaml")
        strategy = read_yaml(plan_dir / "strategy_simulation.yaml")
        target = read_yaml(plan_dir / "target_task.yaml")
        target_id = str(target.get("target_id", ""))
        run_dir = paper_dir / "results" / "runs" / target_id if target_id else None
        evaluation = read_yaml(run_dir / "evaluation_report.yaml") if run_dir else {}
        next_plan = read_yaml(run_dir / "qc" / "next_analysis_plan.yaml") if run_dir else {}

        status = (
            evaluation.get("status")
            or (evaluation.get("evaluation_status") or {}).get("final_status")
            or ("planned" if target else "intent_only")
        )
        blockers = []
        for item in assessment.get("execution_blockers", []) or []:
            blockers.append(f"{item.get('field')}: {item.get('reason')}")
        blockers.extend(str(item) for item in next_plan.get("blocking_issues", []) or [])
        human_review = [str(item) for item in next_plan.get("human_review_items", []) or []]
        next_actions = [str(item) for item in next_plan.get("recommended_next_modules", []) or []]
        if not next_actions:
            next_actions = [
                "review scientific assessment and strategy alternatives",
                "resolve blocking data or environment requirements before real execution",
            ]

        required = {
            "methods": bool(run_dir and (run_dir / "manuscript" / "methods_draft.md").exists()),
            "results": bool(run_dir and (run_dir / "manuscript" / "results_skeleton.md").exists()),
            "evidence": bool(run_dir and (run_dir / "tables" / "evidence_matrix.tsv").exists()),
            "source_maps": bool(run_dir and (run_dir / "figure_source_map.yaml").exists() and (run_dir / "table_source_map.yaml").exists()),
            "quality": (evaluation.get("bioinformatics_quality_status") == "pass"),
        }
        readiness = round(100 * sum(required.values()) / len(required))
        dashboard = {
            "schema_version": "research_dashboard.v1",
            "project_id": project_id,
            "scientific_question": intent["question"],
            "current_status": status,
            "target_id": target_id,
            "claim_boundary": intent["claim_boundary"],
            "recommended_now": [item.get("method_id") for item in strategy.get("recommended_now", []) or []],
            "deferred_methods": [item.get("method_id") for item in strategy.get("deferred", []) or []],
            "blocking_issues": list(dict.fromkeys(blockers)),
            "human_review_items": list(dict.fromkeys(human_review)),
            "next_best_actions": list(dict.fromkeys(next_actions)),
            "publication_readiness": {**required, "percent": readiness},
            "run_dir": self._project_relative(run_dir) if run_dir else "",
        }
        plan_dir.mkdir(parents=True, exist_ok=True)
        (plan_dir / "research_dashboard.yaml").write_text(
            yaml.safe_dump(dashboard, allow_unicode=True, sort_keys=False),
            encoding="utf-8",
        )
        markdown_path = plan_dir / "RESEARCH_DASHBOARD.md"
        markdown_path.write_text(self._markdown(dashboard), encoding="utf-8")
        dashboard["dashboard_markdown"] = str(markdown_path)
        return dashboard

    def _project_relative(self, path: Path) -> str:
        try:
            return str(path.resolve().relative_to(self.project_root.resolve())).replace("\\", "/")
        except ValueError:
            return "external_path_not_recorded"

    @staticmethod
    def _markdown(data: dict[str, Any]) -> str:
        readiness = data["publication_readiness"]
        lines = [
            "# Research Dashboard",
            "",
            f"Project: {data['project_id']}",
            f"Status: {data['current_status']}",
            f"Question: {data['scientific_question']}",
            f"Claim boundary: {data['claim_boundary']}",
            "",
            "## Method Status",
            "",
            f"Recommended now: {', '.join(data['recommended_now']) or 'none'}",
            f"Deferred: {', '.join(data['deferred_methods']) or 'none'}",
            "",
            "## Blocking Issues",
            "",
            *([f"- {item}" for item in data["blocking_issues"]] or ["- none recorded"]),
            "",
            "## Next Best Actions",
            "",
            *[f"- {item}" for item in data["next_best_actions"]],
            "",
            "## Publication Readiness",
            "",
            f"Readiness: {readiness['percent']}%",
            f"Methods packet: {'ready' if readiness['methods'] else 'pending'}",
            f"Results packet: {'ready' if readiness['results'] else 'pending'}",
            f"Evidence matrix: {'ready' if readiness['evidence'] else 'pending'}",
            f"Source maps: {'ready' if readiness['source_maps'] else 'pending'}",
            f"Scientific QA: {'pass' if readiness['quality'] else 'not passed'}",
            "",
        ]
        return "\n".join(lines)
