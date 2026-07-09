#!/usr/bin/env Rscript
args <- commandArgs(trailingOnly = TRUE)
get_arg <- function(flag, default = "") {
  idx <- which(args == flag)
  if (length(idx) == 0 || idx[length(idx)] == length(args)) {
    return(default)
  }
  args[idx[length(idx)] + 1]
}
out_dir <- get_arg("--out", "generic_scaffold_out")
run_id <- get_arg("--run-id", "generic_scaffold")
dir.create(out_dir, recursive = TRUE, showWarnings = FALSE)
if ("--dry-run" %in% args) {
  writeLines(c(
    "schema_version: generic_scaffold_outputs.v1",
    paste0("run_id: ", run_id),
    "status: dry_run_completed",
    "outputs: []"
  ), file.path(out_dir, "outputs_manifest.yaml"))
  writeLines(c(
    "schema_version: generic_scaffold_node.v1",
    paste0("run_id: ", run_id),
    "status: dry_run_completed",
    "claim_boundary: scaffold only; real execution requires manual implementation"
  ), file.path(out_dir, "node_manifest.yaml"))
  quit(status = 0)
}
stop("generic scaffold requires manual implementation before execution")
