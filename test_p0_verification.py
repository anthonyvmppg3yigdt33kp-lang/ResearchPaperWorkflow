"""P0 Config-Code Sync verification script."""
import sys
from pathlib import Path

# Ensure the package root is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from paper_workflow.utils.config_loader import ConfigLoader
from paper_workflow.engine.loop_engine import PaperLoopEngine


def test_config_loader():
    """Test ConfigLoader standalone."""
    cl = ConfigLoader()
    assert cl.is_loaded, "Config should be loaded"

    stages = cl.get_pipeline_stages()
    assert len(stages) == 18, f"Expected 18 stages, got {len(stages)}"
    print(f"Config loaded: {len(stages)} pipeline stages from config")

    ws = cl.get_writing_standards()
    structure = ws.get("structure", "N/A")
    assert structure == "IMRAD", f"Expected IMRAD, got {structure}"
    print(f"Writing standards: {structure}")

    gates = cl.get_quality_gates()
    n_crit = len(gates.get("critical", []))
    n_high = len(gates.get("high", []))
    n_med = len(gates.get("medium", []))
    total = n_crit + n_high + n_med
    assert total == 16, f"Expected 16 total gates, got {total}"
    print(f"Quality gates: {n_crit} critical + {n_high} high + {n_med} medium = {total} total")

    # Additional accessors
    pt = cl.get_paper_type("original_research")
    assert pt["name"] == "Original Research Article"
    print(f"Paper type 'original_research' loaded OK")

    rd = cl.get_research_domain("bioinformatics")
    assert rd["name"].startswith("Bioinformatics")
    print(f"Research domain 'bioinformatics' loaded OK")

    sd = cl.get_skills_dispatcher_rules()
    skills = sd.get("skills", {})
    assert len(skills) >= 10, f"Expected >=10 skills, got {len(skills)}"
    print(f"Skills dispatcher: {len(skills)} skills")

    ar = cl.get_agent_routing()
    agents = ar.get("agents", {})
    assert len(agents) == 11, f"Expected 11 agents, got {len(agents)}"
    print(f"Agent routing: {len(agents)} agents")

    sup = cl.get_supervision()
    assert "timeout" in sup
    print("Supervision config loaded OK")

    return True


def test_engine_with_config():
    """Test PaperLoopEngine initialised with config_path."""
    project_root = Path(__file__).resolve().parent
    config_path = project_root / "config" / "default_config.yaml"
    assert config_path.exists(), f"Config not found at {config_path}"

    engine = PaperLoopEngine(
        project_root=project_root,
        paper_id="test_p0",
        config_path=config_path,
    )
    assert len(engine.stages) == 18, f"Expected 18 stages from config, got {len(engine.stages)}"

    # Verify stage IDs match config IDs
    expected_ids = [
        "select_topic", "target_journal", "literature_search", "formulate_hypotheses",
        "data_audit", "figure_planning", "run_analysis", "verify_methods",
        "write_methods", "write_results", "write_introduction", "write_discussion",
        "assemble_manuscript", "integrity_check", "internal_review",
        "apply_revision", "re_review", "finalize",
    ]
    actual_ids = list(engine.stages.keys())
    assert actual_ids == expected_ids, f"Stage ID mismatch: {actual_ids} != {expected_ids}"

    print(f"Engine loaded {len(engine.stages)} stages from config — IDs match config YAML")
    return True


def test_engine_backward_compat():
    """Test PaperLoopEngine WITHOUT config_path (backward compatible)."""
    project_root = Path(__file__).resolve().parent

    engine = PaperLoopEngine(
        project_root=project_root,
        paper_id="test_backcompat",
        # No config_path — should use hardcoded PIPELINE_STAGES
    )
    expected_hardcoded = [
        "create_project", "search_literature", "research_plan",
        "data_audit", "figure_planning", "run_analysis", "verify_methods",
        "write_methods", "write_results", "write_introduction", "write_discussion",
        "assemble_manuscript", "integrity_check", "internal_review",
        "apply_revision", "re_review", "quality_check", "finalize",
    ]
    actual_ids = list(engine.stages.keys())
    assert actual_ids == expected_hardcoded, (
        f"Backward compat ID mismatch: {actual_ids} != {expected_hardcoded}"
    )
    print(f"Backward compatible: engine uses hardcoded PIPELINE_STAGES ({len(engine.stages)} stages)")
    return True


def test_config_loader_missing_file():
    """Test ConfigLoader with missing config file returns defaults."""
    cl = ConfigLoader(config_path=Path("/nonexistent/config.yaml"))
    assert not cl.is_loaded

    stages = cl.get_pipeline_stages()
    assert len(stages) == 1
    assert stages[0]["id"] == "create_project"
    print("Missing config fallback: stages default OK")

    gates = cl.get_quality_gates()
    assert gates["critical"] == []
    print("Missing config fallback: gates default OK")

    ws = cl.get_writing_standards()
    assert ws["structure"] == "IMRAD"
    print("Missing config fallback: writing standards default OK")

    pt = cl.get_paper_type("nonexistent")
    assert pt["name"] == "Original Research Article"
    print("Missing config fallback: paper type default OK")

    return True


def main():
    tests = [
        ("ConfigLoader standalone", test_config_loader),
        ("Engine with config_path", test_engine_with_config),
        ("Engine backward compat", test_engine_backward_compat),
        ("ConfigLoader missing file", test_config_loader_missing_file),
    ]
    passed = 0
    failed = 0
    for name, test_fn in tests:
        try:
            test_fn()
            passed += 1
            print(f"  [PASS] {name}")
        except Exception as exc:
            failed += 1
            print(f"  [FAIL] {name}: {exc}")

    print()
    if failed == 0:
        print("P0 COMPLETE — all tests passed")
    else:
        print(f"P0 PARTIAL — {failed}/{len(tests)} tests FAILED")
        sys.exit(1)


if __name__ == "__main__":
    main()
