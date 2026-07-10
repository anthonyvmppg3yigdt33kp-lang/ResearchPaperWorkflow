from pathlib import Path

from paper_workflow.bioinformatics.module_registry import ModuleRegistry
from paper_workflow.bioinformatics.strategy_evaluator import StrategyEvaluator


REPO_ROOT = Path(__file__).resolve().parent.parent


def test_findmarkers_is_cell_level_exploratory_not_bulk_de():
    module = ModuleRegistry(REPO_ROOT).get("single_cell.seurat_findmarkers_group_de.v1")
    evaluation = StrategyEvaluator({"modalities": ["single_cell"], "n_samples": 8}).evaluate_module(
        module,
        "Compare disease and control cells with FindMarkers",
    )

    assert evaluation["method_family"] == "cell_level_de_exploratory"
    assert any("replicate-aware" in risk for risk in evaluation["reviewer_risk"])
    assert any("pseudobulk" in note for note in evaluation["comparison_notes"])
