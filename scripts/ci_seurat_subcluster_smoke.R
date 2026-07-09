#!/usr/bin/env Rscript

args_full <- commandArgs(trailingOnly = FALSE)
file_arg <- grep("^--file=", args_full, value = TRUE)
script_dir <- if (length(file_arg) > 0) dirname(sub("^--file=", "", file_arg[[1]])) else "scripts"
repo <- normalizePath(file.path(script_dir, ".."), winslash = "/", mustWork = FALSE)
if (!file.exists(file.path(repo, "code_library"))) repo <- normalizePath(".", winslash = "/", mustWork = TRUE)
module <- file.path(repo, "code_library", "modules", "single_cell", "seurat_subcluster_programs", "main.R")
out <- tempfile("seurat_subcluster_smoke_")
dir.create(out, recursive = TRUE, showWarnings = FALSE)
cmd <- c(module, "--out", out, "--run-id", "seurat_subcluster_smoke_20260709_v1", "--dry-run")
status <- system2("Rscript", cmd, stdout = TRUE, stderr = TRUE)
required <- file.path(out, c(
  "tables/subcluster_cell_counts.csv",
  "tables/subcluster_markers.csv",
  "tables/program_score_summary.csv",
  "figure_source_map.yaml",
  "table_source_map.yaml",
  "logs/sessionInfo.txt"
))
missing <- required[!file.exists(required)]
ok <- length(missing) == 0
cat(paste0(
  "{",
  "\"schema_version\":\"ci_seurat_subcluster_smoke.v1\",",
  "\"status\":\"", if (ok) "pass" else "fail", "\",",
  "\"output_dir\":\"", gsub("\\\\", "/", out), "\",",
  "\"missing_count\":", length(missing),
  "}\n"
))
quit(status = if (ok) 0 else 1)
