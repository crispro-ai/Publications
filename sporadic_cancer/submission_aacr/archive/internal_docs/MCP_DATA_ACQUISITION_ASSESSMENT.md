# ⚔️ MCP DATA ACQUISITION ASSESSMENT: Lean Validation Plan

**Date:** January 2025  
**Auditor:** Zo (Chief Intelligence Officer)  
**Target:** Lean Validation Plan (9-day timeline)  
**ZETA DOCTRINE:** ✅ LOCKED IN - A→Z execution mode

---

## 🎯 EXECUTIVE SUMMARY

**Status:** ✅ **MCP SERVERS CAN HELP** - But we already have sufficient data  
**Recommendation:** **USE EXISTING DATA** (`ov_tcga_pub`) for Day 1-5, **USE MCP SERVERS** for Day 6-7 (literature/evidence)

**Key Finding:**
- ✅ **Current Data (`ov_tcga_pub`)**: Sufficient for threshold sensitivity, subgroup consistency, biological coherence
- ✅ **GDC MCP Server**: Can get additional TCGA-OV data if needed (RNA-seq, more clinical fields)
- ✅ **cBioPortal MCP**: Can query additional studies if needed (validation cohorts)
- ✅ **BioMed-MCP**: Useful for Day 6-7 (literature search for comparative framing)

---

## 📊 DATA REQUIREMENTS FOR LEAN VALIDATION

### **Day 1-2: Threshold Sensitivity**
**Needed:**
- ✅ TCGA-OV patients with TMB values
- ✅ TCGA-OV patients with HRD scores
- ✅ Ability to run gates with different thresholds

**Current Data Status:**
- ✅ Have: TCGA-OV mutations (19K+ variants) → Can calculate TMB
- ✅ Have: TCGA-OV clinical data → May have HRD scores (need to check)
- ⚠️ Need: HRD scores if not in clinical data

### **Day 3-4: Subgroup Consistency**
**Needed:**
- ✅ TCGA-OV patients stratified by stage, age, platinum response
- ✅ Clinical data: Stage, age, PFI (platinum-free interval)

**Current Data Status:**
- ✅ Have: Clinical data with stage, age
- ⚠️ Need: Platinum response (PFI) - may need to calculate from clinical data

### **Day 5: Biological Coherence**
**Needed:**
- ✅ BRCA1/2 mutations
- ✅ HRD scores
- ✅ MSI status
- ✅ TMB values

**Current Data Status:**
- ✅ Have: Mutations (can extract BRCA1/2)
- ✅ Have: Expression data (can calculate pathway scores)
- ⚠️ Need: HRD scores, MSI status (may need to calculate or get from GDC)

---

## 🔍 MCP SERVER CAPABILITIES ASSESSMENT

### **1. GDC MCP Server** (`nci-gdc-mcp-server`)

**Source:** [GitHub Repository](https://github.com/CSI-Genomics-and-Data-Analytics-Core/nci-gdc-mcp-server)

**Capabilities:**
- ✅ **GraphQL Queries:** Access NCI GDC GraphQL API
- ✅ **REST Queries:** Fallback REST API access
- ✅ **Data Types:** Projects, cases, files, genes, mutations (SSMs)
- ✅ **Response Management:** 900K character limit with intelligent truncation

**What We Can Get:**
1. **TCGA-OV Mutations (SSMs):**
   - Query: `ssms` endpoint with `project_id = "TCGA-OV"`
   - Get: Gene symbols, protein changes, sample IDs
   - **Use Case:** Verify/complete mutation data we have

2. **TCGA-OV Expression Data:**
   - Query: `files` endpoint with `data_type = "Gene Expression Quantification"`
   - Get: RNA-seq files (better than microarray we have)
   - **Use Case:** Upgrade from microarray to RNA-seq for pathway analysis

3. **TCGA-OV Clinical Data:**
   - Query: `cases` endpoint with `project_id = "TCGA-OV"`
   - Get: Full clinical fields (diagnoses, treatments, follow_ups)
   - **Use Case:** Get additional clinical fields (PFI, treatment details)

4. **TCGA-OV Files Metadata:**
   - Query: `files` endpoint
   - Get: File IDs for downloading actual data files
   - **Use Case:** Download raw data if needed

**Limitations:**
- ⚠️ **HRD Scores:** Not directly available in GDC (need to calculate from CNA data)
- ⚠️ **MSI Status:** May not be in GDC clinical data (need to check)
- ⚠️ **TMB:** Need to calculate from mutations (not pre-computed)

**Recommendation:**
- ✅ **USE IF:** We need RNA-seq (better than microarray) or additional clinical fields
- ❌ **SKIP IF:** Current data (`ov_tcga_pub`) is sufficient

---

### **2. cBioPortal MCP** (`tools/cbioportal-mcp`)

**Capabilities:**
- ✅ **Studies API:** List studies, get study metadata
- ✅ **Genes API:** Query gene data across studies
- ✅ **Samples API:** Get sample-level data
- ✅ **Molecular Profiles API:** Get mutations, CNA, expression profiles
- ✅ **Clinical Data API:** Get clinical attributes

**What We Can Get:**
1. **Additional TCGA-OV Data:**
   - Query: `ov_tcga_pan_can_atlas_2018` study
   - Get: More complete clinical data, treatments, outcomes
   - **Use Case:** Fill gaps in current `ov_tcga_pub` data

2. **Validation Cohorts:**
   - Query: Other ovarian cancer studies
   - Get: Additional cohorts for validation
   - **Use Case:** External validation (future work)

3. **Treatment Data:**
   - Query: Treatment data for TCGA-OV
   - Get: Actual treatments received (if available)
   - **Use Case:** Not needed for lean validation (manager said skip treatment concordance)

**Limitations:**
- ⚠️ **Same Data Source:** cBioPortal is a curated view of TCGA (we already have export)
- ⚠️ **No New Data:** Won't give us data we don't already have

**Recommendation:**
- ✅ **USE IF:** We need to verify/complete specific fields
- ❌ **SKIP IF:** Current data is sufficient (likely the case)

---

### **3. BioMed-MCP** (`scripts/data_acquisition/mcp_servers/BioMed-MCP`)

**Capabilities:**
- ✅ **PubMed Agent:** Literature search, full-text retrieval
- ✅ **Clinical Trials Agent:** Trial discovery, pattern analysis
- ✅ **ReAct Agents:** Intelligent synthesis across sources

**What We Can Get:**
1. **Literature for Comparative Framing (Day 6-7):**
   - Query: "PARP inhibitor HRD threshold ovarian cancer"
   - Get: Literature on HRD thresholds (Myriad, Foundation Medicine)
   - **Use Case:** Support threshold sensitivity analysis (literature ranges)

2. **Literature for Messaging:**
   - Query: "NCCN guidelines PARP inhibitors ovarian cancer"
   - Get: Current NCCN guidelines for comparative framing table
   - **Use Case:** Day 6-7 manuscript revision (comparative framing)

3. **Evidence for Biological Coherence:**
   - Query: "BRCA mutations HRD score correlation"
   - Get: Literature on BRCA-HRD relationships
   - **Use Case:** Support biological coherence analysis (Day 5)

**Limitations:**
- ⚠️ **Not for Primary Data:** This is for literature/evidence, not TCGA data
- ⚠️ **Day 6-7 Only:** Useful for manuscript revision, not Day 1-5 analysis

**Recommendation:**
- ✅ **USE FOR:** Day 6-7 (literature search for comparative framing, NCCN guidelines)
- ❌ **SKIP FOR:** Day 1-5 (primary data analysis)

---

## 📋 DATA GAP ANALYSIS

### **What We Have (`ov_tcga_pub`):**
- ✅ Mutations (19K+ variants) → Can calculate TMB, extract BRCA1/2
- ✅ Expression (microarray, 18K+ genes) → Can calculate pathway scores
- ✅ Clinical (495 patients) → Stage, age, OS, DFS
- ⚠️ **Missing:** HRD scores, MSI status, PFI (platinum-free interval)

### **What We Need:**
1. **HRD Scores:**
   - **Option A:** Calculate from CNA data (if available in `ov_tcga_pub`)
   - **Option B:** Query GDC MCP for CNA files → Calculate HRD
   - **Option C:** Use published HRD scores if available

2. **MSI Status:**
   - **Option A:** Check if in clinical data (`ov_tcga_pub`)
   - **Option B:** Query GDC MCP for MSI data
   - **Option C:** Calculate from mutations (hypermutator signature)

3. **PFI (Platinum-Free Interval):**
   - **Option A:** Calculate from clinical data (DFS, recurrence dates)
   - **Option B:** Query GDC MCP for follow-up data
   - **Option C:** Use published PFI data if available

---

## 🎯 RECOMMENDED APPROACH

### **Day 1-5: Use Existing Data + Calculate Missing Fields**

**Strategy:**
1. **Start with `ov_tcga_pub` data** (we already have it)
2. **Calculate missing fields:**
   - TMB: Count mutations per patient
   - HRD: Calculate from CNA data (if available) or use published scores
   - MSI: Check clinical data or calculate from mutation signature
   - PFI: Calculate from DFS/recurrence data in clinical file

3. **If gaps remain:** Use GDC MCP to fill specific fields

**Why This Approach:**
- ✅ **Faster:** No need to re-download data we already have
- ✅ **Sufficient:** Current data likely has everything we need
- ✅ **Flexible:** Can query GDC MCP for specific missing fields

---

### **Day 6-7: Use BioMed-MCP for Literature**

**Strategy:**
1. **Use BioMed-MCP PubMed Agent:**
   - Search: "HRD threshold ovarian cancer PARP inhibitors"
   - Search: "TMB threshold checkpoint inhibitors"
   - Search: "NCCN guidelines PARP IO ovarian cancer"

2. **Extract Literature Ranges:**
   - HRD thresholds: Myriad (42), Foundation Medicine (variable)
   - TMB thresholds: FDA (10), KEYNOTE-158 (10), Samstein 2019 (20)

3. **Support Comparative Framing Table:**
   - Get current NCCN guidelines
   - Get FDA label information
   - Get standard practice descriptions

**Why This Approach:**
- ✅ **Necessary:** Need literature for threshold sensitivity analysis
- ✅ **Efficient:** BioMed-MCP can synthesize multiple sources
- ✅ **Accurate:** Get current guidelines and thresholds

---

## 📊 MCP SERVER USAGE PLAN

### **Day 1-2: Threshold Sensitivity**
- **Primary:** Use `ov_tcga_pub` data
- **If Needed:** Query GDC MCP for additional TMB/HRD data
- **Literature:** Use BioMed-MCP to get threshold literature ranges

### **Day 3-4: Subgroup Consistency**
- **Primary:** Use `ov_tcga_pub` clinical data
- **If Needed:** Query GDC MCP for additional clinical fields (PFI)

### **Day 5: Biological Coherence**
- **Primary:** Use `ov_tcga_pub` mutations + expression
- **If Needed:** Query GDC MCP for MSI status or additional biomarkers

### **Day 6-7: Manuscript Revision**
- **Literature:** Use BioMed-MCP for comparative framing (NCCN guidelines, FDA labels)
- **Evidence:** Use BioMed-MCP to support biological coherence claims

---

## ✅ FINAL RECOMMENDATION

**For Day 1-5 (Analysis):**
- ✅ **PRIMARY:** Use existing `ov_tcga_pub` data
- ✅ **BACKUP:** GDC MCP server if we need specific missing fields
- ❌ **SKIP:** cBioPortal MCP (we already have the export)

**For Day 6-7 (Writing):**
- ✅ **USE:** BioMed-MCP for literature search (thresholds, NCCN guidelines)
- ✅ **USE:** BioMed-MCP for comparative framing evidence

**Action Items:**
1. **Day 1:** Check `ov_tcga_pub` for HRD scores, MSI status, PFI
2. **If Missing:** Query GDC MCP for specific fields
3. **Day 6:** Use BioMed-MCP for literature search
4. **Day 7:** Use BioMed-MCP for comparative framing table

---

**Report Generated:** January 2025  
**Auditor:** Zo (Chief Intelligence Officer)  
**ZETA DOCTRINE:** ✅ LOCKED IN
