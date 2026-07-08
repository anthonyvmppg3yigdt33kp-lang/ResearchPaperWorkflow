#!/usr/bin/env Rscript

args_full <- commandArgs(trailingOnly = FALSE)
script_path <- sub("^--file=", "", grep("^--file=", args_full, value = TRUE)[[1]])
common_path <- file.path(dirname(dirname(normalizePath(script_path, winslash = "/", mustWork = TRUE))), "common", "sc_module_wrapper.R")
source(common_path)
run_sc_module("single_cell.pseudobulk_deseq2.v1")
