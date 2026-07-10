"""Short researcher workflow that compiles to the existing TargetTask kernel."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from paper_workflow.research_intent.dashboard import ResearchDashboard
from paper_workflow.research_intent.planner import ResearchIntentPlanner, write_yaml
from paper_workflow.research_intent.schema import load_research_intent
from paper_workflow.target_task import TargetTaskOrchestrator


class ResearchWorkflowOrchestrator:
    """Expose start, analyze, review, write, package, and status actions."""

    def __init__(self, project_root: Path):
        self.project_root = Path(project_root)
        self.planner = ResearchIntentPlanner(self.project_root)
        self.targets = TargetTaskOrchestrator(self.project_root)
        self.dashboard = ResearchDashboard(self.project_root)

    def create_intent(
        self,
        *,
        project_id: str,
        question: str,
        modality: str,
        input_path: str,
        dataset_id: str,
        data_format: str,
        project_goal: str = "discovery",
        claim_boundary: str = "Exploratory analysis until replicate-aware inference, source maps, and fail-closed QA pass.",
    ) -> Path:
        intent = {
            "schema_version": "research_intent.v1",
            "project_id": project_id,
            "title": question[:120],
            "question": question,
            "project_goal": project_goal,
            "claim_boundary": claim_boundary,
            "data": {
                "dataset_id": dataset_id,
                "modality": modality,
                "format": data_format,
                "input_path": input_path,
                "role": "research_data",
                "biological_replicates": "unknown",
            },
            "expected_outputs": {
                "figures": ["analysis_overview", "primary_result"],
                "tables": ["quality_summary", "primary_result_table"],
                "reports": ["scientific_assessment", "strategy_simulation", "evaluation_report", "evidence_matrix"],
            },
            "constraints": {
                "evidence_grade": "exploratory",
                "forbidden_claims": ["disease mechanism", "clinical biomarker", "treatment response", "causal immune state"],
            },
        }
        path = self.project_root / "papers" / project_id / "research_plan" / "research_intent.yaml"
        write_yaml(path, intent)
        return path

    def validate(self, intent_path: Path | str) -> dict[str, Any]:
        return self.planner.validate(intent_path)

    def start(self, intent_path: Path | str) -> dict[str, Any]:
        plan = self.planner.plan(intent_path)
        target_plan = None
        if plan["ready_for_target_plan"]:
            target_plan = self.targets.plan(plan["target_task"])
        dashboard = self.dashboard.refresh(intent_path)
        return {
            "status": "planned" if target_plan else "needs_input",
            "research_plan": plan,
            "target_plan": target_plan,
            "dashboard": dashboard,
        }

    def analyze(self, intent_path: Path | str, *, approved: bool = False, execute: bool = False) -> dict[str, Any]:
        started = self.start(intent_path)
        if not started["research_plan"]["ready_for_target_plan"]:
            return started
        result = self.targets.run(
            started["research_plan"]["target_task"],
            approved=approved,
            execute=execute,
        )
        dashboard = self.dashboard.refresh(intent_path)
        return {"status": result.get("status", "unknown"), "target_run": result, "dashboard": dashboard}

    def review(self, intent_path: Path | str) -> dict[str, Any]:
        started = self.start(intent_path)
        if not started["research_plan"]["ready_for_target_plan"]:
            return started
        evaluation = self.targets.evaluate(started["research_plan"]["target_task"], fail_closed=True)
        dashboard = self.dashboard.refresh(intent_path)
        return {"status": evaluation.get("status", "unknown"), "evaluation": evaluation, "dashboard": dashboard}

    def write(self, intent_path: Path | str) -> dict[str, Any]:
        reviewed = self.review(intent_path)
        if reviewed.get("status") not in {"pass", "workflow_test_pass"}:
            return {
                "status": "blocked",
                "reason": "evidence-bound writing requires a fail-closed pass",
                "review": reviewed,
            }
        plan = self.planner.plan(intent_path)
        package = self.targets.package(plan["target_task"])
        return {"status": package.get("final_status", "unknown"), "package": package, "dashboard": self.dashboard.refresh(intent_path)}

    def package(self, intent_path: Path | str) -> dict[str, Any]:
        started = self.start(intent_path)
        if not started["research_plan"]["ready_for_target_plan"]:
            return started
        package = self.targets.package(started["research_plan"]["target_task"])
        return {"status": package.get("final_status", "unknown"), "package": package, "dashboard": self.dashboard.refresh(intent_path)}

    def status(self, intent_path: Path | str) -> dict[str, Any]:
        intent = load_research_intent(intent_path)
        plan_dir = self.project_root / "papers" / str(intent["project_id"]) / "research_plan"
        if not (plan_dir / "target_task.yaml").exists():
            return {"status": "needs_input", "message": "run research start before requesting status"}
        return self.dashboard.refresh(intent_path)

    def copy_intent(self, source: Path | str, destination: Path | str) -> Path:
        data = load_research_intent(source)
        path = Path(destination)
        write_yaml(path, data)
        return path
