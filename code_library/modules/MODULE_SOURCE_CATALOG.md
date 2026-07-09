# Method Source Catalog

This catalog is the clickable source index for `code_library/modules`.
Each entry identifies the script a researcher can inspect, delegated common wrappers, purpose, execution type, maturity, and current publication boundary.

## bulk_rnaseq.deseq2_de.v1

- Name: Publication-oriented DESeq2 differential expression
- Purpose/use: bulk RNA-seq group contrast; replicate-level association testing
- Modality/step/language: bulk_rnaseq / deseq2_de / r
- Primary script: `code_library/modules/bulk_rnaseq/deseq2_de/main.R`
- Auditable scripts: `code_library/modules/bulk_rnaseq/deseq2_de/main.R`, `code_library/modules/bulk_rnaseq/common/bulk_module_wrapper.R`
- Functions in primary script: delegated or script-level workflow
- Execution type: rscript
- Environment lock: `code_library/env_locks/r_bulk_rnaseq.lock.yaml` status=True
- Maturity/validation: validated_publication_oriented_wrapper / publication_oriented_dry_run_verified
- Claim boundary: Publication-oriented association testing only; causal or mechanism claims require validation.

## bulk_rnaseq.fgsea_enrichment.v1

- Name: Publication-oriented fgsea enrichment
- Purpose/use: ranked gene enrichment; pathway association
- Modality/step/language: bulk_rnaseq / fgsea_enrichment / r
- Primary script: `code_library/modules/bulk_rnaseq/fgsea_enrichment/main.R`
- Auditable scripts: `code_library/modules/bulk_rnaseq/fgsea_enrichment/main.R`, `code_library/modules/bulk_rnaseq/common/bulk_module_wrapper.R`
- Functions in primary script: delegated or script-level workflow
- Execution type: rscript
- Environment lock: `code_library/env_locks/r_bulk_rnaseq.lock.yaml` status=True
- Maturity/validation: validated_publication_oriented_wrapper / publication_oriented_dry_run_verified
- Claim boundary: Pathway enrichment is interpretive and depends on the ranked statistic and gene-set database.

## bulk_rnaseq.immune_deconvolution_adapter.v1

- Name: Immune deconvolution adapter contract
- Purpose/use: immune fraction estimation; sample-level immune composition
- Modality/step/language: bulk_rnaseq / immune_deconvolution_adapter / r
- Primary script: `code_library/modules/bulk_rnaseq/immune_deconvolution_adapter/main.R`
- Auditable scripts: `code_library/modules/bulk_rnaseq/immune_deconvolution_adapter/main.R`, `code_library/modules/bulk_rnaseq/common/bulk_module_wrapper.R`
- Functions in primary script: delegated or script-level workflow
- Execution type: rscript
- Environment lock: `code_library/env_locks/r_bulk_rnaseq.lock.yaml` status=True
- Maturity/validation: adapter_contract / publication_oriented_dry_run_verified
- Claim boundary: Cell-fraction deconvolution is model-based estimation and requires orthogonal validation.

## bulk_rnaseq.limma_voom_de.v1

- Name: Publication-oriented limma-voom differential expression
- Purpose/use: bulk RNA-seq group contrast; paired or blocked design
- Modality/step/language: bulk_rnaseq / limma_voom_de / r
- Primary script: `code_library/modules/bulk_rnaseq/limma_voom_de/main.R`
- Auditable scripts: `code_library/modules/bulk_rnaseq/limma_voom_de/main.R`, `code_library/modules/bulk_rnaseq/common/bulk_module_wrapper.R`
- Functions in primary script: delegated or script-level workflow
- Execution type: rscript
- Environment lock: `code_library/env_locks/r_bulk_rnaseq.lock.yaml` status=True
- Maturity/validation: validated_publication_oriented_wrapper / publication_oriented_dry_run_verified
- Claim boundary: Publication-oriented association testing; design matrix and covariates must be reviewed.

## bulk_rnaseq.python_builtin_pilot.v1

- Name: Built-in bulk RNA-seq pilot adapter
- Purpose/use: proves scoped execution and source-map writing
- Modality/step/language: bulk_rnaseq / differential_expression_pilot / python
- Primary script: `code_library/modules/bulk_rnaseq/python_builtin_pilot/main.py`
- Auditable scripts: `code_library/modules/bulk_rnaseq/python_builtin_pilot/main.py`
- Functions in primary script: bh_fdr, compute_de, main, mean, normal_p_from_t, parse_args, read_counts, read_metadata, render_heatmap, render_volcano, safe_float, select_groups, variance, write_csv, write_source_maps, write_text
- Execution type: python
- Environment lock: `pyproject.toml` status=True
- Maturity/validation: pilot / tested_internal
- Claim boundary: Workflow execution pilot only; use DESeq2/edgeR/limma for publication-grade inference.

## bulk_rnaseq.wgcna.v1

- Name: Publication-oriented WGCNA module-trait workflow
- Purpose/use: co-expression module discovery; module-trait association
- Modality/step/language: bulk_rnaseq / wgcna / r
- Primary script: `code_library/modules/bulk_rnaseq/wgcna/main.R`
- Auditable scripts: `code_library/modules/bulk_rnaseq/wgcna/main.R`, `code_library/modules/bulk_rnaseq/common/bulk_module_wrapper.R`
- Functions in primary script: delegated or script-level workflow
- Execution type: rscript
- Environment lock: `code_library/env_locks/r_bulk_rnaseq.lock.yaml` status=True
- Maturity/validation: validated_publication_oriented_wrapper / publication_oriented_dry_run_verified
- Claim boundary: Co-expression module association only; hub genes and modules do not prove mechanism.

## multi_omics.evidence_synthesis.v1

- Name: Multi-omics evidence synthesis planner
- Purpose/use: prevents unsupported cross-modality claims; separates discovery, association, and validation layers
- Modality/step/language: multi_omics / evidence_synthesis / yaml_contract
- Primary script: `config/bioinformatics_method_contract.yaml`
- Auditable scripts: `config/bioinformatics_method_contract.yaml`
- Functions in primary script: delegated or script-level workflow
- Execution type: not_declared
- Environment lock: `pyproject.toml` status=True
- Maturity/validation: design_ready / planning_contract
- Claim boundary: Evidence synthesis and claim-boundary audit; not an execution-only omics model.

## single_cell.cellchat_communication.v1

- Name: CellChat communication hypothesis adapter
- Purpose/use: cell-cell communication hypothesis generation
- Modality/step/language: single_cell / cellchat_communication / r
- Primary script: `code_library/modules/single_cell/cellchat_communication/main.R`
- Auditable scripts: `code_library/modules/single_cell/cellchat_communication/main.R`, `code_library/modules/single_cell/common/sc_module_wrapper.R`
- Functions in primary script: delegated or script-level workflow
- Execution type: rscript
- Environment lock: `code_library/env_locks/r_cell_communication.lock.yaml` status=True
- Maturity/validation: adapter_contract / communication_dry_run_verified
- Claim boundary: Cell-cell communication inference is hypothesis-generating and requires validation.

## single_cell.marker_feature_plot.v1

- Name: Marker feature plot module
- Purpose/use: marker display; exploratory cell identity support
- Modality/step/language: single_cell / marker_feature_plot / r
- Primary script: `code_library/modules/single_cell/marker_feature_plot/main.R`
- Auditable scripts: `code_library/modules/single_cell/marker_feature_plot/main.R`, `code_library/modules/single_cell/common/sc_module_wrapper.R`
- Functions in primary script: delegated or script-level workflow
- Execution type: rscript
- Environment lock: `code_library/env_locks/r_seurat_v5.lock.yaml` status=True
- Maturity/validation: thin_wrapper / dry_run_verified
- Claim boundary: Marker display only; expression overlays do not establish cell identity or mechanism alone.

## single_cell.nichenet_ligand_target.v1

- Name: NicheNet ligand-target hypothesis adapter
- Purpose/use: ligand-target hypothesis prioritization
- Modality/step/language: single_cell / nichenet_ligand_target / r
- Primary script: `code_library/modules/single_cell/nichenet_ligand_target/main.R`
- Auditable scripts: `code_library/modules/single_cell/nichenet_ligand_target/main.R`, `code_library/modules/single_cell/common/sc_module_wrapper.R`
- Functions in primary script: delegated or script-level workflow
- Execution type: rscript
- Environment lock: `code_library/env_locks/r_cell_communication.lock.yaml` status=True
- Maturity/validation: adapter_contract / communication_dry_run_verified
- Claim boundary: Ligand-target ranking is hypothesis-generating and does not prove causal signaling.

## single_cell.pseudobulk_aggregate.v1

- Name: Single-cell pseudobulk aggregation module
- Purpose/use: replicate-level aggregation; cell-type-specific DE setup
- Modality/step/language: single_cell / pseudobulk_aggregate / r
- Primary script: `code_library/modules/single_cell/pseudobulk_aggregate/main.R`
- Auditable scripts: `code_library/modules/single_cell/pseudobulk_aggregate/main.R`, `code_library/modules/single_cell/common/sc_module_wrapper.R`
- Functions in primary script: delegated or script-level workflow
- Execution type: rscript
- Environment lock: `code_library/env_locks/r_seurat_v5.lock.yaml` status=True
- Maturity/validation: thin_wrapper / dry_run_verified
- Claim boundary: Aggregation prepares replicate-level inference; it is not a differential result.

## single_cell.pseudobulk_deseq2.v1

- Name: Single-cell pseudobulk DESeq2 module
- Purpose/use: cell-type-specific differential expression; replicate-level association
- Modality/step/language: single_cell / pseudobulk_deseq2 / r
- Primary script: `code_library/modules/single_cell/pseudobulk_deseq2/main.R`
- Auditable scripts: `code_library/modules/single_cell/pseudobulk_deseq2/main.R`, `code_library/modules/single_cell/common/sc_module_wrapper.R`
- Functions in primary script: delegated or script-level workflow
- Execution type: rscript
- Environment lock: `code_library/env_locks/r_pseudobulk_deseq2.lock.yaml` status=True
- Maturity/validation: thin_wrapper / dry_run_verified
- Claim boundary: Pseudobulk DE requires valid replicate/sample mapping and covariate review before publication claims.

## single_cell.seurat_clustering_umap.v1

- Name: Seurat clustering and UMAP module
- Purpose/use: cluster discovery; exploratory cell-state visualization
- Modality/step/language: single_cell / seurat_clustering_umap / r
- Primary script: `code_library/modules/single_cell/seurat_clustering_umap/main.R`
- Auditable scripts: `code_library/modules/single_cell/seurat_clustering_umap/main.R`, `code_library/modules/single_cell/common/sc_module_wrapper.R`
- Functions in primary script: delegated or script-level workflow
- Execution type: rscript
- Environment lock: `code_library/env_locks/r_seurat_v5.lock.yaml` status=True
- Maturity/validation: thin_wrapper / dry_run_verified
- Claim boundary: Cluster visualization is exploratory and requires annotation/validation before inference.

## single_cell.seurat_integration_harmony.v1

- Name: Seurat Harmony integration module
- Purpose/use: multi-sample single-cell integration; batch-effect assessment
- Modality/step/language: single_cell / seurat_integration_harmony / r
- Primary script: `code_library/modules/single_cell/seurat_integration_harmony/main.R`
- Auditable scripts: `code_library/modules/single_cell/seurat_integration_harmony/main.R`, `code_library/modules/single_cell/common/sc_module_wrapper.R`
- Functions in primary script: delegated or script-level workflow
- Execution type: rscript
- Environment lock: `code_library/env_locks/r_seurat_harmony.lock.yaml` status=True
- Maturity/validation: thin_wrapper / dry_run_verified
- Claim boundary: Batch-corrected embedding for exploratory integration; does not prove batch-free biology.

## single_cell.seurat_pbmc3k_basic.v1

- Name: Seurat PBMC3K basic workflow
- Purpose/use: single-cell preprocessing and QC; cluster-level exploratory visualization; marker gene display
- Modality/step/language: single_cell / seurat_basic_workflow / r
- Primary script: `code_library/modules/single_cell/seurat_pbmc3k_basic/main.R`
- Auditable scripts: `code_library/modules/single_cell/seurat_pbmc3k_basic/main.R`
- Functions in primary script: find_10x_dir, get_arg, save_plot, write_yaml_lines
- Execution type: rscript
- Environment lock: `code_library/env_locks/r_seurat_v5.lock.yaml` status=True
- Maturity/validation: validated_external_tutorial_wrapper / tutorial_fixture_ready
- Claim boundary: Workflow validation and exploratory single-cell preprocessing only; not a disease mechanism or clinical claim.

## single_cell.seurat_qc.v1

- Name: Seurat QC filtering module
- Purpose/use: single-cell preprocessing; QC threshold documentation
- Modality/step/language: single_cell / seurat_qc / r
- Primary script: `code_library/modules/single_cell/seurat_qc/main.R`
- Auditable scripts: `code_library/modules/single_cell/seurat_qc/main.R`, `code_library/modules/single_cell/common/sc_module_wrapper.R`
- Functions in primary script: delegated or script-level workflow
- Execution type: rscript
- Environment lock: `code_library/env_locks/r_seurat_v5.lock.yaml` status=True
- Maturity/validation: thin_wrapper / dry_run_verified
- Claim boundary: QC and filtering only; retained cells are analysis inputs, not biological evidence.

## spatial.deconvolution_cell2location_or_rctd.v1

- Name: Spatial deconvolution adapter for cell2location or RCTD
- Purpose/use: spatial cell-type composition estimation
- Modality/step/language: spatial / deconvolution_cell2location_or_rctd / r
- Primary script: `code_library/modules/spatial/deconvolution_cell2location_or_rctd/main.R`
- Auditable scripts: `code_library/modules/spatial/deconvolution_cell2location_or_rctd/main.R`, `code_library/modules/spatial/common/spatial_module_wrapper.R`
- Functions in primary script: delegated or script-level workflow
- Execution type: rscript
- Environment lock: `code_library/env_locks/r_spatial_omics.lock.yaml` status=True
- Maturity/validation: adapter_contract / spatial_dry_run_verified
- Claim boundary: Deconvolution estimates cell-type abundance and requires reference and orthogonal validation.

## spatial.seurat_spatial_qc.v1

- Name: Seurat spatial QC adapter
- Purpose/use: spatial data audit; tissue section QC
- Modality/step/language: spatial / seurat_spatial_qc / r
- Primary script: `code_library/modules/spatial/seurat_spatial_qc/main.R`
- Auditable scripts: `code_library/modules/spatial/seurat_spatial_qc/main.R`, `code_library/modules/spatial/common/spatial_module_wrapper.R`
- Functions in primary script: delegated or script-level workflow
- Execution type: rscript
- Environment lock: `code_library/env_locks/r_spatial_omics.lock.yaml` status=True
- Maturity/validation: adapter_contract / spatial_dry_run_verified
- Claim boundary: Spatial QC defines usable spots/cells and tissue section metadata; it is not biological evidence.

## spatial.spatial_domain_detection.v1

- Name: Spatial domain detection adapter
- Purpose/use: spatial domain discovery
- Modality/step/language: spatial / spatial_domain_detection / r
- Primary script: `code_library/modules/spatial/spatial_domain_detection/main.R`
- Auditable scripts: `code_library/modules/spatial/spatial_domain_detection/main.R`, `code_library/modules/spatial/common/spatial_module_wrapper.R`
- Functions in primary script: delegated or script-level workflow
- Execution type: rscript
- Environment lock: `code_library/env_locks/r_spatial_omics.lock.yaml` status=True
- Maturity/validation: adapter_contract / spatial_dry_run_verified
- Claim boundary: Spatial domains are algorithmic groupings and require biological annotation and validation.

## spatial.spatial_feature_plot.v1

- Name: Spatial feature plot adapter
- Purpose/use: spatial expression visualization
- Modality/step/language: spatial / spatial_feature_plot / r
- Primary script: `code_library/modules/spatial/spatial_feature_plot/main.R`
- Auditable scripts: `code_library/modules/spatial/spatial_feature_plot/main.R`, `code_library/modules/spatial/common/spatial_module_wrapper.R`
- Functions in primary script: delegated or script-level workflow
- Execution type: rscript
- Environment lock: `code_library/env_locks/r_spatial_omics.lock.yaml` status=True
- Maturity/validation: adapter_contract / spatial_dry_run_verified
- Claim boundary: Spatial expression visualization is descriptive and does not prove causality.

## spatial.spatial_ligand_receptor.v1

- Name: Spatial ligand-receptor hypothesis adapter
- Purpose/use: spatial communication hypothesis generation
- Modality/step/language: spatial / spatial_ligand_receptor / r
- Primary script: `code_library/modules/spatial/spatial_ligand_receptor/main.R`
- Auditable scripts: `code_library/modules/spatial/spatial_ligand_receptor/main.R`, `code_library/modules/spatial/common/spatial_module_wrapper.R`
- Functions in primary script: delegated or script-level workflow
- Execution type: rscript
- Environment lock: `code_library/env_locks/r_spatial_omics.lock.yaml` status=True
- Maturity/validation: adapter_contract / spatial_dry_run_verified
- Claim boundary: Ligand-receptor and colocalization signals are hypothesis-generating only.
