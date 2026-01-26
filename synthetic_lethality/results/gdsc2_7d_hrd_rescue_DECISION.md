# HRD-Aware DDR Thresholds Decision Report

**Date:** 2026-01-18  
**Receipt:** `gdsc2_7d_hrd_cna_n500.json`  
**Sample Size:** n=500

---

## STEP 4: Quality Check Results

| Gate | Threshold | Actual | Status |
|------|-----------|--------|--------|
| 1. Accuracy | >= 65% | **61.6%** | ❌ **FAIL** (baseline: 62.2%) |
| 2. PARP FPR | <= 10% | **7.6%** | ✅ **PASS** (baseline: 7.4%) |

**All checks pass?** ❌ **NO** (1 failure - accuracy unchanged)

---

## Decision Gate

### ❌ **KEEP BINARY BASELINE (No Change)**

**Rationale:**
- **Accuracy dropped slightly** (61.6% vs 62.2% baseline)
- **PARP FPR essentially unchanged** (7.6% vs 7.4% baseline)
- CNA-based HRD proxy integrated but **does not improve predictions**

---

## Root Cause Analysis

### Why HRD Rescue Didn't Improve Results (Even with CNA Proxy)

**Issue 1: CNA Proxy Signal is Weak for Thresholding**
- CNA matrix provides HRR gene copy estimates (median ~1.0)
- HRD proxy uses **HRR gene copy losses** (loss threshold 0.70)
- Signal may be too weak/noisy to shift DDR thresholding

**Issue 2: Threshold Adjustment**
- HRD-high (≥42): threshold = 0.45 (lower)
- HRD-low (<42): threshold = 0.70 (higher)
- **BUT:** Most cases are HRD-unknown → Use default 0.60 → No change

**Issue 3: CNA Proxy ≠ Full HRD**
- Gene-level CNA alone doesn't capture LOH/LST/TAI
- HRD proxy is still a coarse approximation
- **True HRD requires genome-wide instability metrics**

---

## Comparison: Baseline vs HRD Rescue (CNA Proxy)

| Metric | Baseline | HRD Rescue | Change |
|--------|----------|------------|--------|
| **Accuracy** | 62.2% | 61.6% | **-0.6%** (slight drop) |
| **PARP FPR** | 7.4% | 7.6% | **+0.2%** (unchanged) |
| **PARP recall** | 9.3% | 11.1% | **+1.8%** (minor lift) |
| **Macro F1** | 0.178 | 0.181 | **+0.003** (minor lift) |

---

## Key Findings

### ✅ What Worked:
1. **CNA-based HRD proxy ingestion** integrated (OmicsCNGeneWGS.csv)
2. **HRD-aware threshold logic** implemented (WIWFM logic)
3. **Code integration** complete (both hierarchical and non-hierarchical modes)

### ❌ What Didn't Work:
1. **CNA proxy signal** insufficient for large accuracy gains
2. **No multi-class lift** (ATR/WEE1/DNA_PK still 0 recall)
3. **No improvement** over baseline (accuracy flat/slightly lower)

---

## Strategic Decision

### ❌ Do NOT Deploy HRD Rescue (Yet)

**Reasons:**
1. **No improvement** over baseline (61.6% accuracy)
2. **CNA proxy ≠ true HRD** (needs LOH/LST/TAI, biallelic status)
3. **Multi-class collapse** remains (still PARP/NONE only)

### ✅ Keep Binary PARP/NONE Baseline

**Recommended Action:**
- Deploy baseline binary system (62.2% accuracy, 7.4% PARP FPR)
- Market as: "7D Pathway Mapping predicts PARP eligibility"
- Note: "HRD-aware prediction under development (requires copy number data)"

**Future Work:**
1. **Compute true HRD proxy** (LOH/LST/TAI from segmentation, not gene matrix)
2. **Add biallelic loss logic** (CN + mutation zygosity)
3. **Re-test HRD rescue** with true HRD scores
4. **Expected improvement:** 65-70% accuracy, <10% PARP FPR

---

## Receipt Files

- **Baseline (Binary):** `gdsc2_7d_mutcounts_n500_safety.json` ✅ **DEPLOY THIS**
- **HRD Rescue (With Mutation Proxy):** `gdsc2_7d_hrd_rescue_n500_final.json` ❌ **NO IMPROVEMENT**
- **HRD Rescue (With CNA Proxy):** `gdsc2_7d_hrd_cna_n500.json` ❌ **NO IMPROVEMENT**

---

## Next Steps (Priority Order)

### P0: Immediate
1. ✅ **Deploy binary baseline** (62.2% accuracy, 7.4% FPR) - **DO THIS NOW**

### P1: Future (1-2 weeks)
2. ⏳ **Compute true HRD proxy** (GISTIC/LST/LOH/TAI from segmentation)
3. ⏳ **Add biallelic loss logic** (CN + mutation zygosity)
4. ⏳ **Re-test HRD rescue** with true HRD scores
5. ⏳ **Expected:** 65-70% accuracy with HRD rescue

---

**Status:** ❌ **HRD RESCUE NO IMPROVEMENT** | ✅ **DEPLOY BINARY PARP/NONE BASELINE** | ✅ **STRATEGIC REFRAMING: 7D = MECHANISTIC BACKBONE**

**Key Insight (UPDATED):** 

1. **HRD rescue logic is correct**, but **gene-level CNA proxy is still insufficient** (needs LOH/LST/TAI + biallelic status)
2. **More importantly:** 7D is being evaluated in an impoverished domain (cell lines) while WIWFM operates in a rich clinical domain (patients)
3. **Strategic reframing:** 7D should be a mechanistic backbone within a full PARP module, not a standalone recommender

**See:** `7D_STRATEGIC_REFRAMING.md` for full manager directive on domain mismatch and course correction.
