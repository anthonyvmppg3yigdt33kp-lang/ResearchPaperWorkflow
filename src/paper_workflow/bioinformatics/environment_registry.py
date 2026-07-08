"""Environment registry and lightweight availability checks."""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any, Optional

import yaml


WINDOWS_RSCRIPT_CANDIDATES = [
    Path(r"C:\Program Files\R\R-4.5.3\bin\Rscript.exe"),
    Path(r"C:\Program Files\R\R-4.5.3\bin\x64\Rscript.exe"),
]


def _read_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh) or {}
    return data if isinstance(data, dict) else {}


class EnvironmentRegistry:
    """Resolve declared execution environments without installing packages."""

    def __init__(self, project_root: Path, registry_path: Optional[Path] = None):
        self.project_root = Path(project_root)
        self.registry_path = registry_path or self.project_root / "code_library" / "environment_registry.yaml"
        self.data = _read_yaml(self.registry_path)
        raw = self.data.get("environments", {})
        if isinstance(raw, list):
            self.environments = {str(item.get("env_id", "")): dict(item) for item in raw if isinstance(item, dict) and item.get("env_id")}
        elif isinstance(raw, dict):
            self.environments = {str(k): dict(v or {}) for k, v in raw.items() if isinstance(v, dict)}
        else:
            self.environments = {}

    def get(self, env_id: str) -> dict[str, Any]:
        return dict(self.environments.get(env_id, {}))

    def resolve_runner(self, env_id: str, language: str = "") -> str:
        env = self.get(env_id)
        runner = str(env.get("runner", "")).strip()
        if runner:
            path = Path(runner)
            if path.exists():
                return str(path)
            found = shutil.which(runner)
            if found:
                return found
        language = (language or env.get("language", "")).lower()
        if language == "r":
            found = shutil.which("Rscript")
            if found:
                return found
            for candidate in WINDOWS_RSCRIPT_CANDIDATES:
                if candidate.exists():
                    return str(candidate)
        if language == "python":
            return shutil.which("python") or "python"
        return runner

    def validate_environment(self, env_id: str, language: str = "") -> dict[str, Any]:
        env = self.get(env_id)
        runner = self.resolve_runner(env_id, language)
        runner_available = bool(runner) and (Path(runner).exists() or shutil.which(runner) is not None)
        status = "pass" if env and runner_available else "blocked"
        issues = []
        if not env:
            issues.append(f"environment not declared: {env_id}")
        if not runner_available:
            issues.append(f"runner not available for environment: {env_id}")
        return {
            "env_id": env_id,
            "status": status,
            "runner": runner,
            "runner_available": runner_available,
            "issues": issues,
            "declared_packages": env.get("packages", []) if env else [],
            "validation": env.get("validation", {}) if env else {},
        }
