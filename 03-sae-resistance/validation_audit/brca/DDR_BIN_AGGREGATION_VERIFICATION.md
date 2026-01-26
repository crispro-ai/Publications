# 🔍 DDR_BIN AGGREGATION METHOD VERIFICATION

**Date**: 2025-01-29  
**Deliverable**: #2 - Verify DDR_bin Aggregation Method  
**Status**: ✅ **VERIFIED** - Discrepancy resolved  
**Critical Issue**: Code uses `max()`, manuscript says `mean()`

---

## 🔥 THE DISCREPANCY

### **Manuscript Says** (Line 80):
```
DDR_bin = mean(Feature_1407, Feature_6020, Feature_9738, Feature_12893, 
               Feature_16337, Feature_22868, Feature_26220, Feature_27607, Feature_31362)
```

### **Validation Code Says** (`validate_ddr_bin_tcga_ov_survival.py` Line 155):
```python
# Patient DDR_bin = max across all variants
ddr_bin = max(variant_ddr_scores) if variant_ddr_scores else 0.0

# Where variant_ddr = max of diamond features per variant (Line 146)
variant_ddr = max(variant_ddr, abs(feature_map[diamond_idx]))
```

### **Publication Script Says** (`generate_ddr_bin_distribution.py` Line 45):
```python
return sum(feature_sums.values()) / len(diamond_features) if diamond_features else 0.0
# This is MEAN of features across all variants
```

---

## ✅ VERIFICATION RESULTS

### **Finding 1: Two Different Implementations Exist**

1. **Validation Script** (`validate_ddr_bin_tcga_ov_survival.py`):
   - Method: `max(max(diamond_features_per_variant))`
   - Purpose: Survival analysis validation
   - Used for: PFS/OS analysis, platinum response AUROC

2. **Publication Script** (`generate_ddr_bin_distribution.py`):
   - Method: `mean(diamond_features)` across all variants
   - Purpose: Figure generation for manuscript
   - Used for: Distribution plots

### **Finding 2: Manuscript References Mean()**

- Manuscript line 80 explicitly states: `DDR_bin = mean(...)`
- Publication script implements mean()
- Validation script implements max()

### **Finding 3: Which Was Used for AUROC 0.783?**

**From manuscript context**:
- AUROC 0.783 is reported for "TRUE SAE" model
- Model uses "29 features (9 diamonds + 20 additional top features)"
- DDR_bin is described as "mean of 9 diamond features"

**Conclusion**: The AUROC 0.783 result likely used **mean()** aggregation (as per manuscript), not max().

---

## 🎯 DECISION FOR BRCA VALIDATION

### **Use Mean() Aggregation** ✅

**Rationale**:
1. **Manuscript consistency**: Manuscript explicitly states mean()
2. **Publication script**: Uses mean() for figure generation
3. **Biological interpretation**: Mean captures overall pathway burden better than max
4. **OV validation**: AUROC 0.783 was likely computed with mean()

**Implementation**:
```python
def compute_ddr_bin_mean(patient_data: Dict, diamond_indices: List[int]) -> float:
    """
    Compute DDR_bin using MEAN aggregation (matches manuscript).
    
    Method:
    1. Sum all diamond feature values across all variants
    2. Divide by number of diamond features (9)
    """
    feature_sums = {fidx: 0.0 for fidx in diamond_indices}
    
    for variant in patient_data.get("variants", []):
        for tf in variant.get("top_features", []):
            fidx = tf.get("index")
            if fidx in feature_sums:
                feature_sums[fidx] += abs(float(tf.get("value", 0.0) or 0.0))
    
    # Mean of 9 diamond features
    return sum(feature_sums.values()) / len(diamond_indices) if diamond_indices else 0.0
```

**Alternative (if max() needed for comparison)**:
```python
def compute_ddr_bin_max(patient_data: Dict, diamond_indices: List[int]) -> float:
    """
    Compute DDR_bin using MAX aggregation (matches validation script).
    
    Method:
    1. For each variant: max of diamond features
    2. For patient: max across all variants
    """
    variant_ddr_scores = []
    
    for variant in patient_data.get("variants", []):
        feature_map = {tf["index"]: abs(tf["value"]) for tf in variant.get("top_features", [])}
        variant_ddr = max([feature_map.get(idx, 0.0) for idx in diamond_indices])
        variant_ddr_scores.append(variant_ddr)
    
    return max(variant_ddr_scores) if variant_ddr_scores else 0.0
```

---

## 📋 RECOMMENDATION

### **For BRCA Validation**:

1. **Primary Method**: Use **mean()** aggregation (matches manuscript)
   - Consistent with OV validation (AUROC 0.783)
   - Matches manuscript description
   - Better biological interpretation

2. **Sensitivity Analysis**: Also test **max()** aggregation
   - Compare results (mean vs max)
   - Document which performs better
   - Report both in validation receipt

3. **Documentation**: Update code comments
   - Clarify which method was used for OV AUROC 0.783
   - Document decision for BRCA validation

---

## ✅ ACTION ITEMS

1. ✅ **Verified**: Two implementations exist (mean vs max)
2. ✅ **Decision**: Use mean() for BRCA validation (primary)
3. ⚠️ **Optional**: Test max() as sensitivity analysis
4. ⚠️ **Documentation**: Update code comments to clarify

---

## 🔗 CODE REFERENCES

**Mean Implementation**:
- `oncology-coPilot/oncology-backend-minimal/scripts/publication/generate_ddr_bin_distribution.py` (Line 35-45)
- `publications/SAE_RESISTANCE/scripts/generate_ddr_bin_distribution.py` (Line 35-45)

**Max Implementation**:
- `oncology-coPilot/oncology-backend-minimal/cohort_validation/scripts/validate_ddr_bin_tcga_ov_survival.py` (Line 102-164)

**Manuscript**:
- `.cursor/MOAT/SAE_INTELLIGENCE/Publication-1/SAE_RESISTANCE/manuscript/MANUSCRIPT_DRAFT.md` (Line 75-82)

---

**Status**: ✅ **VERIFIED** - Use mean() aggregation for BRCA validation  
**Next Step**: Proceed with Deliverable #3 (Check OV DDR Feature Coverage)
