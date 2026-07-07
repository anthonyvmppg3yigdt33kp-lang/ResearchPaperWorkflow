# spatial-transcriptomics-analysis

Use this skill for Visium, Stereo-seq, Xenium, CosMx, MERFISH, or other spatial
transcriptomics tasks.

## Minimal Inputs

- `brief/PROJECT_BRIEF.yaml`
- spatial data inventory
- approved analysis design
- `config/bioinformatics_method_contract.yaml`
- `config/visualization_contract.yaml`

## Expected Modules

- spatial QC and tissue coordinate checks;
- spatial feature plots;
- domain or region detection;
- spatially variable genes;
- deconvolution and spatial cell-type proportion maps;
- colocalization and boundary differential analysis when relevant;
- spatial ligand-receptor analysis with explicit validation boundary.

## Do Not

- Do not call colocalization proof of interaction.
- Do not call spatial overlap causality.
- Do not use spatial validation wording without orthogonal or independent
  validation evidence.

## Output

Return figure-ready result interpretation with source data, script, method,
statistical unit, and claim boundary.
