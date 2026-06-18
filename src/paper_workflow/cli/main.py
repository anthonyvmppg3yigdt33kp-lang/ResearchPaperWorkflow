"""
Paper Workflow CLI — Command-line interface for the research paper workflow system.

12 commands for full pipeline control.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from paper_workflow.engine.loop_engine import PaperLoopEngine
from paper_workflow.supervision.passport import PaperPassport
from paper_workflow.supervision.integrity import IntegrityGateChecker
from paper_workflow.strategy.research_strategy import ResearchStrategyManager


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


def cmd_create(args):
    root = get_root()
    papers_dir = get_papers_dir(root)
    manager = ResearchStrategyManager(root)
    strategy = manager.create_strategy(idea=args.idea, field=args.field,
                                       target_journal=args.journal, timeline_weeks=args.timeline or 8)
    paper_id = strategy.strategy_id
    engine = PaperLoopEngine(root, paper_id, papers_dir)
    passport = PaperPassport(engine.paper_dir)
    passport.initialize(idea=args.idea, field=args.field, target_journal=args.journal or "")
    manager.save_strategy(strategy)
    print(f"[OK] Paper created: {paper_id}")
    print(f"     Directory: {engine.paper_dir}")
    print(f"     Journal: {args.journal or 'auto-selected'}")


def cmd_status(args):
    root = get_root()
    papers_dir = get_papers_dir(root)
    paper_dir = papers_dir / args.paper
    if not paper_dir.exists():
        print(f"[ERROR] Paper not found: {args.paper}"); sys.exit(1)
    engine = PaperLoopEngine(root, args.paper, papers_dir)
    print(engine.get_status_summary())
    passport = PaperPassport(paper_dir)
    drifted = passport.detect_artifact_drift()
    if drifted:
        print(f"\n[WARNING] {len(drifted)} artifact(s) drifted. Run 'sync-artifact-stale'.")


def cmd_run(args):
    root = get_root()
    papers_dir = get_papers_dir(root)
    engine = PaperLoopEngine(root, args.paper, papers_dir)
    stage = engine.decide_next_stage()
    if stage is None:
        print("[OK] Pipeline complete or blocked. Run 'status' or 'diagnose-gate-failures'.")
        return
    while stage:
        print(f"  -> Running: {stage}")
        result = engine.run_stage(stage)
        verify = engine.verify_stage(stage)
        engine.record_and_sync()
        if not verify["all_passed"] and args.stop_on_failure:
            print(f"  [FAIL] {stage}"); break
        stage = engine.decide_next_stage()
    print(f"\n[OK] State: {engine.pipeline_state.value}")


def cmd_checkpoint(args):
    root = get_root()
    papers_dir = get_papers_dir(root)
    passport = PaperPassport(papers_dir / args.paper)
    entry = passport.record_checkpoint(stage=args.stage, decision=args.decision, notes=args.notes or "")
    print(f"[OK] Checkpoint: {entry.checkpoint_id} | {args.stage} | {args.decision}")


def cmd_integrity(args):
    root = get_root()
    papers_dir = get_papers_dir(root)
    paper_dir = papers_dir / args.paper
    sections = {}
    for sec in ["abstract", "introduction", "methods", "results", "discussion"]:
        f = paper_dir / "manuscript" / f"{sec}.md"
        if f.exists():
            sections[sec] = f.read_text(encoding="utf-8")
    bibtex = paper_dir / "references" / "library.bib"
    checker = IntegrityGateChecker(paper_dir)
    report = checker.run_all_checks(manuscript_sections=sections if sections else None,
                                    bibtex_path=bibtex if bibtex.exists() else None)
    print(checker.generate_markdown_report(report))
    (paper_dir / "integrity").mkdir(parents=True, exist_ok=True)
    (paper_dir / "integrity" / "integrity_report.md").write_text(checker.generate_markdown_report(report), encoding="utf-8")
    passport = PaperPassport(paper_dir)
    passport.record_integrity_event("gate_run", report.to_dict())
    if report.blocks_pipeline:
        print("\n[BLOCKED] Critical failures. Run 'diagnose-gate-failures'.")
        sys.exit(1)


def cmd_diagnose(args):
    root = get_root()
    papers_dir = get_papers_dir(root)
    engine = PaperLoopEngine(root, args.paper, papers_dir)
    diag = engine.diagnose_failures()
    print(f"Failed stages: {diag['failed_stages']}")
    for f in diag["failures"]:
        print(f"  Stage: {f['stage']} | Errors: {f['errors']} | Gate fails: {f['gate_failures']}")


def cmd_drift(args):
    root = get_root()
    papers_dir = get_papers_dir(root)
    passport = PaperPassport(papers_dir / args.paper)
    drifted = passport.detect_artifact_drift()
    if drifted:
        print(f"[DRIFT] {len(drifted)} artifact(s):")
        for d in drifted:
            print(f"  - {d['path']}: {d['status']}")
    else:
        print("[OK] No artifact drift.")


def cmd_sync(args):
    root = get_root()
    papers_dir = get_papers_dir(root)
    paper_dir = papers_dir / args.paper
    passport = PaperPassport(paper_dir)
    engine = PaperLoopEngine(root, args.paper, papers_dir)
    dep_map = {}
    for sd in engine.PIPELINE_STAGES:
        for art in sd.produces_artifacts:
            dep_map[art] = sd.downstream
    result = passport.sync_artifact_stale(dep_map)
    print(f"[OK] {result['stale_count']} stage(s) marked stale")
    for s in result["stale_stages"]:
        print(f"  - {s}")


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


def main():
    parser = argparse.ArgumentParser(description="Paper Workflow CLI")
    sub = parser.add_subparsers(dest="command")

    p = sub.add_parser("create-project"); p.add_argument("--idea", required=True); p.add_argument("--field", required=True)
    p.add_argument("--journal"); p.add_argument("--timeline", type=int)

    p = sub.add_parser("status"); p.add_argument("--paper", required=True)

    p = sub.add_parser("run-pipeline"); p.add_argument("--paper", required=True)
    p.add_argument("--stop-on-failure", action="store_true")

    p = sub.add_parser("checkpoint"); p.add_argument("--paper", required=True); p.add_argument("--stage", required=True)
    p.add_argument("--decision", required=True, choices=["approved", "rejected", "revision_needed"]); p.add_argument("--notes")

    p = sub.add_parser("run-integrity-gate"); p.add_argument("--paper", required=True)
    p = sub.add_parser("diagnose-gate-failures"); p.add_argument("--paper", required=True)
    p = sub.add_parser("detect-artifact-drift"); p.add_argument("--paper", required=True)
    p = sub.add_parser("sync-artifact-stale"); p.add_argument("--paper", required=True)
    sub.add_parser("list-papers")

    p = sub.add_parser("strategy"); p.add_argument("--idea", required=True); p.add_argument("--field", required=True)
    p.add_argument("--journal"); p.add_argument("--timeline", type=int)

    args = parser.parse_args()
    if args.command is None:
        parser.print_help(); return

    {"create-project": cmd_create, "status": cmd_status, "run-pipeline": cmd_run,
     "checkpoint": cmd_checkpoint, "run-integrity-gate": cmd_integrity,
     "diagnose-gate-failures": cmd_diagnose, "detect-artifact-drift": cmd_drift,
     "sync-artifact-stale": cmd_sync, "list-papers": cmd_list, "strategy": cmd_strategy}[args.command](args)


if __name__ == "__main__":
    main()
