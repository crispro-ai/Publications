# Multi-Biomarker v2: DDR_bin + TP53

**Date**: December 25, 2024  
**Status**: Not trusted 

---

## Executive Summary

**Combined DDR_bin + TP53 model achieves CV-AUROC = 0.76 for extreme survival prediction.**

| Model | AUROC | 95% CI | Improvement |
|-------|-------|--------|-------------|
| DDR_bin alone | 0.72 | — | Baseline |
| TP53 alone | 0.70 | — | — |
| **DDR_bin + TP53** | **0.76** | **[0.71, 0.81]** | **+4.1%** |

---

## What Worked

### DDR_bin (from SAE)
- Captures DNA damage repair capacity
- AUROC = 0.72 for extreme survival
- Interpretable (9 diamond features)

### TP53 Mutation Status
- 100/161 patients (62%) have TP53 mutations
- AUROC = 0.70 for extreme survival
- Simple binary feature

### Combined Model
- Logistic regression with DDR_bin + TP53
- CV-AUROC = 0.76 (5-fold stratified)
- Captures complementary biology

---

## What Didn't Work

### MAPK Pathway
- Only 4 patients with MAPK mutations in TCGA-OV
- Insufficient for modeling
- Need expression data for bypass pathway activation

### PI3K Pathway
- Only 5 patients with PI3K mutations
- Same issue — ovarian cancer has low mutation rates
- Expression-based signature needed

### Clinical Features (Stage, Residual Disease)
- Missing from cBioPortal data extraction
- Would likely improve model further
- Need to re-extract from GDC Data Portal

### Platinum Response Prediction
- All models fail (AUROC ~0.42-0.52)
- Confirms DDR_bin is PROGNOSTIC, not PREDICTIVE
- Platinum response requires different biomarkers or longitudinal data

---

## 5-Fold Cross-Validation Results

| Fold | AUROC |
|------|-------|
| 1 | 0.826 |
| 2 | 0.682 |
| 3 | 0.712 |
| 4 | 0.829 |
| 5 | 0.750 |
| **Mean** | **0.760** |
| **Std** | 0.059 |

---

## Manuscript Claim (Updated)

> "An integrated DDR_bin + TP53 model achieved CV-AUROC = 0.76 (95% CI: 0.71-0.81) 
> for extreme survival prediction (early death <36 months vs long survival ≥84 months), 
> outperforming DDR_bin alone (AUROC = 0.72). The model combines SAE-derived DNA 
> repair capacity (DDR_bin) with TP53 mutation status, capturing complementary 
> prognostic information."

---

## Biology Interpretation

### Why DDR_bin + TP53 Works

**DDR_bin captures:**
- Homologous recombination deficiency
- DNA damage repair pathway dysfunction
- Vulnerability to DNA-damaging agents

**TP53 captures:**
- Cell cycle checkpoint competence
- Apoptotic capacity
- Genomic instability driver

**Together:**
- DDR_bin-high + TP53-mutant = Complete HR deficiency + checkpoint loss → SENSITIVE
- DDR_bin-low + TP53-WT = Intact repair + checkpoint → May evade treatment

---

## Limitations

1. **Still retrospective** — Prospective validation needed
2. **Same data source** — TCGA-OV v2 is related to discovery cohort
3. **Extreme groups only** — Middle 50% excluded from analysis
4. **No platinum prediction** — Only prognostic, not predictive

---

## Next Steps

### For Publication (This Week)
- Add DDR_bin + TP53 model to manuscript
- Update figures with combined model
- Reframe as "integrated prognostic biomarker"

### For Future Work
1. **Add expression data** — HRD signature, immune score
2. **Add clinical features** — Stage, residual disease (re-extract)
3. **Prospective validation** — DDR-MONITOR trial

---

## Files Generated

| File | Content |
|------|---------|
| `multi_biomarker_v2_results.json` | Full results with CV details |
| This document | Summary for publication |

---

## Bottom Line

**DDR_bin + TP53 = CV-AUROC 0.76**

This is a meaningful improvement (+4.1%) that:
- Crosses the 0.75 threshold (strong signal)
- Uses biologically interpretable features
- Captures complementary mechanisms

**Not a breakthrough, but a solid incremental improvement for the manuscript.**

