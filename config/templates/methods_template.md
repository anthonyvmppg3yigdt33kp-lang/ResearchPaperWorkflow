# Methods Section Template for Bioinformatics / Clinical Research Papers

> **Usage**: Copy this template into your manuscript draft. Replace every `{PLACEHOLDER}` with the actual value. Delete any subsection that does not apply to your study. **Do not leave any placeholder unresolved in the final manuscript.**

---

## 2. Materials and Methods

### 2.1 Study Design and Setting
{STUDY_DESIGN_OVERVIEW} — One paragraph summarising the design (e.g., retrospective case-control, prospective cohort, cross-sectional), the setting (single-centre / multi-centre, {INSTITUTION_NAME}, {CITY}, {COUNTRY}), and the study period ({START_DATE} to {END_DATE}). State the primary objective and, if applicable, the pre-registration identifier ({TRIAL_REGISTRATION_NUMBER}) or protocol reference ({PROTOCOL_DOI_OR_URL}).

---

### 2.2 Data Collection

#### 2.2.1 Clinical Data
{CLINICAL_DATA_SOURCE_DESCRIPTION} — Describe the source (electronic health records, prospective enrolment, registry), the variables extracted (demographics {DEMOGRAPHIC_VARIABLES}, laboratory values {LAB_VARIABLES}, imaging parameters {IMAGING_VARIABLES}, medication history {MEDICATION_VARIABLES}), the data extraction method (manual chart review, automated query), and the personnel who performed it ({NUMBER_OF_REVIEWERS} reviewers, inter-rater agreement {KAPPA_VALUE} if applicable). For each variable, specify the unit of measurement and any categorisation criteria with clinical justification.

#### 2.2.2 High-Throughput / Omics Data
{DATA_TYPE} data were generated using the {PLATFORM_NAME} platform ({MANUFACTURER}, {CITY}, {COUNTRY}). Sample preparation followed {PROTOCOL_REFERENCE}. Raw data were deposited in {REPOSITORY_NAME} under accession {ACCESSION_NUMBER} ({URL_OR_DOI}). For publicly available datasets, state the original publication ({ORIGINAL_PMID_OR_DOI}), the download date ({DOWNLOAD_DATE}), and any filtering applied prior to downloading.

| Attribute | Value |
|-----------|-------|
| Data type | {DATA_TYPE: RNA-seq / scRNA-seq / Spatial Transcriptomics / scATAC-seq / ChIP-seq / WGS / WES / Microarray / Proteomics / Metabolomics / Methylation Array / Other} |
| Platform | {PLATFORM_NAME_AND_MODEL} |
| Species | {SPECIES} |
| Tissue / Cell type | {TISSUE_OR_CELL_TYPE} |
| Number of samples | {N_SAMPLES} |
| Sequencing depth (if applicable) | {READ_DEPTH} |
| Reference genome / assembly | {REFERENCE_GENOME_VERSION} |
| Public repository | {REPOSITORY_NAME} |
| Accession number(s) | {ACCESSION_NUMBER} |

---

### 2.3 Data Processing

#### 2.3.1 Pre-processing
Raw {DATA_TYPE} data were processed using {PIPELINE_NAME} version {VERSION} ({CITATION}). **All parameters are documented below; no default values were used without explicit confirmation.**

- **Read alignment / mapping**: {ALIGNER_NAME} v{ALIGNER_VERSION} with parameters `{KEY_PARAMETERS}`. Alignment rate: {MEAN_ALIGNMENT_RATE}% (range {RANGE}%).
- **Quantification**: {QUANTIFICATION_TOOL} v{QUANTIFICATION_VERSION} with parameters `{KEY_PARAMETERS}`.
- **Normalisation**: {NORMALISATION_METHOD} ({CITATION}) implemented via {SOFTWARE_PACKAGE} v{VERSION}.
- **Batch correction** (if applicable): {BATCH_CORRECTION_METHOD} ({CITATION}) implemented via {SOFTWARE_PACKAGE} v{VERSION}, with batch variable `{BATCH_VARIABLE_NAME}` and covariates `{COVARIATE_NAMES}`.

#### 2.3.2 Quality Control
Quality control was performed using {QC_TOOL_OR_PACKAGE} v{QC_VERSION} with the following criteria:

| Metric | Threshold | Samples retained / excluded |
|--------|-----------|-----------------------------|
| {QC_METRIC_1: e.g., MT%} | {THRESHOLD_1} | {N_RETAINED_1} retained / {N_EXCLUDED_1} excluded |
| {QC_METRIC_2: e.g., gene count} | {THRESHOLD_2} | {N_RETAINED_2} retained / {N_EXCLUDED_2} excluded |
| {QC_METRIC_3: e.g., UMI count} | {THRESHOLD_3} | {N_RETAINED_3} retained / {N_EXCLUDED_3} excluded |

After QC, {N_FINAL_SAMPLES} samples ({N_FINAL_FEATURES} features) were retained for downstream analysis. A summary of QC metrics is provided in {SUPPLEMENTARY_TABLE_OR_FIGURE_REFERENCE}.

#### 2.3.3 Data Transformation
- **Log-transformation**: {YES_OR_NO}. If yes: {LOG_BASE}-transformed (log{LOG_BASE}({EXPRESSION_VALUE} + {PSEUDOCOUNT})).
- **Scaling / centering**: {YES_OR_NO}. If yes: {SCALING_METHOD}.
- **Combat / removeBatchEffect** (if not already applied in pre-processing): {YES_OR_NO}. If yes: {PACKAGE} v{VERSION}, batch = {BATCH_VARIABLE}.

---

### 2.4 Bioinformatics Analysis

#### 2.4.1 Differential Expression / Abundance Analysis
Differentially expressed {FEATURE_TYPE} between {GROUP_A} and {GROUP_B} were identified using {METHOD_NAME} v{METHOD_VERSION} ({CITATION}) implemented in {R_PACKAGE_OR_PYTHON_LIBRARY} v{VERSION}. The model formula was `{MODEL_FORMULA}`, adjusting for covariates `{COVARIATES}`. Significance threshold: adjusted *P*-value (FDR / Bonferroni / {OTHER_METHOD}) < {THRESHOLD} and |log{LOG_BASE} fold-change| > {FC_THRESHOLD}. A total of {N_UP} up-regulated and {N_DOWN} down-regulated {FEATURE_TYPE} were identified.

#### 2.4.2 Gene Set / Pathway Enrichment Analysis
Enrichment analysis was performed using {ENRICHMENT_TOOL} v{ENRICHMENT_VERSION} ({CITATION}) against the {DATABASE_NAME} database (version {DB_VERSION}, accessed {DB_ACCESS_DATE}). The background gene set comprised {N_BACKGROUND} {FEATURE_TYPE}. Enrichment significance was assessed by {TEST_METHOD: e.g., Fisher's exact test / hypergeometric test / GSEA} with FDR correction ({P_ADJ_METHOD}). Significantly enriched terms were defined as FDR < {FDR_THRESHOLD}.

#### 2.4.3 Weighted Gene Co-expression Network Analysis (WGCNA) — if applicable
Co-expression network construction was performed using the WGCNA R package v{WGCNA_VERSION} ({CITATION: Langfelder & Horvath, 2008, BMC Bioinformatics}). A signed weighted network was constructed as follows:
- **Soft-thresholding power**: {POWER_VALUE}, selected as the lowest power achieving scale-free topology fit index R^2 > {R2_THRESHOLD} (observed R^2 = {OBSERVED_R2}; {SUPPLEMENTARY_FIGURE_REFERENCE}).
- **Module detection**: `blockwiseModules()` with `minModuleSize = {MIN_MODULE_SIZE}`, `mergeCutHeight = {MERGE_CUT_HEIGHT}`, `deepSplit = {DEEP_SPLIT}`, `networkType = "signed"`, `TOMType = "{TOM_TYPE}"`.
- **Module–trait association**: Pearson ({OR_SPEARMAN}) correlation between module eigengenes and clinical traits. Significance: *P* < {P_THRESHOLD}.
- **Hub gene definition**: |gene significance| > {GS_THRESHOLD} and |module membership| (kME) > {KME_THRESHOLD} within each disease-associated module.

#### 2.4.4 Machine Learning / Feature Selection (if applicable)
{ML_ALGORITHM_NAME} ({CITATION}) was used for {TASK_DESCRIPTION}, implemented via {PACKAGE_NAME} v{PACKAGE_VERSION}. The dataset was split into training ({TRAIN_FRACTION}%, n = {N_TRAIN}) and test ({TEST_FRACTION}%, n = {N_TEST}) sets using stratified sampling by {STRATIFICATION_VARIABLE}. Hyperparameter tuning was performed via {TUNING_METHOD: grid search / random search / Bayesian optimisation} with {K}-fold cross-validation (k = {K_VALUE}). Model performance was assessed by {METRICS: AUC, accuracy, sensitivity, specificity, F1, MCC} with {CONFIDENCE_INTERVAL_METHOD} confidence intervals. Feature importance was determined by {IMPORTANCE_METHOD}.

#### 2.4.5 Cell-Type Deconvolution / Composition Analysis (if applicable)
Cell-type composition was estimated using {DECONVOLUTION_METHOD} ({CITATION}) with the {REFERENCE_SIGNATURE_NAME} reference matrix ({SOURCE}). Deconvolution was implemented via {PACKAGE_NAME} v{PACKAGE_VERSION} with default parameters, except: `{NON_DEFAULT_PARAMETER} = {VALUE}`. Differences in cell-type proportions between groups were assessed by {STATISTICAL_TEST} with FDR correction.

---

### 2.5 Statistical Methods

All statistical analyses were performed in {R_OR_PYTHON} version {R_OR_PYTHON_VERSION} ({CITATION_R_OR_PYTHON}). A two-sided *P*-value < {P_THRESHOLD} was considered statistically significant unless otherwise stated. **All random seeds are explicitly declared** (see Section 2.7).

#### 2.5.1 Descriptive Statistics
Continuous variables are presented as {MEAN_SD_OR_MEDIAN_IQR} and compared using {TEST: t-test / Wilcoxon rank-sum / ANOVA / Kruskal-Wallis} as appropriate, with normality assessed by {NORMALITY_TEST: Shapiro-Wilk / Kolmogorov-Smirnov / Q-Q plot inspection}. Categorical variables are presented as counts (percentages) and compared using {TEST: chi-squared / Fisher's exact}.

#### 2.5.2 Correlation Analysis
Correlations were assessed using {PEARSON_OR_SPEARMAN} correlation coefficient, chosen based on {JUSTIFICATION: normality assessment / presence of outliers / monotonic assumption}. Correlation coefficients (r or rho) are reported with {CONFIDENCE_INTERVAL_METHOD} confidence intervals and FDR-corrected *P*-values.

#### 2.5.3 Multiple Testing Correction
Multiple testing was corrected using {METHOD: Benjamini-Hochberg FDR / Bonferroni / Holm / Other} across {N_TESTS} tests. Adjusted *P*-values < {ADJ_P_THRESHOLD} were considered significant. This correction was applied at the level of {CORRECTION_LEVEL: per analysis / per figure panel / genome-wide}.

#### 2.5.4 Multivariable / Mediation Analysis (if applicable)
{ANALYSIS_DESCRIPTION} was performed using {METHOD} implemented in {PACKAGE_NAME} v{PACKAGE_VERSION}. The regression model was specified as `{MODEL_FORMULA}`. Effect sizes ({BETA_OR_OR_OR_HR}) are reported with {CI_LEVEL}% confidence intervals. Model diagnostics included {DIAGNOSTICS: variance inflation factor / residual plots / Durbin-Watson / Hosmer-Lemeshow}. Mediation analysis followed the {APPROACH: Baron & Kenny / product-of-coefficients / counterfactual} framework, with indirect effects tested by {BOOTSTRAP_OR_SOBEL} ({N_BOOTSTRAP} bootstrap resamples, seed = {BOOTSTRAP_SEED}).

#### 2.5.5 Sensitivity Analysis (if applicable)
{SENSITIVITY_DESCRIPTION: e.g., leave-one-out, random-effects vs fixed-effects meta-analysis, exclusion of outliers, alternative confounder adjustment sets, MR-Egger / weighted median / MR-PRESSO for Mendelian randomisation}.

---

### 2.6 Software and Resources

All analyses were conducted using the following software and versions. **Every version number is explicitly stated; no version was assumed or omitted.**

| Category | Software / Package | Version | Citation / URL | Purpose |
|----------|-------------------|---------|----------------|---------|
| Operating System | {OS_NAME} | {OS_VERSION} | — | Computational environment |
| Primary Language | {R / Python / Other} | {VERSION} | {CITATION} | Core analysis language |
| IDE | {RStudio / VS Code / Jupyter} | {VERSION} | — | Development environment |
| {CATEGORY_1} | {PACKAGE_NAME_1} | {VERSION_1} | {CITATION_1} | {PURPOSE_1} |
| {CATEGORY_2} | {PACKAGE_NAME_2} | {VERSION_2} | {CITATION_2} | {PURPOSE_2} |
| ... | ... | ... | ... | ... |

**Version retrieval**: All package versions were retrieved using `{SESSIONINFO_OR_PIP_FREEZE_OR_CONDALIST}` on {DATE_OF_FREEZE}. The complete environment is archived at {ENVIRONMENT_FILE_PATH_IN_REPOSITORY: e.g., renv.lock / environment.yml / requirements.txt}.

---

### 2.7 Reproducibility and Random Seeds

#### 2.7.1 Random Seed Declaration
To ensure full reproducibility, all stochastic operations were executed with fixed random seeds:

| Operation | Seed value | Software / Function |
|-----------|------------|---------------------|
| Global R/Python seed | {GLOBAL_SEED} | `set.seed({GLOBAL_SEED})` / `random.seed({GLOBAL_SEED})` |
| Train-test split | {SPLIT_SEED} | `{FUNCTION_NAME}(seed = {SPLIT_SEED})` |
| Cross-validation folds | {CV_SEED} | `{FUNCTION_NAME}(seed = {CV_SEED})` |
| Bootstrap resampling | {BOOTSTRAP_SEED} | `{FUNCTION_NAME}(seed = {BOOTSTRAP_SEED})` |
| Dimensionality reduction | {DIMRED_SEED} | `{FUNCTION_NAME}(random_state = {DIMRED_SEED})` |
| Clustering initialisation | {CLUSTER_SEED} | `{FUNCTION_NAME}(random_state = {CLUSTER_SEED})` |
| GPU / CUDA determinism | {GPU_SEED} | `torch.manual_seed({GPU_SEED})` / `tensorflow.random.set_seed({GPU_SEED})` |

Where the same seed value is reused across operations, the rationale is provided: {SEED_REUSE_RATIONALE}.

#### 2.7.2 Reproducibility Infrastructure
- **Environment**: {CONDA_VENV_OR_DOCKER_OR_RENV} with locked dependencies at `{LOCK_FILE_PATH}`.
- **Containerisation** (if applicable): Docker image `{DOCKER_IMAGE_NAME}:{TAG}` built from `{DOCKERFILE_PATH}`, available at {DOCKER_REGISTRY_URL}.
- **Computational hardware**: {CPU_MODEL}, {RAM_GB} GB RAM, {GPU_MODEL_IF_APPLICABLE}.
- **No absolute paths** are present in any analysis script; all file references use project-relative paths or environment variables defined in `{CONFIG_FILE_PATH}`.

---

### 2.8 Data Availability

{CHOOSE_AND_EXPAND_ONE_OF_THE_FOLLOWING_TEMPLATES:}

**Template A — Public data only:**
All data analysed in this study are publicly available. Raw and processed {DATA_TYPE} data were obtained from {REPOSITORY_NAME} under accession number(s) {ACCESSION_NUMBER(S)} ({URL_OR_DOI_LIST}). Clinical metadata are available at {METADATA_REPOSITORY_OR_SUPPLEMENTARY_TABLE}. Derived data (e.g., normalised expression matrices, differential expression results, module assignments) are provided as Supplementary Tables {TABLE_NUMBERS}.

**Template B — Public data + newly generated data:**
Publicly available data were obtained from {REPOSITORY_NAME} under accession {ACCESSION_NUMBER} ({URL_OR_DOI}). Newly generated {DATA_TYPE} data have been deposited in {REPOSITORY_NAME} under accession {ACCESSION_NUMBER} ({URL_OR_DOI}). Access to individual-level data requires approval from {DATA_ACCESS_COMMITTEE_NAME} ({CONTACT_EMAIL_OR_URL}) and is subject to {CONSENT_AND_ETHICS_CONSTRAINTS}.

**Template C — Restricted / sensitive data:**
Individual-level {DATA_TYPE} data cannot be shared publicly because of {REASON: patient privacy / consent restrictions / institutional policy / national regulation}. De-identified summary-level data that support the findings of this study are available in {REPOSITORY_NAME} at {DOI_OR_URL}. Requests for access to individual-level data should be directed to {DATA_ACCESS_COMMITTEE} ({EMAIL}) and require {REQUIREMENTS: data use agreement / ethics approval / institutional sign-off}. The typical response time is {RESPONSE_TIME}.

---

### 2.9 Code Availability

All custom analysis code is publicly available on {PLATFORM: GitHub / GitLab / Zenodo / figshare} at {REPOSITORY_URL_OR_DOI}. The repository is archived with a persistent identifier at {DOI_FROM_ZENODO_OR_SIMILAR}. The repository structure is as follows:

```
{REPOSITORY_NAME}/
├── README.md                   # Setup, execution, citation instructions
├── LICENSE                     # {LICENSE: MIT / GPL-3.0 / Apache-2.0 / CC-BY-4.0}
├── {ENVIRONMENT_LOCK_FILE}     # renv.lock / environment.yml / requirements.txt
├── Dockerfile                  # (optional) Containerised execution
├── config/
│   └── {CONFIG_FILE}           # Parameter definitions (no hard-coded paths)
├── scripts/
│   ├── 01_preprocessing.{R_or_py}
│   ├── 02_qc.{R_or_py}
│   ├── 03_analysis.{R_or_py}
│   └── 04_visualisation.{R_or_py}
├── results/                    # Output directory (.gitkeep for empty)
├── figures/                    # Manuscript figures (>=300 DPI for publication)
└── supplementary/              # Supplementary analyses and tables
```

**Execution**: To reproduce all analyses from raw data:
```
{COMMANDS_TO_RUN_THE_FULL_PIPELINE}
```
Expected runtime: approximately {RUNTIME_HOURS} hours on {HARDWARE_SPECIFICATION}. Intermediate results are cached at {CACHE_DIRECTORY}.

---

### 2.10 Ethical Approval and Informed Consent

{ETHICS_STATEMENT_TEMPLATE} — This study was approved by the {INSTITUTIONAL_REVIEW_BOARD_NAME} (approval number: {APPROVAL_NUMBER}, date: {APPROVAL_DATE}). {WAIVER_STATEMENT_IF_APPLICABLE}. All procedures complied with the Declaration of Helsinki ({YEAR_OF_REVISION}) and {LOCAL_REGULATIONS}. For publicly available data, original ethics approval and informed consent were obtained by the data generators as described in {ORIGINAL_PUBLICATION_CITATION}.

---

### 2.11 Reporting Guidelines

This study is reported in accordance with the {REPORTING_GUIDELINE: STROBE / CONSORT / PRISMA / STREGA / REMARK / TRIPOD / MIAME / MINSEQE / OTHER} statement ({CITATION}). A completed checklist is provided as {SUPPLEMENTARY_FILE_REFERENCE}.

---

## Appendix: Template Validation Checklist

Before submission, confirm:

```
□ All {PLACEHOLDER} tokens are resolved — no curly braces remain in the text
□ No local file paths (C:\, /Users/, /home/, D:\) appear in any section
□ Every software package has an explicit version number
□ Every statistical parameter value appears both here and in the corresponding code
□ Random seeds are declared in Section 2.7 and match those in the analysis scripts
□ Data availability statement uses one of the three templates (A/B/C)
□ Code availability statement includes a persistent DOI (not just a GitHub URL)
□ The referenced repository actually contains the files listed in Section 2.9
□ Reporting guideline checklist is completed and referenced in Section 2.11
□ Figure legends, supplementary references, and in-text citations are consistent with this Methods text
□ Supplementary table/figure numbers referenced here actually exist in the supplementary materials
```
