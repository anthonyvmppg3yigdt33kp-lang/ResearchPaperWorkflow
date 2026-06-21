"""Skill discovery and installer helpers for ResearchPaperWorkflow V4.

The workflow keeps repo-owned Claude/Codex skills under ``.claude/skills``.
This module compares those bundled skills with local agent skill roots and can
copy missing bundled skills into a user's local skill directory.
"""
from __future__ import annotations

import os
import shutil
from pathlib import Path
from typing import Any

import yaml


DEFAULT_TARGET_ROOT = Path.home() / ".codex" / "skills"
DEFAULT_COMPARE_ROOTS = [
    Path.home() / ".codex" / "skills",
    Path.home() / ".agents" / "skills",
    Path.home() / ".claude" / "skills",
]


def find_project_root(start: Path | None = None) -> Path:
    """Find the repository root from a working directory."""
    current = Path(start or Path.cwd()).resolve()
    for _ in range(12):
        if (current / "config" / "required_skills.yaml").exists():
            return current
        if (current / ".claude" / "skills").exists() and (
            (current / "pyproject.toml").exists() or (current / "AGENTS.md").exists()
        ):
            return current
        if current.parent == current:
            break
        current = current.parent
    return Path(start or Path.cwd()).resolve()


def _split_env_paths(value: str) -> list[Path]:
    paths: list[Path] = []
    for raw in value.split(os.pathsep):
        raw = raw.strip()
        if raw:
            paths.append(Path(raw).expanduser())
    return paths


def get_compare_roots(extra_roots: list[Path] | None = None) -> list[Path]:
    """Return local skill roots used for comparison."""
    roots: list[Path] = []
    env_roots = os.environ.get("PAPER_WORKFLOW_SKILL_ROOTS")
    if env_roots:
        roots.extend(_split_env_paths(env_roots))
    roots.extend(extra_roots or [])
    roots.extend(DEFAULT_COMPARE_ROOTS)

    seen: set[str] = set()
    unique: list[Path] = []
    for root in roots:
        resolved = Path(root).expanduser()
        key = str(resolved).lower()
        if key not in seen:
            seen.add(key)
            unique.append(resolved)
    return unique


def load_required_skills(project_root: Path | None = None) -> list[dict[str, Any]]:
    """Load required skill records from config/required_skills.yaml.

    If the manifest is absent, fall back to every Markdown skill bundled in
    ``.claude/skills``.
    """
    root = find_project_root(project_root)
    manifest = root / "config" / "required_skills.yaml"
    if manifest.exists():
        data = yaml.safe_load(manifest.read_text(encoding="utf-8")) or {}
        return list(data.get("skills", []) or [])

    bundled_dir = root / ".claude" / "skills"
    if not bundled_dir.exists():
        return []
    return [
        {"name": p.stem, "source": "bundled", "path": str(p.relative_to(root))}
        for p in sorted(bundled_dir.glob("*.md"))
    ]


def skill_exists(name: str, roots: list[Path]) -> bool:
    """Check common Codex/Claude skill layouts for a skill name."""
    candidates: list[Path] = []
    for root in roots:
        candidates.extend([
            root / name / "SKILL.md",
            root / name / "skill.md",
            root / f"{name}.md",
        ])
    return any(path.exists() for path in candidates)


def _bundled_source_path(project_root: Path, record: dict[str, Any]) -> Path | None:
    rel = record.get("path") or f".claude/skills/{record.get('name', '')}.md"
    path = project_root / rel
    if path.exists():
        return path
    fallback = project_root / ".claude" / "skills" / f"{record.get('name', '')}.md"
    return fallback if fallback.exists() else None


def install_missing_skills(
    project_root: Path | None = None,
    target_root: Path | None = None,
    compare_roots: list[Path] | None = None,
    check_only: bool = False,
    force: bool = False,
) -> dict[str, Any]:
    """Compare and optionally install missing bundled skills.

    Returns a JSON-serializable report with installed, already_present,
    missing_bundled, and missing_external entries.
    """
    root = find_project_root(project_root)
    target = Path(
        target_root
        or os.environ.get("PAPER_WORKFLOW_SKILL_TARGET", "")
        or DEFAULT_TARGET_ROOT
    ).expanduser()
    roots = get_compare_roots(compare_roots)
    if target not in roots:
        roots.insert(0, target)

    report: dict[str, Any] = {
        "project_root": str(root),
        "target_root": str(target),
        "compare_roots": [str(p) for p in roots],
        "installed": [],
        "already_present": [],
        "missing_bundled": [],
        "missing_external": [],
        "check_only": check_only,
        "force": force,
    }

    for record in load_required_skills(root):
        name = str(record.get("name", "")).strip()
        if not name:
            continue
        present = skill_exists(name, roots)
        if present and not force:
            report["already_present"].append(name)
            continue

        source = str(record.get("source", "bundled"))
        if source != "bundled":
            if present:
                report["already_present"].append(name)
                continue
            report["missing_external"].append({
                "name": name,
                "install_hint": record.get("install_hint", "Install this skill manually."),
            })
            continue

        src = _bundled_source_path(root, record)
        if src is None:
            report["missing_bundled"].append({"name": name, "reason": "Bundled source file not found"})
            continue
        if check_only:
            report["missing_bundled"].append({"name": name, "source": str(src)})
            continue

        dest_dir = target / name
        dest_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dest_dir / "SKILL.md")
        report["installed"].append({"name": name, "path": str(dest_dir / "SKILL.md")})

    return report


def ensure_skills_available(
    project_root: Path | None = None,
    auto_install: bool = True,
    quiet: bool = True,
) -> dict[str, Any]:
    """Lightweight startup hook used by the CLI."""
    if os.environ.get("PAPER_WORKFLOW_SKIP_SKILL_CHECK") == "1":
        return {"skipped": True, "reason": "PAPER_WORKFLOW_SKIP_SKILL_CHECK=1"}
    report = install_missing_skills(project_root=project_root, check_only=not auto_install)
    if not quiet:
        print(format_skill_report(report))
    return report


def format_skill_report(report: dict[str, Any]) -> str:
    """Format an installer report for humans."""
    if report.get("skipped"):
        return f"[SKILLS] Skipped: {report.get('reason', '')}"
    lines = [
        "[SKILLS] ResearchPaperWorkflow skill check",
        f"  project: {report.get('project_root')}",
        f"  target:  {report.get('target_root')}",
        f"  present: {len(report.get('already_present', []))}",
        f"  installed: {len(report.get('installed', []))}",
        f"  missing bundled: {len(report.get('missing_bundled', []))}",
        f"  missing external: {len(report.get('missing_external', []))}",
    ]
    for item in report.get("installed", []):
        lines.append(f"    + {item['name']} -> {item['path']}")
    for item in report.get("missing_bundled", []):
        if isinstance(item, dict):
            lines.append(f"    ! bundled missing: {item.get('name')} ({item.get('reason') or item.get('source')})")
        else:
            lines.append(f"    ! bundled missing: {item}")
    for item in report.get("missing_external", []):
        lines.append(f"    ! external missing: {item.get('name')} - {item.get('install_hint')}")
    return "\n".join(lines)
