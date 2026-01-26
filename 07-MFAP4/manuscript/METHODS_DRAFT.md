# Methods (Draft) — MFAP4 / EMT biomarkers for platinum resistance in ovarian cancer

## Study design
We performed a retrospective biomarker validation study using publicly available ovarian cancer gene-expression datasets with annotated platinum sensitivity outcomes. Primary validation was performed in an external cohort (GSE63885). Where possible, we also attempted a TCGA-OV analysis; however, platinum response labels and expression measurements had limited overlap.

## Data sources

### External validation cohort (GSE63885)
- **Accession**: GSE63885 (Gene Expression Omnibus)
- **Platform**: GPL570 (Affymetrix Human Genome U133 Plus 2.0 Array)
- **Samples**: 101
- **Clinical labels**: platinum sensitivity categories provided in the GEO series matrix sample characteristics (resistant / moderately sensitive / highly sensitive / NA).

### TCGA ovarian cohort (exploratory)
- **Study**: TCGA-OV PanCancer Atlas expression (cBioPortal)
- **Expression profile**: `ov_tcga_pan_can_atlas_2018_rna_seq_v2_mrna_median_all_sample_Zscores`
- **Platinum response labels**: derived from our TRUE-SAE v2 cohort (`linked_patients.adjusted.csv`).
- **Note**: only 44 patients overlapped between platinum labels and expression values, with 6 resistant/refractory cases, limiting power.

## Outcomes and label definitions

### GSE63885 platinum sensitivity
We defined the binary outcome **platinum resistant** vs **platinum sensitive** as:
- **Resistant (positive class = 1)**: `platinum_sensitivity == resistant`
- **Sensitive (negative class = 0)**: `platinum_sensitivity ∈ {moderately sensitive, highly sensitive}`
- **Excluded**: `NA` / missing platinum sensitivity

This yielded **n=101** labeled samples with **34 resistant** and **67 sensitive**.

### TCGA-OV platinum response (exploratory)
For TCGA-OV, we used the platinum response labels already attached to our TRUE-SAE v2 cohort:
- **Resistant (positive class = 1)**: `platinum_response ∈ {resistant, refractory}`
- **Sensitive (negative class = 0)**: `platinum_response == sensitive`

## Expression processing

### GSE63885 expression matrix
We downloaded the processed GEO series matrix:
- `GSE63885_series_matrix.txt.gz` → decompressed to `GSE63885_series_matrix.txt`.

The expression matrix contains **probe-level** values (Affymetrix probe IDs). We mapped probes to gene symbols using the GPL570 annotation table.

### Probe-to-gene mapping (GPL570)
We downloaded and parsed `GPL570.annot.gz` and extracted probe IDs for the EMT genes of interest:
- MFAP4: `212713_at`
- EFEMP1: `201842_s_at`, `201843_s_at`, `228421_s_at`
- VIM: `1555938_x_at`, `201426_s_at`
- CDH1: `201130_s_at`, `201131_s_at`
- SNAI1: `219480_at`

When multiple probes mapped to a gene, we computed the **mean** expression across those probes.

### Standardization
For composite scoring, gene expression values were **z-scored** across samples:
\[
 z(x) = \frac{x - \mu}{\sigma}
\]

## Biomarkers evaluated

### MFAP4 single-gene biomarker
We evaluated MFAP4 expression as a continuous score for predicting platinum resistance.

### EMT composite score
We evaluated an EMT composite score capturing mesenchymal/stromal phenotype:
\[
\text{EMT score} = \frac{z(MFAP4) + z(EFEMP1) + z(VIM) - z(CDH1)}{4}
\]

(We also extracted SNAI1 and reported its univariate AUROC as part of the EMT axis characterization.)

## Statistical analysis

### Primary metric: AUROC
Discrimination was quantified using the **area under the ROC curve (AUROC)** for predicting the positive class (platinum resistant).

### Cross-validation
For the multigene EMT model, we trained a logistic regression classifier using standardized EMT gene expression features and evaluated with 5-fold cross-validation:
- Features: `MFAP4_z, EFEMP1_z, VIM_z, CDH1_z, SNAI1_z`
- Model: logistic regression (L2 regularization; `max_iter=1000`)
- Metric: ROC AUC per fold; report mean ± standard deviation.

## Reproducibility and implementation
All data artifacts and analysis scripts are tracked in-repo.

### GSE63885 artifacts
`oncology-coPilot/oncology-backend-minimal/data/external/GSE63885/`
- `GSE63885_series_matrix.txt`
- `sample_annotations.csv`
- `GPL570.annot.txt`
- `emt_probe_mapping.json`
- `emt_platinum_auroc_results.json`

### Scripts
- GSE63885 AUROC computation: generated results in `emt_platinum_auroc_results.json`
- Figure generation: `oncology-coPilot/oncology-backend-minimal/scripts/figures/generate_gse63885_figures.py`

