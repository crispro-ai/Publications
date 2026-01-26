# 🚨 MARS'S RED FLAG AUDIT: Variant Count Confounding Check

**Date**: 2025-01-29  
**Auditor**: Mars  
**Status**: ✅ **AUDIT COMPLETE** - Variant count NOT the confounder

---

## 🔍 MARS'S HYPOTHESIS

**Concern**: Sum aggregation AUROC 0.809 ± 0.167 is suspicious because:
1. Sum = variant count × mean (confounded)
2. High variance (±0.167) suggests instability
3. Model may be learning variant count, not SAE biology

---

## ✅ AUDIT RESULTS

### **Test 1: Variant Count vs Recurrence Correlation**

**Result**: r = 0.017, p = 0.8263  
**Verdict**: ✅ **LOW CORRELATION** - Variant count does NOT predict recurrence

**Interpretation**: 
- Variant count is NOT a confounder
- More variants ≠ higher recurrence risk (in this cohort)
- Sum aggregation is NOT just learning variant count

---

### **Test 2: Variant Count Alone as Predictor**

**Result**: AUROC = 0.378 ± 0.093  
**Verdict**: ✅ **WORSE THAN RANDOM** - Variant count has no predictive power

**Interpretation**:
- Variant count alone: 0.378 (worse than random 0.5)
- Sum aggregation: 0.766 (much better)
- **Conclusion**: Sum is NOT just variant count

---

### **Test 3: Sum vs Mean Comparison**

**Results**:
- Sum features only: **0.766**
- Mean features only: **0.773**
- Variant count only: **0.378**
- Sum + Variant count: **0.773**

**Verdict**: ✅ **SUM AND MEAN ARE SIMILAR** (0.766 vs 0.773)

**Interpretation**:
- Sum and mean give similar performance (within 1 pp)
- Both are much better than variant count (0.378)
- **Conclusion**: Sum is NOT confounded by variant count

---

### **Test 4: Sum Features vs Variant Count Correlation**

**Result**: r = 0.151, p = 0.0476  
**Verdict**: ✅ **LOW CORRELATION** - Sum captures independent signal

**Interpretation**:
- Sum features are only weakly correlated with variant count (r = 0.151)
- Sum captures SAE biology, not just variant burden
- **Conclusion**: Sum aggregation is valid

---

## 🎯 KEY FINDINGS

### **Mars's Concern**: ❌ **NOT CONFIRMED**

1. ❌ Variant count does NOT predict recurrence (AUROC 0.378)
2. ❌ Sum is NOT highly correlated with variant count (r = 0.151)
3. ❌ Sum is NOT just learning variant count

### **Real Issue**: ⚠️ **HIGH VARIANCE** (Mars was right about this!)

**The Problem**:
- Sum aggregation: 0.809 ± 0.167 (high variance)
- Mean aggregation: 0.607 ± 0.039 (low variance)
- **Issue**: High variance (±0.167) = unstable model

**Why High Variance?**:
- Small sample size: 16 events, 173 patients
- With only 3-4 events per CV fold, 1-2 cases swing results massively
- Some folds: AUROC ~1.0 (perfect)
- Other folds: AUROC ~0.5 (random)
- **This is the real red flag** - not variant count, but sample size

---

## 📊 HONEST ASSESSMENT

### **What's True**:
1. ✅ Variant count is NOT a confounder (r = 0.017, AUROC = 0.378)
2. ✅ Sum aggregation captures SAE signal (not variant count)
3. ⚠️ **BUT**: High variance (±0.167) makes results unreliable

### **What's the Real Issue**:
- **Small sample size** (16 events) causes high variance
- With nested CV, sum gives 0.594 ± 0.078 (still high variance)
- Mean gives 0.607 ± 0.039 (more stable)
- **Recommendation**: Use mean (more stable) or accept high variance

---

## 🎯 REVISED RECOMMENDATION

### **Mars's Core Insight**: ✅ **CORRECT** (about variance, not variant count)

**The Real Problem**:
- High variance (±0.167) = unreliable results
- Small sample size (16 events) = unstable CV
- **This is why we can't trust 0.809**

**The Solution**:
1. ✅ **Accept mean aggregation** (0.607 ± 0.039) - more stable
2. ✅ **Acknowledge high variance** in sum results
3. ✅ **Pivot to ovarian** (0.783, validated, stable)
4. ✅ **Revisit BRCA later** with more data (METABRIC)

---

## 📝 CORRECTED CONCLUSIONS

### **Original Claim** (WRONG):
> "Sum aggregation improves AUROC to 0.809"

### **Corrected Claim** (HONEST):
> "Sum aggregation gives AUROC 0.594 ± 0.078 (nested CV), similar to mean (0.607 ± 0.039). High variance (±0.078) reflects small sample size (16 events). Mean aggregation is more stable and recommended."

### **Mars's Recommendation** (CORRECT):
> "Accept AUROC 0.607 with mean aggregation. Pivot to ovarian (0.783) for publication."

---

## ✅ FINAL VERDICT

**Mars's Red Flag**: ⚠️ **PARTIALLY CORRECT**

**What Mars Got Right**:
- ✅ High variance (±0.167) is a red flag
- ✅ Results are unreliable with small sample size
- ✅ Should pivot to ovarian (0.783)
- ✅ Should accept honest result (0.607)

**What Mars Got Wrong**:
- ❌ Variant count is NOT the confounder (r = 0.017, AUROC = 0.378)
- ❌ Sum is NOT just learning variant count
- ❌ Sum does capture SAE signal (but with high variance)

**Bottom Line**:
- **Mars's recommendation stands**: Accept 0.607, pivot to ovarian
- **Reason**: High variance (not variant count confounding)
- **Action**: Use mean aggregation, report honest results

---

**Status**: ✅ **AUDIT COMPLETE** - Variant count not confounded, but high variance is the real issue  
**Recommendation**: Accept mean aggregation (0.607), pivot to ovarian (0.783)
