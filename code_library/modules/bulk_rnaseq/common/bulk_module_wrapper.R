#!/usr/bin/env Rscript

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

bulk_spec <- function(module_id) {
  specs <- list(
    "bulk_rnaseq.deseq2_de.v1" = list(
      short = "deseq2_de",
      method = "DESeq2 negative-binomial GLM with Wald test and BH FDR",
      table_id = "deseq2_de_results",
      table_path = "tables/deseq2_de_results.csv",
      figure_id = "deseq2_volcano",
      figure_path = "figures/deseq2_volcano.png",
      normalized_summary = "tables/normalized_counts_summary.csv",
      parameters = c("condition_column", "reference", "target"),
      unit = "biological_replicate",
      claim_boundary = "Publication-oriented association testing only; causal or mechanism claims require validation."
    ),
    "bulk_rnaseq.limma_voom_de.v1" = list(
      short = "limma_voom_de",
      method = "limma-voom empirical Bayes differential expression with BH FDR",
      table_id = "limma_voom_de_results",
      table_path = "tables/limma_voom_de_results.csv",
      figure_id = "limma_voom_heatmap",
      figure_path = "figures/limma_voom_heatmap.png",
      normalized_summary = "tables/voom_normalization_summary.csv",
      parameters = c("condition_column", "reference", "target", "block_column"),
      unit = "biological_replicate",
      claim_boundary = "Publication-oriented association testing; design matrix and covariates must be reviewed."
    ),
    "bulk_rnaseq.wgcna.v1" = list(
      short = "wgcna",
      method = "WGCNA soft-threshold selection, blockwise modules, module-trait correlation",
      table_id = "wgcna_module_trait_correlation",
      table_path = "tables/wgcna_module_trait_correlation.csv",
      figure_id = "wgcna_sample_clustering",
      figure_path = "figures/wgcna_sample_clustering.png",
      normalized_summary = "tables/wgcna_parameters.csv",
      parameters = c("soft_power", "min_module_size", "merge_cut_height"),
      unit = "sample",
      claim_boundary = "Co-expression module association only; hub genes and modules do not prove mechanism."
    ),
    "bulk_rnaseq.fgsea_enrichment.v1" = list(
      short = "fgsea_enrichment",
      method = "fgsea preranked gene-set enrichment with declared gene universe and gene-set source",
      table_id = "fgsea_results",
      table_path = "tables/fgsea_results.csv",
      figure_id = "fgsea_dotplot",
      figure_path = "figures/fgsea_dotplot.png",
      normalized_summary = "tables/gene_set_source.csv",
      parameters = c("gene_universe", "database_version", "gene_set_source", "fdr_method"),
      unit = "gene_set",
      claim_boundary = "Pathway enrichment is interpretive and depends on the ranked statistic and gene-set database."
    ),
    "bulk_rnaseq.immune_deconvolution_adapter.v1" = list(
      short = "immune_deconvolution_adapter",
      method = "Adapter contract for CIBERSORT/ssGSEA/xCell-style immune deconvolution with provenance review",
      table_id = "immune_fraction_estimates",
      table_path = "tables/immune_fraction_estimates.csv",
      figure_id = "immune_fraction_heatmap",
      figure_path = "figures/immune_fraction_heatmap.png",
      normalized_summary = "tables/deconvolution_reference.csv",
      parameters = c("signature_matrix", "method", "normalization"),
      unit = "sample",
      claim_boundary = "Cell-fraction deconvolution is model-based estimation and requires orthogonal validation."
    )
  )
  spec <- specs[[module_id]]
  if (is.null(spec)) {
    stop(paste("Unknown bulk RNA-seq module:", module_id))
  }
  spec$module_id <- module_id
  spec
}

write_common_outputs <- function(out_dir, run_id, spec, status, dry_run) {
  ensure_dir(file.path(out_dir, "logs"))
  ensure_dir(file.path(out_dir, "tables"))
  ensure_dir(file.path(out_dir, "figures"))
  ensure_dir(file.path(out_dir, "objects"))

  capture.output(sessionInfo(), file = file.path(out_dir, "logs", "sessionInfo.txt"))
  csv_write(file.path(out_dir, spec$table_path), data.frame(run_id = run_id, module_id = spec$module_id, status = status, method = spec$method))
  csv_write(file.path(out_dir, spec$normalized_summary), data.frame(parameter = spec$parameters, status = "declared_or_required"))
  writeLines(c("dry_run_placeholder", spec$module_id, spec$method), con = file.path(out_dir, spec$figure_path), useBytes = TRUE)
  saveRDS(list(run_id = run_id, module_id = spec$module_id, status = status, dry_run = dry_run), file.path(out_dir, "objects", paste0(spec$short, ".rds")))

  write_lines(
    file.path(out_dir, "figure_source_map.yaml"),
    c(
      "schema_version: bulk_module_source_map.v1",
      "figures:",
      paste0("  - figure_id: ", spec$figure_id),
      paste0("    path: ", spec$figure_path),
      paste0("    source_data: ", spec$table_path),
      paste0("    script: code_library/modules/bulk_rnaseq/", spec$short, "/main.R"),
      paste0("    method: ", spec$method),
      paste0("    statistical_unit: ", spec$unit),
      paste0("    claim_boundary: ", spec$claim_boundary)
    )
  )
  write_lines(
    file.path(out_dir, "table_source_map.yaml"),
    c(
      "schema_version: bulk_module_source_map.v1",
      "tables:",
      paste0("  - table_id: ", spec$table_id),
      paste0("    path: ", spec$table_path),
      "    source_inputs: count matrix and sample metadata",
      paste0("    method: ", spec$method),
      paste0("    statistical_unit: ", spec$unit)
    )
  )
  write_lines(
    file.path(out_dir, "outputs_manifest.yaml"),
    c(
      "schema_version: bulk_module_outputs.v1",
      paste0("run_id: ", run_id),
      paste0("module_id: ", spec$module_id),
      paste0("status: ", status),
      "outputs:",
      paste0("  - ", spec$table_path),
      paste0("  - ", spec$figure_path),
      paste0("  - ", spec$normalized_summary),
      "  - logs/sessionInfo.txt",
      "  - figure_source_map.yaml",
      "  - table_source_map.yaml"
    )
  )
  write_lines(
    file.path(out_dir, "node_manifest.yaml"),
    c(
      "schema_version: bulk_node_manifest.v1",
      paste0("run_id: ", run_id),
      paste0("module_id: ", spec$module_id),
      paste0("status: ", status),
      paste0("dry_run: ", ifelse(dry_run, "true", "false")),
      paste0("claim_boundary: ", spec$claim_boundary)
    )
  )
}

run_bulk_module <- function(module_id) {
  args <- parse_args(commandArgs(trailingOnly = TRUE))
  spec <- bulk_spec(module_id)
  out_dir <- arg_value(args, "out", paste0(spec$short, "_out"))
  run_id <- arg_value(args, "run-id", spec$short)
  ensure_dir(out_dir)
  write_lines(
    file.path(out_dir, "parameters.yaml"),
    c(
      "schema_version: bulk_module_parameters.v1",
      paste0("run_id: ", run_id),
      paste0("module_id: ", module_id),
      paste0("counts: ", arg_value(args, "counts", "")),
      paste0("metadata: ", arg_value(args, "metadata", "")),
      paste0("dry_run_requested: ", ifelse("dry-run" %in% args$flags, "true", "false"))
    )
  )
  if ("dry-run" %in% args$flags) {
    write_common_outputs(out_dir, run_id, spec, "dry_run_completed", TRUE)
    message("Dry-run completed for ", module_id, ": ", out_dir)
    return(invisible(TRUE))
  }
  stop("Real bulk RNA-seq execution requires a module-specific approved fixture and is not run by this dry-run wrapper.")
}
