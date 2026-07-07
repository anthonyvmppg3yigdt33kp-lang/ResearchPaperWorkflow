"""Programmatic API for the V4 paper workflow.

This layer is the shared service boundary for CLI commands and Python callers.
It keeps project creation, pipeline execution, checkpoint approval, workflow
validation, and agent-harness completion on the same PaperLoopEngine truth
path.
"""
from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Any, Optional

import yaml

from paper_workflow.engine.agent_harness import AgentHarness
from paper_workflow.engine.loop_engine import PaperLoopEngine
from paper_workflow.supervision.integrity import IntegrityGateChecker
from paper_workflow.supervision.passport import PaperPassport
from paper_workflow.workflow import PaperWorkflow


class WorkflowAPI:
    """Stable Python API over the V4 workflow engine and supervision layer."""

    def __init__(self, project_root: Optional[Path] = None):
        self.project_root = Path(project_root) if project_root is not None else self.find_root()

    @staticmethod
    def find_root(start: Optional[Path] = None) -> Path:
        current = Path(start or Path.cwd()).resolve()
        for _ in range(10):
            if (current / "AGENTS.md").exists() or (current / "CLAUDE.md").exists():
                return current
            if current.parent == current:
                break
            current = current.parent
        return Path(start or Path.cwd()).resolve()

    @property
    def papers_dir(self) -> Path:
        path = self.project_root / "papers"
        path.mkdir(parents=True, exist_ok=True)
        return path

    def paper_dir(self, paper_id: str) -> Path:
        return self.papers_dir / paper_id

    def engine(self, paper_id: str) -> PaperLoopEngine:
        return PaperLoopEngine(self.project_root, paper_id, self.papers_dir)

    def create_project(
        self,
        *,
        idea: str,
        field: str,
        journal: str = "",
        timeline_weeks: int = 8,
    ) -> dict[str, Any]:
        workflow = PaperWorkflow(project_root=self.project_root)
        state = workflow.initialize(
            idea=idea,
            field=field,
            journal=journal,
            timeline_weeks=timeline_weeks,
        )
        return {
            "paper_id": workflow.paper_id,
            "paper_dir": str(workflow.engine.paper_dir),
            "journal": journal or "auto-selected",
            "state": state.pipeline_state,
        }

    def status(self, paper_id: str) -> dict[str, Any]:
        engine = self.engine(paper_id)
        passport = PaperPassport(engine.paper_dir)
        drifted = passport.detect_artifact_drift()
        return {
            "paper_id": paper_id,
            "pipeline_state": engine.pipeline_state.value,
            "summary": engine.get_status_summary(),
            "drifted_artifacts": drifted,
        }

    def run_pipeline(
        self,
        paper_id: str,
        *,
        stop_on_failure: bool = False,
        auto_approve_checkpoints: bool = False,
        max_stages: Optional[int] = None,
        stop_after_stage: Optional[str] = None,
    ) -> dict[str, Any]:
        engine = self.engine(paper_id)
        passport = PaperPassport(engine.paper_dir)
        events: list[dict[str, Any]] = []

        self._resolve_checkpoint_blockers(engine, passport, auto_approve_checkpoints, events)
        stage = engine.decide_next_stage()
        if stage is None:
            engine.record_and_sync()
            return self._pipeline_result(engine, events)

        while stage:
            if max_stages is not None and len([e for e in events if e["event"] == "stage"]) >= max_stages:
                events.append({"event": "max_stages_reached", "max_stages": max_stages})
                break

            result = engine.run_stage(stage)
            verify = engine.verify_stage(stage)
            engine.record_and_sync()
            event = {
                "event": "stage",
                "stage": stage,
                "success": bool(result.get("success")) and bool(verify.get("all_passed")),
                "run": result,
                "verify": verify,
            }
            events.append(event)

            if not verify["all_passed"] and stop_on_failure:
                event["stopped_on_failure"] = True
                break

            if verify["all_passed"] and engine.stages[stage].definition.human_checkpoint:
                if auto_approve_checkpoints:
                    passport.record_checkpoint(
                        stage=stage,
                        decision="approved",
                        notes="Auto-approved by WorkflowAPI.run_pipeline(auto_approve_checkpoints=True)",
                    )
                    events.append({"event": "checkpoint_auto_approved", "stage": stage})
                else:
                    engine.record_and_sync()
                    events.append({"event": "checkpoint_required", "stage": stage})
                    break

            if stop_after_stage and stage == stop_after_stage:
                events.append({"event": "stop_after_stage", "stage": stage})
                break

            self._resolve_checkpoint_blockers(engine, passport, auto_approve_checkpoints, events)
            stage = engine.decide_next_stage()

        engine.record_and_sync()
        return self._pipeline_result(engine, events)

    def record_checkpoint(
        self,
        paper_id: str,
        *,
        stage: str,
        decision: str,
        notes: str = "",
    ) -> dict[str, Any]:
        passport = PaperPassport(self.paper_dir(paper_id))
        entry = passport.record_checkpoint(stage=stage, decision=decision, notes=notes)
        return entry.to_dict()

    def validate_workflow(self, paper_id: str) -> dict[str, Any]:
        return self.engine(paper_id).validate_workflow()

    def validate_contract(self) -> dict[str, Any]:
        """Validate global config/contract/engine/dispatcher consistency."""
        issues: list[dict[str, Any]] = []
        config_path = self.project_root / "config" / "default_config.yaml"
        contract_path = self.project_root / "workflow_contract.yaml"

        if not config_path.exists():
            issues.append({
                "code": "missing_config",
                "message": "config/default_config.yaml does not exist",
            })
            return self._contract_result(issues)
        if not contract_path.exists():
            issues.append({
                "code": "missing_workflow_contract",
                "message": "workflow_contract.yaml does not exist",
            })
            return self._contract_result(issues)

        config = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
        contract = yaml.safe_load(contract_path.read_text(encoding="utf-8")) or {}
        config_stages = [stage.get("id", "") for stage in config.get("pipeline", {}).get("stages", [])]
        contract_stages = list((contract.get("stages") or {}).keys())
        quality_gate_defs = set((config.get("quality_gates") or {}).keys())
        agents = set((config.get("agent_routing") or {}).get("agents", {}).keys())
        stage_agents = {stage.get("agent", "") for stage in config.get("pipeline", {}).get("stages", [])}
        legacy_gate_rules = [
            stage.get("id", "")
            for stage in config.get("pipeline", {}).get("stages", [])
            if "gate_rules" in stage
        ]
        ai_harness = config.get("ai_harness", {}) or {}
        ai_routes = ai_harness.get("scenario_routes", {}) or {}
        ai_command_catalog = ai_harness.get("command_catalog", {}) or {}

        with tempfile.TemporaryDirectory() as tmpdir:
            engine = PaperLoopEngine(self.project_root, "__contract_validation__", Path(tmpdir))
            engine_stages = [stage_def.name for stage_def in engine._active_stages]
            gate_refs = sorted({
                gate.get("rule", "")
                for stage_def in engine._active_stages
                for gate in (stage_def.quality_gates or stage_def.gate_rules or [])
            })
            required_output_mismatches = []
            for stage_def in engine._active_stages:
                missing = set(stage_def.required_artifacts or []) - set(stage_def.produces_artifacts or [])
                if missing:
                    required_output_mismatches.append({
                        "stage": stage_def.name,
                        "missing_from_produces": sorted(missing),
                    })

        from paper_workflow.engine.agent_dispatcher import AgentDispatcher

        dispatcher = AgentDispatcher(project_root=self.project_root)
        handlers = sorted(dispatcher._handlers)

        self._append_set_issues(issues, "config_stage_missing_in_contract", set(config_stages) - set(contract_stages))
        self._append_set_issues(issues, "contract_stage_missing_in_config", set(contract_stages) - set(config_stages))
        self._append_set_issues(issues, "config_stage_missing_in_engine", set(config_stages) - set(engine_stages))
        self._append_set_issues(issues, "engine_stage_missing_in_config", set(engine_stages) - set(config_stages))
        self._append_set_issues(issues, "stage_missing_dispatch_handler", set(config_stages) - set(handlers))
        self._append_set_issues(issues, "stage_agent_missing_from_routing", stage_agents - agents - {""})
        self._append_set_issues(issues, "quality_gate_ref_missing_definition", set(gate_refs) - quality_gate_defs)
        self._append_set_issues(issues, "legacy_gate_rules_present", set(legacy_gate_rules))
        self._validate_ai_harness_config(
            issues,
            ai_harness=ai_harness,
            ai_routes=ai_routes,
            ai_command_catalog=ai_command_catalog,
            config_stages=set(config_stages),
        )

        for mismatch in required_output_mismatches:
            issues.append({
                "code": "required_output_not_declared_as_produced",
                "message": "Stage has required outputs not declared in produces artifacts",
                "details": mismatch,
            })

        return {
            "valid": not issues,
            "issue_count": len(issues),
            "issues": issues,
            "counts": {
                "config_stages": len(config_stages),
                "contract_stages": len(contract_stages),
                "engine_stages": len(engine_stages),
                "dispatcher_handlers": len(handlers),
                "agent_routing_entries": len(agents),
                "quality_gate_definitions": len(quality_gate_defs),
                "stage_quality_gate_refs": len(gate_refs),
                "ai_harness_routes": len(ai_routes),
                "ai_harness_commands": len(ai_command_catalog),
            },
            "stage_ids": {
                "config": config_stages,
                "contract": contract_stages,
                "engine": engine_stages,
            },
        }

    def detect_artifact_drift(self, paper_id: str) -> list[dict[str, Any]]:
        return PaperPassport(self.paper_dir(paper_id)).detect_artifact_drift()

    def sync_artifact_stale(self, paper_id: str) -> dict[str, Any]:
        engine = self.engine(paper_id)
        passport = PaperPassport(engine.paper_dir)
        return passport.sync_artifact_stale(engine.artifact_dependency_map())

    def list_harness_invocations(
        self,
        paper_id: str,
        *,
        status: Optional[str] = None,
    ) -> list[dict[str, Any]]:
        return AgentHarness(self.paper_dir(paper_id)).list_invocations(status=status)

    def complete_harness_invocation(
        self,
        paper_id: str,
        *,
        invocation: str,
        notes: str = "",
    ) -> dict[str, Any]:
        return AgentHarness(self.paper_dir(paper_id)).complete_invocation(invocation, notes=notes)

    def run_aigc_humanizer(self, paper_id: str) -> dict[str, Any]:
        engine = self.engine(paper_id)
        stage = "aigc_humanizer_review"
        if stage not in engine.stages:
            return {"success": False, "error": "V4 stage not found: aigc_humanizer_review"}
        missing_upstream = [
            upstream for upstream in engine.stages[stage].definition.upstream
            if engine.stages.get(upstream) is None
            or engine.stages[upstream].status.value != "completed"
        ]
        if missing_upstream:
            return {
                "success": False,
                "error": f"{stage} cannot run before upstream stage(s) complete: {', '.join(missing_upstream)}",
                "missing_upstream": missing_upstream,
            }
        result = engine.run_stage(stage)
        if not result.get("success"):
            return {"success": False, "error": result.get("error", ""), "run": result}
        verify = engine.verify_stage(stage)
        engine.record_and_sync()
        return {
            "success": bool(verify.get("all_passed", False)),
            "stage": stage,
            "artifacts": result.get("artifacts", []),
            "run": result,
            "verify": verify,
        }

    def run_integrity_gate(self, paper_id: str) -> dict[str, Any]:
        paper_dir = self.paper_dir(paper_id)
        sections = {}
        for section in ["abstract", "introduction", "methods", "results", "discussion"]:
            path = paper_dir / "manuscript" / f"{section}.md"
            if path.exists():
                sections[section] = path.read_text(encoding="utf-8")
        bibtex = paper_dir / "references" / "library.bib"
        checker = IntegrityGateChecker(paper_dir)
        report = checker.run_all_checks(
            manuscript_sections=sections if sections else None,
            bibtex_path=bibtex if bibtex.exists() else None,
        )
        integrity_dir = paper_dir / "integrity"
        integrity_dir.mkdir(parents=True, exist_ok=True)
        markdown = checker.generate_markdown_report(report)
        (integrity_dir / "integrity_report.md").write_text(markdown, encoding="utf-8")
        PaperPassport(paper_dir).record_integrity_event("gate_run", report.to_dict())
        return {
            "passed": not report.blocks_pipeline,
            "blocks_pipeline": report.blocks_pipeline,
            "report": report.to_dict(),
            "markdown": markdown,
        }

    def diagnose_gate_failures(self, paper_id: str) -> dict[str, Any]:
        return self.engine(paper_id).diagnose_failures()

    def _contract_result(self, issues: list[dict[str, Any]]) -> dict[str, Any]:
        return {
            "valid": not issues,
            "issue_count": len(issues),
            "issues": issues,
            "counts": {},
            "stage_ids": {},
        }

    @staticmethod
    def _append_set_issues(issues: list[dict[str, Any]], code: str, values: set[str]) -> None:
        for value in sorted(v for v in values if v):
            issues.append({
                "code": code,
                "message": f"{code}: {value}",
                "details": {"value": value},
            })

    @staticmethod
    def _validate_ai_harness_config(
        issues: list[dict[str, Any]],
        *,
        ai_harness: dict[str, Any],
        ai_routes: dict[str, Any],
        ai_command_catalog: dict[str, Any],
        config_stages: set[str],
    ) -> None:
        if not ai_harness:
            issues.append({
                "code": "missing_ai_harness_config",
                "message": "config/default_config.yaml must define ai_harness for Claude/Codex model-facing execution.",
            })
            return
        if not ai_harness.get("enabled", False):
            issues.append({
                "code": "ai_harness_disabled",
                "message": "ai_harness.enabled must be true for model-facing workflow execution.",
            })

        supported_intents = {
            "create_project", "status", "run_pipeline", "validate_contract",
            "validate_workflow", "approve_checkpoint", "list_harness_invocations",
            "complete_harness_invocation", "run_integrity_gate",
            "diagnose_gate_failures", "run_aigc_humanizer", "list_papers",
            "route_task", "doctor",
        }
        supported_cli_commands = {
            "ai", "ai-harness", "create-project", "status", "run-pipeline",
            "checkpoint", "run-integrity-gate", "diagnose-gate-failures",
            "detect-artifact-drift", "sync-artifact-stale", "validate-workflow",
            "validate-contract", "list-harness-invocations",
            "complete-harness-invocation", "list-papers", "strategy",
            "install-skills", "run-aigc-humanizer", "route-task", "doctor",
        }
        required_top_level = {"command_entrypoint", "default_max_stages_per_turn", "command_catalog", "scenario_routes"}
        for key in sorted(required_top_level - set(ai_harness)):
            issues.append({
                "code": "ai_harness_missing_required_key",
                "message": f"ai_harness missing required key: {key}",
                "details": {"key": key},
            })

        for intent, spec in sorted(ai_command_catalog.items()):
            if intent not in supported_intents:
                issues.append({
                    "code": "ai_harness_unsupported_intent",
                    "message": f"AI harness command catalog references unsupported intent: {intent}",
                    "details": {"intent": intent},
                })
            command = (spec or {}).get("cli_command") or (spec or {}).get("command")
            if command and command not in supported_cli_commands:
                issues.append({
                    "code": "ai_harness_unknown_cli_command",
                    "message": f"AI harness command catalog references unknown CLI command: {command}",
                    "details": {"intent": intent, "cli_command": command},
                })

        for route_name, route in sorted(ai_routes.items()):
            if not isinstance(route, dict):
                issues.append({
                    "code": "ai_harness_invalid_route",
                    "message": f"AI harness scenario route must be an object: {route_name}",
                    "details": {"route": route_name},
                })
                continue
            intent = route.get("intent")
            if intent and intent not in supported_intents:
                issues.append({
                    "code": "ai_harness_route_unsupported_intent",
                    "message": f"AI harness scenario route references unsupported intent: {route_name} -> {intent}",
                    "details": {"route": route_name, "intent": intent},
                })
            stage_refs = set()
            for key in ("target_stage", "stop_after_stage"):
                value = route.get(key)
                if value:
                    stage_refs.add(str(value))
            for key in ("stages", "target_stages", "allowed_start_stages"):
                for value in route.get(key, []) or []:
                    stage_refs.add(str(value))
            for stage in sorted(stage_refs - config_stages):
                issues.append({
                    "code": "ai_harness_route_unknown_stage",
                    "message": f"AI harness scenario route references unknown stage: {route_name} -> {stage}",
                    "details": {"route": route_name, "stage": stage},
                })

    def _resolve_checkpoint_blockers(
        self,
        engine: PaperLoopEngine,
        passport: PaperPassport,
        auto_approve: bool,
        events: list[dict[str, Any]],
    ) -> None:
        blockers = engine.checkpoint_blockers()
        if not blockers:
            return
        if not auto_approve:
            events.append({"event": "checkpoint_blockers", "blockers": blockers})
            return
        for blocker in blockers:
            passport.record_checkpoint(
                stage=blocker["stage"],
                decision="approved",
                notes="Auto-approved by WorkflowAPI.run_pipeline(auto_approve_checkpoints=True)",
            )
            events.append({"event": "checkpoint_auto_approved", "stage": blocker["stage"]})

    def _pipeline_result(self, engine: PaperLoopEngine, events: list[dict[str, Any]]) -> dict[str, Any]:
        return {
            "paper_id": engine.paper_id,
            "paper_dir": str(engine.paper_dir),
            "pipeline_state": engine.pipeline_state.value,
            "events": events,
            "checkpoint_blockers": engine.checkpoint_blockers(),
        }
