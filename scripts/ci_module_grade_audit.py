"""CI gate for v5 module production grading."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from paper_workflow.bioinformatics.module_registry import (  # noqa: E402
    ENVIRONMENT_STATUSES,
    EXECUTION_EVIDENCE_LEVELS,
    FORBIDDEN_PRODUCTION_GRADES,
    PRODUCTION_CAPABILITY_GRADES,
    STRATEGY_VISIBILITY,
    CLAIM_PERMISSIONS,
    ModuleRegistry,
)


def audit(root: Path) -> dict[str, Any]:
    registry = ModuleRegistry(root)
    issues: list[str] = []
    production_visible = []
    for module_id, module in registry.modules.items():
        issues.extend(f"{module_id}: {issue}" for issue in registry.validate_module(module_id))
        values = {
            "production_capability_grade": (module.get("production_capability_grade"), PRODUCTION_CAPABILITY_GRADES),
            "execution_evidence_level": (module.get("execution_evidence_level"), EXECUTION_EVIDENCE_LEVELS),
            "strategy_visibility": (module.get("strategy_visibility"), STRATEGY_VISIBILITY),
            "claim_permission": (module.get("claim_permission"), CLAIM_PERMISSIONS),
            "current_environment_status": (module.get("current_environment_status"), ENVIRONMENT_STATUSES),
        }
        for key, (value, allowed) in values.items():
            if value not in allowed:
                issues.append(f"{module_id}: invalid {key}={value}")
        gate = registry.production_gate(module)
        if registry.is_production_visible(module):
            production_visible.append(module_id)
        if module.get("production_capability_grade") in FORBIDDEN_PRODUCTION_GRADES and gate["allowed"]:
            issues.append(f"{module_id}: forbidden grade passed production gate")
        if module.get("current_environment_status") == "blocked" and gate["allowed"]:
            issues.append(f"{module_id}: blocked environment passed production gate")
    return {
        "schema_version": "module_grade_audit.v1",
        "status": "pass" if not issues else "fail",
        "module_count": len(registry.modules),
        "production_visible_module_count": len(production_visible),
        "production_visible_modules": production_visible,
        "issues": issues,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args()
    result = audit(Path(args.root).resolve())
    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(f"Module grade audit: {result['status']} ({len(result['issues'])} issue(s))")
        for issue in result["issues"]:
            print(f"- {issue}")
    return 0 if result["status"] == "pass" or not args.strict else 1


if __name__ == "__main__":
    raise SystemExit(main())
