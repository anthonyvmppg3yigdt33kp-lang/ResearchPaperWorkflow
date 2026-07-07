"""First-class mode/profile resolver for Claude/Codex task routing.

The resolver is intentionally conservative: ambiguous requests map to a
read-only profile, analysis requests map to design first, and execution is only
selected when the request carries an approval/execution signal.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Optional

import yaml


SCHEMA_VERSION = "mode_route.v1"


MODE_FROM_PROFILE = {
    "quick_status": "exploration_mode",
    "exploratory_omics": "execution_mode",
    "analysis_design": "analysis_design_mode",
    "evidence_maturation": "execution_mode",
    "manuscript_build": "execution_mode",
    "submission_closeout": "closeout_audit_mode",
}


KNOWN_JOURNALS = (
    "Genome Biology",
    "Nature Genetics",
    "Nature Communications",
    "Nature Medicine",
    "Nature",
    "Science",
    "Cell",
    "Bioinformatics",
    "JAMA",
    "The Lancet",
)


def find_project_root(start: Optional[Path] = None) -> Path:
    """Find a repository root that contains ``config/workflow_modes.yaml``."""
    current = Path(start or Path.cwd()).resolve()
    for _ in range(12):
        if (current / "config" / "workflow_modes.yaml").exists():
            return current
        if current.parent == current:
            break
        current = current.parent
    return Path(start or Path.cwd()).resolve()


class ModeResolver:
    """Resolve a natural-language request to a workflow mode and profile."""

    def __init__(self, project_root: Optional[Path] = None):
        self.project_root = find_project_root(project_root)
        self.config_path = self.project_root / "config" / "workflow_modes.yaml"
        self.config = self._load_config()
        self.modes = self.config.get("modes", {}) or {}
        self.profiles = self.config.get("profiles", {}) or {}

    def resolve_mode(
        self,
        request_text: str,
        explicit_mode: Optional[str] = None,
        explicit_profile: Optional[str] = None,
    ) -> str:
        """Return the smallest useful mode for a request."""
        if explicit_mode:
            self._require_mode(explicit_mode)
            return explicit_mode
        if explicit_profile:
            self._require_profile(explicit_profile)
            return MODE_FROM_PROFILE.get(explicit_profile, "exploration_mode")

        text = self._normalize(request_text)

        if self._has_any(text, ("ppt", "slide", "slides", "briefing", "presentation", "汇报", "幻灯", "路演")):
            return "ppt_briefing_mode"
        if self._has_any(
            text,
            (
                "submission", "submit", "closeout", "final audit", "finalize",
                "投稿", "收尾", "定稿", "投稿前", "完整 gate", "完整检查",
            ),
        ):
            return "closeout_audit_mode"
        if self._has_any(text, ("retro", "retrospective", "prompt macro", "skill", "agent", "workflow optimize", "复盘", "习惯", "工作流优化")):
            return "retrospective_mode"
        if self._is_approved_execution(text):
            return "execution_mode"
        if self._is_analysis_design(text):
            return "analysis_design_mode"
        if self._has_any(text, ("status", "progress", "where are we", "list", "scan", "audit only", "read-only", "只读", "进展", "状态", "扫描", "检查")):
            return "exploration_mode"
        if self._has_any(text, ("continue", "run pipeline", "next step", "推进", "继续", "下一步")):
            return "execution_mode"
        return "exploration_mode"

    def resolve_profile(
        self,
        mode: str,
        request_text: str,
        explicit_profile: Optional[str] = None,
    ) -> str:
        """Return the workflow profile that should be active under ``mode``."""
        self._require_mode(mode)
        if explicit_profile:
            self._require_profile(explicit_profile)
            return explicit_profile

        text = self._normalize(request_text)
        if mode == "exploration_mode":
            return "quick_status"
        if mode == "analysis_design_mode":
            return "analysis_design"
        if mode == "ppt_briefing_mode":
            return "quick_status"
        if mode == "closeout_audit_mode":
            return "submission_closeout"
        if mode == "retrospective_mode":
            return "quick_status"
        if mode == "execution_mode":
            if self._has_any(text, ("manuscript", "paper writing", "write paper", "论文撰写", "全文", "手稿")):
                return "manuscript_build"
            if self._has_any(text, ("methods", "results", "evidence", "source map", "证据成熟", "方法", "结果")):
                return "evidence_maturation"
            return "exploratory_omics"
        return "quick_status"

    def active_layers(self, profile: str) -> list[str]:
        return list(self._profile(profile).get("active_layers") or [])

    def active_stages(self, profile: str) -> list[str]:
        return list(self._profile(profile).get("active_stages") or [])

    def deferred_stages(self, profile: str) -> list[str]:
        return list(self._profile(profile).get("deferred_stages") or [])

    def resolve_route(
        self,
        request_text: str,
        *,
        explicit_mode: Optional[str] = None,
        explicit_profile: Optional[str] = None,
        paper_id: Optional[str] = None,
        explicit_journal: Optional[str] = None,
    ) -> dict[str, Any]:
        """Return a JSON-serializable routing packet for CLI and AI harnesses."""
        mode = self.resolve_mode(request_text, explicit_mode=explicit_mode, explicit_profile=explicit_profile)
        profile = self.resolve_profile(mode, request_text, explicit_profile=explicit_profile)
        mode_spec = self.modes.get(mode, {}) or {}
        profile_spec = self.profiles.get(profile, {}) or {}
        journal_policy = self._journal_policy(
            request_text,
            mode=mode,
            profile=profile,
            explicit_journal=explicit_journal,
        )
        return {
            "schema_version": SCHEMA_VERSION,
            "project_root": str(self.project_root),
            "paper_id": paper_id or "",
            "request": request_text,
            "mode": mode,
            "profile": profile,
            "active_layers": self.active_layers(profile),
            "active_stages": self.active_stages(profile),
            "deferred_stages": self.deferred_stages(profile),
            "output_contract": profile_spec.get("output_contract", ""),
            "default_writes": list(mode_spec.get("default_writes") or []),
            "forbidden_actions": list(mode_spec.get("forbidden_actions") or []),
            "human_checkpoint_required": bool(mode_spec.get("human_checkpoint_required", False)),
            "journal_policy": journal_policy,
            "execution_allowed": mode == "execution_mode",
            "analysis_allowed": mode == "execution_mode" and "run_analysis" in self.active_stages(profile),
        }

    def _journal_policy(
        self,
        request_text: str,
        *,
        mode: str,
        profile: str,
        explicit_journal: Optional[str],
    ) -> dict[str, Any]:
        journal = (explicit_journal or "").strip() or self.detect_explicit_journal(request_text)
        exploratory = mode in {"exploration_mode", "analysis_design_mode"} or profile in {"quick_status", "analysis_design", "exploratory_omics"}
        if journal:
            return {
                "explicit_target_journal": journal,
                "final_target_journal_allowed_now": True,
                "final_target_journal_required_now": True,
                "candidate_journal_class_only": False,
                "defer_final_target_journal_to": [],
            }
        return {
            "explicit_target_journal": "",
            "final_target_journal_allowed_now": not exploratory,
            "final_target_journal_required_now": False,
            "candidate_journal_class_only": exploratory,
            "candidate_journal_class": self._candidate_journal_class(request_text),
            "defer_final_target_journal_to": ["evidence_maturation", "submission_closeout"] if exploratory else [],
        }

    def detect_explicit_journal(self, request_text: str) -> str:
        text = request_text or ""
        lowered = text.lower()
        for journal in KNOWN_JOURNALS:
            if journal.lower() in lowered:
                return journal
        match = re.search(
            r"(?:target\s+journal|journal|期刊|投稿到|投到|目标期刊)\s*[:：=为到]?\s*([A-Z][A-Za-z0-9 &().,-]{2,80})",
            text,
        )
        return match.group(1).strip(" .;，。") if match else ""

    def _candidate_journal_class(self, request_text: str) -> str:
        text = self._normalize(request_text)
        if self._has_any(text, ("nature", "science", "cell", "cns", "top journal", "高分", "顶刊")):
            return "high_impact_biomedical"
        if self._has_any(text, ("bioinformatics", "single-cell", "scrna", "spatial", "omics", "生信", "单细胞", "空间")):
            return "computational_biology_or_omics"
        if self._has_any(text, ("clinical", "cohort", "patient", "临床", "队列", "患者")):
            return "clinical_or_translational"
        return "to_be_selected_after_evidence_maturation"

    def _is_approved_execution(self, text: str) -> bool:
        approval_terms = (
            "approved", "approve", "confirmed", "go ahead", "execute", "run analysis",
            "run-analysis", "bounded command", "已批准", "确认执行", "开始运行", "执行分析", "运行代码",
        )
        return self._has_any(text, approval_terms)

    def _is_analysis_design(self, text: str) -> bool:
        design_terms = (
            "analysis design", "design analysis", "plan analysis", "sap", "statistical analysis plan",
            "bulk", "rnaseq", "rna-seq", "scrna", "single-cell", "spatial", "multiomics",
            "deseq2", "scanpy", "squidpy", "wgcna", "lasso", "xgboost",
            "分析设计", "分析方案", "统计分析计划", "差异分析", "单细胞", "空间转录组", "多组学",
        )
        return self._has_any(text, design_terms)

    def _profile(self, profile: str) -> dict[str, Any]:
        self._require_profile(profile)
        return self.profiles.get(profile, {}) or {}

    def _require_mode(self, mode: str) -> None:
        if mode not in self.modes:
            raise ValueError(f"Unknown workflow mode: {mode}")

    def _require_profile(self, profile: str) -> None:
        if profile not in self.profiles:
            raise ValueError(f"Unknown workflow profile: {profile}")

    def _load_config(self) -> dict[str, Any]:
        path = self.config_path
        if not path.exists():
            package_default = Path(__file__).resolve().parents[3] / "config" / "workflow_modes.yaml"
            if package_default.exists():
                path = package_default
            else:
                raise FileNotFoundError(f"Missing workflow modes config: {self.config_path}")
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        if not isinstance(data, dict):
            raise ValueError(f"Invalid workflow modes config: {self.config_path}")
        return data

    @staticmethod
    def _normalize(request_text: str) -> str:
        return re.sub(r"\s+", " ", (request_text or "").lower()).strip()

    @staticmethod
    def _has_any(text: str, needles: tuple[str, ...]) -> bool:
        return any(needle.lower() in text for needle in needles)


def _default_resolver() -> ModeResolver:
    return ModeResolver()


def resolve_mode(
    request_text: str,
    explicit_mode: Optional[str] = None,
    explicit_profile: Optional[str] = None,
) -> str:
    return _default_resolver().resolve_mode(request_text, explicit_mode, explicit_profile)


def resolve_profile(mode: str, request_text: str) -> str:
    return _default_resolver().resolve_profile(mode, request_text)


def active_layers(profile: str) -> list[str]:
    return _default_resolver().active_layers(profile)


def active_stages(profile: str) -> list[str]:
    return _default_resolver().active_stages(profile)


def deferred_stages(profile: str) -> list[str]:
    return _default_resolver().deferred_stages(profile)
