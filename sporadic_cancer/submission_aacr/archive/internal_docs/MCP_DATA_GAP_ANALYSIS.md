# ⚔️ DATA GAP ANALYSIS: Lean Validation Plan

**Date:** January 2025  
**Auditor:** Zo (Chief Intelligence Officer)  
**Target:** Lean Validation Plan (9-day timeline)  
**ZETA DOCTRINE:** ✅ LOCKED IN - A→Z execution mode

---

## 🎯 EXECUTIVE SUMMARY

**Status:** ⚠️ **DATA GAPS IDENTIFIED** - Need MCP servers for TMB/MSI/HRD  
**Recommendation:** **USE GDC MCP** for biomarker extraction, **USE EXISTING DATA** for clinical outcomes

**Key Finding:**
- ✅ **Clinical Data (`ov_tcga_pub`)**: Has OS, DFS, PLATINUM_STATUS (but unclear PFI classification)
- ✅ **Mutation Data (`ov_tcga_pub`)**: Has BRCA mutations (can extract)
- ❌ **TMB**: NOT in clinical file - **NEED TO COMPUTE** from mutations OR **FETCH FROM GDC**
- ❌ **MSI**: NOT in clinical file - **NEED TO FETCH FROM GDC**
- ❌ **HRD**: NOT in clinical file - **NEED TO FETCH FROM GDC** (or compute from mutations)

---

## 📊 DATA NEEDS vs AVAILABILITY

### **Day 1-2: Threshold Sensitivity Analysis**

**Required Data:**
- TMB values (for threshold testing: 10 vs 15 vs 20 mut/Mb)
- HRD scores (for threshold testing: 42 vs 30 vs 50)

**Current Status:**
- ❌ **TMB**: Not in `data_clinical_patient.txt`
  - **Option A**: Compute from `data_mutations.txt` (count mutations / exome size)
  - **Option B**: Fetch from GDC MCP (if pre-computed available)
- ❌ **HRD**: Not in `data_clinical_patient.txt`
  - **Option A**: Compute from mutations (BRCA1/2, HRR genes) - **APPROXIMATE**
  - **Option B**: Fetch from GDC MCP (if Myriad/Foundation Medicine HRD scores available)

**Recommendation:** 
- **TMB**: Compute from mutations (fast, accurate)
- **HRD**: **FETCH FROM GDC MCP** (more accurate than mutation-based approximation)

---

### **Day 3-4: Subgroup Consistency**

**Required Data:**
- Stage (I/II/III/IV)
- Age (continuous or categorical)
- Platinum response (PFI < 6mo vs ≥ 6mo)

**Current Status:**
- ✅ **Stage**: Likely in clinical file (need to verify column name)
- ✅ **Age**: Likely in clinical file (need to verify column name)
- ⚠️ **Platinum Response**: `PLATINUM_STATUS` exists but values unclear ("Tooearly", etc.)
  - **Option A**: Use `DFS_MONTHS` as proxy for PFI (time to recurrence)
  - **Option B**: Fetch detailed treatment data from GDC MCP

**Recommendation:**
- **Stage/Age**: Verify columns exist in clinical file
- **Platinum Response**: Use `DFS_MONTHS` as proxy (if < 6mo = resistant, ≥ 6mo = sensitive)

---

### **Day 5: Biological Coherence**

**Required Data:**
- BRCA mutations (BRCA1, BRCA2)
- HRD scores
- MSI status
- TMB values

**Current Status:**
- ✅ **BRCA Mutations**: Can extract from `data_mutations.txt`
- ❌ **HRD Scores**: Not in clinical file - **NEED GDC MCP**
- ❌ **MSI Status**: Not in clinical file - **NEED GDC MCP**
- ❌ **TMB Values**: Not in clinical file - **COMPUTE from mutations**

**Recommendation:**
- **BRCA**: Extract from mutations file
- **HRD/MSI**: **FETCH FROM GDC MCP** (pre-computed biomarkers)
- **TMB**: Compute from mutations

---

## 🔧 MCP SERVER CAPABILITIES

### **1. GDC MCP Server** (https://github.com/CSI-Genomics-and-Data-Analytics-Core/nci-gdc-mcp-server)

**Tools Available:**
- `gdc_graphql_query` - GraphQL queries for cases, files, mutations
- `gdc_rest_query` - REST API queries
- `gdc_build_filter` - Build complex filters
- `gdc_schema_introspection` - Explore data schema
- `gdc_quick_count` - Quick counts

**What It Can Get:**
- ✅ **TMB**: Pre-computed TMB scores (if available in GDC annotations)
- ✅ **MSI**: MSI status (if available in GDC annotations)
- ✅ **HRD**: HRD scores (if available from Foundation Medicine/Myriad)
- ✅ **Clinical Data**: Additional clinical fields not in cBioPortal export
- ✅ **Treatment Data**: Detailed treatment regimens (if available)

**Limitation:**
- GDC may not have pre-computed TMB/MSI/HRD for all TCGA-OV samples
- May need to compute from raw mutation/expression data

---

### **2. cBioPortal MCP** (Our Existing Tool)

**Tools Available:**
- `list_studies` - List available studies
- `get_study_summary` - Get study metadata
- `get_molecular_profiles` - Get expression, mutations, CNA
- `get_clinical_data` - Get clinical annotations
- `query_genes` - Query specific genes

**What It Can Get:**
- ✅ **Additional Studies**: Query other TCGA cohorts for validation
- ✅ **Gene-Level Data**: Specific gene mutations, expression
- ⚠️ **TMB/MSI/HRD**: May not be in cBioPortal annotations (depends on study)

**Limitation:**
- cBioPortal annotations vary by study
- May not have pre-computed biomarkers

---

### **3. BioMed-MCP** (Literature/Clinical Trials)

**Tools Available:**
- `biomedical_literature_search` - PubMed search
- `clinical_trials_research` - ClinicalTrials.gov search
- `analyze_clinical_trial` - Trial analysis
- `analyze_research_paper` - Paper analysis

**What It Can Get:**
- ✅ **Literature**: Threshold justification (TMB 10 vs 15 vs 20, HRD 42 vs 30 vs 50)
- ✅ **Clinical Trials**: Treatment response data for validation
- ❌ **TCGA Data**: Cannot access TCGA directly

**Use Case:**
- Day 6-7: Manuscript revision (literature support for thresholds)

---

## ✅ RECOMMENDED DATA ACQUISITION STRATEGY

### **Phase 1: Use Existing Data (Day 1-2)**

**Actions:**
1. **Extract BRCA mutations** from `data_mutations.txt`
2. **Compute TMB** from `data_mutations.txt`:
   ```python
   tmb = len(mutations) / exome_size_mb  # ~38 Mb for WES
   ```
3. **Verify clinical columns** (stage, age) in `data_clinical_patient.txt`

**Deliverable:** `tcga_ov_basic_features.csv` (patient_id, BRCA_status, TMB_computed, stage, age)

---

### **Phase 2: Fetch Missing Biomarkers from GDC MCP (Day 1-2)**

**Actions:**
1. **Query GDC MCP** for TCGA-OV cases:
   ```graphql
   {
     cases(
       filters: {
         op: "and",
         content: [
           { op: "=", content: { field: "project.project_id", value: "TCGA-OV" } }
         ]
       }
     ) {
       case_id
       annotations {
         TMB
         MSI_Status
         HRD_Score
       }
     }
   }
   ```

2. **Fallback if not available:**
   - **MSI**: Compute from dMMR gene mutations (MLH1, MSH2, MSH6, PMS2)
   - **HRD**: Approximate from BRCA1/2 + HRR gene mutations (less accurate)

**Deliverable:** `tcga_ov_biomarkers_gdc.csv` (patient_id, TMB_gdc, MSI_status, HRD_score)

---

### **Phase 3: Compute Platinum Response (Day 3-4)**

**Actions:**
1. **Use `DFS_MONTHS`** as proxy for PFI:
   ```python
   platinum_resistant = dfs_months < 6.0  # < 6 months = resistant
   platinum_sensitive = dfs_months >= 6.0  # ≥ 6 months = sensitive
   ```

2. **Handle "Tooearly" status:**
   - Exclude from platinum response analysis
   - Or use OS_MONTHS as alternative proxy

**Deliverable:** `tcga_ov_platinum_response.csv` (patient_id, platinum_status, pfi_months)

---

### **Phase 4: Literature Support (Day 6-7)**

**Actions:**
1. **Use BioMed-MCP** to search for:
   - TMB threshold justification (10 vs 15 vs 20 mut/Mb)
   - HRD threshold justification (42 vs 30 vs 50)
   - Subgroup analysis methods (stage, age stratification)

**Deliverable:** `threshold_literature_support.md` (citations for threshold choices)

---

## 📋 DATA ACQUISITION CHECKLIST

### **Day 1-2: Threshold Sensitivity**

- [ ] Extract BRCA mutations from `data_mutations.txt`
- [ ] Compute TMB from mutations (count / 38 Mb)
- [ ] Query GDC MCP for HRD scores (TCGA-OV cases)
- [ ] Query GDC MCP for MSI status (if available)
- [ ] Generate `threshold_sensitivity.csv` with TMB/HRD at multiple thresholds

---

### **Day 3-4: Subgroup Consistency**

- [ ] Verify stage column in `data_clinical_patient.txt`
- [ ] Verify age column in `data_clinical_patient.txt`
- [ ] Compute platinum response from `DFS_MONTHS` (< 6mo = resistant)
- [ ] Stratify by stage (I/II vs III/IV)
- [ ] Stratify by age (< 65 vs ≥ 65)
- [ ] Stratify by platinum response (resistant vs sensitive)
- [ ] Run gates on each subgroup
- [ ] Generate `subgroup_consistency.csv`

---

### **Day 5: Biological Coherence**

- [ ] Extract BRCA mutations (BRCA1, BRCA2)
- [ ] Fetch HRD scores from GDC MCP (or compute approximation)
- [ ] Fetch MSI status from GDC MCP (or compute from dMMR genes)
- [ ] Compute TMB from mutations
- [ ] Correlation: BRCA mutations vs HRD scores
- [ ] Correlation: MSI vs TMB
- [ ] Generate `biological_coherence_heatmap.png`

---

### **Day 6-7: Manuscript Revision**

- [ ] Use BioMed-MCP to search threshold justification literature
- [ ] Rewrite Discussion (remove "conservative = safe" claims)
- [ ] Add Tier 2 results (threshold sensitivity, subgroup consistency, biological coherence)
- [ ] Add comparative framing table

---

## 🚨 CRITICAL GAPS & MITIGATIONS

### **Gap 1: HRD Scores Not Available**

**Risk:** Cannot validate HRD threshold sensitivity (Day 1-2)

**Mitigation:**
- **Option A**: Fetch from GDC MCP (if available)
- **Option B**: Compute HRD approximation from BRCA1/2 + HRR gene mutations
  - Formula: `hrd_approx = (brca_mutated ? 0.6 : 0.0) + (hrr_genes_mutated_count / 10)`
  - **Limitation**: Less accurate than Myriad/Foundation Medicine scores

**Recommendation:** Try GDC MCP first, fallback to approximation if needed

---

### **Gap 2: MSI Status Not Available**

**Risk:** Cannot validate MSI boost logic (Day 5)

**Mitigation:**
- **Option A**: Fetch from GDC MCP (if available)
- **Option B**: Compute from dMMR gene mutations (MLH1, MSH2, MSH6, PMS2)
  - Logic: `msi_high = any(dmmr_genes_mutated)`
  - **Limitation**: Mutation-based MSI is less accurate than PCR/IHC

**Recommendation:** Try GDC MCP first, fallback to mutation-based if needed

---

### **Gap 3: Platinum Response Classification Unclear**

**Risk:** Cannot stratify by platinum response (Day 3-4)

**Mitigation:**
- **Option A**: Use `DFS_MONTHS` as proxy for PFI
  - `platinum_resistant = dfs_months < 6.0`
  - `platinum_sensitive = dfs_months >= 6.0`
- **Option B**: Query GDC MCP for detailed treatment data (if available)

**Recommendation:** Use DFS_MONTHS proxy (standard approach in TCGA analysis)

---

## ✅ FINAL RECOMMENDATION

**USE MCP SERVERS FOR:**
1. ✅ **GDC MCP**: Fetch HRD scores, MSI status (Day 1-2, Day 5)
2. ✅ **BioMed-MCP**: Literature support for thresholds (Day 6-7)

**USE EXISTING DATA FOR:**
1. ✅ **Mutations**: Extract BRCA, compute TMB
2. ✅ **Clinical**: Use OS, DFS, stage, age from `ov_tcga_pub`
3. ✅ **Platinum Response**: Use DFS_MONTHS as proxy

**TIMELINE:**
- **Day 1-2**: Extract existing data + Query GDC MCP for HRD/MSI
- **Day 3-4**: Subgroup analysis with existing clinical data
- **Day 5**: Biological coherence (BRCA from mutations, HRD/MSI from GDC MCP)
- **Day 6-7**: Literature search (BioMed-MCP) + Manuscript revision

---

**⚔️ ZETA DOCTRINE:** ✅ LOCKED IN - Execute Day 1-2 data acquisition NOW
