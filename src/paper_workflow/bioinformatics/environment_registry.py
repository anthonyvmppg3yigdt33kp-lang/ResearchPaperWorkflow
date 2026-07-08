"""Environment registry and reproducibility checks for method assets."""

from __future__ import annotations

import hashlib
import importlib.util
import copy
import shutil
import subprocess
import sys
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


def _write_yaml(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        yaml.safe_dump(data, fh, allow_unicode=True, sort_keys=False)


class EnvironmentRegistry:
    """Resolve declared execution environments without installing packages."""

    _VALIDATION_CACHE: dict[tuple[str, str, str, str, bool, bool], dict[str, Any]] = {}

    def __init__(self, project_root: Path, registry_path: Optional[Path] = None):
        self.project_root = Path(project_root)
        self.registry_path = registry_path or self.project_root / "code_library" / "environment_registry.yaml"
        self.data = _read_yaml(self.registry_path)
        raw = self.data.get("environments", {})
        if isinstance(raw, list):
            self.environments = {
                str(item.get("env_id", "")): dict(item)
                for item in raw
                if isinstance(item, dict) and item.get("env_id")
            }
        elif isinstance(raw, dict):
            self.environments = {str(k): dict(v or {}) for k, v in raw.items() if isinstance(v, dict)}
        else:
            self.environments = {}

    def content_hash(self) -> str:
        if not self.registry_path.exists():
            return ""
        return hashlib.sha256(self.registry_path.read_bytes()).hexdigest()

    def list_envs(self) -> list[dict[str, Any]]:
        return [
            {"env_id": env_id, **env}
            for env_id, env in sorted(self.environments.items())
        ]

    def get(self, env_id: str) -> dict[str, Any]:
        env = dict(self.environments.get(env_id, {}))
        if env and "env_id" not in env:
            env["env_id"] = env_id
        return env

    def _lock_file(self, env: dict[str, Any]) -> str:
        direct = str(env.get("lock_file", "") or "")
        nested = str((env.get("reproducibility") or {}).get("lock_file", "") or "")
        return direct or nested

    def _required_packages(self, env: dict[str, Any]) -> list[str]:
        return list(env.get("required_packages", env.get("packages", [])) or [])

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
            return sys.executable or shutil.which("python") or "python"
        return runner

    def validate_runner(self, env_id: str, language: str = "") -> dict[str, Any]:
        env = self.get(env_id)
        runner = self.resolve_runner(env_id, language)
        runner_available = bool(runner) and (Path(runner).exists() or shutil.which(runner) is not None)
        issues = []
        if not env:
            issues.append(f"environment not declared: {env_id}")
        if not runner_available:
            issues.append(f"runner not available for environment: {env_id}")
        return {
            "env_id": env_id,
            "runner": runner,
            "runner_available": runner_available,
            "status": "pass" if env and runner_available else "blocked",
            "issues": issues,
        }

    def validate_lock_file(self, env_id: str, require_lock: bool = False) -> dict[str, Any]:
        env = self.get(env_id)
        lock_file = self._lock_file(env)
        lock_path = self.project_root / lock_file if lock_file and not Path(lock_file).is_absolute() else Path(lock_file)
        lock_present = bool(lock_file) and lock_path.exists()
        issues = []
        if require_lock and not lock_present:
            issues.append(f"lock file required but missing for environment: {env_id}")
        status = "pass" if lock_present or not require_lock else "blocked"
        return {
            "env_id": env_id,
            "lock_file": lock_file,
            "lock_file_present": lock_present,
            "status": status,
            "issues": issues,
        }

    def validate_packages(self, env_id: str) -> dict[str, Any]:
        env = self.get(env_id)
        language = str(env.get("language", "")).lower()
        packages = self._required_packages(env)
        if not packages:
            return {
                "env_id": env_id,
                "required_packages": [],
                "missing_packages": [],
                "packages_available": True,
                "status": "pass",
                "issues": [],
            }
        if language == "python":
            missing = [pkg for pkg in packages if importlib.util.find_spec(pkg.replace("-", "_")) is None]
            return self._package_status(env_id, packages, missing)
        if language == "r":
            runner_status = self.validate_runner(env_id, language="r")
            runner = runner_status.get("runner", "")
            if runner_status["status"] != "pass":
                return self._package_status(env_id, packages, packages, runner_status["issues"])
            expr = (
                "pkgs <- c("
                + ",".join(repr(pkg).replace("\\", "\\\\") for pkg in packages)
                + "); missing <- pkgs[!vapply(pkgs, requireNamespace, quietly=TRUE, FUN.VALUE=logical(1))]; "
                "if(length(missing)>0){cat(paste(missing, collapse=',')); quit(status=1)}"
            )
            completed = subprocess.run(
                [str(runner), "-e", expr],
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
                timeout=120,
            )
            missing = [item for item in (completed.stdout or "").strip().split(",") if item]
            issues = []
            if completed.returncode != 0:
                if not missing:
                    missing = packages
                issues.append(f"required R packages missing or unavailable: {', '.join(missing)}")
            return self._package_status(env_id, packages, missing, issues)
        return self._package_status(env_id, packages, [], [f"package check unsupported for language: {language or 'unknown'}"])

    @staticmethod
    def _package_status(
        env_id: str,
        packages: list[str],
        missing: list[str],
        issues: Optional[list[str]] = None,
    ) -> dict[str, Any]:
        issues = list(issues or [])
        if missing and not issues:
            issues.append(f"required packages missing: {', '.join(missing)}")
        return {
            "env_id": env_id,
            "required_packages": packages,
            "missing_packages": missing,
            "packages_available": not missing,
            "status": "pass" if not missing else "blocked",
            "issues": issues,
        }

    def validate_environment(
        self,
        env_id: str,
        language: str = "",
        require_lock: bool = False,
        require_packages: bool = True,
    ) -> dict[str, Any]:
        cache_key = (
            str(self.registry_path.resolve()),
            self.content_hash(),
            env_id,
            language.lower(),
            bool(require_lock),
            bool(require_packages),
        )
        if cache_key in self._VALIDATION_CACHE:
            return copy.deepcopy(self._VALIDATION_CACHE[cache_key])
        env = self.get(env_id)
        runner_status = self.validate_runner(env_id, language)
        lock_status = self.validate_lock_file(env_id, require_lock=require_lock)
        package_status = self.validate_packages(env_id) if require_packages else {
            "status": "pass",
            "packages_available": "not_checked",
            "required_packages": self._required_packages(env),
            "missing_packages": [],
            "issues": [],
        }
        issues = []
        for item in [runner_status, lock_status, package_status]:
            issues.extend(item.get("issues", []) or [])
        status = "pass" if not issues else "blocked"
        reproducibility_grade = "locked" if lock_status["lock_file_present"] else "degraded"
        result = {
            "env_id": env_id,
            "status": status,
            "runner": runner_status.get("runner", ""),
            "runner_available": runner_status["runner_available"],
            "lock_file": lock_status["lock_file"],
            "lock_file_present": lock_status["lock_file_present"],
            "package_check_status": package_status["status"],
            "packages_available": package_status["packages_available"],
            "declared_packages": self._required_packages(env),
            "missing_packages": package_status["missing_packages"],
            "session_info_required": bool(env.get("session_info_required", (env.get("reproducibility") or {}).get("session_info_per_node") == "required")),
            "seed_policy": env.get("seed_policy", (env.get("reproducibility") or {}).get("seed_policy", "")),
            "reproducibility_grade": reproducibility_grade,
            "issues": issues,
            "validation": env.get("validation", {}) if env else {},
        }
        self._VALIDATION_CACHE[cache_key] = copy.deepcopy(result)
        return result

    def write_environment_report(self, env_id: str, path: Path, **kwargs: Any) -> dict[str, Any]:
        report = self.validate_environment(env_id, **kwargs)
        report["environment_registry"] = str(self.registry_path)
        report["environment_registry_hash"] = self.content_hash()
        _write_yaml(path, report)
        return report
