"""
Config Loader — Loads and caches default_config.yaml for the Paper Workflow engine.

Provides typed accessors for all 8 major config sections:
  pipeline / paper_types / quality_gates / writing_standards /
  research_domains / skills_dispatcher / agent_routing / supervision

On init, loads the YAML file once and caches the parsed dict. Every getter
returns the cached data (or a filtered subset). If the config file is missing,
sensible defaults are returned instead of raising.
"""

from __future__ import annotations

import copy
from pathlib import Path
from typing import Any, Optional

import yaml

# Default project root is the grandparent of this file's directory:
#   utils/config_loader.py  -->  utils/  -->  paper_workflow/  -->  src/  -->  project_root/
_DEFAULT_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
_DEFAULT_CONFIG_PATH = _DEFAULT_PROJECT_ROOT / "config" / "default_config.yaml"

# ---------------------------------------------------------------------------
# Sensible defaults returned when the config file is absent
# ---------------------------------------------------------------------------
_FALLBACK_PIPELINE_STAGES: list[dict[str, Any]] = [
    {
        "id": "create_project", "name": "Initialize Project", "layer": "strategy",
        "order": 1, "agent": "research_strategist", "skills": ["topic_research"],
        "timeout_seconds": 600, "dependencies": [], "artifacts_out": ["project_passport.yaml"],
        "human_checkpoint": True, "retry": {"max_attempts": 3},
    },
]

_FALLBACK_QUALITY_GATES: dict[str, Any] = {
    "critical": [],
    "high": [],
    "medium": [],
}

_FALLBACK_WRITING_STANDARDS: dict[str, Any] = {
    "structure": "IMRAD",
    "citation_style_default": "Vancouver",
    "language": "English (US)",
    "reference_manager": "BibTeX",
    "sections": {},
    "formatting": {},
    "language_rules": {},
}

_FALLBACK_PAPER_TYPE: dict[str, Any] = {
    "name": "Original Research Article",
    "pipeline_mode": "full",
    "required_stages": [],
    "skipped_stages": [],
    "structure": ["abstract", "introduction", "methods", "results", "discussion"],
}

_FALLBACK_RESEARCH_DOMAIN: dict[str, Any] = {
    "name": "General",
    "keywords": {"primary": [], "secondary": []},
    "common_methods": [],
    "common_pitfalls": [],
}

_FALLBACK_SKILLS_DISPATCHER: dict[str, Any] = {}

_FALLBACK_AGENT_ROUTING: dict[str, Any] = {
    "routing_strategy": "best_match_with_fallback",
    "fallback_agent": "team_orchestrator",
    "agents": {},
}


class ConfigLoader:
    """Load and cache the workflow configuration from default_config.yaml.

    Usage::

        cl = ConfigLoader()                        # auto-locates config/default_config.yaml
        cl = ConfigLoader(config_path=Path(...))   # explicit path
        cl = ConfigLoader(auto_discover=False)     # empty config, use at own risk

    All getter methods return deep-copies so callers cannot accidentally
    mutate the cached config.
    """

    def __init__(
        self,
        config_path: Optional[Path] = None,
        auto_discover: bool = True,
    ) -> None:
        """Initialise the loader.

        Parameters
        ----------
        config_path:
            Explicit path to a YAML config file. When ``None`` and
            *auto_discover* is ``True``, the default location
            ``<project_root>/config/default_config.yaml`` is used.
        auto_discover:
            If ``True`` (default), locate the config automatically when
            *config_path* is not provided.
        """
        self._config_path: Optional[Path] = config_path
        self._config: Optional[dict[str, Any]] = None

        if auto_discover and self._config_path is None:
            candidate = _DEFAULT_CONFIG_PATH
            if candidate.exists():
                self._config_path = candidate

        if self._config_path is not None and self._config_path.exists():
            self._load()
        # else: config stays None; getters return fallbacks

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _load(self) -> None:
        """Parse the YAML file and cache the result."""
        with open(self._config_path, "r", encoding="utf-8") as fh:
            self._config = yaml.safe_load(fh)

    def _ensure_loaded(self) -> bool:
        """Try a one-shot load if config was not loaded at init time.
        Returns ``True`` when config data is available.
        """
        if self._config is not None:
            return True
        if self._config_path is not None and self._config_path.exists():
            self._load()
            return self._config is not None
        return False

    # ------------------------------------------------------------------
    # Public API — 7 accessors
    # ------------------------------------------------------------------

    def get_pipeline_stages(self) -> list[dict[str, Any]]:
        """Return the ordered list of pipeline stage definitions.

        Each dict mirrors the YAML schema (keys: ``id``, ``name``, ``layer``,
        ``order``, ``agent``, ``skills``, ``timeout_seconds``, ``dependencies``,
        ``parallel_group``, ``retry``, ``artifacts_out``, ``gate_rules``,
        ``human_checkpoint``, ``checkpoint_prompt``).
        """
        if not self._ensure_loaded():
            return copy.deepcopy(_FALLBACK_PIPELINE_STAGES)
        stages = self._config.get("pipeline", {}).get("stages", [])
        if not stages:
            return copy.deepcopy(_FALLBACK_PIPELINE_STAGES)
        return copy.deepcopy(stages)

    def get_paper_type(self, type_name: str) -> dict[str, Any]:
        """Return configuration for a specific paper type.

        Parameters
        ----------
        type_name:
            One of ``original_research``, ``methods``, ``review``,
            ``clinical_research``, ``data_resource``, ``brief_communication``.

        Returns
        -------
        dict
            Paper-type config or fallback if the name is unknown.
        """
        if not self._ensure_loaded():
            return copy.deepcopy(_FALLBACK_PAPER_TYPE)
        paper_types = self._config.get("paper_types", {})
        result = paper_types.get(type_name)
        if result is None:
            return copy.deepcopy(_FALLBACK_PAPER_TYPE)
        return copy.deepcopy(result)

    def get_quality_gates(self) -> dict[str, list[dict[str, Any]]]:
        """Return quality gates grouped by severity level.

        Returns
        -------
        dict
            Keys ``critical``, ``high``, ``medium``. Each value is a list of
            gate definition dicts.
        """
        if not self._ensure_loaded():
            return copy.deepcopy(_FALLBACK_QUALITY_GATES)

        raw_gates: dict[str, Any] = self._config.get("quality_gates", {})
        buckets: dict[str, list[dict[str, Any]]] = {
            "critical": [],
            "high": [],
            "medium": [],
        }
        for gate_key, gate_def in raw_gates.items():
            gate_copy = copy.deepcopy(gate_def)
            gate_copy.setdefault("id", gate_key)
            severity = str(gate_copy.get("severity", "MEDIUM")).lower()
            if severity not in buckets:
                severity = "medium"
            buckets[severity].append(gate_copy)
        return buckets

    def get_writing_standards(self) -> dict[str, Any]:
        """Return writing standards (structure, sections, formatting, language rules)."""
        if not self._ensure_loaded():
            return copy.deepcopy(_FALLBACK_WRITING_STANDARDS)
        return copy.deepcopy(self._config.get("writing_standards", _FALLBACK_WRITING_STANDARDS))

    def get_research_domain(self, domain_name: str) -> dict[str, Any]:
        """Return configuration for a specific research domain.

        Parameters
        ----------
        domain_name:
            Key in the ``research_domains`` map (e.g. ``bioinformatics``).
        """
        if not self._ensure_loaded():
            return copy.deepcopy(_FALLBACK_RESEARCH_DOMAIN)
        domains = self._config.get("research_domains", {})
        result = domains.get(domain_name)
        if result is None:
            return copy.deepcopy(_FALLBACK_RESEARCH_DOMAIN)
        return copy.deepcopy(result)

    def get_skills_dispatcher_rules(self) -> dict[str, Any]:
        """Return the skills dispatcher configuration (trigger rules per skill)."""
        if not self._ensure_loaded():
            return copy.deepcopy(_FALLBACK_SKILLS_DISPATCHER)
        return copy.deepcopy(self._config.get("skills_dispatcher", {}))

    def get_agent_routing(self) -> dict[str, Any]:
        """Return agent routing configuration (task-to-agent mapping)."""
        if not self._ensure_loaded():
            return copy.deepcopy(_FALLBACK_AGENT_ROUTING)
        return copy.deepcopy(self._config.get("agent_routing", _FALLBACK_AGENT_ROUTING))

    def get_supervision(self) -> dict[str, Any]:
        """Return supervision layer config (timeout, retry, fuse, logging)."""
        if not self._ensure_loaded():
            return {}
        return copy.deepcopy(self._config.get("supervision", {}))

    @property
    def config_path(self) -> Optional[Path]:
        """The resolved config file path, or ``None``."""
        return self._config_path

    @property
    def is_loaded(self) -> bool:
        """``True`` when the config was successfully parsed."""
        return self._config is not None
