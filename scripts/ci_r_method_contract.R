#!/usr/bin/env Rscript

message("Parsing R method assets")
files <- list.files("code_library/modules", pattern = "\\.R$", recursive = TRUE, full.names = TRUE)
if (length(files) == 0) {
  stop("No R method assets found")
}
for (file in files) {
  parse(file)
}

message("Running dry-run wrapper contracts")
main_files <- files[basename(files) == "main.R"]
main_files <- main_files[!grepl("seurat_pbmc3k_basic", main_files, fixed = TRUE)]
if (length(main_files) == 0) {
  stop("No dry-run wrapper main.R files found")
}
for (file in main_files) {
  out_dir <- tempfile("r_method_contract_")
  dir.create(out_dir, recursive = TRUE, showWarnings = FALSE)
  run_id <- paste0("ci_", basename(dirname(file)))
  status <- system2(
    "Rscript",
    c(file, "--dry-run", "--out", out_dir, "--run-id", run_id),
    stdout = TRUE,
    stderr = TRUE
  )
  exit_status <- attr(status, "status")
  if (!is.null(exit_status) && exit_status != 0) {
    writeLines(status)
    stop(paste("R dry-run contract failed:", file))
  }
  required <- file.path(out_dir, c("outputs_manifest.yaml", "node_manifest.yaml"))
  if (!all(file.exists(required))) {
    stop(paste("R dry-run did not write required manifests:", file))
  }
}
message("R method contract passed")
