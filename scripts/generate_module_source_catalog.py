#!/usr/bin/env python
"""Generate the clickable module source catalog under code_library/modules."""

from __future__ import annotations

from pathlib import Path

from paper_workflow.bioinformatics.method_asset_audit import MethodAssetAuditor


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    catalog = root / "code_library" / "modules" / "MODULE_SOURCE_CATALOG.md"
    catalog.write_text(MethodAssetAuditor(root).render_source_catalog(), encoding="utf-8")
    print(catalog)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
