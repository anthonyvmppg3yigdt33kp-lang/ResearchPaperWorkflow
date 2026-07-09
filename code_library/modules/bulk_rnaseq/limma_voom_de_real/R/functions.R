LIMMA_VOOM_CLAIM_BOUNDARY <- "Differential expression is association evidence only and depends on valid sample-level design."

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

write_yaml_lines <- function(path, lines) {
  dir.create(dirname(path), recursive = TRUE, showWarnings = FALSE)
  writeLines(lines, con = path, useBytes = TRUE)
}

prepare_limma_dirs <- function(output_dir) {
  for (subdir in c("tables", "figures", "objects", "logs", "qc")) {
    dir.create(file.path(output_dir, subdir), recursive = TRUE, showWarnings = FALSE)
  }
}

write_limma_source_maps <- function(output_dir, input_label, script_label) {
  write_yaml_lines(
    file.path(output_dir, "figure_source_map.yaml"),
    c(
      "schema_version: limma_voom_source_map.v1",
      "figures:",
      "  - figure_id: limma_voom_volcano",
      "    path: figures/limma_voom_volcano.png",
      "    source_data: tables/limma_voom_results.csv",
      paste0("    script: ", script_label),
      "    method: edgeR normalization, limma voom, lmFit, contrasts.fit, eBayes",
      "    statistical_unit: sample",
      paste0("    claim_boundary: \"", LIMMA_VOOM_CLAIM_BOUNDARY, "\"")
    )
  )
  write_yaml_lines(
    file.path(output_dir, "table_source_map.yaml"),
    c(
      "schema_version: limma_voom_source_map.v1",
      "tables:",
      "  - table_id: limma_voom_results",
      "    path: tables/limma_voom_results.csv",
      paste0("    source_inputs: ", input_label),
      "    method: limma topTable standardized differential-expression table",
      "    statistical_unit: sample",
      paste0("    claim_boundary: \"", LIMMA_VOOM_CLAIM_BOUNDARY, "\""),
      "  - table_id: design_summary",
      "    path: qc/design_summary.csv",
      "    source_inputs: sample_metadata",
      "    method: sample count and group-size audit before model fitting",
      "    statistical_unit: sample",
      paste0("    claim_boundary: \"", LIMMA_VOOM_CLAIM_BOUNDARY, "\"")
    )
  )
}

write_limma_manifests <- function(output_dir, run_id, status, dry_run = FALSE) {
  write_yaml_lines(
    file.path(output_dir, "outputs_manifest.yaml"),
    c(
      "schema_version: limma_voom_outputs.v1",
      paste0("run_id: ", run_id),
      paste0("status: ", status),
      paste0("dry_run: ", tolower(as.character(dry_run))),
      paste0("claim_boundary: \"", LIMMA_VOOM_CLAIM_BOUNDARY, "\""),
      "outputs:",
      "  - tables/limma_voom_results.csv",
      "  - qc/design_summary.csv",
      "  - figures/limma_voom_volcano.png",
      "  - objects/limma_voom_parameters.rds",
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
      "module_id: bulk_rnaseq.limma_voom_de_real.v1",
      paste0("status: ", status),
      paste0("dry_run: ", tolower(as.character(dry_run))),
      paste0("claim_boundary: \"", LIMMA_VOOM_CLAIM_BOUNDARY, "\"")
    )
  )
}

write_limma_dry_run <- function(output_dir, run_id) {
  prepare_limma_dirs(output_dir)
  results <- data.frame(
    gene = c("GENE_A", "GENE_B", "GENE_C"),
    logFC = c(1.1, -0.9, 0.2),
    AveExpr = c(5.0, 4.3, 3.8),
    t = c(4.2, -3.1, 0.5),
    P.Value = c(0.001, 0.02, 0.5),
    adj.P.Val = c(0.01, 0.08, 0.7),
    B = c(2.0, 1.2, -1.5),
    reference = "reference",
    target = "target",
    condition_column = "condition",
    stringsAsFactors = FALSE
  )
  utils::write.csv(results, file.path(output_dir, "tables", "limma_voom_results.csv"), row.names = FALSE, quote = TRUE)
  utils::write.csv(
    data.frame(group = c("reference", "target"), n_samples = c(3, 3), sample_mapping_status = "dry_run_fixture"),
    file.path(output_dir, "qc", "design_summary.csv"),
    row.names = FALSE,
    quote = TRUE
  )
  grDevices::png(file.path(output_dir, "figures", "limma_voom_volcano.png"), width = 900, height = 650)
  plot(results$logFC, -log10(results$adj.P.Val), pch = 19, xlab = "logFC", ylab = "-log10(FDR)", main = "limma-voom dry-run volcano")
  grDevices::dev.off()
  saveRDS(list(run_id = run_id, dry_run = TRUE), file.path(output_dir, "objects", "limma_voom_parameters.rds"))
  writeLines("dry-run sessionInfo placeholder; real execution writes R sessionInfo()", file.path(output_dir, "logs", "sessionInfo.txt"))
  write_limma_source_maps(output_dir, "dry_run_fixture", "code_library/modules/bulk_rnaseq/limma_voom_de_real/main.R")
  write_limma_manifests(output_dir, run_id, "dry_run_completed", dry_run = TRUE)
}

run_limma_voom_de_real <- function(
  count_matrix,
  sample_metadata,
  condition_column,
  sample_id_column = "sample_id",
  reference,
  target,
  output_dir,
  run_id
) {
  required <- c("edgeR", "limma")
  missing <- required[!vapply(required, requireNamespace, quietly = TRUE, FUN.VALUE = logical(1))]
  if (length(missing) > 0) {
    stop(paste("Missing required R packages:", paste(missing, collapse = ", ")))
  }
  prepare_limma_dirs(output_dir)
  counts <- utils::read.csv(count_matrix, check.names = FALSE, row.names = 1)
  metadata <- utils::read.csv(sample_metadata, check.names = FALSE)
  if (!sample_id_column %in% colnames(metadata)) {
    stop(paste("sample_id_column not found:", sample_id_column))
  }
  if (!condition_column %in% colnames(metadata)) {
    stop(paste("condition_column not found:", condition_column))
  }
  sample_ids <- as.character(metadata[[sample_id_column]])
  missing_samples <- setdiff(sample_ids, colnames(counts))
  if (length(missing_samples) > 0) {
    stop(paste("metadata samples not found in count matrix:", paste(missing_samples, collapse = ", ")))
  }
  counts <- counts[, sample_ids, drop = FALSE]
  condition <- factor(metadata[[condition_column]])
  if (!all(c(reference, target) %in% levels(condition))) {
    stop("reference and target must both exist in the condition column")
  }
  condition <- stats::relevel(condition, ref = reference)
  design <- stats::model.matrix(~ 0 + condition)
  colnames(design) <- levels(condition)
  contrast <- limma::makeContrasts(contrasts = paste0(target, "-", reference), levels = design)
  dge <- edgeR::DGEList(counts = counts)
  dge <- edgeR::calcNormFactors(dge)
  voom_obj <- limma::voom(dge, design, plot = FALSE)
  fit <- limma::lmFit(voom_obj, design)
  fit2 <- limma::contrasts.fit(fit, contrast)
  fit2 <- limma::eBayes(fit2)
  table <- limma::topTable(fit2, number = Inf, sort.by = "P")
  table$gene <- rownames(table)
  table$reference <- reference
  table$target <- target
  table$condition_column <- condition_column
  table <- table[, c("gene", setdiff(colnames(table), "gene"))]
  utils::write.csv(table, file.path(output_dir, "tables", "limma_voom_results.csv"), row.names = FALSE, quote = TRUE)
  design_summary <- as.data.frame(table(condition))
  names(design_summary) <- c("group", "n_samples")
  design_summary$sample_mapping_status <- "sample_id_matched"
  utils::write.csv(design_summary, file.path(output_dir, "qc", "design_summary.csv"), row.names = FALSE, quote = TRUE)
  grDevices::png(file.path(output_dir, "figures", "limma_voom_volcano.png"), width = 900, height = 650)
  plot(table$logFC, -log10(pmax(table$adj.P.Val, .Machine$double.xmin)), pch = 19, xlab = "logFC", ylab = "-log10(FDR)", main = "limma-voom volcano")
  abline(v = c(-1, 1), lty = 2, col = "grey50")
  grDevices::dev.off()
  saveRDS(
    list(run_id = run_id, condition_column = condition_column, sample_id_column = sample_id_column, reference = reference, target = target),
    file.path(output_dir, "objects", "limma_voom_parameters.rds")
  )
  capture.output(sessionInfo(), file = file.path(output_dir, "logs", "sessionInfo.txt"))
  write_limma_source_maps(output_dir, "count_matrix_and_sample_metadata", "code_library/modules/bulk_rnaseq/limma_voom_de_real/main.R")
  write_limma_manifests(output_dir, run_id, "completed", dry_run = FALSE)
  invisible(table)
}

run_limma_voom_de_cli <- function(args) {
  output_dir <- get_arg(args, "--out", "limma_voom_de_out")
  run_id <- get_arg(args, "--run-id", "limma_voom_de")
  if (has_flag(args, "--dry-run")) {
    write_limma_dry_run(output_dir, run_id)
    return(invisible(TRUE))
  }
  counts <- get_arg(args, "--counts")
  if (!nzchar(counts)) {
    counts <- get_arg(args, "--count-matrix")
  }
  metadata <- get_arg(args, "--metadata")
  if (!nzchar(metadata)) {
    metadata <- get_arg(args, "--sample-metadata")
  }
  if (!nzchar(counts) || !nzchar(metadata)) {
    stop("--counts and --metadata are required")
  }
  run_limma_voom_de_real(
    count_matrix = counts,
    sample_metadata = metadata,
    condition_column = get_arg(args, "--condition-column", "condition"),
    sample_id_column = get_arg(args, "--sample-id-column", "sample_id"),
    reference = get_arg(args, "--reference"),
    target = get_arg(args, "--target"),
    output_dir = output_dir,
    run_id = run_id
  )
}
