#!/usr/bin/env Rscript

args <- commandArgs(trailingOnly = TRUE)
get_arg <- function(flag, default = "") {
  idx <- which(args == flag)
  if (length(idx) == 0 || idx[length(idx)] == length(args)) return(default)
  args[idx[length(idx)] + 1]
}
has_flag <- function(flag) flag %in% args
split_csv <- function(value) trimws(strsplit(value, ",", fixed = TRUE)[[1]])
json_array <- function(values) paste0("[", paste(sprintf('\"%s\"', values), collapse = ","), "]")

packages_arg <- get_arg("--packages", "Seurat,SeuratObject,Matrix,ggplot2")
packages <- split_csv(packages_arg)
packages <- packages[nzchar(packages)]
missing <- packages[!vapply(packages, requireNamespace, quietly = TRUE, FUN.VALUE = logical(1))]
status <- if (length(missing) == 0) "pass" else "blocked"
payload <- paste0(
  "{",
  "\"schema_version\":\"r_environment_check.v1\",",
  "\"status\":\"", status, "\",",
  "\"r_version\":\"", paste(R.version$major, R.version$minor, sep = "."), "\",",
  "\"required_packages\":", json_array(packages), ",",
  "\"missing_packages\":", json_array(missing),
  "}"
)
if (has_flag("--json")) {
  cat(payload, "\n", sep = "")
} else {
  cat("R environment status:", status, "\n")
  if (length(missing) > 0) cat("Missing:", paste(missing, collapse = ", "), "\n")
}
quit(status = if (status == "pass") 0 else 1)
