"""CI cases that must fail closed instead of producing a fake pass."""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path
from typing import Any

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from paper_workflow.outputs.result_run_manager import ResultRunManager  # noqa: E402
from paper_workflow.target_task.schema import validate_target_task  # noqa: E402


def run_cases() -> dict[str, Any]:
    cases: list[dict[str, Any]] = []
    with tempfile.TemporaryDirectory() as tmp:
        paper = Path(tmp) / "papers" / "failure_case"
        paper.mkdir(parents=True)
        (paper / "project_passport.yaml").write_text("paper_id: failure_case\npipeline_state: test\n", encoding="utf-8")
        manager = ResultRunManager(paper)
        manager.create_run("failure_case_20260709_v1")
        run_dir = manager.run_path("failure_case_20260709_v1")
        (run_dir / "figure_source_map.yaml").write_text(
            "schema_version: test\nfigures:\n- figure_id: f1\n  path: figures/f.png\n  source_data: tables/t.csv\n  script: test.py\n  method: visual smoke\n  statistical_unit: cell\n",
            encoding="utf-8",
        )
        (run_dir / "table_source_map.yaml").write_text(
            "schema_version: test\ntables:\n- table_id: t1\n  path: tables/t.csv\n  source_inputs: data.csv\n  method: table smoke\n  statistical_unit: cell\n",
            encoding="utf-8",
        )
        evaluation = manager.evaluate_run("failure_case_20260709_v1", write_report=True).to_dict()
        cases.append({
            "case": "missing_claim_boundary_source_maps",
            "expected_not_pass": True,
            "observed_status": evaluation["status"],
            "passed": evaluation["status"] != "pass",
        })

    invalid_target = {
        "schema_version": "target_task.v1",
        "target_id": "bad_20260709_v1",
        "title": "missing boundary",
        "mode": "execution_mode",
        "evidence_grade": "workflow_test",
        "data": {"dataset_id": "x", "modality": "single_cell", "format": "10x", "input_path": "data/raw/x", "role": "test"},
        "environment": {"required_envs": ["r_seurat_v5"]},
        "analysis_goal": {"forbidden_claims": ["disease mechanism", "clinical biomarker", "treatment response", "causal immune state"]},
        "workflow": {"steps": ["source_map_validation"]},
        "quality_gates": {"fail_closed": True, "require_session_info": True, "require_source_maps": True, "require_claim_boundary": True, "require_no_personal_paths": True},
        "outputs": {"required_tables": []},
    }
    schema = validate_target_task(invalid_target)
    cases.append({
        "case": "target_task_missing_claim_boundary",
        "expected_not_valid": True,
        "observed_valid": schema["valid"],
        "issues": schema["issues"],
        "passed": not schema["valid"],
    })
    return {
        "schema_version": "supervision_failure_cases.v1",
        "status": "pass" if all(case["passed"] for case in cases) else "fail",
        "cases": cases,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    result = run_cases()
    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(f"Supervision failure cases: {result['status']}")
        print(yaml.safe_dump(result, allow_unicode=True, sort_keys=False))
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
