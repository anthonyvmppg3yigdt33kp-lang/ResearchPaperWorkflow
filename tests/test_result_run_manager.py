import sys
import tempfile
from pathlib import Path

import pytest
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

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


def test_run_id_validation_rejects_timestamp_only_names():
    with pytest.raises(ValueError):
        ResultRunManager.validate_run_id("20260707")
    with pytest.raises(ValueError):
        ResultRunManager.validate_run_id("bulk_de_latest")


def test_create_run_writes_required_layout(paper_dir):
    manager = ResultRunManager(paper_dir)
    manifest = manager.create_run("bulk_de_20260707_v1", notes="test run")
    run_dir = manager.run_path("bulk_de_20260707_v1")

    assert manifest["run_id"] == "bulk_de_20260707_v1"
    assert (run_dir / "run_manifest.yaml").exists()
    assert (run_dir / "parameters.yaml").exists()
    assert (run_dir / "inputs_manifest.yaml").exists()
    assert (run_dir / "outputs_manifest.yaml").exists()
    assert (run_dir / "logs").is_dir()
    assert (run_dir / "qc").is_dir()
    assert (run_dir / "tables").is_dir()
    assert (run_dir / "figures").is_dir()


def test_set_current_run_writes_pointer_without_copying_outputs(paper_dir):
    manager = ResultRunManager(paper_dir)
    manager.create_run("bulk_de_20260707_v1")
    current = manager.set_current_run(
        "bulk_de_20260707_v1",
        status="prepared",
        user_approved=True,
        notes="approved pointer update",
    )

    assert current["active_run_id"] == "bulk_de_20260707_v1"
    assert current["user_approved"] is True
    assert manager.current_run_file.exists()
    assert (manager.current_pointer_dir / "RUN_POINTER.txt").exists()
    assert (manager.current_pointer_dir / "RUN_POINTER.txt").read_text(encoding="utf-8") == str(
        manager.run_path("bulk_de_20260707_v1")
    )


def test_analysis_design_is_dry_run_and_requires_checkpoint(paper_dir):
    manager = ResultRunManager(paper_dir)
    design = manager.write_analysis_design(
        run_id="bulk_de_20260707_v1",
        goal="Design a bulk RNA-seq differential expression pilot.",
        modality="bulk_rnaseq",
        inputs=["counts.csv", "metadata.csv"],
    )

    design_path = manager.run_path("bulk_de_20260707_v1") / "analysis_design.yaml"
    saved = yaml.safe_load(design_path.read_text(encoding="utf-8"))

    assert design["execution_status"] == "not_executed"
    assert saved["required_human_checkpoint"] is True
    assert saved["modality"] == "bulk_rnaseq"
    assert saved["inputs"] == ["counts.csv", "metadata.csv"]


def test_evaluate_run_reports_missing_source_maps_without_failing_baseline(paper_dir):
    manager = ResultRunManager(paper_dir)
    manager.create_run("bulk_de_20260707_v1")
    evaluation = manager.evaluate_run("bulk_de_20260707_v1", write_report=True)
    data = evaluation.to_dict()

    assert data["status"] == "needs_fix"
    assert data["missing_required_files"] == []
    assert data["has_figure_source_map"] is False
    assert data["has_table_source_map"] is False
    assert data["source_map_valid"] is False
    assert data["source_map_issue_count"] >= 2
    assert "evidence_grade" in data
    assert data["evidence_summary"]["claim_count"] == 0
    assert (manager.run_path("bulk_de_20260707_v1") / "evaluation_report.yaml").exists()


def test_evaluate_run_writes_evidence_graph_outputs_from_source_maps(paper_dir):
    manager = ResultRunManager(paper_dir)
    manager.create_run("bulk_de_20260707_v1")
    run_dir = manager.run_path("bulk_de_20260707_v1")
    (run_dir / "figure_source_map.yaml").write_text(
        "schema_version: test\n"
        "figures:\n"
        "  - figure_id: pilot_volcano\n"
        "    path: figures/volcano_plot.svg\n"
        "    source_data: tables/de.csv\n"
        "    script: adapter.py\n"
        "    method: pilot differential expression visualization\n"
        "    statistical_unit: sample\n"
        "    claim_boundary: workflow pilot only; not publication-grade DE\n",
        encoding="utf-8",
    )
    (run_dir / "table_source_map.yaml").write_text(
        "schema_version: test\n"
        "tables:\n"
        "  - table_id: pilot_de\n"
        "    path: tables/de.csv\n"
        "    source_inputs: [counts.csv, metadata.csv]\n"
        "    method: pilot logCPM contrast\n"
        "    statistical_unit: sample\n"
        "    claim_boundary: workflow pilot only; not publication-grade DE\n",
        encoding="utf-8",
    )

    data = manager.evaluate_run("bulk_de_20260707_v1", write_report=True).to_dict()

    assert data["source_map_valid"] is True
    assert data["evidence_summary"]["claim_count"] == 2
    assert "publication_candidate_claims" in data["evidence_summary"]
    assert (run_dir / "tables" / "evidence_matrix.tsv").exists()
    assert (run_dir / "review" / "reviewer_risk_report.md").exists()
    assert (run_dir / "brief" / "FIGURE_STORYLINE.md").exists()
    assert (run_dir / "claims" / "claim_ledger.jsonl").exists()


def test_workflow_modes_config_is_parseable_and_defers_full_pipeline_by_default():
    config_path = Path(__file__).resolve().parent.parent / "config" / "workflow_modes.yaml"
    data = yaml.safe_load(config_path.read_text(encoding="utf-8"))

    assert "analysis_design_mode" in data["modes"]
    assert data["default_route"]["fuzzy_request"] == "exploration_mode"
    assert "target_journal" in data["profiles"]["exploratory_omics"]["deferred_stages"]
    assert "run_analysis" in data["profiles"]["submission_closeout"]["deferred_stages"]
