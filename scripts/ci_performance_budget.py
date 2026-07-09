"""Release productivity score gate for v5."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from paper_workflow.bioinformatics.module_registry import ModuleRegistry  # noqa: E402
from paper_workflow.monitoring.performance_ledger import PerformanceLedger, score_productivity  # noqa: E402


def criteria(root: Path) -> dict[str, bool]:
    registry = ModuleRegistry(root)
    production_visible = registry.capability_summary()["production_visible_module_count"]
    docs = [
        root / "docs" / "V5_PRODUCTION_KERNEL_REFORM_PLAN.md",
        root / "docs" / "V5_TARGET_TASK_DESIGN.md",
        root / "docs" / "V5_SEURAT_VALIDATION_PROJECT.md",
        root / "docs" / "V5_PRODUCTIVITY_SCORECARD.md",
        root / "docs" / "RELEASE_NOTES_v5.0.0.md",
    ]
    return {
        "fail_closed": (root / "src" / "paper_workflow" / "bioinformatics" / "run_quality_rules.py").exists(),
        "target_task_entry": (root / "src" / "paper_workflow" / "target_task" / "orchestrator.py").exists() and (root / "targets" / "examples" / "pbmc3k_t_subcluster_v5.yaml").exists(),
        "production_module_ratio": production_visible >= 3,
        "environment_truth": (root / "scripts" / "check_r_environment.R").exists() and (root / "scripts" / "check_r_bioc_environment.R").exists(),
        "seurat_validation": "single_cell.seurat_subcluster_programs.v1" in registry.modules,
        "external_code_wrapper": "external.lung_master.de_table_standardizer.v1" in registry.modules,
        "documentation_truth": all(path.exists() and path.stat().st_size > 400 for path in docs),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--write-ledger", default="")
    args = parser.parse_args()
    root = Path(args.root).resolve()
    result: dict[str, Any] = score_productivity(criteria(root))
    if args.write_ledger:
        result = PerformanceLedger(root / args.write_ledger).write(criteria(root))
    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(f"Performance budget: {result['status']} score={result['score']}")
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
