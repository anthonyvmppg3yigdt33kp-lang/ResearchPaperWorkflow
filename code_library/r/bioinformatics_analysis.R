# =============================================================================
# Bioinformatics Analysis Module — Reusable R functions for research workflows
# Research Paper Workflow Framework v2.0
# =============================================================================
# Designed for agent-callable, parameter-documented, reproducible analysis.
# All paths use {PLACEHOLDER} comments for portability.
# Every function prints a structured message with key results for agent parsing.
#
# DEPENDENCIES (install as needed):
#   Seurat, SeuratObject, SeuratDisk, harmony, WGCNA, GSVA, fgsea,
#   clusterProfiler, org.Hs.eg.db, DESeq2, limma, edgeR, ggplot2,
#   ggrepel, pheatmap, patchwork, dplyr, tibble, Matrix
#
# LOADING: source("C:/Users/HP/Desktop/ResearchPaperWorkflow/code_library/r/bioinformatics_analysis.R")
# =============================================================================


# =============================================================================
# SECTION 0: GLOBAL DEFAULTS & UTILITIES
# =============================================================================

# -- Default paths (override before use) --------------------------------------
DEFAULT_DATA_DIR   <- "{PLACEHOLDER}/data"
DEFAULT_RESULT_DIR <- "{PLACEHOLDER}/results"
DEFAULT_FIGURE_DIR <- "{PLACEHOLDER}/figures"
DEFAULT_SEED       <- 42L

# -- Nature / publication color palettes --------------------------------------
NATURE_REDS    <- c("#C62828", "#EF5350", "#FFCDD2")
NATURE_BLUES   <- c("#0D47A1", "#1565C0", "#42A5F5", "#90CAF9", "#BBDEFB")
NATURE_GREENS  <- c("#1B5E20", "#2E7D32", "#43A047")
NATURE_ORANGES <- c("#E65100", "#EF6C00", "#FF9800")
NATURE_PURPLES <- c("#4A148C", "#6A1B9A", "#8E24AA")
NATURE_DIVERGENT <- c("#1565C0", "#90CAF9", "#F5F5F5", "#FFCDD2", "#C62828")

# -- Utility: set random seed for reproducibility -----------------------------
#' Set random seed across all RNGs used in bioinformatics
#' @param seed Integer seed (default: DEFAULT_SEED = 42)
set_random_seed <- function(seed = DEFAULT_SEED) {
  set.seed(seed)
  if (requireNamespace("Seurat", quietly = TRUE)) {
    # Seurat uses its own RNG; set via options
    options(Seurat.object.assay.version = "v5")
  }
  message(sprintf("Random seed set to %d", seed))
  invisible(seed)
}

# -- Utility: ensure output directory exists ----------------------------------
ensure_dir <- function(path) {
  if (!dir.exists(path)) {
    dir.create(path, recursive = TRUE, showWarnings = FALSE)
  }
  invisible(path)
}

# -- Utility: check & optionally install packages -----------------------------
#' Verify required packages; warn about missing ones
#' @param pkgs Character vector of package names
check_packages <- function(pkgs) {
  installed <- pkgs %in% rownames(installed.packages())
  if (!all(installed)) {
    missing <- pkgs[!installed]
    warning(sprintf("Missing packages: %s", paste(missing, collapse = ", ")))
    message("Install with: install.packages(c('", paste(missing, collapse = "', '"), "'))")
  } else {
    message(sprintf("All %d packages installed.", length(pkgs)))
  }
  invisible(installed)
}


# =============================================================================
# SECTION 1: SEURAT WORKFLOW — QC, Normalization, Integration, Clustering
# =============================================================================

# -- 1a. Standard QC ----------------------------------------------------------
#' Run standard Seurat QC filtering
#'
#' Filters cells by mitochondrial percentage, feature counts, and UMI counts.
#' Adds percent.mt metadata column. Logs retention statistics.
#'
#' @param seurat_obj A Seurat object (v4 or v5)
#' @param mt_pattern  Regex pattern for mitochondrial genes. Human: "^MT-", Mouse: "^mt-"
#' @param max_mt      Maximum mitochondrial percentage (default: 25 for fresh tissue; use 10 for nuclei)
#' @param min_features Minimum nFeature_RNA (default: 200)
#' @param max_features Maximum nFeature_RNA (default: Inf)
#' @param min_counts   Minimum nCount_RNA (default: 500)
#' @param max_counts   Maximum nCount_RNA (default: Inf)
#' @return Filtered Seurat object
#' @export
seurat_qc <- function(seurat_obj,
                      mt_pattern     = "^MT-",
                      max_mt         = 25,
                      min_features   = 200,
                      max_features   = Inf,
                      min_counts     = 500,
                      max_counts     = Inf) {
  library(Seurat)

  initial_cells <- ncol(seurat_obj)

  # Compute MT percentage
  seurat_obj[["percent.mt"]] <- PercentageFeatureSet(seurat_obj, pattern = mt_pattern)

  # Filter
  seurat_obj <- subset(seurat_obj,
    subset = nFeature_RNA > min_features &
             nFeature_RNA < max_features &
             nCount_RNA   > min_counts   &
             nCount_RNA   < max_counts   &
             percent.mt   < max_mt
  )

  retained_cells <- ncol(seurat_obj)
  pct_retained   <- round(100 * retained_cells / initial_cells, 1)

  message(sprintf(
    "[seurat_qc] %d/%d cells retained (%.1f%%) | MT<%.0f%% | %d<nFeature<%s | %d<nCount<%s",
    retained_cells, initial_cells, pct_retained,
    max_mt, min_features, ifelse(is.infinite(max_features), "Inf", as.character(max_features)),
    min_counts,  ifelse(is.infinite(max_counts),  "Inf", as.character(max_counts))
  ))

  return(seurat_obj)
}


# -- 1b. SCTransform Normalization --------------------------------------------
#' Run SCTransform normalization (replaces NormalizeData + ScaleData + FindVariableFeatures)
#'
#' @param seurat_obj      Seurat object
#' @param vars_to_regress Variables to regress out (default: c("percent.mt"))
#' @param vst_flavor      SCTransform v2 flavor: "v2" (default, glmGamPoi) or "v1"
#' @param return_only_var_genes Return only variable genes (default: TRUE)
#' @return Seurat object with SCT assay
#' @export
seurat_sctransform <- function(seurat_obj,
                               vars_to_regress      = c("percent.mt"),
                               vst_flavor           = c("v2", "v1"),
                               return_only_var_genes = TRUE) {
  library(Seurat)
  vst_flavor <- match.arg(vst_flavor)

  seurat_obj <- SCTransform(seurat_obj,
    vst.flavor           = vst_flavor,
    vars.to.regress      = vars_to_regress,
    return.only.var.genes = return_only_var_genes,
    verbose              = FALSE
  )

  message(sprintf(
    "[seurat_sctransform] SCTransform (%s) complete | %d variable features",
    vst_flavor, length(VariableFeatures(seurat_obj))
  ))
  return(seurat_obj)
}


# -- 1c. Harmony Batch Correction ---------------------------------------------
#' Run Harmony integration for batch correction
#'
#' Wraps harmony::RunHarmony. Expects PCA already computed.
#' Harmony corrects for batch effects while preserving biological variation.
#'
#' @param seurat_obj   Seurat object with PCA computed
#' @param batch_var    Column name in meta.data identifying batches
#' @param dims_use     Number of PCs to use (default: 1:30)
#' @param theta        Harmony diversity-clustering penalty (default: 2)
#' @param sigma        Width of soft k-means (default: 0.1)
#' @param max_iter     Maximum Harmony iterations (default: 10)
#' @param assay_use    Assay to use (default: "SCT" or "RNA")
#' @return Seurat object with "harmony" reduction
#' @export
seurat_harmony <- function(seurat_obj,
                           batch_var,
                           dims_use  = 1:30,
                           theta     = 2,
                           sigma     = 0.1,
                           max_iter  = 10,
                           assay_use = NULL) {
  library(Seurat)
  library(harmony)

  if (is.null(assay_use)) {
    assay_use <- if ("SCT" %in% names(seurat_obj@assays)) "SCT" else "RNA"
  }

  seurat_obj <- RunHarmony(seurat_obj,
    group.by.vars = batch_var,
    reduction      = "pca",
    assay.use      = assay_use,
    dims.use       = dims_use,
    theta          = theta,
    sigma          = sigma,
    max.iter.harmony = max_iter,
    verbose        = FALSE
  )

  message(sprintf(
    "[seurat_harmony] Harmony integration on '%s' | dims=%d-%d | theta=%.1f",
    batch_var, min(dims_use), max(dims_use), theta
  ))
  return(seurat_obj)
}


# -- 1d. SCTransform Integration (reference-based) ----------------------------
#' Integrate multiple samples via SCTransform + SelectIntegrationFeatures
#'
#' For multi-sample scRNA-seq, run SCTransform per sample then integrate.
#'
#' @param seurat_list Named list of Seurat objects (one per sample)
#' @param n_features  Number of integration features (default: 3000)
#' @param dims        PC dimensions for integration (default: 1:30)
#' @param k_anchor    k.filter for FindIntegrationAnchors (default: 200)
#' @return Integrated Seurat object
#' @export
seurat_integrate_sct <- function(seurat_list,
                                 n_features = 3000,
                                 dims       = 1:30,
                                 k_anchor   = 200) {
  library(Seurat)

  # SCTransform each sample
  seurat_list <- lapply(seurat_list, function(x) {
    SCTransform(x, vst.flavor = "v2", vars.to.regress = "percent.mt", verbose = FALSE)
  })

  # Select integration features
  features <- SelectIntegrationFeatures(object.list = seurat_list, nfeatures = n_features)

  # Prep and integrate
  seurat_list <- PrepSCTIntegration(object.list = seurat_list, anchor.features = features, verbose = FALSE)
  anchors     <- FindIntegrationAnchors(object.list = seurat_list,
                                        normalization.method = "SCT",
                                        anchor.features = features,
                                        k.filter = k_anchor,
                                        verbose = FALSE)
  integrated  <- IntegrateData(anchorset = anchors, normalization.method = "SCT", verbose = FALSE)

  # PCA + UMAP on integrated
  integrated <- RunPCA(integrated, npcs = max(dims), verbose = FALSE)
  integrated <- RunUMAP(integrated, dims = dims, verbose = FALSE)
  integrated <- FindNeighbors(integrated, dims = dims, verbose = FALSE)

  message(sprintf(
    "[seurat_integrate_sct] %d samples integrated | %d features | %d dims",
    length(seurat_list), n_features, max(dims)
  ))
  return(integrated)
}


# -- 1e. Dimensionality Reduction + Clustering --------------------------------
#' Run PCA, UMAP, FindNeighbors, FindClusters in one call
#'
#' @param seurat_obj  Seurat object
#' @param npcs        Number of PCs to compute (default: 30)
#' @param dims        Dimensions for UMAP/Neighbors/Clustering (default: 1:npcs)
#' @param resolution  Leiden clustering resolution (default: 0.6)
#' @param reduction   Reduction to use for clustering: "pca" or "harmony"
#' @param algorithm   Clustering algorithm: 1=original Louvain, 2=Louvain multilevel, 3=SLM, 4=Leiden
#' @return Seurat object with PCA, UMAP, clusters
#' @export
seurat_cluster <- function(seurat_obj,
                           npcs        = 30,
                           dims        = NULL,
                           resolution  = 0.6,
                           reduction   = c("pca", "harmony"),
                           algorithm   = 4) {
  library(Seurat)
  reduction <- match.arg(reduction)

  if (is.null(dims)) dims <- 1:npcs

  seurat_obj <- RunPCA(seurat_obj, npcs = npcs, verbose = FALSE)
  seurat_obj <- RunUMAP(seurat_obj, dims = dims, reduction = reduction, verbose = FALSE)
  seurat_obj <- FindNeighbors(seurat_obj, dims = dims, reduction = reduction, verbose = FALSE)
  seurat_obj <- FindClusters(seurat_obj, resolution = resolution, algorithm = algorithm, verbose = FALSE)

  n_clusters <- length(unique(seurat_obj$seurat_clusters))
  message(sprintf(
    "[seurat_cluster] %d clusters | resolution=%.2f | npcs=%d | reduction=%s | algorithm=%d",
    n_clusters, resolution, npcs, reduction, algorithm
  ))
  return(seurat_obj)
}


# -- 1f. Pairwise Differential Expression (FindMarkers) -----------------------
#' Run FindMarkers for a single cluster/group comparison
#'
#' @param seurat_obj     Seurat object
#' @param ident_1        Identity class 1 (target group)
#' @param ident_2        Identity class 2 (reference, or NULL for all others)
#' @param group_by       Column to use for grouping (default: "seurat_clusters")
#' @param test_use       Statistical test: "wilcox", "bimod", "roc", "t", "negbinom", "poisson", "LR", "MAST", "DESeq2"
#' @param only_pos       Return only positive markers (default: FALSE)
#' @param logfc_threshold Minimum log2 fold-change threshold (default: 0.25)
#' @param min_pct        Minimum fraction of cells expressing gene in either group (default: 0.1)
#' @return Data frame of DE results
#' @export
seurat_find_markers <- function(seurat_obj,
                                ident_1,
                                ident_2        = NULL,
                                group_by       = "seurat_clusters",
                                test_use       = "wilcox",
                                only_pos       = FALSE,
                                logfc_threshold = 0.25,
                                min_pct        = 0.1) {
  library(Seurat)
  Idents(seurat_obj) <- group_by

  markers <- FindMarkers(seurat_obj,
    ident.1        = ident_1,
    ident.2        = ident_2,
    test.use       = test_use,
    only.pos       = only_pos,
    logfc.threshold = logfc_threshold,
    min.pct        = min_pct,
    verbose        = FALSE
  )

  n_sig <- sum(markers$p_val_adj < 0.05, na.rm = TRUE)
  message(sprintf(
    "[seurat_find_markers] %s vs %s | %d DEGs (%d significant FDR<0.05) | test=%s",
    ident_1, ifelse(is.null(ident_2), "rest", as.character(ident_2)),
    nrow(markers), n_sig, test_use
  ))
  return(markers)
}


# -- 1g. FindAllMarkers -------------------------------------------------------
#' Find markers for all clusters
#'
#' @param seurat_obj     Seurat object
#' @param only_pos       Return only positive markers (default: TRUE)
#' @param logfc_threshold Minimum logFC (default: 0.25)
#' @param min_pct        Minimum expression fraction (default: 0.1)
#' @param test_use       Statistical test (default: "wilcox")
#' @param max_cells_per_ident Down-sample per cluster for speed (default: Inf)
#' @return Data frame of markers with cluster assignments
#' @export
seurat_find_all_markers <- function(seurat_obj,
                                    only_pos        = TRUE,
                                    logfc_threshold  = 0.25,
                                    min_pct         = 0.1,
                                    test_use        = "wilcox",
                                    max_cells_per_ident = Inf) {
  library(Seurat)

  markers <- FindAllMarkers(seurat_obj,
    only.pos          = only_pos,
    logfc.threshold   = logfc_threshold,
    min.pct           = min_pct,
    test.use          = test_use,
    max.cells.per.ident = max_cells_per_ident,
    verbose           = FALSE
  )

  n_clusters <- length(unique(markers$cluster))
  message(sprintf(
    "[seurat_find_all_markers] %d markers across %d clusters | test=%s | logFC>%.2f",
    nrow(markers), n_clusters, test_use, logfc_threshold
  ))
  return(markers)
}


# =============================================================================
# SECTION 2: DIFFERENTIAL EXPRESSION — Pseudobulk (DESeq2, Limma, Wilcoxon)
# =============================================================================

# -- 2a. Pseudobulk aggregation helper ----------------------------------------
#' Aggregate single-cell expression to pseudobulk by sample + cell type
#'
#' Sums raw counts per gene per sample+group combination.
#' This is the recommended input for DESeq2 and limma pseudobulk DE.
#'
#' @param seurat_obj        Seurat object with raw RNA counts
#' @param sample_col        Column identifying biological replicates
#' @param group_col         Column identifying cell types / clusters
#' @param min_cells         Minimum cells per pseudobulk (default: 10)
#' @param assay             Assay to extract counts from (default: "RNA")
#' @param slot              Slot for counts: "counts" for DESeq2, "data" for limma
#' @return List: $count_matrix (genes x pseudobulks), $metadata (data.frame), $pseudobulk_labels
#' @export
pseudobulk_aggregate <- function(seurat_obj,
                                 sample_col,
                                 group_col,
                                 min_cells = 10,
                                 assay     = "RNA",
                                 slot      = "counts") {
  library(Seurat)
  library(Matrix)

  counts <- GetAssayData(seurat_obj, assay = assay, slot = slot)
  meta   <- seurat_obj@meta.data

  pb_list    <- list()
  pb_labels  <- c()
  pb_samples <- c()
  pb_groups  <- c()

  for (s in unique(meta[[sample_col]])) {
    for (g in unique(meta[[group_col]])) {
      cells <- rownames(meta)[meta[[sample_col]] == s & meta[[group_col]] == g]
      if (length(cells) < min_cells) next

      label <- paste(s, g, sep = "_")
      pb_list[[label]]   <- Matrix::rowSums(counts[, cells, drop = FALSE])
      pb_labels          <- c(pb_labels, label)
      pb_samples         <- c(pb_samples, as.character(s))
      pb_groups          <- c(pb_groups, as.character(g))
    }
  }

  pb_matrix <- do.call(cbind, pb_list)
  colnames(pb_matrix) <- pb_labels

  pb_meta <- data.frame(
    pseudobulk = pb_labels,
    sample     = pb_samples,
    group      = pb_groups,
    row.names  = pb_labels,
    stringsAsFactors = FALSE
  )

  message(sprintf(
    "[pseudobulk_aggregate] %d pseudobulks from %d samples x %d groups (min_cells=%d, slot=%s)",
    ncol(pb_matrix), length(unique(pb_samples)), length(unique(pb_groups)),
    min_cells, slot
  ))
  return(list(count_matrix = pb_matrix, metadata = pb_meta, pseudobulk_labels = pb_labels))
}


# -- 2b. DESeq2 Pseudobulk DE -------------------------------------------------
#' Run DESeq2 on pseudobulk-aggregated data
#'
#' Tests differential expression between two conditions within a cell type.
#' Uses DESeq2's Wald test with default size-factor normalization.
#'
#' @param pb_result     Output from pseudobulk_aggregate() with slot="counts"
#' @param condition_col Column in metadata identifying condition (e.g., "treatment")
#' @param reference     Reference level for condition
#' @param target        Target level for condition
#' @param filter_group  Optional: restrict to one cell type group
#' @param alpha         FDR threshold (default: 0.05)
#' @param lfc_threshold Log2 fold-change threshold for s-value / hypothesis testing (default: 0)
#' @return DESeq2 results data frame (as data.frame with gene column)
#' @export
de_deseq2 <- function(pb_result,
                      condition_col,
                      reference,
                      target,
                      filter_group  = NULL,
                      alpha         = 0.05,
                      lfc_threshold = 0) {
  library(DESeq2)

  counts <- pb_result$count_matrix
  meta   <- pb_result$metadata

  # Optionally restrict to one group (one cell-type comparison)
  if (!is.null(filter_group)) {
    keep <- meta$group == filter_group
    counts <- counts[, keep, drop = FALSE]
    meta   <- meta[keep, , drop = FALSE]
  }

  # Ensure condition is a factor with correct reference
  meta[[condition_col]] <- meta$sample  # default: sample IS the condition; customize in meta
  # The caller should have already attached condition info to metadata.
  # We assume condition_col exists in metadata.
  meta[[condition_col]] <- factor(meta[[condition_col]], levels = c(reference, target))

  dds <- DESeqDataSetFromMatrix(
    countData = round(counts),
    colData   = meta,
    design    = as.formula(paste("~", condition_col))
  )

  # Filter low-count genes: at least 10 total counts
  dds <- dds[rowSums(counts(dds)) >= 10, ]

  dds <- DESeq(dds, quiet = TRUE)
  res <- results(dds,
    contrast        = c(condition_col, target, reference),
    alpha           = alpha,
    lfcThreshold    = lfc_threshold
  )
  res <- res[order(res$pvalue), ]
  res_df <- as.data.frame(res)
  res_df$gene <- rownames(res_df)
  rownames(res_df) <- NULL

  n_sig <- sum(res_df$padj < alpha, na.rm = TRUE)
  message(sprintf(
    "[de_deseq2] %s vs %s | %d genes tested | %d DEGs (FDR<%.2f, lfcThreshold=%.1f) | %s",
    target, reference, nrow(res_df), n_sig, alpha, lfc_threshold,
    ifelse(is.null(filter_group), "all groups", paste0("group=", filter_group))
  ))
  return(res_df)
}


# -- 2c. Limma-Voom Pseudobulk DE ---------------------------------------------
#' Run limma-voom on pseudobulk-aggregated data
#'
#' Well-powered for small sample sizes. Uses empirical Bayes moderation.
#'
#' @param pb_result     Output from pseudobulk_aggregate()
#' @param condition_col Column in metadata identifying condition
#' @param reference     Reference level
#' @param target        Target level
#' @param filter_group  Optional: restrict to one group
#' @param block_col     Optional: column for paired design (e.g., patient ID)
#' @param alpha         FDR threshold (default: 0.05)
#' @return Limma topTable as data.frame with gene column
#' @export
de_limma <- function(pb_result,
                     condition_col,
                     reference,
                     target,
                     filter_group  = NULL,
                     block_col     = NULL,
                     alpha         = 0.05) {
  library(limma)
  library(edgeR)

  counts <- pb_result$count_matrix
  meta   <- pb_result$metadata

  if (!is.null(filter_group)) {
    keep <- counts[, meta$group == filter_group, drop = FALSE]
    meta <- meta[meta$group == filter_group, , drop = FALSE]
  }

  meta[[condition_col]] <- factor(meta[[condition_col]], levels = c(reference, target))

  # Design matrix
  if (!is.null(block_col)) {
    design <- model.matrix(as.formula(paste("~ 0 +", condition_col, "+", block_col)), data = meta)
  } else {
    design <- model.matrix(as.formula(paste("~ 0 +", condition_col)), data = meta)
  }
  colnames(design) <- make.names(colnames(design))

  # Voom
  dge <- DGEList(counts = round(counts))
  dge <- dge[filterByExpr(dge, design), , keep.lib.sizes = FALSE]
  dge <- calcNormFactors(dge)
  v   <- voom(dge, design, plot = FALSE)
  fit <- lmFit(v, design)

  # Contrast
  contrast_name <- paste0(condition_col, target)
  ref_name      <- paste0(condition_col, reference)
  contrast_vec  <- setNames(c(1, -1), c(contrast_name, ref_name))

  # Rebuild simpler contrast if design has extra columns
  if (ncol(design) > 2) {
    cm <- makeContrasts(
      contrasts = paste(contrast_name, "-", ref_name),
      levels = design
    )
    fit2 <- contrasts.fit(fit, cm)
  } else {
    cm <- makeContrasts(contrasts = paste(contrast_name, "-", ref_name), levels = design)
    fit2 <- contrasts.fit(fit, cm)
  }

  fit2 <- eBayes(fit2, trend = TRUE, robust = TRUE)
  res  <- topTable(fit2, number = Inf, adjust.method = "BH", sort.by = "P")
  res$gene <- rownames(res)
  rownames(res) <- NULL

  n_sig <- sum(res$adj.P.Val < alpha, na.rm = TRUE)
  message(sprintf(
    "[de_limma] %s vs %s | %d genes tested | %d DEGs (FDR<%.2f) | %spaired",
    target, reference, nrow(res), n_sig, alpha,
    ifelse(is.null(block_col), "un", "")
  ))
  return(res)
}


# -- 2d. Wilcoxon Rank-Sum DE (spatial / single-cell) -------------------------
#' Wilcoxon rank-sum test for two-group comparison on expression matrix
#'
#' Suitable for spatial transcriptomics spots or pseudobulk with moderate n.
#'
#' @param expr_matrix  Genes x samples/observations matrix (or samples x genes; auto-detected)
#' @param group_labels Binary vector (0/1 or FALSE/TRUE) matching columns/rows
#' @param min_expr     Minimum mean expression to test a gene (default: 0.01)
#' @param n_cores      Parallel workers (default: 1)
#' @return Data frame: gene, p_value, log2FC, auc, p_adj
#' @export
de_wilcoxon <- function(expr_matrix,
                        group_labels,
                        min_expr = 0.01,
                        n_cores  = 1) {
  # Auto-detect orientation: if group_labels length matches ncol, genes are rows
  if (length(group_labels) == ncol(expr_matrix)) {
    mat <- expr_matrix
  } else if (length(group_labels) == nrow(expr_matrix)) {
    mat <- t(expr_matrix)
  } else {
    stop(sprintf("group_labels length (%d) does not match rows (%d) or cols (%d) of expr_matrix",
                 length(group_labels), nrow(expr_matrix), ncol(expr_matrix)))
  }

  group_labels <- as.numeric(as.factor(group_labels)) - 1  # ensure 0/1
  group_1 <- which(group_labels == 1)
  group_0 <- which(group_labels == 0)

  if (length(group_1) < 3 || length(group_0) < 3) {
    stop("Each group must have at least 3 observations for Wilcoxon test")
  }

  # Filter low-expression genes
  gene_means <- Matrix::rowMeans(mat)
  keep       <- gene_means >= min_expr
  mat        <- mat[keep, , drop = FALSE]

  results <- data.frame(
    gene     = rownames(mat),
    p_value  = NA_real_,
    log2FC   = NA_real_,
    auc      = NA_real_,
    stringsAsFactors = FALSE
  )

  for (i in seq_len(nrow(mat))) {
    x <- as.numeric(mat[i, group_1])
    y <- as.numeric(mat[i, group_0])

    # Skip if no variation
    if (all(x == x[1]) && all(y == y[1]) && x[1] == y[1]) {
      results$p_value[i] <- 1
      results$log2FC[i]  <- 0
      results$auc[i]     <- 0.5
      next
    }

    test <- suppressWarnings(wilcox.test(x, y, exact = FALSE, conf.int = FALSE))
    results$p_value[i] <- test$p.value

    # Log2FC with pseudocount
    pseudocount <- 0.1
    results$log2FC[i] <- log2(mean(x) + pseudocount) - log2(mean(y) + pseudocount)

    # AUC (rank-biserial)
    n1 <- length(x); n2 <- length(y)
    results$auc[i] <- 1 - (2 * test$statistic) / (n1 * n2)
  }

  results$p_adj <- p.adjust(results$p_value, method = "BH")
  results <- results[order(results$p_value), ]

  n_sig <- sum(results$p_adj < 0.05, na.rm = TRUE)
  message(sprintf(
    "[de_wilcoxon] %d genes tested | %d significant (FDR<0.05) | n_group1=%d, n_group0=%d",
    nrow(results), n_sig, length(group_1), length(group_0)
  ))
  return(results)
}


# =============================================================================
# SECTION 3: PATHWAY ANALYSIS — GSVA, GSEA, clusterProfiler, fgsea
# =============================================================================

# -- 3a. GSVA -----------------------------------------------------------------
#' Run GSVA pathway enrichment on expression matrix
#'
#' @param expr_matrix Expression matrix (genes x samples). Use normalized log-counts.
#' @param gene_sets   Named list of gene sets (each element = character vector of genes)
#' @param method      GSVA method: "gsva", "ssgsea", "zscore", or "plage"
#' @param kcdf        Kernel for CDF estimation: "Gaussian" (microarray/log-norm RNA-seq) or "Poisson" (raw counts)
#' @param min_size    Minimum gene set size (default: 5)
#' @param max_size    Maximum gene set size (default: 500)
#' @param parallel_sz Number of parallel workers (default: 1)
#' @return Matrix of pathway enrichment scores (pathways x samples)
#' @export
run_gsva <- function(expr_matrix,
                     gene_sets,
                     method      = c("gsva", "ssgsea", "zscore", "plage"),
                     kcdf        = c("Gaussian", "Poisson"),
                     min_size    = 5,
                     max_size    = 500,
                     n_cores   = 1) {
  library(GSVA)
  method <- match.arg(method)
  kcdf   <- match.arg(kcdf)

  # Filter gene sets by size
  gs_sizes <- sapply(gene_sets, function(gs) sum(gs %in% rownames(expr_matrix)))
  keep     <- gs_sizes >= min_size & gs_sizes <= max_size
  gene_sets_filt <- gene_sets[keep]

  gsva_result <- gsva(as.matrix(expr_matrix), gene_sets_filt,
    method   = method,
    kcdf     = kcdf,
    mx.diff  = TRUE,
    parallel.sz = n_cores,
    verbose  = FALSE
  )

  message(sprintf(
    "[run_gsva] %d/%d gene sets scored | method=%s | kcdf=%s | range=[%d,%d] genes/set",
    nrow(gsva_result), length(gene_sets), method, kcdf,
    min(gs_sizes[keep]), max(gs_sizes[keep])
  ))
  return(gsva_result)
}


# -- 3b. fgsea (Fast GSEA) ----------------------------------------------------
#' Run fast GSEA using the fgsea algorithm
#'
#' Efficient implementation. Requires pre-ranked gene list.
#'
#' @param ranked_genes Named numeric vector (gene symbols as names, statistic as values). Typically log2FC or t-statistic.
#' @param gene_sets    Named list of gene sets
#' @param min_size     Minimum pathway size (default: 10)
#' @param max_size     Maximum pathway size (default: 500)
#' @param nperm        Number of permutations (default: 10000)
#' @param n_cores      Number of cores (default: 1)
#' @param seed         Random seed (default: DEFAULT_SEED)
#' @return Data table of GSEA results (ordered by padj)
#' @export
run_fgsea <- function(ranked_genes,
                      gene_sets,
                      min_size = 10,
                      max_size = 500,
                      nperm    = 10000,
                      n_cores  = 1,
                      seed     = DEFAULT_SEED) {
  library(fgsea)

  set.seed(seed)
  fgsea_result <- fgsea(
    pathways = gene_sets,
    stats    = ranked_genes,
    minSize  = min_size,
    maxSize  = max_size,
    nperm    = nperm,
    nproc    = n_cores
  )

  # Clean up: collapse leadingEdge for readability if needed by caller
  fgsea_result <- fgsea_result[order(padj), ]

  n_sig <- sum(fgsea_result$padj < 0.05, na.rm = TRUE)
  message(sprintf(
    "[run_fgsea] %d pathways tested | %d significant (FDR<0.05) | nperm=%d | range=[%d,%d]",
    nrow(fgsea_result), n_sig, nperm, min_size, max_size
  ))
  return(fgsea_result)
}


# -- 3c. clusterProfiler ORA (GO + KEGG) --------------------------------------
#' Over-Representation Analysis via clusterProfiler
#'
#' Tests whether a gene list is enriched for specific GO terms or KEGG pathways.
#'
#' @param gene_list    Character vector of gene symbols (DE genes)
#' @param background   Character vector of all expressed genes (universe). If NULL uses all org.Hs.eg.db genes.
#' @param db           Database: "GO_BP", "GO_MF", "GO_CC", or "KEGG"
#' @param organism_db  OrgDb object (default: org.Hs.eg.db)
#' @param pval_cutoff  P-value cutoff (default: 0.05)
#' @param qval_cutoff  Q-value cutoff (default: 0.05)
#' @return enrichResult object
#' @export
run_ora <- function(gene_list,
                    background   = NULL,
                    db           = c("GO_BP", "GO_MF", "GO_CC", "KEGG"),
                    organism_db  = NULL,
                    pval_cutoff  = 0.05,
                    qval_cutoff  = 0.05) {
  library(clusterProfiler)
  db <- match.arg(db)

  if (is.null(organism_db)) {
    if (!requireNamespace("org.Hs.eg.db", quietly = TRUE)) {
      stop("org.Hs.eg.db not installed. Install with: BiocManager::install('org.Hs.eg.db')")
    }
    organism_db <- org.Hs.eg.db
  }

  # Convert SYMBOL to ENTREZID
  entrez_list <- bitr(gene_list, fromType = "SYMBOL", toType = "ENTREZID",
                       OrgDb = organism_db)
  entrez_bg   <- NULL
  if (!is.null(background)) {
    entrez_bg <- bitr(background, fromType = "SYMBOL", toType = "ENTREZID",
                       OrgDb = organism_db)$ENTREZID
  }

  if (db == "KEGG") {
    result <- enrichKEGG(
      gene          = entrez_list$ENTREZID,
      universe      = entrez_bg,
      pAdjustMethod = "BH",
      pvalueCutoff  = pval_cutoff,
      qvalueCutoff  = qval_cutoff
    )
  } else {
    ont <- switch(db,
      "GO_BP" = "BP",
      "GO_MF" = "MF",
      "GO_CC" = "CC"
    )
    result <- enrichGO(
      gene          = entrez_list$ENTREZID,
      universe      = entrez_bg,
      OrgDb         = organism_db,
      ont           = ont,
      pAdjustMethod = "BH",
      pvalueCutoff  = pval_cutoff,
      qvalueCutoff  = qval_cutoff,
      readable      = TRUE
    )
  }

  n_terms <- if (is.null(result)) 0 else nrow(result)
  message(sprintf(
    "[run_ora] %s | %d input genes (%d mapped) | %d enriched terms | p<%.2f, q<%.2f",
    db, length(gene_list), nrow(entrez_list), n_terms, pval_cutoff, qval_cutoff
  ))
  return(result)
}


# -- 3d. clusterProfiler GSEA -------------------------------------------------
#' Gene Set Enrichment Analysis via clusterProfiler::gseGO / gseKEGG
#'
#' Uses ranked gene list (e.g., log2FC-sorted) instead of a cut-off gene list.
#'
#' @param ranked_gene_list Named numeric vector of log2FC (names = SYMBOL)
#' @param db               "GO_BP", "GO_MF", "GO_CC", or "KEGG"
#' @param organism_db      OrgDb (default: org.Hs.eg.db)
#' @param pval_cutoff      P-value cutoff (default: 0.05)
#' @param minGSSize        Minimum gene set size (default: 10)
#' @param maxGSSize        Maximum gene set size (default: 500)
#' @param nPerm            Permutations (default: 10000)
#' @param seed             Random seed
#' @return gseaResult object
#' @export
run_gsea <- function(ranked_gene_list,
                     db          = c("GO_BP", "GO_MF", "GO_CC", "KEGG"),
                     organism_db = NULL,
                     pval_cutoff = 0.05,
                     minGSSize   = 10,
                     maxGSSize   = 500,
                     nPerm       = 10000,
                     seed        = DEFAULT_SEED) {
  library(clusterProfiler)
  db <- match.arg(db)

  if (is.null(organism_db)) {
    if (!requireNamespace("org.Hs.eg.db", quietly = TRUE)) {
      stop("org.Hs.eg.db not installed.")
    }
    organism_db <- org.Hs.eg.db
  }

  # Convert names to ENTREZ and sort by decreasing statistic
  gene_df <- bitr(names(ranked_gene_list), fromType = "SYMBOL", toType = "ENTREZID",
                   OrgDb = organism_db)
  ranked_entrez <- ranked_gene_list[gene_df$SYMBOL]
  names(ranked_entrez) <- gene_df$ENTREZID[match(names(ranked_entrez), gene_df$SYMBOL)]
  ranked_entrez <- sort(ranked_entrez, decreasing = TRUE)

  set.seed(seed)

  if (db == "KEGG") {
    result <- gseKEGG(
      geneList     = ranked_entrez,
      pvalueCutoff = pval_cutoff,
      minGSSize    = minGSSize,
      maxGSSize    = maxGSSize,
      nPermSimple  = nPerm,
      seed         = seed,
      verbose      = FALSE
    )
  } else {
    ont <- switch(db,
      "GO_BP" = "BP",
      "GO_MF" = "MF",
      "GO_CC" = "CC"
    )
    result <- gseGO(
      geneList     = ranked_entrez,
      ont          = ont,
      OrgDb        = organism_db,
      pvalueCutoff = pval_cutoff,
      minGSSize    = minGSSize,
      maxGSSize    = maxGSSize,
      nPermSimple  = nPerm,
      seed         = seed,
      verbose      = FALSE
    )
  }

  n_terms <- if (is.null(result)) 0 else nrow(result)
  message(sprintf(
    "[run_gsea] %s | %d genes ranked | %d enriched terms | nPerm=%d",
    db, length(ranked_entrez), n_terms, nPerm
  ))
  return(result)
}


# =============================================================================
# SECTION 4: WGCNA CO-EXPRESSION NETWORK
# =============================================================================

# -- 4a. Full WGCNA Pipeline --------------------------------------------------
#' Run complete WGCNA analysis: soft-threshold → blockwiseModules
#'
#' @param expr_data       Normalized expression matrix (genes x samples).
#'                        Should be variance-stabilized, filtered for low-count genes.
#' @param power           Soft-thresholding power. NULL = auto-detect via pickSoftThreshold.
#' @param min_module_size Minimum module size (default: 30)
#' @param merge_cut_height Module merging cut height (default: 0.25; lower = fewer merges)
#' @param network_type    "signed", "unsigned", or "signed hybrid"
#' @param max_block_size  Maximum block size for blockwiseModules (default: 25000)
#' @param deep_split      Dynamic tree cut sensitivity 0-4 (default: 2)
#' @param n_threads       Number of threads (default: 0 = auto)
#' @param seed            Random seed
#' @return List: $net (blockwiseModules output), $power (numeric), $colors (module assignments),
#'         $MEs (module eigengenes), $datExpr (expression data used)
#' @export
run_wgcna <- function(expr_data,
                      power            = NULL,
                      min_module_size  = 30,
                      merge_cut_height = 0.25,
                      network_type     = c("signed", "unsigned", "signed hybrid"),
                      max_block_size   = 25000,
                      deep_split       = 2,
                      n_threads        = 0,
                      seed             = DEFAULT_SEED) {
  library(WGCNA)

  network_type <- match.arg(network_type)
  allowWGCNAThreads(nThreads = n_threads)

  # Transpose: WGCNA expects samples x genes
  datExpr <- t(expr_data)

  # QC: remove genes and samples with too many missing values
  gsg <- goodSamplesGenes(datExpr, verbose = 0)
  if (!gsg$allOK) {
    datExpr <- datExpr[gsg$goodSamples, gsg$goodGenes]
    message(sprintf("[run_wgcna] Removed %d samples, %d genes with excess NAs",
                    sum(!gsg$goodSamples), sum(!gsg$goodGenes)))
  }

  # Soft-thresholding
  if (is.null(power)) {
    powers <- c(seq(1, 20, by = 1), seq(22, 30, by = 2))
    sft <- pickSoftThreshold(datExpr, powerVector = powers,
                              networkType = network_type, verbose = 0)
    power <- sft$powerEstimate
    if (is.na(power)) {
      # Fallback: pick power achieving R^2 > 0.8 if available
      idx <- which(sft$fitIndices[, "SFT.R.sq"] > 0.8)
      power <- if (length(idx) > 0) sft$fitIndices[idx[1], "Power"] else 20
      message(sprintf("[run_wgcna] powerEstimate=NA, using fallback power=%d", power))
    }
    message(sprintf("[run_wgcna] Soft-threshold power=%d (R²=%.3f, mean.k=%.1f)",
                    power,
                    sft$fitIndices[which(sft$fitIndices$Power == power), "SFT.R.sq"],
                    sft$fitIndices[which(sft$fitIndices$Power == power), "mean.k."]))
  }

  set.seed(seed)

  # Blockwise modules
  net <- blockwiseModules(datExpr,
    power           = power,
    minModuleSize   = min_module_size,
    mergeCutHeight  = merge_cut_height,
    networkType     = network_type,
    TOMType         = ifelse(network_type == "unsigned", "unsigned", "signed"),
    maxBlockSize    = max_block_size,
    deepSplit       = deep_split,
    numericLabels   = TRUE,
    pamRespectsDendro = FALSE,
    verbose         = 0,
    nThreads        = n_threads
  )

  module_colors <- labels2colors(net$colors)
  module_table  <- table(module_colors)
  n_mods        <- length(unique(module_colors))

  message(sprintf(
    "[run_wgcna] %d modules | sizes: min=%d, max=%d, median=%d | power=%d | network=%s | mergeCut=%.2f",
    n_mods, min(module_table), max(module_table), median(module_table),
    power, network_type, merge_cut_height
  ))

  return(list(
    net      = net,
    power    = power,
    colors   = module_colors,
    MEs      = net$MEs,
    datExpr  = datExpr
  ))
}


# -- 4b. Module-Trait Association --------------------------------------------
#' Calculate module-trait correlations and p-values
#'
#' @param wgcna_result Output from run_wgcna()
#' @param traits       Data frame of traits (samples x traits). Row names must match sample names.
#' @param cor_method   Correlation method: "pearson" or "spearman"
#' @return List: $cor (correlation matrix), $pval (p-value matrix), $heatmap_data (melted)
#' @export
module_trait_correlation <- function(wgcna_result,
                                     traits,
                                     cor_method = c("pearson", "spearman")) {
  library(WGCNA)
  cor_method <- match.arg(cor_method)

  MEs <- wgcna_result$MEs
  n_samples <- nrow(traits)

  # Align samples
  common_samples <- intersect(rownames(MEs), rownames(traits))
  if (length(common_samples) == 0) {
    stop("No common sample names between MEs and traits")
  }
  MEs    <- MEs[common_samples, , drop = FALSE]
  traits <- traits[common_samples, , drop = FALSE]

  module_trait_cor  <- cor(MEs, traits, use = "pairwise.complete.obs", method = cor_method)
  module_trait_pval <- corPvalueStudent(module_trait_cor, length(common_samples))

  n_sig <- sum(module_trait_pval < 0.05)
  message(sprintf(
    "[module_trait_correlation] %d modules x %d traits | %d significant (p<0.05, %s)",
    nrow(module_trait_cor), ncol(module_trait_cor), n_sig, cor_method
  ))

  return(list(
    cor  = module_trait_cor,
    pval = module_trait_pval,
    n_samples = length(common_samples)
  ))
}


# -- 4c. Gene Significance ---------------------------------------------------
#' Calculate gene significance (GS) for each gene-trait pair
#'
#' @param wgcna_result Output from run_wgcna()
#' @param traits       Data frame of traits (samples x traits)
#' @param cor_method   Correlation method
#' @return Data frame: gene, trait, GS (correlation), p_value
#' @export
gene_significance <- function(wgcna_result,
                              traits,
                              cor_method = c("pearson", "spearman")) {
  library(WGCNA)
  cor_method <- match.arg(cor_method)

  datExpr <- wgcna_result$datExpr
  common  <- intersect(rownames(datExpr), rownames(traits))
  datExpr <- datExpr[common, , drop = FALSE]
  traits  <- traits[common, , drop = FALSE]

  gs_list <- list()
  for (trait_name in colnames(traits)) {
    gs <- as.data.frame(cor(datExpr, traits[[trait_name]],
                            use = "pairwise.complete.obs", method = cor_method))
    colnames(gs) <- trait_name
    gs$gene <- rownames(gs)
    gs$trait <- trait_name
    gs_list[[trait_name]] <- gs
  }

  result <- do.call(rbind, gs_list)
  rownames(result) <- NULL
  message(sprintf(
    "[gene_significance] %d genes x %d traits | method=%s",
    ncol(datExpr), ncol(traits), cor_method
  ))
  return(result)
}


# -- 4d. Extract Hub Genes ---------------------------------------------------
#' Extract hub genes per module using module membership (kME)
#'
#' @param wgcna_result Output from run_wgcna()
#' @param kme_threshold Module membership (|kME|) threshold (default: 0.8)
#' @param min_module_genes Minimum genes in module to consider (default: 10)
#' @return Named list: module_color → character vector of hub gene names
#' @export
extract_hub_genes <- function(wgcna_result,
                              kme_threshold     = 0.8,
                              min_module_genes  = 10) {
  library(WGCNA)

  datExpr <- wgcna_result$datExpr
  MEs     <- wgcna_result$MEs
  colors  <- wgcna_result$colors

  kME <- signedKME(datExpr, MEs, corFnc = "bicor")

  hub_genes <- list()
  for (mod in unique(colors)) {
    mod_genes <- colnames(datExpr)[colors == mod]
    if (length(mod_genes) < min_module_genes) next

    kme_col  <- paste0("kME", mod)
    if (!(kme_col %in% colnames(kME))) {
      # Module name may be in a different format; try grepping
      kme_col <- grep(paste0("^kME", gsub("[^A-Za-z0-9]", ".", mod), "$"),
                       colnames(kME), value = TRUE)[1]
      if (is.na(kme_col)) next
    }

    mod_kme <- kME[mod_genes, kme_col, drop = TRUE]
    hub_ids <- names(mod_kme)[abs(mod_kme) > kme_threshold]
    if (length(hub_ids) > 0) {
      hub_genes[[mod]] <- hub_ids
    }
  }

  total_hubs <- sum(vapply(hub_genes, length, integer(1)))
  n_mods     <- length(hub_genes)
  message(sprintf(
    "[extract_hub_genes] %d hub genes across %d modules (|kME|>%.1f, min_size=%d)",
    total_hubs, n_mods, kme_threshold, min_module_genes
  ))
  return(hub_genes)
}


# -- 4e. Export to Cytoscape -------------------------------------------------
#' Export WGCNA network edges for Cytoscape visualization
#'
#' Exports top edges (by topological overlap) for specified modules.
#'
#' @param wgcna_result Output from run_wgcna()
#' @param modules      Character vector of module colors to export ("all" for all modules)
#' @param top_n_edges  Number of top edges per module to export
#' @param output_dir   Output directory (default: DEFAULT_RESULT_DIR)
#' @param prefix       File name prefix
#' @return Invisibly, path to combined edge file
#' @export
export_wgcna_cytoscape <- function(wgcna_result,
                                   modules     = "all",
                                   top_n_edges = 5000,
                                   output_dir  = NULL,
                                   prefix      = "wgcna") {
  library(WGCNA)

  if (is.null(output_dir)) output_dir <- DEFAULT_RESULT_DIR
  ensure_dir(output_dir)

  datExpr <- wgcna_result$datExpr
  net     <- wgcna_result$net
  colors  <- wgcna_result$colors

  if ("all" %in% modules) modules <- unique(colors)

  # Recompute TOM if needed
  TOM <- TOMsimilarityFromExpr(datExpr, power = wgcna_result$power,
                                networkType = "signed", TOMType = "signed",
                                verbose = 0)

  edge_files <- c()
  for (mod in modules) {
    mod_genes <- colnames(datExpr)[colors == mod]
    if (length(mod_genes) < 5) next

    mod_tom <- TOM[mod_genes, mod_genes]
    rownames(mod_tom) <- mod_genes
    colnames(mod_tom) <- mod_genes

    edges <- exportNetworkToCytoscape(mod_tom,
      edgeFile      = NULL,
      nodeFile      = NULL,
      weighted      = TRUE,
      threshold     = 0,
      nodeNames     = mod_genes
    )

    # Limit to top edges
    edges <- edges[order(edges$weight, decreasing = TRUE), ]
    if (nrow(edges) > top_n_edges) edges <- edges[1:top_n_edges, ]

    out_file <- file.path(output_dir, sprintf("%s_%s_edges.tsv", prefix, gsub("[^A-Za-z0-9]", "_", mod)))
    write.table(edges, out_file, sep = "\t", quote = FALSE, row.names = FALSE)
    edge_files <- c(edge_files, out_file)
  }

  message(sprintf(
    "[export_wgcna_cytoscape] %d modules exported to %s (%d files)",
    length(edge_files), output_dir, length(edge_files)
  ))
  invisible(edge_files)
}


# =============================================================================
# SECTION 5: PUBLICATION-GRADE VISUALIZATION (Nature / CNS Style)
# =============================================================================

# -- Central Nature theme -----------------------------------------------------
#' Nature / Cell journal style ggplot2 theme
#'
#' Clean, minimal theme suitable for high-impact journal figures.
#' Font size 8pt, no gridlines, thin axis lines.
#'
#' @param base_size   Base font size (default: 8)
#' @param base_family Font family (default: "sans")
#' @param legend_pos  Legend position (default: "right")
#' @return ggplot2 theme object
#' @export
theme_nature <- function(base_size = 8, base_family = "sans", legend_pos = "right") {
  theme_minimal(base_size = base_size, base_family = base_family) +
    theme(
      panel.grid         = element_blank(),
      axis.line          = element_line(color = "black", size = 0.3),
      axis.ticks         = element_line(color = "black", size = 0.3),
      axis.ticks.length  = unit(0.05, "cm"),
      axis.text          = element_text(color = "black", size = base_size),
      axis.title         = element_text(color = "black", size = base_size + 1),
      legend.position    = legend_pos,
      legend.text        = element_text(size = base_size - 1),
      legend.title       = element_text(size = base_size),
      legend.key.size    = unit(0.4, "cm"),
      plot.title         = element_blank(),
      strip.background   = element_blank(),
      strip.text         = element_text(size = base_size, face = "bold"),
      aspect.ratio       = 1
    )
}


# -- 5a. UMAP / DimPlot -------------------------------------------------------
#' Nature-style UMAP / t-SNE embedding plot
#'
#' @param seurat_obj  Seurat object
#' @param group_by    Column in meta.data to color by
#' @param reduction   Reduction to plot: "umap", "tsne", "pca" (default: "umap")
#' @param colors      Named color vector or palette function. NULL = default ggplot2 colors.
#' @param pt_size     Point size (default: 0.3 for large datasets, 1.0 for small)
#' @param alpha       Point transparency (default: 0.8)
#' @param label       Add cluster labels (default: TRUE for cluster plots)
#' @param repel       Use ggrepel for labels (default: TRUE)
#' @param legend      Show legend (default: TRUE)
#' @return ggplot object
#' @export
plot_umap_nature <- function(seurat_obj,
                             group_by   = "seurat_clusters",
                             reduction  = "umap",
                             colors     = NULL,
                             pt_size    = 0.3,
                             alpha      = 0.8,
                             label      = TRUE,
                             repel      = TRUE,
                             legend     = TRUE) {
  library(Seurat)
  library(ggplot2)

  p <- DimPlot(seurat_obj,
    group.by  = group_by,
    reduction = reduction,
    pt.size   = pt_size,
    cols      = colors,
    label     = label,
    repel     = repel,
    alpha     = alpha
  ) +
    theme_nature() +
    theme(legend.position = if (legend) "right" else "none")

  return(p)
}


# -- 5b. FeaturePlot ----------------------------------------------------------
#' Nature-style feature/gene expression overlay on UMAP
#'
#' @param seurat_obj  Seurat object
#' @param features    Character vector of gene names or metadata column
#' @param reduction   Reduction (default: "umap")
#' @param pt_size     Point size (default: 0.3)
#' @param order       Plot cells in order of expression (default: TRUE)
#' @param ncol        Number of columns for multi-feature layout
#' @param color_low   Low color (default: "grey90")
#' @param color_high  High color (default: "#C62828")
#' @param combine     Combine multiple features into one plot (default: TRUE)
#' @return ggplot or patchwork object
#' @export
plot_feature_nature <- function(seurat_obj,
                                features,
                                reduction   = "umap",
                                pt_size     = 0.3,
                                order       = TRUE,
                                ncol        = NULL,
                                color_low   = "grey90",
                                color_high  = "#C62828",
                                combine     = TRUE) {
  library(Seurat)
  library(ggplot2)

  p <- FeaturePlot(seurat_obj,
    features  = features,
    reduction = reduction,
    pt.size   = pt_size,
    order     = order,
    ncol      = ncol,
    combine   = combine
  ) &
    scale_color_gradientn(colors = c(color_low, color_high)) &
    theme_nature() &
    theme(legend.position = "right")

  return(p)
}


# -- 5c. VlnPlot --------------------------------------------------------------
#' Nature-style violin plot for gene expression across groups
#'
#' @param seurat_obj  Seurat object
#' @param features    Gene name(s) to plot
#' @param group_by    Grouping column (default: "seurat_clusters")
#' @param pt_size     Jitter point size (default: 0, no points)
#' @param colors      Fill colors
#' @param ncol        Facet columns
#' @return ggplot or patchwork object
#' @export
plot_violin_nature <- function(seurat_obj,
                               features,
                               group_by = "seurat_clusters",
                               pt_size  = 0,
                               colors   = NULL,
                               ncol     = NULL) {
  library(Seurat)
  library(ggplot2)

  p <- VlnPlot(seurat_obj,
    features = features,
    group.by = group_by,
    pt.size  = pt_size,
    cols     = colors,
    ncol     = ncol,
    combine  = TRUE
  ) &
    theme_nature() &
    theme(
      axis.text.x = element_text(angle = 45, hjust = 1, size = 7),
      legend.position = "none"
    )

  return(p)
}


# -- 5d. DotPlot --------------------------------------------------------------
#' Nature-style dot plot for marker gene expression
#'
#' @param seurat_obj  Seurat object
#' @param features    Genes to plot
#' @param group_by    Grouping column (default: "seurat_clusters")
#' @param scale       Scale expression (default: TRUE)
#' @param cluster_idents Reorder identities (default: FALSE)
#' @return ggplot object
#' @export
plot_dot_nature <- function(seurat_obj,
                            features,
                            group_by       = "seurat_clusters",
                            scale          = TRUE,
                            cluster_idents = FALSE) {
  library(Seurat)
  library(ggplot2)

  Idents(seurat_obj) <- group_by
  p <- DotPlot(seurat_obj,
    features  = features,
    scale     = scale,
    cluster.idents = cluster_idents
  ) +
    theme_nature() +
    theme(
      axis.text.x = element_text(angle = 45, hjust = 1, size = 7),
      axis.text.y = element_text(size = 7),
      legend.position = "right"
    ) +
    scale_color_gradientn(colors = c("grey90", "#1565C0", "#C62828"))

  return(p)
}


# -- 5e. DoHeatmap ------------------------------------------------------------
#' Nature-style heatmap of top marker genes per cluster
#'
#' @param seurat_obj  Seurat object
#' @param markers     Data frame from FindAllMarkers (optional; if NULL, auto-computes)
#' @param n_top       Number of top genes per cluster (default: 10)
#' @param group_by    Grouping column (default: "seurat_clusters")
#' @param font_size   Font size (default: 7)
#' @return ggplot object
#' @export
plot_doheatmap_nature <- function(seurat_obj,
                                  markers   = NULL,
                                  n_top     = 10,
                                  group_by  = "seurat_clusters",
                                  font_size = 7) {
  library(Seurat)
  library(ggplot2)
  library(dplyr)

  Idents(seurat_obj) <- group_by

  if (is.null(markers)) {
    markers <- FindAllMarkers(seurat_obj, only.pos = TRUE, verbose = FALSE)
  }

  top_genes <- markers %>%
    group_by(cluster) %>%
    slice_max(n = n_top, order_by = avg_log2FC) %>%
    pull(gene) %>%
    unique()

  p <- DoHeatmap(seurat_obj, features = top_genes, size = font_size, angle = 45) +
    theme(
      text = element_text(size = font_size),
      axis.text.y = element_text(size = font_size * 0.8)
    ) +
    NoLegend()

  return(p)
}


# -- 5f. Volcano Plot ---------------------------------------------------------
#' Nature-style volcano plot for differential expression results
#'
#' @param de_results  Data frame with columns: log2FC, p_adj (or padj), and a gene ID column
#' @param gene_col    Column name for gene IDs (default: "gene")
#' @param logfc_col   Column name for log2 fold change (default: "log2FC")
#' @param padj_col    Column name for adjusted p-value (default: "p_adj")
#' @param label_genes Specific genes to label (character vector)
#' @param n_label     If label_genes is NULL, label this many top genes (default: 10)
#' @param fc_cutoff   Fold-change cutoff for coloring (default: 0.5)
#' @param alpha_cutoff Significance cutoff (default: 0.05)
#' @param title       Optional plot title
#' @param max_overlaps Max overlaps for ggrepel labels (default: 20)
#' @return ggplot object
#' @export
plot_volcano_nature <- function(de_results,
                                gene_col    = "gene",
                                logfc_col   = "log2FC",
                                padj_col    = "p_adj",
                                label_genes = NULL,
                                n_label     = 10,
                                fc_cutoff   = 0.5,
                                alpha_cutoff = 0.05,
                                title       = NULL,
                                max_overlaps = 20) {
  library(ggplot2)
  library(ggrepel)

  # Standardize column names internally
  df <- de_results
  df$log2FC  <- df[[logfc_col]]
  df$p_adj   <- df[[padj_col]]
  df$gene_id <- df[[gene_col]]

  df$sig <- "NS"
  df$sig[df$p_adj < alpha_cutoff & df$log2FC > fc_cutoff]   <- "Up"
  df$sig[df$p_adj < alpha_cutoff & df$log2FC < -fc_cutoff]  <- "Down"
  df$neg_log10_p <- -log10(pmax(df$p_adj, 1e-300))

  sig_colors <- c(
    "Up"    = "#C62828",
    "Down"  = "#1565C0",
    "NS"    = "grey70"
  )

  p <- ggplot(df, aes(x = log2FC, y = neg_log10_p, color = sig)) +
    geom_point(size = 0.8, alpha = 0.6) +
    scale_color_manual(values = sig_colors) +
    theme_nature() +
    theme(legend.position = "none") +
    xlab(expression(log[2] * "(Fold Change)")) +
    ylab(expression(-log[10] * "(adjusted P)"))

  if (!is.null(title)) p <- p + ggtitle(title)

  # Label genes
  if (!is.null(label_genes)) {
    label_data <- df[df$gene_id %in% label_genes, ]
  } else {
    df_sig <- df[df$sig != "NS", ]
    df_sig <- df_sig[order(df_sig$p_adj), ]
    label_data <- head(df_sig, n_label)
  }

  if (nrow(label_data) > 0) {
    p <- p + geom_text_repel(
      data          = label_data,
      aes(label     = gene_id),
      size          = 2.5,
      max.overlaps  = max_overlaps,
      show.legend   = FALSE,
      box.padding   = 0.3,
      point.padding = 0.2
    )
  }

  return(p)
}


# -- 5g. Static Heatmap (pheatmap) --------------------------------------------
#' Nature-style static heatmap via pheatmap
#'
#' @param expr_matrix     Expression matrix (genes x samples, already scaled)
#' @param annotation_col  Column annotation data frame (sample annotations)
#' @param annotation_row  Row annotation data frame (gene annotations)
#' @param color_palette   Vector of colors for heatmap gradient
#' @param show_rownames   Show gene names (default: FALSE for large matrices)
#' @param show_colnames   Show sample names (default: FALSE)
#' @param cluster_rows    Cluster rows (default: TRUE)
#' @param cluster_cols    Cluster columns (default: TRUE)
#' @param fontsize        Base font size (default: 8)
#' @param treeheight_row  Row dendrogram height (default: 15)
#' @param treeheight_col  Column dendrogram height (default: 15)
#' @param main            Title (default: NULL)
#' @param filename        Save to file (default: NULL, plot to device)
#' @param width           Output width in inches (default: 8)
#' @param height          Output height in inches (default: 6)
#' @return pheatmap object (invisibly)
#' @export
plot_heatmap_nature <- function(expr_matrix,
                                annotation_col  = NULL,
                                annotation_row  = NULL,
                                color_palette   = NULL,
                                show_rownames   = FALSE,
                                show_colnames   = FALSE,
                                cluster_rows    = TRUE,
                                cluster_cols    = TRUE,
                                fontsize        = 8,
                                treeheight_row  = 15,
                                treeheight_col  = 15,
                                main            = NULL,
                                filename        = NULL,
                                width           = 8,
                                height          = 6) {
  library(pheatmap)

  if (is.null(color_palette)) {
    color_palette <- colorRampPalette(c("#1565C0", "#F5F5F5", "#C62828"))(100)
  }

  p <- pheatmap(expr_matrix,
    color              = color_palette,
    annotation_col     = annotation_col,
    annotation_row     = annotation_row,
    show_rownames      = show_rownames,
    show_colnames      = show_colnames,
    cluster_rows       = cluster_rows,
    cluster_cols       = cluster_cols,
    fontsize           = fontsize,
    fontsize_row       = fontsize - 1,
    fontsize_col       = fontsize - 1,
    treeheight_row     = treeheight_row,
    treeheight_col     = treeheight_col,
    main               = main,
    border_color       = NA,
    filename           = filename,
    width              = width,
    height             = height,
    silent             = !is.null(filename)
  )

  invisible(p)
}


# -- 5h. Module-Trait Heatmap -------------------------------------------------
#' WGCNA module-trait correlation heatmap
#'
#' @param mt_result  Output from module_trait_correlation()
#' @param filename   Save path (NULL = plot to device)
#' @return pheatmap object (invisibly)
#' @export
plot_module_trait_heatmap <- function(mt_result, filename = NULL) {
  library(pheatmap)

  cor_mat  <- mt_result$cor
  pval_mat <- mt_result$pval

  # Build significance annotation text
  sig_text <- matrix("", nrow = nrow(cor_mat), ncol = ncol(cor_mat))
  sig_text[pval_mat < 0.05]  <- "*"
  sig_text[pval_mat < 0.01]  <- "**"
  sig_text[pval_mat < 0.001] <- "***"
  rownames(sig_text) <- rownames(cor_mat)
  colnames(sig_text) <- colnames(cor_mat)

  p <- pheatmap(cor_mat,
    color             = colorRampPalette(c("#1565C0", "white", "#C62828"))(100),
    display_numbers   = sig_text,
    fontsize_number   = 10,
    fontsize          = 8,
    fontsize_row      = 8,
    fontsize_col      = 8,
    treeheight_row    = 10,
    treeheight_col    = 10,
    cluster_rows      = TRUE,
    cluster_cols      = TRUE,
    border_color      = "grey80",
    main              = "Module-Trait Correlations",
    filename          = filename,
    width             = max(8, ncol(cor_mat) * 1.2),
    height            = max(6, nrow(cor_mat) * 0.5),
    silent            = !is.null(filename)
  )

  invisible(p)
}


# -- 5i. Save ggplot with Nature specs ----------------------------------------
#' Save a ggplot object at publication resolution
#'
#' @param plot      ggplot object
#' @param filename  Output file path (extension determines format: .pdf, .png, .tiff, .svg)
#' @param width     Width in inches (default: 4)
#' @param height    Height in inches (default: 4)
#' @param dpi       Resolution for raster formats (default: 300)
#' @param device    Output device (auto-detected from extension if NULL)
#' @export
save_nature_plot <- function(plot,
                             filename,
                             width   = 4,
                             height  = 4,
                             dpi     = 300,
                             device  = NULL) {
  ensure_dir(dirname(filename))

  ext <- tolower(tools::file_ext(filename))
  if (is.null(device)) {
    device <- switch(ext,
      pdf  = "pdf",
      png  = "png",
      tiff = "tiff",
      tif  = "tiff",
      svg  = "svg",
      jpg  = "jpeg",
      jpeg = "jpeg",
      stop("Unknown file extension: ", ext)
    )
  }

  ggsave(filename, plot = plot, device = device,
         width = width, height = height, dpi = dpi,
         bg = "white")

  message(sprintf("[save_nature_plot] Saved: %s (%.1f x %.1f in, %d DPI, %s)",
                  filename, width, height, dpi, device))
}


# =============================================================================
# SECTION 6: DATA I/O HELPERS
# =============================================================================

# -- 6a. Read 10X Genomics output ---------------------------------------------
#' Read 10X Genomics Cell Ranger output into a Seurat object
#'
#' @param data_dir   Path to Cell Ranger "outs/filtered_feature_bc_matrix" directory
#' @param project    Project name for the Seurat object (default: basename of parent dir)
#' @param min_cells  Include genes detected in at least this many cells (default: 3)
#' @param min_features Include cells with at least this many genes (default: 200)
#' @return Seurat object with raw RNA counts
#' @export
read_10x <- function(data_dir,
                     project     = NULL,
                     min_cells   = 3,
                     min_features = 200) {
  library(Seurat)

  if (!dir.exists(data_dir)) {
    stop(sprintf("[read_10x] Directory not found: %s", data_dir))
  }

  if (is.null(project)) {
    project <- basename(dirname(dirname(data_dir)))  # typically the sample name
  }

  counts <- Read10X(data.dir = data_dir)
  seurat_obj <- CreateSeuratObject(
    counts      = counts,
    project     = project,
    min.cells   = min_cells,
    min.features = min_features
  )

  message(sprintf(
    "[read_10x] %s | %d genes x %d cells | min_cells=%d, min_features=%d",
    project, nrow(seurat_obj), ncol(seurat_obj), min_cells, min_features
  ))
  return(seurat_obj)
}


# -- 6b. Safe RDS read/write --------------------------------------------------
#' Safe read of RDS files with error handling
#' @param path Path to .rds file
#' @return Deserialized R object
#' @export
safe_read_rds <- function(path) {
  if (!file.exists(path)) {
    stop(sprintf("[safe_read_rds] File not found: %s", path))
  }
  obj <- tryCatch(
    readRDS(path),
    error = function(e) stop(sprintf("[safe_read_rds] Error reading %s: %s", path, e$message))
  )
  message(sprintf("[safe_read_rds] Loaded: %s (%.2f MB)", path, file.size(path) / 1e6))
  return(obj)
}

#' Safe write of RDS files with directory creation
#' @param obj  R object to save
#' @param path Output file path
#' @export
safe_write_rds <- function(obj, path) {
  ensure_dir(dirname(path))
  tryCatch(
    saveRDS(obj, path),
    error = function(e) stop(sprintf("[safe_write_rds] Error writing %s: %s", path, e$message))
  )
  message(sprintf("[safe_write_rds] Saved: %s", path))
}


# -- 6c. Seurat <-> h5ad (Scanpy) conversion ----------------------------------
#' Convert Seurat object to h5ad (for Scanpy interop)
#'
#' @param seurat_obj Seurat object
#' @param path       Output .h5ad file path
#' @param assay      Assay to export (default: "RNA")
#' @export
seurat_to_h5ad <- function(seurat_obj, path, assay = "RNA") {
  library(SeuratDisk)

  temp_h5seurat <- tempfile(fileext = ".h5Seurat")
  on.exit(unlink(temp_h5seurat), add = TRUE)

  DefaultAssay(seurat_obj) <- assay
  SaveH5Seurat(seurat_obj, filename = temp_h5seurat, overwrite = TRUE)
  Convert(temp_h5seurat, dest = "h5ad", assay = assay, overwrite = TRUE)

  h5ad_from <- sub("\\.h5Seurat$", ".h5ad", temp_h5seurat)
  if (file.exists(path)) file.remove(path)
  file.rename(h5ad_from, path)
  # Also rename the directory that SeuratDisk creates (.h5seurat -> .h5ad dir)
  h5ad_dir_from <- paste0(sub("\\.h5Seurat$", "", temp_h5seurat), ".h5ad")
  h5ad_dir_to   <- paste0(tools::file_path_sans_ext(path), ".h5ad")
  if (dir.exists(h5ad_dir_from)) {
    if (dir.exists(h5ad_dir_to)) unlink(h5ad_dir_to, recursive = TRUE)
    file.rename(h5ad_dir_from, h5ad_dir_to)
  }

  message(sprintf("[seurat_to_h5ad] Exported: %s", path))
}


#' Read h5ad (Scanpy) file into Seurat
#'
#' WARNING: This writes a temporary .h5Seurat file. The function handles cleanup.
#' Requires SeuratDisk.
#'
#' @param path   Path to .h5ad file
#' @param assay  Assay name (default: "RNA")
#' @return Seurat object
#' @export
h5ad_to_seurat <- function(path, assay = "RNA") {
  library(SeuratDisk)

  if (!file.exists(path)) {
    stop(sprintf("[h5ad_to_seurat] File not found: %s", path))
  }

  temp_h5seurat <- tempfile(fileext = ".h5Seurat")
  on.exit(unlink(temp_h5seurat), add = TRUE)

  Convert(path, dest = "h5Seurat", assay = assay, overwrite = TRUE)
  seurat_obj <- LoadH5Seurat(temp_h5seurat, assays = assay)

  message(sprintf("[h5ad_to_seurat] Loaded: %s | %d genes x %d cells",
                  path, nrow(seurat_obj), ncol(seurat_obj)))
  return(seurat_obj)
}


# -- 6d. Export data frames to CSV --------------------------------------------
#' Export data frame to CSV with standardised settings
#'
#' @param df          Data frame
#' @param path        Output .csv path
#' @param row.names   Write row names (default: FALSE)
#' @export
export_csv <- function(df, path, row.names = FALSE) {
  ensure_dir(dirname(path))
  write.csv(df, path, row.names = row.names, quote = FALSE)
  message(sprintf("[export_csv] %d rows x %d cols → %s", nrow(df), ncol(df), path))
}


# =============================================================================
# SECTION 7: STATISTICAL TESTING
# =============================================================================

#' Mann-Whitney U / Wilcoxon Rank-Sum test with effect size
#'
#' Returns p-value, rank-biserial correlation r, confidence interval.
#'
#' @param x            Numeric vector (group 1)
#' @param y            Numeric vector (group 2)
#' @param conf_level   Confidence level for CI (default: 0.95)
#' @param alternative  "two.sided", "greater", or "less"
#' @return Named list: p_value, effect_size_r (rank-biserial correlation),
#'         ci_low, ci_high, statistic (W), n1, n2
#' @export
mw_test <- function(x, y, conf_level = 0.95, alternative = c("two.sided", "greater", "less")) {
  alternative <- match.arg(alternative)

  test <- wilcox.test(x, y, exact = FALSE, conf.int = TRUE,
                       conf.level = conf_level, alternative = alternative)

  n1 <- length(x)
  n2 <- length(y)

  # Rank-biserial correlation r = 1 - (2W) / (n1 * n2) for two-sided
  r <- 1 - (2 * test$statistic) / (n1 * n2)

  list(
    p_value       = test$p.value,
    effect_size_r = r,
    ci_low        = test$conf.int[1],
    ci_high       = test$conf.int[2],
    statistic_W   = as.numeric(test$statistic),
    n1            = n1,
    n2            = n2,
    alternative   = alternative
  )
}


#' Cohen's d (standardized mean difference)
#'
#' @param x Numeric vector (group 1)
#' @param y Numeric vector (group 2)
#' @param hedges_correction Apply Hedges' g small-sample correction (default: TRUE)
#' @return Numeric: Cohen's d (or Hedges' g if corrected)
#' @export
cohens_d <- function(x, y, hedges_correction = TRUE) {
  nx <- length(x)
  ny <- length(y)

  if (nx < 2 || ny < 2) {
    warning("Need at least 2 observations per group for Cohen's d")
    return(NA_real_)
  }

  # Pooled standard deviation
  sp <- sqrt(((nx - 1) * var(x) + (ny - 1) * var(y)) / (nx + ny - 2))
  d  <- (mean(x) - mean(y)) / sp

  if (hedges_correction) {
    # Hedges' g correction factor
    df <- nx + ny - 2
    J  <- 1 - (3 / (4 * df - 1))  # approximation
    d  <- d * J
  }

  return(d)
}


#' Hedges' g (small-sample corrected effect size)
#'
#' Alias for cohens_d with hedges_correction = TRUE.
#'
#' @param x Numeric vector (group 1)
#' @param y Numeric vector (group 2)
#' @return Hedges' g
#' @export
hedges_g <- function(x, y) {
  cohens_d(x, y, hedges_correction = TRUE)
}


#' Benjamini-Hochberg FDR correction
#'
#' @param p_values Numeric vector of raw p-values
#' @param alpha    Significance threshold (default: 0.05)
#' @return List: p_adj (adjusted p-values), n_sig (count at alpha), alpha
#' @export
bh_correct <- function(p_values, alpha = 0.05) {
  p_adj <- p.adjust(p_values, method = "BH")
  n_sig <- sum(p_adj < alpha, na.rm = TRUE)
  message(sprintf("[bh_correct] %d / %d significant at FDR < %.2f", n_sig, length(p_values), alpha))
  list(p_adj = p_adj, n_sig = n_sig, alpha = alpha)
}


#' Bonferroni correction
#'
#' @param p_values Numeric vector of raw p-values
#' @param alpha    Family-wise error rate (default: 0.05)
#' @return List: p_adj, n_sig, alpha
#' @export
bonferroni_correct <- function(p_values, alpha = 0.05) {
  p_adj <- p.adjust(p_values, method = "bonferroni")
  n_sig <- sum(p_adj < alpha, na.rm = TRUE)
  message(sprintf("[bonferroni_correct] %d / %d significant at FWER < %.2f", n_sig, length(p_values), alpha))
  list(p_adj = p_adj, n_sig = n_sig, alpha = alpha)
}


# -- Batch effect quantification ----------------------------------------------
#' Quantify batch effects via principal variance component analysis (PVCA)
#'
#' Computes variance explained by batch vs biology using lme4 + variancePartition.
#' Useful for assessing batch correction effectiveness.
#'
#' @param expr_matrix Genes x samples expression matrix
#' @param meta        Data frame of sample metadata
#' @param batch_var   Column name for batch
#' @param bio_var     Column name for biological variable of interest
#' @param n_pcs       Number of PCs to use (default: 10)
#' @return Data frame of variance fractions
#' @export
batch_variance_explained <- function(expr_matrix,
                                     meta,
                                     batch_var,
                                     bio_var,
                                     n_pcs = 10) {
  if (!requireNamespace("variancePartition", quietly = TRUE)) {
    stop("variancePartition not installed. BiocManager::install('variancePartition')")
  }
  library(variancePartition)

  # PCA reduction
  pca <- prcomp(t(expr_matrix), center = TRUE, scale. = TRUE)
  pca_mat <- pca$x[, 1:min(n_pcs, ncol(pca$x)), drop = FALSE]
  rownames(pca_mat) <- colnames(expr_matrix)

  # Check alignment
  common <- intersect(rownames(pca_mat), rownames(meta))
  pca_mat <- pca_mat[common, ]
  meta    <- meta[common, ]

  form <- as.formula(paste("~ (1|", batch_var, ") + (1|", bio_var, ")"))
  varPart <- fitExtractVarPartModel(pca_mat, form, meta)

  message(sprintf(
    "[batch_variance_explained] %d samples, %d PCs | batch='%s', bio='%s'",
    length(common), ncol(pca_mat), batch_var, bio_var
  ))
  return(varPart)
}


# =============================================================================
# SECTION 8: SESSION INFO & REPRODUCIBILITY
# =============================================================================

#' Capture full session info for reproducibility
#'
#' Writes R version, platform, and all loaded package versions to a file.
#'
#' @param output_path Path to write sessionInfo() report (NULL = print to console)
#' @param include_packages Also print installed.packages() snapshot (default: FALSE)
#' @return Character vector (invisibly), the sessionInfo output
#' @export
capture_session <- function(output_path = NULL, include_packages = FALSE) {
  si <- sessionInfo()
  report <- capture.output({
    cat("=== Analysis Date ===\n")
    cat(format(Sys.time(), "%Y-%m-%d %H:%M:%S %Z"), "\n\n")
    cat("=== Working Directory ===\n")
    cat(getwd(), "\n\n")
    print(si)
    if (include_packages) {
      cat("\n=== All Installed Packages ===\n")
      ip <- as.data.frame(installed.packages()[, c("Package", "Version", "Built")],
                           stringsAsFactors = FALSE)
      print(ip, row.names = FALSE)
    }
  })

  if (!is.null(output_path)) {
    ensure_dir(dirname(output_path))
    writeLines(report, output_path)
    message(sprintf("[capture_session] Session info saved: %s", output_path))
  }

  invisible(report)
}


# =============================================================================
# MODULE LOAD COMPLETE
# =============================================================================

message("================================================================")
message("Bioinformatics Analysis Module v2.0 loaded.")
message("================================================================")
message("Core workflows:")
message("  1. Seurat:    seurat_qc, seurat_sctransform, seurat_harmony,")
message("                seurat_integrate_sct, seurat_cluster,")
message("                seurat_find_markers, seurat_find_all_markers")
message("  2. DE:        pseudobulk_aggregate, de_deseq2, de_limma, de_wilcoxon")
message("  3. Pathway:   run_gsva, run_fgsea, run_ora, run_gsea")
message("  4. WGCNA:     run_wgcna, module_trait_correlation,")
message("                gene_significance, extract_hub_genes,")
message("                export_wgcna_cytoscape")
message("  5. Viz:       theme_nature, plot_umap_nature, plot_feature_nature,")
message("                plot_violin_nature, plot_dot_nature,")
message("                plot_doheatmap_nature, plot_volcano_nature,")
message("                plot_heatmap_nature, plot_module_trait_heatmap,")
message("                save_nature_plot")
message("  6. I/O:       read_10x, safe_read_rds, safe_write_rds,")
message("                seurat_to_h5ad, h5ad_to_seurat, export_csv")
message("  7. Stats:     mw_test, cohens_d, hedges_g, bh_correct,")
message("                bonferroni_correct, batch_variance_explained")
message("  8. Utils:     set_random_seed, check_packages, ensure_dir,")
message("                capture_session")
message("================================================================")
message("Set paths before use:")
message("  DEFAULT_DATA_DIR, DEFAULT_RESULT_DIR, DEFAULT_FIGURE_DIR")
message("================================================================")
