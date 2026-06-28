"""
Paper Workflow — Unified end-to-end paper pipeline orchestrator.

Ties together Strategy, Loop Engine, Passport, and Integrity Gates.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

import yaml

from paper_workflow.strategy.research_strategy import ResearchStrategyManager, ResearchStrategy
from paper_workflow.engine.loop_engine import PaperLoopEngine, StageStatus, PipelineState
from paper_workflow.supervision.passport import PaperPassport
from paper_workflow.supervision.integrity import IntegrityGateChecker


@dataclass
class WorkflowState:
    paper_id: str
    started_at: str = field(default_factory=lambda: datetime.now().isoformat())
    completed_at: Optional[str] = None
    strategy: Optional[ResearchStrategy] = None
    pipeline_state: str = "initialized"
    stages_completed: int = 0
    stages_failed: int = 0
    errors: list[dict] = field(default_factory=list)
    decisions: list[dict] = field(default_factory=list)


class PaperWorkflow:
    """Unified paper workflow orchestrator."""

    def __init__(self, project_root: Optional[Path] = None, paper_id: Optional[str] = None):
        self.project_root = project_root or self._find_root()
        self.paper_id = paper_id
        self._strategy_manager: Optional[ResearchStrategyManager] = None
        self._engine: Optional[PaperLoopEngine] = None
        self._passport: Optional[PaperPassport] = None
        self._integrity: Optional[IntegrityGateChecker] = None
        self.state = WorkflowState(paper_id=paper_id or "uninitialized")

    @property
    def strategy_manager(self) -> ResearchStrategyManager:
        if self._strategy_manager is None:
            self._strategy_manager = ResearchStrategyManager(self.project_root)
        return self._strategy_manager

    @property
    def engine(self) -> PaperLoopEngine:
        if self._engine is None:
            papers_dir = self.project_root / "papers"
            self._engine = PaperLoopEngine(self.project_root, self.paper_id, papers_dir)
        return self._engine

    @property
    def passport(self) -> PaperPassport:
        if self._passport is None:
            self._passport = PaperPassport(self.engine.paper_dir)
        return self._passport

    @property
    def integrity(self) -> IntegrityGateChecker:
        if self._integrity is None:
            self._integrity = IntegrityGateChecker(self.engine.paper_dir)
        return self._integrity

    def _find_root(self) -> Path:
        current = Path(__file__).resolve().parent
        for _ in range(10):
            if (current / "AGENTS.md").exists() or (current / "CLAUDE.md").exists():
                return current
            current = current.parent
        return Path.cwd()

    def initialize(self, idea: str, field: str, journal: str = "", timeline_weeks: int = 8) -> WorkflowState:
        strategy = self.strategy_manager.create_strategy(idea=idea, field=field,
                                                         target_journal=journal, timeline_weeks=timeline_weeks)
        self.paper_id = strategy.strategy_id
        self.state = WorkflowState(paper_id=self.paper_id)
        self.state.strategy = strategy
        self.strategy_manager.save_strategy(strategy)
        papers_dir = self.project_root / "papers"
        self._engine = PaperLoopEngine(self.project_root, self.paper_id, papers_dir)
        self._passport = PaperPassport(self.engine.paper_dir)
        self.passport.initialize(idea=idea, field=field, target_journal=journal)
        self.passport.record_checkpoint(stage="select_topic", decision="approved",
                                        notes=f"Workflow initialized. Timeline: {timeline_weeks} weeks.")
        if "select_topic" in self.engine.stages:
            artifacts = self._write_initial_topic_artifacts(strategy, idea, field, journal, timeline_weeks)
            stage = self.engine.stages["select_topic"]
            stage.status = StageStatus.COMPLETED
            stage.completed_at = datetime.now().isoformat()
            stage.execution_mode = "real"
            stage.outputs_verified = True
            stage.artifacts_produced = artifacts
            stage.required_outputs = artifacts
            stage.missing_outputs = []
            stage.gate_results = [{
                "rule": "manual_checkpoint_artifact_set",
                "severity": "critical",
                "passed": True,
                "message": "select_topic approved during workflow initialization with concrete artifacts",
            }]
            self.engine.record_and_sync()
        # Backward compat: if engine uses legacy "create_project" ID
        elif "create_project" in self.engine.stages:
            self.engine.stages["create_project"].status = StageStatus.COMPLETED
            self.engine.stages["create_project"].completed_at = datetime.now().isoformat()
        self.state.pipeline_state = "ready"
        print(f"[PaperWorkflow] Initialized: {self.paper_id}")
        return self.state

    def _write_initial_topic_artifacts(
        self,
        strategy: ResearchStrategy,
        idea: str,
        field: str,
        journal: str,
        timeline_weeks: int,
    ) -> list[str]:
        research_dir = self.engine.paper_dir / "research_plan"
        research_dir.mkdir(parents=True, exist_ok=True)
        topic_path = research_dir / "research_question.md"
        topic_path.write_text(
            "\n".join([
                "# Research Topic",
                "",
                f"Initialized: {datetime.now().isoformat()}",
                f"Field: {field}",
                f"Target journal: {journal or 'auto-selected'}",
                f"Timeline weeks: {timeline_weeks}",
                "",
                "## Research Question",
                "",
                (strategy.topic.research_questions[0] if strategy.topic and strategy.topic.research_questions else idea),
                "",
                "## Scope",
                "",
                idea,
            ]) + "\n",
            encoding="utf-8",
        )
        hypotheses_path = research_dir / "hypotheses.yaml"
        hypotheses_path.write_text(
            yaml.dump({
                "generated_at": datetime.now().isoformat(),
                "source": "workflow_initialize_checkpoint",
                "hypotheses": [
                    {
                        "id": "H1",
                        "statement": (strategy.topic.research_questions[0] if strategy.topic and strategy.topic.research_questions else idea),
                        "status": "author_approved_seed",
                    }
                ],
            }, allow_unicode=True, sort_keys=False),
            encoding="utf-8",
        )
        return ["research_plan/research_question.md", "research_plan/hypotheses.yaml"]

    def run(self, stop_at_checkpoint: bool = True, max_stages: Optional[int] = None) -> WorkflowState:
        stages_run = 0
        if not stop_at_checkpoint:
            self._auto_approve_checkpoint_blockers("PaperWorkflow.run(stop_at_checkpoint=False)")
        stage = self.engine.decide_next_stage()
        while stage:
            if max_stages and stages_run >= max_stages:
                print(f"[PaperWorkflow] Max stages ({max_stages}) reached"); break
            sd = self.engine.stages[stage].definition
            result = self._execute_stage(stage)
            stages_run += 1
            if not result["success"]:
                self.state.errors.append({"stage": stage, "error": result.get("error", ""),
                                          "timestamp": datetime.now().isoformat()})
                self.state.stages_failed += 1
                if result.get("critical"): break
            else:
                self.state.stages_completed += 1
                if sd.human_checkpoint:
                    if stop_at_checkpoint:
                        print(f"\n[PaperWorkflow] CHECKPOINT: {stage} - approve artifacts before continuing")
                        break
                    self.passport.record_checkpoint(
                        stage=stage,
                        decision="approved",
                        notes="Auto-approved by PaperWorkflow.run(stop_at_checkpoint=False)",
                    )
            if self.engine.pipeline_state == PipelineState.BLOCKED: break
            if not stop_at_checkpoint:
                self._auto_approve_checkpoint_blockers("PaperWorkflow.run(stop_at_checkpoint=False)")
            stage = self.engine.decide_next_stage()
        self.engine.record_and_sync()
        self.state.pipeline_state = self.engine.pipeline_state.value
        if self.engine.pipeline_state == PipelineState.CLEAN:
            self.state.completed_at = datetime.now().isoformat()
        print(f"\n[PaperWorkflow] Done: {stages_run} stage(s) | {self.state.stages_completed} ok | {self.state.stages_failed} fail")
        return self.state

    def _auto_approve_checkpoint_blockers(self, notes: str) -> None:
        for blocker in self.engine.checkpoint_blockers():
            self.passport.record_checkpoint(
                stage=blocker["stage"],
                decision="approved",
                notes=notes,
            )

    def _execute_stage(self, stage_name: str) -> dict:
        print(f"\n{'='*50}\n  Executing: {stage_name}\n{'='*50}")
        result = self.engine.run_stage(stage_name)
        if not result["success"]: return result
        verify = self.engine.verify_stage(stage_name)
        for art in result.get("artifacts", []):
            self.passport.record_artifact(art, stage=stage_name)
        self.engine.record_and_sync()
        self.state.decisions.append({"stage": stage_name, "success": verify["all_passed"],
                                     "timestamp": datetime.now().isoformat()})
        return {
            "success": verify["all_passed"],
            "critical": not verify["all_passed"],
            "stage": stage_name,
            "artifacts": result.get("artifacts", []),
            "error": verify.get("error") or verify.get("results", []),
        }

    def diagnose_failures(self) -> dict:
        engine_diag = self.engine.diagnose_failures()
        sections = {}
        for sec in ["abstract", "introduction", "methods", "results", "discussion"]:
            f = self.engine.paper_dir / "manuscript" / f"{sec}.md"
            if f.exists(): sections[sec] = f.read_text(encoding="utf-8")
        bibtex = self.engine.paper_dir / "references" / "library.bib"
        integrity_report = self.integrity.run_all_checks(
            manuscript_sections=sections if sections else None,
            bibtex_path=bibtex if bibtex.exists() else None)
        return {"engine_diagnosis": engine_diag, "integrity_report": integrity_report.to_dict(),
                "integrity_passed": not integrity_report.blocks_pipeline, "total_errors": len(self.state.errors)}

    def get_summary(self) -> str:
        engine_summary = self.engine.get_status_summary()
        ps = self.passport.export_summary()
        lines = [engine_summary, "", f"Artifacts: {ps['total_artifacts']} | Checkpoints: {ps['total_checkpoints']}",
                 f"Completed: {self.state.stages_completed} | Failed: {self.state.stages_failed}"]
        return "\n".join(lines)

    def save_state(self) -> Path:
        d = self.engine.paper_dir / "workflow_state"
        d.mkdir(parents=True, exist_ok=True)
        p = d / f"state_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(p, "w", encoding="utf-8") as f:
            json.dump({"paper_id": self.state.paper_id, "started_at": self.state.started_at,
                       "pipeline_state": self.state.pipeline_state,
                       "stages_completed": self.state.stages_completed,
                       "stages_failed": self.state.stages_failed}, f, indent=2)
        return p


def create_and_run_paper(idea: str, field: str, journal: str = "",
                         project_root: Optional[Path] = None, auto_run: bool = False,
                         max_stages: Optional[int] = None) -> PaperWorkflow:
    wf = PaperWorkflow(project_root=project_root)
    wf.initialize(idea=idea, field=field, journal=journal)
    if auto_run:
        wf.run(stop_at_checkpoint=False, max_stages=max_stages)
    return wf
