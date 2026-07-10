"""Strategy-level method evaluation for multi-omics analysis planning.

This layer is intentionally explicit: it records the methodological reasoning
that a keyword scorer cannot express, such as pseudobulk DE versus WGCNA,
spatial deconvolution prerequisites, figure-readiness, and sample-size risk.
"""

from __future__ import annotations

from typing import Any

from paper_workflow.bioinformatics.literature_method_advisor import default_method_guidance


class StrategyEvaluator:
    """Evaluate method assets against data readiness and reviewer value."""

    def __init__(self, data_summary: dict[str, Any] | None = None):
        self.data_summary = data_summary or {}

    def evaluate_module(self, module: dict[str, Any], goal: str) -> dict[str, Any]:
        question_type = self.infer_question_type(goal)
        method_family = self.method_family(module)
        guidance = default_method_guidance(question_type)
        modalities = {str(m).lower().replace("-", "_") for m in self.data_summary.get("modalities", []) or []}
        n_samples = self._int(self.data_summary.get("n_samples", 0))
        tags = {str(t).lower() for t in module.get("capability_tags", []) or []}
        step = str(module.get("step", "")).lower()
        maturity = str(module.get("method_maturity", "")).lower()
        validation = str(module.get("validation_status", "")).lower()

        prerequisites: list[str] = []
        risks: list[str] = []
        comparison_notes: list[str] = []
        fit = 0.62
        decision = "candidate"

        if question_type == "cell_type_de":
            if method_family == "pseudobulk_de":
                fit = 0.93
                prerequisites.extend([
                    "validated sample_id-to-cell mapping",
                    "at least two biological replicates per compared group",
                    "declared covariates or documented reason for no covariates",
                ])
                comparison_notes.append("For cell-type-specific group contrasts, pseudobulk DE is preferred over cell-level tests and usually precedes network analysis.")
                if n_samples and n_samples < 4:
                    risks.append("sample count is below the minimum practical replicate threshold for group DE")
                    fit -= 0.25
            elif method_family == "coexpression_network":
                fit = 0.48
                prerequisites.extend(["normalized expression matrix", "sample-level traits", "sufficient sample count"])
                comparison_notes.append("WGCNA is secondary for module-trait structure; it should not replace replicate-aware pseudobulk DE for primary group contrasts.")
                if n_samples and n_samples < 15:
                    risks.append("WGCNA is underpowered for small sample counts; use only as exploratory support")
                    fit -= 0.18
            elif method_family == "cell_level_de_exploratory":
                fit = 0.74
                prerequisites.extend([
                    "reviewed cell identities and group labels",
                    "explicit statement that cells are not independent biological replicates",
                ])
                risks.append("cell-level differential testing is exploratory unless replicate-aware inference is documented")
                comparison_notes.append("Use FindMarkers for marker screening or exploratory cell-state contrasts; prefer sample-level pseudobulk for disease-group inference when biological replicates are available.")
            elif "differential-expression" in tags:
                fit = 0.78
            elif method_family in {"qc", "visualization", "pseudobulk_aggregation"}:
                fit = 0.35
                comparison_notes.append("QC, clustering, and visualization can be prerequisites, but they are not the primary method for cell-type group inference.")
        elif question_type == "bulk_de":
            if method_family == "bulk_de":
                fit = 0.91
                prerequisites.extend(["raw count matrix", "sample metadata", "primary contrast", "replicate and covariate review"])
            elif method_family == "coexpression_network":
                fit = 0.58
                comparison_notes.append("Use WGCNA after DE/QC when the question is module-trait structure rather than a primary contrast.")
        elif question_type == "spatial_deconvolution":
            if method_family == "spatial_deconvolution":
                fit = 0.9
                prerequisites.extend(["spatial expression object", "cell-type reference or reviewed marker signature", "spot/cell-level QC"])
                if "spatial" not in modalities and modalities:
                    risks.append("declared data modalities do not include spatial data")
                    fit -= 0.25
                if "single_cell" not in modalities and "reference" not in " ".join(tags):
                    risks.append("no single-cell/reference modality declared for deconvolution")
                    fit -= 0.15
            elif method_family == "spatial_qc":
                fit = 0.76
                comparison_notes.append("Run spatial QC before deconvolution to avoid interpreting low-quality spots or sections.")
        elif question_type == "annotation":
            if "annotation" in step or "marker" in tags or "feature-plot" in tags:
                fit = 0.82
                prerequisites.extend(["clustered single-cell object", "marker panel or reference atlas", "manual review of ambiguous cell states"])
        elif question_type == "communication":
            if method_family == "communication":
                fit = 0.86
                prerequisites.extend(["validated cell grouping", "reviewed ligand-receptor or ligand-target database", "hypothesis-only claim boundary"])
                risks.append("communication inference cannot prove causal signaling without orthogonal validation")
        elif question_type == "visualization":
            if module.get("figure_outputs"):
                fit = 0.84

        if "dry" in validation or "thin_wrapper" in maturity or "adapter_contract" in maturity:
            risks.append("execution maturity is not publication-grade; require real-data run evidence before manuscript claims")
            fit -= 0.08
        if "validated" in validation or "validated" in maturity:
            fit += 0.08

        fit = max(0.0, min(1.0, fit))
        if risks and fit < 0.55:
            decision = "deprioritize_or_block_until_requirements_met"
        elif risks:
            decision = "candidate_with_requirements"
        elif fit >= 0.85:
            decision = "recommended"

        return {
            "question_type": question_type,
            "method_family": method_family,
            "strategy_fit": round(fit, 3),
            "decision": decision,
            "figure_role": self.figure_role(module, fit, risks),
            "recommended_methods": guidance.get("recommended_methods", []),
            "not_recommended_methods": guidance.get("not_recommended_methods", []),
            "prerequisites": prerequisites,
            "minimum_data_requirements": guidance.get("minimum_data_requirements", []),
            "statistical_unit": guidance.get("statistical_unit", self.data_summary.get("statistical_unit", "not_declared")),
            "risks": risks,
            "reviewer_risk": risks,
            "claim_boundary": module.get("claim_boundary", ""),
            "next_step_plan": guidance.get("next_step_plan", []),
            "comparison_notes": comparison_notes,
            "data_context": {
                "modalities": sorted(modalities),
                "n_samples": n_samples or "not_declared",
                "statistical_unit": self.data_summary.get("statistical_unit", "not_declared"),
            },
        }

    @staticmethod
    def infer_question_type(goal: str) -> str:
        text = goal.lower()
        if any(token in text for token in ["pseudobulk", "cell-type differential", "cell type differential", "celltype differential", "findmarkers", "findallmarkers", "mast", "差异分析", "差异基因", "组间比较", "疾病组", "对照组"]):
            return "cell_type_de"
        if any(token in text for token in ["deseq", "limma", "voom", "edge", "differential", "de ", "contrast", "case", "control"]):
            return "bulk_de"
        if any(token in text for token in ["wgcna", "co-expression", "coexpression", "module-trait", "hub gene", "调控网络", "共表达"]):
            return "network"
        if any(token in text for token in ["deconvolution", "cell fraction", "cell abundance", "rctd", "cell2location", "免疫浸润"]):
            return "spatial_deconvolution"
        if any(token in text for token in ["annotation", "cell type", "cell identity", "marker"]):
            return "annotation"
        if any(token in text for token in ["cellchat", "nichenet", "ligand", "receptor", "communication", "细胞通讯"]):
            return "communication"
        if any(token in text for token in ["go", "kegg", "gsea", "fgsea", "clusterprofiler", "富集分析", "通路分析"]):
            return "enrichment"
        if any(token in text for token in ["figure", "visual", "umap", "plot", "heatmap", "绘图"]):
            return "visualization"
        if any(token in text for token in ["single-cell", "single cell", "scrna", "pbmc"]):
            return "single_cell_preprocessing"
        return "general"

    @staticmethod
    def method_family(module: dict[str, Any]) -> str:
        tags = {str(t).lower() for t in module.get("capability_tags", []) or []}
        step = str(module.get("step", "")).lower()
        if "pseudobulk" in tags or "pseudobulk" in step:
            return "pseudobulk_de" if "deseq" in step or "differential-expression" in tags else "pseudobulk_aggregation"
        if "findmarkers" in step or any("findmarkers" in tag for tag in tags):
            return "cell_level_de_exploratory"
        if "wgcna" in tags or "wgcna" in step:
            return "coexpression_network"
        if "deseq2" in tags or "limma" in tags or "differential-expression" in tags:
            return "bulk_de"
        if "deconvolution" in step or "cell2location" in tags or "rctd" in tags:
            return "spatial_deconvolution"
        if "spatial" in tags and "qc" in tags:
            return "spatial_qc"
        if "cellchat" in tags or "nichenet" in tags or "ligand-receptor" in tags or "ligand-target" in tags:
            return "communication"
        if "qc" in tags:
            return "qc"
        if module.get("figure_outputs"):
            return "visualization"
        return str(module.get("step", "method_asset"))

    @staticmethod
    def figure_role(module: dict[str, Any], fit: float, risks: list[str]) -> str:
        outputs = module.get("figure_outputs", []) or []
        if not outputs:
            return "table_or_intermediate_asset"
        boundary = str(module.get("claim_boundary", "")).lower()
        maturity = str(module.get("method_maturity", "")).lower()
        if risks or "pilot" in maturity or "dry" in maturity or "tutorial" in boundary:
            return "qc_or_supplementary_until_real_data_validation"
        if fit >= 0.85 and any(token in boundary for token in ["association", "publication", "validated"]):
            return "main_figure_candidate_after_source_map_review"
        return "secondary_figure_candidate"

    @staticmethod
    def _int(value: Any) -> int:
        try:
            return int(value)
        except (TypeError, ValueError):
            return 0
