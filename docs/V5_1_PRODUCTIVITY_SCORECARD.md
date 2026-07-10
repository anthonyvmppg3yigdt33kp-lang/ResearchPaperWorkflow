# v5.1 Productivity Scorecard

## Decision

Measured research-workflow productivity: **82/100**. This is separate from the
binary CI release-gate completion score, which can reach 100% when every required
engineering check passes. Neither score represents publication readiness.

| Dimension | Score | Evidence and remaining limit |
|---|---:|---|
| Real executable assets | 13/20 | Five modules are production-visible; the Seurat PBMC3K and subcluster nodes ran for real. Most legacy assets remain dry-run, adapter, planning-only, or environment-blocked. |
| Analysis output effectiveness | 17/20 | Real two-node Seurat run produced nonempty objects, tables, five subcluster figures, source maps, and QA. Evidence remains an official tutorial fixture. |
| Strategy-to-execution continuity | 14/15 | Research Intent parameters now reach graph nodes and R arguments; method grades and environment gates constrain selection. Literature evidence is structured but not automatically retrieved. |
| Supervision authority | 15/15 | Fault injection cannot yield pass; real evaluation combined workflow, scientific, environment, source-map, and claim gates. |
| Maintainability | 8/10 | Short researcher CLI, TargetTask expert path, schemas, focused tests, and current docs are aligned. The retained 20-stage loop and expert command surface still carry complexity. |
| Performance and complexity control | 8/10 | Every graph run records node runtime and size. The real validation used 237.93 seconds and about 431 MB of local output; large artifacts are excluded from Git. |
| Documentation truth | 4/5 | Real evidence is hash-bound and claim-limited. Historical documents remain in-place as archives and require ongoing drift control. |
| External-code conversion | 3/5 | The lung-master DE-table standardizer is real and reusable, but general source-to-function semantic refactoring still requires human review. |

## Real Validation Snapshot

- Run: `pbmc3k_t_subcluster_20260710_v4`
- Execution: two real R nodes, 237.93 seconds
- Quality gates: workflow pass, scientific pass, environment pass, source maps valid
- Cells: 2,638 after base QC; 1,372 selected by marker-plus-anchor rule
- Outputs: six exploratory subclusters, 2,962 marker rows, 24 program-summary rows
- Evidence grade: `workflow_test`
- Claim boundary: no disease, clinical, treatment, or causal inference

## Residual Risks

1. DESeq2 and WGCNA are absent locally; related bulk and pseudobulk paths remain blocked.
2. FindMarkers remains cell-level exploratory evidence unless replicate-aware inference is documented.
3. Program scores and resolution selection require researcher review and external validation.
4. External-code adaptation is not a general AST/dataflow refactoring engine.
5. The research dashboard is file-based rather than a graphical application.

Expansion should remain conservative: promote additional modules only after toy or
real execution, fail-closed QA, source maps, environment evidence, and a reviewed
claim boundary all exist.
