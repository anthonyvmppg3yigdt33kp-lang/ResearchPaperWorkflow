# v4.8 Reality Audit

This audit records the baseline that drove the v5.0.0 upgrade. It is a release-control artifact, not a claim that v4.8 was unusable.

## Baseline Score

Estimated productivity score before v5: 51/100.

Main causes:

- QA was partly fail-open: `needs_review` could coexist with final pass language.
- The module registry counted many assets, but production-capable executable modules were not clearly separated from dry-run, adapter, scaffold, and planning contracts.
- Strategy selection did not consistently change graph order, execution policy, or environment eligibility.
- Bulk and pseudobulk modules had declared locks but runtime package readiness was not decisive enough in production planning.
- External code intake could leave a scaffold looking like an available method.
- Windows personal paths could leak into artifacts unless checked downstream.
- Manuscript-facing outputs could be generated without a strong claim-boundary ledger.

## v5 Blocking Conditions

v5 release must be blocked if any of these are true:

- bioinformatics QA reports `needs_review`, `needs_fix`, or `blocked` while final evaluation says `pass`;
- adapter, scaffold, planning-only, retired, or environment-blocked modules are production-visible;
- the PBMC3K TargetTask cannot fail closed when R, Seurat, data, source maps, or claim boundaries are missing;
- missing Seurat produces a fake pass;
- missing claim boundaries still generate result conclusion paragraphs;
- Windows personal paths appear in artifacts;
- external lung-master code is marked production without real local wrapper execution;
- current docs use unqualified "validated", "pass", or "production-ready" language beyond the evidence.

## v5 Target

The release target is not "all biomedical analyses are fully automated." The target is a bounded production kernel:

```text
TargetTask -> graph -> environment gate -> run/evaluate -> fail-closed package -> evidence-bound manuscript packet
```

The expected score after implementation is at least 75/100, with remaining risk stated explicitly.
