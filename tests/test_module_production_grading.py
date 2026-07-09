from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from paper_workflow.bioinformatics.module_registry import FORBIDDEN_PRODUCTION_GRADES, ModuleRegistry


REPO_ROOT = Path(__file__).resolve().parent.parent


def test_v5_modules_have_explicit_production_grading():
    registry = ModuleRegistry(REPO_ROOT)
    for module_id in registry.modules:
        module = registry.get(module_id)
        assert registry.validate_module(module_id) == []
        assert module["production_capability_grade"]
        assert module["execution_evidence_level"]
        assert module["strategy_visibility"]
        assert module["claim_permission"]
        assert module["current_environment_status"]


def test_forbidden_and_blocked_modules_do_not_pass_production_gate():
    registry = ModuleRegistry(REPO_ROOT)
    for module_id, module in registry.modules.items():
        gate = registry.production_gate(module)
        if module["production_capability_grade"] in FORBIDDEN_PRODUCTION_GRADES:
            assert gate["allowed"] is False, module_id
        if module["current_environment_status"] == "blocked":
            assert gate["allowed"] is False, module_id


def test_v5_real_wrappers_are_registered_as_production_visible():
    registry = ModuleRegistry(REPO_ROOT)
    for module_id in [
        "single_cell.seurat_subcluster_programs.v1",
        "external.lung_master.de_table_standardizer.v1",
    ]:
        module = registry.get(module_id)
        assert module["production_capability_grade"] in {"production_capable_real_wrapper", "validated_workflow_pilot"}
        assert registry.production_gate(module)["allowed"] is True
