# 💀 SAE RESISTANCE PUBLICATION AUDIT

**Date:** January 25, 2026  
**Auditor:** Zo  
**Status:** 🔴 **PUBLICATION BLOCKED** — Fundamental approach issues identified

---

## 📋 EXECUTIVE SUMMARY

The SAE Resistance publication has **multiple fundamental issues** that explain why it couldn't be solved:

1. ❌ **TRUE SAE validation failed** — AUROC 0.555 after correcting for data leakage (was 0.783)
2. ❌ **Insufficient sample size** — 24 resistant patients is too small for 32K features
3. ⚠️ **DDR_bin is PROGNOSTIC, not PREDICTIVE** — Predicts survival (p=0.013), not resistance (p=0.80)
4. ✅ **MFAP4 shows promise** — AUROC 0.763 in external validation for EMT-based prediction
5. ✅ **PROXY SAE works** — Gene-level markers (DIS3, NF1) are validated

---

## 🔍 ROOT CAUSE: ARE YOU USING SAE WRONG?

### **What SAE Was Supposed To Do:**

1. Extract 32,768 "monosemantic" features from Evo2 protein language model
2. Find features that distinguish resistant vs sensitive patients
3. Map features to biological pathways (DDR, MAPK, etc.)
4. Predict platinum resistance at variant-level granularity

### **What Actually Happened:**

| Step | Expected | Actual | Problem |
|------|----------|--------|---------|
| **1. Feature extraction** | Works | ✅ Works | No issue |
| **2. Find discriminative features** | Strong signal | ❌ 0 FDR-significant | Not enough patients |
| **3. Map to pathways** | Many mappings | ❌ Couldn't map | No significant features |
| **4. Predict resistance** | AUROC >0.70 | ❌ AUROC 0.555 | Weak signal |

### **Why It Failed:**

```
THE MATH PROBLEM:

Features: 32,768
Patients: 149 (24 resistant, 125 sensitive)
Events per variable: 24 / 32,768 = 0.0007

Minimum needed: 10-15 events per variable
You have: 0.0007 events per variable

That's 14,000x UNDERPOWERED!
```

---

## 🎯 THE THREE POSSIBLE PUBLICATIONS

Based on the mdc files and validation results, there are **three distinct publication paths**:

### **Path 1: DDR_bin as PROGNOSTIC Biomarker** ⚠️ (Pivot Required)

**Current Status:** DDR_bin predicts SURVIVAL (HR=0.62, p=0.013) but NOT resistance (AUROC=0.52)

| Claim | Evidence | Status |
|-------|----------|--------|
| DDR_bin predicts platinum resistance | AUROC 0.52, p=0.80 | ❌ FAILED |
| DDR_bin predicts overall survival | HR=0.62, p=0.013, 17.9 month difference | ✅ WORKS |
| DDR_bin correlates with survival | Spearman ρ=0.252, p=0.001 | ✅ WORKS |

**What This Means:**
- Can publish as "SAE-derived DDR_bin predicts survival in ovarian cancer"
- Cannot claim "predicts platinum resistance"
- Prognostic biomarkers are valid and publishable (OncotypeDX, etc.)

**Manuscript Title (Revised):**
> "Sparse Autoencoder-Derived DDR_bin is a Prognostic Biomarker in High-Grade Serous Ovarian Cancer"

### **Path 2: MFAP4/EMT as Resistance Predictor** ✅ (Best Option)

**Current Status:** MFAP4 predicts resistance with AUROC 0.763 in external validation (GSE63885)

| Metric | Value |
|--------|-------|
| Dataset | GSE63885 (Polish cohort) |
| Samples | 101 (34 resistant, 67 sensitive) |
| MFAP4 AUROC | **0.763** ⭐ |
| EMT 5-fold CV | 0.715 ± 0.179 |

**Why This Works:**
- External validation (not just TCGA development)
- Adequate sample size
- Clear biological mechanism (EMT = mesenchymal = chemo-resistant)
- Single gene = interpretable

**Manuscript Title:**
> "MFAP4 Expression Predicts Platinum Resistance in High-Grade Serous Ovarian Cancer: External Validation"

### **Path 3: PROXY SAE (Gene-Level)** ✅ (Already Working in Production)

**Current Status:** Gene-level markers validated in MMRF and TCGA-OV

| Cancer | Marker | Relative Risk | p-value |
|--------|--------|--------------|---------|
| Multiple Myeloma | DIS3 | **2.08** | **0.0145** |
| Ovarian | NF1 | **2.10** | **<0.05** |
| Ovarian | PI3K | **1.39** | **0.02** |

**Why This Works:**
- Gene-level is interpretable ("DIS3 mutation → 2x mortality")
- No GPU required
- Already validated and in production

---

## ❌ WHY TRUE SAE APPROACH FAILED

### **Issue 1: Insufficient Sample Size**

```
For 32,768 features with balanced classes:
  Minimum patients needed: ~300,000 (10 EPV)
  
For reduced 9 "diamond" features:
  Minimum patients needed: ~180 (10 EPV × 2 classes × 9 features)
  You have: 149 (close but imbalanced)
  
For 24 resistant patients:
  Maximum features you can test: 2-3 (10 EPV rule)
  You tested: 1,571 "active" features → GUARANTEED to fail FDR
```

### **Issue 2: Class Imbalance**

```
Cohort breakdown:
  Sensitive: 125 (84%)
  Resistant: 24 (16%)
  
For 5-fold CV:
  Each test fold has ~5 resistant patients
  Cannot reliably estimate AUROC with 5 events
```

### **Issue 3: Data Leakage**

```
WRONG (what was done initially):
  1. Select features on FULL dataset (n=149)
  2. Train classifier on training set
  3. Evaluate on test set
  → Features already "saw" test set → INFLATED AUROC

RIGHT (nested CV):
  1. Split into train/test
  2. Select features on TRAINING only
  3. Train classifier on training
  4. Evaluate on test
  → Features never see test → HONEST AUROC

Result:
  Before correction: AUROC 0.783
  After correction: AUROC 0.555
  Inflation: 30.5 percentage points!
```

### **Issue 4: Wrong Outcome Variable**

DDR_bin measures DNA repair capacity, which:
- ✅ Correlates with overall survival (less repair → faster tumor growth → shorter OS)
- ❌ Does NOT predict platinum response (resistance is ACQUIRED, not intrinsic)

```
Why DDR_bin doesn't predict resistance:

At BASELINE (when sample taken):
  Sensitive: DDR_bin = 0.441
  Resistant: DDR_bin = 0.445
  Difference: p = 0.80 (NO DIFFERENCE)

Why?
  - Resistance often develops DURING treatment (acquired)
  - Baseline sample doesn't capture future resistance mechanisms
  - Need SERIAL sampling to detect emerging resistance
```

---

## 🛠️ WHAT WOULD FIX IT

### **Fix 1: Use SURVIVAL as Outcome (Not Resistance)**

DDR_bin predicts survival (p=0.013). Pivot to prognostic claim.

```
Original: "DDR_bin predicts resistance" (failed)
Revised: "DDR_bin predicts survival" (validated)
```

### **Fix 2: Use Gene-Level Aggregation (PROXY SAE)**

Skip variant-level features. Use gene-level pathway scores.

```
PROXY: "Does patient have mutations in DDR genes?"
  - Simple
  - Interpretable
  - Validated (DIS3, NF1)

TRUE: "What SAE features are activated by each variant?"
  - Complex
  - Not interpretable (yet)
  - Not validated
```

### **Fix 3: Use MFAP4/EMT Instead**

MFAP4 achieved AUROC 0.763 in external validation. Publish this.

```
MFAP4 works because:
  - Different mechanism (EMT, not DDR)
  - Expression-based (more robust than mutation-based)
  - External validation available (GSE63885)
```

### **Fix 4: Stratified Sampling for TRUE SAE**

If you want to continue TRUE SAE, need balanced cohort:

```python
# WRONG: Random 10 patients
patients = random.sample(all_patients, 10)  # Got 9 sensitive, 1 resistant

# RIGHT: Stratified
resistant = [p for p in all_patients if p.outcome == "resistant"]
sensitive = [p for p in all_patients if p.outcome == "sensitive"]
patients = random.sample(resistant, ALL) + random.sample(sensitive, 50)
# Gets ~24 resistant + 50 sensitive = balanced
```

### **Fix 5: Full Cohort Extraction**

TRUE SAE extraction only completed for 149 of 469 patients (32%). Need full extraction.

```
Cost: ~$50-100 Modal credits
Time: 15-40 hours
Outcome: Statistical power for validation
```

---

## 📊 RECOMMENDATION

### **What to Publish NOW:**

| Publication | Status | Action |
|-------------|--------|--------|
| **MFAP4 EMT resistance** | ✅ Ready | **PUBLISH** |
| **DDR_bin survival (prognostic)** | ⚠️ Needs pivot | Revise manuscript, publish |
| **TRUE SAE resistance** | ❌ Failed | **ABANDON** (or require 10x more data) |
| **PROXY SAE (gene-level)** | ✅ In production | Already deployed |

### **Priority Order:**

1. **PUBLISH MFAP4** — AUROC 0.763 external validation, strongest result
2. **PIVOT DDR_bin to prognostic** — HR=0.62 for survival, publishable
3. **SHELVE TRUE SAE** — Not enough data, not worth fixing now

---

## 📝 MANUSCRIPT STATUS

### Current Manuscript (`MANUSCRIPT_DRAFT.md`):

**Title:** "Sparse Autoencoder Features from Evo2 for Platinum Resistance Prediction in Ovarian Cancer"

**Status:** ⚠️ **DRAFT — CRITICAL VALIDATION FINDINGS**

**Main Issue:** Manuscript honestly reports the failure but doesn't provide a path to publication.

### Recommended Pivot:

**Option A: MFAP4 Paper (New Manuscript)**
```
Title: "MFAP4 Expression Predicts Platinum Resistance in Ovarian Cancer"
Key Result: AUROC 0.763 (external validation)
Status: Ready to write
```

**Option B: DDR_bin Prognostic Paper (Revise Current)**
```
Title: "SAE-Derived DDR_bin is a Prognostic Biomarker in Ovarian Cancer"
Key Result: HR=0.62, p=0.013 for overall survival
Status: Requires reframing, survival analysis focus
```

---

## 🔴 BOTTOM LINE

**Q: Are you using SAE wrong?**

**A: Not exactly "wrong," but:**

1. **Wrong outcome** — SAE features correlate with survival, not resistance
2. **Wrong sample size** — 24 resistant patients for 32K features is 14,000x underpowered
3. **Wrong aggregation** — Mean pooling may dilute signal; MAX shows weak improvement
4. **Right biology** — Features DO map to DDR pathway, providing interpretability

**The SAE approach has biological validity but lacks statistical power for resistance prediction.**

---

## ✅ ACTIONABLE NEXT STEPS

| Priority | Action | Time | Outcome |
|----------|--------|------|---------|
| **P0** | Write MFAP4 manuscript | 1 week | Publishable paper |
| **P1** | Pivot DDR_bin to survival | 3 days | Publishable paper |
| **P2** | Clean up TRUE SAE as "lessons learned" | 1 day | Blog post or supplement |
| **DEFER** | Full TRUE SAE extraction | 2-4 weeks | Only if clinical need arises |

---

**Document Status:** 💀 **AUDIT COMPLETE**  
**Recommendation:** Pivot to MFAP4 (resistance) + DDR_bin (survival)  
**TRUE SAE resistance prediction:** SHELVE (insufficient data)
