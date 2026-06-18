"""
Reproducibility infrastructure for research paper workflows.

Provides environment capture, session reporting, reproducibility verification,
and Dockerfile generation to ensure computational reproducibility of analyses.

Usage::

    from paper_workflow.utils.reproducibility import (
        capture_environment,
        capture_session_info,
        verify_reproducibility,
        generate_dockerfile,
    )

    env = capture_environment()
    report = capture_session_info(output_path="reproducibility_report.txt")
    status = verify_reproducibility("/path/to/paper_dir")
    dockerfile = generate_dockerfile("/path/to/paper_dir", output_path="Dockerfile")
"""

from __future__ import annotations

import datetime
import importlib.metadata
import io
import json
import os
import platform
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# Error logging helper (replaces bare except: pass patterns)
# ---------------------------------------------------------------------------

def _log_nonfatal(stage: str, exc: Exception, severity: str = "warning") -> None:
    """Log a non-fatal error without crashing the pipeline."""
    try:
        import sys
        print(f"[{severity.upper()}] [{stage}] {type(exc).__name__}: {exc}", file=sys.stderr, flush=True)
    except Exception:
        pass  # Last-resort pass: error logging itself must never crash


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Files that indicate a reproducibility-aware project
_REPRO_FILES = [
    "requirements.txt",
    "environment.yml",
    "environment.yaml",
    "renv.lock",
    "Pipfile",
    "Pipfile.lock",
    "pyproject.toml",
    "setup.cfg",
    "setup.py",
    "conda-lock.yml",
]

# Seed-related patterns to search for in R and Python code
_SEED_PATTERNS = [
    re.compile(p, re.IGNORECASE)
    for p in [
        r"set\.seed\s*\(.+\)",
        r"random\.seed\s*\(.+\)",
        r"np\.random\.seed\s*\(.+\)",
        r"numpy\.random\.seed\s*\(.+\)",
        r"torch\.manual_seed\s*\(.+\)",
        r"tf\.random\.set_seed\s*\(.+\)",
        r"random_state\s*=\s*\d+",
        r"random_seed\s*=\s*\d+",
        r"seed\s*=\s*\d+",
    ]
]

# ---------------------------------------------------------------------------
# Helper utilities
# ---------------------------------------------------------------------------


def _run_cmd(cmd: List[str], timeout: int = 15) -> str:
    """Run a command and return its stdout, or empty string on failure."""
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            shell=False,
        )
        return result.stdout.strip()
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        return ""


def _find_files(
    root: Path,
    patterns: List[str],
    max_depth: int = 4,
) -> List[Path]:
    """Find files matching *patterns* within *root* up to *max_depth*."""
    matches: List[Path] = []
    search_root = root.resolve()
    for depth, dirpath, dirnames, filenames in _walk_depth(search_root, max_depth):
        for fname in filenames:
            for pat in patterns:
                if re.match(pat.replace(".", r"\.").replace("*", ".*"), fname):
                    matches.append(Path(dirpath) / fname)
                    break
    return matches


def _walk_depth(root: Path, max_depth: int):
    """os.walk with depth control."""
    root = Path(root)
    for dirpath, dirnames, filenames in os.walk(root):
        rel = Path(dirpath).relative_to(root)
        depth = len(rel.parts) if rel != Path(".") else 0
        if depth > max_depth:
            dirnames.clear()
            continue
        yield depth, dirpath, dirnames, filenames


def _grep_files(
    root: Path,
    patterns: List[re.Pattern],
    file_extensions: Tuple[str, ...] = (".py", ".R", ".r", ".Rmd", ".qmd", ".ipynb"),
    max_depth: int = 5,
) -> Dict[str, List[str]]:
    """Search for regex patterns inside files and return {path: [matched_lines]}."""
    hits: Dict[str, List[str]] = {}
    search_root = root.resolve()
    for _depth, dirpath, dirnames, filenames in _walk_depth(search_root, max_depth):
        # Skip hidden / venv directories
        dirnames[:] = [d for d in dirnames if not d.startswith(".") and d not in {
            "node_modules", "__pycache__", "venv", ".venv", "env",
            "renv", "packrat", ".git", "dist", "build", "egg-info",
        }]
        for fname in filenames:
            if not fname.endswith(file_extensions):
                continue
            fpath = Path(dirpath) / fname
            try:
                text = fpath.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            for pat in patterns:
                for line in text.splitlines():
                    m = pat.search(line)
                    if m:
                        rel = str(fpath.relative_to(search_root))
                        hits.setdefault(rel, []).append(line.strip())
                        break  # one hit per file per pattern is enough
    return hits


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def capture_environment() -> Dict[str, Any]:
    """Capture the current Python environment for reproducibility.

    Returns a dictionary with keys:

    - ``python_version``: full ``sys.version`` string
    - ``python_executable``: path to the Python interpreter
    - ``platform``: OS / platform description
    - ``platform_details``: machine, processor, architecture, node
    - ``packages``: dict of ``{package_name: version}`` from ``pip freeze``
    - ``packages_raw``: raw ``pip freeze`` output as a list of lines
    - ``timestamp_utc``: ISO-8601 UTC timestamp
    - ``cwd``: current working directory at capture time
    """
    # Platform details
    uname = platform.uname()
    platform_details = {
        "system": uname.system,
        "node": uname.node,
        "release": uname.release,
        "version": uname.version,
        "machine": uname.machine,
        "processor": uname.processor,
    }

    # Python version
    python_version = sys.version

    # Installed packages via pip freeze
    packages_raw = _run_cmd([sys.executable, "-m", "pip", "freeze"], timeout=30)
    packages: Dict[str, str] = {}
    if packages_raw:
        for line in packages_raw.splitlines():
            line = line.strip()
            if not line or line.startswith("#") or line.startswith("-"):
                continue
            if "==" in line:
                name, ver = line.split("==", 1)
                packages[name.strip()] = ver.strip()
            elif "@" in line:
                # Editable / VCS install — capture key only
                name_part = line.split("@")[0].strip()
                packages[name_part] = "(editable)"
            else:
                packages[line.strip()] = "(unknown)"

    return {
        "python_version": python_version,
        "python_executable": sys.executable,
        "platform": platform.platform(),
        "platform_details": platform_details,
        "packages": packages,
        "packages_raw": packages_raw.splitlines() if packages_raw else [],
        "timestamp_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "cwd": os.getcwd(),
    }


def capture_session_info(output_path: Optional[str] = None) -> str:
    """Generate a full reproducibility report as a multi-line string.

    Includes Python version, platform, pip freeze, and session metadata.
    If *output_path* is provided, also writes the report to that file.

    Returns the report string.
    """
    env = capture_environment()

    lines: List[str] = []
    lines.append("=" * 72)
    lines.append("REPRODUCIBILITY SESSION REPORT")
    lines.append("=" * 72)
    lines.append(f"Generated (UTC): {env['timestamp_utc']}")
    lines.append(f"Working Directory: {env['cwd']}")
    lines.append("")

    # Platform
    lines.append("-" * 72)
    lines.append("PLATFORM")
    lines.append("-" * 72)
    lines.append(f"  System:    {env['platform_details']['system']}")
    lines.append(f"  Release:   {env['platform_details']['release']}")
    lines.append(f"  Version:   {env['platform_details']['version']}")
    lines.append(f"  Machine:   {env['platform_details']['machine']}")
    lines.append(f"  Processor: {env['platform_details']['processor']}")
    lines.append(f"  Node:      {env['platform_details']['node']}")
    lines.append("")

    # Python
    lines.append("-" * 72)
    lines.append("PYTHON")
    lines.append("-" * 72)
    lines.append(f"  Executable: {env['python_executable']}")
    for ver_line in env["python_version"].splitlines():
        lines.append(f"  {ver_line}")
    lines.append("")

    # Packages
    lines.append("-" * 72)
    lines.append(f"INSTALLED PACKAGES ({len(env['packages'])} total)")
    lines.append("-" * 72)
    for pkg in sorted(env["packages"]):
        lines.append(f"  {pkg}=={env['packages'][pkg]}")
    lines.append("")

    # Environment variables (filtered for relevance)
    lines.append("-" * 72)
    lines.append("RELEVANT ENVIRONMENT VARIABLES")
    lines.append("-" * 72)
    relevant_vars = [
        k for k in sorted(os.environ)
        if any(prefix in k.upper() for prefix in [
            "PYTHON", "CONDA", "R_", "PATH", "HOME", "USER",
            "LANG", "LC_", "TMP", "TEMP", "SHELL", "VIRTUAL",
        ])
    ]
    for var in relevant_vars:
        lines.append(f"  {var}={os.environ[var]}")
    lines.append("")

    lines.append("=" * 72)
    lines.append("END OF REPORT")
    lines.append("=" * 72)

    report = "\n".join(lines)

    if output_path:
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(report, encoding="utf-8")
        report += f"\n\n[Report written to {out.resolve()}]"

    return report


def verify_reproducibility(paper_dir: str) -> Dict[str, Any]:
    """Verify that a paper directory has reproducibility infrastructure in place.

    Checks:
        - Dependency file(s) present (requirements.txt, environment.yml, etc.)
        - Random seeds documented in source code
        - README or similar documentation present
        - Software versions recorded

    Parameters
    ----------
    paper_dir : str
        Path to the root of the paper / project directory.

    Returns
    -------
    dict
        ``status``: ``"pass"`` | ``"warning"`` | ``"fail"``
        ``score``: integer 0-100
        ``checks``: per-check dicts with ``name``, ``passed``, ``detail``
        ``summary``: human-readable summary string
    """
    root = Path(paper_dir).resolve()
    checks: List[Dict[str, Any]] = []
    passed_count = 0
    total_count = 0

    # --- Check 1: Dependency files ---
    total_count += 1
    dep_files = _find_files(root, _REPRO_FILES, max_depth=3)
    dep_names = [f.name for f in dep_files]
    if dep_files:
        checks.append({
            "name": "dependency_files",
            "passed": True,
            "detail": f"Found: {', '.join(dep_names)}",
        })
        passed_count += 1
    else:
        checks.append({
            "name": "dependency_files",
            "passed": False,
            "detail": "No dependency file found (requirements.txt, environment.yml, etc.).",
        })

    # --- Check 2: Seeds documented ---
    total_count += 1
    seed_hits = _grep_files(root, _SEED_PATTERNS, max_depth=5)
    if seed_hits:
        checks.append({
            "name": "random_seeds",
            "passed": True,
            "detail": f"Seed calls found in {len(seed_hits)} file(s): {', '.join(sorted(seed_hits))}",
            "seed_locations": seed_hits,
        })
        passed_count += 1
    else:
        checks.append({
            "name": "random_seeds",
            "passed": False,
            "detail": "No random seed calls detected. Reproducibility requires fixed seeds.",
        })

    # --- Check 3: README or docs ---
    total_count += 1
    readme_files = _find_files(root, ["README*", "readme*"], max_depth=2)
    if readme_files:
        checks.append({
            "name": "documentation",
            "passed": True,
            "detail": f"Found: {', '.join(f.name for f in readme_files)}",
        })
        passed_count += 1
    else:
        checks.append({
            "name": "documentation",
            "passed": False,
            "detail": "No README file found. Add setup/usage instructions.",
        })

    # --- Check 4: LICENSE ---
    total_count += 1
    license_files = _find_files(root, ["LICENSE*", "LICENCE*", "COPYING*"], max_depth=2)
    if license_files:
        checks.append({
            "name": "license",
            "passed": True,
            "detail": f"Found: {license_files[0].name}",
        })
        passed_count += 1
    else:
        checks.append({
            "name": "license",
            "passed": False,
            "detail": "No LICENSE file found. Required for open-source compliance.",
        })

    # --- Check 5: Version pinning heuristics in dep files ---
    total_count += 1
    has_versioned_deps = False
    for dep_file in dep_files:
        try:
            content = dep_file.read_text(encoding="utf-8", errors="replace")
            if "==" in content or ">=" in content or "<=" in content or "~=" in content:
                has_versioned_deps = True
                break
            if dep_file.suffix in (".yml", ".yaml") and "dependencies:" in content:
                has_versioned_deps = True
                break
        except OSError:
            continue
    if has_versioned_deps or not dep_files:
        checks.append({
            "name": "version_pinning",
            "passed": has_versioned_deps,
            "detail": (
                "Dependencies appear to be version-pinned."
                if has_versioned_deps
                else "No version-pinned dependencies detected."
            ),
        })
        if has_versioned_deps:
            passed_count += 1
    else:
        checks.append({
            "name": "version_pinning",
            "passed": False,
            "detail": "Dependencies found but no version pinning detected.",
        })

    # --- Check 6: .gitignore present ---
    total_count += 1
    gitignore = root / ".gitignore"
    if gitignore.exists():
        checks.append({
            "name": "gitignore",
            "passed": True,
            "detail": ".gitignore present.",
        })
        passed_count += 1
    else:
        checks.append({
            "name": "gitignore",
            "passed": False,
            "detail": "No .gitignore file. Recommended for clean version control.",
        })

    # --- Compute status ---
    score = int((passed_count / total_count) * 100) if total_count > 0 else 0
    if score >= 80:
        status = "pass"
    elif score >= 50:
        status = "warning"
    else:
        status = "fail"

    failed_checks = [c["name"] for c in checks if not c["passed"]]

    return {
        "status": status,
        "score": score,
        "passed": passed_count,
        "total": total_count,
        "checks": checks,
        "summary": (
            f"Reproducibility score: {score}/100 ({status}). "
            f"{passed_count}/{total_count} checks passed."
            + (
                f" Issues: {', '.join(failed_checks)}."
                if failed_checks
                else " All checks passed."
            )
        ),
    }


def generate_dockerfile(
    paper_dir: str,
    output_path: Optional[str] = None,
    base_image: str = "python:3.10-slim",
    extra_packages: Optional[List[str]] = None,
) -> str:
    """Generate a Dockerfile for a research paper project.

    Reads the project's dependency files (requirements.txt, environment.yml, pyproject.toml)
    and generates a multi-stage Dockerfile that reproduces the environment.

    Parameters
    ----------
    paper_dir : str
        Path to the paper/project root directory.
    output_path : str, optional
        If provided, write the generated Dockerfile to this path.
    base_image : str
        Docker base image tag. Default ``"python:3.10-slim"``.
    extra_packages : list of str, optional
        Additional apt or pip packages to install.

    Returns
    -------
    str
        The generated Dockerfile content.
    """
    root = Path(paper_dir).resolve()
    project_name = root.name or "research-paper"

    # Detect dependency file
    dep_file: Optional[str] = None
    dep_type: str = "none"
    for candidate, dtype in [
        ("requirements.txt", "pip"),
        ("environment.yml", "conda"),
        ("environment.yaml", "conda"),
        ("pyproject.toml", "pip"),
    ]:
        if (root / candidate).exists():
            dep_file = candidate
            dep_type = dtype
            break

    # Read pyproject.toml for project metadata
    project_version = "1.0.0"
    pyproject_path = root / "pyproject.toml"
    if pyproject_path.exists():
        try:
            content = pyproject_path.read_text(encoding="utf-8")
            m = re.search(r'version\s*=\s*["\']([^"\']+)["\']', content)
            if m:
                project_version = m.group(1)
        except OSError as e:
            _log_nonfatal("generate_dockerfile:read_pyproject_version", e, "info")

    # Detect paper-workflow package install path
    paper_workflow_installed = False
    setup_paths = [
        root / "setup.py",
        root / "setup.cfg",
    ]
    for sp in setup_paths:
        if sp.exists():
            paper_workflow_installed = True
            break
    if pyproject_path.exists():
        try:
            content = pyproject_path.read_text(encoding="utf-8")
            if "[build-system]" in content:
                paper_workflow_installed = True
        except OSError as e:
            _log_nonfatal("generate_dockerfile:read_pyproject_build_system", e, "info")

    # Build the Dockerfile
    lines: List[str] = []

    # Stage 1: base
    lines.append(f"# =============================================================================")
    lines.append(f"# Dockerfile — {project_name} v{project_version}")
    lines.append(f"# Auto-generated by paper_workflow.utils.reproducibility")
    lines.append(f"# Generated: {datetime.datetime.now(datetime.timezone.utc).isoformat()}")
    lines.append(f"# =============================================================================")
    lines.append("")
    lines.append(f"# --- Stage 1: Build environment ---")
    lines.append(f"FROM {base_image} AS builder")
    lines.append("")
    lines.append("ENV DEBIAN_FRONTEND=noninteractive \\")
    lines.append("    PYTHONDONTWRITEBYTECODE=1 \\")
    lines.append("    PYTHONUNBUFFERED=1 \\")
    lines.append("    PIP_NO_CACHE_DIR=1 \\")
    lines.append("    PIP_DISABLE_PIP_VERSION_CHECK=1")
    lines.append("")

    # System dependencies
    lines.append("# System dependencies for scientific computing")
    extra_apt = " ".join(extra_packages) if extra_packages else ""
    lines.append("RUN apt-get update && apt-get install -y --no-install-recommends \\")
    lines.append("    build-essential \\")
    lines.append("    curl \\")
    lines.append("    git \\")
    lines.append("    libopenblas-dev \\")
    lines.append("    liblapack-dev \\")
    if extra_apt:
        lines.append(f"    {extra_apt} \\")
    lines.append("    && rm -rf /var/lib/apt/lists/*")
    lines.append("")

    # Install Python dependencies
    if dep_file and dep_type == "pip":
        lines.append(f"# Copy and install Python dependencies from {dep_file}")
        lines.append(f"COPY {dep_file} /tmp/")
        lines.append(f"RUN pip install --no-cache-dir -r /tmp/{dep_file}")
        lines.append("")
    elif dep_file and dep_type == "conda":
        lines.append(f"# Install Miniconda and create environment from {dep_file}")
        lines.append("RUN curl -sSL https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -o /tmp/miniconda.sh \\")
        lines.append("    && bash /tmp/miniconda.sh -b -p /opt/conda \\")
        lines.append("    && rm /tmp/miniconda.sh")
        lines.append(f"COPY {dep_file} /tmp/")
        lines.append(f"RUN /opt/conda/bin/conda env create -f /tmp/{dep_file}")
        lines.append("ENV PATH=/opt/conda/bin:$PATH")
        lines.append("")
    else:
        lines.append("# Install core scientific packages")
        lines.append("RUN pip install --no-cache-dir \\")
        lines.append("    numpy>=1.24 \\")
        lines.append("    scipy>=1.10 \\")
        lines.append("    pandas>=2.0 \\")
        lines.append("    matplotlib>=3.7 \\")
        lines.append("    seaborn>=0.12 \\")
        lines.append("    scikit-learn>=1.3 \\")
        lines.append("    statsmodels>=0.14 \\")
        lines.append("    pyyaml>=6.0")
        lines.append("")

    # Install paper-workflow if it's a package project
    if paper_workflow_installed:
        lines.append("# Install paper-workflow package")
        lines.append("COPY pyproject.toml setup.cfg setup.py* /app/")
        lines.append("COPY src/ /app/src/")
        lines.append("RUN pip install --no-cache-dir -e /app/[full]")
        lines.append("")

    # --- Stage 2: Runtime ---
    lines.append(f"# --- Stage 2: Runtime environment ---")
    lines.append(f"FROM {base_image} AS runtime")
    lines.append("")
    lines.append("ENV DEBIAN_FRONTEND=noninteractive \\")
    lines.append("    PYTHONDONTWRITEBYTECODE=1 \\")
    lines.append("    PYTHONUNBUFFERED=1")
    lines.append("")

    lines.append("# Copy installed packages from builder stage")
    lines.append("COPY --from=builder /usr/local/lib/python3.10/site-packages /usr/local/lib/python3.10/site-packages")
    lines.append("COPY --from=builder /usr/local/bin /usr/local/bin")
    lines.append("")

    # Copy project files
    lines.append("# Copy project files")
    lines.append("WORKDIR /workspace")
    lines.append(f"COPY . /workspace/{project_name}/")
    lines.append("")

    # Entry point
    lines.append("# Default entry point: run the full pipeline")
    lines.append(f"WORKDIR /workspace/{project_name}")
    if (root / "Makefile").exists():
        lines.append("CMD [\"make\", \"all\"]")
    elif (root / "scripts").exists():
        lines.append("CMD [\"bash\", \"scripts/run_pipeline.sh\"]")
    else:
        lines.append(f"CMD [\"python\", \"-m\", \"paper_workflow\"]")
    lines.append("")

    dockerfile_content = "\n".join(lines)

    if output_path:
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(dockerfile_content, encoding="utf-8")
        dockerfile_content += f"\n# Written to {out.resolve()}"

    return dockerfile_content
