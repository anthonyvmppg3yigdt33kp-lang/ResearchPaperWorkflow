# single-cell-analysis

Use this skill for scRNA-seq or single-cell immune-landscape analysis planning,
review, or execution after approval.

## Minimal Inputs

- `brief/PROJECT_BRIEF.yaml`
- single-cell data inventory or manifest
- approved analysis design
- `config/bioinformatics_method_contract.yaml`
- `config/visualization_contract.yaml`

## Expected Modules

- QC summary and doublet/mitochondrial/ribosomal checks;
- normalization, integration, dimensional reduction, clustering;
- cell type annotation and marker evidence;
- marker dotplot or heatmap;
- cell-type proportion summaries at sample/donor level;
- pseudobulk differential expression when group inference is needed;
- volcano/heatmap/enrichment outputs for DE results;
- cell-cell communication only with clear method and validation boundary.

## Do Not

- Do not infer disease effects from cell-level tests alone.
- Do not claim mechanism or clinical utility from visualization-only panels.
- Do not read large matrix contents unless execution is approved.

## Output

Report method, input files, statistical unit, figures, limitations, and source
map entries for each result.
