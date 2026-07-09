# V5 Production Kernel Reform Plan

## Goal

Move ResearchPaperWorkflow from a broad framework into a bounded, release-gated research production system.

## Implemented Kernel

The maintained v5 execution path is:

```text
TargetTask YAML
-> schema validation
-> module/environment validation
-> analysis graph planning
-> dry-run or approved execution
-> bioinformatics QA
-> fail-closed evaluation
-> evidence-bound manuscript package
```

## Reform Areas

| Area | v5 implementation |
|---|---|
| Unified entry | `paper-workflow target validate|plan|run|evaluate|package` |
| QA stop rule | `BioinformaticsRunQualityRules` and `ResultRunManager` write `qc/fail_closed_decision.yaml` |
| Registry truth | every module has production grade, evidence level, strategy visibility, claim permission, env status |
| Graph execution | production gate blocks adapter/scaffold/planning/environment-blocked modules during execution |
| Seurat validation | PBMC3K TargetTask plus `single_cell.seurat_subcluster_programs.v1` |
| External code | lung-master DE-table standardizer converted to local Python wrapper |
| Manuscript packet | methods draft, results skeleton, figure storyline, evidence matrix, claim ledger, reviewer risk report |
| Release gates | module grade audit, supervision failure cases, target task smoke, performance budget |

## Release Stop Rules

Do not release if:

- final status is `pass` while bioinformatics quality is not `pass`;
- missing Seurat or missing PBMC3K data produces pass;
- missing `claim_boundary` still produces result conclusions;
- Windows personal paths appear in artifacts;
- external scaffold code is marked as production;
- docs make claims beyond local tests and runtime checks.
