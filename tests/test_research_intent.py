from __future__ import annotations

import shutil
from pathlib import Path

import yaml

from paper_workflow.research_intent import ResearchIntentPlanner, ResearchWorkflowOrchestrator
from paper_workflow.target_task.schema import validate_target_task


REPO_ROOT = Path(__file__).resolve().parent.parent


def copy_fixture(tmp_path: Path) -> Path:
    root = tmp_path / "repo"
    for name in ("code_library", "config", "local_experience", "intents"):
        shutil.copytree(REPO_ROOT / name, root / name)
    (root / "AGENTS.md").write_text("# test\n", encoding="utf-8")
    return root


def test_research_intent_compiles_to_target_and_dashboard(tmp_path: Path):
    root = copy_fixture(tmp_path)
    intent = root / "intents" / "examples" / "pbmc3k_t_subcluster_intent.yaml"
    orchestrator = ResearchWorkflowOrchestrator(root)

    validation = orchestrator.validate(intent)
    started = orchestrator.start(intent)

    assert validation["valid"] is True
    assert started["status"] == "planned"
    plan = started["research_plan"]
    assert plan["ready_for_target_plan"] is True
    assert "single_cell.seurat_subcluster_programs.v1" in plan["selected_modules"]
    target = yaml.safe_load(Path(plan["target_task"]).read_text(encoding="utf-8"))
    graph = yaml.safe_load(Path(started["target_plan"]["analysis_graph"]).read_text(encoding="utf-8"))
    nodes = {node["module_id"]: node for node in graph["analysis_graph"]["nodes"]}
    assert validate_target_task(target)["valid"] is True
    assert Path(plan["artifacts"]["scientific_assessment"]).exists()
    assert Path(plan["artifacts"]["strategy_simulation"]).exists()
    assert Path(plan["artifacts"]["figure_plan_markdown"]).exists()
    assert Path(started["dashboard"]["dashboard_markdown"]).exists()
    subcluster = nodes["single_cell.seurat_subcluster_programs.v1"]["parameters"]
    assert subcluster["min_subset_markers"] == 2
    assert subcluster["min_anchor_markers"] == 2
    assert subcluster["subset_anchor_markers"] == "CD3D,CD3E,NKG7,GNLY"
    assert subcluster["marker_method"] == "wilcox"
    assert "naive_memory_like=IL7R,CCR7,TCF7,LTB" in subcluster["program_spec"]


def test_research_strategy_defers_pseudobulk_without_replicates(tmp_path: Path):
    root = copy_fixture(tmp_path)
    intent_path = root / "disease_intent.yaml"
    intent_path.write_text(
        yaml.safe_dump({
            "schema_version": "research_intent.v1",
            "project_id": "disease_scrna",
            "title": "Disease cell-state comparison",
            "question": "Compare disease versus control cell-type differential expression.",
            "project_goal": "discovery",
            "claim_boundary": "Exploratory until sample-level inference is available.",
            "data": {
                "dataset_id": "scrna_v1",
                "modality": "single_cell",
                "format": "seurat_rds",
                "input_path": "data/scrna.rds",
                "role": "research_data",
                "biological_replicates": "unknown",
            },
            "scientific_questions": ["cell_type_differential_expression", "disease_group_comparison"],
            "expected_outputs": {"figures": ["volcano"], "tables": ["de_table"], "reports": ["strategy_simulation"]},
        }, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )

    plan = ResearchIntentPlanner(root).plan(intent_path)
    strategy = yaml.safe_load(Path(plan["artifacts"]["strategy_simulation"]).read_text(encoding="utf-8"))

    deferred = {item["method_id"]: item for item in strategy["deferred"]}
    recommended = {item["method_id"] for item in strategy["recommended_now"]}
    assert "pseudobulk_deseq2" in deferred
    assert "data.sample_id_column" in deferred["pseudobulk_deseq2"]["missing_prerequisites"]
    assert "seurat_findmarkers_cell_level" in recommended
    assert "single_cell.seurat_findmarkers_group_de.v1" in plan["selected_modules"]


def test_research_write_is_blocked_without_fail_closed_pass(tmp_path: Path):
    root = copy_fixture(tmp_path)
    intent = root / "intents" / "examples" / "pbmc3k_t_subcluster_intent.yaml"

    result = ResearchWorkflowOrchestrator(root).write(intent)

    assert result["status"] == "blocked"
    assert "fail-closed pass" in result["reason"]
