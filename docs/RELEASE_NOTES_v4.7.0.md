# ResearchPaperWorkflow v4.7.0 Release Notes

Release date: 2026-07-09

v4.7.0 addresses the production gaps found after v4.6.0: module source
inspectability, strict graph input binding, multilingual graph execution,
external GitHub source clone/parse/proposal generation, environment lock
coverage, method-asset audit gates, and deeper strategy evaluation.

## Added

- `code_library/modules/MODULE_SOURCE_CATALOG.md` with every registered module's
  purpose, primary script, delegated wrapper, function list, execution type,
  environment lock, maturity, validation status, and claim boundary.
- Standalone Python method asset at
  `code_library/modules/bulk_rnaseq/python_builtin_pilot/main.py`.
- `StrategyEvaluator` and strategy fields in `list-capabilities` output.
- Strict node input contracts generated from module `input_schema.required`.
- GraphExecutor support for `rscript`, `python`, `shell`/`bash`, and
  `jupyter`/`ipynb` execution types.
- External GitHub code intake `--clone`, R/Python source parsing, capability
  detection, and review-only `module_proposals.yaml`.
- `audit-method-assets` CLI command and CI gate.
- Bulk and pseudobulk environment lock files:
  `r_bulk_rnaseq.lock.yaml` and `r_pseudobulk_deseq2.lock.yaml`.
- Mandatory CI R method contract job using R setup, script parsing, and dry-run
  wrapper manifests.

## Changed

- Version metadata updated to `4.7.0`.
- README now points to v4.7 method-asset architecture and practice guide.
- Method selection no longer performs slow package checks during planning;
  package checks remain enforced during real graph execution.
- Python bulk pilot registry entry now points to the complete module script
  instead of the internal adapter file.
- `plan-analysis --from-code-library` records node input binding state in the
  graph.

## Explicit Boundaries

- Most newly registered R assets remain dry-run wrappers or adapter contracts.
  The release reports this as method-asset audit warnings instead of claiming
  publication-grade execution.
- Full Seurat/DESeq2 package-level execution still requires a provisioned R
  runtime with required packages and a valid paper-scoped data registry.
- Evidence graph synthesis remains a source-map and claim-boundary audit layer;
  it is not a full semantic proof engine.

## Validation

Local validation for the release includes:

```text
compileall: pass
ci_quality_check.py: pass
audit-method-assets --strict: pass with maturity warnings
validate-contract --strict: pass
pytest: 128 passed
ci_cli_smoke.py: pass
ci_graph_dry_run.py: pass
doctor --json: degraded only because fast-context is unavailable in the current agent session
local Rscript: unavailable; GitHub CI setup-r job owns the mandatory R method contract check
```

GitHub Actions must pass on the release commit before the release is treated as
published-current.
