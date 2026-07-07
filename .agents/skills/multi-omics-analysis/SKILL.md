# multi-omics-analysis

Use this skill for cross-omics or multi-modal integration design and review.

## Minimal Inputs

- `brief/PROJECT_BRIEF.yaml`
- modality-specific inventories
- approved analysis design
- `config/bioinformatics_method_contract.yaml`
- `config/visualization_contract.yaml`

## Expected Modules

- modality-specific QC;
- batch and confounder assessment;
- MOFA/MOFA2 or equivalent factor analysis when appropriate;
- DIABLO/mixOmics or supervised integration when approved;
- cross-omics correlation and module mapping;
- WGCNA/network modules;
- pathway integration;
- factor heatmap and variance-explained plots;
- validation/sensitivity analysis.

## Do Not

- Do not overstate integration as mechanism.
- Do not merge modalities without explicit sample matching or aggregation rules.
- Do not use patient-level labels for unmatched cell-level panels.

## Output

Return an integration plan or audit with source mapping, inference boundary, and
figure requirements.
