"""Compile a scientific question into an evidence-bounded TargetTask."""

from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml

from paper_workflow.bioinformatics.module_registry import ModuleRegistry
from paper_workflow.bioinformatics.module_selector import MethodSelector
from paper_workflow.research_intent.knowledge import ResearchKnowledge
from paper_workflow.research_intent.schema import load_research_intent, normalize_modality, validate_research_intent


DEFAULT_FORBIDDEN_CLAIMS = [
    "disease mechanism",
    "clinical biomarker",
    "treatment response",
    "causal immune state",
]


def write_yaml(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8")


class ResearchIntentPlanner:
    """Produce an assessment, alternatives, figure plan, and executable target."""

    def __init__(self, project_root: Path):
        self.project_root = Path(project_root)
        self.registry = ModuleRegistry(self.project_root)
        self.knowledge = ResearchKnowledge(self.project_root)

    def validate(self, intent_path: Path | str) -> dict[str, Any]:
        intent = load_research_intent(intent_path)
        result = validate_research_intent(intent)
        result["intent"] = str(intent_path)
        result["question_types"] = self.infer_question_types(intent)
        return result

    def plan(self, intent_path: Path | str) -> dict[str, Any]:
        intent = load_research_intent(intent_path)
        validation = validate_research_intent(intent)
        if not validation["valid"]:
            raise ValueError("; ".join(validation["issues"]))

        project_id = validation["project_id"]
        paper_dir = self.project_root / "papers" / project_id
        plan_dir = paper_dir / "research_plan"
        plan_dir.mkdir(parents=True, exist_ok=True)
        question_types = self.infer_question_types(intent)
        method_decisions = self._method_decisions(intent, question_types)
        selected_modules = self._selected_modules(intent, method_decisions)
        module_gates = [self._module_gate(module_id) for module_id in selected_modules]
        ready_for_target_plan = bool(selected_modules) and all(item["exists"] and item["gate"]["allowed"] for item in module_gates)

        missing_information = self._missing_information(intent, question_types)
        execution_blockers = [item for item in missing_information if item["severity"] == "blocking"]
        assessment = {
            "schema_version": "scientific_assessment.v1",
            "project_id": project_id,
            "question": intent["question"],
            "project_goal": intent["project_goal"],
            "question_types": question_types,
            "facts": self._facts(intent),
            "assumptions": self._assumptions(intent),
            "unknowns": missing_information,
            "decisions": self._decisions(method_decisions),
            "recommended_phases": self._recommended_phases(question_types),
            "experience_reminders": self.knowledge.experience_for(question_types),
            "claim_boundary": intent["claim_boundary"],
            "ready_for_target_plan": ready_for_target_plan,
            "execution_blockers": execution_blockers,
            "validation_warnings": validation["warnings"],
        }
        strategy = {
            "schema_version": "strategy_simulation.v1",
            "project_id": project_id,
            "question_types": question_types,
            "alternatives": method_decisions,
            "recommended_now": [item for item in method_decisions if item["decision"] == "recommended_now"],
            "deferred": [item for item in method_decisions if item["decision"] == "deferred"],
            "planning_only": [item for item in method_decisions if item["decision"] == "planning_only"],
            "selected_modules": selected_modules,
            "module_gates": module_gates,
            "claim_boundary": intent["claim_boundary"],
        }
        figure_plan = self._figure_plan(intent, question_types, selected_modules)
        target = self._target_task(intent, selected_modules, figure_plan)

        resolved_intent = dict(intent)
        resolved_intent["resolved_question_types"] = question_types
        resolved_intent["resolved_target_id"] = target["target_id"]
        resolved_intent["resolved_at"] = datetime.now().isoformat()
        paths = {
            "resolved_intent": plan_dir / "research_intent_resolved.yaml",
            "scientific_assessment": plan_dir / "scientific_assessment.yaml",
            "strategy_simulation": plan_dir / "strategy_simulation.yaml",
            "figure_plan": plan_dir / "figure_plan.yaml",
            "figure_plan_markdown": plan_dir / "FIGURE_PLAN.md",
            "target_task": plan_dir / "target_task.yaml",
        }
        write_yaml(paths["resolved_intent"], resolved_intent)
        write_yaml(paths["scientific_assessment"], assessment)
        write_yaml(paths["strategy_simulation"], strategy)
        write_yaml(paths["figure_plan"], figure_plan)
        paths["figure_plan_markdown"].write_text(self._figure_plan_markdown(figure_plan), encoding="utf-8")
        write_yaml(paths["target_task"], target)
        return {
            "status": "planned" if ready_for_target_plan else "needs_input",
            "project_id": project_id,
            "paper_dir": str(paper_dir),
            "plan_dir": str(plan_dir),
            "target_id": target["target_id"],
            "target_task": str(paths["target_task"]),
            "ready_for_target_plan": ready_for_target_plan,
            "selected_modules": selected_modules,
            "execution_blockers": execution_blockers,
            "artifacts": {key: str(value) for key, value in paths.items()},
        }

    @staticmethod
    def infer_question_types(intent: dict[str, Any]) -> list[str]:
        declared = [str(item) for item in intent.get("scientific_questions", []) or []]
        text = " ".join([str(intent.get("question", "")), str(intent.get("title", "")), *declared]).lower()
        inferred = list(declared)
        rules = [
            (("subcluster", "cell state", "亚群", "细胞状态"), "subcluster_refinement"),
            (("marker", "findmarkers", "标志基因"), "marker_discovery"),
            (("differential", "disease", "control", "versus", " vs ", "差异", "疾病", "对照"), "disease_group_comparison"),
            (("pseudobulk", "cell-type differential", "cell type differential"), "cell_type_differential_expression"),
            (("bulk", "limma", "deseq2", "bulk rnaseq"), "bulk_differential_expression"),
            (("pathway", "enrichment", "gsea", "go ", "kegg", "通路", "富集"), "pathway_analysis"),
            (("wgcna", "co-expression", "network", "调控网络", "共表达"), "network_analysis"),
            (("cellchat", "nichenet", "communication", "细胞通讯"), "communication_analysis"),
            (("cell state", "atlas", "annotation", "细胞状态", "图谱", "注释"), "cell_state_identification"),
        ]
        for tokens, question_type in rules:
            if any(token in text for token in tokens):
                inferred.append(question_type)
        if not inferred:
            inferred.append("general_discovery")
        return list(dict.fromkeys(inferred))

    def _method_decisions(self, intent: dict[str, Any], question_types: list[str]) -> list[dict[str, Any]]:
        decisions = []
        for method in self.knowledge.methods_for(question_types):
            module_reports = [self._module_gate(module_id) for module_id in method.get("module_ids", []) or []]
            missing = self._method_prerequisite_gaps(method["id"], intent)
            allowed = [item for item in module_reports if item["exists"] and item["gate"]["allowed"]]
            if missing:
                decision = "deferred"
                score = 55
            elif allowed:
                decision = "recommended_now"
                score = 90 if "pseudobulk" in method["id"] else 80
            else:
                decision = "planning_only"
                score = 40
            decisions.append({
                "method_id": method["id"],
                "label": method.get("label", method["id"]),
                "decision": decision,
                "score": score,
                "solves": method.get("solves", []),
                "not_for": method.get("not_for", []),
                "statistical_unit": method.get("statistical_unit", "not_declared"),
                "prerequisites": method.get("prerequisites", []),
                "missing_prerequisites": missing,
                "module_reports": module_reports,
                "reviewer_risks": method.get("reviewer_risks", []),
                "claim_boundary": method.get("claim_boundary", ""),
                "figure_examples": method.get("figure_examples", []),
            })
        return sorted(decisions, key=lambda item: (-item["score"], item["method_id"]))

    def _module_gate(self, module_id: str) -> dict[str, Any]:
        module = self.registry.get(module_id)
        return {
            "module_id": module_id,
            "exists": bool(module),
            "grade": module.get("production_capability_grade", "") if module else "missing",
            "environment_status": module.get("current_environment_status", "unknown") if module else "missing",
            "claim_permission": module.get("claim_permission", "no_claim") if module else "no_claim",
            "gate": self.registry.production_gate(module) if module else {"allowed": False, "reasons": ["module_missing"]},
        }

    @staticmethod
    def _method_prerequisite_gaps(method_id: str, intent: dict[str, Any]) -> list[str]:
        data = intent.get("data") or {}
        gaps = []
        if method_id == "pseudobulk_deseq2":
            if not data.get("sample_id_column"):
                gaps.append("data.sample_id_column")
            if not data.get("condition_column"):
                gaps.append("data.condition_column")
            if data.get("biological_replicates") not in {True, "true", "documented"}:
                gaps.append("documented biological replicates")
        if method_id == "communication_inference" and not (intent.get("constraints") or {}).get("orthogonal_validation"):
            gaps.append("orthogonal validation plan")
        return gaps

    def _selected_modules(self, intent: dict[str, Any], decisions: list[dict[str, Any]]) -> list[str]:
        explicit = [str(item) for item in ((intent.get("workflow") or {}).get("required_modules", []) or [])]
        if explicit:
            return list(dict.fromkeys(explicit))
        selected = []
        for decision in decisions:
            if decision["decision"] != "recommended_now":
                continue
            for report in decision["module_reports"]:
                if report["gate"]["allowed"]:
                    selected.append(report["module_id"])
        if not selected:
            modality = normalize_modality(str((intent.get("data") or {}).get("modality", "general")))
            candidates = MethodSelector(self.project_root).select(
                goal=str(intent.get("question", "")),
                modalities=[modality],
                max_modules=3,
            )
            selected.extend(
                str(item.get("id") or item.get("module_id"))
                for item in candidates
                if (item.get("production_gate") or {}).get("allowed")
            )
        return list(dict.fromkeys(selected))

    def _target_task(self, intent: dict[str, Any], selected_modules: list[str], figure_plan: dict[str, Any]) -> dict[str, Any]:
        data = intent.get("data") or {}
        constraints = intent.get("constraints") or {}
        workflow = intent.get("workflow") or {}
        target_id = str(constraints.get("target_id") or f"{intent['project_id']}_{datetime.now().strftime('%Y%m%d')}_v1")
        if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_-]*_[0-9]{8}_v[0-9]+", target_id):
            raise ValueError("constraints.target_id must match <name>_<YYYYMMDD>_v<N>")
        required_envs = [str(item) for item in constraints.get("required_envs", []) or []]
        for module_id in selected_modules:
            module = self.registry.get(module_id)
            env_id = ((module or {}).get("environment") or {}).get("env_id")
            if env_id:
                required_envs.append(str(env_id))
        expected = intent.get("expected_outputs") or {}
        forbidden = list(dict.fromkeys([*DEFAULT_FORBIDDEN_CLAIMS, *(constraints.get("forbidden_claims", []) or [])]))
        return {
            "schema_version": "target_task.v1",
            "target_id": target_id,
            "title": intent["title"],
            "mode": "analysis_production_mode",
            "evidence_grade": constraints.get("evidence_grade", "exploratory"),
            "claim_boundary": intent["claim_boundary"],
            "data": {
                "dataset_id": data["dataset_id"],
                "modality": normalize_modality(str(data["modality"])),
                "format": data["format"],
                "input_path": data["input_path"],
                "immutable": bool(data.get("immutable", True)),
                "role": data.get("role", "research_data"),
                "sample_id_column": data.get("sample_id_column", ""),
                "condition_column": data.get("condition_column", ""),
            },
            "environment": {
                "required_envs": list(dict.fromkeys(required_envs)) or ["python_builtin"],
                "optional_envs": constraints.get("optional_envs", []),
                "package_policy": "validate before execute; never install silently",
            },
            "analysis_goal": {
                "primary_goal": intent["question"],
                "biological_scope": intent.get("scientific_questions", []),
                "forbidden_claims": forbidden,
            },
            "workflow": {
                "steps": workflow.get("steps") or self._default_steps(self.infer_question_types(intent)),
                "required_modules": selected_modules,
            },
            "parameters": intent.get("analysis_parameters", {}),
            "quality_gates": {
                "fail_closed": True,
                "require_session_info": True,
                "require_source_maps": True,
                "require_claim_boundary": True,
                "require_no_personal_paths": True,
                "require_nonempty_marker_tables": True,
                "require_object_hashes": True,
            },
            "outputs": {
                "figures": expected.get("figures", []),
                "tables": expected.get("tables", []),
                "reports": list(dict.fromkeys([
                    *expected.get("reports", []),
                    "evaluation_report",
                    "bioinformatics_quality_report",
                    "evidence_matrix",
                    "figure_storyline",
                    "methods_draft",
                    "results_skeleton",
                ])),
                "figure_plan": [item["figure_id"] for item in figure_plan["figures"]],
            },
        }

    def _figure_plan(self, intent: dict[str, Any], question_types: list[str], selected_modules: list[str]) -> dict[str, Any]:
        figures = list(intent.get("figure_goals", []) or [])
        if not figures:
            figures = [
                {
                    "figure_id": "figure_1",
                    "scientific_message": "Establish the analyzed cohort or molecular landscape and its quality context.",
                    "required_evidence": ["data_qc", "analysis_overview"],
                },
                {
                    "figure_id": "figure_2",
                    "scientific_message": "Present the primary discovery with its statistical unit and claim boundary.",
                    "required_evidence": ["primary_result_table", "source_map", "quality_report"],
                },
            ]
        return {
            "schema_version": "figure_plan.v1",
            "project_id": intent["project_id"],
            "story_first": True,
            "question_types": question_types,
            "figures": [
                {
                    **figure,
                    "required_modules": figure.get("required_modules", selected_modules),
                    "claim_boundary": figure.get("claim_boundary", intent["claim_boundary"]),
                }
                for figure in figures
            ],
            "forbidden_shortcuts": [
                "do not infer biology from UMAP geometry alone",
                "do not place enrichment before a reviewed ranked-gene result",
                "do not present communication or network inference as mechanism proof",
            ],
        }

    @staticmethod
    def _figure_plan_markdown(figure_plan: dict[str, Any]) -> str:
        lines = ["# Figure Plan", "", "The figure plan is evidence-first and inherits the project claim boundary.", ""]
        for figure in figure_plan["figures"]:
            lines.extend([
                f"## {figure['figure_id']}",
                "",
                f"Scientific message: {figure.get('scientific_message', '')}",
                f"Required evidence: {', '.join(figure.get('required_evidence', []))}",
                f"Required modules: {', '.join(figure.get('required_modules', [])) or 'not yet executable'}",
                f"Claim boundary: {figure.get('claim_boundary', '')}",
                "",
            ])
        return "\n".join(lines)

    def _missing_information(self, intent: dict[str, Any], question_types: list[str]) -> list[dict[str, str]]:
        data = intent.get("data") or {}
        missing = []
        input_path = self.project_root / str(data.get("input_path", ""))
        if not input_path.exists():
            missing.append({"field": "data.input_path", "severity": "blocking", "reason": "data path does not exist in the project root"})
        if "disease_group_comparison" in question_types and normalize_modality(str(data.get("modality", ""))) == "single_cell":
            if not data.get("sample_id_column"):
                missing.append({"field": "data.sample_id_column", "severity": "blocking_for_inference", "reason": "required for replicate-aware pseudobulk"})
            if data.get("biological_replicates") not in {True, "true", "documented"}:
                missing.append({"field": "data.biological_replicates", "severity": "blocking_for_inference", "reason": "FindMarkers remains exploratory without biological replicates"})
        return missing

    @staticmethod
    def _facts(intent: dict[str, Any]) -> list[dict[str, Any]]:
        data = intent.get("data") or {}
        return [
            {"field": "project_goal", "value": intent.get("project_goal")},
            {"field": "data.modality", "value": normalize_modality(str(data.get("modality", "")))},
            {"field": "data.dataset_id", "value": data.get("dataset_id")},
            {"field": "claim_boundary", "value": intent.get("claim_boundary")},
        ]

    @staticmethod
    def _assumptions(intent: dict[str, Any]) -> list[str]:
        assumptions = list(intent.get("assumptions", []) or [])
        if not assumptions:
            assumptions.append("input data will be immutable and registered before real execution")
        return assumptions

    @staticmethod
    def _decisions(decisions: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return [
            {
                "method_id": item["method_id"],
                "decision": item["decision"],
                "statistical_unit": item["statistical_unit"],
                "reason": item["solves"][0] if item["solves"] else "method knowledge match",
            }
            for item in decisions
        ]

    @staticmethod
    def _recommended_phases(question_types: list[str]) -> list[dict[str, Any]]:
        phases = [
            {"phase": 1, "name": "data_and_design_audit", "purpose": "freeze data, metadata, statistical unit, and claim boundary"},
            {"phase": 2, "name": "primary_analysis", "purpose": "run the strongest currently executable method for the primary question"},
        ]
        if "pathway_analysis" in question_types:
            phases.append({"phase": 3, "name": "pathway_interpretation", "purpose": "use a reviewed ranked-gene statistic with database provenance"})
        if any(item in question_types for item in ("network_analysis", "communication_analysis")):
            phases.append({"phase": 4, "name": "hypothesis_generation", "purpose": "generate secondary network hypotheses without causal overclaim"})
        phases.append({"phase": len(phases) + 1, "name": "evidence_and_writing", "purpose": "fail-closed QA, source maps, figure story, and evidence-bound manuscript packet"})
        return phases

    @staticmethod
    def _default_steps(question_types: list[str]) -> list[str]:
        steps = ["data_audit", "primary_analysis"]
        if "subcluster_refinement" in question_types:
            steps.extend(["subcluster_reanalysis", "subcluster_marker_detection", "program_scoring"])
        if "pathway_analysis" in question_types:
            steps.append("ranked_gene_enrichment")
        steps.extend(["figure_generation", "qa_fail_closed", "manuscript_pack"])
        return list(dict.fromkeys(steps))
