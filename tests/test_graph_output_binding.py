from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from paper_workflow.bioinformatics.analysis_graph import build_graph_from_selected_modules


def test_graph_binds_upstream_outputs_to_downstream_inputs():
    modules = [
        {
            "id": "single_cell.seurat_qc.v1",
            "step": "seurat_qc",
            "input_schema": {"required": [{"name": "input", "type": "seurat_rds"}]},
            "output_schema": {"artifacts": ["objects/seurat_qc.rds"]},
            "output_bindings": {"seurat_rds": "objects/seurat_qc.rds"},
        },
        {
            "id": "single_cell.seurat_clustering_umap.v1",
            "step": "seurat_clustering_umap",
            "input_schema": {"required": [{"name": "input", "type": "seurat_rds"}]},
            "output_schema": {"artifacts": ["objects/seurat_clustered.rds"]},
            "output_bindings": {"seurat_rds": "objects/seurat_clustered.rds"},
            "compatible_upstream_modules": ["single_cell.seurat_qc.v1"],
        },
        {
            "id": "single_cell.seurat_findmarkers_group_de.v1",
            "step": "seurat_findmarkers_group_de",
            "input_schema": {"required": [{"name": "seurat_rds", "type": "seurat_rds"}]},
            "output_schema": {"artifacts": ["tables/findmarkers_results.csv"]},
            "output_bindings": {"ranked_gene_statistic": "tables/findmarkers_results.csv"},
            "compatible_upstream_modules": ["single_cell.seurat_clustering_umap.v1"],
        },
        {
            "id": "bulk_rnaseq.fgsea_enrichment.v1",
            "step": "fgsea_enrichment",
            "input_schema": {"required": ["ranked_gene_statistic"]},
            "output_schema": {"artifacts": ["tables/fgsea_results.csv"]},
            "compatible_upstream_modules": ["single_cell.seurat_findmarkers_group_de.v1"],
        },
    ]

    graph = build_graph_from_selected_modules(
        run_id="graph_binding_20260709_v1",
        goal="QC to clustering to FindMarkers to enrichment",
        selected_modules=modules,
        input_dir="data/input.rds",
    )

    clustering = graph.nodes[1]
    findmarkers = graph.nodes[2]
    enrichment = graph.nodes[3]

    assert clustering.inputs["input"]["binding_source"] == "upstream_output.seurat_qc.seurat_rds"
    assert clustering.inputs["input"]["value"] == "nodes/seurat_qc/objects/seurat_qc.rds"
    assert findmarkers.inputs["seurat_rds"]["binding_source"] == "upstream_output.seurat_clustering_umap.seurat_rds"
    assert "seurat_clustering_umap" in findmarkers.depends_on
    assert enrichment.inputs["ranked_gene_statistic"]["binding_source"] == "upstream_output.seurat_findmarkers_group_de.ranked_gene_statistic"
    assert enrichment.inputs["ranked_gene_statistic"]["status"] == "bound"
