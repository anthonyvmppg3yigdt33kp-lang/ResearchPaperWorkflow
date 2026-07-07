"""Model-facing natural-language harness for Claude/Codex integration.

The harness is intentionally thin: it routes a user's natural-language request
to the existing WorkflowAPI and records which command a model executed. It does
not replace the V4 truth layer, stage verification, quality gates, or human
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

from paper_workflow.api import WorkflowAPI
from paper_workflow.routing.mode_resolver import ModeResolver
from paper_workflow.routing.tool_doctor import ToolDoctor


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
        if dry_run:
            payload["next_model_actions"] = self._next_actions_for_plan(intent, resolved_paper)
            payload["user_facing_reply"] = self._planned_reply(payload)
            return payload

        paperless_intents = {"create_project", "list_papers", "validate_contract", "route_task", "doctor"}
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

        if self._has_any(text, compact, ("route task", "route-task", "resolve mode", "mode/profile", "模式路由", "模式匹配")):
            return "route_task"
        if self._has_any(text, compact, ("doctor", "tool check", "fast-context", "fast_context", "skill check", "agent check", "工具不可用", "工具检查")):
            return "doctor"

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
        return ["Report the result to the user and ask for approval if a checkpoint is required."]

    def _next_actions_for_plan(self, intent: str, resolved_paper: dict[str, Any]) -> list[str]:
        paperless_intents = {"create_project", "list_papers", "validate_contract", "route_task", "doctor"}
        if intent not in paperless_intents and not resolved_paper.get("paper_id"):
            return ["Ask the user for the paper_id or create a new project first."]
        return ["Execute the planned harness command if the user confirms the intent."]

    def _executed_reply(self, intent: str, result: Any) -> str:
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
