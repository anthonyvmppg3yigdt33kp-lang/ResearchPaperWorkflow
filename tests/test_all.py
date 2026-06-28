"""
Integration tests for the Research Paper Workflow Framework.

5 test suites covering all layers:
  1. Strategy Layer — topic selection, journal targeting, feasibility, hypothesis generation
  2. Passport System — initialize, record artifact, detect drift, checkpoints, integrity events
  3. Loop Engine — 18 stages init, observe state, decide next stage, run stage, verify, diagnose
  4. Integrity Gates — empty checks, section checks, citation checks, statistics checks, markdown report
  5. Full Integration — PaperWorkflow create, initialize, run stages, diagnose, save state

Run with:
    python tests/test_all.py
    python -m pytest tests/test_all.py -v
"""
from __future__ import annotations

import json
import sys
import tempfile
from datetime import datetime
from pathlib import Path

# Ensure the src directory is on sys.path
_src_dir = Path(__file__).resolve().parent.parent / "src"
if str(_src_dir) not in sys.path:
    sys.path.insert(0, str(_src_dir))


# ============================================================================
# Helpers
# ============================================================================

def _make_project_root(tmpdir: str) -> Path:
    """Create a minimal project root with AGENTS.md marker."""
    root = Path(tmpdir)
    (root / "AGENTS.md").write_text("# Test Project\n", encoding="utf-8")
    (root / "config").mkdir(exist_ok=True)
    (root / "config" / "journal_database.yaml").write_text("""journals:
  Genome Biology:
    full_name: "Genome Biology"
    impact_factor: 12.0
    category: specialty-high
    format_type: LaTeX
    citation_style: Vancouver
    abstract_word_limit: 250
    figure_limit: 8
    main_text_word_limit: 5000
    requires_data_availability: true
    requires_code_availability: true
    open_access: true
    submission_system: "Editorial Manager"
    special_requirements: ["Open access"]
    scope_keywords: [genomics, transcriptomics, bioinformatics, single-cell, spatial]
  Nature Genetics:
    full_name: "Nature Genetics"
    impact_factor: 30.0
    category: high-impact
    format_type: LaTeX
    citation_style: Vancouver
    abstract_word_limit: 150
    figure_limit: 6
    main_text_word_limit: 3000
    requires_data_availability: true
    requires_code_availability: true
    open_access: false
    submission_system: "Editorial Manager"
    special_requirements: ["Structured abstract"]
    scope_keywords: [genetics, genomics, transcriptomics, gene regulation]
  Bioinformatics:
    full_name: "Bioinformatics (Oxford)"
    impact_factor: 5.0
    category: methods
    format_type: LaTeX
    citation_style: Vancouver
    abstract_word_limit: 250
    figure_limit: 8
    main_text_word_limit: 5000
    requires_data_availability: true
    requires_code_availability: true
    open_access: false
    submission_system: "ScholarOne"
    special_requirements: ["Software/tool available"]
    scope_keywords: [bioinformatics, computational biology, software, methods]
""", encoding="utf-8")
    return root


# ============================================================================
# Suite 1: Strategy Layer
# ============================================================================

def test_strategy_layer():
    """Test Strategy Layer: topic selection, journal targeting, feasibility, hypothesis generation."""
    print("=" * 60)
    print("Test Suite 1: Strategy Layer")
    print("=" * 60)

    from paper_workflow.strategy.topic_selector import TopicSelector
    from paper_workflow.strategy.journal_targeter import JournalTargeter
    from paper_workflow.strategy.feasibility import FeasibilityAssessor
    from paper_workflow.strategy.hypothesis_framework import HypothesisFramework
    from paper_workflow.strategy.research_strategy import ResearchStrategyManager

    # --- TopicSelector ---
    selector = TopicSelector()

    # Basic selection
    topic = selector.select_topic(
        "Single-cell transcriptomics reveals disease mechanisms in kidney",
        "single-cell, nephrology, disease"
    )
    assert topic.idea, "[FAIL] Topic should have idea"
    assert len(topic.keywords) > 0, "[FAIL] Topic should have keywords"
    assert len(topic.research_questions) > 0, "[FAIL] Topic should have research questions"
    assert 1 <= topic.innovation_level <= 5, "[FAIL] Innovation level out of range"
    print(f"  [OK] TopicSelector basic — innovation={topic.innovation_level}, scope={topic.scope}, "
          f"keywords={len(topic.keywords)}, questions={len(topic.research_questions)}")

    # Innovation scoring
    low_innov_topic = selector.select_topic("replicate known analysis", "genomics")
    assert low_innov_topic.innovation_level <= 3
    print(f"  [OK] Innovation scoring low — level={low_innov_topic.innovation_level}")

    # Scope detection: atlas/resource → resource
    atlas_topic = selector.select_topic("cell atlas resource", "single-cell, atlas")
    assert atlas_topic.scope == "resource"
    print(f"  [OK] Scope detection: atlas → {atlas_topic.scope}")

    # Scope detection: pilot/preliminary → preliminary
    pilot_topic = selector.select_topic("pilot study", "exploratory")
    assert pilot_topic.scope == "preliminary"
    print(f"  [OK] Scope detection: pilot → {pilot_topic.scope}")

    # Data type detection (spatial field triggers Spatial transcriptomics)
    spatial_topic = selector.select_topic("cell atlas resource", "spatial transcriptomics, atlas")
    assert "Spatial transcriptomics" in spatial_topic.data_types, (
        f"Expected Spatial transcriptomics in {spatial_topic.data_types}")
    print(f"  [OK] Data type detection: {spatial_topic.data_types}")

    # Topic to_dict
    d = topic.to_dict()
    assert d["idea"] == topic.idea
    print(f"  [OK] Topic to_dict")

    # --- JournalTargeter ---
    with tempfile.TemporaryDirectory() as tmpdir:
        root = _make_project_root(tmpdir)
        targeter = JournalTargeter(root)

        # Exact match
        journal = targeter.resolve_journal("Genome Biology")
        assert journal.name == "Genome Biology"
        assert journal.impact_factor == 12.0
        assert journal.open_access is True
        print(f"  [OK] JournalTargeter exact match — {journal.name} (IF {journal.impact_factor})")

        # Fuzzy match
        fuzzy = targeter.resolve_journal("Nature Genetics journal")
        assert fuzzy.name == "Nature Genetics"
        print(f"  [OK] JournalTargeter fuzzy match — '{fuzzy.name}'")

        # Unknown journal fallback
        unknown = targeter.resolve_journal("Unknown Journal XYZ")
        assert unknown.fit_score == 1
        assert "not in database" in unknown.fit_reasoning
        print(f"  [OK] JournalTargeter unknown fallback — fit={unknown.fit_score}")

        # Recommend journal
        recommended = targeter.recommend_journal(topic)
        assert recommended.name
        assert recommended.fit_score >= 1
        print(f"  [OK] Journal recommendation — {recommended.name} (fit={recommended.fit_score})")

        # Compliance checklist
        checklist = targeter.get_compliance_checklist(journal)
        assert len(checklist) >= 7
        assert any(c["item"] == "Abstract word limit" for c in checklist)
        print(f"  [OK] Compliance checklist — {len(checklist)} items")

        # List journals
        all_journals = targeter.list_journals()
        assert len(all_journals) >= 3
        print(f"  [OK] List journals — {len(all_journals)} total")

        high_impact = targeter.list_journals(category="high-impact")
        assert len(high_impact) >= 1
        print(f"  [OK] List journals (high-impact) — {len(high_impact)} total")

        # --- FeasibilityAssessor ---
        assessor = FeasibilityAssessor(root)
        report = assessor.assess(topic=topic, journal=journal)
        assert report.overall_score > 0, "[FAIL] Feasibility score should be positive"
        assert report.go_no_go in ("go", "conditional_go", "no_go"), "[FAIL] Invalid go/no-go"
        assert report.timeline_feasible in (True, False)
        print(f"  [OK] Feasibility basic — score={report.overall_score}, go/no-go={report.go_no_go}")

        # Feasibility report to_dict
        rd = report.to_dict()
        assert rd["go_no_go"] == report.go_no_go
        print(f"  [OK] Feasibility to_dict")

        # Minimal data (no data types → low score)
        sparse_topic = selector.select_topic("test idea", "unknown")
        sparse_topic.data_types = []
        sparse_topic.methods_required = []
        sparse_report = assessor.assess(topic=sparse_topic, journal=journal)
        assert sparse_report.data_score <= 2.0
        print(f"  [OK] Feasibility sparse data — data_score={sparse_report.data_score}")

        # Small sample size
        small_topic = selector.select_topic("test", "test")
        small_topic.estimated_sample_size = 2
        small_report = assessor.assess(topic=small_topic, journal=journal)
        has_sample_concern = any("small" in c.lower() for c in small_report.data_concerns)
        print(f"  [OK] Feasibility small sample — concerns={'yes' if has_sample_concern else 'no'}")

        # --- HypothesisFramework ---
        framework = HypothesisFramework(root)
        hypotheses = framework.generate_hypotheses(topic=topic, feasibility=report)
        assert len(hypotheses) >= 3, f"[FAIL] Expected >=3 hypotheses, got {len(hypotheses)}"
        assert hypotheses[0].category == "primary"
        assert hypotheses[0].id == "H-C1"
        print(f"  [OK] HypothesisFramework — {len(hypotheses)} hypotheses (H1={hypotheses[0].type})")

        # Add evidence and validate
        h1 = hypotheses[0]
        assert h1.confidence == "hypothesis"
        h1.add_evidence("Spatial expression map of key markers")
        h1.add_evidence("Statistical test results with effect sizes", supports=True)
        h1.add_evidence("Contradicting result from pilot", supports=False)
        assert len(h1.supporting_data) == 2
        assert len(h1.contradicting_data) == 1
        print(f"  [OK] Hypothesis evidence — supporting={len(h1.supporting_data)}, "
              f"contradicting={len(h1.contradicting_data)}")

        # Validate (partial evidence)
        val = framework.validate_hypothesis(h1)
        assert "required_evidence_met" in val
        assert "required_evidence_missing" in val
        print(f"  [OK] Hypothesis validation — met={len(val['required_evidence_met'])}, "
              f"missing={len(val['required_evidence_missing'])}")

        # Confidence upgrade
        h1.update_confidence("supported")
        assert h1.confidence == "supported"
        print(f"  [OK] Hypothesis confidence upgrade — {h1.confidence}")

        # Hypothesis to_dict
        hd = h1.to_dict()
        assert hd["id"] == "H-C1"
        print(f"  [OK] Hypothesis to_dict")

        # --- ResearchStrategyManager ---
        manager = ResearchStrategyManager(root)
        strategy = manager.create_strategy(
            idea="Single-cell analysis of disease mechanisms",
            field="single-cell, disease",
            target_journal="Genome Biology",
            timeline_weeks=4,
        )
        assert strategy.status == "ready", f"[FAIL] Strategy status should be ready, got {strategy.status}"
        assert strategy.topic is not None
        assert strategy.journal_target is not None
        assert strategy.feasibility is not None
        assert len(strategy.hypotheses) >= 3
        assert len(strategy.phases) == 4  # timeline_weeks=4
        assert len(strategy.risks) >= 0
        assert len(strategy.dependencies) >= 6
        print(f"  [OK] ResearchStrategyManager create — id={strategy.strategy_id}, "
              f"hypotheses={len(strategy.hypotheses)}, phases={len(strategy.phases)}")

        # Save strategy
        saved = manager.save_strategy(strategy)
        assert saved.exists()
        assert saved.suffix == ".yaml"
        print(f"  [OK] Strategy saved — {saved.name}")

        # Print summary
        summary = manager.print_summary(strategy)
        assert strategy.strategy_id in summary
        print(f"  [OK] Strategy summary — {len(summary)} chars")

        # Strategy to_dict
        sd = strategy.to_dict()
        assert sd["strategy_id"] == strategy.strategy_id
        print(f"  [OK] Strategy to_dict")

        # Create strategy without journal (auto-recommend)
        strategy2 = manager.create_strategy(
            idea="Aging spatial atlas of kidney",
            field="spatial transcriptomics, aging",
        )
        assert strategy2.journal_target is not None
        print(f"  [OK] Strategy auto-journal — {strategy2.journal_target.name}")

    print("  Suite 1: ALL PASSED\n")


# ============================================================================
# Suite 2: Passport System
# ============================================================================

def test_passport_system():
    """Test Passport System: initialize, record artifact, detect drift, checkpoints, integrity events."""
    print("=" * 60)
    print("Test Suite 2: Passport System")
    print("=" * 60)

    from paper_workflow.supervision.passport import PaperPassport

    with tempfile.TemporaryDirectory() as tmpdir:
        paper_dir = Path(tmpdir) / "test_paper"
        passport = PaperPassport(paper_dir)

        # --- Initialize ---
        data = passport.initialize(
            idea="Test paper about spatial transcriptomics",
            field="spatial transcriptomics",
            target_journal="Genome Biology",
        )
        assert data["status"] == "initialized"
        assert data["paper_type"] == "original_research"
        assert "paper_" in data["paper_id"]
        assert data["target_journal"] == "Genome Biology"
        assert passport.passport_path.exists()
        print(f"  [OK] Initialize — id={data['paper_id']}, status={data['status']}")

        # --- Record artifact ---
        test_file = paper_dir / "manuscript"
        test_file.mkdir(parents=True, exist_ok=True)
        (test_file / "introduction.md").write_text("Introduction content.", encoding="utf-8")

        entry = passport.record_artifact("manuscript/introduction.md", stage="write_introduction")
        assert entry.hash_sha256 != "pending"
        assert entry.status == "active"
        assert entry.size_bytes > 0
        print(f"  [OK] Record artifact — hash={entry.hash_sha256[:16]}..., size={entry.size_bytes}B")

        # Record same artifact again (no change → should be no-op)
        entry2 = passport.record_artifact("manuscript/introduction.md", stage="write_introduction")
        assert entry2.hash_sha256 == entry.hash_sha256
        print(f"  [OK] Re-record artifact (no change) — hash unchanged")

        # Record artifact that does not exist on disk
        ghost_entry = passport.record_artifact("nonexistent/file.md", stage="test", compute_hash=True)
        assert ghost_entry.hash_sha256 == "pending"
        assert ghost_entry.size_bytes == 0
        print(f"  [OK] Record missing artifact — hash='pending'")

        # --- Detect drift (none for the real file; ghost file shows as deleted) ---
        drifted = passport.detect_artifact_drift()
        # ghost file does not exist on disk → detected as deleted
        assert len(drifted) >= 1
        assert any(d["path"] == "nonexistent/file.md" and d["status"] == "deleted" for d in drifted)
        print(f"  [OK] Drift detection — {len(drifted)} drifted (ghost=deleted)")

        # --- Modify and detect drift ---
        (test_file / "introduction.md").write_text("Modified introduction content.", encoding="utf-8")
        drifted = passport.detect_artifact_drift()
        # Should find at least the modified file (ghost file also shows as deleted)
        assert len(drifted) >= 1
        assert any(d["path"] == "manuscript/introduction.md" and d["status"] == "modified" for d in drifted), (
            f"Expected modified drift for manuscript/introduction.md in {drifted}")
        print(f"  [OK] Drift detected — {len(drifted)} items, modification confirmed")

        # --- Sync artifact stale ---
        dep_map = {"manuscript/introduction.md": ["write_results", "write_discussion"]}
        sync_result = passport.sync_artifact_stale(dep_map)
        assert sync_result["stale_count"] == 2
        assert "write_results" in sync_result["stale_stages"]
        assert "write_discussion" in sync_result["stale_stages"]
        print(f"  [OK] Sync stale — {sync_result['stale_count']} stages: {sync_result['stale_stages']}")

        # --- Re-record artifact to sync hash (clears the drift) ---
        passport.record_artifact("manuscript/introduction.md", stage="write_introduction")
        # Now drift should be only the ghost file (not in dep_map)
        sync2 = passport.sync_artifact_stale(dep_map)
        assert sync2["stale_count"] == 0, (
            f"Expected 0 stale after re-record, got {sync2['stale_count']}: {sync2['stale_stages']}")
        print(f"  [OK] Sync stale (after re-record) — {sync2['stale_count']} stages")

        # --- Record checkpoint ---
        cp = passport.record_checkpoint("write_introduction", "approved", "Prose looks good, proceed.")
        assert cp.decision == "approved"
        assert cp.stage == "write_introduction"
        assert cp.checkpoint_id.startswith("cp_")
        assert passport.checkpoint_ledger_path.exists()
        print(f"  [OK] Record checkpoint — {cp.checkpoint_id}")

        # Another checkpoint
        cp2 = passport.record_checkpoint("figure_planning", "approved", "6 figures, clear layout")
        assert len(passport.checkpoints) == 2
        print(f"  [OK] Record second checkpoint — total={len(passport.checkpoints)}")

        # --- Record integrity event ---
        ie = passport.record_integrity_event("gate_run", {"passed": True, "critical_failures": 0})
        assert ie.event_type == "gate_run"
        assert ie.details["passed"] is True
        assert passport.integrity_ledger_path.exists()
        print(f"  [OK] Record integrity event — {ie.event_id}")

        ie2 = passport.record_integrity_event("drift_detected", {"artifact": "manuscript/introduction.md"})
        print(f"  [OK] Record second integrity event — {ie2.event_id}")

        # --- Export summary ---
        summary = passport.export_summary()
        assert summary["total_artifacts"] == 2  # introduction.md + ghost
        assert summary["total_checkpoints"] == 2
        assert summary["total_integrity_events"] >= 5  # stale_sync + drift_detected + stale_sync + gate_run + drift_detected
        assert summary["paper_id"] == data["paper_id"]
        assert summary["artifact_summary"]["active"] == 1
        assert summary["artifact_summary"]["modified"] == 1
        print(f"  [OK] Export summary — artifacts={summary['total_artifacts']}, "
              f"checkpoints={summary['total_checkpoints']}, events={summary['total_integrity_events']}")

        # --- Entries to_dict ---
        ad = entry.to_dict()
        assert ad["path"] == "manuscript/introduction.md"
        cpd = cp.to_dict()
        assert cpd["decision"] == "approved"
        ied = ie.to_dict()
        assert ied["event_type"] == "gate_run"
        print(f"  [OK] All entries to_dict")

        # --- Deleted file detection ---
        (test_file / "introduction.md").unlink()
        drifted2 = passport.detect_artifact_drift()
        # Both intro (just deleted) + ghost (never existed) show as deleted
        assert len(drifted2) >= 1
        assert any(d["path"] == "manuscript/introduction.md" and d["status"] == "deleted" for d in drifted2), (
            f"Expected intro.md as deleted in {drifted2}")
        print(f"  [OK] Deleted file detected — {len(drifted2)} items, intro.md confirmed deleted")

    print("  Suite 2: ALL PASSED\n")


# ============================================================================
# Suite 3: Loop Engine
# ============================================================================

def test_loop_engine():
    """Test Loop Engine: 18 stages init, observe state, decide next stage, run stage, verify, diagnose."""
    print("=" * 60)
    print("Test Suite 3: Paper Loop Engine")
    print("=" * 60)

    from paper_workflow.engine.loop_engine import (
        PaperLoopEngine, StageStatus, PipelineState,
        StageDefinition, StageState,
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        (root / "AGENTS.md").write_text("# Test Project\n", encoding="utf-8")

        engine = PaperLoopEngine(root, paper_id="test_paper")

        # --- 18 stages initialized ---
        assert len(engine.stages) == 20, f"[FAIL] Expected 20 stages, got {len(engine.stages)}"
        all_pending = all(s.status == StageStatus.PENDING for s in engine.stages.values())
        assert all_pending
        print(f"  [OK] {len(engine.stages)} stages initialized (all pending)")

        # --- Observe state ---
        state = engine.observe()
        assert state["paper_id"] == "test_paper"
        assert state["pipeline_state"] == "clean"
        assert "stages" in state
        assert "timestamp" in state
        print(f"  [OK] Observe state — pipeline={state['pipeline_state']}, "
              f"stages={len(state['stages'])}")

        # --- decide_next_stage: first stage should be create_project ---
        next_s = engine.decide_next_stage()
        assert next_s == "select_topic", f"[FAIL] Expected select_topic, got {next_s}"
        print(f"  [OK] First next stage — {next_s}")

        # --- Run stage ---
        result = engine.run_stage(next_s)
        assert result["success"], f"[FAIL] Run should succeed: {result}"
        assert result["agent"] == "research_strategist"
        assert result["skill"] == "topic_research"
        assert engine.stages[next_s].status == StageStatus.RUNNING
        print(f"  [OK] Run stage — {result['agent']}/{result['skill']}")

        # --- Verify stage: scaffold/template output should not pass truth gates ---
        verify = engine.verify_stage(next_s)
        assert not verify["all_passed"], f"[FAIL] Template output should not pass: {verify}"
        assert engine.stages[next_s].status == StageStatus.FAILED
        assert engine.stages[next_s].execution_mode == "template"
        print(f"  [OK] Verify stage — all_passed={verify['all_passed']}")

        # Manually approve select_topic to continue testing dependency routing.
        engine.stages[next_s].status = StageStatus.COMPLETED
        engine.stages[next_s].completed_at = datetime.now().isoformat()
        engine.stages[next_s].execution_mode = "real"
        engine.stages[next_s].outputs_verified = True
        from paper_workflow.supervision.passport import PaperPassport
        passport = PaperPassport(engine.paper_dir)
        passport.record_checkpoint("select_topic", "approved", "test approval")

        # --- Record and sync ---
        sync = engine.record_and_sync()
        assert sync["passport_updated"]
        assert sync["stale_report"]["count"] == 0
        print(f"  [OK] Record and sync — passport_updated={sync['passport_updated']}")

        # --- Pipeline progression ---
        # After create_project completed, next should be search_literature
        next2 = engine.decide_next_stage()
        assert next2 == "target_journal", f"[FAIL] Expected target_journal, got {next2}"
        print(f"  [OK] Pipeline progression — after create_project → {next2}")

        # Complete search_literature and verify
        engine.run_stage("target_journal")
        target_verify = engine.verify_stage("target_journal")
        assert target_verify["all_passed"]
        assert engine.stages["target_journal"].status == StageStatus.COMPLETED
        next_lit = engine.decide_next_stage()
        assert next_lit == "literature_search", f"[FAIL] Expected literature_search, got {next_lit}"
        engine.run_stage("literature_search")
        lit_verify = engine.verify_stage("literature_search")
        assert not lit_verify["all_passed"]
        assert engine.stages["literature_search"].execution_mode == "pending_harness"
        engine.stages["literature_search"].status = StageStatus.COMPLETED
        engine.stages["literature_search"].completed_at = datetime.now().isoformat()
        engine.stages["literature_search"].execution_mode = "real"
        engine.stages["literature_search"].outputs_verified = True
        assert engine.stages["literature_search"].status == StageStatus.COMPLETED
        print(f"  [OK] search_literature completed")

        # Next should be research_plan (has 2 upstreams: create_project + search_literature)
        next3 = engine.decide_next_stage()
        assert next3 == "formulate_hypotheses", f"[FAIL] Expected formulate_hypotheses, got {next3}"
        print(f"  [OK] Upstream-aware progression — {next3}")

        # --- Blocked pipeline: complete some but not all upstreams ---
        # Reset: create_project done, others pending. search_literature NOT done yet, but
        # we need to check that research_plan won't proceed without search_literature.
        # Mark search_literature back to pending
        engine.stages["literature_search"].status = StageStatus.PENDING
        # Now research_plan has both upstreams but search_literature is pending.
        # But create_project is the only one with no upstreams, so decide_next
        # will return search_literature (which has upstream 'create_project' done).
        next4 = engine.decide_next_stage()
        assert next4 == "literature_search", f"[FAIL] Expected literature_search, got {next4}"
        print(f"  [OK] Blocked detection — returned {next4} (not research_plan)")

        # --- Unknown stage error ---
        bad_result = engine.run_stage("nonexistent_stage")
        assert not bad_result["success"]
        assert "Unknown" in bad_result["error"]
        print(f"  [OK] Unknown stage error — {bad_result['error']}")

        bad_verify = engine.verify_stage("nonexistent_stage")
        assert not bad_verify.get("passed", True)
        print(f"  [OK] Unknown stage verify error")

        # --- Diagnose failures ---
        diag = engine.diagnose_failures()
        assert diag["failed_stages"] >= 0
        assert "failures" in diag
        print(f"  [OK] Diagnosis — failures={diag['failed_stages']}")

        # --- Status summary ---
        summary = engine.get_status_summary()
        assert "test_paper" in summary
        assert "Phase 1" in summary
        assert "Phase 2" in summary
        assert "Phase 3" in summary
        assert "[OK]" in summary
        assert "[   ]" in summary
        print(f"  [OK] Status summary — {len(summary)} chars")

        # --- Human checkpoint stages ---
        human_stages = [sd.name for sd in engine.PIPELINE_STAGES if sd.human_checkpoint]
        assert "select_topic" in human_stages
        assert "internal_review" in human_stages
        assert "finalize" in human_stages
        print(f"  [OK] Human checkpoints — {human_stages}")

        # --- StageDefinition to_dict ---
        sd0 = engine.PIPELINE_STAGES[0]
        sdd = sd0.to_dict()
        assert sdd["name"] == sd0.name
        assert sdd["phase"] == sd0.phase
        print(f"  [OK] StageDefinition to_dict")

        # --- StageState to_dict ---
        ss = engine.stages["select_topic"]
        ssd = ss.to_dict()
        assert ssd["name"] == "select_topic"
        assert ssd["status"] == "completed"
        print(f"  [OK] StageState to_dict")

        # --- PipelineState enum values ---
        assert PipelineState.CLEAN.value == "clean"
        assert PipelineState.DRIFT_DETECTED.value == "drift_detected"
        assert PipelineState.BLOCKED.value == "blocked"
        print(f"  [OK] PipelineState enum values")

        # --- StageStatus enum values ---
        assert StageStatus.COMPLETED.value == "completed"
        assert StageStatus.PENDING.value == "pending"
        assert StageStatus.FAILED.value == "failed"
        print(f"  [OK] StageStatus enum values")

        # --- Max retries blocking ---
        # Complete all 18 stages
        for sd in engine.PIPELINE_STAGES:
            engine.stages[sd.name].status = StageStatus.COMPLETED
            if sd.human_checkpoint:
                passport.record_checkpoint(sd.name, "approved", "test approval")
        final_next = engine.decide_next_stage()
        assert final_next is None, f"[FAIL] All done should return None, got {final_next}"
        assert engine.pipeline_state == PipelineState.CLEAN
        print(f"  [OK] All complete — next_stage=None, pipeline={engine.pipeline_state.value}")

    print("  Suite 3: ALL PASSED\n")


# ============================================================================
# Suite 4: Integrity Gates
# ============================================================================

def test_integrity_gates():
    """Test Integrity Gates: 16 rules, edge cases, markdown report generation."""
    print("=" * 60)
    print("Test Suite 4: Integrity Gates")
    print("=" * 60)

    from paper_workflow.supervision.integrity import (
        IntegrityGateChecker, IntegrityReport, GateResult,
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        paper_dir = Path(tmpdir)
        checker = IntegrityGateChecker(paper_dir)

        # --- 16 gates defined ---
        assert len(checker.GATES) == 44, f"[FAIL] Expected 44 gates, got {len(checker.GATES)}"
        critical_count = sum(1 for g in checker.GATES.values() if g["severity"] == "critical")
        assert critical_count == 17
        print(f"  [OK] {len(checker.GATES)} gates defined ({critical_count} critical)")

        # --- Empty run ---
        report = checker.run_all_checks(active_categories=["format"])
        assert isinstance(report, IntegrityReport)
        assert not report.blocks_pipeline
        assert report.report_id.startswith("ir_")
        print(f"  [OK] Empty run — blocks_pipeline={report.blocks_pipeline}, id={report.report_id}")

        # --- Good manuscript sections ---
        good_sections = {
            "abstract": "This study investigates the role of cellular senescence in tissue aging. " * 10,
            "introduction": "Aging is a complex biological process characterized by progressive functional decline. "
                            "Recent studies have highlighted the importance of cellular senescence. "
                            "Spatial transcriptomics provides unprecedented resolution. " * 20,
            "methods": "We used a systematic pipeline for quality control, normalization, dimensionality reduction, "
                       "clustering with Leiden algorithm at resolution 0.6, and differential expression analysis. "
                       "All analyses were performed using Scanpy v1.9 and Python 3.10. " * 30,
            "results": "Our analysis revealed significant differences p=0.001 and β=0.5. "
                        "Figure 1 shows the spatial distribution of key markers. "
                        "The effect size was large (Cohen d=1.2). " * 40,
            "discussion": "Our findings demonstrate the utility of spatial transcriptomics. "
                          "Several limitations should be noted. "
                          "First, the sample size was limited. "
                          "Second, validation was performed on a single cohort. "
                          "Future studies should expand the sample size. "
                          "The data availability statement is provided below. "
                          "All code is available on GitHub under MIT license. " * 20,
        }
        report = checker.run_all_checks(manuscript_sections=good_sections)

        # Section length checks should pass
        for r in report.results:
            if r.rule == "section_length_minimum":
                assert r.passed, f"[FAIL] Section length should pass: {r.message}"
                print(f"  [OK] Section length — {r.message}")
            if r.rule == "no_bullets_in_prose":
                assert r.passed, f"[FAIL] No bullets should pass: {r.message}"
                print(f"  [OK] No bullets — {r.message}")
            if r.rule == "statistics_reported":
                assert r.passed, f"[FAIL] Statistics should pass: {r.message}"
                print(f"  [OK] Statistics — {r.message}")
            if r.rule == "data_availability_statement":
                assert r.passed, f"[FAIL] Data availability should pass: {r.message}"
                print(f"  [OK] Data availability — {r.message}")
            if r.rule == "code_availability_statement":
                assert r.passed, f"[FAIL] Code availability should pass: {r.message}"
                print(f"  [OK] Code availability — {r.message}")
            if r.rule == "no_local_paths":
                assert r.passed, f"[FAIL] No local paths should pass: {r.message}"
                print(f"  [OK] No local paths — {r.message}")

        # --- Bullet detection ---
        bullet_sections = {
            "introduction": "- First bullet point\n- Second bullet point\n\n" * 20,
        }
        bullet_report = checker.run_all_checks(manuscript_sections=bullet_sections)
        for r in bullet_report.results:
            if r.rule == "no_bullets_in_prose":
                assert not r.passed, "[FAIL] Should detect bullets"
                print(f"  [OK] Bullet detection — {r.message}")
                break

        # --- Local path detection ---
        path_sections = {
            "methods": "Load data from D:\\data\\file.h5ad and run C:\\scripts\\analysis.py. "
                        "Results are in /home/user/results/runs/output.h5ad. " * 5,
        }
        path_report = checker.run_all_checks(manuscript_sections=path_sections)
        for r in path_report.results:
            if r.rule == "no_local_paths":
                assert not r.passed, "[FAIL] Should detect local paths"
                assert len(r.details.get("violations", [])) > 0
                print(f"  [OK] Path detection — {r.message}")
                break

        # --- Results with citations (should fail) ---
        cite_results = {
            "results": "Our findings \\cite{smith2020} show that \\citep{jones2021} supports this. " * 20,
        }
        cite_report = checker.run_all_checks(manuscript_sections=cite_results)
        for r in cite_report.results:
            if r.rule == "results_no_citations":
                assert not r.passed, "[FAIL] Should detect citations in results"
                print(f"  [OK] Citation in results detection — {r.message}")
                break

        # --- BibTeX check ---
        bibtex_path = paper_dir / "test_library.bib"
        bibtex_path.write_text("""
@article{smith2020,
  author = {Smith, J.},
  title = {Test Article},
  journal = {Test Journal},
  year = {2020}
}
@article{jones2021,
  author = {Jones, K.},
  title = {Another Paper},
  journal = {Other Journal},
  year = {2021}
}
""", encoding="utf-8")
        bib_sections = {
            "introduction": "As shown previously \\cite{smith2020}, and also \\citet{jones2021}. " * 20,
            "methods": "Methods text. " * 50,
            "results": "Results text. " * 50,
            "discussion": "Discussion text. " * 30,
        }
        bib_report = checker.run_all_checks(
            manuscript_sections=bib_sections,
            bibtex_path=bibtex_path,
        )
        for r in bib_report.results:
            if r.rule == "bibtex_citation_existence":
                assert r.passed, f"[FAIL] BibTeX check should pass: {r.message}"
                print(f"  [OK] BibTeX citation check — {r.message}")
                break

        # BibTeX with missing citation
        missing_bib_sections = {
            "introduction": "This is cited \\cite{smith2020} and \\cite{missing_ref2025}. " * 20,
            "methods": "Methods. " * 50,
            "results": "Results. " * 50,
            "discussion": "Discussion. " * 30,
        }
        missing_bib_report = checker.run_all_checks(
            manuscript_sections=missing_bib_sections,
            bibtex_path=bibtex_path,
        )
        for r in missing_bib_report.results:
            if r.rule == "bibtex_citation_existence":
                assert not r.passed, "[FAIL] Should detect missing BibTeX keys"
                assert len(r.details.get("missing_keys", [])) == 1
                print(f"  [OK] Missing BibTeX detection — {r.message}")
                break

        # --- Statistics missing test ---
        no_stats_sections = {
            "results": "We observed changes. The differences were notable. Several trends emerged. " * 50,
        }
        no_stats_report = checker.run_all_checks(manuscript_sections=no_stats_sections)
        for r in no_stats_report.results:
            if r.rule == "statistics_reported":
                assert not r.passed, "[FAIL] Should flag missing statistics"
                print(f"  [OK] Missing statistics detection — {r.message}")
                break

        # --- Figure count check ---
        figure_plan_large = {"figures": ["fig1", "fig2", "fig3", "fig4", "fig5", "fig6", "fig7", "fig8", "fig9"]}
        journal = {"figure_limit": 6}
        fig_report = checker.run_all_checks(figure_plan=figure_plan_large, journal_target=journal)
        for r in fig_report.results:
            if r.rule == "figure_count_requirements":
                assert not r.passed, "[FAIL] Should flag excessive figures"
                print(f"  [OK] Figure count check — {r.message}")
                break

        # OK figure count
        figure_plan_ok = {"figures": ["fig1", "fig2", "fig3", "fig4"]}
        fig_report2 = checker.run_all_checks(figure_plan=figure_plan_ok, journal_target=journal)
        for r in fig_report2.results:
            if r.rule == "figure_count_requirements":
                assert r.passed
                print(f"  [OK] Figure count check (ok) — {r.message}")
                break

        # --- Short section check ---
        short_sections = {
            "methods": "Too short.",
        }
        short_report = checker.run_all_checks(manuscript_sections=short_sections)
        for r in short_report.results:
            if r.rule == "section_length_minimum" and r.details.get("section") == "methods":
                assert not r.passed, f"[FAIL] Should fail on too-short methods: {r.message}"
                print(f"  [OK] Short section detection — {r.message}")
                break

        # --- Markdown report (passing) ---
        md = checker.generate_markdown_report(report)
        assert "Integrity Gate Report" in md
        assert "Summary" in md
        assert "Detailed Results" in md
        print(f"  [OK] Markdown report (passing) — {len(md)} chars")

        # --- Markdown report (with failures) ---
        fail_report = checker.run_all_checks(manuscript_sections=bullet_sections)
        md_fail = checker.generate_markdown_report(fail_report)
        assert "[FAIL]" in md_fail
        print(f"  [OK] Markdown report (with failures) — contains [FAIL] markers")

        # --- IntegrityReport properties ---
        r = IntegrityReport(paper_id="test")
        assert r.blocks_pipeline is False
        assert r.has_critical_failures is False
        r.critical_failures = 1
        assert r.blocks_pipeline is True
        assert r.has_critical_failures is True
        print(f"  [OK] IntegrityReport properties — blocks_pipeline={r.blocks_pipeline}")

        # --- IntegrityReport to_dict ---
        rd = report.to_dict()
        assert "report_id" in rd
        assert "passed" in rd
        assert "results" in rd
        print(f"  [OK] IntegrityReport to_dict")

        # --- GateResult dataclass ---
        gr = GateResult(rule="test_rule", severity="critical", passed=True, message="OK")
        assert gr.rule == "test_rule"
        assert gr.severity == "critical"
        assert gr.checked_at is not None
        print(f"  [OK] GateResult dataclass")

        # --- Empty bibtex file (missing) test ---
        nonexistent_bib = paper_dir / "nonexistent.bib"
        bib_check = checker.run_all_checks(
            manuscript_sections={"introduction": "\\cite{test} text " * 20},
            bibtex_path=nonexistent_bib,
        )
        for r in bib_check.results:
            if r.rule == "bibtex_citation_existence":
                assert not r.passed, "[FAIL] Missing bibtex file should fail"
                print(f"  [OK] Missing BibTeX file detection — {r.message}")
                break

    print("  Suite 4: ALL PASSED\n")


# ============================================================================
# Suite 5: Full Integration
# ============================================================================

def test_full_integration():
    """Test Full Integration: PaperWorkflow create → initialize → run → diagnose → save state."""
    print("=" * 60)
    print("Test Suite 5: Full Integration")
    print("=" * 60)

    from paper_workflow.workflow import PaperWorkflow, WorkflowState, create_and_run_paper
    from paper_workflow.engine.loop_engine import StageStatus, PipelineState

    with tempfile.TemporaryDirectory() as tmpdir:
        root = _make_project_root(tmpdir)

        # --- Create PaperWorkflow ---
        wf = PaperWorkflow(project_root=root)
        assert wf.project_root == root
        assert wf.paper_id is None
        assert wf.state.paper_id == "uninitialized"
        print(f"  [OK] PaperWorkflow created — root={root.name}")

        # --- Initialize ---
        state = wf.initialize(
            idea="Spatial transcriptomics reveals aging mechanisms in kidney",
            field="spatial transcriptomics, aging, kidney",
            journal="Genome Biology",
            timeline_weeks=4,
        )
        assert wf.paper_id is not None
        assert "strat-" in wf.paper_id
        assert state.pipeline_state == "ready"
        assert state.strategy is not None
        assert state.strategy.topic is not None
        assert state.strategy.journal_target is not None
        assert state.strategy.journal_target.name == "Genome Biology"
        print(f"  [OK] Initialize — paper_id={wf.paper_id}, pipeline={state.pipeline_state}")

        # --- Verify passport exists ---
        passport_path = wf.engine.paper_dir / "project_passport.yaml"
        assert passport_path.exists(), "[FAIL] Passport should exist"
        print(f"  [OK] Passport file exists — {passport_path.name}")

        # --- Verify select_topic completed ---
        assert wf.engine.stages["select_topic"].status == StageStatus.COMPLETED
        print(f"  [OK] select_topic already completed after initialize")

        # --- Run next stages ---
        # Run without stop_at_checkpoint to get past human checkpoints
        wf.run(max_stages=4, stop_at_checkpoint=False)
        print(f"  [OK] Pipeline run (max_stages=4) — completed={wf.state.stages_completed}, "
              f"failed={wf.state.stages_failed}")

        # --- Verify Phase 1 progresses to journal profile, then stops for literature harness input ---
        assert wf.state.stages_completed == 1
        assert wf.state.stages_failed >= 1
        assert wf.engine.stages["target_journal"].status == StageStatus.COMPLETED
        assert wf.engine.stages["literature_search"].execution_mode == "pending_harness"
        print(f"  [OK] Truth layer stopped for literature harness input: failed={wf.state.stages_failed}")

        # --- Diagnose ---
        diag = wf.diagnose_failures()
        assert "engine_diagnosis" in diag
        assert "integrity_report" in diag
        assert "integrity_passed" in diag
        assert "total_errors" in diag
        print(f"  [OK] Diagnose — integrity_passed={diag['integrity_passed']}, "
              f"errors={diag['total_errors']}")

        # --- Get summary ---
        summary = wf.get_summary()
        assert wf.paper_id in summary
        assert "Artifacts" in summary or "artifacts" in summary.lower()
        print(f"  [OK] Get summary — {len(summary)} chars")

        # --- Save state ---
        state_path = wf.save_state()
        assert state_path.exists()
        assert state_path.suffix == ".json"
        # Verify state file content
        state_data = json.loads(state_path.read_text(encoding="utf-8"))
        assert state_data["paper_id"] == wf.paper_id
        assert "started_at" in state_data
        assert "stages_completed" in state_data
        print(f"  [OK] Save state — {state_path.name}")
        print(f"  [OK] State file valid JSON — paper_id={state_data['paper_id']}")

        # --- Lazy property initialization ---
        wf2 = PaperWorkflow(project_root=root)
        # strategy_manager does not need paper_id
        sm = wf2.strategy_manager  # triggers lazy init
        assert sm is not None
        print(f"  [OK] Lazy property: strategy_manager accessible without paper_id")
        # engine/passport/integrity require paper_id — initialize first
        wf2.initialize(idea="Lazy init test", field="testing")
        eng = wf2.engine  # triggers lazy init (forces rebuild after initialize)
        assert eng is not None
        pp = wf2.passport  # triggers lazy init
        assert pp is not None
        ig = wf2.integrity  # triggers lazy init
        assert ig is not None
        print(f"  [OK] Lazy property initialization — all properties accessible after initialize")

        # --- create_and_run_paper convenience function ---
        wf3 = create_and_run_paper(
            idea="Comparative analysis of disease states",
            field="bioinformatics, comparative",
            journal="Bioinformatics",
            project_root=root,
        )
        assert wf3.state.pipeline_state == "ready"
        assert wf3.state.strategy is not None
        assert wf3.state.strategy.journal_target.name == "Bioinformatics"
        print(f"  [OK] create_and_run_paper — paper_id={wf3.paper_id}, state={wf3.state.pipeline_state}")

        # --- create_and_run_paper with auto_run ---
        wf4 = create_and_run_paper(
            idea="Auto-run test paper",
            field="genomics",
            journal="Nature Genetics",
            project_root=root,
            auto_run=True,
            max_stages=2,
        )
        assert wf4.state.stages_failed >= 1
        assert wf4.state.pipeline_state == "blocked"
        print(f"  [OK] create_and_run_paper (auto_run) — completed={wf4.state.stages_completed}")

        # --- WorkflowState dataclass ---
        ws = WorkflowState(paper_id="test_paper")
        assert ws.paper_id == "test_paper"
        assert ws.started_at is not None
        assert ws.completed_at is None
        assert ws.stages_completed == 0
        assert ws.errors == []
        print(f"  [OK] WorkflowState dataclass")

        # --- Manual stage failure tracking ---
        wf5 = PaperWorkflow(project_root=root)
        wf5.initialize(idea="Failure test", field="testing", journal="Bioinformatics")
        # Simulate a stage failure
        wf5.state.errors.append({"stage": "run_analysis", "error": "Simulated failure",
                                  "timestamp": datetime.now().isoformat()})
        wf5.state.stages_failed += 1
        assert len(wf5.state.errors) == 1
        assert wf5.state.stages_failed == 1
        print(f"  [OK] Error tracking — errors={len(wf5.state.errors)}, "
              f"failed_stages={wf5.state.stages_failed}")

        # --- Pipeline save with no stages completed yet ---
        state_path2 = wf5.save_state()
        sd2 = json.loads(state_path2.read_text(encoding="utf-8"))
        assert sd2["stages_completed"] == 0
        assert sd2["stages_failed"] == 1
        print(f"  [OK] Save state (with failures) — completed={sd2['stages_completed']}, "
              f"failed={sd2['stages_failed']}")

    print("  Suite 5: ALL PASSED\n")


# ============================================================================
# Runner
# ============================================================================

def run_all():
    """Run all test suites. Returns True if all pass, False otherwise."""
    print()
    print("=" * 70)
    print("  Research Paper Workflow Framework — Comprehensive Integration Tests")
    print("=" * 70)
    print(f"  Timestamp: {datetime.now().isoformat()}")
    print(f"  Python: {sys.version}")
    print("=" * 70)
    print()

    tests = [
        ("Strategy Layer", test_strategy_layer),
        ("Passport System", test_passport_system),
        ("Loop Engine", test_loop_engine),
        ("Integrity Gates", test_integrity_gates),
        ("Full Integration", test_full_integration),
    ]

    passed = 0
    failed = 0

    for name, test_func in tests:
        try:
            test_func()
            passed += 1
        except AssertionError as e:
            print(f"\n  [FAIL] {name}: ASSERTION ERROR — {e}")
            import traceback
            traceback.print_exc()
            failed += 1
        except ImportError as e:
            print(f"\n  [FAIL] {name}: IMPORT ERROR — {e}")
            import traceback
            traceback.print_exc()
            failed += 1
        except Exception as e:
            print(f"\n  [FAIL] {name}: UNEXPECTED ERROR — {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            failed += 1

    print()
    print("=" * 70)
    print(f"  RESULTS: {passed} passed, {failed} failed, {len(tests)} total")
    if failed == 0:
        print("  ALL TESTS PASSED")
    else:
        print(f"  {failed} suite(s) FAILED")
    print("=" * 70)

    return failed == 0


if __name__ == "__main__":
    success = run_all()
    sys.exit(0 if success else 1)
