#!/usr/bin/env Rscript

args_full <- commandArgs(trailingOnly = FALSE)
script_path <- sub("^--file=", "", grep("^--file=", args_full, value = TRUE)[[1]])
common_path <- file.path(dirname(dirname(normalizePath(script_path, winslash = "/", mustWork = TRUE))), "common", "spatial_module_wrapper.R")
source(common_path)
run_spatial_module("spatial.deconvolution_cell2location_or_rctd.v1")
