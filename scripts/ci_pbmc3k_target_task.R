#!/usr/bin/env Rscript

repo <- normalizePath(".", winslash = "/", mustWork = TRUE)
script <- file.path(repo, "scripts", "ci_pbmc3k_target_task.py")
out <- system2("python", c(script, "--json"), stdout = TRUE, stderr = TRUE)
cat(paste(out, collapse = "\n"), "\n", sep = "")
status_line <- paste(out, collapse = "\n")
quit(status = if (grepl('"status"\\s*:\\s*"pass"', status_line)) 0 else 1)
