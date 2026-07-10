"""Model-facing natural-language harness for Claude/Codex integration.

The harness is intentionally thin: it routes a user's natural-language request
to the existing WorkflowAPI and records which command a model executed. It does
not replace v5 TargetTask gates, stage verification, quality gates, or human
checkpoints.
"""
from __future__ import annotations

import contextlib
import io
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

import yaml

from paper_workflow.analysis import AnalysisDesign, run_analysis_adapter
from paper_workflow.api import WorkflowAPI
from paper_workflow.bioinformatics.module_registry import ModuleRegistry
from paper_workflow.bioinformatics.module_selector import MethodSelector
from paper_workflow.outputs.result_run_manager import ResultRunManager
from paper_workflow.research_intent import ResearchWorkflowOrchestrator
from paper_workflow.routing.mode_resolver import ModeResolver
from paper_workflow.routing.tool_doctor import ToolDoctor
from paper_workflow.target_task import TargetTaskOrchestrator


class AIWorkflowHarness:
    """Route natural-language user requests to workflow commands for AI agents."""

    SCHEMA_VERSION = "ai_harness.v1"
    DEFAULT_MAX_STAGES_PER_TURN = 1
    SUPPORTED_INTENTS = {
        "create_project",
        "status",
        "run_pipeline",
        "validate_contract",
        "validate_workflow",
        "approve_checkpoint",
        "list_harness_invocations",
        "complete_harness_invocation",
        "run_integrity_gate",
        "diagnose_gate_failures",
        "run_aigc_humanizer",
        "list_papers",
        "route_task",
        "doctor",
        "list_capabilities",
        "list_modules",
        "inspect_module",
        "plan_analysis",
        "run_analysis",
        "evaluate_run",
        "target_task",
        "research_intent",
    }

    INTENT_COMMANDS = {
        "create_project": "create-project",
        "status": "status",
        "run_pipeline": "run-pipeline",
        "validate_contract": "validate-contract",
        "validate_workflow": "validate-workflow",
        "approve_checkpoint": "checkpoint",
        "list_harness_invocations": "list-harness-invocations",
        "complete_harness_invocation": "complete-harness-invocation",
        "run_integrity_gate": "run-integrity-gate",
        "diagnose_gate_failures": "diagnose-gate-failures",
        "run_aigc_humanizer": "run-aigc-humanizer",
        "list_papers": "list-papers",
        "route_task": "route-task",
        "doctor": "doctor",
        "list_capabilities": "list-capabilities",
        "list_modules": "list-modules",
        "inspect_module": "inspect-module",
        "plan_analysis": "plan-analysis",
        "run_analysis": "run-analysis",
        "evaluate_run": "evaluate-run",
        "target_task": "target",
        "research_intent": "research",
    }

    STAGE_IDS = (
        "select_topic",
        "target_journal",
        "literature_search",
        "formulate_hypotheses",
        "design_analysis_plan",
        "data_audit",
        "figure_planning",
        "run_analysis",
        "verify_methods",
        "write_methods",
        "write_results",
        "write_introduction",
        "write_discussion",
        "assemble_manuscript",
        "aigc_humanizer_review",
        "integrity_check",
        "internal_review",
        "apply_revision",
        "re_review",
        "finalize",
    )

    STAGE_ALIASES = {
        "选题": "select_topic",
        "主题": "select_topic",
        "方向": "select_topic",
        "期刊": "target_journal",
        "投稿": "target_journal",
        "文献": "literature_search",
        "调研": "literature_search",
        "假设": "formulate_hypotheses",
        "研究假设": "formulate_hypotheses",
        "sap": "design_analysis_plan",
        "统计分析计划": "design_analysis_plan",
        "分析计划": "design_analysis_plan",
        "数据审计": "data_audit",
        "数据检查": "data_audit",
        "图表": "figure_planning",
        "figure": "figure_planning",
        "分析": "run_analysis",
        "方法验证": "verify_methods",
        "方法": "write_methods",
        "结果": "write_results",
        "引言": "write_introduction",
        "讨论": "write_discussion",
        "组稿": "assemble_manuscript",
        "全文": "assemble_manuscript",
        "aigc": "aigc_humanizer_review",
        "去ai": "aigc_humanizer_review",
        "完整性": "integrity_check",
        "质控": "integrity_check",
        "内审": "internal_review",
        "审稿": "internal_review",
        "修订": "apply_revision",
        "复审": "re_review",
        "定稿": "finalize",
        "最终": "finalize",
    }

    FIELD_HINTS = (
        (("单细胞", "single-cell", "scrna", "scRNA"), "single-cell"),
        (("空间", "spatial"), "spatial transcriptomics"),
        (("临床", "患者", "队列", "病人", "病例"), "clinical research"),
        (("生信", "bioinformatics", "转录组", "基因", "omics"), "bioinformatics"),
        (("医学", "疾病", "肿瘤", "癌"), "biomedical research"),
    )

    def __init__(self, project_root: Optional[Path] = None):
        self.api = WorkflowAPI(project_root)
        self.project_root = self.api.project_root
        self.config = self._load_config()
        self.harness_config = self.config.get("ai_harness", {}) or {}
        self.mode_resolver = ModeResolver(self.project_root)

    def handle_request(
        self,
        request: str,
        *,
        paper_id: Optional[str] = None,
        field: Optional[str] = None,
        journal: Optional[str] = None,
        timeline_weeks: Optional[int] = None,
        max_stages: Optional[int] = None,
        stop_on_failure: bool = True,
        auto_approve_checkpoints: bool = False,
        dry_run: bool = False,
        invocation: Optional[str] = None,
        stage: Optional[str] = None,
        decision: str = "approved",
        notes: str = "",
    ) -> dict[str, Any]:
        """Classify and optionally execute one model-facing workflow request."""
        request = (request or "").strip()
        paper_id = self._extract_paper_id(request) or paper_id
        resolved_paper = self._resolve_paper_id(paper_id)
        route = self.mode_resolver.resolve_route(
            request,
            paper_id=resolved_paper.get("paper_id") or paper_id,
            explicit_journal=journal,
        )
        intent = self.classify_request(request, paper_id=resolved_paper.get("paper_id"))
        intent = self._apply_route_guard(intent, request=request, route=route, resolved_paper=resolved_paper)
        route = self._method_asset_route(intent, route, request=request)
        timeline_weeks = timeline_weeks or self._infer_timeline(request) or 8
        max_stages = (
            max_stages
            if max_stages is not None
            else int(self.harness_config.get("default_max_stages_per_turn", self.DEFAULT_MAX_STAGES_PER_TURN))
        )

        plan = self._build_plan(
            intent=intent,
            request=request,
            paper_id=resolved_paper.get("paper_id"),
            field=field or self._infer_field(request),
            journal=journal or self._infer_journal(request),
            timeline_weeks=timeline_weeks,
            max_stages=max_stages,
            stop_on_failure=stop_on_failure,
            auto_approve_checkpoints=auto_approve_checkpoints,
            invocation=invocation,
            stage=stage or self._infer_stage(request),
            decision=decision,
            notes=notes,
            route=route,
        )

        payload = {
            "schema_version": self.SCHEMA_VERSION,
            "generated_at": datetime.now().isoformat(),
            "project_root": str(self.project_root),
            "request": request,
            "intent": intent,
            "route": route,
            "paper_resolution": resolved_paper,
            "plan": plan,
            "dry_run": dry_run,
            "executed": False,
            "status": "planned" if dry_run else "pending",
            "result": None,
            "next_model_actions": [],
            "user_facing_reply": "",
        }
        guard = self._method_asset_guard(intent, request, resolved_paper)
        if guard:
            payload.update(guard)
            return payload
        if dry_run:
            payload["next_model_actions"] = self._next_actions_for_plan(intent, resolved_paper)
            payload["user_facing_reply"] = self._planned_reply(payload)
            return payload

        paperless_intents = {
            "create_project",
            "list_papers",
            "validate_contract",
            "route_task",
            "doctor",
            "list_capabilities",
            "list_modules",
            "inspect_module",
            "target_task",
            "research_intent",
        }
        if intent not in paperless_intents and not resolved_paper.get("paper_id"):
            payload["status"] = "needs_input"
            payload["result"] = {
                "message": "A paper_id is required, or exactly one existing paper project must be present.",
                "available_papers": resolved_paper.get("candidates", []),
            }
            payload["next_model_actions"] = [
                "Ask the user which paper project to operate on.",
                "If this is a new project, rerun the harness with a create/start request.",
            ]
            payload["user_facing_reply"] = "我需要先确认要操作哪个 paper_id；如果是新课题，我会先创建项目。"
            return payload

        try:
            result = self._execute(
                intent=intent,
                request=request,
                paper_id=resolved_paper.get("paper_id"),
                field=field or self._infer_field(request),
                journal=journal or self._infer_journal(request),
                timeline_weeks=timeline_weeks,
                max_stages=max_stages,
                stop_on_failure=stop_on_failure,
                auto_approve_checkpoints=auto_approve_checkpoints,
                invocation=invocation,
                stage=stage or self._infer_stage(request),
                decision=decision,
                notes=notes,
                route=route,
            )
            payload["executed"] = True
            payload["status"] = self._result_status(intent, result)
            payload["result"] = result
            payload["next_model_actions"] = self._next_actions(intent, result)
            payload["user_facing_reply"] = self._executed_reply(intent, result)
            return payload
        except Exception as exc:  # pragma: no cover - exercised through CLI strict behavior
            payload["status"] = "error"
            payload["result"] = {
                "error_type": type(exc).__name__,
                "error": str(exc),
            }
            payload["next_model_actions"] = [
                "Report the error to the user with the command that failed.",
                "Run validate-contract --strict if the failure looks like wiring or config drift.",
            ]
            payload["user_facing_reply"] = f"工作流执行失败：{type(exc).__name__}: {exc}"
            return payload

    def classify_request(self, request: str, *, paper_id: Optional[str] = None) -> str:
        text = request.lower()
        compact = re.sub(r"\s+", "", request.lower())

        if self._has_any(
            text,
            compact,
            (
                "research intent",
                "research start",
                "research analyze",
                "research review",
                "research write",
                "research package",
                "research status",
                "科研意图",
                "科研启动",
                "科研分析",
                "科研复核",
                "科研写作",
                "科研打包",
                "科研状态",
            ),
        ):
            return "research_intent"
        if self._has_any(
            text,
            compact,
            (
                "target task",
                "target-task",
                "target validate",
                "target plan",
                "target run",
                "target evaluate",
                "target package",
                "目标任务",
                "目标校验",
                "目标规划",
                "目标执行",
                "目标评价",
                "目标打包",
            ),
        ):
            return "target_task"
        if self._has_any(text, compact, ("route task", "route-task", "resolve mode", "mode/profile", "模式路由", "模式匹配")):
            return "route_task"
        if self._has_any(text, compact, ("doctor", "tool check", "fast-context", "fast_context", "skill check", "agent check", "工具不可用", "工具检查")):
            return "doctor"
        if self._has_any(
            text,
            compact,
            (
                "list capabilities",
                "list-capabilities",
                "available analysis",
                "available capabilities",
                "what analyses",
                "有哪些分析可用",
                "可用分析",
                "能力清单",
                "列出能力",
            ),
        ):
            return "list_capabilities"
        if self._has_any(
            text,
            compact,
            (
                "list modules",
                "list-modules",
                "method modules",
                "module registry",
                "方法模块",
                "列出模块",
                "模块清单",
                "代码资产清单",
            ),
        ):
            return "list_modules"
        if self._has_any(
            text,
            compact,
            (
                "inspect module",
                "inspect-module",
                "module detail",
                "查看模块",
                "检查模块",
                "模块详情",
            ),
        ):
            return "inspect_module"
        if self._has_any(
            text,
            compact,
            (
                "plan-analysis",
                "plan analysis",
                "from code library",
                "code library",
                "code_library",
                "根据代码库规划",
                "从codelibrary选择",
                "从 code library 选择",
                "规划单细胞分析",
                "规划分析",
                "分析方案",
                "不要执行",
            ),
        ):
            return "plan_analysis"
        if self._has_any(
            text,
            compact,
            (
                "evaluate-run",
                "evaluate run",
                "run qa",
                "run quality",
                "评估这个 run",
                "评估run",
                "评估这个分析",
                "审核run",
            ),
        ):
            return "evaluate_run"
        if self._has_any(
            text,
            compact,
            (
                "run-analysis",
                "run analysis",
                "execute analysis graph",
                "execute this analysis",
                "执行分析图",
                "执行这个分析",
                "运行这个分析",
                "执行分析",
                "运行分析",
            ),
        ):
            return "run_analysis"

        if self._has_any(text, compact, ("列出项目", "有哪些项目", "list papers")):
            return "list_papers"
        if self._has_any(text, compact, ("静态", "validate contract", "contract", "配置检查", "全局检查")):
            return "validate_workflow" if paper_id and self._has_any(text, compact, ("项目", "workflow", "状态")) else "validate_contract"
        if self._has_any(text, compact, ("validate workflow", "工作流检查", "项目检查", "体检")):
            return "validate_workflow"
        if self._has_any(text, compact, ("状态", "进度", "status", "现在到哪", "到哪一步")):
            return "status"
        if self._has_any(text, compact, ("完成harness", "complete harness", "回填", "验证产物", "完成待办")):
            return "complete_harness_invocation"
        if self._has_any(text, compact, ("pending", "待办", "缺什么", "harness", "需要补什么")):
            return "list_harness_invocations"
        if self._has_any(text, compact, ("批准", "approve", "检查点", "checkpoint")):
            return "approve_checkpoint"
        if self._has_any(text, compact, ("aigc", "去ai", "humanizer", "ai痕迹")):
            return "run_aigc_humanizer"
        if self._has_any(text, compact, ("完整性", "integrity", "质量门", "gate")):
            return "run_integrity_gate"
        if self._has_any(text, compact, ("诊断", "失败原因", "diagnose", "为什么失败")):
            return "diagnose_gate_failures"
        if self._has_any(
            text,
            compact,
            (
                "新建", "创建", "尚未起步", "还没起步", "没有起步", "没起步", "从零开始",
                "start a new", "create project", "not started", "have not started", "haven't started",
            ),
        ):
            return "create_project"
        if paper_id and self._has_any(
            text,
            compact,
            (
                "已有部分", "部分进展", "接入工作流", "检查缺口", "完善工作流", "散乱材料",
                "partial progress", "workflow design", "integrate materials", "check gaps",
                "scattered materials",
            ),
        ):
            return "validate_workflow"
        if paper_id and self._has_any(
            text,
            compact,
            (
                "选题调研", "文献空白", "已有方向", "已有选题", "数据分析", "数据审计",
                "图表规划", "论文撰写", "写作", "投稿包", "多数材料", "进入sap",
                "have a direction", "topic research", "literature gap", "literature gaps",
                "have a topic", "data analysis", "data audit", "figure planning",
                "manuscript writing", "write the paper", "submission package",
                "most materials",
            ),
        ):
            return "run_pipeline"
        if not paper_id and self._has_any(text, compact, ("选题", "方向", "课题", "研究", "proposal")):
            return "create_project"
        if self._has_any(text, compact, ("继续", "推进", "运行", "执行", "下一步", "run pipeline", "workflow")):
            return "run_pipeline"
        return "status" if paper_id else "create_project"

    def _execute(
        self,
        *,
        intent: str,
        request: str,
        paper_id: Optional[str],
        field: str,
        journal: str,
        timeline_weeks: int,
        max_stages: int,
        stop_on_failure: bool,
        auto_approve_checkpoints: bool,
        invocation: Optional[str],
        stage: Optional[str],
        decision: str,
        notes: str,
        route: dict[str, Any],
    ) -> Any:
        if intent == "route_task":
            return route
        if intent == "doctor":
            return ToolDoctor(self.project_root).run()
        if intent == "target_task":
            target_path = self._resolve_target_path(self._extract_target_path(request, notes=notes) or "")
            subcommand = self._infer_target_subcommand(request)
            orchestrator = TargetTaskOrchestrator(self.project_root)
            if subcommand == "validate":
                return orchestrator.validate(target_path, require_packages=self._target_package_check_requested(request))
            if subcommand == "plan":
                return orchestrator.plan(target_path)
            if subcommand == "run":
                return orchestrator.run(
                    target_path,
                    approved=self._has_approval_phrase(request),
                    execute=self._target_execute_requested(request),
                )
            if subcommand == "evaluate":
                return orchestrator.evaluate(target_path, fail_closed=True)
            if subcommand == "package":
                return orchestrator.package(target_path)
            raise ValueError(f"Unsupported TargetTask subcommand: {subcommand}")
        if intent == "research_intent":
            intent_path = self._resolve_target_path(self._extract_research_intent_path(request, notes=notes) or "")
            subcommand = self._infer_research_subcommand(request)
            orchestrator = ResearchWorkflowOrchestrator(self.project_root)
            if subcommand == "validate":
                return orchestrator.validate(intent_path)
            if subcommand == "start":
                return orchestrator.start(intent_path)
            if subcommand == "analyze":
                return orchestrator.analyze(
                    intent_path,
                    approved=self._has_approval_phrase(request),
                    execute=self._target_execute_requested(request),
                )
            if subcommand == "review":
                return orchestrator.review(intent_path)
            if subcommand == "write":
                return orchestrator.write(intent_path)
            if subcommand == "package":
                return orchestrator.package(intent_path)
            if subcommand == "status":
                return orchestrator.status(intent_path)
            raise ValueError(f"Unsupported research subcommand: {subcommand}")
        if intent == "list_capabilities":
            modality = self._infer_modality(request)
            paper_dir = self.api.papers_dir / paper_id if paper_id else None
            selected = MethodSelector(self.project_root, paper_dir=paper_dir).select(
                goal=request,
                modalities=[modality],
                max_modules=6,
            )
            return {
                "question": request,
                "modalities": [modality],
                "selected_modules": selected,
            }
        if intent == "list_modules":
            modality = self._infer_modality(request)
            registry = ModuleRegistry(self.project_root)
            return {
                "modality": modality,
                "summary": registry.capability_summary(),
                "modules": registry.list_modules(modality=modality),
            }
        if intent == "inspect_module":
            module_id = self._extract_module_id(request, notes=notes)
            if not module_id:
                return {
                    "status": "needs_input",
                    "message": "A module_id is required to inspect a method asset.",
                }
            registry = ModuleRegistry(self.project_root)
            module = registry.get(module_id)
            if not module:
                return {
                    "status": "needs_input",
                    "message": f"Module not found: {module_id}",
                    "available_modules": [m.get("id") or m.get("module_id") for m in registry.list_modules()],
                }
            return {
                "module_id": module_id,
                "module": module,
                "issues": registry.validate_module(module_id),
            }
        if intent == "create_project":
            with contextlib.redirect_stdout(io.StringIO()):
                return self.api.create_project(
                    idea=request,
                    field=field,
                    journal=journal,
                    timeline_weeks=timeline_weeks,
                )
        if intent == "status":
            return self.api.status(paper_id or "")
        if intent == "run_pipeline":
            return self.api.run_pipeline(
                paper_id or "",
                stop_on_failure=stop_on_failure,
                auto_approve_checkpoints=auto_approve_checkpoints,
                max_stages=max_stages,
            )
        if intent == "validate_contract":
            return self.api.validate_contract()
        if intent == "validate_workflow":
            return self.api.validate_workflow(paper_id or "")
        if intent == "approve_checkpoint":
            checkpoint_stage = stage or self._first_checkpoint_blocker(paper_id or "")
            if not checkpoint_stage:
                return {
                    "status": "needs_input",
                    "message": "No checkpoint stage was specified or detected.",
                }
            return self.api.record_checkpoint(
                paper_id or "",
                stage=checkpoint_stage,
                decision=decision,
                notes=notes or "Approved through AIWorkflowHarness after user natural-language approval.",
            )
        if intent == "list_harness_invocations":
            return self.api.list_harness_invocations(paper_id or "")
        if intent == "complete_harness_invocation":
            target = invocation or stage or self._single_pending_invocation(paper_id or "")
            if not target:
                return {
                    "status": "needs_input",
                    "message": "No harness invocation was specified and there is not exactly one pending invocation.",
                }
            return self.api.complete_harness_invocation(
                paper_id or "",
                invocation=target,
                notes=notes or "Checked through AIWorkflowHarness.",
            )
        if intent == "run_integrity_gate":
            return self.api.run_integrity_gate(paper_id or "")
        if intent == "diagnose_gate_failures":
            return self.api.diagnose_gate_failures(paper_id or "")
        if intent == "run_aigc_humanizer":
            return self.api.run_aigc_humanizer(paper_id or "")
        if intent == "list_papers":
            return {"papers": self._paper_candidates()}
        if intent == "plan_analysis":
            run_id = self._extract_run_id(request) or self._default_run_id("method_asset")
            paper_dir = self.api.papers_dir / (paper_id or "")
            manager = ResultRunManager(paper_dir)
            if not manager.run_path(run_id).exists():
                manager.create_run(
                    run_id=run_id,
                    mode="analysis_design_mode",
                    status="prepared",
                    notes=notes or "Prepared through AIWorkflowHarness method-asset planning.",
                )
            design = manager.write_analysis_design(
                run_id=run_id,
                goal=request,
                modality=self._infer_modality(request),
                inputs=self._extract_inputs(request),
                primary_contrast="requires_human_input",
                execution_backend="dry_run",
                from_code_library=True,
            )
            manager.set_current_run(
                run_id=run_id,
                status="prepared",
                user_approved=False,
                notes="analysis design prepared through AIWorkflowHarness; execution not approved",
            )
            return {
                "run_id": run_id,
                "run_dir": str(manager.run_path(run_id)),
                "analysis_design": design,
                "analysis_design_path": str(manager.run_path(run_id) / "analysis_design.yaml"),
                "analysis_graph_path": str(manager.run_path(run_id) / "analysis_graph.yaml"),
                "method_selection_report": str(manager.run_path(run_id) / "method_selection_report.md"),
            }
        if intent == "run_analysis":
            run_id = self._extract_run_id(request)
            paper_dir = self.api.papers_dir / (paper_id or "")
            manager = ResultRunManager(paper_dir)
            run_dir = manager.run_path(run_id or "")
            design = AnalysisDesign.from_file(run_dir / "analysis_design.yaml")
            design.user_approval = True
            result = run_analysis_adapter(design, run_dir, execute=True)
            evaluation = manager.evaluate_run(run_id or "", write_report=True)
            manager.set_current_run(
                run_id=run_id or "",
                status="exploratory",
                user_approved=True,
                notes=f"run-analysis adapter status: {result.status}",
            )
            return {"adapter_result": result.to_dict(), "evaluation": evaluation.to_dict()}
        if intent == "evaluate_run":
            run_id = self._extract_run_id(request)
            if not run_id:
                return {
                    "status": "needs_input",
                    "message": "A run_id is required to evaluate a result run.",
                }
            manager = ResultRunManager(self.api.papers_dir / (paper_id or ""))
            return manager.evaluate_run(run_id, write_report=True).to_dict()
        raise ValueError(f"Unsupported AI harness intent: {intent}")

    def _build_plan(self, **kwargs: Any) -> dict[str, Any]:
        intent = kwargs["intent"]
        command = self.INTENT_COMMANDS.get(intent, intent)
        args: list[str] = []
        if intent == "create_project":
            args.extend(["--idea", kwargs["request"], "--field", kwargs["field"]])
            if kwargs["journal"]:
                args.extend(["--journal", kwargs["journal"]])
            args.extend(["--timeline", str(kwargs["timeline_weeks"])])
        elif intent == "run_pipeline":
            args.extend(["--paper", kwargs["paper_id"] or "<paper_id>"])
            args.extend(["--max-stages", str(kwargs["max_stages"])])
            if kwargs["stop_on_failure"]:
                args.append("--stop-on-failure")
            if kwargs["auto_approve_checkpoints"]:
                args.append("--auto-approve-checkpoints")
        elif intent == "approve_checkpoint":
            args.extend(["--paper", kwargs["paper_id"] or "<paper_id>"])
            args.extend(["--stage", kwargs["stage"] or "<stage>"])
            args.extend(["--decision", kwargs["decision"]])
            if kwargs["notes"]:
                args.extend(["--notes", kwargs["notes"]])
        elif intent in {
            "status",
            "validate_workflow",
            "list_harness_invocations",
            "run_integrity_gate",
            "diagnose_gate_failures",
            "run_aigc_humanizer",
        }:
            args.extend(["--paper", kwargs["paper_id"] or "<paper_id>"])
        elif intent == "route_task":
            args.extend(["--request", kwargs["request"], "--json"])
        elif intent == "doctor":
            args.append("--json")
        elif intent == "list_capabilities":
            args.extend(["--question", kwargs["request"], "--modality", self._infer_modality(kwargs["request"]), "--json"])
            if kwargs["paper_id"]:
                args.extend(["--paper", kwargs["paper_id"]])
        elif intent == "list_modules":
            args.extend(["--modality", self._infer_modality(kwargs["request"]), "--json"])
        elif intent == "inspect_module":
            args.extend([self._extract_module_id(kwargs["request"], notes=kwargs.get("notes", "")) or "<module_id>", "--json"])
        elif intent == "plan_analysis":
            args.extend([
                "--paper", kwargs["paper_id"] or "<paper_id>",
                "--run-id", self._extract_run_id(kwargs["request"]) or self._default_run_id("method_asset"),
                "--goal", kwargs["request"],
                "--modality", self._infer_modality(kwargs["request"]),
                "--from-code-library",
                "--set-current",
                "--json",
            ])
        elif intent == "run_analysis":
            args.extend([
                "--paper", kwargs["paper_id"] or "<paper_id>",
                "--run-id", self._extract_run_id(kwargs["request"]) or "<run_id>",
                "--execute",
            ])
            if self._has_approval_phrase(kwargs["request"]):
                args.append("--approved")
            args.extend(["--set-current", "--json"])
        elif intent == "evaluate_run":
            args.extend([
                "--paper", kwargs["paper_id"] or "<paper_id>",
                "--run-id", self._extract_run_id(kwargs["request"]) or "<run_id>",
                "--write-report",
                "--json",
            ])
        elif intent == "target_task":
            subcommand = self._infer_target_subcommand(kwargs["request"])
            target_path = self._extract_target_path(kwargs["request"], notes=kwargs.get("notes", "")) or "<target.yaml>"
            args.extend([subcommand, "--target", target_path])
            if subcommand == "validate" and self._target_package_check_requested(kwargs["request"]):
                args.append("--require-packages")
            if subcommand == "run":
                if self._target_execute_requested(kwargs["request"]):
                    args.append("--execute")
                if self._has_approval_phrase(kwargs["request"]):
                    args.append("--approved")
            if subcommand == "evaluate":
                args.append("--fail-closed")
            args.append("--json")
        elif intent == "research_intent":
            subcommand = self._infer_research_subcommand(kwargs["request"])
            intent_path = self._extract_research_intent_path(kwargs["request"], notes=kwargs.get("notes", "")) or "<research_intent.yaml>"
            args.extend([subcommand, "--intent", intent_path])
            if subcommand == "analyze":
                if self._target_execute_requested(kwargs["request"]):
                    args.append("--execute")
                if self._has_approval_phrase(kwargs["request"]):
                    args.append("--approved")
            args.append("--json")
        elif intent == "complete_harness_invocation":
            args.extend(["--paper", kwargs["paper_id"] or "<paper_id>"])
            args.extend(["--invocation", kwargs["invocation"] or kwargs["stage"] or "<invocation>"])
        equivalent = self._format_command(command, args)
        harness_args = ["--request", kwargs["request"], "--json"]
        if kwargs.get("paper_id"):
            harness_args.extend(["--paper", kwargs["paper_id"]])
        if kwargs.get("max_stages") is not None and intent == "run_pipeline":
            harness_args.extend(["--max-stages", str(kwargs["max_stages"])])
        harness = self._format_command("ai", harness_args)
        return {
            "intent": intent,
            "equivalent_cli_command": equivalent,
            "model_harness_command": harness,
            "route": kwargs.get("route") or {},
            "stop_policy": {
                "max_stages_per_turn": kwargs["max_stages"],
                "stop_on_failure": kwargs["stop_on_failure"],
                "auto_approve_checkpoints": kwargs["auto_approve_checkpoints"],
            },
        }

    def _result_status(self, intent: str, result: Any) -> str:
        if isinstance(result, dict):
            if result.get("status") == "needs_input":
                return "needs_input"
            if intent in {"validate_contract", "validate_workflow"}:
                return "ok" if result.get("valid") else "failed"
            if intent == "run_pipeline":
                if any(event.get("event") == "checkpoint_required" for event in result.get("events", [])):
                    return "checkpoint_required"
                blockers = result.get("checkpoint_blockers") or []
                if blockers:
                    return "checkpoint_required"
                state = result.get("pipeline_state")
                if state in {"blocked", "gate_failure", "stale_stages"}:
                    return state
            if intent == "run_integrity_gate" and result.get("blocks_pipeline"):
                return "blocked"
            if intent == "run_aigc_humanizer" and not result.get("success", False):
                return "blocked"
            if intent == "doctor" and result.get("status") == "fail":
                return "failed"
            if intent == "doctor" and result.get("status") == "degraded":
                return "ok"
            if intent == "run_analysis":
                adapter = result.get("adapter_result") or {}
                if adapter.get("status") in {"blocked", "failed", "error"}:
                    return "blocked"
                evaluation = result.get("evaluation") or {}
                return "ok" if evaluation.get("status") in {"pass", "degraded_exploratory"} else str(evaluation.get("status", "ok"))
            if intent == "evaluate_run":
                return "ok" if result.get("status") in {"pass", "degraded_exploratory"} else str(result.get("status", "ok"))
            if intent == "target_task":
                if result.get("valid") is False:
                    return "failed"
                status = result.get("status") or result.get("final_status") or result.get("environment_status")
                if status in {"blocked", "needs_fix", "failed", "error"}:
                    return str(status)
                return "ok"
            if intent == "research_intent":
                if result.get("valid") is False:
                    return "failed"
                status = result.get("status")
                if status in {"blocked", "needs_fix", "needs_input", "failed", "error"}:
                    return str(status)
                return "ok"
        return "ok"

    def _next_actions(self, intent: str, result: Any) -> list[str]:
        if intent == "create_project" and isinstance(result, dict):
            return [
                f"Run status for paper_id={result.get('paper_id')}.",
                "Run the AI harness again with a request to continue one stage.",
            ]
        if intent == "run_pipeline" and isinstance(result, dict):
            actions = []
            for event in result.get("events", []):
                if event.get("event") == "checkpoint_required":
                    actions.append(f"Ask the user to approve checkpoint stage {event.get('stage')}.")
                if event.get("stopped_on_failure"):
                    actions.append("Inspect pending harness invocations and workflow validation before rerunning.")
            if result.get("checkpoint_blockers"):
                actions.append("Ask for human checkpoint approval before continuing.")
            return actions or ["Run status and validate-workflow before the next turn."]
        if intent in {"validate_contract", "validate_workflow"} and isinstance(result, dict):
            return ["Fix reported issues before running pipeline."] if not result.get("valid") else ["Proceed with one workflow step."]
        if intent == "list_harness_invocations":
            return ["Complete the pending external task, then run complete-harness-invocation and rerun pipeline."]
        if intent == "route_task":
            return ["Use the returned mode/profile packet before selecting any workflow command."]
        if intent == "doctor":
            return ["Repair required failures first; use listed fallbacks for degraded optional tools."]
        if intent == "plan_analysis":
            return ["Review the analysis design and ask for explicit user approval before run-analysis --execute."]
        if intent == "run_analysis":
            return ["Evaluate the run report and inspect source maps before treating outputs as evidence."]
        if intent == "evaluate_run":
            return ["Fix blocked or missing run artifacts before promoting any manuscript claim."]
        if intent == "target_task":
            return ["Use the TargetTask status and fail-closed report to choose the next approved action."]
        if intent == "research_intent":
            return ["Review the scientific assessment, alternatives, figure plan, and dashboard before approving real execution."]
        if intent in {"list_capabilities", "list_modules", "inspect_module"}:
            return ["Select a compatible method asset, then create an analysis design before execution."]
        return ["Report the result to the user and ask for approval if a checkpoint is required."]

    def _next_actions_for_plan(self, intent: str, resolved_paper: dict[str, Any]) -> list[str]:
        paperless_intents = {
            "create_project",
            "list_papers",
            "validate_contract",
            "route_task",
            "doctor",
            "list_capabilities",
            "list_modules",
            "inspect_module",
            "target_task",
            "research_intent",
        }
        if intent not in paperless_intents and not resolved_paper.get("paper_id"):
            return ["Ask the user for the paper_id or create a new project first."]
        if intent == "run_analysis":
            return ["Do not execute until the user gives explicit approval and a concrete run_id."]
        if intent == "plan_analysis":
            return ["Write an analysis design from code_library, then wait for human approval before execution."]
        return ["Execute the planned harness command if the user confirms the intent."]

    def _executed_reply(self, intent: str, result: Any) -> str:
        if intent == "plan_analysis" and isinstance(result, dict):
            return f"Analysis design prepared for run_id={result.get('run_id')}; execution remains blocked until explicit approval."
        if intent == "run_analysis" and isinstance(result, dict):
            adapter = result.get("adapter_result") or {}
            evaluation = result.get("evaluation") or {}
            return f"Analysis execution finished with adapter_status={adapter.get('status')} and evaluation_status={evaluation.get('status')}."
        if intent == "evaluate_run" and isinstance(result, dict):
            return f"Run evaluation completed with status={result.get('status')}."
        if intent == "target_task" and isinstance(result, dict):
            status = result.get("status") or result.get("final_status") or result.get("environment_status") or ("valid" if result.get("valid") else "invalid")
            return f"TargetTask command completed with status={status}."
        if intent == "research_intent" and isinstance(result, dict):
            status = result.get("status") or ("valid" if result.get("valid") else "invalid")
            return f"Research workflow command completed with status={status}."
        if intent in {"list_capabilities", "list_modules", "inspect_module"}:
            return "Method-asset capability information has been returned in structured output."
        if intent == "create_project" and isinstance(result, dict):
            return f"项目已创建：{result.get('paper_id')}。下一步我会检查状态并推进到第一个需要真实输入或人工确认的位置。"
        if intent == "run_pipeline" and isinstance(result, dict):
            state = result.get("pipeline_state")
            stages = [e.get("stage") for e in result.get("events", []) if e.get("event") == "stage"]
            return f"已执行工作流步骤：{', '.join(stages) or '无新 stage'}；当前状态：{state}。"
        if intent in {"validate_contract", "validate_workflow"} and isinstance(result, dict):
            return f"验证完成：valid={result.get('valid')}，issue_count={result.get('issue_count')}。"
        if intent == "status" and isinstance(result, dict):
            return result.get("summary", "状态已读取。")
        return "请求已通过 AI harness 执行，结果已写入结构化输出。"

    def _planned_reply(self, payload: dict[str, Any]) -> str:
        return f"已生成执行计划，intent={payload['intent']}，尚未运行工作流。"

    def _apply_route_guard(
        self,
        intent: str,
        *,
        request: str,
        route: dict[str, Any],
        resolved_paper: dict[str, Any],
    ) -> str:
        """Prevent fuzzy exploration requests from becoming pipeline actions."""
        if route.get("mode") != "exploration_mode":
            return intent
        if intent == "run_pipeline" and self._looks_like_orientation_request(request):
            return "status" if resolved_paper.get("paper_id") else "list_papers"
        if intent == "create_project" and self._looks_like_orientation_request(request):
            return "status" if resolved_paper.get("paper_id") else "list_papers"
        return intent

    def _method_asset_route(self, intent: str, route: dict[str, Any], *, request: str = "") -> dict[str, Any]:
        overrides = {
            "list_capabilities": "exploration_mode",
            "list_modules": "exploration_mode",
            "inspect_module": "exploration_mode",
            "plan_analysis": "analysis_design_mode",
            "run_analysis": "execution_mode",
            "evaluate_run": "closeout_audit_mode",
        }
        mode = overrides.get(intent)
        if intent == "target_task":
            mode = {
                "validate": "exploration_mode",
                "plan": "analysis_design_mode",
                "run": "execution_mode" if self._target_execute_requested(request) else "analysis_design_mode",
                "evaluate": "closeout_audit_mode",
                "package": "closeout_audit_mode",
            }[self._infer_target_subcommand(request)]
        if intent == "research_intent":
            mode = {
                "validate": "exploration_mode",
                "start": "analysis_design_mode",
                "analyze": "execution_mode" if self._target_execute_requested(request) else "analysis_design_mode",
                "review": "closeout_audit_mode",
                "write": "closeout_audit_mode",
                "package": "closeout_audit_mode",
                "status": "exploration_mode",
            }[self._infer_research_subcommand(request)]
        if not mode:
            return route
        profile = self.mode_resolver.resolve_profile(mode, request)
        updated = self.mode_resolver.resolve_route(
            request,
            explicit_mode=mode,
            explicit_profile=profile,
            paper_id=(route or {}).get("paper_id") or None,
            explicit_journal=((route or {}).get("journal_policy") or {}).get("explicit_target_journal") or None,
        )
        updated["human_checkpoint"] = (
            intent == "run_analysis"
            or (intent == "target_task" and self._target_execute_requested(request))
            or (intent == "research_intent" and self._target_execute_requested(request))
        )
        return updated

    def _method_asset_guard(
        self,
        intent: str,
        request: str,
        resolved_paper: dict[str, Any],
    ) -> Optional[dict[str, Any]]:
        if intent == "target_task":
            target_path = self._extract_target_path(request)
            required = []
            if not target_path:
                required.append("target_task_yaml")
            elif not self._resolve_target_path(target_path).exists():
                required.append("existing_target_task_yaml")
            if (
                self._infer_target_subcommand(request) == "run"
                and self._target_execute_requested(request)
                and not self._has_approval_phrase(request)
            ):
                required.append("explicit_user_approval")
            if required:
                message = f"target_task requires {', '.join(required)} before execution."
                return {
                    "status": "needs_input",
                    "result": {"message": message, "required": required, "target": target_path},
                    "next_model_actions": [
                        "Provide an existing TargetTask YAML path.",
                        "Use explicit approval only after reviewing the resolved target and environment gates.",
                    ],
                    "user_facing_reply": message,
                }
            return None
        if intent == "research_intent":
            intent_path = self._extract_research_intent_path(request)
            required = []
            if not intent_path:
                required.append("research_intent_yaml")
            elif not self._resolve_target_path(intent_path).exists():
                required.append("existing_research_intent_yaml")
            if (
                self._infer_research_subcommand(request) == "analyze"
                and self._target_execute_requested(request)
                and not self._has_approval_phrase(request)
            ):
                required.append("explicit_user_approval")
            if required:
                message = f"research_intent requires {', '.join(required)} before execution."
                return {
                    "status": "needs_input",
                    "result": {"message": message, "required": required, "intent": intent_path},
                    "next_model_actions": [
                        "Provide an existing research_intent.v1 YAML path or use research start to create one.",
                        "Review the generated strategy and dashboard before real execution.",
                    ],
                    "user_facing_reply": message,
                }
            return None
        if intent not in {"run_analysis", "evaluate_run"}:
            return None
        paper_id = resolved_paper.get("paper_id")
        run_id = self._extract_run_id(request)
        required = []
        if not paper_id:
            required.append("paper_id")
        if not run_id:
            required.append("run_id")
        if intent == "run_analysis" and not self._has_approval_phrase(request):
            required.append("explicit_user_approval")
        if paper_id and run_id and intent == "run_analysis":
            design_path = self.api.papers_dir / paper_id / "results" / "runs" / run_id / "analysis_design.yaml"
            if not design_path.exists():
                required.append("analysis_design.yaml")
        if required:
            message = (
                f"{intent} requires " + ", ".join(required)
                + ". Prepare a code_library analysis design and obtain explicit approval before execution."
            )
            return {
                "status": "needs_input",
                "result": {
                    "message": message,
                    "required": required,
                    "paper_id": paper_id,
                    "run_id": run_id,
                },
                "next_model_actions": [
                    "Create or identify the result run with plan-analysis.",
                    "Ask the user for explicit approval before --execute.",
                ],
                "user_facing_reply": message,
            }
        return None

    def _resolve_paper_id(self, paper_id: Optional[str]) -> dict[str, Any]:
        candidates = self._paper_candidates()
        if paper_id:
            exists = (self.api.papers_dir / paper_id).exists()
            return {
                "paper_id": paper_id if exists else None,
                "strategy": "explicit",
                "exists": exists,
                "candidates": candidates,
            }
        if len(candidates) == 1:
            return {
                "paper_id": candidates[0]["paper_id"],
                "strategy": "single_existing_paper",
                "exists": True,
                "candidates": candidates,
            }
        return {
            "paper_id": None,
            "strategy": "needs_input" if candidates else "no_existing_paper",
            "exists": False,
            "candidates": candidates,
        }

    def _paper_candidates(self) -> list[dict[str, Any]]:
        if not self.api.papers_dir.exists():
            return []
        candidates = []
        for path in sorted(self.api.papers_dir.iterdir(), key=lambda p: p.stat().st_mtime, reverse=True):
            if not path.is_dir():
                continue
            passport_path = path / "project_passport.yaml"
            if not passport_path.exists():
                continue
            title = ""
            state = ""
            try:
                data = yaml.safe_load(passport_path.read_text(encoding="utf-8")) or {}
                title = str(data.get("idea", ""))
                state = str(data.get("pipeline_state", data.get("status", "")))
            except Exception:
                state = "unreadable_passport"
            candidates.append({
                "paper_id": path.name,
                "paper_dir": str(path),
                "pipeline_state": state,
                "idea": title,
            })
        return candidates

    def _first_checkpoint_blocker(self, paper_id: str) -> Optional[str]:
        blockers = self.api.engine(paper_id).checkpoint_blockers()
        return blockers[0]["stage"] if blockers else None

    def _single_pending_invocation(self, paper_id: str) -> Optional[str]:
        pending = self.api.list_harness_invocations(paper_id, status="pending_harness")
        if len(pending) == 1:
            return pending[0].get("name") or pending[0].get("stage_id")
        return None

    def _infer_field(self, request: str) -> str:
        fields = []
        lowered = request.lower()
        for needles, field in self.FIELD_HINTS:
            if any(str(needle).lower() in lowered for needle in needles):
                fields.append(field)
        return ", ".join(dict.fromkeys(fields)) or "biomedical research"

    def _infer_journal(self, request: str) -> str:
        known = [
            "Genome Biology",
            "Nature Genetics",
            "Nature Communications",
            "Bioinformatics",
            "Cell",
            "Science",
            "JAMA",
            "The Lancet",
        ]
        lowered = request.lower()
        for name in known:
            if name.lower() in lowered:
                return name
        match = re.search(r"(?:journal|期刊|投稿到|目标期刊)[:：\s]+([A-Za-z][A-Za-z &-]{2,80})", request)
        return match.group(1).strip() if match else ""

    def _infer_timeline(self, request: str) -> Optional[int]:
        match = re.search(r"(\d{1,2})\s*(?:weeks?|周|星期)", request, flags=re.IGNORECASE)
        return int(match.group(1)) if match else None

    def _infer_stage(self, request: str) -> Optional[str]:
        lowered = request.lower()
        for stage in self.STAGE_IDS:
            if stage in lowered:
                return stage
        for alias, stage in self.STAGE_ALIASES.items():
            if alias.lower() in lowered:
                return stage
        return None

    def _extract_paper_id(self, request: str) -> Optional[str]:
        match = re.search(r"\b((?:strat|paper)[-_][A-Za-z0-9_.-]+)\b", request)
        return match.group(1) if match else None

    def _extract_run_id(self, request: str) -> Optional[str]:
        patterns = [
            r"\brun[_-]?id[:=\s]+([A-Za-z][A-Za-z0-9_.-]*_\d{8}_v\d+)\b",
            r"\b([A-Za-z][A-Za-z0-9_.-]*_\d{8}_v\d+)\b",
        ]
        for pattern in patterns:
            match = re.search(pattern, request, flags=re.IGNORECASE)
            if match:
                return match.group(1)
        return None

    @staticmethod
    def _extract_target_path(request: str, *, notes: str = "") -> Optional[str]:
        text = f"{request} {notes}".strip()
        quoted = re.search(r"[\"']([^\"']+\.ya?ml)[\"']", text, flags=re.IGNORECASE)
        if quoted:
            return quoted.group(1)
        unquoted = re.search(r"(?<![\w.-])([^\s,;]+\.ya?ml)(?![\w.-])", text, flags=re.IGNORECASE)
        if unquoted:
            return unquoted.group(1).strip("\"'")
        if "pbmc3k" in text.lower():
            return "targets/examples/pbmc3k_t_subcluster_v5.yaml"
        return None

    @staticmethod
    def _extract_research_intent_path(request: str, *, notes: str = "") -> Optional[str]:
        text = f"{request} {notes}".strip()
        quoted = re.search(r"[\"']([^\"']+\.ya?ml)[\"']", text, flags=re.IGNORECASE)
        if quoted:
            return quoted.group(1)
        unquoted = re.search(r"(?<![\w.-])([^\s,;]+\.ya?ml)(?![\w.-])", text, flags=re.IGNORECASE)
        if unquoted:
            return unquoted.group(1).strip("\"'")
        if "pbmc3k" in text.lower():
            return "intents/examples/pbmc3k_t_subcluster_intent.yaml"
        return None

    def _resolve_target_path(self, target_path: str) -> Path:
        path = Path(target_path).expanduser()
        return path if path.is_absolute() else self.project_root / path

    @staticmethod
    def _infer_target_subcommand(request: str) -> str:
        text = request.lower()
        text = re.sub(r"([\"']).+?\.ya?ml\1", " ", text)
        text = re.sub(r"\S+\.ya?ml", " ", text)
        if any(token in text for token in ("evaluate", "evaluation", "评估", "评价", "审核")):
            return "evaluate"
        if any(token in text for token in ("package", "打包", "归档")):
            return "package"
        if any(token in text for token in ("plan", "规划", "设计")):
            return "plan"
        if any(token in text for token in ("run", "execute", "执行", "运行")):
            return "run"
        return "validate"

    @staticmethod
    def _infer_research_subcommand(request: str) -> str:
        text = request.lower()
        text = re.sub(r"([\"']).+?\.ya?ml\1", " ", text)
        text = re.sub(r"\S+\.ya?ml", " ", text)
        if any(token in text for token in ("analyze", "analysis", "分析", "执行")):
            return "analyze"
        if any(token in text for token in ("review", "evaluate", "复核", "评估", "审核")):
            return "review"
        if any(token in text for token in ("write", "manuscript", "写作", "撰写")):
            return "write"
        if any(token in text for token in ("package", "打包", "归档")):
            return "package"
        if any(token in text for token in ("status", "dashboard", "状态", "进度", "驾驶舱")):
            return "status"
        if any(token in text for token in ("start", "plan", "启动", "规划")):
            return "start"
        return "validate"

    @staticmethod
    def _target_execute_requested(request: str) -> bool:
        text = request.lower()
        compact = re.sub(r"\s+", "", text)
        return any(
            token in text or token in compact
            for token in ("--execute", "real execution", "execute target", "真实执行", "执行目标任务")
        )

    @staticmethod
    def _target_package_check_requested(request: str) -> bool:
        text = request.lower()
        return "--require-packages" in text or "检查包" in text or "check packages" in text

    def _extract_module_id(self, request: str, *, notes: str = "") -> Optional[str]:
        text = f"{request} {notes}".strip()
        registry = ModuleRegistry(self.project_root)
        for module_id in registry.modules:
            if module_id.lower() in text.lower():
                return module_id
        match = re.search(r"\b([A-Za-z0-9_]+(?:\.[A-Za-z0-9_-]+){2,})\b", text)
        return match.group(1) if match else None

    @staticmethod
    def _extract_inputs(request: str) -> list[str]:
        inputs = []
        for match in re.finditer(r"(?:input|data|path|输入|数据路径)[:=]\s*([^\s,;]+)", request, flags=re.IGNORECASE):
            inputs.append(match.group(1).strip().strip('"'))
        return inputs

    @staticmethod
    def _default_run_id(prefix: str) -> str:
        return f"{prefix}_{datetime.now().strftime('%Y%m%d')}_v1"

    @staticmethod
    def _has_approval_phrase(request: str) -> bool:
        text = request.lower()
        compact = re.sub(r"\s+", "", text)
        needles = (
            "--approved",
            "approved",
            "explicit approval",
            "user approved",
            "已批准",
            "批准执行",
            "确认执行",
            "我批准",
            "可以执行",
        )
        return any(needle.lower() in text or needle.lower() in compact for needle in needles)

    @staticmethod
    def _infer_modality(request: str) -> str:
        text = request.lower()
        compact = re.sub(r"\s+", "", text)
        if any(needle in text or needle in compact for needle in ("single-cell", "single cell", "scrna", "seurat", "pbmc", "单细胞")):
            return "scrna"
        if any(needle in text or needle in compact for needle in ("spatial", "visium", "xenium", "空间")):
            return "spatial"
        if any(needle in text or needle in compact for needle in ("bulk", "bulk-rnaseq", "bulk rnaseq", "deseq2", "rna-seq", "转录组")):
            return "bulk_rnaseq"
        if any(needle in text or needle in compact for needle in ("multiomics", "multi-omics", "multi omics", "多组学")):
            return "multiomics"
        return "general"

    def _looks_like_orientation_request(self, request: str) -> bool:
        text = request.lower()
        compact = re.sub(r"\s+", "", text)
        return self._has_any(
            text,
            compact,
            (
                "scan", "audit", "optimize", "improve workflow", "fast-context",
                "tool unavailable", "skill", "agent", "检查", "扫描", "优化", "工具不可用",
            ),
        )

    def _load_config(self) -> dict[str, Any]:
        path = self.project_root / "config" / "default_config.yaml"
        if not path.exists():
            return {}
        return yaml.safe_load(path.read_text(encoding="utf-8")) or {}

    @staticmethod
    def _format_command(command: str, args: list[str]) -> str:
        parts = ["python", "-m", "paper_workflow.cli", command]
        for arg in args:
            parts.append(json.dumps(str(arg), ensure_ascii=False) if arg.startswith("-") is False else arg)
        return " ".join(parts)

    @staticmethod
    def _has_any(text: str, compact: str, needles: tuple[str, ...]) -> bool:
        return any(needle.lower() in text or needle.lower() in compact for needle in needles)
