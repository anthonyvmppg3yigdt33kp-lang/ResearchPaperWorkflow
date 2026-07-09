"""
Paper Workflow CLI — Command-line interface for the research paper workflow system.

Full pipeline control plus a model-facing AI harness for Claude/Codex.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import yaml

from paper_workflow.ai_harness import AIWorkflowHarness
from paper_workflow.analysis import AnalysisDesign, run_analysis_adapter
from paper_workflow.api import WorkflowAPI
from paper_workflow.bioinformatics.code_source_importer import CodeSourceImporter
from paper_workflow.bioinformatics.environment_registry import EnvironmentRegistry
from paper_workflow.bioinformatics.method_adapter import adapt_method_block
from paper_workflow.bioinformatics.method_asset_audit import MethodAssetAuditor
from paper_workflow.bioinformatics.module_feedback import ModuleFeedbackManager
from paper_workflow.bioinformatics.module_registry import ModuleRegistry
from paper_workflow.bioinformatics.module_selector import MethodSelector
from paper_workflow.outputs.result_run_manager import ResultRunManager
from paper_workflow.routing.mode_resolver import ModeResolver
from paper_workflow.routing.tool_doctor import ToolDoctor, format_doctor_report
from paper_workflow.strategy.research_strategy import ResearchStrategyManager
from paper_workflow.target_task import TargetTaskOrchestrator
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


def get_paper_dir(args, must_exist: bool = True) -> Path:
    root = get_root()
    papers_dir = get_papers_dir(root)
    paper_dir = papers_dir / args.paper
    if must_exist and not paper_dir.exists():
        print(f"[ERROR] Paper not found: {args.paper}")
        sys.exit(1)
    return paper_dir


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


def cmd_route_task(args):
    resolver = ModeResolver(get_root())
    try:
        route = resolver.resolve_route(
            args.request,
            explicit_mode=args.mode,
            explicit_profile=args.profile,
            paper_id=args.paper,
            explicit_journal=args.journal,
        )
    except (ValueError, FileNotFoundError) as exc:
        print(f"[ERROR] {exc}")
        sys.exit(1)
    if args.check_tools:
        route["doctor"] = ToolDoctor(get_root()).run()
    if args.json:
        print(json.dumps(route, indent=2, ensure_ascii=False))
    else:
        print(f"Mode: {route['mode']}")
        print(f"Profile: {route['profile']}")
        print(f"Active layers: {', '.join(route['active_layers']) or 'none'}")
        print(f"Active stages: {', '.join(route['active_stages']) or 'none'}")
        print(f"Deferred stages: {', '.join(route['deferred_stages']) or 'none'}")
        print(f"Output contract: {route['output_contract'] or 'none'}")
        print(f"Journal policy: {json.dumps(route['journal_policy'], ensure_ascii=False)}")


def cmd_doctor(args):
    report = ToolDoctor(get_root()).run()
    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print(format_doctor_report(report))
    if args.strict and report["status"] == "fail":
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


def cmd_new_run(args):
    paper_dir = get_paper_dir(args)
    manager = ResultRunManager(paper_dir)
    try:
        manifest = manager.create_run(
            run_id=args.run_id,
            mode=args.mode,
            status=args.status,
            notes=args.notes or "",
            allow_existing=args.allow_existing,
        )
        current = None
        if args.set_current:
            current = manager.set_current_run(
                run_id=args.run_id,
                status=args.status,
                user_approved=args.user_approved,
                notes=args.notes or "",
            )
    except (ValueError, FileExistsError, FileNotFoundError) as exc:
        print(f"[ERROR] {exc}")
        sys.exit(1)

    if args.json:
        print(json.dumps({"run": manifest, "current_run": current}, indent=2, ensure_ascii=False))
    else:
        print(f"[OK] Run created: {args.run_id}")
        print(f"     Path: {manager.run_path(args.run_id)}")
        if current:
            print(f"     Current pointer: {manager.current_run_file}")


def cmd_set_current_run(args):
    paper_dir = get_paper_dir(args)
    manager = ResultRunManager(paper_dir)
    try:
        current = manager.set_current_run(
            run_id=args.run_id,
            status=args.status,
            user_approved=args.user_approved,
            notes=args.notes or "",
        )
    except (ValueError, FileNotFoundError) as exc:
        print(f"[ERROR] {exc}")
        sys.exit(1)

    if args.json:
        print(json.dumps(current, indent=2, ensure_ascii=False))
    else:
        print(f"[OK] Current run set: {args.run_id}")
        print(f"     Status: {current['status']}")
        print(f"     Pointer: {manager.current_run_file}")


def cmd_brief_status(args):
    paper_dir = get_paper_dir(args)
    manager = ResultRunManager(paper_dir)
    status = manager.brief_status()
    if args.json:
        print(json.dumps(status, indent=2, ensure_ascii=False))
    else:
        print(f"Paper: {status['paper_id']}")
        print(f"State: {status['pipeline_state']}")
        current = status.get("current_run") or {}
        print(f"Current run: {current.get('active_run_id', '(none)')}")
        print(f"Truth source: {status['truth_source']}")
        if status.get("brief_path"):
            print(f"Brief: {status['brief_path']}")
        else:
            print("Brief: (missing)")


def cmd_evaluate_run(args):
    paper_dir = get_paper_dir(args)
    manager = ResultRunManager(paper_dir)
    try:
        evaluation = manager.evaluate_run(args.run_id, write_report=args.write_report)
    except (ValueError, FileNotFoundError) as exc:
        print(f"[ERROR] {exc}")
        sys.exit(1)

    data = evaluation.to_dict()
    if args.json:
        print(json.dumps(data, indent=2, ensure_ascii=False))
    else:
        print(f"Run: {data['run_id']}")
        print(f"Status: {data['status']}")
        print(f"Files: {data['output_file_count']} ({data['output_size_bytes']} bytes)")
        print(f"Missing required files: {', '.join(data['missing_required_files']) or 'none'}")
        print(f"Figure source map: {data['has_figure_source_map']}")
        print(f"Table source map: {data['has_table_source_map']}")
        if args.write_report:
            print(f"Report: {manager.run_path(args.run_id) / 'evaluation_report.yaml'}")


def cmd_plan_analysis(args):
    paper_dir = get_paper_dir(args)
    manager = ResultRunManager(paper_dir)
    try:
        if not manager.run_path(args.run_id).exists():
            manager.create_run(
                run_id=args.run_id,
                mode="analysis_design_mode",
                status="prepared",
                notes=args.notes or "",
            )
        design = manager.write_analysis_design(
            run_id=args.run_id,
            goal=args.goal,
            modality=args.modality,
            inputs=args.input or [],
            primary_contrast=args.primary_contrast,
            group_column=args.group_column,
            sample_id_column=args.sample_id_column,
            execution_backend=args.execution_backend,
            from_code_library=args.from_code_library,
            module_limit=args.module_limit,
        )
        if args.set_current:
            manager.set_current_run(
                run_id=args.run_id,
                status="prepared",
                user_approved=False,
                notes="analysis design prepared; execution not approved",
            )
    except (ValueError, FileExistsError, FileNotFoundError) as exc:
        print(f"[ERROR] {exc}")
        sys.exit(1)

    if args.json:
        print(json.dumps(design, indent=2, ensure_ascii=False))
    else:
        print(f"[OK] Analysis design written: {manager.run_path(args.run_id) / 'analysis_design.yaml'}")
        if (manager.run_path(args.run_id) / "analysis_graph.yaml").exists():
            print(f"     Analysis graph: {manager.run_path(args.run_id) / 'analysis_graph.yaml'}")
            print(f"     Method selection: {manager.run_path(args.run_id) / 'method_selection_report.md'}")
        print("     Execution status: not_executed")
        print("     Human checkpoint required before execution.")


def cmd_run_analysis(args):
    if args.execute and not args.approved:
        print("[ERROR] --execute requires --approved for any real analysis execution.")
        sys.exit(1)

    paper_dir = get_paper_dir(args)
    manager = ResultRunManager(paper_dir)
    try:
        run_dir = manager.run_path(args.run_id)
        if not run_dir.exists():
            raise FileNotFoundError(f"Run does not exist: {run_dir}")
        design_path = run_dir / "analysis_design.yaml"
        if not design_path.exists():
            raise FileNotFoundError(f"Analysis design not found: {design_path}")
        design = AnalysisDesign.from_file(design_path)
        graph_path = run_dir / "analysis_graph.yaml"
        if not design.analysis_graph and graph_path.exists():
            graph_data = yaml.safe_load(graph_path.read_text(encoding="utf-8")) or {}
            if isinstance(graph_data, dict):
                design.raw.update(graph_data)
                design.analysis_graph = dict((graph_data.get("analysis_graph") or {}))
        if args.approved:
            design.user_approval = True
        result = run_analysis_adapter(design, run_dir, execute=args.execute, backend=args.backend)
        evaluation = manager.evaluate_run(args.run_id, write_report=True)
        usage_records = ModuleFeedbackManager(get_root()).record_run(
            paper_id=args.paper,
            run_id=args.run_id,
            run_dir=run_dir,
            adapter_result=result.to_dict(),
            evaluation=evaluation.to_dict(),
        )
        if args.set_current:
            manager.set_current_run(
                run_id=args.run_id,
                status="prepared" if not args.execute else "exploratory",
                user_approved=args.approved,
                notes=f"run-analysis adapter status: {result.status}",
            )
    except (ValueError, FileNotFoundError) as exc:
        print(f"[ERROR] {exc}")
        sys.exit(1)

    payload = {"adapter_result": result.to_dict(), "evaluation": evaluation.to_dict(), "module_usage": usage_records}
    if args.json:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        print(f"Run: {args.run_id}")
        print(f"Adapter: {result.adapter}")
        print(f"Status: {result.status}")
        print(f"Artifacts: {len(result.artifacts)}")
        print(f"Warnings: {len(result.warnings)}")
        print(f"Errors: {len(result.errors)}")
        print(f"Evaluation: {evaluation.status}")
        print(f"Report: {manager.run_path(args.run_id) / 'evaluation_report.yaml'}")
        if result.errors:
            print("Blocked/errors:")
            for err in result.errors:
                print(f"  - {err}")


def cmd_list_modules(args):
    registry = ModuleRegistry(get_root())
    modules = registry.list_modules(modality=args.modality or "", step=args.step or "", language=args.language or "")
    payload = {"summary": registry.capability_summary(), "modules": modules}
    if args.json:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return
    print(f"Registry: {registry.registry_path}")
    print(f"Modules: {len(modules)} / {payload['summary']['module_count']}")
    for module in modules:
        print(
            f"  - {module.get('id') or module.get('module_id')} | "
            f"{module.get('modality')} | {module.get('step')} | {module.get('language')}"
        )


def cmd_inspect_module(args):
    registry = ModuleRegistry(get_root())
    module = registry.get(args.module_id)
    if not module:
        print(f"[ERROR] Module not found: {args.module_id}")
        sys.exit(1)
    issues = registry.validate_module(args.module_id)
    payload = {"module_id": args.module_id, "module": module, "issues": issues}
    if args.json:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        print(f"Module: {args.module_id}")
        print(f"Name: {module.get('name', '')}")
        print(f"Modality/step: {module.get('modality', '')} / {module.get('step', '')}")
        print(f"Language: {module.get('language', '')}")
        print(f"Source: {(module.get('source') or {}).get('path', '')}")
        print(f"Claim boundary: {module.get('claim_boundary', '')}")
        print(f"Issues: {', '.join(issues) if issues else 'none'}")
    if args.strict and issues:
        sys.exit(1)


def cmd_list_capabilities(args):
    selector = MethodSelector(project_root=get_root(), paper_dir=get_paper_dir(args, must_exist=bool(args.paper)) if args.paper else None)
    selected = selector.select(goal=args.question, modalities=args.modality or [], max_modules=args.limit)
    decision = {
        "recommended_now": [],
        "deferred_until_environment_ready": [],
        "planning_only": [],
        "blocked_by_environment": [],
        "blocked_by_grade": [],
        "forbidden_as_primary": [],
        "downstream_allowed": [],
    }
    for module in selected:
        module_id = module.get("id") or module.get("module_id")
        score = module.get("method_selection_score", {})
        gate = module.get("production_gate") or score.get("production_gate") or {}
        item = {
            "module": module_id,
            "score": score.get("total"),
            "grade": module.get("production_capability_grade") or score.get("production_capability_grade"),
            "claim_permission": module.get("claim_permission") or score.get("claim_permission"),
            "environment_status": module.get("current_environment_status") or score.get("current_environment_status"),
            "reason": (module.get("strategy_evaluation") or {}).get("decision", ""),
        }
        if gate.get("allowed"):
            decision["recommended_now"].append(item)
        if item["environment_status"] == "blocked":
            decision["blocked_by_environment"].append(item)
            decision["deferred_until_environment_ready"].append(item)
        if not gate.get("allowed"):
            decision["blocked_by_grade"].append({**item, "blockers": gate.get("reasons", [])})
        if item["grade"] in {"dry_run_contract", "adapter_contract", "planning_contract", "scaffold_only"}:
            decision["planning_only"].append(item)
        if module_id == "bulk_rnaseq.wgcna.v1":
            decision["forbidden_as_primary"].append({**item, "reason": "WGCNA does not replace primary differential expression"})
        if "fgsea" in str(module_id):
            decision["downstream_allowed"].append({**item, "prerequisite": "ranked_gene_statistic exists"})
    payload = {
        "question": args.question,
        "modalities": args.modality or [],
        "selected_modules": selected,
        **decision,
    }
    if args.json:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return
    print(f"Question: {args.question}")
    for module in selected:
        score = module.get("method_selection_score", {})
        print(
            f"  - {module.get('id') or module.get('module_id')} | "
            f"score={score.get('total')} env={score.get('environment_status')} "
            f"risk={score.get('reviewer_risk')}"
        )


def cmd_audit_method_assets(args):
    result = MethodAssetAuditor(get_root()).run()
    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(f"Status: {result['status']}")
        print(f"Modules: {result['module_count']}")
        print(f"Issues: {result['issue_count']}")
        print(f"Warnings: {result['warning_count']}")
        for issue in result["issues"]:
            print(f"  - {issue}")
        if args.show_warnings:
            for warning in result["warnings"]:
                print(f"  - WARNING: {warning}")
    if args.strict and result["status"] == "fail":
        sys.exit(1)


def cmd_import_code_source(args):
    importer = CodeSourceImporter(get_root())
    try:
        result = importer.import_source(
            source_id=args.source_id,
            github=args.github or "",
            local=args.local or "",
            clone_github=args.clone,
            paper_doi=args.paper_doi or "",
            license_text=args.license or "requires_human_review",
        ).to_dict()
    except (ValueError, FileNotFoundError) as exc:
        print(f"[ERROR] {exc}")
        sys.exit(1)
    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(f"[OK] Source imported for review: {result['source_id']}")
        print(f"     Manifest: {result['manifest_path']}")
        print("     Registry update: not performed")


def cmd_review_code_source(args):
    importer = CodeSourceImporter(get_root())
    try:
        result = importer.review_source(args.source_id)
    except (ValueError, FileNotFoundError) as exc:
        print(f"[ERROR] {exc}")
        sys.exit(1)
    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(f"[OK] Source review packet updated: {args.source_id}")
        print("     Registry update allowed: false")


def cmd_adapt_method_block(args):
    try:
        result = adapt_method_block(
            project_root=get_root(),
            source_id=args.source_id,
            block_id=args.block_id,
            module_id=args.module_id,
            family=args.family,
            approved_review=args.approved_review,
            register=args.register,
        )
    except (ValueError, FileNotFoundError, PermissionError) as exc:
        print(f"[ERROR] {exc}")
        sys.exit(1)
    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(f"[OK] Adapted module scaffold: {result['module_id']}")
        print(f"     Directory: {result['module_dir']}")
        print("     Registry update: not performed")
        if result.get("registry_patch"):
            print(f"     Registry patch: {result['registry_patch']}")


def cmd_register_figure_style(args):
    importer = CodeSourceImporter(get_root())
    try:
        result = importer.register_figure_style(args.source_id, style_id=args.style_id or "")
    except (ValueError, FileNotFoundError) as exc:
        print(f"[ERROR] {exc}")
        sys.exit(1)
    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(f"[OK] Figure style registered: {result['style_id']}")


def cmd_list_figure_styles(args):
    result = CodeSourceImporter(get_root()).list_figure_styles()
    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        styles = result.get("styles", {}) or {}
        if not styles:
            print("No figure styles registered.")
        for style_id, style in styles.items():
            print(f"- {style_id}: source={style.get('source_id', '')}")


def cmd_summarize_module_usage(args):
    result = ModuleFeedbackManager(get_root()).summarize_module_usage(args.module)
    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(f"Module: {args.module}")
        print(f"Usage count: {result['usage_count']}")
        print(f"Status counts: {result['status_counts']}")


def cmd_propose_module_improvement(args):
    try:
        result = ModuleFeedbackManager(get_root()).propose_module_improvement(args.run_id, paper_id=args.paper or "")
    except FileNotFoundError as exc:
        print(f"[ERROR] {exc}")
        sys.exit(1)
    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(f"[OK] Proposal written: {result['path']}")
        print("     Registry update: not performed")


def cmd_apply_module_improvement(args):
    try:
        result = ModuleFeedbackManager(get_root()).apply_module_improvement(args.proposal, approved=args.approved)
    except (FileNotFoundError, PermissionError) as exc:
        print(f"[ERROR] {exc}")
        sys.exit(1)
    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(f"[OK] Proposal approved for manual implementation: {result['proposal_id']}")
        print("     Registry update: not performed")


def cmd_list_envs(args):
    registry = EnvironmentRegistry(get_root())
    payload = {
        "environment_registry": str(registry.registry_path),
        "environment_registry_hash": registry.content_hash(),
        "environments": registry.list_envs(),
    }
    if args.json:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return
    print(f"Registry: {registry.registry_path}")
    for env in payload["environments"]:
        print(f"  - {env.get('env_id')} | {env.get('language')} | runner={env.get('runner')}")


def cmd_inspect_env(args):
    registry = EnvironmentRegistry(get_root())
    env = registry.get(args.env_id)
    if not env:
        print(f"[ERROR] Environment not found: {args.env_id}")
        sys.exit(1)
    payload = {"env_id": args.env_id, "environment": env}
    if args.json:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return
    print(f"Environment: {args.env_id}")
    print(f"Language: {env.get('language', '')}")
    print(f"Runner: {env.get('runner', '')}")
    print(f"Packages: {', '.join(env.get('required_packages', env.get('packages', [])) or []) or 'none'}")


def cmd_doctor_env(args):
    registry = EnvironmentRegistry(get_root())
    kwargs = {
        "require_lock": args.require_lock,
        "require_packages": not args.skip_packages,
    }
    if args.write_report:
        report = registry.write_environment_report(
            args.env_id,
            get_root() / "code_library" / "environment_reports" / f"{args.env_id}.yaml",
            **kwargs,
        )
    else:
        report = registry.validate_environment(
            args.env_id,
            **kwargs,
        )
        report["environment_registry"] = str(registry.registry_path)
        report["environment_registry_hash"] = registry.content_hash()
    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print(f"Environment: {args.env_id}")
        print(f"Status: {report['status']}")
        print(f"Runner: {report.get('runner', '')}")
        print(f"Reproducibility: {report.get('reproducibility_grade', '')}")
        for issue in report.get("issues", []):
            print(f"  - {issue}")
    if args.strict and report["status"] != "pass":
        sys.exit(1)


def cmd_validate_env(args):
    modules = ModuleRegistry(get_root())
    module = modules.get(args.module)
    if not module:
        print(f"[ERROR] Module not found: {args.module}")
        sys.exit(1)
    env_id = str((module.get("environment") or {}).get("env_id", ""))
    registry = EnvironmentRegistry(get_root())
    report = registry.validate_environment(
        env_id,
        language=str(module.get("language", "")),
        require_lock=args.require_lock,
        require_packages=not args.skip_packages,
    )
    payload = {"module_id": args.module, "env_id": env_id, "environment": report}
    if args.json:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        print(f"Module: {args.module}")
        print(f"Environment: {env_id}")
        print(f"Status: {report['status']}")
        for issue in report.get("issues", []):
            print(f"  - {issue}")
    if args.strict and report["status"] != "pass":
        sys.exit(1)


def cmd_target(args):
    orchestrator = TargetTaskOrchestrator(get_root())
    try:
        if args.target_command == "validate":
            payload = orchestrator.validate(args.target, require_packages=args.require_packages)
        elif args.target_command == "plan":
            payload = orchestrator.plan(args.target)
        elif args.target_command == "run":
            payload = orchestrator.run(args.target, approved=args.approved, execute=args.execute)
        elif args.target_command == "evaluate":
            payload = orchestrator.evaluate(args.target, fail_closed=args.fail_closed)
        elif args.target_command == "package":
            payload = orchestrator.package(args.target)
        else:
            raise ValueError("target subcommand is required")
    except (ValueError, FileNotFoundError, PermissionError) as exc:
        print(f"[ERROR] {exc}")
        sys.exit(1)
    if args.json:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        print(f"Target command: {args.target_command}")
        print(f"Status: {payload.get('status', payload.get('environment_status', 'unknown'))}")
        if payload.get("target_id"):
            print(f"Target: {payload['target_id']}")
        if payload.get("run_id"):
            print(f"Run: {payload['run_id']}")
        if payload.get("run_dir"):
            print(f"Run dir: {payload['run_dir']}")
    if args.target_command in {"evaluate", "run", "package"}:
        final_status = payload.get("status") or payload.get("final_status") or (payload.get("evaluation") or {}).get("status")
        if getattr(args, "strict", False) and final_status not in {"pass", "workflow_test_pass"}:
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

    p = sub.add_parser("route-task")
    p.add_argument("--request", required=True)
    p.add_argument("--mode", choices=["exploration_mode", "analysis_design_mode", "execution_mode",
                                      "closeout_audit_mode", "ppt_briefing_mode", "retrospective_mode"])
    p.add_argument("--profile")
    p.add_argument("--paper")
    p.add_argument("--journal")
    p.add_argument("--check-tools", action="store_true")
    p.add_argument("--json", action="store_true")

    p = sub.add_parser("doctor")
    p.add_argument("--json", action="store_true")
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

    p = sub.add_parser("new-run")
    p.add_argument("--paper", required=True)
    p.add_argument("--run-id", required=True)
    p.add_argument("--mode", default="analysis_design_mode",
                   choices=["exploration_mode", "analysis_design_mode", "execution_mode",
                            "closeout_audit_mode", "ppt_briefing_mode", "retrospective_mode"])
    p.add_argument("--status", default="prepared",
                   choices=["exploratory", "prepared", "qa_passed", "stage_completed", "stale"])
    p.add_argument("--notes")
    p.add_argument("--allow-existing", action="store_true")
    p.add_argument("--set-current", action="store_true")
    p.add_argument("--user-approved", action="store_true")
    p.add_argument("--json", action="store_true")

    p = sub.add_parser("set-current-run")
    p.add_argument("--paper", required=True)
    p.add_argument("--run-id", required=True)
    p.add_argument("--status", default="prepared",
                   choices=["exploratory", "prepared", "qa_passed", "stage_completed", "stale"])
    p.add_argument("--notes")
    p.add_argument("--user-approved", action="store_true")
    p.add_argument("--json", action="store_true")

    p = sub.add_parser("brief-status")
    p.add_argument("--paper", required=True)
    p.add_argument("--json", action="store_true")

    p = sub.add_parser("evaluate-run")
    p.add_argument("--paper", required=True)
    p.add_argument("--run-id", required=True)
    p.add_argument("--write-report", action="store_true")
    p.add_argument("--json", action="store_true")

    p = sub.add_parser("plan-analysis")
    p.add_argument("--paper", required=True)
    p.add_argument("--run-id", required=True)
    p.add_argument("--goal", required=True)
    p.add_argument("--modality", default="general",
                   choices=["general", "bulk_rnaseq", "scrna", "spatial",
                            "multiomics", "metabolomics", "mr", "ml_biomarker"])
    p.add_argument("--input", action="append")
    p.add_argument("--primary-contrast", default="requires_human_input")
    p.add_argument("--group-column", default="condition")
    p.add_argument("--sample-id-column", default="sample_id")
    p.add_argument("--execution-backend", default="dry_run",
                   choices=["dry_run", "python_builtin_pilot"])
    p.add_argument("--from-code-library", action="store_true")
    p.add_argument("--module-limit", type=int, default=4)
    p.add_argument("--notes")
    p.add_argument("--set-current", action="store_true")
    p.add_argument("--json", action="store_true")

    p = sub.add_parser("run-analysis")
    p.add_argument("--paper", required=True)
    p.add_argument("--run-id", required=True)
    p.add_argument("--execute", action="store_true")
    p.add_argument("--approved", action="store_true")
    p.add_argument("--backend", choices=["dry_run", "python_builtin_pilot"])
    p.add_argument("--set-current", action="store_true")
    p.add_argument("--json", action="store_true")

    p = sub.add_parser("list-modules")
    p.add_argument("--modality")
    p.add_argument("--step")
    p.add_argument("--language")
    p.add_argument("--json", action="store_true")

    p = sub.add_parser("inspect-module")
    p.add_argument("module_id")
    p.add_argument("--json", action="store_true")
    p.add_argument("--strict", action="store_true")

    p = sub.add_parser("list-capabilities")
    p.add_argument("--question", required=True)
    p.add_argument("--modality", action="append")
    p.add_argument("--paper")
    p.add_argument("--limit", type=int, default=6)
    p.add_argument("--json", action="store_true")

    p = sub.add_parser("import-code-source")
    source = p.add_mutually_exclusive_group(required=True)
    source.add_argument("--github")
    source.add_argument("--local")
    p.add_argument("--source-id", required=True)
    p.add_argument("--clone", action="store_true", help="Clone GitHub source with depth=1, retain parsable scripts, and generate module proposals.")
    p.add_argument("--paper-doi")
    p.add_argument("--license")
    p.add_argument("--json", action="store_true")

    p = sub.add_parser("audit-method-assets")
    p.add_argument("--json", action="store_true")
    p.add_argument("--strict", action="store_true")
    p.add_argument("--show-warnings", action="store_true")

    p = sub.add_parser("review-code-source")
    p.add_argument("--source-id", required=True)
    p.add_argument("--json", action="store_true")

    p = sub.add_parser("adapt-method-block")
    p.add_argument("--source-id", required=True)
    p.add_argument("--block-id", required=True)
    p.add_argument("--module-id", required=True)
    p.add_argument("--family", required=True)
    p.add_argument("--approved-review", action="store_true")
    p.add_argument("--register", action="store_true")
    p.add_argument("--json", action="store_true")

    p = sub.add_parser("register-figure-style")
    p.add_argument("--source-id", required=True)
    p.add_argument("--style-id")
    p.add_argument("--json", action="store_true")

    p = sub.add_parser("list-figure-styles")
    p.add_argument("--json", action="store_true")

    p = sub.add_parser("summarize-module-usage")
    p.add_argument("--module", required=True)
    p.add_argument("--json", action="store_true")

    p = sub.add_parser("propose-module-improvement")
    p.add_argument("--run-id", required=True)
    p.add_argument("--paper")
    p.add_argument("--json", action="store_true")

    p = sub.add_parser("apply-module-improvement")
    p.add_argument("--proposal", required=True)
    p.add_argument("--approved", action="store_true")
    p.add_argument("--json", action="store_true")

    p = sub.add_parser("list-envs")
    p.add_argument("--json", action="store_true")

    p = sub.add_parser("inspect-env")
    p.add_argument("env_id")
    p.add_argument("--json", action="store_true")

    p = sub.add_parser("doctor-env")
    p.add_argument("env_id")
    p.add_argument("--require-lock", action="store_true")
    p.add_argument("--skip-packages", action="store_true")
    p.add_argument("--write-report", action="store_true")
    p.add_argument("--json", action="store_true")
    p.add_argument("--strict", action="store_true")

    p = sub.add_parser("validate-env")
    p.add_argument("--module", required=True)
    p.add_argument("--require-lock", action="store_true")
    p.add_argument("--skip-packages", action="store_true")
    p.add_argument("--json", action="store_true")
    p.add_argument("--strict", action="store_true")

    p = sub.add_parser("target")
    target_sub = p.add_subparsers(dest="target_command")
    for name in ["validate", "plan", "run", "evaluate", "package"]:
        sp = target_sub.add_parser(name)
        sp.add_argument("--target", required=True)
        sp.add_argument("--json", action="store_true")
        sp.add_argument("--strict", action="store_true")
        if name == "validate":
            sp.add_argument("--require-packages", action="store_true")
        if name == "run":
            sp.add_argument("--approved", action="store_true")
            sp.add_argument("--execute", action="store_true")
        if name == "evaluate":
            sp.add_argument("--fail-closed", action="store_true")

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

    if args.command not in {"install-skills", "route-task", "doctor"}:
        try:
            ensure_skills_available(get_root(), auto_install=True, quiet=True)
        except Exception as exc:
            print(f"[WARNING] Skill auto-check skipped: {exc}")

    {"create-project": cmd_create, "status": cmd_status, "run-pipeline": cmd_run,
     "checkpoint": cmd_checkpoint, "run-integrity-gate": cmd_integrity,
     "diagnose-gate-failures": cmd_diagnose, "detect-artifact-drift": cmd_drift,
     "sync-artifact-stale": cmd_sync, "validate-workflow": cmd_validate_workflow,
     "validate-contract": cmd_validate_contract,
     "route-task": cmd_route_task, "doctor": cmd_doctor,
     "list-harness-invocations": cmd_list_harness_invocations,
     "complete-harness-invocation": cmd_complete_harness_invocation,
     "list-papers": cmd_list, "strategy": cmd_strategy,
     "install-skills": cmd_install_skills, "run-aigc-humanizer": cmd_aigc_humanizer,
     "new-run": cmd_new_run, "set-current-run": cmd_set_current_run,
     "brief-status": cmd_brief_status, "evaluate-run": cmd_evaluate_run,
     "plan-analysis": cmd_plan_analysis, "run-analysis": cmd_run_analysis,
     "list-modules": cmd_list_modules, "inspect-module": cmd_inspect_module,
     "list-capabilities": cmd_list_capabilities,
      "audit-method-assets": cmd_audit_method_assets,
      "import-code-source": cmd_import_code_source,
      "review-code-source": cmd_review_code_source,
      "adapt-method-block": cmd_adapt_method_block,
      "register-figure-style": cmd_register_figure_style,
     "list-figure-styles": cmd_list_figure_styles,
     "summarize-module-usage": cmd_summarize_module_usage,
     "propose-module-improvement": cmd_propose_module_improvement,
     "apply-module-improvement": cmd_apply_module_improvement,
     "list-envs": cmd_list_envs, "inspect-env": cmd_inspect_env,
     "doctor-env": cmd_doctor_env, "validate-env": cmd_validate_env,
     "target": cmd_target,
     "ai": cmd_ai_harness, "ai-harness": cmd_ai_harness}[args.command](args)


if __name__ == "__main__":
    main()
