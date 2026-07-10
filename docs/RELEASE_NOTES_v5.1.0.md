# ResearchPaperWorkflow v5.1.0

v5.1 adds a researcher experience layer over the v5 TargetTask production kernel. The release focuses on turning a scientific question into an executable, reviewable plan without weakening any data, environment, approval, QA, or claim gate.

## Added

- `research_intent.v1` schema and PBMC3K example intent;
- `paper-workflow research validate|start|analyze|review|write|package|status`;
- scientific assessment with facts, assumptions, decisions, unknowns, and missing prerequisites;
- strategy simulation with statistical units, alternatives, module grades, environment state, reviewer risks, and claim boundaries;
- Figure-first planning and a compact research dashboard;
- method knowledge base and active local-experience reminders;
- natural-language Harness execution for TargetTask and Research Intent;
- CI smoke for Research Intent to TargetTask compilation.
- per-run node timing, input/output size reporting, and a TSV performance ledger;
- a path-safe PBMC3K real-execution evidence packet with artifact hashes.

## Corrected

- FindMarkers is classified as exploratory cell-level DE rather than bulk DE;
- TargetTask is bound to `workflow_contract.yaml` and strict contract validation;
- Harness mode overrides now regenerate a coherent profile and permission packet;
- Seurat subcluster QA now checks markers, program scores, resolutions, quality status, figures, object, and session information;
- Research Intent and TargetTask parameters now reach graph nodes and concrete R command arguments instead of remaining descriptive YAML;
- marker-driven T/NK-like subsetting requires both declared-marker and lineage-anchor thresholds;
- `FindAllMarkers` operation names are no longer misused as Seurat `test.use`; the configured test is recorded separately;
- subcluster resolution selection now prefers the first stable cluster-count plateau instead of the maximum number of clusters;
- empty marker or program results fail closed;
- current Agent and Skill documents no longer describe v4.x as the active operating model.

## Scientific Boundaries

- cell-level tests remain exploratory for disease-group inference;
- pseudobulk requires sample mapping and biological replicates;
- enrichment requires a reviewed ranked-gene result;
- network and communication results remain hypothesis-generating;
- tutorial fixtures do not support disease, clinical, treatment, or causal claims;
- evidence-bound writing remains blocked until fail-closed evaluation passes.

## Validation

The real PBMC3K release run completed two R nodes in 237.93 seconds with all workflow, scientific-quality, environment, and source-map gates passing. It retained 1,372 of 2,638 QC-passing cells under the marker-and-anchor rule, selected six exploratory subclusters at resolution 0.4, and produced 2,962 marker rows and 24 program-summary rows. The compact evidence packet is in `validation/pbmc3k_v5_1/`; no large data or RDS objects are committed.

The release is published only after Python tests, strict contract validation, module grading, supervision fault injection, researcher-experience smoke, graph and TargetTask smoke, performance budget, R wrapper checks, and GitHub pull-request CI pass.

The measured workflow-productivity score is 82/100; this is intentionally distinct from 100% binary release-gate completion. Current deductions are documented in `docs/V5_1_PRODUCTIVITY_SCORECARD.md`.

Local release preflight completed with 159 Python tests passed and 2 skipped. R 4.5.3 with Seurat, SeuratObject, Matrix, and ggplot2 passed; DESeq2 and WGCNA remain absent, so their dependent bulk/pseudobulk modules remain explicitly blocked rather than advertised as current capacity.
