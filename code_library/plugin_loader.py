"""
Plugin Loader — Auto-discovery and registration of analysis code modules.

Scans code_library/ subdirectories for Python (.py) and R (.R) analysis
modules, extracts metadata from docstrings, and maintains a YAML registry.
"""
from __future__ import annotations

import importlib
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

import yaml


# Plugin definition schema version
PLUGIN_SCHEMA_VERSION = "1.0.0"

# Expected keys in a valid plugin definition
REQUIRED_PLUGIN_KEYS = ["name", "version", "language", "category", "entry_point"]
OPTIONAL_PLUGIN_KEYS = ["description", "inputs", "outputs", "parameters", "dependencies", "test_command"]


class PluginRegistry:
    """Manages the code library plugin registry."""

    def __init__(self, registry_path: Optional[Path] = None):
        self.registry_path = registry_path
        self._plugins: dict[str, dict[str, Any]] = {}
        if registry_path and registry_path.exists():
            self.load_registry()

    def load_registry(self) -> dict[str, Any]:
        """Load the plugin registry from YAML."""
        if not self.registry_path or not self.registry_path.exists():
            return {}
        with open(self.registry_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        self._plugins = data.get("plugins", {})
        return self._plugins

    def save_registry(self) -> None:
        """Save the plugin registry to YAML."""
        if not self.registry_path:
            return
        self.registry_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.registry_path, "w", encoding="utf-8") as f:
            yaml.dump({
                "schema_version": PLUGIN_SCHEMA_VERSION,
                "updated_at": datetime.now().isoformat(),
                "total_plugins": len(self._plugins),
                "plugins": self._plugins,
            }, f, allow_unicode=True, default_flow_style=False)

    def register_plugin(self, name: str, plugin_def: dict[str, Any]) -> bool:
        """Register or update a plugin definition."""
        issues = self.validate_plugin(plugin_def)
        if issues:
            print(f"[WARN] Plugin '{name}' has issues: {issues}")
        plugin_def["registered_at"] = datetime.now().isoformat()
        plugin_def["schema_version"] = PLUGIN_SCHEMA_VERSION
        self._plugins[name] = plugin_def
        return True

    def get_plugin(self, name: str) -> Optional[dict[str, Any]]:
        """Get a plugin definition by name."""
        return self._plugins.get(name)

    def list_plugins(self, language: str = None, category: str = None) -> list[dict[str, Any]]:
        """List plugins, optionally filtered by language and/or category."""
        results = list(self._plugins.values())
        if language:
            results = [p for p in results if p.get("language") == language]
        if category:
            results = [p for p in results if p.get("category") == category]
        return sorted(results, key=lambda p: p.get("name", ""))

    def validate_plugin(self, plugin_def: dict[str, Any]) -> list[str]:
        """Validate a plugin definition. Returns list of issue strings."""
        issues = []
        for key in REQUIRED_PLUGIN_KEYS:
            if key not in plugin_def or not plugin_def[key]:
                issues.append(f"Missing required key: '{key}'")

        language = plugin_def.get("language", "")
        if language not in ("python", "r", "bash"):
            issues.append(f"Unsupported language: '{language}'")

        valid_categories = ["qc", "clustering", "annotation", "integration",
                           "visualization", "statistics", "ml", "dl", "spatial", "other"]
        category = plugin_def.get("category", "")
        if category not in valid_categories:
            issues.append(f"Unknown category '{category}'. Valid: {valid_categories}")

        return issues

    def remove_plugin(self, name: str) -> bool:
        """Remove a plugin from the registry."""
        if name in self._plugins:
            del self._plugins[name]
            return True
        return False


def discover_plugins(scan_paths: list[Path]) -> list[dict[str, Any]]:
    """Auto-discover analysis modules in the given scan paths.

    Scans for .py and .R files and extracts metadata from docstrings/comments.
    """
    discovered = []

    for scan_path in scan_paths:
        if not scan_path.exists():
            continue

        for py_file in scan_path.rglob("*.py"):
            if py_file.name.startswith("__"):
                continue

            plugin_def = _extract_python_metadata(py_file, scan_path)
            if plugin_def:
                discovered.append(plugin_def)

        for r_file in scan_path.rglob("*.R"):
            plugin_def = _extract_r_metadata(r_file, scan_path)
            if plugin_def:
                discovered.append(plugin_def)

    return discovered


def _extract_python_metadata(file_path: Path, base_path: Path) -> Optional[dict[str, Any]]:
    """Extract plugin metadata from a Python file's docstring."""
    try:
        content = file_path.read_text(encoding="utf-8")
    except Exception:
        return None

    # Try to parse the module docstring
    doc_match = re.search(r'"""(.*?)"""', content, re.DOTALL)
    docstring = doc_match.group(1).strip() if doc_match else ""

    # Derive metadata from filename and path
    name = file_path.stem
    relative_path = file_path.relative_to(base_path.parent) if hasattr(file_path, 'relative_to') else file_path

    # Detect category from path
    category = "other"
    path_str = str(relative_path).lower()
    if "qc" in path_str:
        category = "qc"
    elif "cluster" in path_str:
        category = "clustering"
    elif "annot" in path_str:
        category = "annotation"
    elif "integrat" in path_str:
        category = "integration"
    elif "visual" in path_str or "plot" in path_str:
        category = "visualization"
    elif "stat" in path_str or "test" in path_str:
        category = "statistics"
    elif "ml" in path_str or "deep" in path_str or "neural" in path_str:
        category = "ml"
    elif "spatial" in path_str:
        category = "spatial"

    # Extract function names as potential entry points
    func_matches = re.findall(r'^def\s+(\w+)\s*\(', content, re.MULTILINE)
    entry_point = f"code_library.{'.'.join(relative_path.with_suffix('').parts)}"

    return {
        "name": name,
        "version": "1.0.0",
        "language": "python",
        "category": category,
        "entry_point": entry_point,
        "description": docstring[:200] if docstring else f"Python module: {name}",
        "file_path": str(relative_path),
        "functions": func_matches[:10],
        "inputs": [],
        "outputs": [],
        "parameters": [],
        "dependencies": [],
    }


def _extract_r_metadata(file_path: Path, base_path: Path) -> Optional[dict[str, Any]]:
    """Extract plugin metadata from an R script's header comments."""
    try:
        content = file_path.read_text(encoding="utf-8")
    except Exception:
        return None

    name = file_path.stem
    relative_path = file_path.relative_to(base_path.parent) if hasattr(file_path, 'relative_to') else file_path

    # Extract R functions
    func_matches = re.findall(r'(\w+)\s*<-\s*function\s*\(', content)

    # Detect category from path
    category = "other"
    path_str = str(relative_path).lower()
    if "qc" in path_str:
        category = "qc"
    elif "cluster" in path_str:
        category = "clustering"
    elif "annot" in path_str:
        category = "annotation"
    elif "stat" in path_str or "test" in path_str:
        category = "statistics"

    return {
        "name": name,
        "version": "1.0.0",
        "language": "r",
        "category": category,
        "entry_point": str(relative_path),
        "description": f"R script: {name}",
        "file_path": str(relative_path),
        "functions": func_matches[:10],
        "inputs": [],
        "outputs": [],
        "parameters": [],
        "dependencies": [],
    }


def auto_discover_and_register(
    base_path: Path,
    registry_path: Optional[Path] = None,
    scan_paths: Optional[list[str]] = None,
) -> dict[str, Any]:
    """Auto-discover all plugins and update the registry.

    Args:
        base_path: Project root directory
        registry_path: Path to plugin_registry.yaml (auto-derived if None)
        scan_paths: List of directories to scan (uses defaults if None)

    Returns:
        Summary dict with counts and list of discovered plugins
    """
    if scan_paths is None:
        scan_paths = [
            "code_library/patterns/qc/",
            "code_library/patterns/clustering/",
            "code_library/modules/",
            "code_library/solutions/",
            "code_library/snippets/",
            "code_library/r/",
            "code_library/pipelines/",
        ]

    if registry_path is None:
        registry_path = base_path / "code_library" / "plugin_registry.yaml"

    # Resolve scan paths
    resolved_paths = [base_path / p for p in scan_paths]

    # Discover plugins
    discovered = discover_plugins(resolved_paths)

    # Load existing registry
    registry = PluginRegistry(registry_path)

    # Register discovered plugins
    new_count = 0
    updated_count = 0
    for plugin_def in discovered:
        name = plugin_def["name"]
        existing = registry.get_plugin(name)
        if existing:
            # Update existing
            existing.update(plugin_def)
            updated_count += 1
        else:
            # New registration
            registry.register_plugin(name, plugin_def)
            new_count += 1

    # Save registry
    registry.save_registry()

    return {
        "discovered": len(discovered),
        "new_registrations": new_count,
        "updated": updated_count,
        "total_plugins": len(registry._plugins),
        "registry_path": str(registry_path),
        "plugins": discovered,
    }
