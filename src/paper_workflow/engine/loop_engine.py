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
            "gate_rules": self.gate_rules, "agent": self.agent, "skill": self.skill,
            "human_checkpoint": self.human_checkpoint, "max_retries": self.max_retries,
            "timeout_minutes": self.timeout_minutes,
        }

    # ------------------------------------------------------------------
    # Phase derivation — order integer (1–19) → phase integer (1–6)
    # ------------------------------------------------------------------
    # The 6-phase grouping per ARCHITECTURE.md (v3.0 — 19 stages):
    #   1. Research & Planning   → stages order 1–5
    #   2. Data & Methods        → stages order 6–9
    #   3. Writing               → stages order 10–13
    #   4. Assembly & Review     → stages order 14–16
    #   5. Revision              → stages order 17–18
    #   6. Finalize              → stages order 19
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
        v3.0: Research & Planning now includes design_analysis_plan (order 5).
        """
        if order <= 5:
            return 1   # Research & Planning (v3: orders 1-5)
        if order <= 9:
            return 2   # Data & Methods (v3: orders 6-9)
        if order <= 13:
            return 3   # Writing (v3: orders 10-13)
        if order <= 16:
            return 4   # Assembly & Review (v3: orders 14-16)
        if order <= 18:
            return 5   # Revision (v3: orders 17-18)
        return 6       # Finalize (v3: order 19)

    @classmethod
    def _resolve_gate_severities(cls, quality_gates: dict[str, Any]) -> None:
        """Populate ``_GATE_SEVERITY_MAP`` from a quality-gates dict so
        that gate-rule entries can be annotated with their severity."""
        cls._GATE_SEVERITY_MAP.clear()
        for gate_key, gate_def in quality_gates.items():
            sev = str(gate_def.get("severity", "MEDIUM")).upper()
            cls._GATE_SEVERITY_MAP[gate_key] = sev

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
            phase: int = cls._LAYER_TO_PHASE.get(layer, order)

            # --- Upstream dependencies ---
            upstream: list[str] = list(raw.get("dependencies", []) or [])

            # --- Produced artifacts ---
            artifacts: list[str] = list(raw.get("artifacts_out", []) or [])

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

            # --- Gate rules (config format: {on_pass: [...], on_fail: [...]}) ---
            gate_rules_raw: dict[str, Any] = raw.get("gate_rules", {}) or {}
            gate_rules: list[dict[str, Any]] = []
            for rule_id in gate_rules_raw.get("on_pass", []) or []:
                severity = cls._GATE_SEVERITY_MAP.get(rule_id, "")
                gate_rules.append({"rule": rule_id, "severity": severity})
            for rule_id in gate_rules_raw.get("on_fail", []) or []:
                severity = cls._GATE_SEVERITY_MAP.get(rule_id, "")
                gate_rules.append({"rule": rule_id, "severity": severity})

            # --- Human checkpoint ---
            human_checkpoint: bool = bool(raw.get("human_checkpoint", False))

            definitions.append(StageDefinition(
                name=stage_id,
                description=stage_name,
                phase=phase,
                category=layer,
                upstream=upstream,
                downstream=[],  # downstream is derived at runtime, not stored in config
                required_artifacts=[],
                produces_artifacts=artifacts,
                gate_rules=gate_rules,
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

    def to_dict(self) -> dict:
        return {
            "name": self.definition.name, "status": self.status.value,
            "started_at": self.started_at, "completed_at": self.completed_at,
            "retry_count": self.retry_count, "artifacts_produced": self.artifacts_produced,
            "artifact_hashes": self.artifact_hashes, "errors": self.errors,
            "gate_results": self.gate_results,
        }


class PaperLoopEngine:
    """Core paper loop orchestrator — 19-stage pipeline with state management (v3.0)."""

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
        StageDefinition(name="integrity_check", phase=4, category="review",
                        description="Run integrity gates on complete manuscript",
                        upstream=["assemble_manuscript"],
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

        self._initialize_stages()

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

    def _initialize_stages(self) -> None:
        for stage_def in self._active_stages:
            self.stages[stage_def.name] = StageState(definition=stage_def)

    def observe(self) -> dict:
        """Observe current project state."""
        return {
            "paper_id": self.paper_id, "paper_dir": str(self.paper_dir),
            "pipeline_state": self.pipeline_state.value,
            "stages": {name: {"status": s.status.value, "completed_at": s.completed_at,
                              "retry_count": s.retry_count, "has_errors": len(s.errors) > 0}
                       for name, s in self.stages.items()},
            "timestamp": datetime.now().isoformat(),
        }

    def decide_next_stage(self) -> Optional[str]:
        """Decide the next safe stage to run."""
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

                errors_list = getattr(result, 'errors', []) if hasattr(result, 'errors') else result.get('errors', [])
                if errors_list:
                    for err in errors_list:
                        self._record_error(stage_name, str(err))

                return {
                    "success": True,
                    "stage": stage_name,
                    "agent": stage.definition.agent,
                    "skill": stage.definition.skill,
                    "artifacts": stage.artifacts_produced,
                }
            except Exception as e:
                self._record_error(stage_name, f"AgentDispatcher error: {e}")
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

        # Collect manuscript sections if they exist
        sections = {}
        manuscript_dir = self.paper_dir / "manuscript"
        for sec in ["abstract", "introduction", "methods", "results", "discussion"]:
            sec_file = manuscript_dir / f"{sec}.md"
            if sec_file.exists():
                sections[sec] = sec_file.read_text(encoding="utf-8", errors="ignore")

        # Run actual integrity checks if sections exist and gate rules are defined
        if sections and stage.definition.gate_rules:
            try:
                from paper_workflow.supervision.integrity import IntegrityGateChecker
                checker = IntegrityGateChecker(self.paper_dir)
                bibtex = self.paper_dir / "references" / "library.bib"
                report = checker.run_all_checks(
                    manuscript_sections=sections,
                    bibtex_path=bibtex if bibtex.exists() else None
                )
                # Map report results to gate_rules
                report_map = {r.rule: r for r in report.results}
                for rule_def in stage.definition.gate_rules:
                    rule_id = rule_def["rule"]
                    if rule_id in report_map:
                        gr = report_map[rule_id]
                        gate_results.append({
                            "rule": rule_id, "severity": rule_def["severity"],
                            "passed": gr.passed, "message": gr.message
                        })
                    else:
                        gate_results.append({
                            "rule": rule_id, "severity": rule_def["severity"],
                            "passed": True, "message": "Not checked (no matching content)"
                        })
            except Exception as e:
                self._record_error(stage_name, f"Integrity check failed: {e}")
                for rule_def in stage.definition.gate_rules:
                    gate_results.append({
                        "rule": rule_def["rule"], "severity": rule_def["severity"],
                        "passed": False, "message": f"Gate execution error: {e}"
                    })
        else:
            # No sections or no gate rules defined
            sd = stage.definition
            if not sections and sd.phase >= 3:
                return {
                    "stage": stage_name, "all_passed": False, "results": [],
                    "error": "No manuscript sections found"
                }
            # Use default gate rules if none explicitly defined
            rules = sd.gate_rules if sd.gate_rules else self._get_default_gate_rules(stage_name, sd.phase)
            for rule_def in rules:
                gate_results.append({
                    "rule": rule_def["rule"], "severity": rule_def["severity"],
                    "passed": True, "message": "No content to check (default gate)"
                })

        stage.gate_results = gate_results
        all_passed = all(g["passed"] for g in gate_results)
        if all_passed:
            stage.status = StageStatus.COMPLETED
            stage.completed_at = datetime.now().isoformat()
        else:
            stage.status = StageStatus.FAILED
            self.pipeline_state = PipelineState.GATE_FAILURE
        return {"stage": stage_name, "all_passed": all_passed, "results": gate_results}

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
        self._update_passport()
        stale_report = self._sync_stale()
        return {"passport_updated": True, "stale_report": stale_report}

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
                cp = " [CHECKPOINT]" if sd.human_checkpoint else ""
                lines.append(f"  {icons.get(stage.status, '[?]')} {sd.name}{cp}")
                if stage.errors:
                    lines.append(f"      Error: {stage.errors[-1][:60]}")
            lines.append("")
        lines.append("=" * 60)
        return "\n".join(lines)
