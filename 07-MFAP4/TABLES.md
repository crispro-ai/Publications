# MFAP4/EMT Analysis - Publication Figures and Tables

**Dataset:** GSE63885 (n=101 ovarian cancer patients)  
**Outcome:** Platinum resistance (34 resistant, 67 sensitive)

---

## TABLE 1: Univariate Gene AUROCs for Platinum Resistance Prediction

| Rank | Gene | AUROC | 95% CI | Direction | p-value |
|------|------|-------|--------|-----------|---------|
| 1 | **MFAP4** | **0.763** | 0.668-0.858 | High → Resistant | <0.001 |
| 2 | SNAI1 | 0.606 | — | High → Resistant | 0.06 |
| 3 | EFEMP1 | 0.592 | — | High → Resistant | 0.11 |
| 4 | CDH1 | 0.561 | — | Low → Resistant | 0.28 |
| 5 | VIM | 0.511 | — | — | 0.86 |

**Note:** MFAP4 is the strongest single-gene predictor with AUROC = 0.763 (bootstrap 95% CI: 0.668-0.858, n=5000 iterations).

---

## TABLE 2: MFAP4-High vs MFAP4-Low Clinical Outcomes

| Metric | MFAP4-high (n=51) | MFAP4-low (n=50) | OR (95% CI) | p-value |
|--------|-------------------|------------------|-------------|---------|
| **Platinum Resistant** | **54.9%** | **12.0%** | **8.93** | **<0.0001** |
| Platinum Sensitive | 45.1% | 88.0% | — | — |

**Interpretation:** Patients with high MFAP4 expression have ~9x higher odds of platinum resistance compared to patients with low MFAP4 expression.

---

## TABLE 3: EMT Composite Score Performance

| Metric | Value |
|--------|-------|
| EMT Score AUROC | 0.653 |
| Cross-validated AUROC | 0.715 ± 0.179 |
| EMT orientation | High EMT → Resistant |

**Cross-validation fold performance:**
| Fold | AUROC |
|------|-------|
| 1 | 0.378 |
| 2 | 0.703 |
| 3 | 0.769 |
| 4 | 0.857 |
| 5 | 0.869 |

---

## FIGURES

### Figure 1: MFAP4 Single-Gene ROC Curve
**File:** `fig_gse63885_roc_mfap4.png`  
**Caption:** Receiver operating characteristic (ROC) curve for MFAP4 expression predicting platinum resistance in GSE63885 (n=101). AUROC = 0.763 (95% CI: 0.668-0.858). High MFAP4 expression is associated with platinum resistance.

### Figure 2: MFAP4 Expression by Platinum Sensitivity
**File:** `fig_gse63885_box_mfap4_by_platinum.png`  
**Caption:** Box plot of MFAP4 expression (z-scored) by platinum sensitivity status. Platinum-resistant tumors show significantly higher MFAP4 expression compared to sensitive tumors.

### Figure 3: EMT Composite Score ROC Curve
**File:** `fig_gse63885_roc_emt_score.png`  
**Caption:** ROC curve for the 5-gene EMT composite score predicting platinum resistance. AUROC = 0.653 (raw) and 0.715 ± 0.179 (5-fold cross-validated).

### Figure 4: EMT Score by Platinum Sensitivity
**File:** `fig_gse63885_box_emt_by_platinum.png`  
**Caption:** Box plot of EMT composite score by platinum sensitivity. The EMT score incorporates MFAP4, SNAI1, EFEMP1, VIM, and CDH1 (inverted).

### Figure 5: Resistance Rates by MFAP4 Status  
**File:** `fig_gse63885_mortality_by_mfap4.png`  
**Caption:** Bar chart comparing platinum resistance rates between MFAP4-high and MFAP4-low groups (median split). MFAP4-high patients had 54.9% resistance rate vs 12.0% in MFAP4-low (OR = 8.93, p < 0.0001).

---

## SUPPLEMENTARY FIGURES

### Figure S1: Cohort Flow Diagram
**File:** `fig_gse63885_cohort_flow.png`  
**Caption:** CONSORT-style flow diagram for GSE63885 cohort selection.

---

## KEY STATISTICS FOR LANDING PAGE

| Metric | Value | Context |
|--------|-------|---------|
| **MFAP4 AUROC** | **0.763** | Single-gene platinum resistance prediction |
| **Resistance OR** | **8.93x** | MFAP4-high vs MFAP4-low |
| **Resistance rate (MFAP4-high)** | **54.9%** | vs 12.0% in MFAP4-low |
| **Cohort size** | **n=101** | GSE63885 external validation |
| **Publication-ready** | ✅ | Figures + tables complete |

---

## DATA PROVENANCE

All results from:  
`oncology-coPilot/oncology-backend-minimal/data/external/GSE63885/emt_platinum_auroc_results.json`

Reproducible via:  
`python oncology-coPilot/oncology-backend-minimal/scripts/validation/gse63885_bootstrap_ci.py`
