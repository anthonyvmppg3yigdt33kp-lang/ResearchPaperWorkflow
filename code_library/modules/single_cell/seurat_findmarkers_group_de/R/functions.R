FINDMARKERS_CLAIM_BOUNDARY <- "Cell-level marker/differential expression is exploratory unless biological replicate-aware inference is documented."

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

write_yaml_lines <- function(path, lines) {
  dir.create(dirname(path), recursive = TRUE, showWarnings = FALSE)
  writeLines(lines, con = path, useBytes = TRUE)
}

prepare_findmarkers_dirs <- function(output_dir) {
  for (subdir in c("tables", "figures", "objects", "logs", "qc")) {
    dir.create(file.path(output_dir, subdir), recursive = TRUE, showWarnings = FALSE)
  }
}

write_findmarkers_source_maps <- function(output_dir, run_id, input_label, script_label) {
  write_yaml_lines(
    file.path(output_dir, "figure_source_map.yaml"),
    c(
      "schema_version: seurat_findmarkers_source_map.v1",
      "figures:",
      "  - figure_id: findmarkers_volcano",
      "    path: figures/findmarkers_volcano.png",
      "    source_data: tables/findmarkers_results.csv",
      paste0("    script: ", script_label),
      "    method: Seurat FindMarkers group comparison with parameterized identities",
      "    statistical_unit: cell",
      paste0("    claim_boundary: \"", FINDMARKERS_CLAIM_BOUNDARY, "\"")
    )
  )
  write_yaml_lines(
    file.path(output_dir, "table_source_map.yaml"),
    c(
      "schema_version: seurat_findmarkers_source_map.v1",
      "tables:",
      "  - table_id: findmarkers_results",
      "    path: tables/findmarkers_results.csv",
      paste0("    source_inputs: ", input_label),
      "    method: Seurat FindMarkers with standardized output columns",
      "    statistical_unit: cell",
      paste0("    claim_boundary: \"", FINDMARKERS_CLAIM_BOUNDARY, "\""),
      "  - table_id: findmarkers_summary",
      "    path: tables/findmarkers_summary.csv",
      "    source_inputs: tables/findmarkers_results.csv",
      "    method: group size and result-count summary",
      "    statistical_unit: cell",
      paste0("    claim_boundary: \"", FINDMARKERS_CLAIM_BOUNDARY, "\"")
    )
  )
}

write_findmarkers_manifests <- function(output_dir, run_id, status, dry_run = FALSE) {
  write_yaml_lines(
    file.path(output_dir, "outputs_manifest.yaml"),
    c(
      "schema_version: seurat_findmarkers_outputs.v1",
      paste0("run_id: ", run_id),
      paste0("status: ", status),
      paste0("dry_run: ", tolower(as.character(dry_run))),
      paste0("claim_boundary: \"", FINDMARKERS_CLAIM_BOUNDARY, "\""),
      "outputs:",
      "  - tables/findmarkers_results.csv",
      "  - tables/findmarkers_summary.csv",
      "  - qc/group_size_sample_mapping.csv",
      "  - figures/findmarkers_volcano.png",
      "  - objects/findmarkers_parameters.rds",
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
      "module_id: single_cell.seurat_findmarkers_group_de.v1",
      paste0("status: ", status),
      paste0("dry_run: ", tolower(as.character(dry_run))),
      paste0("claim_boundary: \"", FINDMARKERS_CLAIM_BOUNDARY, "\"")
    )
  )
}

write_findmarkers_dry_run <- function(output_dir, run_id) {
  prepare_findmarkers_dirs(output_dir)
  results <- data.frame(
    gene = c("GENE_A", "GENE_B", "GENE_C"),
    p_val = c(0.001, 0.05, 0.2),
    avg_log2FC = c(1.2, -0.7, 0.1),
    pct.1 = c(0.75, 0.22, 0.48),
    pct.2 = c(0.30, 0.55, 0.45),
    p_val_adj = c(0.01, 0.2, 0.8),
    ident_1 = "group_a",
    ident_2 = "group_b",
    group_column = "condition",
    subset_column = "",
    subset_value = "",
    stringsAsFactors = FALSE
  )
  utils::write.csv(results, file.path(output_dir, "tables", "findmarkers_results.csv"), row.names = FALSE, quote = TRUE)
  summary <- data.frame(
    run_id = run_id,
    status = "dry_run_fixture",
    n_genes = nrow(results),
    significant_fdr_0_05 = sum(results$p_val_adj < 0.05),
    claim_boundary = FINDMARKERS_CLAIM_BOUNDARY,
    stringsAsFactors = FALSE
  )
  utils::write.csv(summary, file.path(output_dir, "tables", "findmarkers_summary.csv"), row.names = FALSE, quote = TRUE)
  utils::write.csv(
    data.frame(group = c("group_a", "group_b"), n_cells = c(50, 50), sample_mapping_status = "dry_run_not_replicate_aware"),
    file.path(output_dir, "qc", "group_size_sample_mapping.csv"),
    row.names = FALSE,
    quote = TRUE
  )
  grDevices::png(file.path(output_dir, "figures", "findmarkers_volcano.png"), width = 900, height = 650)
  plot(results$avg_log2FC, -log10(results$p_val_adj), pch = 19, xlab = "avg_log2FC", ylab = "-log10(FDR)", main = "FindMarkers dry-run volcano")
  grDevices::dev.off()
  saveRDS(list(run_id = run_id, dry_run = TRUE), file.path(output_dir, "objects", "findmarkers_parameters.rds"))
  writeLines("dry-run sessionInfo placeholder; real execution writes R sessionInfo()", file.path(output_dir, "logs", "sessionInfo.txt"))
  write_findmarkers_source_maps(output_dir, run_id, "dry_run_fixture", "code_library/modules/single_cell/seurat_findmarkers_group_de/main.R")
  write_findmarkers_manifests(output_dir, run_id, "dry_run_completed", dry_run = TRUE)
}

standardize_findmarkers_table <- function(markers, ident_1, ident_2, group_column, subset_column, subset_value) {
  markers$gene <- rownames(markers)
  if (!"avg_log2FC" %in% colnames(markers) && "avg_logFC" %in% colnames(markers)) {
    markers$avg_log2FC <- markers$avg_logFC
  }
  required <- c("p_val", "avg_log2FC", "pct.1", "pct.2", "p_val_adj")
  for (column in required) {
    if (!column %in% colnames(markers)) {
      markers[[column]] <- NA
    }
  }
  markers$ident_1 <- ident_1
  markers$ident_2 <- ident_2
  markers$group_column <- group_column
  markers$subset_column <- subset_column
  markers$subset_value <- subset_value
  markers[, c("gene", "p_val", "avg_log2FC", "pct.1", "pct.2", "p_val_adj", "ident_1", "ident_2", "group_column", "subset_column", "subset_value")]
}

run_seurat_findmarkers_group_de <- function(
  seurat_object,
  group_column,
  ident_1,
  ident_2,
  subset_column = NULL,
  subset_value = NULL,
  assay = NULL,
  slot = "data",
  test_use = "wilcox",
  min_pct = 0.1,
  logfc_threshold = 0.25,
  only_pos = FALSE,
  output_dir,
  run_id
) {
  required <- c("Seurat", "ggplot2")
  missing <- required[!vapply(required, requireNamespace, quietly = TRUE, FUN.VALUE = logical(1))]
  if (length(missing) > 0) {
    stop(paste("Missing required R packages:", paste(missing, collapse = ", ")))
  }
  prepare_findmarkers_dirs(output_dir)
  obj <- seurat_object
  if (is.character(seurat_object)) {
    obj <- readRDS(seurat_object)
  }
  if (!is.null(assay) && nzchar(assay)) {
    Seurat::DefaultAssay(obj) <- assay
  }
  metadata <- obj[[]]
  if (!group_column %in% colnames(metadata)) {
    stop(paste("group_column not found in Seurat metadata:", group_column))
  }
  subset_column_value <- ifelse(is.null(subset_column), "", subset_column)
  subset_value_value <- ifelse(is.null(subset_value), "", subset_value)
  if (!is.null(subset_column) && nzchar(subset_column)) {
    if (!subset_column %in% colnames(metadata)) {
      stop(paste("subset_column not found in Seurat metadata:", subset_column))
    }
    keep <- rownames(metadata)[as.character(metadata[[subset_column]]) == as.character(subset_value)]
    obj <- subset(obj, cells = keep)
    metadata <- obj[[]]
  }
  Seurat::Idents(obj) <- metadata[[group_column]]
  group_sizes <- as.data.frame(table(group = as.character(Seurat::Idents(obj))))
  names(group_sizes) <- c("group", "n_cells")
  group_sizes$sample_mapping_status <- ifelse("sample_id" %in% colnames(metadata), "sample_id_present_not_modeled", "sample_id_not_found_cell_level_only")
  utils::write.csv(group_sizes, file.path(output_dir, "qc", "group_size_sample_mapping.csv"), row.names = FALSE, quote = TRUE)
  markers <- Seurat::FindMarkers(
    obj,
    ident.1 = ident_1,
    ident.2 = ident_2,
    slot = slot,
    test.use = test_use,
    min.pct = min_pct,
    logfc.threshold = logfc_threshold,
    only.pos = only_pos
  )
  out <- standardize_findmarkers_table(markers, ident_1, ident_2, group_column, subset_column_value, subset_value_value)
  utils::write.csv(out, file.path(output_dir, "tables", "findmarkers_results.csv"), row.names = FALSE, quote = TRUE)
  summary <- data.frame(
    run_id = run_id,
    group_column = group_column,
    ident_1 = ident_1,
    ident_2 = ident_2,
    subset_column = subset_column_value,
    subset_value = subset_value_value,
    n_genes = nrow(out),
    significant_fdr_0_05 = sum(out$p_val_adj < 0.05, na.rm = TRUE),
    claim_boundary = FINDMARKERS_CLAIM_BOUNDARY,
    stringsAsFactors = FALSE
  )
  utils::write.csv(summary, file.path(output_dir, "tables", "findmarkers_summary.csv"), row.names = FALSE, quote = TRUE)
  grDevices::png(file.path(output_dir, "figures", "findmarkers_volcano.png"), width = 900, height = 650)
  plot(out$avg_log2FC, -log10(pmax(out$p_val_adj, .Machine$double.xmin)), pch = 19, xlab = "avg_log2FC", ylab = "-log10(FDR)", main = "FindMarkers volcano")
  abline(v = c(-logfc_threshold, logfc_threshold), lty = 2, col = "grey50")
  grDevices::dev.off()
  saveRDS(
    list(
      run_id = run_id,
      group_column = group_column,
      ident_1 = ident_1,
      ident_2 = ident_2,
      subset_column = subset_column_value,
      subset_value = subset_value_value,
      assay = assay,
      slot = slot,
      test_use = test_use,
      min_pct = min_pct,
      logfc_threshold = logfc_threshold,
      only_pos = only_pos
    ),
    file.path(output_dir, "objects", "findmarkers_parameters.rds")
  )
  capture.output(sessionInfo(), file = file.path(output_dir, "logs", "sessionInfo.txt"))
  write_findmarkers_source_maps(output_dir, run_id, "seurat_rds", "code_library/modules/single_cell/seurat_findmarkers_group_de/main.R")
  write_findmarkers_manifests(output_dir, run_id, "completed", dry_run = FALSE)
  invisible(out)
}

run_seurat_findmarkers_group_de_cli <- function(args) {
  output_dir <- get_arg(args, "--out", "findmarkers_group_de_out")
  run_id <- get_arg(args, "--run-id", "findmarkers_group_de")
  if (has_flag(args, "--dry-run")) {
    write_findmarkers_dry_run(output_dir, run_id)
    return(invisible(TRUE))
  }
  input <- get_arg(args, "--input")
  if (!nzchar(input)) {
    input <- get_arg(args, "--seurat-rds")
  }
  if (!nzchar(input)) {
    stop("--input <seurat_rds> is required")
  }
  run_seurat_findmarkers_group_de(
    seurat_object = input,
    group_column = get_arg(args, "--group-column"),
    ident_1 = get_arg(args, "--ident-1"),
    ident_2 = get_arg(args, "--ident-2"),
    subset_column = get_arg(args, "--subset-column", ""),
    subset_value = get_arg(args, "--subset-value", ""),
    assay = get_arg(args, "--assay", ""),
    slot = get_arg(args, "--slot", "data"),
    test_use = get_arg(args, "--test-use", "wilcox"),
    min_pct = as.numeric(get_arg(args, "--min-pct", "0.1")),
    logfc_threshold = as.numeric(get_arg(args, "--logfc-threshold", "0.25")),
    only_pos = truthy(get_arg(args, "--only-pos", "false")),
    output_dir = output_dir,
    run_id = run_id
  )
}
