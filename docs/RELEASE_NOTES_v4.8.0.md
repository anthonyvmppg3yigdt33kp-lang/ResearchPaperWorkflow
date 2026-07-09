# ResearchPaperWorkflow v4.8.0 Release Notes

v4.8.0 upgrades the method-asset pipeline from external script intake to a
reviewable, executable, and QA-audited bioinformatics method asset workflow.

## Added

- `method_blocks.yaml` generation during `import-code-source`.
- `method_block_extractor.py`, `method_depersonalizer.py`, and `source_parser.py`
  for method-call detection, line-range provenance, hardcoded-term review, and
  parameterization planning.
- `adapt-method-block` CLI command for generating reviewed external module
  scaffolds without silently mutating `module_registry.yaml`.
- `single_cell.seurat_findmarkers_group_de.v1`.
- `bulk_rnaseq.limma_voom_de_real.v1`.
- Module `output_bindings` and graph-level upstream artifact binding.
- Optional `research_plan/method_evidence_packet.yaml` strategy enhancement.
- `BioinformaticsRunQualityRules`, writing
  `qc/bioinformatics_quality_report.yaml` and `qc/next_analysis_plan.yaml`.
- Tests for method-block extraction, depersonalization, adaptation CLI,
  FindMarkers module contract, graph output binding, and bioinformatics QA.

## Changed

- Version metadata updated to `4.8.0`.
- `config/default_config.yaml` no longer advertises v4.6 as the current
  pipeline version.
- README now describes the current release as a method-asset builder rather
  than only a method-asset orchestration framework.
- `AnalysisGraphExecutor` resolves `nodes/<upstream_node>/...` inputs relative
  to the active run directory.
- Run manifests, evaluation reports, and PBMC3K QC summaries now prefer
  repository-relative paths in reportable artifacts to avoid Windows personal
  path leakage.
- `StrategyEvaluator` now returns explicit recommended methods,
  not-recommended methods, prerequisites, statistical unit, minimum data
  requirements, reviewer risk, claim boundary, and next-step plan.

## Validation

- `lung_master_nsclc_20260523_v1` local intake retained 132 files, parsed 70
  source scripts, and generated 82 method blocks for review. Detected block
  families include differential-expression post-processing, enrichment,
  percent-expression summaries, Seurat marker/feature plots, volcano plots, and
  general plotting. No `FindMarkers` or limma/voom call was present in the
  inspected R pipeline; the importer reports observed methods rather than
  fabricating absent calls.
- A reviewed external scaffold was generated for
  `dea_tvsbh__differential_expression_script__L1__e1476a90` under
  `code_library/modules/external/lung_master_nsclc_20260523_v1/`; registry
  mutation remains disabled because license review is still pending.
- PBMC3K tutorial execution completed as `workflow_test` evidence with
  `evaluation_report.yaml`, source maps, node manifest, session info, QC/UMAP
  figures, `qc/bioinformatics_quality_report.yaml`, and
  `qc/next_analysis_plan.yaml`. Bioinformatics QA status was `pass`.
- Final local checks passed: compileall, CI quality check, strict workflow
  contract validation, graph dry-run, R method contract, and pytest.

## Boundaries

- External code is still review-only by default.
- Registry promotion requires separate human review, tests, and an explicit
  registry patch.
- Dry-run and tutorial fixtures are not publication-grade evidence.
- FindMarkers outputs remain exploratory for disease-group inference unless
  biological replicate-aware analysis is documented.
