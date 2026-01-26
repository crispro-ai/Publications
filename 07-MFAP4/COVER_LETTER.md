[Date]

Editorial Office
Clinical Cancer Research
American Association for Cancer Research
OR
NPJ Precision Oncology
Nature Portfolio

Re: Submission of manuscript, "MFAP4 Expression Predicts Platinum Resistance in High-Grade Serous Ovarian Cancer: External Validation in an Independent Cohort"

Dear Editors,

We are submitting the enclosed manuscript for consideration in *Clinical Cancer Research* [or *NPJ Precision Oncology*].

### Summary of the work

We report external validation of **MFAP4 as a platinum resistance biomarker** with **AUROC = 0.763** in an independent cohort (GSE63885, n=101). MFAP4 operates through an epithelial-mesenchymal transition (EMT)/stromal mechanism orthogonal to DNA damage repair pathways, addressing a critical gap in current biomarker panels for ovarian cancer. The 5-gene EMT composite score achieves cross-validated AUROC = 0.715, confirming the biological coherence of the mesenchymal resistance phenotype.

**Key findings:**
- MFAP4 single-gene AUROC = 0.763 (95% CI: 0.668-0.858, bootstrap n=5000)
- EMT composite score CV-AUROC = 0.715 ± 0.179 (5-fold cross-validation)
- Validated in external cohort (GSE63885, n=101; 34 resistant, 67 sensitive)
- Orthogonal to DDR pathways (different biological mechanism)

This work provides a validated expression-based biomarker for platinum resistance that captures resistance mechanisms beyond HRD status, with potential applications in treatment selection, risk stratification, and clinical trial enrichment.

### Manuscript type and scope

This submission is a **biomarker validation study** with external cohort validation. It provides executable receipts, complete data provenance, and reproducible analysis scripts. All reported metrics are validated against machine-readable results files (`emt_platinum_auroc_results.json`).

### Data and code availability

**Data artifacts:**
- `oncology-coPilot/oncology-backend-minimal/data/external/GSE63885/`
  - Primary results: `emt_platinum_auroc_results.json`
  - Expression matrix: `GSE63885_series_matrix.txt`
  - Sample annotations: `sample_annotations.csv`
- Public data source: GSE63885 (Gene Expression Omnibus)

**Analysis scripts:**
- `oncology-coPilot/oncology-backend-minimal/scripts/validation/gse63885_bootstrap_ci.py`
- `oncology-coPilot/oncology-backend-minimal/scripts/figures/generate_gse63885_figures.py`

**Reproduce command:**
```bash
python oncology-coPilot/oncology-backend-minimal/scripts/validation/gse63885_bootstrap_ci.py
```

This command regenerates all reported metrics and validates reproducibility.

### Conflicts of interest

[To be completed]

Sincerely,

[Corresponding Author, degrees]
[Institution]
[Email]
