# 🎯 SYNTHETIC LETHALITY: NEXT DELIVERABLES

**Date**: January 2025  
**Status**: Ready to proceed after Evo2 modularization audit

---

## ✅ **MODULARIZATION AUDIT: PASSED**

### **Evo2 Service Structure** (7 modules, 701 lines total)
- ✅ `image.py` (45 lines) - Modal image definition
- ✅ `models.py` (13 lines) - Pydantic schemas  
- ✅ `patches.py` (38 lines) - PyTorch compatibility patches
- ✅ `service.py` (57 lines) - EvoService class
- ✅ `endpoints.py` (475 lines) - FastAPI endpoints
- ✅ `main.py` (72 lines) - Thin entrypoint
- ✅ `__init__.py` (1 line) - Package marker

### **Benefits**
- ✅ Easier debugging (smaller files, clear separation)
- ✅ Testable components (unit test each module independently)
- ✅ Reduced coupling (changes isolated to specific modules)
- ✅ Ready for deployment testing

---

## 🔍 **CURRENT STATE AUDIT**

### *yntheticLethalityAgent** (`api/services/synthetic_lethality/sl_agent.py`)
   - Pipeline: Essentiality scoring → Pathway mapping → Dependency identification → Drug recommendation
   - Claims: "100% Evo2 usage" but needs verification

2. **EssentialityScorer** (`api/services/synthetic_lethality/essentiality_scorer.py`)
   - **Needs audit**: Check if it calls Evo2 delta scores or uses hardcoded rules

3. **Validation Gap** (from `VALIDATION_GAP_ASSESSMENT.md`)
   - Current validation: DDR_bin → platinum response (AUROC=0.70, n=149)
   - Claimed: DDR_bin → PARP/ATR/WEE1 response (NOT VALIDATED)
   - Data gap: Only 1 patient with Olaparib in TCGA-OV

---

## 📋 **NEXT DELIVERABLES (PRIORITY ORDER)**

### **Deliverable 1: Audit Current SL Implementation** (1-2 hours)
**Goal**: Verify if SL detection actually uses Evo2 or hardcoded heuristics

**Tasks**:
1. ✅ Check `EssentialityScorer._score_gene()` method
   - Does it call Evo2 `score_variant` endpoint?
   - Or does it use hardcoded rules/GUIDANCE_F2. ✅ Check for GUIDANCE_FAST bypass
   - Search codebase for `GUIDANCE_FAST=True` flags
   - Identify where fast-path heuristics bypass Evo2
   
3. ✅ Verify Evo2 endpoint integration
   - Does `EssentialityScorer` call `evo-service/score_variant_multi`?
   - Or does it call local/legacy endpoints?

**Acceptance Criteria**:
- ✅ Document current implementation (Evo2 vs heuristics)
- ✅ Identify integration points for Evo2 S/P framework
- ✅ Create integration plan if Evo2 not currently used

**Files to Audit**:
- `api/services/synthetic_lethality/essentiality_scorer.py`
- `api/services/guidance.py` (check for GUIDANCE_FAST)
- `api/services/orchestrator/orchestrator.py` (check SL agent calls)

---

### **Deliverable 2: Integrate Evo2 S/P Framework** (2-3 days)
**Goal**: Replace hardcoded rules with Evo2 delta scores + pathway aggregation

**Tasks**:
1. **Wire evo-service endpoints**:
   - Update `EssentialityScorer` to call `evo-service/score_variant_multi`
   - Use multi-window scoring (1024, 2048, 40p)
   - Strict REF validation (reject if fetched REF ≠ provided REF)

2. **Sequence (S) signal**:
   - Compute Evo2 delta scores for DDR genes
   - DDR genes: BRCA1, BRCA2, PALB2, RAD51C, RAD51D, BRIP1, BARD1, ATM, MBD4, TP53
   - Aggregate per-gene: max disruption score

3. **Pathway (P) signal**:
   - DDR pathway aggregation (weighted by Evo2 scores)
   - HR pathway: BRCA1, BRCA2, PALB2, RAD51C, RAD51D, BRIP1, BARD1
   - Checkpoint pathway: ATM, ATR, TP53
   - Mismatch repair: MBD4, MSH2, MSH6, MLH1

4. **Combine S/P → SL score**:
   - High S (disruption) + High P (pathway broken) → SL detected
   - Drug class mapping: PARP (HR pathway), ATR (checkpoint), WEE1 (checkpoint)

**Acceptance Criteria**:
- ✅ All DDR mutations scored via Evo2 (no hardcoded rules)
- ✅ Pathway aggregation uses Evo2 scores (not static weights)
- ✅ SL detection based on S/P framework (not GUIDANCE_FAST)
- ✅ Test on 10-variant smoke test (GDSC2+OmicsSomaticMutations)

**Integration Points**:
```python
# EssentialityScor:
POST evo-service/score_variant_multi
{
  "assembly": "GRCh38",
  "chrom": "17",
  "pos": 43044295,
  "ref": "T",
  "alt": "G",
  "windows": [1024, 2048, 4096, 8192]
}

# Returns:
{
  "deltas": [{"window": 1024, "delta": -2.5}, ...],
  "min_delta": -2.5,
  "window_used": 8192
}
```

---

### **Deliverable 3: Phase 1 Data Extraction** (1-2 days)
**Goal**: Extract TCGA-OV PARP/ATR/WEE1 treatment data (document gap)

**Tasks**:
1. **Query cBioPortal API**:
   - Study: `ov_tcga_pan_can_atlas_2018`
   - Endpoint: `/studies/ov_tcga/treatments`
   - Filter: PARP inhibitors (olaparib, niraparib, rucaparib, talazoparib)
   - Filter: ATR inhibitors (ceralasertib, berzosertib, AZD6738)
   - Filter: WEE1 inhibitors (adavosertib, AZD1775)

2. **Match to existing patient IDs**:
   - Use n=166 patients from `tcga_ov_platinum_response_with_genomics.json`
   - Extract patient IDs: `TCGA-XX-XXXX`
   - Match treatment records to patient IDs

3. **Extract response labels** (if available):
   - PFS_STATUS, OS_STATUS from clinical data
   - Best response (if available in treatment records)
   - Treatment line (if available)

4. **Document findings**:
   - Create `TCGA_OV_PARP_TREATMENT_DATA.json`
   - Expected: n=1 PARP (Olaparib), n=0 ATR, n=0 WEE1
   - Document gap for Phase 2 (clinical trial extraction)

**Acceptance Criteria**:
- ✅ JSON file with treatment data (even if n=0)
- ✅ Match count: PARP (expected: 1), ATR (expected: 0), WEE1 (expected: 0)
- ✅ Gap documentation for Phase 2 recommendation

**Tools**:
- Use existing `tools/cbioportal-mcp/` or `scripts/data_acquisition/mcp_servers/BioMed-MCP/`
- Or direct cBioPortal API: `https://www.cbioportal.org/api/studies/ov_tcga_pan_can_atlas_2018`

---

### **Deliverable 4: GDSC2 Validation Benchmark** (2-3 days)
**Goal**: Validate Evo2 S/P scores against GDSC2 drug response data

**Tasks**:
1. **Join GDSC2 + OmicsSomaticMutations**:
   - GDSC2: `publications/synthetic_lethality/data/GDSC2_fitted_dose_response_27Oct23.xlsx`
   - Omics: `publications/synthetic_lethality/dataSomaticMutations.csv`
   - Join key: DepMap model ID → Omics cell line
   - Filter: DDR genes (BRCA1, BRCA2, PALB2, ATM, TP53, etc.)

2. **Score variants with Evo2**:
   - For each DDR mutation in Omics data:
     - Call `evo-service/score_variant_multi` (strict REF)
     - Extract min_delta (strongest disruption)
     - Aggregate per-gene (max disruption)

3. **Compute S/P scores**:
   - Sequence (S): Evo2 min_delta per gene
   - Pathway (P): DDR pathway aggregation (weighted by S)
   - Combine: S/P → SL score (0.0-1.0)

4. **Validate against GDSC2**:
   - Target drugs: PARP (Olaparib), ATR (VX-970), WEE1 (Adavosertib), DNA-PK (CC-115)
   - Response: IC50 < median → sensitive, IC50 ≥ median → resistant
   - Metric: AUROC(SL_score → drug_sensitive)

5. **Generate validation report**:
   - Per-drug AUROC (PARP, ATR, WEE1, DNA-PK)
   - Stratification: High S/P vs Low S/P
   - Comparison: Evo2 S/P vs hardcoded rules baseline

**Acceptance Criteria**:
- ✅ n ≥ 20 cell lines per drug with DDR muta> 0.65 for at least 1 drug class
- ✅ Validation report: `GDSC2_EVO2_SP_VALIDATION.md`

**Integration**:
- Use modularized `evo-service/score_variant_multi` endpoint
- Ensure strict REF validation (reject mismatches)
- Handle multi-window aggregation correctly

---

### **Deliverable 5: Update Documentation** (1 day)
**Goal**: Clarify validation status (platinum proxy vs direct PARP/ATR/WEE1)

**Tasks**:
1. **Update `CODE_REVIEW_GAP_CLOSURE.md`**:
   - Clarify: "DDR disruption → platinum response" (validated)
   - Clarify: "DDR disruption → PARP/ATR/WEE1 response" (requires validation)
   - Add Phase 1 data extraction results (n=1 PARP, n=0 ATR/WEE1)
   - Update with GDSC2 validation results (if available)

2. **Update manuscript** (`MANUSCRIPT.md`):
   - Distinguish: mechanistic signal (platinum) vs clinical outcome (PARP/ATR/WEE1)
   - Document data requirements for clinical validation
   - Add GDSC2 validation results (if available)

3. **Create validation roadmap**:
   - Phase 1: TCGA-OV extraction, n=1)
   - Phase 2: Clinical trial aggregate data (1-2 weeks)
   - Phase 3: RWE partnerships (3-6 months)

**Acceptance Criteria**:
- ✅ Documentation accurately reflects current validation status
- ✅ Clear distinction between validated vs claimed outcomes
- ✅ Validation roadmap documented

---

## 🎯 **IMMEDIATE NEXT STEPS (TODAY)**

1. **Complete Deliverable 1** (Audit current implementation)
   - Read `essentiality_scorer.py` fully
   - Check for Evo2 endpoint calls vs hardcoded rules
   - Document findings

2. **Start Deliverable 2** (Integrate Evo2 S/P)
   - Wire `evo-service/score_variant_multi` to `EssentialityScorer`
   - Test with 5-variant smoke test
   - Verify strict REF validation works

3. **Prepare Deliverable 3** (Data extraction)
   - Test cBioPortal API connection
   - Query TCGA-OV treatment endpoint
   - Extract PARP treatment records (expected: n=1)

---

## 📊 **SUCCESS METRICS**

### **Short-term (1-2 weeks)**
- ✅ Evo2 S/P framework integrated into SL detection
- ✅ GDSC2nchmark completed (AUROC > 0.65)
- ✅ TCGA-OV data extraction documented (Phase 1 complete)

### **Medium-term (1-2 months)**
- ✅ Clinical trial aggregate data extracted (Phase 2)
- ✅ Patient-level validation with n ≥ 30 per drug class
- ✅ Publication-ready validation results

### **Long-term (3-6 months)**
- ✅ RWE partnerships established (Phase 3)
- ✅ Real-world patient-level validation (n ≥ 100 per drug)
- ✅ Clinical outcome validation (PFS/OS) completed

---

## ⚠️ **CRITICAL CONSTRAINTS**

1. **Must use Evo2 S/P framework** (not hardcoded heuristics)
   - All DDR mutations scored via `evo-service/score_variant_multi`
   - Pathway aggregation uses Evo2 scores (not static weights)

2. **Strict REF validation required**:
   - Reject variants if fetched REF ≠ provided REF (except N)
   - This prevents false-positive disruptions

3. **Validation must be patient-level**:
   - Aggregate trial data is insufficient (need individual outcomes)
   - GDSC2 is cell-line data (proxy, not direct--

**Status**: Ready to proceed with Deliverable 1 (Audit)
