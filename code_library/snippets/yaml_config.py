"""
YAML Config Loader Snippet - Hierarchical YAML configuration.

Usage:
    from snippets.yaml_config import YAMLConfigLoader

    loader = YAMLConfigLoader("config/")
    config = loader.load("params_qc")

    # With tissue-type override
    config = loader.load_qc_config(tissue_type="ffpe")
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

import yaml


class YAMLConfigLoader:
    """
    Hierarchical YAML configuration loader.

    Priority (highest to lowest):
    1. Sample-specific config
    2. Tissue-type config (e.g., ffpe, fresh)
    3. Default config
    """

    def __init__(self, config_dir: str):
        self.config_dir = Path(config_dir)
        self._cache: dict[str, dict] = {}

    def load(self, config_name: str) -> dict[str, Any]:
        """
        Load a config file by name.

        Args:
            config_name: Config name (without .yaml extension)

        Returns:
            Config dict
        """
        if config_name in self._cache:
            return self._cache[config_name]

        config_path = self.config_dir / f"{config_name}.yaml"
        if not config_path.exists():
            raise FileNotFoundError(f"Config not found: {config_path}")

        with open(config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)

        self._cache[config_name] = config
        return config

    def load_with_override(
        self,
        config_name: str,
        override: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Load config with override dict.

        Args:
            config_name: Base config name
            override: Override values

        Returns:
            Merged config
        """
        config = self.load(config_name)
        return self._merge(config, override)

    def load_tissue_config(
        self,
        config_name: str,
        tissue_type: str
    ) -> dict[str, Any]:
        """
        Load config with tissue-type override.

        Args:
            config_name: Config name
            tissue_type: Tissue type (fresh, ffpe, kidney_fresh, etc.)

        Returns:
            Config with tissue-type overrides applied
        """
        config = self.load(config_name)

        # Look for tissue-specific thresholds in qc_thresholds.yaml
        thresholds_path = self.config_dir / "qc_thresholds.yaml"
        if thresholds_path.exists():
            with open(thresholds_path, "r", encoding="utf-8") as f:
                thresholds = yaml.safe_load(f)

            if tissue_type in thresholds:
                override = thresholds[tissue_type]
                config = self._merge(config, override)

        return config

    def _merge(self, base: dict, override: dict) -> dict:
        """Deep merge two dicts."""
        result = base.copy()
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge(result[key], value)
            else:
                result[key] = value
        return result

    def get(
        self,
        config_name: str,
        *keys: str,
        default: Any = None
    ) -> Any:
        """
        Get a specific config value by dot-path keys.

        Args:
            config_name: Config name
            *keys: Dot-path keys (e.g., "filter", "mt_pct_max")
            default: Default value if not found

        Returns:
            Config value
        """
        config = self.load(config_name)
        for key in keys:
            if isinstance(config, dict) and key in config:
                config = config[key]
            else:
                return default
        return config

    def reload(self) -> None:
        """Clear cache and reload."""
        self._cache.clear()


def load_config(config_name: str, config_dir: str = "config") -> dict:
    """
    Convenience function to load a config.

    Args:
        config_name: Config name
        config_dir: Config directory

    Returns:
        Config dict
    """
    loader = YAMLConfigLoader(config_dir)
    return loader.load(config_name)
