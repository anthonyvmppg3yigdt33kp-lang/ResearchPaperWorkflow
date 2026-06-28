"""
Paper Workflow CLI — Command-line interface for the research paper workflow system.

Full pipeline control plus a model-facing AI harness for Claude/Codex.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from paper_workflow.ai_harness import AIWorkflowHarness
from paper_workflow.api import WorkflowAPI
from paper_workflow.strategy.research_strategy import ResearchStrategyManager
from paper_workflow.utils.skill_installer import (
    ensure_skills_available,
    format_skill_report,
    install_missing_skills,
)


def get_root() -> Path:
    current = Path.cwd()
    for _ in range(10):
        if (current / "AGENTS.md").exists() or (current / "CLAUDE.md").exists():
            return current
        current = current.parent
    return Path.cwd()


def get_papers_dir(root: Path) -> Path:
    d = root / "papers"
    d.mkdir(parents=True, exist_ok=True)
    return d


def get_api() -> WorkflowAPI:
    return WorkflowAPI(get_root())


def cmd_create(args):
    result = get_api().create_project(
        idea=args.idea,
        field=args.field,
        journal=args.journal or "",
        timeline_weeks=args.timeline or 8,
    )
    print(f"[OK] Paper created: {result['paper_id']}")
    print(f"     Directory: {result['paper_dir']}")
    print(f"     Journal: {result['journal']}")


def cmd_status(args):
    root = get_root()
    papers_dir = get_papers_dir(root)
    paper_dir = papers_dir / args.paper
    if not paper_dir.exists():
        print(f"[ERROR] Paper not found: {args.paper}"); sys.exit(1)
    result = WorkflowAPI(root).status(args.paper)
    print(result["summary"])
    drifted = result["drifted_artifacts"]
    if drifted:
        print(f"\n[WARNING] {len(drifted)} artifact(s) drifted. Run 'sync-artifact-stale'.")


def cmd_run(args):
    result = get_api().run_pipeline(
        args.paper,
        stop_on_failure=args.stop_on_failure,
        auto_approve_checkpoints=args.auto_approve_checkpoints,
        max_stages=args.max_stages,
    )
    if not result["events"]:
        blockers = result.get("checkpoint_blockers", [])
        if blockers:
            _print_checkpoint_blockers(blockers)
            return
        print("[OK] Pipeline complete or blocked. Run 'status' or 'diagnose-gate-failures'.")
        return
    for event in result["events"]:
        if event["event"] == "stage":
            print(f"  -> Running: {event['stage']}")
            if event.get("stopped_on_failure"):
                print(f"  [FAIL] {event['stage']}")
        elif event["event"] == "checkpoint_auto_approved":
            print(f"  [CHECKPOINT] auto-approved: {event['stage']}")
        elif event["event"] == "checkpoint_required":
            print(f"  [CHECKPOINT] Approval required before continuing: {event['stage']}")
            print(f"               Run: paper-workflow checkpoint --paper {args.paper} --stage {event['stage']} --decision approved")
        elif event["event"] == "checkpoint_blockers":
            _print_checkpoint_blockers(event["blockers"])
        elif event["event"] == "max_stages_reached":
            print(f"  [STOP] max stages reached: {event['max_stages']}")
    print(f"\n[OK] State: {result['pipeline_state']}")


def _print_checkpoint_blockers(blockers: list[dict]) -> None:
    print("[CHECKPOINT] Human approval required before pipeline can continue:")
    for blocker in blockers:
        artifacts = ", ".join(blocker.get("artifacts", []) or [])
        print(f"  - {blocker['stage']} | status={blocker['status']} | artifacts={artifacts or 'none'}")


def cmd_checkpoint(args):
    entry = get_api().record_checkpoint(
        args.paper,
        stage=args.stage,
        decision=args.decision,
        notes=args.notes or "",
    )
    print(f"[OK] Checkpoint: {entry['checkpoint_id']} | {args.stage} | {args.decision}")


def cmd_integrity(args):
    result = get_api().run_integrity_gate(args.paper)
    print(result["markdown"])
    if result["blocks_pipeline"]:
        print("\n[BLOCKED] Critical failures. Run 'diagnose-gate-failures'.")
        sys.exit(1)


def cmd_diagnose(args):
    diag = get_api().diagnose_gate_failures(args.paper)
    print(f"Failed stages: {diag['failed_stages']}")
    for f in diag["failures"]:
        print(f"  Stage: {f['stage']} | Errors: {f['errors']} | Gate fails: {f['gate_failures']}")


def cmd_drift(args):
    drifted = get_api().detect_artifact_drift(args.paper)
    if drifted:
        print(f"[DRIFT] {len(drifted)} artifact(s):")
        for d in drifted:
            print(f"  - {d['path']}: {d['status']}")
    else:
        print("[OK] No artifact drift.")


def cmd_sync(args):
    result = get_api().sync_artifact_stale(args.paper)
    print(f"[OK] {result['stale_count']} stage(s) marked stale")
    for s in result["stale_stages"]:
        print(f"  - {s}")


def cmd_validate_workflow(args):
    result = get_api().validate_workflow(args.paper)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    if args.strict and not result["valid"]:
        sys.exit(1)


def cmd_validate_contract(args):
    result = get_api().validate_contract()
    print(json.dumps(result, indent=2, ensure_ascii=False))
    if args.strict and not result["valid"]:
        sys.exit(1)


def cmd_list_harness_invocations(args):
    records = get_api().list_harness_invocations(args.paper, status=args.status)
    if args.json:
        print(json.dumps(records, indent=2, ensure_ascii=False))
        return
    if not records:
        print("[OK] No harness invocations found.")
        return
    print(f"Harness invocations ({len(records)}):")
    for record in records:
        print(
            f"  - {record.get('name')} | stage={record.get('stage_id', '')} "
            f"| skill={record.get('skill_name', '')} | status={record.get('status', '')}"
        )


def cmd_complete_harness_invocation(args):
    try:
        result = get_api().complete_harness_invocation(
            args.paper,
            invocation=args.invocation,
            notes=args.notes or "",
        )
    except FileNotFoundError as exc:
        print(f"[ERROR] {exc}")
        sys.exit(1)
    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(
            f"[{result['status'].upper()}] {result['stage_id']} | "
            f"outputs_verified={result['outputs_verified']}"
        )
        if result["missing_outputs"]:
            print(f"  missing: {', '.join(result['missing_outputs'])}")
        if result["empty_outputs"]:
            print(f"  empty: {', '.join(result['empty_outputs'])}")
        if result["placeholder_outputs"]:
            print(f"  placeholder: {', '.join(result['placeholder_outputs'])}")
        print(f"  result: {result['result_path']}")
    if args.strict and result["status"] != "completed":
        sys.exit(1)


def cmd_list(args):
    root = get_root()
    papers_dir = get_papers_dir(root)
    papers = list(papers_dir.iterdir())
    if not papers:
        print("No paper projects found."); return
    print(f"Papers ({len(papers)}):")
    for pd in sorted(papers):
        if not pd.is_dir(): continue
        pp = pd / "project_passport.yaml"
        if pp.exists():
            import yaml
            with open(pp, "r", encoding="utf-8") as f:
                d = yaml.safe_load(f)
            print(f"  {pd.name} | {d.get('pipeline_state', '?')} | {d.get('idea', '')[:50]}")


def cmd_strategy(args):
    root = get_root()
    manager = ResearchStrategyManager(root)
    strategy = manager.create_strategy(idea=args.idea, field=args.field,
                                       target_journal=args.journal, timeline_weeks=args.timeline or 8)
    manager.save_strategy(strategy)
    print(manager.print_summary(strategy))


def cmd_install_skills(args):
    root = get_root()
    target = Path(args.target_root).expanduser() if args.target_root else None
    report = install_missing_skills(
        project_root=root,
        target_root=target,
        check_only=args.check_only,
        force=args.force,
    )
    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print(format_skill_report(report))
    if args.strict and (report.get("missing_bundled") or report.get("missing_external")):
        sys.exit(1)


def cmd_aigc_humanizer(args):
    stage = "aigc_humanizer_review"
    result = get_api().run_aigc_humanizer(args.paper)
    if not result.get("success") and "verify" not in result:
        print(f"[ERROR] {stage} failed: {result.get('error', '')}")
        sys.exit(1)
    print(f"     Artifacts: {', '.join(result.get('artifacts', [])) or 'none'}")
    verify = result.get("verify", {})
    if not verify.get("all_passed", False):
        print(f"[FAIL] {stage} did not pass workflow gates")
        print(f"       Details: {verify.get('error') or verify.get('results')}")
        sys.exit(1)
    print(f"[OK] {stage} complete")


def cmd_ai_harness(args):
    harness = AIWorkflowHarness(get_root())
    result = harness.handle_request(
        args.request,
        paper_id=args.paper,
        field=args.field,
        journal=args.journal,
        timeline_weeks=args.timeline,
        max_stages=args.max_stages,
        stop_on_failure=args.stop_on_failure,
        auto_approve_checkpoints=args.auto_approve_checkpoints,
        dry_run=args.dry_run,
        invocation=args.invocation,
        stage=args.stage,
        decision=args.decision,
        notes=args.notes or "",
    )
    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(f"[AI-HARNESS] intent={result['intent']} status={result['status']}")
        print(f"  request: {result['request']}")
        print(f"  command: {result['plan']['equivalent_cli_command']}")
        print(f"  reply: {result['user_facing_reply']}")
        actions = result.get("next_model_actions") or []
        if actions:
            print("  next:")
            for action in actions:
                print(f"    - {action}")
    if args.strict and result["status"] in {"error", "failed", "blocked", "gate_failure", "needs_input"}:
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Paper Workflow CLI")
    sub = parser.add_subparsers(dest="command")

    p = sub.add_parser("create-project"); p.add_argument("--idea", required=True); p.add_argument("--field", required=True)
    p.add_argument("--journal"); p.add_argument("--timeline", type=int)

    p = sub.add_parser("status"); p.add_argument("--paper", required=True)

    p = sub.add_parser("run-pipeline"); p.add_argument("--paper", required=True)
    p.add_argument("--stop-on-failure", action="store_true")
    p.add_argument("--auto-approve-checkpoints", action="store_true")
    p.add_argument("--max-stages", type=int)

    p = sub.add_parser("checkpoint"); p.add_argument("--paper", required=True); p.add_argument("--stage", required=True)
    p.add_argument("--decision", required=True, choices=["approved", "rejected", "revision_needed"]); p.add_argument("--notes")

    p = sub.add_parser("run-integrity-gate"); p.add_argument("--paper", required=True)
    p = sub.add_parser("diagnose-gate-failures"); p.add_argument("--paper", required=True)
    p = sub.add_parser("detect-artifact-drift"); p.add_argument("--paper", required=True)
    p = sub.add_parser("sync-artifact-stale"); p.add_argument("--paper", required=True)
    p = sub.add_parser("validate-workflow"); p.add_argument("--paper", required=True)
    p.add_argument("--strict", action="store_true")

    p = sub.add_parser("validate-contract")
    p.add_argument("--strict", action="store_true")

    p = sub.add_parser("list-harness-invocations")
    p.add_argument("--paper", required=True)
    p.add_argument("--status")
    p.add_argument("--json", action="store_true")

    p = sub.add_parser("complete-harness-invocation")
    p.add_argument("--paper", required=True)
    p.add_argument("--invocation", required=True)
    p.add_argument("--notes")
    p.add_argument("--json", action="store_true")
    p.add_argument("--strict", action="store_true")

    sub.add_parser("list-papers")

    p = sub.add_parser("strategy"); p.add_argument("--idea", required=True); p.add_argument("--field", required=True)
    p.add_argument("--journal"); p.add_argument("--timeline", type=int)

    p = sub.add_parser("install-skills")
    p.add_argument("--target-root")
    p.add_argument("--check-only", action="store_true")
    p.add_argument("--json", action="store_true")
    p.add_argument("--strict", action="store_true")
    p.add_argument("--force", action="store_true")

    p = sub.add_parser("run-aigc-humanizer")
    p.add_argument("--paper", required=True)

    p = sub.add_parser(
        "ai",
        aliases=["ai-harness"],
        help="Model-facing natural-language harness for Claude/Codex.",
    )
    p.add_argument("--request", required=True, help="Natural-language user request.")
    p.add_argument("--paper", help="Optional paper_id; if omitted, one existing project can be resolved.")
    p.add_argument("--field", help="Optional field override for project creation.")
    p.add_argument("--journal", help="Optional target journal override.")
    p.add_argument("--timeline", type=int, help="Timeline in weeks for project creation.")
    p.add_argument("--max-stages", type=int, help="Maximum stages to run in this model turn.")
    p.add_argument("--stop-on-failure", action="store_true", default=True)
    p.add_argument("--auto-approve-checkpoints", action="store_true")
    p.add_argument("--dry-run", action="store_true", help="Plan only; do not execute workflow state changes.")
    p.add_argument("--invocation", help="Harness invocation filename, stem, or stage id.")
    p.add_argument("--stage", help="Stage id for checkpoint or harness completion.")
    p.add_argument("--decision", default="approved", choices=["approved", "rejected", "revision_needed"])
    p.add_argument("--notes")
    p.add_argument("--json", action="store_true")
    p.add_argument("--strict", action="store_true")

    args = parser.parse_args()
    if args.command is None:
        parser.print_help(); return

    if args.command != "install-skills":
        try:
            ensure_skills_available(get_root(), auto_install=True, quiet=True)
        except Exception as exc:
            print(f"[WARNING] Skill auto-check skipped: {exc}")

    {"create-project": cmd_create, "status": cmd_status, "run-pipeline": cmd_run,
     "checkpoint": cmd_checkpoint, "run-integrity-gate": cmd_integrity,
     "diagnose-gate-failures": cmd_diagnose, "detect-artifact-drift": cmd_drift,
     "sync-artifact-stale": cmd_sync, "validate-workflow": cmd_validate_workflow,
     "validate-contract": cmd_validate_contract,
     "list-harness-invocations": cmd_list_harness_invocations,
     "complete-harness-invocation": cmd_complete_harness_invocation,
     "list-papers": cmd_list, "strategy": cmd_strategy,
     "install-skills": cmd_install_skills, "run-aigc-humanizer": cmd_aigc_humanizer,
     "ai": cmd_ai_harness, "ai-harness": cmd_ai_harness}[args.command](args)


if __name__ == "__main__":
    main()
