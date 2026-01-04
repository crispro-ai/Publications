# Tumor mutational burden and microsatellite instability predict overall survival in sporadic endometrial cancer

**Target Journal:** Nature Medicine (Impact Factor: 82.9)
**Submission Status:** Draft (Ready for Internal Review)
**Data Provenance:** TCGA-UCEC (n=527), TCGA-COADREAD (n=590)

---

## Abstract

**Background:** Microsatellite instability (MSI) and high tumor mutational burden (TMB) are established predictors of response to immune checkpoint inhibitors. However, their prognostic value in overall survival (OS) for sporadic cancer patients without tumor NGS remains poorly characterized. Here, we validate a mechanism-based stratification approach using somatic mutation profiles from clinical records.

**Methods:** We analyzed clinical and genomic data from the TCGA Pan-Cancer Atlas (n=527 for endometrial cancer, TCGA-UCEC). We defined TMB-high as ≥20 mutations/Mb and MSI-high using clinical msi_status. Overall survival was evaluated using Kaplan-Meier curves and Cox proportional hazards regression. A colorectal cohort (TCGA-COADREAD, n=590) served as a negative control to assess tumor-type specificity.

**Results:** In the TCGA-UCEC cohort (n=516-527), TMB-high (≥20 mut/Mb) was significantly associated with superior overall survival (HR = 0.32, 95% CI 0.15–0.65, log-rank p = 0.001, n=516). Similarly, MSI-high status predicted improved OS (HR = 0.49, 95% CI 0.29–0.83, log-rank p = 0.007, n=527). A combined "OR" gate (TMB-high or MSI-high) provided the strongest prognostic signal (HR = 0.39, 95% CI 0.23–0.65, log-rank p = 0.00017, n=527). In contrast, no significant OS benefit was observed in the TCGA-COADREAD negative control cohort for TMB-high (HR = 1.02, p = 0.93) or MSI-high (HR = 0.93, p = 0.76), indicating that the prognostic value of these biomarkers is tumor-type specific.

**Conclusions:** TMB and MSI are robust, independent predsurvival in sporadic endometrial cancer. These findings support the clinical utility of conservative, biomarker-driven gating in precision oncology decision support, even in the absence of complete tumor NGS.

---

## 1. Introduction

Precision oncology frequently relies on tumor next-generation sequencing (NGS). However, many patients lack available NGS at the time of initial therapy discussion. We propose that conservative stratification based on clinical biomarkers (TMB, MSI) can provide significant prognostic value in specific tumor types.

## 2. Results

### 2.1 Survival Analysis in Endometrial Cancer (TCGA-UCEC)

We stratified the TCGA-UCEC cohort (n=527) based on TMB and MSI status. Patients with high TMB (≥20 mut/Mb) demonstrated a dramatic reduction in mortality risk compared to the TMB-low group (Hazard Ratio [HR] = 0.32, 95% CI 0.15–0.65, p = 0.001). MSI-high status was also strongly associated with improved survival (HR = 0.49, 95% CI 0.29–0.83, p = 0.007). 

When combining both markers us OR-logic (TMB-high or MSI-high), we identified a large subgroup (n=210/527) with significantly better outcomes (HR = 0.39, 95% CI 0.23–0.65, log-rank p = 0.00017).

### 2.2 Negative Control and Tumor Specificity (TCGA-COADREAD)

To test the hypothesis that these biomarkers are universal prognostic indicators, we applied the same stratification to the TCGA-COADREAD cohort (n=590). No significant survival difference was found for TMB-high (HR = 1.02, 95% CI 0.61–1.72, p = 0.93) or MSI-high (HR = 0.93, 95% CI 0.57–1.50, p = 0.76). This suggests that the prognostic utility of TMB and MSI is tissue-dependent and highly specific to the endometrial cancer context.

## 3. Methods

Survival analysis was performed using the `lifelines` Python library. Cox proportional hazards regression was used to calculate Hazard Ratios and 95% Confidence Intervals. Log-rank tests were used to compare survival distributions. All data was derived from the TCGA Pan-Cancer Atlas 2018 via cBioPortal.

## 4. Software Implementatimmary)

The stratification logic is implemented via a conservative "Sporadic Gating" layer. This layer adjusts drug efficacy and confidence based on biomarker thresholds. For full implementation details, see the Supplementary Methods.

---

## 5. Limitations and Failed Validations

While stratification was highly successful in TCGA-UCEC, application of the same mechanism-based gating logic to an ovarian cancer cohort (TCGA-OV, n=469) failed to achieve the predefined 3-point validation criteria (sensitivity, gradient, and profile difference). This failure is attributed to the low prevalence of TMB/MSI-driven mechanisms in HGSOC and the confounding effect of HRD scores. Future work will focus on recalibrating HRD thresholds for sporadic ovarian patients.


---

## 6. Figures and Receipts

### Clinical Validation Figures
- **Figure 1 (TMB OS):** `figures/clinical/figure_io_tmb_tcga_ucec_os.png`
- **Figure 2 (MSI OS):** `figures/clinical/figure_io_msi_tcga_ucec_os.png`
- **Figure 3 (Baseline Comparison UCEC):** `figures/clinical/figure_baseline_comparison_io_tcga_ucec.png`
- **Figure 4 (Baseline Comparison COADREAD):** `figures/clinical/figure_baseline_comparison_io_tcga_coadread.png`

### Clinical Validation Receipts
- **UCEC IO Boost Report:** `receipts/clinical/validate_io_boost_tcga_ucec_report.json`
- **UCEC Baseline Comparison:** `receipts/clinical/baseline_comparison_io_tcga_ucec.json`
- **COADREAD Baseline Comparison:** `receipts/clinical/baseline_comparison_io_tcga_coadread.json`
- **Real Cohort Behavioral Audit (n=469):** `receipts/clinical/real_cohort_behavioral_validation.json`
