#!/usr/bin/env Rscript

# Parameterized wrapper around the official Seurat PBMC3K guided clustering workflow.
# It is intended for workflow validation and tutorial-fixture execution, not for
# project-specific disease inference.

args <- commandArgs(trailingOnly = TRUE)

get_arg <- function(flag, default = "") {
  idx <- which(args == flag)
  if (length(idx) == 0 || idx[length(idx)] == length(args)) {
    return(default)
  }
  args[idx[length(idx)] + 1]
}

input_dir <- get_arg("--input")
reported_input_dir <- input_dir
out_dir <- get_arg("--out", "seurat_pbmc3k_basic_out")
run_id <- get_arg("--run-id", "seurat_pbmc3k_basic")
markers_arg <- get_arg("--markers", "MS4A1,GNLY,CD3E,CD14,FCER1A,FCGR3A,LYZ,PPBP,CD8A")
min_features <- as.numeric(get_arg("--min-features", "200"))
max_features <- as.numeric(get_arg("--max-features", "2500"))
max_mt <- as.numeric(get_arg("--max-mt", "5"))
npcs <- as.integer(get_arg("--npcs", "10"))
resolution <- as.numeric(get_arg("--resolution", "0.5"))

if (!nzchar(input_dir)) {
  stop("--input is required and must point to a 10X matrix directory or a parent containing filtered_gene_bc_matrices/hg19")
}

required <- c("Seurat", "Matrix", "ggplot2")
missing <- required[!vapply(required, requireNamespace, quietly = TRUE, FUN.VALUE = logical(1))]
if (length(missing) > 0) {
  stop(paste("Missing required R packages:", paste(missing, collapse = ", ")))
}

suppressPackageStartupMessages({
  library(Seurat)
  library(ggplot2)
})

set.seed(20260708)

dir.create(out_dir, recursive = TRUE, showWarnings = FALSE)
dir.create(file.path(out_dir, "qc"), showWarnings = FALSE)
dir.create(file.path(out_dir, "tables"), showWarnings = FALSE)
dir.create(file.path(out_dir, "figures"), showWarnings = FALSE)
dir.create(file.path(out_dir, "objects"), showWarnings = FALSE)
dir.create(file.path(out_dir, "logs"), showWarnings = FALSE)

find_10x_dir <- function(path) {
  path <- normalizePath(path, winslash = "/", mustWork = TRUE)
  candidates <- c(
    path,
    file.path(path, "filtered_gene_bc_matrices", "hg19"),
    file.path(path, "hg19")
  )
  for (candidate in candidates) {
    if (file.exists(file.path(candidate, "matrix.mtx")) ||
        file.exists(file.path(candidate, "matrix.mtx.gz"))) {
      return(candidate)
    }
  }
  stop(paste("No 10X matrix.mtx(.gz) found under", path))
}

write_yaml_lines <- function(path, lines) {
  writeLines(lines, con = path, useBytes = TRUE)
}

save_plot <- function(plot, path, width = 1100, height = 800, res = 140) {
  grDevices::png(path, width = width, height = height, res = res)
  print(plot)
  grDevices::dev.off()
}

data_dir <- find_10x_dir(input_dir)
pbmc_data <- Read10X(data.dir = data_dir)
pbmc <- CreateSeuratObject(counts = pbmc_data, project = "pbmc3k", min.cells = 3, min.features = 200)
initial_cells <- ncol(pbmc)
initial_features <- nrow(pbmc)
pbmc[["percent.mt"]] <- PercentageFeatureSet(pbmc, pattern = "^MT-")

qc_metrics_path <- file.path(out_dir, "qc", "qc_metrics.csv")
utils::write.csv(pbmc@meta.data, qc_metrics_path, quote = TRUE)

qc_plot <- VlnPlot(pbmc, features = c("nFeature_RNA", "nCount_RNA", "percent.mt"), ncol = 3, pt.size = 0.1)
save_plot(qc_plot, file.path(out_dir, "figures", "qc_violin.png"), width = 1300, height = 600)

pbmc <- subset(pbmc, subset = nFeature_RNA > min_features & nFeature_RNA < max_features & percent.mt < max_mt)
filtered_cells <- ncol(pbmc)

retention <- data.frame(
  run_id = run_id,
  input_dir = reported_input_dir,
  initial_cells = initial_cells,
  filtered_cells = filtered_cells,
  retained_fraction = filtered_cells / max(initial_cells, 1),
  initial_features = initial_features,
  min_features = min_features,
  max_features = max_features,
  max_mt = max_mt
)
utils::write.csv(retention, file.path(out_dir, "qc", "cell_retention.csv"), row.names = FALSE, quote = TRUE)

pbmc <- NormalizeData(pbmc, normalization.method = "LogNormalize", scale.factor = 10000, verbose = FALSE)
pbmc <- FindVariableFeatures(pbmc, selection.method = "vst", nfeatures = 2000, verbose = FALSE)
pbmc <- ScaleData(pbmc, features = rownames(pbmc), verbose = FALSE)
pbmc <- RunPCA(pbmc, features = VariableFeatures(object = pbmc), verbose = FALSE)
pbmc <- FindNeighbors(pbmc, dims = 1:npcs, verbose = FALSE)
pbmc <- FindClusters(pbmc, resolution = resolution, verbose = FALSE)
pbmc <- RunUMAP(pbmc, dims = 1:npcs, verbose = FALSE, seed.use = 20260708)

cluster_counts <- as.data.frame(table(cluster = as.character(Idents(pbmc))))
names(cluster_counts) <- c("cluster", "n_cells")
utils::write.csv(cluster_counts, file.path(out_dir, "tables", "cluster_counts.csv"), row.names = FALSE, quote = TRUE)

umap_plot <- DimPlot(pbmc, reduction = "umap", label = TRUE) + NoLegend()
save_plot(umap_plot, file.path(out_dir, "figures", "umap_clusters.png"), width = 1000, height = 800)

markers <- trimws(unlist(strsplit(markers_arg, ",")))
markers <- markers[nzchar(markers)]
present_markers <- intersect(markers, rownames(pbmc))
utils::write.csv(
  data.frame(marker = markers, present = markers %in% present_markers),
  file.path(out_dir, "tables", "marker_presence.csv"),
  row.names = FALSE,
  quote = TRUE
)

if (length(present_markers) > 0) {
  feature_plot <- FeaturePlot(pbmc, features = present_markers, ncol = 3)
  save_plot(feature_plot, file.path(out_dir, "figures", "feature_plot_markers.png"), width = 1300, height = 1000)
}

saveRDS(pbmc, file.path(out_dir, "objects", "pbmc3k_seurat_basic.rds"))
capture.output(sessionInfo(), file = file.path(out_dir, "logs", "sessionInfo.txt"))

write_yaml_lines(
  file.path(out_dir, "figure_source_map.yaml"),
  c(
    "schema_version: seurat_pbmc3k_source_map.v1",
    "figures:",
    "  - figure_id: qc_violin",
    "    path: figures/qc_violin.png",
    "    source_data: qc/qc_metrics.csv",
    "    script: code_library/modules/single_cell/seurat_pbmc3k_basic/main.R",
    "    method: Seurat QC violin plots for nFeature_RNA, nCount_RNA, percent.mt",
    "    statistical_unit: cell",
    "    claim_boundary: tutorial workflow QC only",
    "  - figure_id: umap_clusters",
    "    path: figures/umap_clusters.png",
    "    source_data: objects/pbmc3k_seurat_basic.rds",
    "    script: code_library/modules/single_cell/seurat_pbmc3k_basic/main.R",
    "    method: Seurat PCA-neighbor-cluster-UMAP visualization",
    "    statistical_unit: cell",
    "    claim_boundary: visualization-only exploratory structure",
    "  - figure_id: feature_plot_markers",
    "    path: figures/feature_plot_markers.png",
    "    source_data: objects/pbmc3k_seurat_basic.rds",
    "    script: code_library/modules/single_cell/seurat_pbmc3k_basic/main.R",
    "    method: Seurat FeaturePlot marker visualization",
    "    statistical_unit: cell",
    "    claim_boundary: marker display only"
  )
)

write_yaml_lines(
  file.path(out_dir, "table_source_map.yaml"),
  c(
    "schema_version: seurat_pbmc3k_source_map.v1",
    "tables:",
    "  - table_id: qc_metrics",
    "    path: qc/qc_metrics.csv",
    "    source_inputs: 10X matrix directory",
    "    method: CreateSeuratObject metadata and PercentageFeatureSet",
    "    statistical_unit: cell",
    "    claim_boundary: tutorial workflow QC only",
    "  - table_id: cell_retention",
    "    path: qc/cell_retention.csv",
    "    source_inputs: qc/qc_metrics.csv",
    "    method: nFeature_RNA and percent.mt threshold filter",
    "    statistical_unit: cell",
    "    claim_boundary: tutorial fixture filtering summary only",
    "  - table_id: cluster_counts",
    "    path: tables/cluster_counts.csv",
    "    source_inputs: objects/pbmc3k_seurat_basic.rds",
    "    method: table(Idents(pbmc)) after FindClusters",
    "    statistical_unit: cell",
    "    claim_boundary: exploratory tutorial cluster-size summary only"
  )
)

write_yaml_lines(
  file.path(out_dir, "outputs_manifest.yaml"),
  c(
    "schema_version: seurat_pbmc3k_outputs.v1",
    paste0("run_id: ", run_id),
    "status: completed",
    "outputs:",
    "  - qc/qc_metrics.csv",
    "  - qc/cell_retention.csv",
    "  - tables/cluster_counts.csv",
    "  - tables/marker_presence.csv",
    "  - figures/qc_violin.png",
    "  - figures/umap_clusters.png",
    "  - figures/feature_plot_markers.png",
    "  - objects/pbmc3k_seurat_basic.rds",
    "  - logs/sessionInfo.txt"
  )
)

message("Seurat PBMC3K workflow completed: ", out_dir)
