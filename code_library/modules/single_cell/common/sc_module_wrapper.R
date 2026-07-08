#!/usr/bin/env Rscript

get_script_path <- function() {
  args <- commandArgs(trailingOnly = FALSE)
  file_arg <- grep("^--file=", args, value = TRUE)
  if (length(file_arg) > 0) {
    return(normalizePath(sub("^--file=", "", file_arg[[1]]), winslash = "/", mustWork = TRUE))
  }
  normalizePath(getwd(), winslash = "/", mustWork = FALSE)
}

parse_args <- function(args) {
  out <- list(flags = character())
  i <- 1
  while (i <= length(args)) {
    item <- args[[i]]
    if (startsWith(item, "--")) {
      key <- sub("^--", "", item)
      if (i == length(args) || startsWith(args[[i + 1]], "--")) {
        out$flags <- c(out$flags, key)
        out[[key]] <- TRUE
        i <- i + 1
      } else {
        out[[key]] <- args[[i + 1]]
        i <- i + 2
      }
    } else {
      i <- i + 1
    }
  }
  out
}

arg_value <- function(args, key, default = "") {
  value <- args[[key]]
  if (is.null(value) || isTRUE(value)) {
    return(default)
  }
  as.character(value)
}

ensure_dir <- function(path) {
  if (!dir.exists(path)) {
    dir.create(path, recursive = TRUE, showWarnings = FALSE)
  }
  invisible(path)
}

write_lines <- function(path, lines) {
  ensure_dir(dirname(path))
  writeLines(lines, con = path, useBytes = TRUE)
}

csv_write <- function(path, data) {
  ensure_dir(dirname(path))
  utils::write.csv(data, path, row.names = FALSE, quote = TRUE)
}

module_spec <- function(module_id) {
  specs <- list(
    "single_cell.seurat_qc.v1" = list(
      short = "seurat_qc",
      function_name = "seurat_qc",
      method = "Seurat QC filtering by feature counts, UMI counts, and mitochondrial fraction",
      figure_id = "qc_violin",
      figure_path = "figures/qc_violin.png",
      table_id = "cell_retention",
      table_path = "qc/cell_retention.csv",
      object_path = "objects/seurat_qc.rds",
      source_data = "qc/cell_retention.csv",
      unit = "cell",
      claim_boundary = "QC and filtering only; retained cells are analysis inputs, not biological evidence."
    ),
    "single_cell.seurat_integration_harmony.v1" = list(
      short = "seurat_integration_harmony",
      function_name = "seurat_harmony",
      method = "Harmony correction on Seurat PCA embeddings using declared batch variable",
      figure_id = "harmony_embedding",
      figure_path = "figures/harmony_embedding.png",
      table_id = "integration_summary",
      table_path = "tables/integration_summary.csv",
      object_path = "objects/seurat_harmony.rds",
      source_data = "objects/seurat_harmony.rds",
      unit = "cell",
      claim_boundary = "Batch-corrected embedding for exploratory integration; does not prove batch-free biology."
    ),
    "single_cell.seurat_clustering_umap.v1" = list(
      short = "seurat_clustering_umap",
      function_name = "seurat_cluster",
      method = "Seurat PCA, neighbors, clustering, and UMAP visualization",
      figure_id = "umap_clusters",
      figure_path = "figures/umap_clusters.png",
      table_id = "cluster_counts",
      table_path = "tables/cluster_counts.csv",
      object_path = "objects/seurat_clustered.rds",
      source_data = "objects/seurat_clustered.rds",
      unit = "cell",
      claim_boundary = "Cluster visualization is exploratory and requires annotation/validation before inference."
    ),
    "single_cell.marker_feature_plot.v1" = list(
      short = "marker_feature_plot",
      function_name = "plot_feature_nature",
      method = "Marker feature expression overlay on Seurat UMAP coordinates",
      figure_id = "marker_feature_plot",
      figure_path = "figures/marker_feature_plot.png",
      table_id = "marker_presence",
      table_path = "tables/marker_presence.csv",
      object_path = "objects/feature_plot_input.rds",
      source_data = "objects/feature_plot_input.rds",
      unit = "cell",
      claim_boundary = "Marker display only; expression overlays do not establish cell identity or mechanism alone."
    ),
    "single_cell.pseudobulk_aggregate.v1" = list(
      short = "pseudobulk_aggregate",
      function_name = "pseudobulk_aggregate",
      method = "Aggregate single-cell counts by sample and cell group for pseudobulk inference",
      figure_id = "",
      figure_path = "",
      table_id = "pseudobulk_metadata",
      table_path = "tables/pseudobulk_metadata.csv",
      object_path = "objects/pseudobulk_result.rds",
      source_data = "objects/pseudobulk_result.rds",
      unit = "sample_by_cell_group",
      claim_boundary = "Aggregation prepares replicate-level inference; it is not a differential result."
    ),
    "single_cell.pseudobulk_deseq2.v1" = list(
      short = "pseudobulk_deseq2",
      function_name = "de_deseq2",
      method = "DESeq2 Wald test on pseudobulk count matrix with BH FDR",
      figure_id = "pseudobulk_deseq2_volcano",
      figure_path = "figures/pseudobulk_deseq2_volcano.png",
      table_id = "pseudobulk_deseq2_results",
      table_path = "tables/pseudobulk_deseq2_results.csv",
      object_path = "objects/pseudobulk_deseq2_result.rds",
      source_data = "tables/pseudobulk_deseq2_results.csv",
      unit = "biological_replicate",
      claim_boundary = "Pseudobulk DE requires valid replicate/sample mapping and covariate review before publication claims."
    )
  )
  spec <- specs[[module_id]]
  if (is.null(spec)) {
    stop(paste("Unknown single-cell module:", module_id))
  }
  spec$module_id <- module_id
  spec
}

write_common_outputs <- function(out_dir, run_id, spec, status, dry_run) {
  ensure_dir(file.path(out_dir, "logs"))
  ensure_dir(file.path(out_dir, "tables"))
  ensure_dir(file.path(out_dir, "figures"))
  ensure_dir(file.path(out_dir, "objects"))
  ensure_dir(file.path(out_dir, "qc"))

  capture.output(sessionInfo(), file = file.path(out_dir, "logs", "sessionInfo.txt"))

  if (nzchar(spec$table_path) && !file.exists(file.path(out_dir, spec$table_path))) {
    csv_write(file.path(out_dir, spec$table_path), data.frame(run_id = run_id, module_id = spec$module_id, status = status))
  }
  if (nzchar(spec$figure_path) && !file.exists(file.path(out_dir, spec$figure_path))) {
    writeLines(c("dry_run_placeholder", spec$module_id, spec$method), con = file.path(out_dir, spec$figure_path), useBytes = TRUE)
  }
  if (nzchar(spec$object_path) && !file.exists(file.path(out_dir, spec$object_path))) {
    saveRDS(list(run_id = run_id, module_id = spec$module_id, status = status, dry_run = dry_run), file.path(out_dir, spec$object_path))
  }

  fig_lines <- c("schema_version: single_cell_module_source_map.v1", "figures:")
  if (nzchar(spec$figure_id)) {
    fig_lines <- c(
      fig_lines,
      paste0("  - figure_id: ", spec$figure_id),
      paste0("    path: ", spec$figure_path),
      paste0("    source_data: ", spec$source_data),
      paste0("    script: code_library/modules/single_cell/", spec$short, "/main.R"),
      paste0("    method: ", spec$method),
      paste0("    statistical_unit: ", spec$unit),
      paste0("    claim_boundary: ", spec$claim_boundary)
    )
  }
  write_lines(file.path(out_dir, "figure_source_map.yaml"), fig_lines)

  write_lines(
    file.path(out_dir, "table_source_map.yaml"),
    c(
      "schema_version: single_cell_module_source_map.v1",
      "tables:",
      paste0("  - table_id: ", spec$table_id),
      paste0("    path: ", spec$table_path),
      "    source_inputs: declared Seurat or pseudobulk input",
      paste0("    method: ", spec$method),
      paste0("    statistical_unit: ", spec$unit)
    )
  )

  write_lines(
    file.path(out_dir, "outputs_manifest.yaml"),
    c(
      "schema_version: single_cell_module_outputs.v1",
      paste0("run_id: ", run_id),
      paste0("module_id: ", spec$module_id),
      paste0("status: ", status),
      "outputs:",
      paste0("  - ", spec$table_path),
      if (nzchar(spec$figure_path)) paste0("  - ", spec$figure_path) else NULL,
      paste0("  - ", spec$object_path),
      "  - logs/sessionInfo.txt",
      "  - figure_source_map.yaml",
      "  - table_source_map.yaml"
    )
  )

  write_lines(
    file.path(out_dir, "node_manifest.yaml"),
    c(
      "schema_version: single_cell_node_manifest.v1",
      paste0("run_id: ", run_id),
      paste0("module_id: ", spec$module_id),
      paste0("status: ", status),
      paste0("dry_run: ", ifelse(dry_run, "true", "false")),
      paste0("claim_boundary: ", spec$claim_boundary)
    )
  )
}

run_real_module <- function(args, spec, out_dir) {
  input <- arg_value(args, "input")
  if (!nzchar(input) || !file.exists(input)) {
    stop("--input must point to an existing .rds object for real execution")
  }
  project_root <- arg_value(args, "project-root", normalizePath(getwd(), winslash = "/", mustWork = FALSE))
  source_path <- file.path(project_root, "code_library", "r", "bioinformatics_analysis.R")
  if (!file.exists(source_path)) {
    stop(paste("Function library not found:", source_path))
  }
  source(source_path)
  obj <- readRDS(input)

  if (spec$module_id == "single_cell.seurat_qc.v1") {
    result <- seurat_qc(obj)
    saveRDS(result, file.path(out_dir, spec$object_path))
    csv_write(file.path(out_dir, spec$table_path), data.frame(initial_cells = ncol(obj), retained_cells = ncol(result)))
    return(invisible(result))
  }
  if (spec$module_id == "single_cell.seurat_integration_harmony.v1") {
    batch_var <- arg_value(args, "batch-var", "batch")
    result <- seurat_harmony(obj, batch_var = batch_var)
    saveRDS(result, file.path(out_dir, spec$object_path))
    csv_write(file.path(out_dir, spec$table_path), data.frame(batch_var = batch_var, cells = ncol(result)))
    return(invisible(result))
  }
  if (spec$module_id == "single_cell.seurat_clustering_umap.v1") {
    result <- seurat_cluster(obj, resolution = as.numeric(arg_value(args, "resolution", "0.6")))
    saveRDS(result, file.path(out_dir, spec$object_path))
    counts <- as.data.frame(table(cluster = as.character(result$seurat_clusters)))
    names(counts) <- c("cluster", "n_cells")
    csv_write(file.path(out_dir, spec$table_path), counts)
    return(invisible(result))
  }
  if (spec$module_id == "single_cell.marker_feature_plot.v1") {
    markers <- trimws(unlist(strsplit(arg_value(args, "markers", "MS4A1,CD3E,LYZ"), ",")))
    present <- markers[markers %in% rownames(obj)]
    csv_write(file.path(out_dir, spec$table_path), data.frame(marker = markers, present = markers %in% present))
    saveRDS(obj, file.path(out_dir, spec$object_path))
    return(invisible(obj))
  }
  if (spec$module_id == "single_cell.pseudobulk_aggregate.v1") {
    result <- pseudobulk_aggregate(
      obj,
      sample_col = arg_value(args, "sample-column", "sample_id"),
      group_col = arg_value(args, "group-column", "seurat_clusters")
    )
    saveRDS(result, file.path(out_dir, spec$object_path))
    csv_write(file.path(out_dir, spec$table_path), result$metadata)
    return(invisible(result))
  }
  if (spec$module_id == "single_cell.pseudobulk_deseq2.v1") {
    result <- de_deseq2(
      obj,
      condition_col = arg_value(args, "condition-column", "condition"),
      reference = arg_value(args, "reference", "control"),
      target = arg_value(args, "target", "case")
    )
    saveRDS(result, file.path(out_dir, spec$object_path))
    csv_write(file.path(out_dir, spec$table_path), result)
    return(invisible(result))
  }
}

run_sc_module <- function(module_id) {
  args <- parse_args(commandArgs(trailingOnly = TRUE))
  spec <- module_spec(module_id)
  out_dir <- arg_value(args, "out", paste0(spec$short, "_out"))
  run_id <- arg_value(args, "run-id", spec$short)
  ensure_dir(out_dir)
  write_lines(
    file.path(out_dir, "parameters.yaml"),
    c(
      "schema_version: single_cell_module_parameters.v1",
      paste0("run_id: ", run_id),
      paste0("module_id: ", module_id),
      paste0("input: ", arg_value(args, "input", "")),
      paste0("dry_run_requested: ", ifelse("dry-run" %in% args$flags, "true", "false"))
    )
  )

  dry_run <- "dry-run" %in% args$flags
  if (dry_run) {
    write_common_outputs(out_dir, run_id, spec, "dry_run_completed", TRUE)
    message("Dry-run completed for ", module_id, ": ", out_dir)
    return(invisible(TRUE))
  }

  run_real_module(args, spec, out_dir)
  write_common_outputs(out_dir, run_id, spec, "completed", FALSE)
  message("Module completed for ", module_id, ": ", out_dir)
  invisible(TRUE)
}
