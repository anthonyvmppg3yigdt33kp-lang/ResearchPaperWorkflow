"""Method-block extraction for reviewed R/Python literature code sources."""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from paper_workflow.bioinformatics.method_depersonalizer import (
    find_object_terms,
    find_project_terms,
    parameterization_plan,
)


CALL_SPECS: dict[str, dict[str, Any]] = {
    "FindMarkers": {"family": "seurat_findmarkers_de", "package": "Seurat", "module": "single_cell.seurat_findmarkers_group_de"},
    "FindAllMarkers": {"family": "seurat_marker_discovery", "package": "Seurat", "module": "single_cell.seurat_findmarkers_group_de"},
    "FindConservedMarkers": {"family": "seurat_conserved_marker_discovery", "package": "Seurat", "module": "single_cell.seurat_findmarkers_group_de"},
    "NormalizeData": {"family": "seurat_preprocessing", "package": "Seurat", "module": "single_cell.seurat_qc"},
    "ScaleData": {"family": "seurat_preprocessing", "package": "Seurat", "module": "single_cell.seurat_qc"},
    "RunPCA": {"family": "seurat_dimensionality_reduction", "package": "Seurat", "module": "single_cell.seurat_clustering_umap"},
    "RunUMAP": {"family": "seurat_dimensionality_reduction", "package": "Seurat", "module": "single_cell.seurat_clustering_umap"},
    "FindNeighbors": {"family": "seurat_clustering", "package": "Seurat", "module": "single_cell.seurat_clustering_umap"},
    "FindClusters": {"family": "seurat_clustering", "package": "Seurat", "module": "single_cell.seurat_clustering_umap"},
    "FeaturePlot": {"family": "seurat_feature_plot", "package": "Seurat", "module": "single_cell.marker_feature_plot"},
    "VlnPlot": {"family": "seurat_qc_plot", "package": "Seurat", "module": "single_cell.marker_feature_plot"},
    "DotPlot": {"family": "seurat_marker_plot", "package": "Seurat", "module": "single_cell.marker_feature_plot"},
    "DoHeatmap": {"family": "seurat_heatmap", "package": "Seurat", "module": "single_cell.marker_feature_plot"},
    "DGEList": {"family": "limma_voom_de", "package": "edgeR", "module": "bulk_rnaseq.limma_voom_de_real"},
    "calcNormFactors": {"family": "limma_voom_de", "package": "edgeR", "module": "bulk_rnaseq.limma_voom_de_real"},
    "model.matrix": {"family": "limma_voom_de", "package": "stats", "module": "bulk_rnaseq.limma_voom_de_real"},
    "voom": {"family": "limma_voom_de", "package": "limma", "module": "bulk_rnaseq.limma_voom_de_real"},
    "lmFit": {"family": "limma_voom_de", "package": "limma", "module": "bulk_rnaseq.limma_voom_de_real"},
    "contrasts.fit": {"family": "limma_voom_de", "package": "limma", "module": "bulk_rnaseq.limma_voom_de_real"},
    "eBayes": {"family": "limma_voom_de", "package": "limma", "module": "bulk_rnaseq.limma_voom_de_real"},
    "topTable": {"family": "limma_voom_de", "package": "limma", "module": "bulk_rnaseq.limma_voom_de_real"},
    "DESeqDataSetFromMatrix": {"family": "deseq2_de", "package": "DESeq2", "module": "bulk_rnaseq.deseq2_de"},
    "DESeq": {"family": "deseq2_de", "package": "DESeq2", "module": "bulk_rnaseq.deseq2_de"},
    "results": {"family": "deseq2_de", "package": "DESeq2", "module": "bulk_rnaseq.deseq2_de"},
    "lfcShrink": {"family": "deseq2_de", "package": "DESeq2", "module": "bulk_rnaseq.deseq2_de"},
    "enrichGO": {"family": "enrichment", "package": "clusterProfiler", "module": "bulk_rnaseq.fgsea_enrichment"},
    "enrichKEGG": {"family": "enrichment", "package": "clusterProfiler", "module": "bulk_rnaseq.fgsea_enrichment"},
    "compareCluster": {"family": "enrichment", "package": "clusterProfiler", "module": "bulk_rnaseq.fgsea_enrichment"},
    "enricher": {"family": "enrichment", "package": "clusterProfiler", "module": "bulk_rnaseq.fgsea_enrichment"},
    "GSEA": {"family": "enrichment", "package": "clusterProfiler", "module": "bulk_rnaseq.fgsea_enrichment"},
    "fgsea": {"family": "enrichment", "package": "fgsea", "module": "bulk_rnaseq.fgsea_enrichment"},
    "EnhancedVolcano": {"family": "volcano_plot", "package": "EnhancedVolcano", "module": "general.plotting"},
    "ggplot": {"family": "plotting", "package": "ggplot2", "module": "general.plotting"},
    "wilcox.test": {"family": "percent_expression_summary", "package": "stats", "module": "single_cell.percent_composition_stats"},
    "CellChat": {"family": "communication_network", "package": "CellChat", "module": "single_cell.cellchat_communication"},
    "NicheNet": {"family": "communication_network", "package": "nichenetr", "module": "single_cell.nichenet_ligand_target"},
    "AUCell": {"family": "regulatory_network", "package": "AUCell", "module": "single_cell.scenic_adapter"},
    "SCENIC": {"family": "regulatory_network", "package": "SCENIC", "module": "single_cell.scenic_adapter"},
}

FILENAME_HINTS = {
    "dea": ("differential_expression_script", "bulk_rnaseq.differential_expression_postprocess"),
    "pct": ("percent_expression_summary", "single_cell.percent_composition_stats"),
    "clinical": ("clinical_plot", "general.clinical_plot"),
    "plot": ("plotting", "general.plotting"),
}


@dataclass(frozen=True)
class MethodBlock:
    block_id: str
    source_file: str
    line_start: int
    line_end: int
    language: str
    method_family: str
    detected_calls: list[str]
    packages: list[str]
    inferred_inputs: list[str]
    inferred_outputs: list[str]
    hardcoded_terms: list[str]
    disease_or_project_terms: list[str]
    object_terms: list[str]
    parameterization_plan: dict[str, Any]
    candidate_module_family: str
    reviewer_risk: list[str]
    claim_boundary: str
    status: str = "requires_human_review"

    def to_dict(self) -> dict[str, Any]:
        return {
            "block_id": self.block_id,
            "source_file": self.source_file,
            "line_start": self.line_start,
            "line_end": self.line_end,
            "language": self.language,
            "method_family": self.method_family,
            "detected_calls": self.detected_calls,
            "packages": self.packages,
            "inferred_inputs": self.inferred_inputs,
            "inferred_outputs": self.inferred_outputs,
            "hardcoded_terms": self.hardcoded_terms,
            "disease_or_project_terms": self.disease_or_project_terms,
            "object_terms": self.object_terms,
            "parameterization_plan": self.parameterization_plan,
            "candidate_module_family": self.candidate_module_family,
            "reviewer_risk": self.reviewer_risk,
            "claim_boundary": self.claim_boundary,
            "status": self.status,
        }


def extract_method_blocks(source_dir: Path, parsed_scripts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Extract method blocks from retained scripts listed in parsed_source_index."""
    blocks: list[MethodBlock] = []
    for script in parsed_scripts:
        rel = str(script.get("path", ""))
        language = str(script.get("language", "")).lower()
        if language not in {"r", "python"}:
            continue
        path = source_dir / rel
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        blocks.extend(_extract_from_text(rel.replace("\\", "/"), text, language))
    return [block.to_dict() for block in blocks]


def _extract_from_text(source_file: str, text: str, language: str) -> list[MethodBlock]:
    lines = text.splitlines()
    blocks = []
    for idx, line in enumerate(lines, start=1):
        calls = _calls_on_line(line)
        if not calls:
            continue
        line_start = max(1, idx - 3)
        line_end = min(len(lines), idx + 3)
        block_text = "\n".join(lines[line_start - 1:line_end])
        blocks.append(_make_block(source_file, language, line_start, line_end, calls, block_text))
    hint = _filename_hint(source_file)
    if hint and not any(block.method_family == hint[0] for block in blocks):
        line_start = 1
        line_end = min(len(lines), 25) if lines else 1
        block_text = "\n".join(lines[line_start - 1:line_end])
        blocks.append(_make_block(source_file, language, line_start, line_end, [], block_text, family_hint=hint[0], module_hint=hint[1]))
    return _deduplicate_blocks(blocks)


def _calls_on_line(line: str) -> list[str]:
    calls = []
    for call in CALL_SPECS:
        pattern = rf"(?<![A-Za-z0-9_.])(?:[A-Za-z0-9_.]+::)?{re.escape(call)}\s*\("
        if re.search(pattern, line):
            calls.append(call)
    return calls


def _make_block(
    source_file: str,
    language: str,
    line_start: int,
    line_end: int,
    calls: list[str],
    block_text: str,
    *,
    family_hint: str = "",
    module_hint: str = "",
) -> MethodBlock:
    specs = [CALL_SPECS[call] for call in calls if call in CALL_SPECS]
    family = family_hint or _majority([str(spec["family"]) for spec in specs]) or "script_level_method"
    packages = sorted({str(spec["package"]) for spec in specs if spec.get("package")})
    module_family = module_hint or _majority([str(spec["module"]) for spec in specs]) or "external.reviewed_method"
    project_terms = find_project_terms(block_text)
    object_terms = find_object_terms(block_text)
    block_id = _block_id(source_file, family, line_start, calls)
    return MethodBlock(
        block_id=block_id,
        source_file=source_file,
        line_start=line_start,
        line_end=line_end,
        language=language,
        method_family=family,
        detected_calls=sorted(set(calls)),
        packages=packages,
        inferred_inputs=_inferred_inputs(family),
        inferred_outputs=_inferred_outputs(family),
        hardcoded_terms=project_terms,
        disease_or_project_terms=project_terms,
        object_terms=object_terms,
        parameterization_plan=parameterization_plan(method_family=family, hardcoded_terms=project_terms, object_terms=object_terms),
        candidate_module_family=module_family,
        reviewer_risk=_reviewer_risk(family),
        claim_boundary=_claim_boundary(family),
    )


def _block_id(source_file: str, family: str, line_start: int, calls: list[str]) -> str:
    stem = re.sub(r"[^A-Za-z0-9_]+", "_", Path(source_file).stem).strip("_").lower() or "script"
    call_token = "_".join(calls[:2]).lower() if calls else family
    digest = hashlib.sha1(f"{source_file}:{line_start}:{call_token}".encode("utf-8")).hexdigest()[:8]
    return f"{stem}__{family}__L{line_start}__{digest}"


def _filename_hint(source_file: str) -> tuple[str, str] | None:
    lower = Path(source_file).name.lower()
    for token, hint in FILENAME_HINTS.items():
        if token in lower:
            return hint
    return None


def _majority(values: list[str]) -> str:
    if not values:
        return ""
    counts = {value: values.count(value) for value in set(values)}
    return sorted(counts, key=lambda item: (-counts[item], item))[0]


def _deduplicate_blocks(blocks: list[MethodBlock]) -> list[MethodBlock]:
    seen: set[tuple[str, int, str]] = set()
    unique = []
    for block in blocks:
        key = (block.source_file, block.line_start, ",".join(block.detected_calls))
        if key in seen:
            continue
        seen.add(key)
        unique.append(block)
    return unique


def _inferred_inputs(family: str) -> list[str]:
    if "findmarkers" in family:
        return ["seurat_object", "group_column", "ident_1", "ident_2", "optional_subset"]
    if "differential_expression" in family:
        return ["differential_expression_tables", "contrast_metadata", "expression_percent_tables"]
    if "percent_expression" in family:
        return ["cell_metadata", "sample_metadata", "group_column", "cell_type_column"]
    if "limma" in family:
        return ["count_matrix", "sample_metadata", "condition_column", "contrast"]
    if "deseq2" in family:
        return ["count_matrix", "sample_metadata", "design_formula", "contrast"]
    if "enrichment" in family:
        return ["ranked_gene_table", "gene_sets", "gene_universe"]
    if "plot" in family or "visual" in family:
        return ["input_object", "features_or_grouping", "plot_parameters"]
    return ["input_object", "metadata", "parameters"]


def _inferred_outputs(family: str) -> list[str]:
    if "findmarkers" in family:
        return ["differential_expression_table", "volcano_plot", "source_maps"]
    if "differential_expression" in family:
        return ["curated_differential_expression_table", "ranked_gene_table", "enrichment_inputs", "source_maps"]
    if "percent_expression" in family:
        return ["composition_summary_table", "composition_statistical_test_table", "composition_plot"]
    if "limma" in family or "deseq2" in family:
        return ["differential_expression_table", "ranked_gene_statistic", "volcano_plot", "source_maps"]
    if "enrichment" in family:
        return ["enrichment_table", "enrichment_plot", "database_provenance"]
    if "plot" in family or "visual" in family:
        return ["figure", "figure_source_map"]
    return ["method_artifacts", "provenance_record"]


def _reviewer_risk(family: str) -> list[str]:
    if "findmarkers" in family:
        return ["cell-level tests are exploratory for disease contrasts unless replicate-aware inference is documented"]
    if "differential_expression" in family:
        return ["imported differential-expression post-processing depends on upstream contrast design, replicate unit, and FDR provenance"]
    if "percent_expression" in family:
        return ["cell-composition percentages require sample-level grouping and should not treat cells as independent patients"]
    if "limma" in family or "deseq2" in family:
        return ["sample metadata, contrast coding, covariates, and replicate units require human review"]
    if "enrichment" in family:
        return ["enrichment depends on ranked statistic, gene universe, and database version"]
    if "communication" in family or "network" in family:
        return ["network or communication inference is hypothesis-generating and does not prove mechanism"]
    return ["external literature code requires license, provenance, and parameter review before adaptation"]


def _claim_boundary(family: str) -> str:
    if "findmarkers" in family:
        return "Cell-level marker/differential expression is exploratory unless biological replicate-aware inference is documented."
    if "differential_expression" in family:
        return "Imported differential-expression summaries require upstream design and replicate provenance before manuscript claims."
    if "percent_expression" in family:
        return "Cell-composition summaries are descriptive unless sample-level statistical design is documented."
    if "limma" in family or "deseq2" in family:
        return "Differential expression is association evidence only and depends on valid sample-level design."
    if "enrichment" in family:
        return "Pathway enrichment is interpretive and depends on ranked genes, universe, and database version."
    if "communication" in family or "network" in family:
        return "Communication or regulatory-network inference is hypothesis-generating until validated."
    return "Reviewed external code block; no manuscript claim until adapted module tests and provenance review pass."
