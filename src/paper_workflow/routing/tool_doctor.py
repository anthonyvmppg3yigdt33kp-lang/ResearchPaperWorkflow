"""Local tool, skill, and agent availability checks.

This checker separates repo-controlled failures from external capability drift.
Bundled skill and agent source files are strict. Optional tools such as a
fast-context MCP server are reported with fallbacks instead of failing CI.
"""
from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path
from typing import Any, Optional

import yaml

from paper_workflow.routing.mode_resolver import find_project_root
from paper_workflow.utils.skill_installer import get_compare_roots, load_required_skills, skill_exists


class ToolDoctor:
    """Run repository capability checks for Codex/Claude operation."""

    def __init__(self, project_root: Optional[Path] = None):
        self.project_root = find_project_root(project_root)

    def run(self) -> dict[str, Any]:
        tools = self.check_tools()
        skills = self.check_skills()
        agents = self.check_agents()
        required_failures = []
        if skills["missing_bundled_sources"]:
            required_failures.append("missing bundled skill sources")
        if agents["missing_agent_files"]:
            required_failures.append("missing configured agent files")

        degraded = []
        if tools["fast_context"]["status"] != "available":
            degraded.append("fast-context unavailable; using fallback search")
        if not tools["search_fallback"]["rg_available"]:
            degraded.append("rg unavailable; using Python file scan fallback")
        if skills["missing_local_installs"]:
            degraded.append("some bundled skills are installable but not present in local skill roots")

        status = "fail" if required_failures else ("degraded" if degraded else "pass")
        return {
            "schema_version": "tool_doctor.v1",
            "project_root": str(self.project_root),
            "status": status,
            "required_failures": required_failures,
            "degraded": degraded,
            "tools": tools,
            "skills": skills,
            "agents": agents,
            "fallback_policy": {
                "semantic_code_search": [
                    "mcp__fast-context__fast_context_search when callable",
                    "rg --line-number for exact and suggested keywords",
                    "direct file reads for cited ranges",
                    "Python pathlib scan only when rg is unavailable",
                ],
                "skill_repair": "Run paper-workflow install-skills for bundled skills; install external MCP/plugins separately.",
            },
        }

    def check_tools(self) -> dict[str, Any]:
        fast_context_available = self._fast_context_available()
        return {
            "python": {
                "available": True,
                "executable": sys.executable,
                "version": sys.version.split()[0],
            },
            "git": self._command_status("git"),
            "gh": self._command_status("gh"),
            "rg": self._command_status("rg"),
            "fast_context": {
                "status": "available" if fast_context_available else "unavailable",
                "mcp_tool": "mcp__fast-context__fast_context_search",
                "detection": "PAPER_WORKFLOW_FAST_CONTEXT_AVAILABLE=1 or fast-context executable on PATH",
                "fallback": "Use rg plus direct file reads until the MCP tool is exposed to the session.",
            },
            "search_fallback": {
                "rg_available": shutil.which("rg") is not None,
                "python_file_scan_available": True,
            },
        }

    def check_skills(self) -> dict[str, Any]:
        records = load_required_skills(self.project_root)
        roots = get_compare_roots([self.project_root / ".agents" / "skills", self.project_root / ".claude" / "skills"])
        missing_sources: list[dict[str, str]] = []
        missing_local: list[dict[str, str]] = []
        present_local: list[str] = []
        for record in records:
            name = str(record.get("name", "")).strip()
            if not name:
                continue
            rel = record.get("path") or f".claude/skills/{name}.md"
            source_path = self.project_root / str(rel)
            if not source_path.exists():
                missing_sources.append({"name": name, "path": str(source_path)})
            if skill_exists(name, roots):
                present_local.append(name)
            else:
                missing_local.append({"name": name, "install_hint": "paper-workflow install-skills"})

        required_agent_skills = [
            "workflow-light-mode",
            "bioinformatics-analysis-design",
            "research-ppt-briefing",
            "result-run-management",
            "codex-self-audit",
        ]
        missing_agent_skill_mirrors = [
            name
            for name in required_agent_skills
            if not (self.project_root / ".agents" / "skills" / name / "SKILL.md").exists()
        ]
        return {
            "required_count": len(records),
            "local_roots": [str(root) for root in roots],
            "present_local_count": len(present_local),
            "present_local": sorted(present_local),
            "missing_bundled_sources": missing_sources,
            "missing_local_installs": missing_local,
            "required_agent_skill_mirrors": required_agent_skills,
            "missing_agent_skill_mirrors": missing_agent_skill_mirrors,
        }

    def check_agents(self) -> dict[str, Any]:
        config_path = self.project_root / "config" / "default_config.yaml"
        config = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
        configured = sorted(((config.get("agent_routing") or {}).get("agents") or {}).keys())
        agent_dir = self.project_root / ".claude" / "agents"
        available = sorted(path.stem for path in agent_dir.glob("*.md")) if agent_dir.exists() else []
        missing = sorted(set(configured) - set(available))
        extra = sorted(set(available) - set(configured))
        return {
            "configured_count": len(configured),
            "available_count": len(available),
            "configured_agents": configured,
            "available_agent_files": available,
            "missing_agent_files": missing,
            "extra_agent_files": extra,
        }

    @staticmethod
    def _command_status(command: str) -> dict[str, Any]:
        path = shutil.which(command)
        return {
            "available": path is not None,
            "path": path or "",
        }

    @staticmethod
    def _fast_context_available() -> bool:
        env_value = os.environ.get("PAPER_WORKFLOW_FAST_CONTEXT_AVAILABLE", "").strip().lower()
        if env_value in {"1", "true", "yes"}:
            return True
        return shutil.which("fast-context") is not None


def format_doctor_report(report: dict[str, Any]) -> str:
    """Format a doctor report for CLI humans."""
    lines = [
        f"[DOCTOR] status={report.get('status')} project={report.get('project_root')}",
        f"  required failures: {len(report.get('required_failures', []))}",
        f"  degraded: {len(report.get('degraded', []))}",
    ]
    for item in report.get("required_failures", []):
        lines.append(f"    ! {item}")
    for item in report.get("degraded", []):
        lines.append(f"    - {item}")
    tools = report.get("tools", {})
    for name in ("python", "git", "gh", "rg"):
        spec = tools.get(name, {})
        available = spec.get("available", False)
        detail = spec.get("path") or spec.get("executable") or ""
        lines.append(f"  tool {name}: {'ok' if available else 'missing'} {detail}")
    fast = tools.get("fast_context", {})
    lines.append(f"  tool fast-context: {fast.get('status')} | fallback: {fast.get('fallback')}")
    skills = report.get("skills", {})
    lines.append(
        "  skills: "
        f"required={skills.get('required_count', 0)} "
        f"present_local={skills.get('present_local_count', 0)} "
        f"missing_sources={len(skills.get('missing_bundled_sources', []))} "
        f"missing_local={len(skills.get('missing_local_installs', []))}"
    )
    agents = report.get("agents", {})
    lines.append(
        "  agents: "
        f"configured={agents.get('configured_count', 0)} "
        f"available={agents.get('available_count', 0)} "
        f"missing={len(agents.get('missing_agent_files', []))}"
    )
    return "\n".join(lines)
