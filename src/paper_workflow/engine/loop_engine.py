"""
Paper Loop Engine — Core research paper loop orchestrator.

Loop model: observe → decide → run → verify → record → mark_stale → diagnose → repeat

Domain-agnostic. Configured via config/default_config.yaml.
Supports overriding the hardcoded PIPELINE_STAGES from config via ConfigLoader.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, ClassVar, Optional
import warnings
import json

import yaml


class StageStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    STALE = "stale"
    SKIPPED = "skipped"
    BLOCKED = "blocked"


class PipelineState(Enum):
    CLEAN = "clean"
    DRIFT_DETECTED = "drift_detected"
    STALE_STAGES = "stale_stages"
    GATE_FAILURE = "gate_failure"
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"
    CHECKPOINT_REQUIRED = "checkpoint_required"


@dataclass
class StageDefinition:
    """Definition of a paper pipeline stage."""
    name: str
    description: str
    phase: int
    category: str
    upstream: list[str] = field(default_factory=list)
    downstream: list[str] = field(default_factory=list)
    required_artifacts: list[str] = field(default_factory=list)
    produces_artifacts: list[str] = field(default_factory=list)
    gate_rules: list[dict] = field(default_factory=list)
    quality_gates: list[dict] = field(default_factory=list)
    transition_policy: dict[str, Any] = field(default_factory=dict)
    executor_mode: str = "real"
    agent: str = ""
    skill: str = ""
    human_checkpoint: bool = False
    max_retries: int = 3
    timeout_minutes: int = 30

    def to_dict(self) -> dict:
        return {
            "name": self.name, "description": self.description, "phase": self.phase,
            "category": self.category, "upstream": self.upstream, "downstream": self.downstream,
            "required_artifacts": self.required_artifacts, "produces_artifacts": self.produces_artifacts,
            "gate_rules": self.gate_rules, "quality_gates": self.quality_gates,
            "transition_policy": self.transition_policy, "executor_mode": self.executor_mode,
            "agent": self.agent, "skill": self.skill,
            "human_checkpoint": self.human_checkpoint, "max_retries": self.max_retries,
            "timeout_minutes": self.timeout_minutes,
        }

    # ------------------------------------------------------------------
    # Phase derivation: order integer (1-20) -> phase integer (1-6)
    # ------------------------------------------------------------------
    # The 6-phase grouping per ARCHITECTURE.md (v4.0, 20 stages):
    #   1. Research & Planning   -> stage orders 1-5
    #   2. Data & Methods        -> stage orders 6-9
    #   3. Writing               -> stage orders 10-13
    #   4. Assembly & Review     -> stage orders 14-16
    #   5. Revision              -> stage orders 17-19
    #   6. Finalize              -> stage order 20
    # ------------------------------------------------------------------
    # Legacy fallback — layer string → phase integer (deprecated; prefer
    # explicit ``phase`` or ``order``-based derivation).
    # ------------------------------------------------------------------
    _LAYER_TO_PHASE: ClassVar[dict[str, int]] = {
        "strategy": 1,
        "execution": 2,
        "decision": 3,
        "supervision": 4,
    }

    # ------------------------------------------------------------------
    # Config-gate severity lookup (lazy-filled by _resolve_gate_severities)
    # ------------------------------------------------------------------
    _GATE_SEVERITY_MAP: ClassVar[dict[str, str]] = {}

    @staticmethod
    def _order_to_phase(order: int) -> int:
        """Map a pipeline stage *order* (1–19) to its phase (1–6).

        This is the canonical mapping used when stages are loaded from the
        YAML config (which uses ``order``, not ``phase``).
        v4.0 includes design_analysis_plan (order 5) and
        aigc_humanizer_review (order 15).
        """
        if order <= 5:
            return 1   # Research & Planning (v3: orders 1-5)
        if order <= 9:
            return 2   # Data & Methods (v3: orders 6-9)
        if order <= 13:
            return 3   # Writing (v3: orders 10-13)
        if order <= 16:
            return 4   # Assembly & Review (v3: orders 14-16)
        if order <= 19:
            return 5   # Revision (v3: orders 17-18)
        return 6       # Finalize (v4: order 20)

    @classmethod
    def _resolve_gate_severities(cls, quality_gates: dict[str, Any]) -> None:
        """Populate ``_GATE_SEVERITY_MAP`` from a quality-gates dict so
        that gate-rule entries can be annotated with their severity."""
        cls._GATE_SEVERITY_MAP.clear()
        for gate_key, gate_def in quality_gates.items():
            sev = str(gate_def.get("severity", "MEDIUM")).upper()
            cls._GATE_SEVERITY_MAP[gate_key] = sev

    @classmethod
    def _gate_ref(cls, rule_id: str) -> dict[str, str]:
        return {"rule": rule_id, "severity": cls._GATE_SEVERITY_MAP.get(rule_id, "")}

    @staticmethod
    def _looks_like_transition(item: str) -> bool:
        return (
            item.startswith("advance_to:")
            or item.startswith("notify_human:")
            or item in {"retry_stage", "abort_pipeline", "pipeline_complete"}
        )

    @classmethod
    def _transition_policy_from_legacy(cls, gate_rules_raw: dict[str, Any]) -> dict[str, Any]:
        policy: dict[str, Any] = {}
        on_pass = list(gate_rules_raw.get("on_pass", []) or [])
        on_fail = list(gate_rules_raw.get("on_fail", []) or [])
        pass_transitions = [x for x in on_pass if cls._looks_like_transition(str(x))]
        fail_transitions = [x for x in on_fail if cls._looks_like_transition(str(x))]
        if pass_transitions:
            first = str(pass_transitions[0])
            if first.startswith("advance_to:"):
                policy["on_pass"] = {"action": "advance_to", "stage": first.split(":", 1)[1].strip()}
            else:
                policy["on_pass"] = {"action": first}
        if fail_transitions:
            actions = []
            for item in fail_transitions:
                text = str(item)
                if text.startswith("notify_human:"):
                    actions.append({"action": "notify_human", "reason": text.split(":", 1)[1].strip()})
                else:
                    actions.append({"action": text})
            policy["on_fail"] = {"actions": actions}
        return policy

    @classmethod
    def from_config_stages(
        cls,
        config_stages: list[dict[str, Any]],
        quality_gates: Optional[dict[str, Any]] = None,
    ) -> list[StageDefinition]:
        """Convert pipeline stages from the YAML config format into
        ``StageDefinition`` objects used by the engine.

        Parameters
        ----------
        config_stages:
            Raw stage list as returned by ``ConfigLoader.get_pipeline_stages()``.
        quality_gates:
            Optional quality-gates dict (the raw ``quality_gates`` section)
            used to resolve severity labels on gate rules.  When ``None``,
            gate rules receive an empty severity string.

        Returns
        -------
        list[StageDefinition]
            Converted stage definitions in the order they appear in the config.
        """
        if quality_gates:
            cls._resolve_gate_severities(quality_gates)

        definitions: list[StageDefinition] = []
        for raw in config_stages:
            # --- Basic identity ---
            stage_id: str = raw.get("id", "")
            stage_name: str = raw.get("name", stage_id)
            layer: str = raw.get("layer", "strategy")
            order: int = int(raw.get("order", 0))
            if "phase" in raw:
                phase = int(raw["phase"])
            elif order:
                phase = cls._order_to_phase(order)
            else:
                phase = cls._LAYER_TO_PHASE.get(layer, 0)

            # --- Upstream dependencies ---
            upstream: list[str] = list(raw.get("dependencies", []) or [])

            # --- Produced artifacts / required outputs ---
            artifacts: list[str] = list(raw.get("artifacts_out", []) or [])
            required_outputs: list[str] = list(raw.get("required_outputs", artifacts) or [])

            # --- Agent & skill ---
            agent: str = raw.get("agent", "")
            skills: list[str] = raw.get("skills", []) or []
            skill: str = skills[0] if skills else ""

            # --- Timeout (seconds → minutes) ---
            timeout_seconds: int = int(raw.get("timeout_seconds", 1800))
            timeout_minutes: int = max(1, timeout_seconds // 60)

            # --- Retry ---
            retry: dict[str, Any] = raw.get("retry", {}) or {}
            max_retries: int = int(retry.get("max_attempts", 3))

            # --- Quality gates and transition policy ---
            quality_gate_entries: list[dict[str, Any]] = []
            for gate in raw.get("quality_gates", []) or []:
                if isinstance(gate, dict):
                    rule_id = str(gate.get("rule") or gate.get("id") or gate.get("name") or "")
                    if rule_id:
                        entry = cls._gate_ref(rule_id)
                        entry.update(gate)
                        quality_gate_entries.append(entry)
                else:
                    quality_gate_entries.append(cls._gate_ref(str(gate)))

            transition_policy: dict[str, Any] = dict(raw.get("transition_policy", {}) or {})
            gate_rules_raw: dict[str, Any] = raw.get("gate_rules", {}) or {}
            if gate_rules_raw:
                warnings.warn(
                    "gate_rules is deprecated; use quality_gates and transition_policy",
                    DeprecationWarning,
                    stacklevel=2,
                )
                for rule_id in list(gate_rules_raw.get("on_pass", []) or []) + list(gate_rules_raw.get("on_fail", []) or []):
                    rule_id = str(rule_id)
                    if not cls._looks_like_transition(rule_id):
                        quality_gate_entries.append(cls._gate_ref(rule_id))
                if not transition_policy:
                    transition_policy = cls._transition_policy_from_legacy(gate_rules_raw)
            gate_rules: list[dict[str, Any]] = list(quality_gate_entries)

            # --- Human checkpoint ---
            human_checkpoint: bool = bool(raw.get("human_checkpoint", False))

            definitions.append(StageDefinition(
                name=stage_id,
                description=stage_name,
                phase=phase,
                category=layer,
                upstream=upstream,
                downstream=[],  # downstream is derived at runtime, not stored in config
                required_artifacts=required_outputs,
                produces_artifacts=artifacts,
                gate_rules=gate_rules,
                quality_gates=quality_gate_entries,
                transition_policy=transition_policy,
                executor_mode=str(raw.get("executor_mode", "real")),
                agent=agent,
                skill=skill,
                human_checkpoint=human_checkpoint,
                max_retries=max_retries,
                timeout_minutes=timeout_minutes,
            ))

        return definitions


@dataclass
class StageState:
    """Runtime state of a single stage."""
    definition: StageDefinition
    status: StageStatus = StageStatus.PENDING
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    retry_count: int = 0
    artifacts_produced: list[str] = field(default_factory=list)
    artifact_hashes: dict[str, str] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)
    gate_results: list[dict] = field(default_factory=list)
    execution_mode: str = "real"
    outputs_verified: bool = False
    required_outputs: list[str] = field(default_factory=list)
    missing_outputs: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "name": self.definition.name, "status": self.status.value,
            "started_at": self.started_at, "completed_at": self.completed_at,
            "retry_count": self.retry_count, "artifacts_produced": self.artifacts_produced,
            "artifact_hashes": self.artifact_hashes, "errors": self.errors,
            "gate_results": self.gate_results, "execution_mode": self.execution_mode,
            "outputs_verified": self.outputs_verified,
            "required_outputs": self.required_outputs,
            "missing_outputs": self.missing_outputs,
        }


class PaperLoopEngine:
    """Core paper loop orchestrator: 20-stage pipeline with state management (v4.0)."""

    PIPELINE_STAGES = [
        # Phase 1: Research & Planning
        StageDefinition(name="select_topic", phase=1, category="research",
                        description="Select research topic and define scope",
                        produces_artifacts=["project_passport.yaml", "paper_config.yaml"],
                        agent="research_strategist", skill="topic_research",
                        human_checkpoint=True, timeout_minutes=10),
        StageDefinition(name="target_journal", phase=1, category="research",
                        description="Identify target journal and understand requirements",
                        upstream=["select_topic"],
                        produces_artifacts=["target_journal/journal_profile.md"],
                        agent="research_strategist", skill="topic_research",
                        timeout_minutes=15),
        StageDefinition(name="literature_search", phase=1, category="research",
                        description="Search and curate literature",
                        upstream=["select_topic"],
                        produces_artifacts=["references/library.bib", "references/citation_evidence.csv"],
                        agent="literature_reviewer", skill="literature_search", timeout_minutes=30),
        StageDefinition(name="formulate_hypotheses", phase=1, category="research",
                        description="Formulate research hypotheses and plan",
                        upstream=["select_topic", "literature_search", "target_journal"],
                        produces_artifacts=["research_plan/research_plan.md", "research_plan/hypotheses.yaml"],
                        agent="research_strategist", skill="topic_research",
                        human_checkpoint=True, timeout_minutes=20),
        StageDefinition(name="design_analysis_plan", phase=1, category="research",
                        description="Design and freeze Statistical Analysis Plan BEFORE primary analysis (v3.0)",
                        upstream=["formulate_hypotheses"],
                        produces_artifacts=["research_plan/statistical_analysis_plan.yaml",
                                          "research_plan/study_design_protocol.yaml"],
                        agent="statistician", skill="statistical_testing",
                        human_checkpoint=True, timeout_minutes=30),
        # Phase 2: Data & Methods
        StageDefinition(name="data_audit", phase=2, category="analysis",
                        description="Audit data quality, completeness, and metadata",
                        upstream=["design_analysis_plan"],
                        produces_artifacts=["data/data_audit_report.md", "data/data_inventory.yaml"],
                        agent="data_auditor", skill="qc_pipeline", timeout_minutes=20),
        StageDefinition(name="figure_planning", phase=2, category="analysis",
                        description="Design Figure 1-6 layout and identify needed analyses",
                        upstream=["design_analysis_plan", "data_audit"],
                        produces_artifacts=["results/figure_plan.json", "results/figure_plan.html"],
                        agent="figure_planner", skill="figure_planning",
                        human_checkpoint=True, timeout_minutes=20),
        StageDefinition(name="run_analysis", phase=2, category="analysis",
                        description="Execute data analysis pipeline and generate results",
                        upstream=["figure_planning", "data_audit"],
                        downstream=["verify_methods"],
                        produces_artifacts=["results/*/", "results/run_manifest.yaml"],
                        agent="analysis_executor", skill="spatial_analysis", timeout_minutes=120),
        StageDefinition(name="verify_methods", phase=2, category="analysis",
                        description="Verify all analysis code runs and produces declared outputs",
                        upstream=["run_analysis"],
                        produces_artifacts=["methods/run_manifest.yaml"],
                        gate_rules=[{"rule": "all_outputs_exist", "severity": "critical"},
                                    {"rule": "code_reproducible", "severity": "critical"}],
                        agent="pipeline_engineer", skill="reproducibility", timeout_minutes=30),
        # Phase 3: Writing
        StageDefinition(name="write_methods", phase=3, category="writing",
                        description="Write Methods section from verified analysis",
                        upstream=["verify_methods"],
                        produces_artifacts=["manuscript/methods.md"],
                        gate_rules=[{"rule": "no_local_paths", "severity": "critical"},
                                    {"rule": "parameters_complete", "severity": "high"}],
                        agent="report_writer", skill="paper_writing", timeout_minutes=30),
        StageDefinition(name="write_results", phase=3, category="writing",
                        description="Write Results section bound to figures and tables",
                        upstream=["verify_methods", "figure_planning"],
                        produces_artifacts=["manuscript/results.md", "manuscript/claims_evidence_table.md"],
                        gate_rules=[{"rule": "no_citations_in_results", "severity": "critical"},
                                    {"rule": "figures_referenced", "severity": "critical"}],
                        agent="report_writer", skill="paper_writing", timeout_minutes=45),
        StageDefinition(name="write_introduction", phase=3, category="writing",
                        description="Write Introduction with literature-grounded background",
                        upstream=["literature_search", "formulate_hypotheses"],
                        produces_artifacts=["manuscript/introduction.md"],
                        gate_rules=[{"rule": "citations_exist_in_bibtex", "severity": "critical"}],
                        agent="report_writer", skill="paper_writing", timeout_minutes=30),
        StageDefinition(name="write_discussion", phase=3, category="writing",
                        description="Write Discussion with interpretation and limitations",
                        upstream=["write_results", "literature_search"],
                        produces_artifacts=["manuscript/discussion.md"],
                        gate_rules=[{"rule": "citations_exist_in_bibtex", "severity": "critical"},
                                    {"rule": "limitations_discussed", "severity": "high"}],
                        agent="report_writer", skill="paper_writing", timeout_minutes=30),
        # Phase 4: Assembly & Review
        StageDefinition(name="assemble_manuscript", phase=4, category="writing",
                        description="Assemble all sections into complete manuscript",
                        upstream=["write_introduction", "write_methods", "write_results", "write_discussion"],
                        produces_artifacts=["manuscript/manuscript.tex", "manuscript/manuscript.pdf"],
                        agent="report_writer", skill="paper_writing", timeout_minutes=20),
        StageDefinition(name="aigc_humanizer_review", phase=4, category="review",
                        description="Audit AIGC writing signals and create a humanizer revision pass",
                        upstream=["assemble_manuscript"],
                        produces_artifacts=["review/aigc_detection_report.md",
                                           "review/humanizer_revision_plan.yaml",
                                           "manuscript/manuscript_humanized.md"],
                        gate_rules=[{"rule": "aigc_artifact_scan", "severity": "high"},
                                    {"rule": "aigc_style_signal_density", "severity": "medium"},
                                    {"rule": "humanizer_revision_trace", "severity": "medium"}],
                        agent="aigc_humanizer_reviewer", skill="aigc_humanizer_review",
                        timeout_minutes=25),
        StageDefinition(name="integrity_check", phase=4, category="review",
                        description="Run integrity gates on complete manuscript",
                        upstream=["aigc_humanizer_review"],
                        produces_artifacts=["integrity/integrity_report.json"],
                        gate_rules=[{"rule": "bibtex_citation_existence", "severity": "critical"},
                                    {"rule": "results_no_citations", "severity": "critical"},
                                    {"rule": "claim_artifact_binding", "severity": "critical"}],
                        agent="integrity_checker", skill="paper_loop", timeout_minutes=20),
        StageDefinition(name="internal_review", phase=4, category="review",
                        description="Multi-perspective internal review",
                        upstream=["integrity_check"],
                        produces_artifacts=["review/review_report.md"],
                        agent="team_orchestrator", skill="paper_writing",
                        human_checkpoint=True, timeout_minutes=45),
        # Phase 5: Revision
        StageDefinition(name="apply_revision", phase=5, category="review",
                        description="Apply revision plan to manuscript",
                        upstream=["internal_review"],
                        produces_artifacts=["manuscript/manuscript_revised.tex"],
                        agent="report_writer", skill="paper_writing", max_retries=5, timeout_minutes=60),
        StageDefinition(name="re_review", phase=5, category="review",
                        description="Re-review revised manuscript",
                        upstream=["apply_revision"],
                        produces_artifacts=["review/re_review_report.md"],
                        agent="team_orchestrator", skill="paper_loop", timeout_minutes=30),
        # Phase 6: Finalize
        StageDefinition(name="finalize", phase=6, category="finalize",
                        description="Final quality check and prepare submission package",
                        upstream=["re_review"],
                        produces_artifacts=["submission/manuscript_final.pdf", "submission/cover_letter.pdf",
                                           "quality/final_quality_report.md"],
                        gate_rules=[{"rule": "section_length_minimum", "severity": "medium"},
                                    {"rule": "no_bullets_in_prose", "severity": "medium"}],
                        agent="integrity_checker", skill="paper_loop",
                        human_checkpoint=True, timeout_minutes=30),
    ]

    def __init__(
        self,
        project_root: Path,
        paper_id: str,
        papers_dir: Optional[Path] = None,
        config_path: Optional[Path] = None,
    ):
        """Initialise the loop engine for a paper project.

        Parameters
        ----------
        project_root:
            Root directory of the workflow project.
        paper_id:
            Unique identifier for this paper (used as sub-directory name).
        papers_dir:
            Directory containing all paper projects.  Defaults to
            ``<project_root>/papers``.
        config_path:
            Optional path to a YAML config file.  When provided, the engine
            loads pipeline stage definitions from the config via
            ``ConfigLoader``, overriding the hardcoded ``PIPELINE_STAGES``.
            When ``None`` (default), the hardcoded fallback stages are used,
            preserving full backward compatibility.
        """
        self.project_root = project_root
        self.paper_id = paper_id
        if papers_dir is None:
            papers_dir = project_root / "papers"
        self.paper_dir = papers_dir / paper_id
        self.paper_dir.mkdir(parents=True, exist_ok=True)
        self.stages: dict[str, StageState] = {}
        self.pipeline_state = PipelineState.CLEAN

        # --- Resolve pipeline stages: config → hardcoded fallback ---
        self._active_stages: list[StageDefinition] = list(self.PIPELINE_STAGES)
        if config_path is not None:
            self._load_stages_from_config(config_path)
        self._load_workflow_contract()

        self._initialize_stages()
        self._derive_downstream_links()
        self._hydrate_from_passport()
        self._hydrate_from_stage_results()

        # Initialize AgentDispatcher for actual stage execution
        self._dispatcher: Optional[Any] = None
        try:
            from paper_workflow.engine.agent_dispatcher import AgentDispatcher
            from paper_workflow.utils.config_loader import ConfigLoader
            loader = ConfigLoader(config_path=config_path) if config_path else ConfigLoader()
            self._dispatcher = AgentDispatcher(loader, self.project_root)
        except Exception as e:
            self._record_config_error(f"AgentDispatcher initialization failed: {e}")

    def _load_stages_from_config(self, config_path: Path) -> None:
        """Load pipeline stage definitions from a YAML config file.

        Delegates to ``ConfigLoader`` for parsing and the classmethod
        ``from_config_stages`` for conversion.  On any error the hardcoded
        ``PIPELINE_STAGES`` are kept in place (fail-safe).
        """
        try:
            from paper_workflow.utils.config_loader import ConfigLoader

            loader = ConfigLoader(config_path=config_path)
            raw_stages = loader.get_pipeline_stages()
            if not raw_stages:
                return

            raw_gates = loader.get_quality_gates()
            # Flatten the grouped gates back into {gate_id: gate_def} for the mapper
            flat_gates: dict[str, Any] = {}
            for gate_list in raw_gates.values():
                for g in gate_list:
                    flat_gates[g.get("id", "")] = g

            converted = StageDefinition.from_config_stages(raw_stages, flat_gates)
            if converted:
                self._active_stages = converted
        except Exception as e:
            # Log error and keep hardcoded PIPELINE_STAGES as safest fallback
            self._record_config_error(f"Failed to load pipeline config: {e}")

    def _load_workflow_contract(self) -> None:
        """Overlay truth-layer stage contract if workflow_contract.yaml exists."""
        candidates = [
            self.project_root / "workflow_contract.yaml",
            self.project_root / "config" / "workflow_contract.yaml",
            Path(__file__).resolve().parents[3] / "workflow_contract.yaml",
        ]
        contract_path = next((p for p in candidates if p.exists()), None)
        if contract_path is None:
            return
        try:
            with open(contract_path, "r", encoding="utf-8") as f:
                contract = yaml.safe_load(f) or {}
            raw_stages = contract.get("stages", {}) or {}
            if isinstance(raw_stages, list):
                stage_contracts = {s.get("id") or s.get("name"): s for s in raw_stages if isinstance(s, dict)}
            else:
                stage_contracts = raw_stages
            for sd in self._active_stages:
                raw = stage_contracts.get(sd.name, {}) or {}
                if not isinstance(raw, dict):
                    continue
                if "required_outputs" in raw:
                    sd.required_artifacts = list(raw.get("required_outputs", []) or [])
                    for artifact in sd.required_artifacts:
                        if artifact not in sd.produces_artifacts:
                            sd.produces_artifacts.append(artifact)
                if "quality_gates" in raw:
                    sd.quality_gates = [
                        g if isinstance(g, dict) else {"rule": str(g), "severity": ""}
                        for g in (raw.get("quality_gates", []) or [])
                    ]
                    sd.gate_rules = list(sd.quality_gates)
                if "transition_policy" in raw:
                    sd.transition_policy = dict(raw.get("transition_policy", {}) or {})
                if "executor_mode" in raw:
                    sd.executor_mode = str(raw.get("executor_mode", "real"))
        except Exception as e:
            self._record_config_error(f"Failed to load workflow contract: {e}")

    def _initialize_stages(self) -> None:
        for stage_def in self._active_stages:
            self.stages[stage_def.name] = StageState(definition=stage_def)

    def _derive_downstream_links(self) -> None:
        downstream: dict[str, list[str]] = {sd.name: [] for sd in self._active_stages}
        for sd in self._active_stages:
            for upstream in sd.upstream:
                downstream.setdefault(upstream, []).append(sd.name)
        for sd in self._active_stages:
            sd.downstream = downstream.get(sd.name, [])

    def _hydrate_from_passport(self) -> None:
        passport_path = self.paper_dir / "project_passport.yaml"
        if not passport_path.exists():
            return
        try:
            with open(passport_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
            state_raw = data.get("pipeline_state")
            if state_raw:
                try:
                    self.pipeline_state = PipelineState(state_raw)
                except ValueError:
                    pass
            for name, saved in (data.get("stages", {}) or {}).items():
                if name not in self.stages or not isinstance(saved, dict):
                    continue
                stage = self.stages[name]
                status_raw = saved.get("status")
                if status_raw:
                    try:
                        stage.status = StageStatus(status_raw)
                    except ValueError:
                        pass
                stage.started_at = saved.get("started_at", stage.started_at)
                stage.completed_at = saved.get("completed_at", stage.completed_at)
                stage.retry_count = int(saved.get("retry_count", stage.retry_count) or 0)
                stage.artifacts_produced = list(saved.get("artifacts_produced", []) or [])
                stage.artifact_hashes = dict(saved.get("artifact_hashes", {}) or {})
                stage.errors = list(saved.get("errors", []) or [])
                stage.gate_results = list(saved.get("gate_results", []) or [])
                stage.execution_mode = saved.get("execution_mode", stage.execution_mode)
                stage.outputs_verified = bool(saved.get("outputs_verified", stage.outputs_verified))
                stage.required_outputs = list(saved.get("required_outputs", []) or [])
                stage.missing_outputs = list(saved.get("missing_outputs", []) or [])
        except Exception as e:
            self._record_config_error(f"Failed to hydrate stage state from passport: {e}")

    def _hydrate_from_stage_results(self) -> None:
        """Hydrate stage truth from per-stage result files when present.

        The passport remains the compact project-level state, while
        ``stage_results/*_result.json`` is the auditable execution record for
        each stage.  Loading both makes status/resume robust when either file
        is missing or older.
        """
        results_dir = self.paper_dir / "stage_results"
        if not results_dir.exists():
            return
        for result_path in results_dir.glob("*_result.json"):
            try:
                data = json.loads(result_path.read_text(encoding="utf-8"))
            except Exception as e:
                self._record_config_error(f"Failed to read stage result {result_path.name}: {e}")
                continue
            stage_name = data.get("stage_id") or result_path.name.replace("_result.json", "")
            if stage_name not in self.stages:
                continue
            stage = self.stages[stage_name]
            status_raw = data.get("engine_stage_status")
            if status_raw:
                try:
                    stage.status = StageStatus(status_raw)
                except ValueError:
                    pass
            stage.started_at = data.get("started_at") or stage.started_at
            stage.completed_at = data.get("engine_completed_at") or data.get("completed_at") or stage.completed_at
            stage.execution_mode = data.get("execution_mode", stage.execution_mode)
            stage.outputs_verified = bool(data.get("outputs_verified", stage.outputs_verified))
            stage.required_outputs = list(data.get("required_outputs", stage.required_outputs) or [])
            stage.missing_outputs = list(data.get("missing_outputs", stage.missing_outputs) or [])
            gate_results = data.get("quality_gate_results") or data.get("gate_results") or []
            if gate_results:
                stage.gate_results = list(gate_results)
            artifacts = data.get("artifacts", []) or []
            paths: list[str] = []
            hashes: dict[str, str] = {}
            for item in artifacts:
                if not isinstance(item, dict):
                    continue
                path = item.get("path", "")
                if path:
                    paths.append(path)
                    hashes[path] = item.get("hash_sha256", "")
            if paths:
                stage.artifacts_produced = paths
                stage.artifact_hashes = hashes

    def observe(self) -> dict:
        """Observe current project state."""
        return {
            "paper_id": self.paper_id, "paper_dir": str(self.paper_dir),
            "pipeline_state": self.pipeline_state.value,
            "stages": {name: {"status": s.status.value, "completed_at": s.completed_at,
                              "retry_count": s.retry_count, "has_errors": len(s.errors) > 0,
                              "checkpoint": self.checkpoint_status(name)}
                       for name, s in self.stages.items()},
            "timestamp": datetime.now().isoformat(),
        }

    def decide_next_stage(self) -> Optional[str]:
        """Decide the next safe stage to run."""
        checkpoint_blockers = self.checkpoint_blockers()
        if checkpoint_blockers:
            self.pipeline_state = PipelineState.CHECKPOINT_REQUIRED
            return None
        for stage_def in self._active_stages:
            stage = self.stages[stage_def.name]
            if stage.status == StageStatus.COMPLETED:
                continue
            if stage.status == StageStatus.FAILED and stage.retry_count >= stage_def.max_retries:
                continue
            upstream_ready = all(
                self.stages.get(u, StageState(definition=StageDefinition(name=u, description="", phase=0, category=""))).status
                == StageStatus.COMPLETED
                for u in stage_def.upstream
            )
            if upstream_ready:
                return stage_def.name
        all_complete = all(s.status in (StageStatus.COMPLETED, StageStatus.SKIPPED) for s in self.stages.values())
        if all_complete:
            self.pipeline_state = PipelineState.CLEAN
            return None
        self.pipeline_state = PipelineState.BLOCKED
        return None

    def latest_checkpoint(self, stage_name: str) -> dict[str, Any]:
        """Return the latest recorded checkpoint decision for a stage."""
        try:
            from paper_workflow.supervision.passport import PaperPassport
            passport = PaperPassport(self.paper_dir)
            checkpoints = [
                c for c in passport.checkpoints
                if c.get("stage") == stage_name
            ]
        except Exception:
            checkpoints = []
        if not checkpoints:
            return {}
        return sorted(checkpoints, key=lambda c: c.get("recorded_at", ""))[-1]

    def checkpoint_status(self, stage_name: str) -> str:
        if stage_name not in self.stages:
            return "unknown"
        stage = self.stages[stage_name]
        if not stage.definition.human_checkpoint:
            return "not_required"
        latest = self.latest_checkpoint(stage_name)
        if not latest:
            return "pending" if stage.status == StageStatus.COMPLETED else "not_ready"
        return str(latest.get("decision", "pending"))

    def checkpoint_approved(self, stage_name: str) -> bool:
        return self.checkpoint_status(stage_name) == "approved"

    def checkpoint_blockers(self) -> list[dict[str, Any]]:
        blockers: list[dict[str, Any]] = []
        for stage_def in self._active_stages:
            if not stage_def.human_checkpoint:
                continue
            stage = self.stages[stage_def.name]
            if stage.status != StageStatus.COMPLETED:
                continue
            if not self.checkpoint_approved(stage_def.name):
                blockers.append({
                    "stage": stage_def.name,
                    "status": self.checkpoint_status(stage_def.name),
                    "artifacts": stage.artifacts_produced,
                    "completed_at": stage.completed_at,
                })
        return blockers

    def run_stage(self, stage_name: str) -> dict:
        """Execute a stage."""
        if stage_name not in self.stages:
            return {"success": False, "error": f"Unknown stage: {stage_name}"}
        stage = self.stages[stage_name]
        stage.status = StageStatus.RUNNING
        stage.started_at = datetime.now().isoformat()
        self.pipeline_state = PipelineState.IN_PROGRESS

        # Delegate to AgentDispatcher for actual execution
        if self._dispatcher is not None:
            try:
                result = self._dispatcher.dispatch(
                    stage_name, stage.definition, self.paper_dir
                )
                # Extract artifacts from StageResult
                if hasattr(result, 'artifacts'):
                    stage.artifacts_produced = [a.path for a in result.artifacts]
                    for art in result.artifacts:
                        stage.artifact_hashes[art.path] = getattr(art, 'hash_sha256', '')
                elif isinstance(result, dict) and 'artifacts' in result:
                    stage.artifacts_produced = [a.get('path', '') for a in result['artifacts']]

                if isinstance(result, dict):
                    stage.execution_mode = result.get('execution_mode', 'real')
                    stage.outputs_verified = bool(result.get('outputs_verified', False))
                    stage.required_outputs = list(result.get('required_outputs', []) or [])
                    stage.missing_outputs = list(result.get('missing_outputs', []) or [])
                    qgr = result.get('quality_gate_results', [])
                else:
                    stage.execution_mode = getattr(result, 'execution_mode', 'real')
                    stage.outputs_verified = bool(getattr(result, 'outputs_verified', False))
                    stage.required_outputs = list(getattr(result, 'required_outputs', []) or [])
                    stage.missing_outputs = list(getattr(result, 'missing_outputs', []) or [])
                    qgr = getattr(result, 'quality_gate_results', [])
                if qgr:
                    stage.gate_results = list(qgr)

                errors_list = getattr(result, 'errors', []) if hasattr(result, 'errors') else result.get('errors', [])
                if errors_list:
                    for err in errors_list:
                        self._record_error(stage_name, str(err))
                self._write_stage_result_file(stage_name, result)

                return {
                    "success": not bool(errors_list),
                    "stage": stage_name,
                    "agent": stage.definition.agent,
                    "skill": stage.definition.skill,
                    "artifacts": stage.artifacts_produced,
                    "execution_mode": stage.execution_mode,
                    "outputs_verified": stage.outputs_verified,
                    "missing_outputs": stage.missing_outputs,
                }
            except Exception as e:
                self._record_error(stage_name, f"AgentDispatcher error: {e}")
                stage.status = StageStatus.FAILED
                stage.errors.append(str(e))
                self.pipeline_state = PipelineState.GATE_FAILURE
                self._write_stage_result_file(stage_name)
                return {"success": False, "stage": stage_name, "error": str(e)}

        # Fallback: basic metadata only (dispatcher unavailable)
        return {
            "success": True, "stage": stage_name,
            "agent": stage.definition.agent,
            "skill": stage.definition.skill,
        }

    def _get_default_gate_rules(self, stage_name: str, phase: int) -> list[dict]:
        """Return sensible default gate rules when none are explicitly defined."""
        if phase <= 2:  # Research & Data phases
            return [{"rule": "all_outputs_exist", "severity": "critical"}]
        elif phase == 3:  # Writing phase
            return [
                {"rule": "no_local_paths", "severity": "high"},
                {"rule": "section_length_minimum", "severity": "medium"},
                {"rule": "no_bullets_in_prose", "severity": "medium"},
            ]
        elif phase == 4:  # Assembly & Review
            return [
                {"rule": "bibtex_citation_existence", "severity": "critical"},
                {"rule": "results_no_citations", "severity": "critical"},
                {"rule": "figures_referenced", "severity": "critical"},
            ]
        else:  # Phase 5-6: Revision & Finalize
            return [
                {"rule": "data_availability_statement", "severity": "high"},
                {"rule": "code_availability_statement", "severity": "high"},
                {"rule": "figure_count_requirements", "severity": "medium"},
            ]

    def verify_stage(self, stage_name: str) -> dict:
        """Run gate checks on a completed stage using IntegrityGateChecker."""
        if stage_name not in self.stages:
            return {"passed": False, "error": f"Unknown stage: {stage_name}"}
        stage = self.stages[stage_name]
        gate_results = []
        required_outputs = stage.required_outputs or stage.definition.required_artifacts or stage.definition.produces_artifacts
        missing_outputs = [p for p in required_outputs if not self._output_exists_and_nonempty(p)]
        stage.required_outputs = list(required_outputs)
        stage.missing_outputs = missing_outputs

        if missing_outputs:
            gate_results.append({
                "rule": "required_outputs_present",
                "severity": "critical",
                "passed": False,
                "message": "Missing or empty required output(s): " + ", ".join(missing_outputs[:10]),
            })
        elif required_outputs:
            gate_results.append({
                "rule": "required_outputs_present",
                "severity": "critical",
                "passed": True,
                "message": "All required outputs exist and are non-empty",
            })

        if stage.execution_mode in {"template", "pending_harness", "needs_input"}:
            gate_results.append({
                "rule": "real_execution_required",
                "severity": "critical",
                "passed": False,
                "message": f"Stage produced {stage.execution_mode} output; not eligible for completed status",
            })
        elif required_outputs and not stage.outputs_verified and not missing_outputs:
            stage.outputs_verified = True

        # Collect manuscript sections if they exist
        sections = {}
        manuscript_dir = self.paper_dir / "manuscript"
        for sec in ["abstract", "introduction", "methods", "results", "discussion"]:
            sec_file = manuscript_dir / f"{sec}.md"
            if sec_file.exists():
                sections[sec] = sec_file.read_text(encoding="utf-8", errors="ignore")
        if not sections:
            for full_name in ["manuscript_humanized.md", "manuscript_full.md", "manuscript.md"]:
                full_path = manuscript_dir / full_name
                if full_path.exists():
                    sections["full"] = full_path.read_text(encoding="utf-8", errors="ignore")
                    break
        if not sections and stage_name == "design_analysis_plan":
            for doc_name in ["causal_assumption_audit.md"]:
                doc_path = self.paper_dir / "research_plan" / doc_name
                if doc_path.exists():
                    sections[doc_name.replace(".md", "")] = doc_path.read_text(
                        encoding="utf-8", errors="ignore"
                    )
        if not sections and stage_name == "verify_methods":
            for rel_path in ["methods/run_manifest.yaml", "data/data_audit_report.md"]:
                doc_path = self.paper_dir / rel_path
                if doc_path.exists():
                    sections[Path(rel_path).stem] = doc_path.read_text(
                        encoding="utf-8", errors="ignore"
                    )
        if stage_name == "finalize":
            for rel_path in [
                "submission/data_availability_statement.md",
                "submission/code_availability_statement.md",
                "submission/manuscript_final.md",
                "submission/cover_letter.md",
            ]:
                doc_path = self.paper_dir / rel_path
                if doc_path.exists():
                    sections[Path(rel_path).stem] = doc_path.read_text(
                        encoding="utf-8", errors="ignore"
                    )

        configured_rules = stage.definition.quality_gates or stage.definition.gate_rules

        # Run actual integrity checks if sections exist and quality gates are defined
        if sections and configured_rules:
            try:
                from paper_workflow.supervision.integrity import IntegrityGateChecker
                checker = IntegrityGateChecker(self.paper_dir)
                bibtex = self.paper_dir / "references" / "library.bib"
                gate_inputs = self._load_structured_gate_inputs()
                report = checker.run_all_checks(
                    manuscript_sections=sections,
                    bibtex_path=bibtex if bibtex.exists() else None,
                    study_design=gate_inputs.get("study_design"),
                    data_inventory=gate_inputs.get("data_inventory"),
                    statistical_plan=gate_inputs.get("statistical_plan"),
                    claim_ledger=gate_inputs.get("claim_ledger"),
                )
                # Map report results to gate_rules
                report_map = {r.rule: r for r in report.results}
                for rule_def in configured_rules:
                    rule_id = rule_def["rule"]
                    if rule_id in report_map:
                        gr = report_map[rule_id]
                        gate_results.append({
                            "rule": rule_id, "severity": rule_def["severity"],
                            "passed": gr.passed, "message": gr.message
                        })
                    else:
                        severity = str(rule_def.get("severity", "")).lower()
                        gate_results.append({
                            "rule": rule_id, "severity": rule_def["severity"],
                            "passed": severity not in {"critical", "high"},
                            "message": "Gate not executed (no matching result)"
                        })
            except Exception as e:
                self._record_error(stage_name, f"Integrity check failed: {e}")
                for rule_def in configured_rules:
                    gate_results.append({
                        "rule": rule_def["rule"], "severity": rule_def["severity"],
                        "passed": False, "message": f"Gate execution error: {e}"
                    })
        else:
            # No sections or no gate rules defined
            sd = stage.definition
            if configured_rules:
                for rule_def in configured_rules:
                    severity = str(rule_def.get("severity", "")).lower()
                    gate_results.append({
                        "rule": rule_def["rule"], "severity": rule_def.get("severity", ""),
                        "passed": severity not in {"critical", "high"},
                        "message": "Gate not executed (no input content)"
                    })
            elif not sections and sd.phase >= 3:
                gate_results.append({
                    "rule": "manuscript_sections_present", "severity": "critical",
                    "passed": False, "message": "No manuscript sections found"
                })

        stage.gate_results = gate_results
        all_passed = bool(gate_results) and all(g["passed"] for g in gate_results)
        if all_passed:
            stage.status = StageStatus.COMPLETED
            stage.completed_at = datetime.now().isoformat()
            stage.outputs_verified = True
        else:
            if stage.execution_mode in {"pending_harness", "needs_input"}:
                stage.status = StageStatus.BLOCKED
                self.pipeline_state = PipelineState.BLOCKED
            else:
                stage.status = StageStatus.FAILED
                self.pipeline_state = PipelineState.GATE_FAILURE
        self._write_stage_result_file(stage_name)
        return {"stage": stage_name, "all_passed": all_passed, "results": gate_results}

    def _output_exists_and_nonempty(self, pattern: str) -> bool:
        if "*" in pattern:
            return any(p.is_file() and p.stat().st_size > 0 for p in self.paper_dir.glob(pattern))
        full_path = self.paper_dir / pattern
        if full_path.is_dir():
            return any(p.is_file() and p.stat().st_size > 0 for p in full_path.rglob("*"))
        return full_path.is_file() and full_path.stat().st_size > 0

    def _load_structured_gate_inputs(self) -> dict[str, Any]:
        statistical_plan = self._read_yaml_first([
            self.paper_dir / "research_plan" / "statistical_analysis_plan.yaml",
            self.paper_dir / "statistical_analysis_plan.yaml",
        ])
        study_design = self._read_yaml_first([
            self.paper_dir / "research_plan" / "study_design_protocol.yaml",
            self.paper_dir / "study_design_protocol.yaml",
        ])
        data_inventory = self._read_yaml_first([
            self.paper_dir / "data" / "data_inventory.yaml",
            self.paper_dir / "data_inventory.yaml",
        ])
        if statistical_plan and not data_inventory:
            data_inventory = {
                "statistical_unit": statistical_plan.get("statistical_unit", "patient"),
                "batch_variables": statistical_plan.get("covariates", []),
            }
        claim_ledger = self._read_claim_ledger()
        return {
            "statistical_plan": statistical_plan or None,
            "study_design": study_design or None,
            "data_inventory": data_inventory or None,
            "claim_ledger": claim_ledger or None,
        }

    @staticmethod
    def _read_yaml_first(paths: list[Path]) -> dict[str, Any]:
        for path in paths:
            if not path.exists():
                continue
            try:
                data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
            except Exception:
                continue
            if isinstance(data, dict):
                return data
        return {}

    def _read_claim_ledger(self) -> list[dict[str, Any]]:
        candidates = [
            self.paper_dir / "claims" / "claim_ledger.jsonl",
            self.paper_dir / "claim_ledger.jsonl",
        ]
        claims: list[dict[str, Any]] = []
        for path in candidates:
            if not path.exists():
                continue
            for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
                line = line.strip()
                if not line:
                    continue
                try:
                    import json
                    item = json.loads(line)
                except Exception:
                    continue
                if isinstance(item, dict):
                    claims.append(item)
            if claims:
                break
        return claims

    def _record_config_error(self, message: str) -> None:
        """Record a configuration error to the paper error log."""
        try:
            error_log = self.paper_dir.parent / "error_log.md"
            if not error_log.exists():
                error_log.parent.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
            entry = (
                f"### [ERR-CFG] {timestamp} — Configuration Error\n"
                f"| Field | Value |\n|-------|-------|\n"
                f"| **Phase** | pipeline_init |\n"
                f"| **Severity** | Warning |\n"
                f"| **Status** | Resolved (fallback used) |\n"
                f"| **Message** | {message} |\n"
                f"| **Resolution** | Using hardcoded PIPELINE_STAGES as fallback |\n\n"
            )
            with open(error_log, "a", encoding="utf-8") as f:
                f.write(entry)
        except Exception:
            pass  # Error logging itself should never crash the pipeline

    def _record_error(self, stage_name: str, message: str) -> None:
        """Record a pipeline error to the paper error log."""
        try:
            error_log = self.paper_dir.parent / "error_log.md"
            error_log.parent.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
            entry = (
                f"### [ERR-ENG] {timestamp} — Pipeline Error\n"
                f"| Field | Value |\n|-------|-------|\n"
                f"| **Phase** | {stage_name} |\n"
                f"| **Severity** | Error |\n"
                f"| **Status** | Open |\n"
                f"| **Message** | {message} |\n\n"
            )
            with open(error_log, "a", encoding="utf-8") as f:
                f.write(entry)
        except Exception:
            pass  # Error logging itself should never crash the pipeline

    def record_and_sync(self) -> dict:
        """Record artifacts and sync stale stages."""
        self._record_artifact_ledger()
        stale_report = self._sync_stale()
        self._write_all_stage_result_files()
        self._update_passport()
        return {"passport_updated": True, "stale_report": stale_report}

    def _stage_result_path(self, stage_name: str) -> Path:
        return self.paper_dir / "stage_results" / f"{stage_name}_result.json"

    def _artifact_records_from_state(self, stage: StageState) -> list[dict[str, Any]]:
        records: list[dict[str, Any]] = []
        for rel_path in stage.artifacts_produced:
            if not rel_path:
                continue
            full_path = self.paper_dir / rel_path
            records.append({
                "path": rel_path,
                "hash_sha256": stage.artifact_hashes.get(rel_path, ""),
                "size_bytes": full_path.stat().st_size if full_path.exists() and full_path.is_file() else 0,
                "mime_type": "text/plain",
                "description": "",
                "version": "1.0",
                "source_stage": stage.definition.name,
            })
        return records

    def _stage_status_to_result_status(self, status: StageStatus) -> str:
        if status == StageStatus.COMPLETED:
            return "success"
        if status == StageStatus.SKIPPED:
            return "skipped"
        if status == StageStatus.FAILED:
            return "failure"
        return "warning"

    def _payload_from_stage_state(self, stage_name: str) -> dict[str, Any]:
        stage = self.stages[stage_name]
        return {
            "schema_version": "2.0.0",
            "stage_id": stage_name,
            "status": self._stage_status_to_result_status(stage.status),
            "engine_stage_status": stage.status.value,
            "engine_completed_at": stage.completed_at,
            "started_at": stage.started_at or "",
            "completed_at": stage.completed_at or "",
            "artifacts": self._artifact_records_from_state(stage),
            "metrics": {},
            "warnings": [],
            "errors": stage.errors,
            "agent_log": [],
            "retry_count": stage.retry_count,
            "checksum": "",
            "metadata": {
                "agent": stage.definition.agent,
                "skill": stage.definition.skill,
                "pipeline_state": self.pipeline_state.value,
            },
            "execution_mode": stage.execution_mode,
            "outputs_verified": stage.outputs_verified,
            "required_outputs": stage.required_outputs or stage.definition.required_artifacts,
            "missing_outputs": stage.missing_outputs,
            "quality_gate_results": stage.gate_results,
        }

    def _write_stage_result_file(self, stage_name: str, result: Any = None) -> None:
        if stage_name not in self.stages:
            return
        stage = self.stages[stage_name]
        if result is not None and hasattr(result, "to_dict"):
            try:
                payload = result.to_dict()
            except Exception:
                payload = self._payload_from_stage_state(stage_name)
        elif isinstance(result, dict):
            payload = dict(result)
        else:
            payload = self._payload_from_stage_state(stage_name)
        payload.setdefault("schema_version", "2.0.0")
        payload["stage_id"] = stage_name
        payload["engine_stage_status"] = stage.status.value
        payload["engine_completed_at"] = stage.completed_at
        payload["pipeline_state"] = self.pipeline_state.value
        payload["execution_mode"] = stage.execution_mode
        payload["outputs_verified"] = stage.outputs_verified
        payload["required_outputs"] = stage.required_outputs or stage.definition.required_artifacts
        payload["missing_outputs"] = stage.missing_outputs
        payload["quality_gate_results"] = stage.gate_results
        if not payload.get("artifacts"):
            payload["artifacts"] = self._artifact_records_from_state(stage)
        result_path = self._stage_result_path(stage_name)
        result_path.parent.mkdir(parents=True, exist_ok=True)
        result_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    def _write_all_stage_result_files(self) -> None:
        for stage_name, stage in self.stages.items():
            if stage.status not in {StageStatus.PENDING, StageStatus.RUNNING}:
                self._write_stage_result_file(stage_name)

    def _record_artifact_ledger(self) -> None:
        try:
            from paper_workflow.supervision.passport import PaperPassport
            passport = PaperPassport(self.paper_dir)
            for stage_name, stage in self.stages.items():
                for artifact_path in stage.artifacts_produced:
                    if artifact_path:
                        passport.record_artifact(artifact_path, stage_name, compute_hash=True)
        except Exception as e:
            self._record_error("artifact_ledger", f"Failed to record artifacts: {e}")

    def _update_passport(self) -> None:
        passport_path = self.paper_dir / "project_passport.yaml"
        data = {"paper_id": self.paper_id, "updated_at": datetime.now().isoformat(),
                "pipeline_state": self.pipeline_state.value,
                "stages": {n: s.to_dict() for n, s in self.stages.items()}}
        passport_path.parent.mkdir(parents=True, exist_ok=True)
        with open(passport_path, "w", encoding="utf-8") as f:
            yaml.dump(data, f, allow_unicode=True, default_flow_style=False)

    def _sync_stale(self) -> dict:
        stale_found = []
        for stage_def in self._active_stages:
            stage = self.stages[stage_def.name]
            if stage.status != StageStatus.COMPLETED:
                continue
            if any(self.stages[u].status == StageStatus.STALE for u in stage_def.upstream if u in self.stages):
                stage.status = StageStatus.STALE
                stale_found.append(stage_def.name)
        if stale_found:
            self.pipeline_state = PipelineState.STALE_STAGES
        return {"stale_stages": stale_found, "count": len(stale_found)}

    def artifact_dependency_map(self) -> dict[str, list[str]]:
        """Map each produced artifact to all downstream stages that depend on its stage."""
        dependency_map: dict[str, list[str]] = {}
        for sd in self._active_stages:
            downstream = self._transitive_downstream(sd.name)
            for artifact in sd.produces_artifacts:
                dependency_map[artifact] = downstream
        return dependency_map

    def _transitive_downstream(self, stage_name: str) -> list[str]:
        seen: set[str] = set()
        stack = list(self.stages.get(stage_name).definition.downstream if stage_name in self.stages else [])
        while stack:
            current = stack.pop(0)
            if current in seen:
                continue
            seen.add(current)
            if current in self.stages:
                stack.extend(self.stages[current].definition.downstream)
        return list(seen)

    def mark_drifted_artifact_dependents_stale(self) -> dict:
        try:
            from paper_workflow.supervision.passport import PaperPassport
            passport = PaperPassport(self.paper_dir)
            result = passport.sync_artifact_stale(self.artifact_dependency_map())
            for stage_name in result.get("stale_stages", []):
                if stage_name in self.stages:
                    self.stages[stage_name].status = StageStatus.STALE
            if result.get("stale_stages"):
                self.pipeline_state = PipelineState.STALE_STAGES
                self._update_passport()
            return result
        except Exception as e:
            self._record_error("artifact_drift", f"Failed to sync drifted artifacts: {e}")
            return {"stale_stages": [], "stale_count": 0, "error": str(e)}

    def validate_workflow(self) -> dict:
        """Validate that persisted stage truth matches artifacts and gates."""
        issues: list[dict[str, Any]] = []
        for stage_name, stage in self.stages.items():
            required_outputs = stage.required_outputs or stage.definition.required_artifacts or stage.definition.produces_artifacts
            missing = [p for p in required_outputs if not self._output_exists_and_nonempty(p)]
            result_path = self._stage_result_path(stage_name)
            persisted_result: dict[str, Any] = {}
            if result_path.exists():
                try:
                    persisted_result = json.loads(result_path.read_text(encoding="utf-8"))
                except Exception as e:
                    issues.append({
                        "stage": stage_name,
                        "code": "stage_result_unreadable",
                        "message": f"Stage result file is not valid JSON: {e}",
                    })
            if stage.status in {StageStatus.FAILED, StageStatus.BLOCKED}:
                issues.append({
                    "stage": stage_name,
                    "code": "stage_not_passed",
                    "message": f"Stage status is {stage.status.value}",
                    "details": {
                        "execution_mode": stage.execution_mode,
                        "failed_gates": [g for g in stage.gate_results if not g.get("passed", True)],
                    },
                })
            if (
                stage.status == StageStatus.COMPLETED
                and stage.definition.human_checkpoint
                and not self.checkpoint_approved(stage_name)
            ):
                issues.append({
                    "stage": stage_name,
                    "code": "checkpoint_required",
                    "message": "Human checkpoint approval is required before downstream progression",
                    "details": {"checkpoint_status": self.checkpoint_status(stage_name)},
                })
            if stage.status == StageStatus.COMPLETED:
                if not result_path.exists():
                    issues.append({
                        "stage": stage_name,
                        "code": "completed_missing_stage_result",
                        "message": "Completed stage has no stage_results JSON truth file",
                    })
                elif persisted_result.get("engine_stage_status") != StageStatus.COMPLETED.value:
                    issues.append({
                        "stage": stage_name,
                        "code": "completed_stage_result_status_mismatch",
                        "message": "Stage result file does not record completed engine status",
                        "details": {"engine_stage_status": persisted_result.get("engine_stage_status")},
                    })
                if missing:
                    issues.append({
                        "stage": stage_name,
                        "code": "completed_missing_outputs",
                        "message": "Completed stage has missing or empty required outputs",
                        "details": {"missing_outputs": missing},
                    })
                if stage.execution_mode in {"template", "pending_harness", "needs_input"}:
                    issues.append({
                        "stage": stage_name,
                        "code": "completed_non_real_execution",
                        "message": f"Completed stage has execution_mode={stage.execution_mode}",
                    })
                configured = stage.definition.quality_gates or stage.definition.gate_rules
                if configured:
                    result_rules = {g.get("rule") for g in stage.gate_results}
                    for rule_def in configured:
                        rule = rule_def.get("rule")
                        severity = str(rule_def.get("severity", "")).lower()
                        if severity in {"critical", "high"} and rule not in result_rules:
                            issues.append({
                                "stage": stage_name,
                                "code": "completed_gate_not_run",
                                "message": f"Configured {severity} gate did not produce a result: {rule}",
                            })
            elif stage.execution_mode in {"template", "pending_harness"} and stage.status == StageStatus.COMPLETED:
                issues.append({
                    "stage": stage_name,
                    "code": "pending_marked_completed",
                    "message": "Pending/template stage is marked completed",
                })

        drift_result = self.mark_drifted_artifact_dependents_stale()
        if drift_result.get("stale_stages"):
            issues.append({
                "stage": "*",
                "code": "artifact_drift_propagated",
                "message": "Artifact drift detected and downstream stages marked stale",
                "details": drift_result,
            })
        return {
            "valid": not issues,
            "issue_count": len(issues),
            "issues": issues,
            "pipeline_state": self.pipeline_state.value,
        }

    def diagnose_failures(self) -> dict:
        """Diagnose stage failures."""
        failures = []
        for name, stage in self.stages.items():
            if stage.status == StageStatus.FAILED:
                failures.append({"stage": name, "errors": stage.errors,
                                 "gate_failures": [g for g in stage.gate_results if not g.get("passed", True)],
                                 "retry_count": stage.retry_count, "max_retries": stage.definition.max_retries})
        return {"failed_stages": len(failures), "failures": failures, "revision_needed": len(failures) > 0}

    def get_status_summary(self) -> str:
        """Generate human-readable status summary."""
        lines = ["=" * 60, f"Paper: {self.paper_id}", f"State: {self.pipeline_state.value}", "=" * 60, ""]
        phases = {}
        for sd in self._active_stages:
            phases.setdefault(sd.phase, []).append(sd)
        phase_names = {1: "Research & Planning", 2: "Data & Methods", 3: "Writing",
                       4: "Assembly & Review", 5: "Revision", 6: "Finalize"}
        icons = {StageStatus.COMPLETED: "[OK]", StageStatus.RUNNING: "[..]", StageStatus.FAILED: "[FAIL]",
                 StageStatus.STALE: "[STALE]", StageStatus.PENDING: "[   ]", StageStatus.BLOCKED: "[BLOCK]",
                 StageStatus.SKIPPED: "[SKIP]"}
        for pn in sorted(phases):
            lines.append(f"Phase {pn}: {phase_names[pn]}")
            lines.append("-" * 40)
            for sd in phases[pn]:
                stage = self.stages[sd.name]
                cp = ""
                if sd.human_checkpoint:
                    status = self.checkpoint_status(sd.name)
                    cp = f" [CHECKPOINT:{status}]"
                lines.append(f"  {icons.get(stage.status, '[?]')} {sd.name}{cp}")
                if stage.errors:
                    lines.append(f"      Error: {stage.errors[-1][:60]}")
            lines.append("")
        lines.append("=" * 60)
        return "\n".join(lines)
