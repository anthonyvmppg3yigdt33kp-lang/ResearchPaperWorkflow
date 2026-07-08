#!/usr/bin/env Rscript

args_full <- commandArgs(trailingOnly = FALSE)
script_path <- sub("^--file=", "", grep("^--file=", args_full, value = TRUE)[[1]])
modules_root <- dirname(dirname(dirname(normalizePath(script_path, winslash = "/", mustWork = TRUE))))
common_path <- file.path(modules_root, "spatial", "common", "spatial_module_wrapper.R")
source(common_path)
run_spatial_module("single_cell.cellchat_communication.v1")
