#!/usr/bin/env Rscript

args_full <- commandArgs(trailingOnly = FALSE)
file_arg <- grep("^--file=", args_full, value = TRUE)
script_path <- if (length(file_arg) > 0) sub("^--file=", "", file_arg[[1]]) else "code_library/modules/single_cell/seurat_findmarkers_group_de/main.R"
source(file.path(dirname(normalizePath(script_path, winslash = "/", mustWork = TRUE)), "R", "functions.R"))
run_seurat_findmarkers_group_de_cli(commandArgs(trailingOnly = TRUE))
