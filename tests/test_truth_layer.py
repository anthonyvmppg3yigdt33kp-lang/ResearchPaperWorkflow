from __future__ import annotations

import json
import tempfile
import warnings
from datetime import datetime
from pathlib import Path

from paper_workflow.api import WorkflowAPI
from paper_workflow.engine.agent_harness import AgentHarness
from paper_workflow.engine.loop_engine import PaperLoopEngine, StageDefinition, StageStatus
from paper_workflow.supervision.passport import PaperPassport
from paper_workflow.workflow import PaperWorkflow


def _root(tmpdir: str) -> Path:
    root = Path(tmpdir)
    (root / "AGENTS.md").write_text("# Test Project\n", encoding="utf-8")
    return root


def test_stage_definition_splits_quality_gates_and_transition_policy():
    raw = [{
        "id": "design_analysis_plan",
        "name": "Design SAP",
        "order": 5,
        "artifacts_out": ["statistical_analysis_plan.yaml"],
        "quality_gates": ["statistical_analysis_plan_exists"],
        "transition_policy": {
            "on_pass": {"action": "advance_to", "stage": "data_audit"},
            "on_fail": {"actions": [{"action": "retry_stage"}]},
        },
    }]
    defs = StageDefinition.from_config_stages(
        raw,
        {"statistical_analysis_plan_exists": {"severity": "critical"}},
    )
    assert defs[0].required_artifacts == ["statistical_analysis_plan.yaml"]
    assert defs[0].quality_gates == [{"rule": "statistical_analysis_plan_exists", "severity": "CRITICAL"}]
    assert defs[0].transition_policy["on_pass"]["stage"] == "data_audit"


def test_legacy_gate_rules_are_compatibility_only():
    raw = [{
        "id": "select_topic",
        "name": "Select Topic",
        "order": 1,
        "gate_rules": {
            "on_pass": ["advance_to: target_journal"],
            "on_fail": ["retry_stage", "notify_human: topic_not_feasible"],
        },
    }]
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        defs = StageDefinition.from_config_stages(raw, {})
    assert caught
    assert defs[0].quality_gates == []
    assert defs[0].transition_policy["on_pass"] == {"action": "advance_to", "stage": "target_journal"}
    assert defs[0].transition_policy["on_fail"]["actions"][0] == {"action": "retry_stage"}


def test_configured_critical_gate_fails_closed_when_not_run():
    with tempfile.TemporaryDirectory() as tmpdir:
        root = _root(tmpdir)
        engine = PaperLoopEngine(root, "paper")
        stage = engine.stages["write_methods"]
        stage.execution_mode = "real"
        stage.outputs_verified = True
        stage.required_outputs = ["manuscript/methods.md"]
        stage.definition.quality_gates = [{"rule": "definitely_not_a_real_gate", "severity": "critical"}]
        path = engine.paper_dir / "manuscript" / "methods.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("# Methods\n\nPatients were analyzed.\n", encoding="utf-8")

        verify = engine.verify_stage("write_methods")

        assert not verify["all_passed"]
        assert engine.stages["write_methods"].status == StageStatus.FAILED
        assert verify["results"][-1]["message"] == "Gate not executed (no matching result)"


def test_dispatcher_template_output_cannot_complete_stage():
    with tempfile.TemporaryDirectory() as tmpdir:
        root = _root(tmpdir)
        engine = PaperLoopEngine(root, "paper")

        run = engine.run_stage("select_topic")
        verify = engine.verify_stage("select_topic")

        assert run["success"]
        assert run["execution_mode"] == "template"
        assert not verify["all_passed"]
        assert engine.stages["select_topic"].status == StageStatus.FAILED
        pending_dir = engine.paper_dir / "workflow_state" / "pending_invocations"
        pending = list(pending_dir.glob("select_topic_*.json"))
        assert pending, "template stage should create a pending harness invocation"


def test_engine_hydrates_stage_truth_from_passport():
    with tempfile.TemporaryDirectory() as tmpdir:
        root = _root(tmpdir)
        engine = PaperLoopEngine(root, "paper")
        stage = engine.stages["select_topic"]
        stage.status = StageStatus.COMPLETED
        stage.completed_at = datetime.now().isoformat()
        stage.execution_mode = "real"
        stage.outputs_verified = True
        stage.artifacts_produced = ["research_plan/research_question.md"]
        stage.required_outputs = ["research_plan/research_question.md"]
        path = engine.paper_dir / "research_plan" / "research_question.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("# Question\n\nConcrete approved question.\n", encoding="utf-8")
        engine.record_and_sync()

        hydrated = PaperLoopEngine(root, "paper")

        assert hydrated.stages["select_topic"].status == StageStatus.COMPLETED
        assert hydrated.stages["select_topic"].execution_mode == "real"
        assert hydrated.stages["select_topic"].outputs_verified
        result_path = hydrated.paper_dir / "stage_results" / "select_topic_result.json"
        assert result_path.exists()
        assert json.loads(result_path.read_text(encoding="utf-8"))["engine_stage_status"] == "completed"


def test_artifact_drift_propagates_to_downstream_stages():
    with tempfile.TemporaryDirectory() as tmpdir:
        root = _root(tmpdir)
        engine = PaperLoopEngine(root, "paper")
        engine.stages["select_topic"].definition.produces_artifacts = ["research_plan/research_question.md"]
        path = engine.paper_dir / "research_plan" / "research_question.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("v1\n", encoding="utf-8")
        passport = PaperPassport(engine.paper_dir)
        passport.record_artifact("research_plan/research_question.md", "select_topic")
        path.write_text("v2\n", encoding="utf-8")

        result = passport.sync_artifact_stale(engine.artifact_dependency_map())

        assert "target_journal" in result["stale_stages"]
        assert "formulate_hypotheses" in result["stale_stages"]


def test_contract_required_outputs_are_produced_in_default_and_config_modes():
    with tempfile.TemporaryDirectory() as tmpdir:
        root = _root(tmpdir)
        repo_root = Path(__file__).resolve().parent.parent
        (root / "workflow_contract.yaml").write_text(
            (repo_root / "workflow_contract.yaml").read_text(encoding="utf-8"),
            encoding="utf-8",
        )
        for config_path in (None, repo_root / "config" / "default_config.yaml"):
            engine = PaperLoopEngine(
                root,
                "paper",
                config_path=config_path,
            )
            mismatches = []
            for sd in engine._active_stages:
                missing = set(sd.required_artifacts or []) - set(sd.produces_artifacts or [])
                if missing:
                    mismatches.append((sd.name, sorted(missing)))
            assert mismatches == []


def test_workflow_api_validate_contract_passes_for_repo_defaults():
    repo_root = Path(__file__).resolve().parent.parent
    result = WorkflowAPI(repo_root).validate_contract()

    assert result["valid"], result
    assert result["counts"]["config_stages"] == 20
    assert result["counts"]["contract_stages"] == 20
    assert result["counts"]["engine_stages"] == 20
    assert result["counts"]["dispatcher_handlers"] == 20
    assert result["counts"]["stage_quality_gate_refs"] > 0


def test_design_analysis_plan_real_executor_passes_core_gates():
    with tempfile.TemporaryDirectory() as tmpdir:
        root = _root(tmpdir)
        repo_root = Path(__file__).resolve().parent.parent
        (root / "workflow_contract.yaml").write_text(
            (repo_root / "workflow_contract.yaml").read_text(encoding="utf-8"),
            encoding="utf-8",
        )
        engine = PaperLoopEngine(root, "paper")

        run = engine.run_stage("design_analysis_plan")
        verify = engine.verify_stage("design_analysis_plan")

        assert run["execution_mode"] == "real"
        assert run["outputs_verified"]
        assert verify["all_passed"]
        assert engine.stages["design_analysis_plan"].status == StageStatus.COMPLETED
        rules = {item["rule"] for item in verify["results"]}
        assert {
            "statistical_analysis_plan_exists",
            "endpoint_definition_complete",
            "patient_level_independence",
        }.issubset(rules)


def test_phase1_progresses_with_human_literature_handoff_and_seed_completion():
    with tempfile.TemporaryDirectory() as tmpdir:
        root = _root(tmpdir)
        workflow = PaperWorkflow(project_root=root)
        workflow.initialize(
            idea="Spatial transcriptomics identifies patient-level ccRCC diabetes biomarkers",
            field="bioinformatics, clinical, single-cell",
            journal="Genome Biology",
        )
        engine = workflow.engine

        target_run = engine.run_stage("target_journal")
        target_verify = engine.verify_stage("target_journal")
        assert target_run["execution_mode"] == "real"
        assert target_verify["all_passed"]

        literature_run = engine.run_stage("literature_search")
        literature_verify = engine.verify_stage("literature_search")
        assert literature_run["execution_mode"] == "pending_harness"
        assert not literature_verify["all_passed"]
        assert list((engine.paper_dir / "workflow_state" / "pending_invocations").glob("literature_search_*.json"))

        seed = engine.paper_dir / "references" / "manual_seed.bib"
        seed.write_text(
            "@article{seed2026,\n"
            "  title={Verified seed reference for workflow testing},\n"
            "  author={Doe, Jane},\n"
            "  journal={Genome Biology},\n"
            "  year={2026}\n"
            "}\n",
            encoding="utf-8",
        )
        literature_run = engine.run_stage("literature_search")
        literature_verify = engine.verify_stage("literature_search")
        assert literature_run["execution_mode"] == "real"
        assert literature_verify["all_passed"]

        hypotheses_run = engine.run_stage("formulate_hypotheses")
        hypotheses_verify = engine.verify_stage("formulate_hypotheses")
        assert hypotheses_run["execution_mode"] == "real"
        assert hypotheses_verify["all_passed"]


def test_agent_harness_validates_pending_invocation_outputs_before_completion():
    with tempfile.TemporaryDirectory() as tmpdir:
        root = _root(tmpdir)
        workflow = PaperWorkflow(project_root=root)
        workflow.initialize(
            idea="Spatial transcriptomics biomarkers",
            field="bioinformatics",
            journal="Genome Biology",
        )
        engine = workflow.engine

        run = engine.run_stage("literature_search")
        verify = engine.verify_stage("literature_search")
        assert run["execution_mode"] == "pending_harness"
        assert not verify["all_passed"]

        harness = AgentHarness(engine.paper_dir)
        invocations = harness.list_invocations()
        assert invocations
        assert invocations[-1]["stage_id"] == "literature_search"

        pending_result = harness.complete_invocation("literature_search", notes="first check")
        assert pending_result["status"] == "needs_input"
        assert pending_result["placeholder_outputs"] == ["references/library.bib"]

        (engine.paper_dir / "references" / "library.bib").write_text(
            "@article{verified2026,\n"
            "  title={Verified reference},\n"
            "  author={Doe, Jane},\n"
            "  journal={Genome Biology},\n"
            "  year={2026}\n"
            "}\n",
            encoding="utf-8",
        )
        complete_result = harness.complete_invocation("literature_search", notes="verified bibtex imported")
        assert complete_result["status"] == "completed"
        assert complete_result["outputs_verified"]
        assert Path(complete_result["result_path"]).exists()

        updated = harness.list_invocations(status="completed")
        assert updated
        assert updated[-1]["outputs_verified"]


def test_workflow_api_uses_same_harness_truth_layer_as_cli():
    with tempfile.TemporaryDirectory() as tmpdir:
        root = _root(tmpdir)
        api = WorkflowAPI(root)
        created = api.create_project(
            idea="API smoke spatial transcriptomics biomarkers",
            field="bioinformatics",
            journal="Genome Biology",
            timeline_weeks=4,
        )
        paper_id = created["paper_id"]

        first_run = api.run_pipeline(paper_id, stop_on_failure=True)
        assert first_run["pipeline_state"] == "blocked"
        stage_events = [e for e in first_run["events"] if e["event"] == "stage"]
        assert [e["stage"] for e in stage_events] == ["target_journal", "literature_search"]
        assert stage_events[-1]["stopped_on_failure"]

        invocations = api.list_harness_invocations(paper_id)
        assert invocations
        assert invocations[-1]["stage_id"] == "literature_search"

        needs_input = api.complete_harness_invocation(
            paper_id,
            invocation="literature_search",
            notes="API negative path",
        )
        assert needs_input["status"] == "needs_input"
        assert needs_input["placeholder_outputs"] == ["references/library.bib"]

        library = root / "papers" / paper_id / "references" / "library.bib"
        library.write_text(
            "@article{api2026,\n"
            "  title={API verified reference},\n"
            "  author={Doe, Jane},\n"
            "  journal={Genome Biology},\n"
            "  year={2026}\n"
            "}\n",
            encoding="utf-8",
        )
        completed = api.complete_harness_invocation(
            paper_id,
            invocation="literature_search",
            notes="API positive path",
        )
        assert completed["status"] == "completed"
        assert completed["outputs_verified"]

        rerun = api.run_pipeline(paper_id, stop_on_failure=True, max_stages=1)
        rerun_events = [e for e in rerun["events"] if e["event"] == "stage"]
        assert rerun_events[0]["stage"] == "literature_search"
        assert rerun_events[0]["success"]


def test_e2e_non_dry_run_delegates_to_v4_workflow_api_truth_layer():
    with tempfile.TemporaryDirectory() as tmpdir:
        root = _root(tmpdir)
        api = WorkflowAPI(root)
        created = api.create_project(
            idea="E2E compatibility smoke",
            field="bioinformatics",
            journal="Genome Biology",
            timeline_weeks=4,
        )
        paper_id = created["paper_id"]

        from paper_workflow.e2e_workflow import E2EWorkflow, PhaseStatus

        wf = E2EWorkflow(
            paper_id=paper_id,
            project_root=root,
            auto_load=False,
        )
        reports = wf.run(
            phases=[1],
            stop_at_checkpoint=False,
            skip_optional=True,
            dry_run=False,
        )

        phase1 = reports[1]
        stages = [inv.stage for inv in phase1.skill_invocations]
        assert stages == ["target_journal", "literature_search"]
        assert all(inv.metadata.get("execution_backend") == "v4_workflow_api" for inv in phase1.skill_invocations)
        assert phase1.status == PhaseStatus.FAILED
        assert (root / "papers" / paper_id / "stage_results" / "literature_search_result.json").exists()
        assert api.list_harness_invocations(paper_id, status="pending_harness")


def test_phase2_data_methods_loop_uses_human_inputs_and_analysis_outputs():
    with tempfile.TemporaryDirectory() as tmpdir:
        root = _root(tmpdir)
        workflow = PaperWorkflow(project_root=root)
        workflow.initialize(
            idea="Clinical single-cell biomarker workflow",
            field="bioinformatics, clinical, single-cell",
            journal="Genome Biology",
        )
        engine = workflow.engine

        engine.run_stage("target_journal")
        assert engine.verify_stage("target_journal")["all_passed"]

        refs = engine.paper_dir / "references"
        refs.mkdir(parents=True, exist_ok=True)
        (refs / "manual_seed.bib").write_text(
            "@article{seed2026,\n"
            "  title={Verified seed reference},\n"
            "  author={Doe, Jane},\n"
            "  journal={Genome Biology},\n"
            "  year={2026}\n"
            "}\n",
            encoding="utf-8",
        )
        engine.run_stage("literature_search")
        assert engine.verify_stage("literature_search")["all_passed"]
        engine.run_stage("formulate_hypotheses")
        assert engine.verify_stage("formulate_hypotheses")["all_passed"]
        engine.run_stage("design_analysis_plan")
        assert engine.verify_stage("design_analysis_plan")["all_passed"]

        no_data = engine.run_stage("data_audit")
        no_data_verify = engine.verify_stage("data_audit")
        assert no_data["execution_mode"] == "needs_input"
        assert not no_data_verify["all_passed"]

        data_dir = engine.paper_dir / "data"
        data_dir.mkdir(parents=True, exist_ok=True)
        (data_dir / "data_inventory_input.yaml").write_text(
            "statistical_unit: patient\n"
            "n_patients: 12\n"
            "batch_variables: [center, platform]\n"
            "data_types: [single_cell, clinical_metadata]\n"
            "files:\n"
            "  - path: data/raw/clinical_metadata.csv\n"
            "    size_bytes: 128\n",
            encoding="utf-8",
        )
        data_run = engine.run_stage("data_audit")
        assert data_run["execution_mode"] == "real"
        assert engine.verify_stage("data_audit")["all_passed"]

        figure_run = engine.run_stage("figure_planning")
        assert figure_run["execution_mode"] == "real"
        assert engine.verify_stage("figure_planning")["all_passed"]

        pending_analysis = engine.run_stage("run_analysis")
        pending_verify = engine.verify_stage("run_analysis")
        assert pending_analysis["execution_mode"] == "pending_harness"
        assert not pending_verify["all_passed"]

        outputs_dir = engine.paper_dir / "results" / "analysis_outputs"
        outputs_dir.mkdir(parents=True, exist_ok=True)
        (outputs_dir / "primary_results.csv").write_text(
            "endpoint,effect_size,ci_low,ci_high,p_value\nprimary,1.2,0.3,2.1,0.01\n",
            encoding="utf-8",
        )
        analysis_run = engine.run_stage("run_analysis")
        assert analysis_run["execution_mode"] == "real"
        assert engine.verify_stage("run_analysis")["all_passed"]

        methods_run = engine.run_stage("verify_methods")
        methods_verify = engine.verify_stage("verify_methods")
        assert methods_run["execution_mode"] == "real"
        assert methods_verify["all_passed"]
        assert engine.stages["verify_methods"].status == StageStatus.COMPLETED


def test_validate_workflow_flags_completed_template_stage():
    with tempfile.TemporaryDirectory() as tmpdir:
        root = _root(tmpdir)
        engine = PaperLoopEngine(root, "paper")
        stage = engine.stages["select_topic"]
        stage.status = StageStatus.COMPLETED
        stage.execution_mode = "template"
        stage.outputs_verified = False
        stage.required_outputs = ["research_plan/research_question.md"]
        engine.record_and_sync()

        result = engine.validate_workflow()

        codes = {issue["code"] for issue in result["issues"]}
        assert not result["valid"]
        assert "completed_missing_outputs" in codes
        assert "completed_non_real_execution" in codes


def test_validate_workflow_flags_failed_stage_state():
    with tempfile.TemporaryDirectory() as tmpdir:
        root = _root(tmpdir)
        engine = PaperLoopEngine(root, "paper")
        stage = engine.stages["write_methods"]
        stage.status = StageStatus.FAILED
        stage.execution_mode = "template"
        stage.gate_results = [{
            "rule": "real_execution_required",
            "severity": "critical",
            "passed": False,
            "message": "template output",
        }]
        engine.record_and_sync()

        result = engine.validate_workflow()

        codes = {issue["code"] for issue in result["issues"]}
        assert not result["valid"]
        assert "stage_not_passed" in codes


def test_completed_checkpoint_stage_blocks_until_approved():
    with tempfile.TemporaryDirectory() as tmpdir:
        root = _root(tmpdir)
        engine = PaperLoopEngine(root, "paper")
        stage = engine.stages["select_topic"]
        stage.status = StageStatus.COMPLETED
        stage.completed_at = datetime.now().isoformat()
        stage.execution_mode = "real"
        stage.outputs_verified = True
        stage.required_outputs = ["research_plan/research_question.md"]
        path = engine.paper_dir / "research_plan" / "research_question.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("# Question\n\nApproved direction.\n", encoding="utf-8")
        engine.record_and_sync()

        assert engine.decide_next_stage() is None
        assert engine.pipeline_state.value == "checkpoint_required"
        validation = engine.validate_workflow()
        assert not validation["valid"]
        assert "checkpoint_required" in {issue["code"] for issue in validation["issues"]}

        PaperPassport(engine.paper_dir).record_checkpoint("select_topic", "approved", "author approved")

        assert engine.decide_next_stage() == "target_journal"


def test_phase3_writing_and_assembly_real_executor_from_verified_artifacts():
    with tempfile.TemporaryDirectory() as tmpdir:
        root = _root(tmpdir)
        repo_root = Path(__file__).resolve().parent.parent
        (root / "workflow_contract.yaml").write_text(
            (repo_root / "workflow_contract.yaml").read_text(encoding="utf-8"),
            encoding="utf-8",
        )
        workflow = PaperWorkflow(project_root=root)
        workflow.initialize(
            idea="Clinical single-cell biomarker workflow",
            field="bioinformatics, clinical, single-cell",
            journal="Genome Biology",
        )
        engine = workflow.engine

        engine.run_stage("target_journal")
        assert engine.verify_stage("target_journal")["all_passed"]
        refs = engine.paper_dir / "references"
        refs.mkdir(parents=True, exist_ok=True)
        (refs / "manual_seed.bib").write_text(
            "@article{seed2026,\n"
            "  title={Verified seed reference},\n"
            "  author={Doe, Jane},\n"
            "  journal={Genome Biology},\n"
            "  year={2026}\n"
            "}\n",
            encoding="utf-8",
        )
        for stage in ["literature_search", "formulate_hypotheses", "design_analysis_plan"]:
            engine.run_stage(stage)
            assert engine.verify_stage(stage)["all_passed"]
        passport = PaperPassport(engine.paper_dir)
        passport.record_checkpoint("formulate_hypotheses", "approved", "test approval")
        passport.record_checkpoint("design_analysis_plan", "approved", "test approval")

        data_dir = engine.paper_dir / "data"
        data_dir.mkdir(parents=True, exist_ok=True)
        (data_dir / "data_inventory_input.yaml").write_text(
            "statistical_unit: patient\n"
            "n_patients: 24\n"
            "n_samples: 24\n"
            "batch_variables: [center, platform]\n"
            "data_types: [single_cell, clinical_metadata]\n"
            "files:\n"
            "  - path: data/raw/clinical_metadata.csv\n"
            "    size_bytes: 128\n",
            encoding="utf-8",
        )
        for stage in ["data_audit", "figure_planning"]:
            engine.run_stage(stage)
            assert engine.verify_stage(stage)["all_passed"]
        passport.record_checkpoint("figure_planning", "approved", "test approval")
        outputs_dir = engine.paper_dir / "results" / "analysis_outputs"
        outputs_dir.mkdir(parents=True, exist_ok=True)
        (outputs_dir / "primary_results.csv").write_text(
            "endpoint,effect_size,ci_lower,ci_upper,p_value,test,n_patients\n"
            "primary,0.42,0.18,0.66,0.004,linear model,24\n",
            encoding="utf-8",
        )

        for stage in [
            "run_analysis",
            "verify_methods",
            "write_methods",
            "write_results",
            "write_introduction",
            "write_discussion",
            "assemble_manuscript",
        ]:
            run = engine.run_stage(stage)
            verify = engine.verify_stage(stage)
            assert run["execution_mode"] == "real"
            assert verify["all_passed"], verify
            assert engine.stages[stage].status == StageStatus.COMPLETED

        engine.record_and_sync()
        validation = engine.validate_workflow()
        assert validation["valid"], validation
        assert (engine.paper_dir / "claims" / "claim_ledger.jsonl").exists()
        result_payload = json.loads(
            (engine.paper_dir / "stage_results" / "write_results_result.json").read_text(encoding="utf-8")
        )
        assert result_payload["engine_stage_status"] == "completed"
        assert {g["rule"] for g in result_payload["quality_gate_results"]} >= {
            "results_no_citations",
            "claim_artifact_binding",
            "statistics_reported",
        }
