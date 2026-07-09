"""Source parsing facade for external literature-code intake."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from paper_workflow.bioinformatics.method_block_extractor import extract_method_blocks


class SourceParser:
    """Parse retained source scripts into method-block review packets."""

    def __init__(self, source_dir: Path):
        self.source_dir = Path(source_dir)

    def method_blocks(self, parsed_scripts: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return extract_method_blocks(self.source_dir, parsed_scripts)
