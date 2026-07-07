import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace

import pytest
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from paper_workflow.analysis import AnalysisDesign, run_analysis_adapter
from paper_workflow.engine.agent_dispatcher import AgentDispatcher
from paper_workflow.outputs.result_run_manager import ResultRunManager


@pytest.fixture
def paper_dir():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        paper = root / "papers" / "test_paper"
        paper.mkdir(parents=True)
        (paper / "project_passport.yaml").write_text(
            "paper_id: test_paper\npipeline_state: stale_stages\n",
            encoding="utf-8",
        )
        yield paper


def write_complete_bulk_design(manager: ResultRunManager, run_id: str) -> Path:
    manager.create_run(run_id, allow_existing=True)
    design = manager.write_analysis_design(
        run_id=run_id,
        goal="Test IgG4-ROD vs MALT-L bulk RNA-seq differential expression.",
        modality="bulk_rnaseq",
        inputs=["counts.csv", "metadata.csv"],
    )
    design.update({
        "primary_contrast": "IgG4_ROD vs MALT_L",
        "inclusion_exclusion": ["include samples with complete disease labels"],
        "covariates": ["batch"],
        "batch_or_confounder_plan": "include batch if present; otherwise document absence",
        "sensitivity_plan": ["rerun after excluding low-depth samples"],
        "user_approval": False,
    })
    design_path = manager.run_path(run_id) / "analysis_design.yaml"
    with design_path.open("w", encoding="utf-8") as fh:
        yaml.safe_dump(design, fh, allow_unicode=True, sort_keys=False)
    return design_path


def write_bulk_pilot_inputs(paper_dir: Path) -> tuple[str, str]:
    data_dir = paper_dir / "data" / "pilot"
    data_dir.mkdir(parents=True, exist_ok=True)
    counts = data_dir / "counts.csv"
    metadata = data_dir / "metadata.csv"
    counts.write_text(
        "gene,A1,A2,A3,B1,B2,B3\n"
        "CXCL13,120,130,125,10,12,9\n"
        "MS4A1,95,90,100,30,28,35\n"
        "XBP1,8,9,7,100,105,110\n"
        "PRDM1,12,11,10,90,95,93\n"
        "ACTB,50,52,48,51,49,50\n",
        encoding="utf-8-sig",
    )
    metadata.write_text(
        "sample_id,condition,batch\n"
        "A1,IgG4_ROD,b1\n"
        "A2,IgG4_ROD,b1\n"
        "A3,IgG4_ROD,b2\n"
        "B1,MALT_L,b1\n"
        "B2,MALT_L,b2\n"
        "B3,MALT_L,b2\n",
        encoding="utf-8-sig",
    )
    return (
        str(counts.relative_to(paper_dir)),
        str(metadata.relative_to(paper_dir)),
    )


def test_analysis_design_validates_complete_bulk_design(paper_dir):
    manager = ResultRunManager(paper_dir)
    design_path = write_complete_bulk_design(manager, "bulk_de_20260707_v1")

    design = AnalysisDesign.from_file(design_path)
    valid, issues = design.validate()

    assert valid, issues
    assert design.modality == "bulk_rnaseq"
    assert design.statistical_unit == "sample"


def test_skeleton_analysis_design_keeps_unresolved_fields_invalid(paper_dir):
    manager = ResultRunManager(paper_dir)
    manager.write_analysis_design(
        run_id="bulk_de_20260707_v1",
        goal="Draft a bounded analysis plan before execution.",
        modality="bulk_rnaseq",
        inputs=["counts.csv", "metadata.csv"],
    )

    design_path = manager.run_path("bulk_de_20260707_v1") / "analysis_design.yaml"
    design = AnalysisDesign.from_file(design_path)
    valid, issues = design.validate()

    assert valid is False
    assert "unresolved primary_contrast" in issues
    assert "unresolved inclusion_exclusion" in issues
    assert "unresolved batch_or_confounder_plan" in issues
    assert "unresolved sensitivity_plan" in issues


def test_bulk_dry_run_adapter_writes_execution_package(paper_dir):
    manager = ResultRunManager(paper_dir)
    design_path = write_complete_bulk_design(manager, "bulk_de_20260707_v1")
    design = AnalysisDesign.from_file(design_path)

    result = run_analysis_adapter(design, manager.run_path("bulk_de_20260707_v1"), execute=False)
    evaluation = manager.evaluate_run("bulk_de_20260707_v1", write_report=True)
    manifest = yaml.safe_load((manager.run_path("bulk_de_20260707_v1") / "run_manifest.yaml").read_text(encoding="utf-8"))

    assert result.status == "dry_run_completed"
    assert result.errors == []
    assert manifest["analysis_adapter"] == "bulk_rnaseq_deseq2_dry_run"
    assert manifest["dry_run"] is True
    assert (manager.run_path("bulk_de_20260707_v1") / "execution_blueprint.md").exists()
    assert (manager.run_path("bulk_de_20260707_v1") / "figure_source_map.yaml").exists()
    assert (manager.run_path("bulk_de_20260707_v1") / "table_source_map.yaml").exists()
    assert evaluation.has_figure_source_map is True
    assert evaluation.has_table_source_map is True


def test_real_execution_request_is_blocked_until_adapter_exists(paper_dir):
    manager = ResultRunManager(paper_dir)
    design_path = write_complete_bulk_design(manager, "bulk_de_20260707_v1")
    design = AnalysisDesign.from_file(design_path)
    design.user_approval = True

    result = run_analysis_adapter(design, manager.run_path("bulk_de_20260707_v1"), execute=True)

    assert result.status == "blocked"
    assert result.errors
    assert "real execution is not enabled" in result.errors[0]


def test_python_builtin_bulk_pilot_executes_fixture_and_writes_quality_package(paper_dir):
    manager = ResultRunManager(paper_dir)
    counts, metadata = write_bulk_pilot_inputs(paper_dir)
    design = manager.write_analysis_design(
        run_id="bulk_de_20260707_v1",
        goal="Pilot bulk RNA-seq execution test.",
        modality="bulk_rnaseq",
        inputs=[counts, metadata],
        primary_contrast="IgG4_ROD vs MALT_L",
        execution_backend="python_builtin_pilot",
    )
    design.update({
        "inclusion_exclusion": ["all pilot samples with complete labels"],
        "covariates": ["batch"],
        "batch_or_confounder_plan": "record batch; pilot does not model covariates",
        "sensitivity_plan": ["confirm signal after publication-grade DESeq2 setup"],
        "user_approval": True,
    })
    design_path = manager.run_path("bulk_de_20260707_v1") / "analysis_design.yaml"
    with design_path.open("w", encoding="utf-8") as fh:
        yaml.safe_dump(design, fh, allow_unicode=True, sort_keys=False)

    result = run_analysis_adapter(
        AnalysisDesign.from_file(design_path),
        manager.run_path("bulk_de_20260707_v1"),
        execute=True,
        backend="python_builtin_pilot",
    )
    evaluation = manager.evaluate_run("bulk_de_20260707_v1", write_report=True)
    run_dir = manager.run_path("bulk_de_20260707_v1")
    manifest = yaml.safe_load((run_dir / "run_manifest.yaml").read_text(encoding="utf-8"))

    assert result.status == "pilot_completed"
    assert result.errors == []
    assert manifest["analysis_adapter"] == "bulk_rnaseq_python_builtin_pilot"
    assert manifest["execution_status"] == "completed"
    assert manifest["metrics"]["genes_tested"] == 5
    assert (run_dir / "tables" / "differential_expression_pilot.csv").exists()
    assert (run_dir / "qc" / "sample_qc.csv").exists()
    assert (run_dir / "qc" / "pilot_quality_report.yaml").exists()
    assert (run_dir / "figures" / "volcano_plot.svg").exists()
    assert (run_dir / "figures" / "deg_heatmap.svg").exists()
    assert evaluation.has_figure_source_map is True
    assert evaluation.has_table_source_map is True
    assert evaluation.manifest_status == "pilot_completed"


def test_agent_dispatcher_uses_current_run_analysis_design(paper_dir):
    project_root = paper_dir.parents[1]
    manager = ResultRunManager(paper_dir)
    write_complete_bulk_design(manager, "bulk_de_20260707_v1")
    manager.set_current_run("bulk_de_20260707_v1", status="prepared")

    dispatcher = AgentDispatcher(project_root=project_root)
    stage_def = SimpleNamespace(agent="analysis_executor", skill="bulk-rnaseq")
    result = dispatcher.dispatch("run_analysis", stage_def, paper_dir)
    result_dict = result.to_dict() if hasattr(result, "to_dict") else result

    manifest = yaml.safe_load((manager.run_path("bulk_de_20260707_v1") / "run_manifest.yaml").read_text(encoding="utf-8"))
    assert result_dict["stage_id"] == "run_analysis"
    assert manifest["status"] == "dry_run_completed"
    assert result_dict["metrics"]["adapter_status"] == "dry_run_completed"
    assert (manager.run_path("bulk_de_20260707_v1") / "evaluation_report.yaml").exists()
