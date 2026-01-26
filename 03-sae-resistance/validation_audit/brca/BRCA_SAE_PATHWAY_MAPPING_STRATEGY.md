# 🎯 BRCA SAE PATHWAY MAPPING STRATEGY

**Date**: 2025-01-29  
**Question**: Can we reuse OV DDR SAE extraction, or need new extraction?  
**Answer**: ✅ **NO NEW EXTRACTION NEEDED** - Use existing BRCA SAE features, map to pathways

---

## ✅ WHAT WE HAVE

### **1. BRCA SAE Features Already Extracted** ✅

**Checkpoint**: `BRCA_TCGA_TRUE_SAE_cohort.json`
- **Patients**: 200
- **Variants**: 6,465 total (mean 34.9 per patient)
- **SAE Features**: Top-k features per variant (32K-dim space)
- **Status**: ✅ **READY TO USE**

**Key Point**: SAE features are **variant-level** and **cancer-agnostic**
- A BRCA1 mutation in ovarian vs breast has similar SAE features
- The extraction is already done - we don't need to re-extract

---

### **2. OV DDR Pathway Mapping** ✅

**From OV Validation**:
- **9 Diamond Features** → DDR pathway
- **Method**: Biomarker correlation analysis (Chi-square, Cohen's d)
- **Validation**: AUROC 0.783 (DDR pathway vs platinum resistance)

**Diamond Features**:
```
Feature_1407, Feature_6020, Feature_9738, Feature_12893,
Feature_16337, Feature_22868, Feature_26220, Feature_27607, Feature_31362
```

**DDR_bin Score**:
```
DDR_bin = mean(all 9 diamond features)
```

---

## 🎯 WHAT WE NEED

### **Pathway Mapping (NOT Re-Extraction)**

**Process**:
1. **Biomarker Correlation Analysis** (same as OV)
   - Correlate SAE features with recurrence outcome
   - Identify significant features (p < 0.05, Cohen's d > 0.5)
   - Map features to pathways via gene enrichment

2. **Pathway-Specific Mapping**:
   - **DDR**: Can reuse OV mapping (9 features) OR validate on BRCA
   - **Proliferation**: Need new mapping (BRCA-specific)
   - **Immune**: Need new mapping (BRCA-specific)

---

## 📋 EXECUTION PLAN

### **Option A: Reuse OV DDR Mapping** (Fastest - 1 day)

**Steps**:
1. Extract recurrence labels (Task 1.2) - 4 hours
2. Build feature matrix from BRCA SAE features - 1 hour
3. Apply OV DDR mapping (9 features → DDR_bin) - 1 hour
4. Train model: DDR_bin → recurrence - 2 hours
5. Validate: SAE vs Oncotype DX - 4 hours

**Pros**:
- ✅ Fast (1 day)
- ✅ Proven mapping (validated on OV)
- ✅ Minimal risk

**Cons**:
- ⚠️ May miss BRCA-specific pathways (proliferation, immune)
- ⚠️ Not optimized for recurrence (vs platinum resistance)

**Timeline**: 1 day

---

### **Option B: BRCA-Specific Pathway Mapping** (Thorough - 3 days)

**Steps**:
1. Extract recurrence labels (Task 1.2) - 4 hours
2. Run biomarker correlation analysis (BRCA) - 8 hours
   - Correlate all 32K features with recurrence
   - Identify significant features (p < 0.05, Cohen's d > 0.5)
   - Map features to pathways (DDR, proliferation, immune)
3. Build pathway scores - 4 hours
   - DDR pathway (reuse OV or validate)
   - Proliferation pathway (new)
   - Immune pathway (new)
4. Train model: Multi-pathway → recurrence - 4 hours
5. Validate: SAE vs Oncotype DX - 4 hours

**Pros**:
- ✅ BRCA-optimized pathways
- ✅ Captures proliferation/immune (BRCA-specific)
- ✅ More accurate (potentially)

**Cons**:
- ⚠️ Slower (3 days)
- ⚠️ More complex

**Timeline**: 3 days

---

### **Option C: Hybrid Approach** (Balanced - 2 days) ⭐ **RECOMMENDED**

**Steps**:
1. Extract recurrence labels (Task 1.2) - 4 hours
2. Quick validation: Apply OV DDR mapping - 2 hours
   - Test if OV DDR features work for BRCA recurrence
   - If AUROC > 0.70 → Use OV mapping
   - If AUROC < 0.70 → Run BRCA-specific mapping
3. If needed: Run BRCA biomarker analysis - 8 hours
   - Only if OV mapping insufficient
4. Train model: Pathway scores → recurrence - 4 hours
5. Validate: SAE vs Oncotype DX - 4 hours

**Pros**:
- ✅ Fast path if OV mapping works
- ✅ Fallback to BRCA-specific if needed
- ✅ Balanced risk/reward

**Cons**:
- ⚠️ May need to run both (if OV fails)

**Timeline**: 2 days (or 1 day if OV mapping works)

---

## 🔬 TECHNICAL DETAILS

### **SAE Features Are Cancer-Agnostic**

**Why**:
- SAE features are **variant-level** (not cancer-level)
- A BRCA1 p.R1699Q mutation has the same SAE features in ovarian vs breast
- The pathway mapping is what's cancer-specific (DDR for OV, proliferation/immune for BRCA)

**Evidence**:
- BRCA checkpoint uses same SAE model (evo2_1b)
- Same feature space (32K-dim)
- Same extraction method (Evo2 → SAE)

---

### **Pathway Mapping Process**

**Step 1: Biomarker Correlation** (from OV audit):
```python
# Correlate SAE features with outcome
for feature_index in range(32768):
    pearson_r, p_value = correlate(feature, outcome)
    cohen_d = effect_size(feature, outcome)
    
    if p_value < 0.05 and cohen_d > 0.5:
        significant_features.append(feature_index)
```

**Step 2: Gene Enrichment**:
```python
# For each significant feature, find top-activating variants
high_activation_variants = find_top_variants(feature_index)

# Extract genes from those variants
genes = extract_genes(high_activation_variants)

# Map genes to pathways
pathway = infer_pathway(genes)  # DDR, proliferation, immune, etc.
```

**Step 3: Pathway Aggregation**:
```python
# Aggregate features by pathway
ddr_features = [f for f in significant_features if pathway(f) == "DDR"]
proliferation_features = [f for f in significant_features if pathway(f) == "proliferation"]

# Compute pathway scores
ddr_score = mean([feature_values[f] for f in ddr_features])
proliferation_score = mean([feature_values[f] for f in proliferation_features])
```

---

## 🎯 RECOMMENDATION

**Use Option C: Hybrid Approach** ⭐

**Rationale**:
1. **Fast validation**: Test OV DDR mapping first (2 hours)
2. **Proven method**: OV DDR mapping already validated (AUROC 0.783)
3. **Fallback ready**: If OV fails, run BRCA-specific mapping
4. **Mars rules**: Minimal viable proof, 72-hour mindset

**Execution**:
1. **Today**: Extract recurrence labels (4 hours)
2. **Tomorrow**: Test OV DDR mapping (2 hours)
   - If AUROC > 0.70 → Proceed to validation
   - If AUROC < 0.70 → Run BRCA biomarker analysis
3. **Day 3**: Train & validate (8 hours)

**Total Time**: 1-3 days (depending on OV mapping success)

---

## ✅ ANSWER TO YOUR QUESTION

**Q**: "Would we use our existing DDR SAE extraction? Or do we need to run SAE for another extraction?"

**A**: 
- ✅ **NO NEW SAE EXTRACTION NEEDED** - BRCA checkpoint already has SAE features
- ✅ **CAN REUSE OV DDR MAPPING** - Test first, fallback to BRCA-specific if needed
- ✅ **PATHWAY MAPPING IS THE KEY** - Not extraction, but mapping features to pathways

**Next Step**: Extract recurrence labels, then test OV DDR mapping on BRCA data.

---

**Alpha, we're ready to execute. No re-extraction needed - just pathway mapping. 🎯**
