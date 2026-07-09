"""Load TargetTask YAML files."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


def load_target_task(path: Path | str) -> dict[str, Any]:
    target_path = Path(path)
    if not target_path.exists():
        raise FileNotFoundError(f"TargetTask file not found: {target_path}")
    data = yaml.safe_load(target_path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise ValueError(f"TargetTask must be a YAML mapping: {target_path}")
    data["_target_path"] = str(target_path)
    return data


def write_yaml(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        yaml.safe_dump(data, fh, allow_unicode=True, sort_keys=False)
