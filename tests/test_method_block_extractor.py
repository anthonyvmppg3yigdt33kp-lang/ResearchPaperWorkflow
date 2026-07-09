from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from paper_workflow.bioinformatics.method_block_extractor import extract_method_blocks


def test_method_block_extractor_detects_r_method_families(tmp_path: Path):
    source_dir = tmp_path / "external"
    original = source_dir / "original"
    original.mkdir(parents=True)
    script = original / "DEA_LUAD_vs_LUSC.R"
    script.write_text(
        "\n".join(
            [
                "library(Seurat)",
                "markers <- FindMarkers(obj, ident.1 = 'LUAD', ident.2 = 'LUSC')",
                "dge <- DGEList(counts)",
                "v <- voom(dge, design)",
                "fit <- eBayes(lmFit(v, design))",
                "ego <- clusterProfiler::enrichGO(genes)",
                "FeaturePlot(obj, features = c('MS4A1'))",
            ]
        ),
        encoding="utf-8",
    )
    parsed = [{"path": "original/DEA_LUAD_vs_LUSC.R", "language": "r"}]

    blocks = extract_method_blocks(source_dir, parsed)
    families = {block["method_family"] for block in blocks}
    calls = {call for block in blocks for call in block["detected_calls"]}

    assert "seurat_findmarkers_de" in families
    assert "limma_voom_de" in families
    assert "enrichment" in families
    assert {"FindMarkers", "DGEList", "voom", "enrichGO", "FeaturePlot"} <= calls
    assert any("LUAD" in block["disease_or_project_terms"] for block in blocks)
    assert all(block["status"] == "requires_human_review" for block in blocks)


def test_method_block_extractor_detects_literature_dea_postprocessing(tmp_path: Path):
    source_dir = tmp_path / "external"
    original = source_dir / "original"
    original.mkdir(parents=True)
    dea = original / "DEA_TvsBH.R"
    dea.write_text(
        "\n".join(
                [
                    "all_files <- list.files('~/Desktop/Lung project/DEA/TvsBH', pattern = '.csv')",
                    "group_label <- 'tumour'",
                    "sig <- data %>% filter(abs(log2FoldChange) > 1 & padj <= 0.05)",
                "temp <- compareCluster(genes~group, data = sig, fun = 'enrichGO')",
                "react <- enricher(gene = sig$genes, TERM2GENE = REAC_DB)",
                "EnhancedVolcano(sig, x = 'log2FoldChange', y = 'padj')",
                "ggplot(sig, aes(x = log2FoldChange, y = -log10(padj))) + geom_point()",
            ]
        ),
        encoding="utf-8",
    )
    pct = original / "Pct_stats_new.R"
    pct.write_text(
        "\n".join(
            [
                "tumour_pct <- meta %>% mutate(pct_patient = n / total)",
                "stat_res <- wilcox.test(data = tumour_pct, pct_patient ~ group)",
            ]
        ),
        encoding="utf-8",
    )
    parsed = [
        {"path": "original/DEA_TvsBH.R", "language": "r"},
        {"path": "original/Pct_stats_new.R", "language": "r"},
    ]

    blocks = extract_method_blocks(source_dir, parsed)
    families = {block["method_family"] for block in blocks}
    calls = {call for block in blocks for call in block["detected_calls"]}

    assert "differential_expression_script" in families
    assert "percent_expression_summary" in families
    assert "enrichment" in families
    assert "plotting" in families
    assert {"compareCluster", "enricher", "EnhancedVolcano", "ggplot", "wilcox.test"} <= calls
    assert any("Tumour" in block["disease_or_project_terms"] or "tumour" in block["disease_or_project_terms"] for block in blocks)
