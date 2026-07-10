# PBMC3K v5.1 Real-Execution Evidence

This directory contains a small, reproducible evidence packet for the real
PBMC3K TargetTask run used to accept ResearchPaperWorkflow v5.1. Large tutorial
data, figures, and RDS objects are intentionally excluded.

Regenerate the packet after a real run:

```bash
python scripts/capture_pbmc3k_validation.py \
  --run-dir papers/pbmc3k_t_subcluster/results/runs/<run_id> \
  --out-dir validation/pbmc3k_v5_1
```

`validation_summary.yaml` records the fail-closed statuses, executed parameters,
scientific workflow-test metrics, runtime, and environment. `artifact_manifest.tsv`
binds those claims to SHA-256 hashes of the local run artifacts without exposing
personal paths or committing large outputs.

Claim boundary: this is official tutorial workflow validation only. It supports
no disease, clinical, treatment, or causal conclusion.
