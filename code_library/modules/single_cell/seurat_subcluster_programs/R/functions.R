SUBCLUSTER_CLAIM_BOUNDARY <- "PBMC3K workflow-test exploratory T-cell-like subcluster program only; no disease, clinical, or causal claim."

get_arg <- function(args, flag, default = "") {
  idx <- which(args == flag)
  if (length(idx) == 0 || idx[length(idx)] == length(args)) {
    return(default)
  }
  args[idx[length(idx)] + 1]
}

has_flag <- function(args, flag) {
  flag %in% args
}

truthy <- function(value) {
  tolower(as.character(value)) %in% c("true", "t", "1", "yes", "y")
}

split_csv <- function(value) {
  items <- trimws(unlist(strsplit(as.character(value), ",")))
  items[nzchar(items)]
}

prepare_dirs <- function(output_dir) {
  for (subdir in c("tables", "figures", "objects", "logs", "qc")) {
    dir.create(file.path(output_dir, subdir), recursive = TRUE, showWarnings = FALSE)
  }
}

write_yaml_lines <- function(path, lines) {
  dir.create(dirname(path), recursive = TRUE, showWarnings = FALSE)
  writeLines(lines, con = path, useBytes = TRUE)
}

write_source_maps <- function(output_dir) {
  write_yaml_lines(
    file.path(output_dir, "figure_source_map.yaml"),
    c(
      "schema_version: seurat_subcluster_programs_source_map.v1",
      "figures:",
      "  - figure_id: tcell_subset_umap",
      "    path: figures/tcell_subset_umap.png",
      "    source_data: objects/subcluster_seurat.rds",
      "    script: code_library/modules/single_cell/seurat_subcluster_programs/main.R",
      "    method: Seurat T-cell-like subset UMAP after marker-driven subsetting",
      "    statistical_unit: cell",
      paste0("    claim_boundary: \"", SUBCLUSTER_CLAIM_BOUNDARY, "\""),
      "  - figure_id: resolution_grid_umap",
      "    path: figures/resolution_grid_umap.png",
      "    source_data: tables/resolution_summary.csv",
      "    script: code_library/modules/single_cell/seurat_subcluster_programs/main.R",
      "    method: Seurat resolution grid clustering summary",
      "    statistical_unit: cell",
      paste0("    claim_boundary: \"", SUBCLUSTER_CLAIM_BOUNDARY, "\""),
      "  - figure_id: subcluster_marker_heatmap",
      "    path: figures/subcluster_marker_heatmap.png",
      "    source_data: tables/subcluster_markers.csv",
      "    script: code_library/modules/single_cell/seurat_subcluster_programs/main.R",
      "    method: top subcluster marker heatmap",
      "    statistical_unit: cell",
      paste0("    claim_boundary: \"", SUBCLUSTER_CLAIM_BOUNDARY, "\""),
      "  - figure_id: program_score_violin",
      "    path: figures/program_score_violin.png",
      "    source_data: tables/program_score_summary.csv",
      "    script: code_library/modules/single_cell/seurat_subcluster_programs/main.R",
      "    method: exploratory program score distribution by subcluster",
      "    statistical_unit: cell",
      paste0("    claim_boundary: \"", SUBCLUSTER_CLAIM_BOUNDARY, "\""),
      "  - figure_id: program_score_dotplot",
      "    path: figures/program_score_dotplot.png",
      "    source_data: tables/program_score_summary.csv",
      "    script: code_library/modules/single_cell/seurat_subcluster_programs/main.R",
      "    method: exploratory program score summary by subcluster",
      "    statistical_unit: cell",
      paste0("    claim_boundary: \"", SUBCLUSTER_CLAIM_BOUNDARY, "\"")
    )
  )
  write_yaml_lines(
    file.path(output_dir, "table_source_map.yaml"),
    c(
      "schema_version: seurat_subcluster_programs_source_map.v1",
      "tables:",
      "  - table_id: subcluster_cell_counts",
      "    path: tables/subcluster_cell_counts.csv",
      "    source_inputs: objects/subcluster_seurat.rds",
      "    method: table(subcluster identities)",
      "    statistical_unit: cell",
      paste0("    claim_boundary: \"", SUBCLUSTER_CLAIM_BOUNDARY, "\""),
      "  - table_id: resolution_summary",
      "    path: tables/resolution_summary.csv",
      "    source_inputs: objects/subcluster_seurat.rds",
      "    method: Seurat FindClusters resolution grid",
      "    statistical_unit: cell",
      paste0("    claim_boundary: \"", SUBCLUSTER_CLAIM_BOUNDARY, "\""),
      "  - table_id: subcluster_markers",
      "    path: tables/subcluster_markers.csv",
      "    source_inputs: objects/subcluster_seurat.rds",
      "    method: Seurat FindAllMarkers standardized marker table",
      "    statistical_unit: cell",
      paste0("    claim_boundary: \"", SUBCLUSTER_CLAIM_BOUNDARY, "\""),
      "  - table_id: program_score_summary",
      "    path: tables/program_score_summary.csv",
      "    source_inputs: objects/subcluster_seurat.rds",
      "    method: AddModuleScore summaries by subcluster",
      "    statistical_unit: cell",
      paste0("    claim_boundary: \"", SUBCLUSTER_CLAIM_BOUNDARY, "\""),
      "  - table_id: marker_program_mapping",
      "    path: tables/marker_program_mapping.csv",
      "    source_inputs: TargetTask program gene sets",
      "    method: declared marker-to-program mapping",
      "    statistical_unit: gene",
      paste0("    claim_boundary: \"", SUBCLUSTER_CLAIM_BOUNDARY, "\"")
    )
  )
}

write_manifests <- function(output_dir, run_id, status, dry_run = FALSE) {
  write_yaml_lines(
    file.path(output_dir, "outputs_manifest.yaml"),
    c(
      "schema_version: seurat_subcluster_programs_outputs.v1",
      paste0("run_id: ", run_id),
      paste0("status: ", status),
      paste0("dry_run: ", tolower(as.character(dry_run))),
      paste0("claim_boundary: \"", SUBCLUSTER_CLAIM_BOUNDARY, "\""),
      "outputs:",
      "  - objects/subcluster_seurat.rds",
      "  - tables/subcluster_cell_counts.csv",
      "  - tables/resolution_summary.csv",
      "  - tables/subcluster_markers.csv",
      "  - tables/program_score_summary.csv",
      "  - tables/marker_program_mapping.csv",
      "  - figures/tcell_subset_umap.png",
      "  - figures/resolution_grid_umap.png",
      "  - figures/subcluster_marker_heatmap.png",
      "  - figures/program_score_violin.png",
      "  - figures/program_score_dotplot.png",
      "  - qc/subcluster_quality_report.yaml",
      "  - logs/sessionInfo.txt",
      "  - figure_source_map.yaml",
      "  - table_source_map.yaml"
    )
  )
  write_yaml_lines(
    file.path(output_dir, "node_manifest.yaml"),
    c(
      "schema_version: method_node_manifest.v1",
      paste0("run_id: ", run_id),
      "module_id: single_cell.seurat_subcluster_programs.v1",
      paste0("status: ", status),
      paste0("dry_run: ", tolower(as.character(dry_run))),
      paste0("claim_boundary: \"", SUBCLUSTER_CLAIM_BOUNDARY, "\"")
    )
  )
}

program_sets <- function() {
  list(
    naive_memory_like = c("IL7R", "CCR7", "TCF7", "LTB"),
    cytotoxic_like = c("NKG7", "GNLY", "PRF1", "GZMB"),
    interferon_like = c("ISG15", "IFIT1", "IFIT3", "MX1"),
    stress_ribosomal_like = c("FOS", "JUN", "RPLP0", "RPS3")
  )
}

write_dry_run <- function(output_dir, run_id) {
  prepare_dirs(output_dir)
  counts <- data.frame(subcluster = c("0", "1", "2"), n_cells = c(120, 95, 80))
  utils::write.csv(counts, file.path(output_dir, "tables", "subcluster_cell_counts.csv"), row.names = FALSE, quote = TRUE)
  res <- data.frame(resolution = c(0.2, 0.4, 0.6, 0.8), n_subclusters = c(2, 3, 3, 4), selected = c(FALSE, TRUE, FALSE, FALSE))
  utils::write.csv(res, file.path(output_dir, "tables", "resolution_summary.csv"), row.names = FALSE, quote = TRUE)
  markers <- data.frame(
    gene = c("IL7R", "CCR7", "NKG7", "GNLY", "ISG15", "FOS"),
    cluster = c("0", "0", "1", "1", "2", "2"),
    p_val = c(0.001, 0.002, 0.003, 0.004, 0.006, 0.01),
    avg_log2FC = c(1.4, 1.1, 1.6, 1.5, 0.9, 0.8),
    pct.1 = c(0.8, 0.7, 0.82, 0.78, 0.5, 0.6),
    pct.2 = c(0.3, 0.28, 0.25, 0.2, 0.2, 0.3),
    p_val_adj = c(0.01, 0.02, 0.03, 0.04, 0.05, 0.06)
  )
  utils::write.csv(markers, file.path(output_dir, "tables", "subcluster_markers.csv"), row.names = FALSE, quote = TRUE)
  programs <- data.frame(
    subcluster = rep(c("0", "1", "2"), each = 4),
    program = rep(names(program_sets()), times = 3),
    mean_score = c(0.8, 0.1, 0.2, 0.3, 0.2, 0.9, 0.1, 0.2, 0.3, 0.2, 0.7, 0.8),
    median_score = c(0.7, 0.1, 0.2, 0.25, 0.2, 0.85, 0.1, 0.2, 0.25, 0.2, 0.65, 0.75),
    n_cells = rep(c(120, 95, 80), each = 4)
  )
  utils::write.csv(programs, file.path(output_dir, "tables", "program_score_summary.csv"), row.names = FALSE, quote = TRUE)
  mapping <- data.frame(program = rep(names(program_sets()), lengths(program_sets())), gene = unlist(program_sets(), use.names = FALSE))
  utils::write.csv(mapping, file.path(output_dir, "tables", "marker_program_mapping.csv"), row.names = FALSE, quote = TRUE)
  for (fig in c("tcell_subset_umap", "resolution_grid_umap", "subcluster_marker_heatmap", "program_score_violin", "program_score_dotplot")) {
    grDevices::png(file.path(output_dir, "figures", paste0(fig, ".png")), width = 900, height = 650)
    plot(1:10, 1:10, pch = 19, main = paste(fig, "dry run"), xlab = "workflow test", ylab = "value")
    grDevices::dev.off()
  }
  saveRDS(list(run_id = run_id, dry_run = TRUE), file.path(output_dir, "objects", "subcluster_seurat.rds"))
  write_yaml_lines(
    file.path(output_dir, "qc", "subcluster_quality_report.yaml"),
    c(
      "schema_version: subcluster_quality_report.v1",
      "status: pass",
      "subset_cells: 295",
      "subcluster_count: 3",
      "marker_table_valid: true",
      "program_scores_valid: true",
      paste0("claim_boundary: \"", SUBCLUSTER_CLAIM_BOUNDARY, "\"")
    )
  )
  writeLines("dry-run sessionInfo placeholder; real execution writes R sessionInfo()", file.path(output_dir, "logs", "sessionInfo.txt"))
  write_source_maps(output_dir)
  write_manifests(output_dir, run_id, "dry_run_completed", dry_run = TRUE)
}

run_seurat_subcluster_programs <- function(
  seurat_object,
  output_dir,
  run_id,
  subset_markers,
  subset_column = NULL,
  subset_idents = NULL,
  resolutions = c(0.2, 0.4, 0.6, 0.8),
  npcs = 10,
  marker_method = "wilcox",
  only_pos = TRUE,
  min_pct = 0.1,
  logfc_threshold = 0.25,
  program_gene_sets = list(),
  seed = 1234
) {
  required <- c("Seurat", "Matrix", "ggplot2")
  missing <- required[!vapply(required, requireNamespace, quietly = TRUE, FUN.VALUE = logical(1))]
  if (length(missing) > 0) {
    stop(paste("Missing required R packages:", paste(missing, collapse = ", ")))
  }
  prepare_dirs(output_dir)
  set.seed(seed)
  obj <- if (is.character(seurat_object)) readRDS(seurat_object) else seurat_object
  metadata <- obj[[]]
  keep <- colnames(obj)
  if (!is.null(subset_column) && nzchar(subset_column) && !is.null(subset_idents) && length(subset_idents) > 0) {
    if (!subset_column %in% colnames(metadata)) {
      stop(paste("subset_column not found in metadata:", subset_column))
    }
    keep <- rownames(metadata)[as.character(metadata[[subset_column]]) %in% as.character(subset_idents)]
  } else {
    present_markers <- intersect(subset_markers, rownames(obj))
    if (length(present_markers) == 0) {
      stop("none of the subset markers are present in the Seurat object")
    }
    expr <- Seurat::GetAssayData(obj, layer = "data")[present_markers, , drop = FALSE]
    keep <- colnames(obj)[Matrix::colSums(expr > 0) > 0]
  }
  if (length(keep) == 0) {
    stop("subset cells is zero; fail-closed before marker comparison")
  }
  sub_obj <- subset(obj, cells = keep)
  sub_obj <- Seurat::FindVariableFeatures(sub_obj, selection.method = "vst", nfeatures = 1500, verbose = FALSE)
  sub_obj <- Seurat::ScaleData(sub_obj, features = rownames(sub_obj), verbose = FALSE)
  sub_obj <- Seurat::RunPCA(sub_obj, features = Seurat::VariableFeatures(sub_obj), npcs = max(npcs), verbose = FALSE)
  sub_obj <- Seurat::FindNeighbors(sub_obj, dims = 1:npcs, verbose = FALSE)
  resolution_rows <- list()
  for (res in resolutions) {
    sub_obj <- Seurat::FindClusters(sub_obj, resolution = res, verbose = FALSE)
    column <- paste0("RNA_snn_res.", res)
    if (!column %in% colnames(sub_obj[[]])) {
      column <- tail(grep("_snn_res\\.", colnames(sub_obj[[]]), value = TRUE), 1)
    }
    n_clusters <- length(unique(as.character(sub_obj[[column]][, 1])))
    resolution_rows[[length(resolution_rows) + 1]] <- data.frame(resolution = res, n_subclusters = n_clusters)
  }
  resolution_summary <- do.call(rbind, resolution_rows)
  selected_idx <- which.max(resolution_summary$n_subclusters)
  selected_resolution <- resolution_summary$resolution[selected_idx]
  sub_obj <- Seurat::FindClusters(sub_obj, resolution = selected_resolution, verbose = FALSE)
  sub_obj <- Seurat::RunUMAP(sub_obj, dims = 1:npcs, verbose = FALSE, seed.use = seed)
  sub_obj$target_subcluster <- as.character(Seurat::Idents(sub_obj))
  resolution_summary$selected <- resolution_summary$resolution == selected_resolution
  utils::write.csv(resolution_summary, file.path(output_dir, "tables", "resolution_summary.csv"), row.names = FALSE, quote = TRUE)
  counts <- as.data.frame(table(subcluster = sub_obj$target_subcluster))
  names(counts) <- c("subcluster", "n_cells")
  utils::write.csv(counts, file.path(output_dir, "tables", "subcluster_cell_counts.csv"), row.names = FALSE, quote = TRUE)
  if (nrow(counts) < 2) {
    write_yaml_lines(
      file.path(output_dir, "qc", "subcluster_quality_report.yaml"),
      c("schema_version: subcluster_quality_report.v1", "status: blocked", "block_reason: fewer than two subclusters")
    )
    stop("fewer than two subclusters; marker comparison blocked")
  }
  markers <- Seurat::FindAllMarkers(sub_obj, test.use = marker_method, only.pos = only_pos, min.pct = min_pct, logfc.threshold = logfc_threshold)
  if (!"gene" %in% colnames(markers)) {
    markers$gene <- rownames(markers)
  }
  if (!"avg_log2FC" %in% colnames(markers) && "avg_logFC" %in% colnames(markers)) {
    markers$avg_log2FC <- markers$avg_logFC
  }
  required_cols <- c("gene", "cluster", "p_val", "avg_log2FC", "pct.1", "pct.2", "p_val_adj")
  for (column in required_cols) {
    if (!column %in% colnames(markers)) {
      markers[[column]] <- NA
    }
  }
  markers <- markers[, required_cols]
  utils::write.csv(markers, file.path(output_dir, "tables", "subcluster_markers.csv"), row.names = FALSE, quote = TRUE)
  if (length(program_gene_sets) == 0) {
    program_gene_sets <- program_sets()
  }
  present_sets <- lapply(program_gene_sets, function(genes) intersect(genes, rownames(sub_obj)))
  present_sets <- present_sets[lengths(present_sets) > 0]
  if (length(present_sets) > 0) {
    sub_obj <- Seurat::AddModuleScore(sub_obj, features = present_sets, name = names(present_sets), seed = seed)
  }
  score_cols <- if (length(present_sets) > 0) {
    grep(paste0("^(", paste(names(present_sets), collapse = "|"), ")"), colnames(sub_obj[[]]), value = TRUE)
  } else {
    character()
  }
  score_rows <- list()
  for (col in score_cols) {
    program <- sub("[0-9]+$", "", col)
    values <- sub_obj[[col]][, 1]
    for (cluster in sort(unique(sub_obj$target_subcluster))) {
      idx <- sub_obj$target_subcluster == cluster
      score_rows[[length(score_rows) + 1]] <- data.frame(
        subcluster = cluster,
        program = program,
        mean_score = mean(values[idx], na.rm = TRUE),
        median_score = stats::median(values[idx], na.rm = TRUE),
        n_cells = sum(idx)
      )
    }
  }
  program_summary <- if (length(score_rows)) do.call(rbind, score_rows) else data.frame(subcluster = character(), program = character(), mean_score = numeric(), median_score = numeric(), n_cells = integer())
  utils::write.csv(program_summary, file.path(output_dir, "tables", "program_score_summary.csv"), row.names = FALSE, quote = TRUE)
  mapping <- data.frame(program = rep(names(program_gene_sets), lengths(program_gene_sets)), gene = unlist(program_gene_sets, use.names = FALSE))
  utils::write.csv(mapping, file.path(output_dir, "tables", "marker_program_mapping.csv"), row.names = FALSE, quote = TRUE)
  grDevices::png(file.path(output_dir, "figures", "tcell_subset_umap.png"), width = 1000, height = 800)
  print(Seurat::DimPlot(sub_obj, reduction = "umap", group.by = "target_subcluster", label = TRUE) + Seurat::NoLegend())
  grDevices::dev.off()
  grDevices::png(file.path(output_dir, "figures", "resolution_grid_umap.png"), width = 900, height = 650)
  plot(resolution_summary$resolution, resolution_summary$n_subclusters, type = "b", xlab = "resolution", ylab = "subclusters", main = "Resolution grid")
  grDevices::dev.off()
  top_markers <- head(markers$gene[!is.na(markers$gene)], 12)
  grDevices::png(file.path(output_dir, "figures", "subcluster_marker_heatmap.png"), width = 1000, height = 800)
  if (length(top_markers) > 1) {
    print(Seurat::DoHeatmap(sub_obj, features = unique(top_markers), group.by = "target_subcluster"))
  } else {
    plot.new(); text(0.5, 0.5, "Insufficient markers for heatmap")
  }
  grDevices::dev.off()
  grDevices::png(file.path(output_dir, "figures", "program_score_violin.png"), width = 1000, height = 800)
  if (length(score_cols) > 0) {
    print(Seurat::VlnPlot(sub_obj, features = score_cols, group.by = "target_subcluster", pt.size = 0))
  } else {
    plot.new(); text(0.5, 0.5, "No program score columns")
  }
  grDevices::dev.off()
  grDevices::png(file.path(output_dir, "figures", "program_score_dotplot.png"), width = 1000, height = 800)
  if (length(unique(mapping$gene)) > 0) {
    print(Seurat::DotPlot(sub_obj, features = unique(intersect(mapping$gene, rownames(sub_obj))), group.by = "target_subcluster"))
  } else {
    plot.new(); text(0.5, 0.5, "No program genes present")
  }
  grDevices::dev.off()
  saveRDS(sub_obj, file.path(output_dir, "objects", "subcluster_seurat.rds"))
  capture.output(sessionInfo(), file = file.path(output_dir, "logs", "sessionInfo.txt"))
  write_yaml_lines(
    file.path(output_dir, "qc", "subcluster_quality_report.yaml"),
    c(
      "schema_version: subcluster_quality_report.v1",
      "status: pass",
      paste0("subset_cells: ", ncol(sub_obj)),
      paste0("subcluster_count: ", nrow(counts)),
      "marker_table_valid: true",
      paste0("program_scores_valid: ", tolower(as.character(!any(is.na(program_summary$mean_score))))),
      paste0("claim_boundary: \"", SUBCLUSTER_CLAIM_BOUNDARY, "\"")
    )
  )
  write_source_maps(output_dir)
  write_manifests(output_dir, run_id, "completed", dry_run = FALSE)
  invisible(sub_obj)
}

run_seurat_subcluster_programs_cli <- function(args) {
  output_dir <- get_arg(args, "--out", "seurat_subcluster_programs_out")
  run_id <- get_arg(args, "--run-id", "seurat_subcluster_programs")
  if (has_flag(args, "--dry-run")) {
    write_dry_run(output_dir, run_id)
    return(invisible(TRUE))
  }
  input <- get_arg(args, "--input")
  if (!nzchar(input)) {
    input <- get_arg(args, "--seurat-rds")
  }
  if (!nzchar(input)) {
    stop("--input <seurat_rds> is required")
  }
  run_seurat_subcluster_programs(
    seurat_object = input,
    output_dir = output_dir,
    run_id = run_id,
    subset_markers = split_csv(get_arg(args, "--subset-markers", "CD3D,CD3E,IL7R,CCR7,S100A4,CD8A,NKG7,GNLY")),
    subset_column = get_arg(args, "--subset-column", ""),
    subset_idents = split_csv(get_arg(args, "--subset-idents", "")),
    resolutions = as.numeric(split_csv(get_arg(args, "--resolutions", "0.2,0.4,0.6,0.8"))),
    npcs = as.integer(get_arg(args, "--npcs", "10")),
    marker_method = get_arg(args, "--marker-method", "wilcox"),
    only_pos = truthy(get_arg(args, "--only-pos", "true")),
    min_pct = as.numeric(get_arg(args, "--min-pct", "0.1")),
    logfc_threshold = as.numeric(get_arg(args, "--logfc-threshold", "0.25")),
    program_gene_sets = program_sets(),
    seed = as.integer(get_arg(args, "--seed", "1234"))
  )
}
