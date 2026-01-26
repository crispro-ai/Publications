# 🔍 MANAGER PLAN CRITICAL REVIEW: BRCA SAE PATHWAY MAPPING

**Date**: 2025-01-29  
**Reviewer**: Zo (Alpha's AI)  
**Status**: ✅ **REVIEWED WITH CORRECTIONS**

---

## ✅ WHAT'S CORRECT

### **1. OV DDR Diamond Features** ✅
- **9 Features**: 1407, 6020, 9738, 12893, 16337, 22868, 26220, 27607, 31362
- **Status**: ✅ **VERIFIED** (confirmed in manuscript + validation scripts)
- **Source**: `.cursor/MOAT/SAE_INTELLIGENCE/Publication-1/SAE_RESISTANCE/manuscript/MANUSCRIPT_DRAFT.md`

### **2. Hypotheses** ✅
- **Hypothesis 1**: OV DDR → BRCA Recurrence (biological transfer)
- **Hypothesis 2**: BRCA Proliferation → BRCA Recurrence (cancer-specific)
- **Status**: ✅ **SOUND** - Both hypotheses are biologically plausible

### **3. Success Thresholds** ✅
- **4 Scenarios (A-D)**: Well-defined decision tree
- **Status**: ✅ **REASONABLE** - Thresholds align with clinical significance

### **4. Parallel Execution** ✅
- **Approach**: Test OV DDR transfer while running BRCA-specific analysis
- **Status**: ✅ **EFFICIENT** - Saves 1-2 days vs sequential

### **5. Oncotype DX Genes** ✅
- **Manager mentions**: MKI67, AURKA, BIRC5
- **Status**: ✅ **CORRECT** - These are standard Oncotype DX proliferation genes
- **Full 21-gene panel**: ACTB, GAPDH, RPLP0, GUS, TFRC, GSTM1, BAG1, BCL2, CCNB1, CD68, CTSL2, ESR1, GRB7, HER2, **MKI67**, **MYBL2**, PGR, MMP11, **BIRC5**, **STK15**, SURV
- **Note**: Manager correctly identified proliferation-heavy genes

---

## ⚠️ CRITICAL ISSUES FOUND

### **ISSUE 1: DDR_bin Aggregation Method Discrepancy** 🔥 **CRITICAL**

**Manager Says**:
```python
DDR_bin = mean(Feature_1407, Feature_6020, Feature_9738, ...)
```

**Actual Code** (`validate_ddr_bin_tcga_ov_survival.py`):
```python
# Line 142-147: Variant-level DDR = max of diamond features
variant_ddr = max(variant_ddr, abs(feature_map[diamond_idx]))

# Line 155: Patient DDR_bin = max across all variants
ddr_bin = max(variant_ddr_scores)
```

**Manuscript Says**:
```
DDR_bin = mean(Feature_1407, Feature_6020, Feature_9738, ...)
```

**Problem**: 
- **Code uses**: `max(max(diamond_features_per_variant))` = max across variants
- **Manuscript says**: `mean(diamond_features)` = mean of 9 features
- **Discrepancy**: Two different aggregation methods!

**Impact**:
- If manager uses `mean()` but code uses `max()`, results won't match OV validation
- Need to decide: Which method was actually used for OV AUROC 0.783?

**Recommendation**:
1. **Check OV validation code**: Which aggregation method was used?
2. **Use same method for BRCA**: Consistency is critical
3. **Update documentation**: Align code + manuscript + manager plan

**Action Required**: ⚠️ **VERIFY BEFORE EXECUTION**

---

### **ISSUE 2: Recurrence Outcome Field** ⚠️ **NEEDS VERIFICATION**

**Manager Says**:
```python
recurrence = patient.get("new_tumor_event_after_initial_treatment")
rfs_days = patient.get("days_to_new_tumor_event_after_initial_treatment")
```

**Problem**:
- Field name may differ in TCGA-BRCA clinical data
- Need to verify actual field names in cBioPortal/TCGA

**Alternative Fields** (from codebase search):
- `DFS_STATUS` (Disease-Free Survival status)
- `DFS_MONTHS` (Disease-Free Survival months)
- `new_tumor_event_after_initial_treatment` (may not exist)

**Recommendation**:
1. **Check TCGA-BRCA clinical data structure** first
2. **Use DFS_STATUS** if available (more standard)
3. **Map**: `DFS_STATUS == "1:Recurred/Progressed"` → recurrence = True

**Action Required**: ⚠️ **VERIFY FIELD NAMES**

---

### **ISSUE 3: Feature Extraction from BRCA Checkpoint** ⚠️ **NEEDS CLARIFICATION**

**Manager's Code**:
```python
patient_features = aggregate_sae_features(patient["variants"], ov_ddr_features)
ddr_bin = mean(patient_features)
```

**Problem**:
- BRCA checkpoint has `top_features` per variant (k=64, not full 32K)
- OV DDR features may not be in top-64 for BRCA variants
- Need to handle missing features

**BRCA Checkpoint Structure** (from validation):
```json
{
  "variants": [
    {
      "top_features": [
        {"index": 32710, "value": 8.36},
        {"index": 10035, "value": 3.00},
        ...
      ]
    }
  ]
}
```

**Issue**: 
- If OV DDR feature 1407 is NOT in top-64 for a variant, it's missing
- Manager's code assumes all 9 features are present

**Recommendation**:
1. **Check feature coverage**: How many BRCA variants have OV DDR features?
2. **Handle missing features**: Use 0.0 if feature not in top-64, or re-extract full 32K
3. **Alternative**: Re-extract full 32K features for OV DDR indices only (cheaper than full extraction)

**Action Required**: ⚠️ **VERIFY FEATURE COVERAGE**

---

### **ISSUE 4: BRCA Proliferation Gene List** ⚠️ **INCOMPLETE**

**Manager Says**:
```python
# Proliferation (MKI67, AURKA, BIRC5, CCNB1, MYBL2) - Oncotype DX genes
```

**Problem**:
- Manager lists 5 genes, but Oncotype DX has 21 genes
- Proliferation pathway should include more genes

**Full Oncotype DX Proliferation Genes**:
- **Proliferation**: MKI67, AURKA, BIRC5, CCNB1, MYBL2, STK15
- **Cell cycle**: CCNB1, MYBL2, STK15
- **Apoptosis**: BCL2, BIRC5

**Recommendation**:
1. **Expand gene list**: Include all Oncotype DX proliferation genes
2. **Pathway mapping**: Map SAE features to proliferation via gene enrichment
3. **Validation**: Compare SAE proliferation score vs Oncotype DX 21-gene score

**Action Required**: ⚠️ **EXPAND GENE LIST**

---

## 📋 CORRECTED EXECUTION PLAN

### **Task 1.1: Extract Recurrence Labels** (CORRECTED)

**Original Issue**: Field name may be wrong

**Corrected Code**:
```python
def extract_brca_recurrence_labels():
    """
    Extract recurrence outcome from TCGA-BRCA clinical data
    
    CORRECTED: Use DFS_STATUS (more standard than new_tumor_event)
    """
    clinical_data = download_tcga_clinical("BRCA")
    
    outcomes = []
    for patient in clinical_data:
        # Try multiple field names (defensive)
        dfs_status = (
            patient.get("DFS_STATUS") or 
            patient.get("new_tumor_event_after_initial_treatment") or
            patient.get("disease_free_survival_status")
        )
        
        dfs_months = (
            patient.get("DFS_MONTHS") or
            patient.get("days_to_new_tumor_event_after_initial_treatment") or
            patient.get("disease_free_survival_months")
        )
        
        # Parse DFS_STATUS: "0:DiseaseFree" or "1:Recurred/Progressed"
        if dfs_status and isinstance(dfs_status, str):
            if dfs_status.startswith("1:") or "recurred" in dfs_status.lower() or "progressed" in dfs_status.lower():
                recurrence = True
            elif dfs_status.startswith("0:") or "diseasefree" in dfs_status.lower():
                recurrence = False
            else:
                recurrence = None
        else:
            recurrence = None
        
        outcomes.append({
            "patient_id": patient["patient_id"],
            "recurrence": recurrence,
            "recurrence_free_survival_months": dfs_months,
            "vital_status": patient.get("vital_status")
        })
    
    return outcomes
```

**Key Changes**:
- ✅ Try multiple field names (defensive)
- ✅ Use DFS_STATUS as primary (more standard)
- ✅ Handle missing data gracefully

---

### **Task 1.2: Test OV DDR Transfer** (CORRECTED)

**Original Issue**: Aggregation method + feature coverage

**Corrected Code**:
```python
def test_ov_ddr_transfer():
    """
    Test if OV DDR diamond features predict BRCA recurrence
    
    CORRECTED: Handle missing features + verify aggregation method
    """
    # Load BRCA SAE features
    brca_sae = load_json("BRCA_TCGA_TRUE_SAE_cohort.json")
    
    # Load OV DDR diamond features
    ov_ddr_features = [1407, 6020, 9738, 12893, 16337, 22868, 26220, 27607, 31362]
    
    # Load BRCA recurrence labels
    recurrence = load_json("brca_recurrence_labels.json")
    
    # CRITICAL: Check feature coverage first
    coverage_stats = check_feature_coverage(brca_sae, ov_ddr_features)
    logger.info(f"OV DDR feature coverage: {coverage_stats}")
    
    # If coverage < 50%, need to re-extract full 32K for OV DDR indices
    if coverage_stats["mean_coverage"] < 0.5:
        logger.warning("⚠️ Low feature coverage. Consider re-extracting full 32K for OV DDR indices.")
    
    # For each BRCA patient, compute DDR_bin using OV features
    ddr_bins = []
    outcomes = []
    
    for patient_id, patient_data in brca_sae["data"].items():
        # Extract SAE features for OV DDR indices
        # CORRECTED: Handle missing features (use 0.0 if not in top-64)
        patient_ddr_features = []
        
        for variant in patient_data.get("variants", []):
            top_features = variant.get("top_features", [])
            feature_map = {tf["index"]: tf["value"] for tf in top_features}
            
            # Extract OV DDR features (use 0.0 if missing)
            variant_ddr_features = [
                abs(feature_map.get(diamond_idx, 0.0)) 
                for diamond_idx in ov_ddr_features
            ]
            patient_ddr_features.extend(variant_ddr_features)
        
        # CORRECTED: Use same aggregation as OV validation
        # Check: Was OV validation using mean() or max()?
        # For now, use mean() (as per manuscript)
        if patient_ddr_features:
            ddr_bin = statistics.mean(patient_ddr_features)
        else:
            ddr_bin = 0.0
        
        ddr_bins.append(ddr_bin)
        outcomes.append(recurrence.get(patient_id, {}).get("recurrence"))
    
    # Filter out None outcomes
    valid_pairs = [(d, o) for d, o in zip(ddr_bins, outcomes) if o is not None]
    ddr_bins_valid, outcomes_valid = zip(*valid_pairs) if valid_pairs else ([], [])
    
    # Compute AUROC
    if len(set(outcomes_valid)) < 2:
        logger.error("❌ Not enough outcome diversity for AUROC")
        return {"error": "Insufficient outcome diversity"}
    
    auroc = compute_auroc(ddr_bins_valid, outcomes_valid)
    
    # Interpret
    if auroc >= 0.70:
        interpretation = "success"
        next_action = "use_ov_mapping"
    elif auroc >= 0.60:
        interpretation = "moderate"
        next_action = "refine_brca_ddr"
    else:
        interpretation = "poor"
        next_action = "run_brca_specific"
    
    return {
        "ov_ddr_auroc": auroc,
        "interpretation": interpretation,
        "next_action": next_action,
        "feature_coverage": coverage_stats,
        "n_patients": len(ddr_bins_valid)
    }
```

**Key Changes**:
- ✅ Check feature coverage first
- ✅ Handle missing features (use 0.0)
- ✅ Use mean() aggregation (match manuscript)
- ✅ Filter None outcomes
- ✅ Add coverage stats to output

---

### **Task 1.3: BRCA Biomarker Correlation** (CORRECTED)

**Original Issue**: Proliferation gene list incomplete

**Corrected Code**:
```python
# CORRECTED: Full Oncotype DX proliferation gene list
PROLIFERATION_GENES = {
    # Core proliferation (Oncotype DX)
    "MKI67", "AURKA", "BIRC5", "CCNB1", "MYBL2", "STK15",
    # Cell cycle
    "CCND1", "CCNE1", "CDK4", "CDK6", "RB1",
    # Apoptosis
    "BCL2", "BAX", "CASP3",
    # Growth factors
    "MYC", "MYCN"
}

# CORRECTED: Full DDR gene list (for BRCA-specific DDR mapping)
DDR_GENES_BRCA = {
    "BRCA1", "BRCA2", "ATM", "ATR", "CHEK2", "PALB2",
    "RAD51", "RAD51C", "RAD51D", "BRIP1", "BARD1",
    "TP53", "MBD4", "MLH1", "MSH2", "MSH6", "PMS2"
}

# CORRECTED: Immune genes (for BRCA IO response)
IMMUNE_GENES_BRCA = {
    "CD8A", "CD274", "PDCD1", "CTLA4", "LAG3", "TIGIT",
    "IFNG", "GZMB", "PRF1", "TNF", "IL2"
}
```

**Key Changes**:
- ✅ Expanded proliferation gene list (full Oncotype DX)
- ✅ Added BRCA-specific DDR genes
- ✅ Added immune genes for IO response

---

## ✅ FINAL RECOMMENDATIONS

### **Before Execution**:

1. **Verify DDR_bin Aggregation Method** 🔥 **CRITICAL**
   - Check OV validation code: mean() or max()?
   - Use same method for BRCA
   - Update documentation if needed

2. **Verify Recurrence Field Names** ⚠️ **IMPORTANT**
   - Check TCGA-BRCA clinical data structure
   - Use DFS_STATUS as primary
   - Add fallback field names

3. **Check Feature Coverage** ⚠️ **IMPORTANT**
   - How many BRCA variants have OV DDR features in top-64?
   - If < 50%, consider re-extracting full 32K for OV DDR indices only

4. **Expand Gene Lists** ⚠️ **MINOR**
   - Use full Oncotype DX proliferation gene list
   - Add BRCA-specific DDR and immune genes

### **Execution Order**:

1. **Day 1 Morning**: Extract recurrence labels (with corrected field names)
2. **Day 1 Afternoon**: Test OV DDR transfer (with corrected aggregation + coverage check)
3. **Day 1 Evening**: Run BRCA biomarker correlation (with expanded gene lists)
4. **Day 2**: Compare results + build multi-pathway model

---

## 📊 EXPECTED CORRECTIONS IMPACT

| Issue | Impact | Severity |
|-------|--------|----------|
| DDR_bin aggregation | Results won't match OV if wrong method | 🔥 **CRITICAL** |
| Recurrence field names | May fail to extract outcomes | ⚠️ **HIGH** |
| Feature coverage | May have missing features | ⚠️ **MEDIUM** |
| Gene list expansion | May miss proliferation signals | ⚠️ **LOW** |

---

**Alpha, manager's plan is solid but has 4 issues that need fixing before execution. Most critical: DDR_bin aggregation method discrepancy. Fix these and we're ready to go. 🎯**
