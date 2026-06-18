---
name: reproducibility
description: Reproducibility verification — environment snapshot, checksum comparison, Docker/conda audit, isolation replay, CI/CD skeleton generation. 可复现性验证。触发词：reproducible, docker, environment, conda, renv, seed, snapshot, 复现, 可重复, 环境.
version: "1.0"
paper_loop_stages: "8"
agent: pipeline_engineer
type: skill
---

# Reproducibility Skill

Ensures computational reproducibility of the entire analysis pipeline. Executed during Stage 8 (`verify_methods`) by `pipeline_engineer`.

## Pipeline Position
Stage 8 (`verify_methods`) — executed by `pipeline_engineer` after `analysis_executor` completes Stage 7.

## Verification Methods

### 1. Environment Snapshot Capture
Extract complete dependency manifests from the execution environment:
- **R**: `renv::snapshot()` or `sessionInfo()` capture
- **Python**: `pip freeze` or `conda env export --from-history`
- **System**: OS version, BLAS/LAPACK version, GPU drivers (if applicable)

### 2. Checksum Comparison
For every output file from Stage 7, recompute SHA-256 in the replay environment:
```
Original Run SHA-256 == Replay Run SHA-256 ?
  YES -> PASS
  NO  -> Record deviation with severity
```

### 3. Isolation Replay
Rebuild the entire environment from scratch and re-run all analysis:
- **Docker**: `docker build && docker run` with locked dependencies
- **Conda**: Fresh `conda env create -f environment.yml`
- **renv**: `renv::restore()` in clean R session

### 4. Path Hardcoding Scan
Scan all analysis scripts for non-portable paths:
- Windows: `C:\`, `D:\`
- Linux: `/home/`, `/Users/`
- Home dir: `~/`
- Local filenames in prose: `.h5ad`, `.rds`, `.py`, `.R`

### 5. Parameter Manifest
Extract all hardcoded parameters from analysis scripts:
- `set.seed(42)` -> `seed = 42`
- `resolution = 0.6` -> `leiden_resolution = 0.6`
- `mt_threshold = 25` -> `mt_filter_threshold = 25`

### 6. CI/CD Skeleton
Generate automated reproducibility workflow:
- GitHub Actions: `.github/workflows/reproducibility_check.yaml`
- Snakemake: `Snakefile_repro`
- Nextflow: `nextflow_repro.config`

## Deviation Severity Matrix

| Output Type | Tolerance | Failure Action |
|-------------|-----------|----------------|
| Numerical tables (.csv, .tsv) | Zero deviation — SHA-256 exact match | CRITICAL — block pipeline |
| Statistical results (p-value, effect size) | Zero deviation — floating-point exact | CRITICAL — block pipeline |
| Figures (.pdf, .png, .svg) | Visual equivalence (<0.1% pixel diff allowed) | HIGH — log deviation |
| Intermediate files (.rds, .h5ad, .pkl) | Zero deviation | HIGH — log deviation |
| Log files | Content variance OK, structure must match | INFO — log only |

## Output Files

```
papers/{paper_id}/reproducibility/
+-- reproducibility_report.md       # Human-readable verification report
+-- environment_snapshot.yaml       # Complete dependency manifest
+-- dockerfile_check.md             # Dockerfile audit or generated Dockerfile
+-- path_violations.json            # Hardcoded path violations
+-- parameter_manifest.yaml         # Extracted parameter inventory
+-- checksum_comparison.csv         # Per-file original vs replay SHA-256
+-- ci/
    +-- github_actions_repro.yaml   # CI/CD reproducibility workflow
```

## Integration

See `pipeline_engineer.md` for full agent specification. See `integrity.py` Gates H2 (code availability), H3 (no local paths), H4 (parameters complete).
