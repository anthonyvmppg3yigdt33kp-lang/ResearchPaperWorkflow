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

shared_risk <- c(
  "ligand-receptor inference is hypothesis-generating",
  "colocalization does not prove physical interaction",
  "spatial overlap does not prove causality",
  "orthogonal validation required for mechanism claims"
)

spatial_spec <- function(module_id) {
  specs <- list(
    "spatial.seurat_spatial_qc.v1" = list(short = "seurat_spatial_qc", modality = "spatial", method = "Seurat spatial object QC with coordinate and tissue-section checks", figure_id = "spatial_qc", table_id = "spatial_qc_metrics", unit = "spot_or_cell", claim_boundary = "Spatial QC defines usable spots/cells and tissue section metadata; it is not biological evidence."),
    "spatial.spatial_feature_plot.v1" = list(short = "spatial_feature_plot", modality = "spatial", method = "SpatialFeaturePlot-style gene or score visualization with coordinate-system provenance", figure_id = "spatial_feature_plot", table_id = "spatial_feature_source", unit = "spot_or_cell", claim_boundary = "Spatial expression visualization is descriptive and does not prove causality."),
    "spatial.spatial_domain_detection.v1" = list(short = "spatial_domain_detection", modality = "spatial", method = "Spatial domain detection contract with sample and tissue-section audit", figure_id = "spatial_domains", table_id = "spatial_domain_assignments", unit = "spot_or_cell", claim_boundary = "Spatial domains are algorithmic groupings and require biological annotation and validation."),
    "spatial.deconvolution_cell2location_or_rctd.v1" = list(short = "deconvolution_cell2location_or_rctd", modality = "spatial", method = "Spatial deconvolution adapter for reviewed cell2location/RCTD reference signatures", figure_id = "spatial_deconvolution", table_id = "spatial_deconvolution_fractions", unit = "spot_or_cell", claim_boundary = "Deconvolution estimates cell-type abundance and requires reference and orthogonal validation."),
    "spatial.spatial_ligand_receptor.v1" = list(short = "spatial_ligand_receptor", modality = "spatial", method = "Spatial ligand-receptor proximity hypothesis adapter", figure_id = "spatial_ligand_receptor", table_id = "spatial_ligand_receptor_pairs", unit = "spot_or_cell_pair", claim_boundary = "Ligand-receptor and colocalization signals are hypothesis-generating only."),
    "single_cell.cellchat_communication.v1" = list(short = "cellchat_communication", modality = "single_cell", method = "CellChat-style cell-cell communication inference contract", figure_id = "cellchat_network", table_id = "cellchat_interactions", unit = "cell_group_pair", claim_boundary = "Cell-cell communication inference is hypothesis-generating and requires validation."),
    "single_cell.nichenet_ligand_target.v1" = list(short = "nichenet_ligand_target", modality = "single_cell", method = "NicheNet-style ligand-target prioritization contract", figure_id = "nichenet_ligand_target", table_id = "nichenet_ligand_targets", unit = "cell_group_pair", claim_boundary = "Ligand-target ranking is hypothesis-generating and does not prove causal signaling.")
  )
  spec <- specs[[module_id]]
  if (is.null(spec)) {
    stop(paste("Unknown spatial/communication module:", module_id))
  }
  spec$module_id <- module_id
  spec
}

write_outputs <- function(out_dir, run_id, spec, status, dry_run) {
  ensure_dir(file.path(out_dir, "logs"))
  ensure_dir(file.path(out_dir, "tables"))
  ensure_dir(file.path(out_dir, "figures"))
  ensure_dir(file.path(out_dir, "objects"))
  capture.output(sessionInfo(), file = file.path(out_dir, "logs", "sessionInfo.txt"))
  table_path <- paste0("tables/", spec$table_id, ".csv")
  figure_path <- paste0("figures/", spec$figure_id, ".png")
  csv_write(
    file.path(out_dir, table_path),
    data.frame(
      run_id = run_id,
      module_id = spec$module_id,
      status = status,
      coordinate_system = "requires_human_input",
      tissue_section = "requires_human_input",
      sample_id = "requires_human_input",
      deconvolution_reference = "requires_human_input",
      method_version = "requires_human_input"
    )
  )
  writeLines(c("dry_run_placeholder", spec$module_id, spec$method), con = file.path(out_dir, figure_path), useBytes = TRUE)
  saveRDS(list(run_id = run_id, module_id = spec$module_id, status = status), file.path(out_dir, "objects", paste0(spec$short, ".rds")))
  write_lines(
    file.path(out_dir, "figure_source_map.yaml"),
    c(
      "schema_version: spatial_module_source_map.v1",
      "figures:",
      paste0("  - figure_id: ", spec$figure_id),
      paste0("    path: ", figure_path),
      paste0("    source_data: ", table_path),
      paste0("    script: code_library/modules/", ifelse(spec$modality == "spatial", "spatial", "single_cell"), "/", spec$short, "/main.R"),
      paste0("    method: ", spec$method),
      paste0("    statistical_unit: ", spec$unit),
      paste0("    claim_boundary: ", spec$claim_boundary),
      "    coordinate_system: requires_human_input",
      "    spot_cell_bin_unit: requires_human_input",
      "    tissue_section: requires_human_input",
      "    sample_id: requires_human_input",
      "    deconvolution_reference: requires_human_input",
      "    method_version: requires_human_input"
    )
  )
  write_lines(
    file.path(out_dir, "table_source_map.yaml"),
    c(
      "schema_version: spatial_module_source_map.v1",
      "tables:",
      paste0("  - table_id: ", spec$table_id),
      paste0("    path: ", table_path),
      "    source_inputs: spatial object, coordinates, metadata, and reviewed references",
      paste0("    method: ", spec$method),
      paste0("    statistical_unit: ", spec$unit)
    )
  )
  write_lines(
    file.path(out_dir, "outputs_manifest.yaml"),
    c("schema_version: spatial_module_outputs.v1", paste0("run_id: ", run_id), paste0("module_id: ", spec$module_id), paste0("status: ", status), "outputs:", paste0("  - ", table_path), paste0("  - ", figure_path), "  - logs/sessionInfo.txt", "  - figure_source_map.yaml", "  - table_source_map.yaml")
  )
  write_lines(
    file.path(out_dir, "node_manifest.yaml"),
    c("schema_version: spatial_node_manifest.v1", paste0("run_id: ", run_id), paste0("module_id: ", spec$module_id), paste0("status: ", status), paste0("dry_run: ", ifelse(dry_run, "true", "false")), paste0("claim_boundary: ", spec$claim_boundary), "reviewer_risk:", paste0("  - ", shared_risk))
  )
}

run_spatial_module <- function(module_id) {
  args <- parse_args(commandArgs(trailingOnly = TRUE))
  spec <- spatial_spec(module_id)
  out_dir <- arg_value(args, "out", paste0(spec$short, "_out"))
  run_id <- arg_value(args, "run-id", spec$short)
  ensure_dir(out_dir)
  write_lines(
    file.path(out_dir, "parameters.yaml"),
    c("schema_version: spatial_module_parameters.v1", paste0("run_id: ", run_id), paste0("module_id: ", module_id), paste0("input: ", arg_value(args, "input", "")), paste0("dry_run_requested: ", ifelse("dry-run" %in% args$flags, "true", "false")))
  )
  if ("dry-run" %in% args$flags) {
    write_outputs(out_dir, run_id, spec, "dry_run_completed", TRUE)
    message("Dry-run completed for ", module_id, ": ", out_dir)
    return(invisible(TRUE))
  }
  stop("Real spatial/communication execution requires approved data, reviewed references, and module-specific validation.")
}
