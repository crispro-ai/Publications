# Data and Code Availability

## Data Availability

### Primary Data Artifacts

All data artifacts are available in-repo with complete provenance:

**GSE63885 validation cohort:**
- `oncology-coPilot/oncology-backend-minimal/data/external/GSE63885/`
  - `GSE63885_series_matrix.txt` - Processed expression matrix (probe-level)
  - `sample_annotations.csv` - Platinum sensitivity labels (resistant/sensitive)
  - `GPL570.annot.txt` - Probe-to-gene mapping (Affymetrix U133 Plus 2.0)
  - `emt_probe_mapping.json` - EMT gene probe mappings (MFAP4, SNAI1, EFEMP1, VIM, CDH1)
  - `emt_platinum_auroc_results.json` - **Primary results file** with all reported metrics

### Public Data Source

**GSE63885:**
- **Accession**: GSE63885
- **Repository**: Gene Expression Omnibus (GEO)
- **URL**: https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE63885
- **Platform**: GPL570 (Affymetrix Human Genome U133 Plus 2.0 Array)
- **Samples**: 101 ovarian cancer patients with platinum sensitivity labels

### Receipts and Validation

**Primary results receipt:**
- `oncology-coPilot/oncology-backend-minimal/data/external/GSE63885/emt_platinum_auroc_results.json`
  - Contains exact AUROC values, bootstrap CIs, cross-validation metrics
  - Validates all reported numbers in manuscript

**Figure receipts:**
- `publications/07-MFAP4/figures/fig_gse63885_roc_mfap4.png` - MFAP4 ROC curve
- `publications/07-MFAP4/figures/fig_gse63885_roc_emt_score.png` - EMT score ROC curve
- `publications/07-MFAP4/figures/fig_gse63885_cohort_flow.png` - Cohort flow diagram
- `publications/07-MFAP4/figures/fig_gse63885_box_mfap4_by_platinum.png` - MFAP4 expression box plots
- `publications/07-MFAP4/figures/fig_gse63885_box_emt_by_platinum.png` - EMT score box plots

## Code Availability

### Analysis Scripts

All analysis scripts are available in-repo with complete provenance:

**Primary analysis:**
- **Main repo**: `oncology-coPilot/oncology-backend-minimal/scripts/validation/gse63885_bootstrap_ci.py`
- **Local copy**: `publications/07-MFAP4/scripts/gse63885_bootstrap_ci.py`
  - Computes AUROC for MFAP4 and EMT composite score
  - Generates bootstrap confidence intervals (n=5000 iterations)
  - Performs 5-fold cross-validation for EMT score
  - Outputs `emt_platinum_auroc_results.json` with all metrics

**Figure generation:**
- **Main repo**: `oncology-coPilot/oncology-backend-minimal/scripts/figures/generate_gse63885_figures.py`
- **Local copy**: `publications/07-MFAP4/scripts/generate_gse63885_figures.py`
  - Generates ROC curves (MFAP4 + EMT score)
  - Creates expression box plots (resistant vs sensitive)
  - Produces orthogonality scatter plots (MFAP4 vs DDR markers)
  - Outputs publication-ready figures in `figures/` directory

### Dependencies

**Python packages:**
- `numpy` (array operations)
- `pandas` (data manipulation)
- `scikit-learn` (logistic regression, cross-validation, ROC AUC)
- `scipy` (statistical functions)
- `matplotlib` (figure generation)
- `seaborn` (enhanced plotting)

**Installation:**
```bash
pip install numpy pandas scikit-learn scipy matplotlib seaborn
```

## Reproducibility

### One-Command Reproduction

**Regenerate all results (from publication folder):**
```bash
cd publications/07-MFAP4
python scripts/gse63885_bootstrap_ci.py
```

**Or from main repo:**
```bash
python oncology-coPilot/oncology-backend-minimal/scripts/validation/gse63885_bootstrap_ci.py
```

This command:
1. Loads GSE63885 expression matrix and sample annotations
2. Maps probes to genes using GPL570 annotation
3. Computes z-scored expression values
4. Calculates MFAP4 AUROC with bootstrap CIs
5. Computes EMT composite score with 5-fold CV
6. Generates `emt_platinum_auroc_results.json` with all metrics

**Regenerate all figures (from publication folder):**
```bash
cd publications/07-MFAP4
python scripts/generate_gse63885_figures.py
```

**Or from main repo:**
```bash
python oncology-coPilot/oncology-backend-minimal/scripts/figures/generate_gse63885_figures.py
```

This command generates all publication-ready figures in `figures/` directory.

### Validation

**Verify reported metrics:**
```bash
python -c "import json; r = json.load(open('oncology-coPilot/oncology-backend-minimal/data/external/GSE63885/emt_platinum_auroc_results.json')); print(f\"MFAP4 AUROC: {r['individual_gene_aurocs']['MFAP4']:.3f}\"); print(f\"EMT CV-AUROC: {r['cv_auroc_mean']:.3f} ± {r['cv_auroc_std']:.3f}\")"
```

Expected output:
```
MFAP4 AUROC: 0.763
EMT CV-AUROC: 0.715 ± 0.179
```

### Provenance Tracking

All scripts include:
- **Version control**: Git-tracked with commit history
- **Seed values**: Fixed random seeds (seed=7 for bootstrap, seed=42 for CV) for reproducibility
- **Input/output validation**: Checksums and file size validation
- **Complete audit trail**: All transformations logged with timestamps

---

**Last Updated**: January 28, 2025  
**Reproducibility Status**: ✅ Validated
