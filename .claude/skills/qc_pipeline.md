---
name: qc_pipeline
description: Quality control pipeline for data integrity checking, gate enforcement, and artifact validation. 质量控制管道。触发词：check, verify, validate, integrity, gate, quality, audit, QC, 质量检查, 验证.
version: "1.0"
paper_loop_stages: "5, 14"
agent: data_auditor, integrity_checker
type: skill
---

# QC Pipeline Skill

Quality control and integrity enforcement across data audit (Stage 5) and manuscript integrity check (Stage 14). Implements the 16-rule integrity gate system.

## Pipeline Position
- Stage 5 (`data_audit`) — Data quality audit and metadata validation
- Stage 14 (`integrity_check`) — Full 16-rule integrity gate suite on assembled manuscript

## QC Checks (Stage 5: Data Audit)

1. **File existence and format validation** — Verify all declared input files exist and are in expected formats (`.h5ad`, `.csv`, `.rds`, `.fastq`, etc.)
2. **Metadata completeness** — Check that all required metadata fields are present and non-null
3. **Batch effect detection** — PCA/tSNE colored by batch, library, and technical covariates
4. **Outlier detection** — Per-sample QC metrics (MT%, gene count, read depth) with flagging thresholds
5. **Data integrity hashing** — SHA-256 of raw input files for provenance tracking

## Integrity Gates (Stage 14: Manuscript Check)

### CRITICAL Gates (Block Pipeline on Failure)
| Gate ID | Rule | Check |
|---------|------|-------|
| C1 | `bibtex_citation_existence` | Every `\cite{}` has a BibTeX entry |
| C2 | `citation_evidence_traceability` | Citations traceable to `citation_evidence.csv` |
| C3 | `results_no_citations` | Results section has zero `\cite{}` commands |
| C4 | `claim_artifact_binding` | Every result claim binds to a figure/table file |
| C5 | `figures_referenced` | Every `\ref{fig:...}` points to an existing file |

### HIGH Gates (Warn, Document if Unresolved)
| Gate ID | Rule |
|---------|------|
| H1 | Data Availability statement present |
| H2 | Code Availability statement present |
| H3 | No absolute filesystem paths in manuscript |
| H4 | All parameters and software versions documented |
| H5 | Discussion includes Limitations paragraph |
| H6 | No causal language for correlational results |
| H7 | Exact p-values + effect sizes + confidence intervals |
| H8 | Correct biological replicate unit for inference |

### MEDIUM Gates (Advisory)
| Gate ID | Rule |
|---------|------|
| M1 | Each section meets minimum word count |
| M2 | Natural prose paragraphs (no bullet points) |
| M3 | Figure count within journal limits |

## Output Files

```
papers/{paper_id}/
+-- data/
|   +-- data_audit_report.md       # Human-readable QC report
|   +-- data_inventory.yaml        # Machine-readable data manifest
|   +-- qc_metrics.json            # Per-sample QC metrics
+-- integrity/
    +-- integrity_report.json      # Machine-readable gate results
    +-- integrity_report.md        # Human-readable gate report
    +-- gate_failures_detail.jsonl  # Per-failure structured details
```

## Integration

See `integrity.py` for the full 16-gate implementation. See `data_auditor.md` and `integrity_checker.md` for agent specifications.
