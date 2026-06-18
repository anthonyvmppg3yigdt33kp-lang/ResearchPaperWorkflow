# Results Section Template

**Rules for this section:**
- Each `###` subsection maps to exactly one main figure (and its supporting tables/supplementary figures).
- Every declarative sentence carries a `(Figure X)` or `(Table X)` annotation. No orphan claims.
- **No citations** anywhere in Results. All context and comparison belong in Discussion.
- Quantitative claims always carry exact p-values and effect sizes (e.g., β/OR/HR + 95% CI + p).
- Language is strictly objective: "showed", "demonstrated", "was associated with", "was observed". No "interesting", "notably", "remarkably", "surprisingly".
- Use `{PLACEHOLDER}` for all values to be filled from actual output.

---

## {N}. Results

### {N}.1 {Study cohort / data overview descriptor}

A total of {N_SAMPLES} samples ({N_CASE} {CONDITION_A}, {N_CONTROL} {CONDITION_B}) were included after quality control filtering (Figure {N}A, Table {N_PLACEHOLDER}). The {CONDITION_A} group had a mean age of {MEAN_AGE_A} years (SD = {SD_AGE_A}) and {PCT_FEMALE_A}% female; the {CONDITION_B} group had a mean age of {MEAN_AGE_B} years (SD = {SD_AGE_B}) and {PCT_FEMALE_B}% female (Table {N_PLACEHOLDER}). No significant difference in age (p = {P_AGE}) or sex distribution (p = {P_SEX}) was observed between groups.

After {FILTERING_CRITERIA}, {N_GENES_PASS} genes passed expression thresholds and were retained for downstream analysis (Figure {N}B). Principal component analysis revealed {OBSERVED_PATTERN} between groups, with PC1 explaining {PC1_VAR}% and PC2 explaining {PC2_VAR}% of total variance (Figure {N}C).

### {N}.2 {Differential analysis descriptor}

Differential expression analysis identified {N_DEG} differentially expressed genes (DEGs) between {CONDITION_A} and {CONDITION_B} at |log2 fold change| > {LFC_THRESHOLD} and adjusted p < {PADJ_THRESHOLD} (Figure {N}A, Table {N_PLACEHOLDER}). Of these, {N_UP} were upregulated and {N_DOWN} were downregulated in {CONDITION_A} relative to {CONDITION_B} (Figure {N}B). The top upregulated genes included {GENE_A} (log2FC = {LFC_A}, padj = {PADJ_A}), {GENE_B} (log2FC = {LFC_B}, padj = {PADJ_B}), and {GENE_C} (log2FC = {LFC_C}, padj = {PADJ_C}) (Figure {N}C, Table {N_PLACEHOLDER}). The top downregulated genes included {GENE_D} (log2FC = {LFC_D}, padj = {PADJ_D}), {GENE_E} (log2FC = {LFC_E}, padj = {PADJ_E}), and {GENE_F} (log2FC = {LFC_F}, padj = {PADJ_F}).

Gene set enrichment analysis of the upregulated DEGs revealed significant enrichment in {GO_TERM_1} (FDR = {FDR_1}), {GO_TERM_2} (FDR = {FDR_2}), and {GO_TERM_3} (FDR = {FDR_3}) (Figure {N}D, Table {N_PLACEHOLDER}). Downregulated DEGs were enriched in {GO_TERM_4} (FDR = {FDR_4}) and {GO_TERM_5} (FDR = {FDR_5}).

### {N}.3 {WGCNA / network analysis descriptor}

Weighted gene co-expression network analysis (WGCNA) was performed on the {N_GENES_WGCNA} expressed genes. A soft-thresholding power of β = {POWER} was selected to achieve approximate scale-free topology (R² = {R2_SFT}; Figure {N}A). This produced {N_MODULES} co-expression modules, ranging in size from {MIN_MODULE_SIZE} to {MAX_MODULE_SIZE} genes (Figure {N}B, Table {N_PLACEHOLDER}).

Module-trait association analysis identified {N_SIG_MODULES} modules significantly associated with {CONDITION_A} status (|correlation| > {COR_THRESHOLD}, p < {P_MODTRAIT}; Figure {N}C). The {MODULE_COLOR_A} module showed the strongest positive correlation (r = {COR_A}, p = {P_A}), followed by {MODULE_COLOR_B} (r = {COR_B}, p = {P_B}). The {MODULE_COLOR_C} module showed the strongest negative correlation (r = {COR_C}, p = {P_C}).

Within the disease-associated modules, {N_HUB} hub genes were identified by module membership (|kME| > {KME_THRESHOLD}) and gene significance (|GS| > {GS_THRESHOLD}) criteria (Figure {N}D). Intersection of these hub genes with the DEGs from Section {N_PREV}.{N_PREV_SUB} yielded {N_HUB_DEG} hub-DEGs (Figure {N}E, Table {N_PLACEHOLDER}).

### {N}.4 {Machine learning / feature selection descriptor}

The {N_HUB_DEG} hub-DEGs were subjected to feature selection using {ML_METHOD_1} and {ML_METHOD_2} (Figure {N}A). {ML_METHOD_1} identified {N_FEATURES_1} discriminatory features with a {METRIC} of {VALUE_1} (95% CI: {CI_LOW_1}–{CI_HIGH_1}; Figure {N}B). {ML_METHOD_2} identified {N_FEATURES_2} discriminatory features with a {METRIC} of {VALUE_2} (95% CI: {CI_LOW_2}–{CI_HIGH_2}; Figure {N}C).

The intersection of features selected by both methods yielded {N_CONSENSUS} consensus biomarkers (Figure {N}D, Table {N_PLACEHOLDER}). A {CLASSIFIER_TYPE} model built on these {N_CONSENSUS} biomarkers achieved an AUC of {AUC_VALUE} (95% CI: {AUC_CI_LOW}–{AUC_CI_HIGH}) in the training set and {AUC_VAL} (95% CI: {AUC_VAL_CI_LOW}–{AUC_VAL_CI_HIGH}) in the validation set (Figure {N}E). Sensitivity was {SENS}% and specificity was {SPEC}% at the optimal threshold (Table {N_PLACEHOLDER}).

### {N}.5 {Immune infiltration / downstream characterization descriptor}

Immune cell infiltration analysis using {METHOD} estimated the relative abundance of {N_IMMUNE_TYPES} immune cell types across samples (Figure {N}A, Table {N_PLACEHOLDER}). Comparison between groups revealed significantly higher infiltration of {CELL_TYPE_A} ({EFFECT_SIZE_A}, p = {P_IMMUNE_A}) and {CELL_TYPE_B} ({EFFECT_SIZE_B}, p = {P_IMMUNE_B}) in {CONDITION_A} (Figure {N}B). Conversely, {CELL_TYPE_C} showed lower infiltration in {CONDITION_A} ({EFFECT_SIZE_C}, p = {P_IMMUNE_C}).

Correlation analysis between the consensus biomarkers and immune cell fractions showed that {BIOMARKER_A} expression was positively correlated with {CELL_TYPE_A} (r = {R_A}, p = {P_CORR_A}) and negatively correlated with {CELL_TYPE_C} (r = {R_C}, p = {P_CORR_C}) (Figure {N}C). {BIOMARKER_B} showed the opposite pattern, with negative correlation with {CELL_TYPE_A} (r = {R_B}, p = {P_CORR_B}) (Figure {N}D).

### {N}.6 {Validation / external dataset descriptor}

The diagnostic performance of the {N_CONSENSUS} consensus biomarkers was validated in an independent cohort of {N_VAL} samples ({GSE_ACCESSION}; Figure {N}A, Table {N_PLACEHOLDER}). In this external cohort, {N_VALIDATED} of {N_CONSENSUS} biomarkers maintained significant differential expression (|log2FC| > {VAL_LFC_THRESHOLD}, p < {VAL_P_THRESHOLD}; Figure {N}B). The combined {CLASSIFIER_TYPE} model achieved an AUC of {VAL_AUC} (95% CI: {VAL_AUC_CI_LOW}–{VAL_AUC_CI_HIGH}), sensitivity of {VAL_SENS}%, and specificity of {VAL_SPEC}% in the external cohort (Figure {N}C, Table {N_PLACEHOLDER}).

---

## Placeholder Reference Table

| Placeholder | Type | Source | Example Fill |
|---|---|---|---|
| `{N_SAMPLES}` | integer | QC output | `47` |
| `{MEAN_AGE_A}` | float (1 dp) | clinical table | `52.3` |
| `{P_AGE}` | scientific notation | t-test output | `0.47` |
| `{N_DEG}` | integer | DESeq2/limma output | `842` |
| `{LFC_A}` | float (2 dp) | DEG table | `2.34` |
| `{PADJ_A}` | scientific notation | DEG table | `3.2e-5` |
| `{POWER}` | integer | WGCNA pickSoftThreshold | `20` |
| `{N_MODULES}` | integer | WGCNA blockwiseModules | `17` |
| `{MODULE_COLOR_A}` | string | WGCNA output | `turquoise` |
| `{COR_A}` | float (3 dp) | moduleTraitCor | `0.724` |
| `{N_HUB_DEG}` | integer | hub x DEG intersection | `132` |
| `{AUC_VALUE}` | float (3 dp) | pROC / sklearn | `0.947` |
| `{AUC_CI_LOW}` | float (3 dp) | CI from bootstrap/Delong | `0.891` |
| `{FDR_1}` | scientific notation | clusterProfiler / GSEA | `1.2e-8` |

---

## Usage Notes

1. **Subsection granularity**: If a main figure has 4+ panels that tell independent sub-stories, consider splitting them into separate subsections (e.g., `{N}.2A` and `{N}.2B`), but each must still correspond to a coherent unit of evidence.
2. **Suppressing non-signals**: Do not write a subsection just because an analysis was run. If no significant results were found, summarize in one sentence (e.g., "No significant module-trait associations were observed for modules {X}, {Y}, and {Z} (all p > {THRESHOLD}; Figure {N}—Figure Supplement {N_PLACEHOLDER}).") and relegate details to supplements.
3. **Cross-referencing figures**: When a supporting table or supplementary figure belongs to the same subsection thesis, annotate it but keep the main figure as the anchor: "(Figure {N}A; see also Table {N_PLACEHOLDER} and Figure {N}—Figure Supplement {N_PLACEHOLDER})."
4. **Placeholder discipline**: Every `{PLACEHOLDER}` must be resolved from actual code output before the draft is considered complete. Do not estimate or round from memory.
5. **Language audit**: Before finalizing, search the Results text for subjective words (interesting, notable, striking, remarkably, surprisingly, curiously, intriguing, robust, elegant) and remove or replace with quantitative descriptors.
