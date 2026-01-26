# PARP Identification: 7D Framework vs WIWFM Sporadic Gates - Critical Discovery

**Date:** 2026-01-18  
**Purpose:** Discover what WIWFM sporadic gates do for PARP that our 7D approach is missing

---

## EXECUTIVE SUMMARY

**Key Discovery:** The **WIWFM sporadic gates framework has a PARP gating system** that uses **germline status + HRD score** to penalize/rescue PARP predictions, which our 7D approach completely lacks!

**Critical Missing Pieces:**
1. ❌ **No germline status consideration** (all cell lines treated as germline-negative)
2. ❌ **No HRD score integration** (HRD rescue mechanism missing)
3. ❌ **No PARP penalty for low-HRD cases** (WIWFM applies 0.6x penalty)
4. ⚠️ **No confidence capping** (WIWFM caps by completeness level)

---

## HOW WIWFM IDENTIFIES PARP

### PARP Gate Logic (from `parp_gates.py`)

```python
# Gate 1: PARP penalty/rescue based on germline + HRD
if drug_class == "PARP inhibitor":
    germline = germline_status  # "positive", "negative", "unknown"
    hrd_score = tumor_context.get("hrd_score")  # 0-100
    
    if germline == "positive":
        factor = 1.0  # No penalty for germline carriers
    elif germline == "negative":
        if hrd_score is None:
            factor = 0.8  # Unknown HRD → partial penalty
        elif hrd_score >= 42.0:
            factor = 1.0  # HRD-high → rescue (no penalty)
        else:
            factor = 0.6  # HRD-low → STRONG penalty
    else:  # unknown
        factor = 0.8  # Partial penalty
    
    efficacy_score *= factor
    # Also adjusts confidence based on rationale
```

**Key Thresholds:**
- **HRD ≥ 42.0**: Rescue (no penalty for germline-negative)
- **HRD < 42.0**: Penalty (0.6x efficacy)
- **HRD unknown**: Partial penalty (0.8x efficacy)

---

## COMPARISON: 7D vs WIWFM

| Feature | 7D Framework | WIWFM Sporadic Gates | Gap |
|---------|-------------|---------------------|-----|
| **Germline Status** | ❌ Not considered | ✅ Used for PARP gating | ❌ **Critical Gap** |
| **HRD Score** | ❌ Not used | ✅ HRD ≥ 42 rescues PARP | ❌ **Critical Gap** |
| **PARP Penalty** | ❌ Binary threshold only (DDR ≥ 0.60) | ✅ 0.6x for low-HRD germline-negative | ❌ **Critical Gap** |
| **Gene-Specific Logic** | ⚠️ Attempted (not working) | ✅ Integrated in pathway scoring | ⚠️ **Partial Gap** |
| **S/P/E Scoring** | ❌ Pathway-only | ✅ Sequence + Pathway + Evidence | ❌ **Gap** |
| **Confidence Capping** | ❌ Not used | ✅ L0/L1/L2 caps (0.4/0.6/1.0) | ⚠️ **Gap** |

---

## ROOT CAUSE OF 7D LIMITATIONS

### Why Our Accuracy is Low (62% → 30% with multi-class)

**Issue 1: No HRD Rescue**
- WIWFM: Germline-negative + HRD-high (≥42) → **No penalty** (1.0x)
- 7D: All germline-negative cases → **Same threshold** (DDR ≥ 0.60)
- **Impact:** We're penalizing HRD-high cases that should get PARP

**Issue 2: No PARP Penalty for Low-HRD**
- WIWFM: Germline-negative + HRD-low (<42) → **0.6x penalty**
- 7D: Binary threshold (DDR ≥ 0.60) → **No penalty differentiation**
- **Impact:** We're predicting PARP for low-HRD cases that shouldn't get it

**Issue 3: No Germline Status**
- WIWFM: Germline-positive → **Always 1.0x** (no penalty)
- 7D: All cases treated equally → **No distinction**
- **Impact:** We're not prioritizing germline carriers (highest PARP benefit)

---

## WHAT WE'RE MISSING (Priority Order)

### P0: Critical (Why PARP FPR is High)

1. **HRD Rescue Mechanism**
   - **Current:** Binary DDR threshold (≥0.60)
   - **Needed:** HRD ≥ 42 → Lower DDR threshold (e.g., ≥0.40 for HRD-high)
   - **Impact:** Should improve PARP recall for HRD-high cases

2. **PARP Penalty for Low-HRD**
   - **Current:** Same threshold for all cases
   - **Needed:** HRD < 42 → Higher DDR threshold (e.g., ≥0.70) or penalty
   - **Impact:** Should reduce PARP false positives

3. **Germline Status Integration**
   - **Current:** Not available in GDSC2 (all cell lines are germline-negative by default)
   - **Needed:** If germline-positive → Lower threshold (e.g., ≥0.40)
   - **Impact:** Future improvement (need germline data)

### P1: Important (Why Multi-Class Fails)

4. **Gene-Specific Logic** (already attempted, needs fix)
5. **S/P/E Scoring** (Sequence + Evidence components)

---

## PROPOSED FIX: Integrate HRD Rescue into 7D

### Option 1: Add HRD-Aware DDR Thresholds

```python
def predict_drug_with_7d(
    mechanism_vector_7d: List[float],
    hrd_score: Optional[float] = None,  # NEW: HRD score (0-100)
    germline_status: str = "negative",  # NEW: germline status
    min_ddr_threshold: float = 0.60,
    ...
) -> Tuple[str, Dict[str, float]]:
    ddr_score = mechanism_vector_7d[0]
    
    # Adjust DDR threshold based on HRD + germline
    adjusted_ddr_threshold = min_ddr_threshold
    
    if germline_status == "positive":
        adjusted_ddr_threshold = 0.40  # Lower for germline carriers
    elif hrd_score is not None:
        if hrd_score >= 42.0:
            adjusted_ddr_threshold = 0.45  # Lower for HRD-high
        else:
            adjusted_ddr_threshold = 0.70  # Higher for HRD-low (penalty)
    # else: use default threshold (0.60)
    
    # Gene-specific boosts (existing logic)
    if primary_gene in PARP_GENES:
        if ddr_score >= max(0.40, adjusted_ddr_threshold - 0.10):
            return "PARP", fit_scores
    
    # Fallback to threshold-based logic
    if ddr_score >= adjusted_ddr_threshold:
        return "PARP", fit_scores
    ...
```

**Impact:**
- HRD-high cases: DDR ≥ 0.45 → PARP (more permissive)
- HRD-low cases: DDR ≥ 0.70 → PARP (more restrictive)
- Should improve accuracy and reduce false positives

### Option 2: Apply Efficacy Penalty (Like WIWFM)

```python
# After computing pathway scores, apply HRD penalty
if predicted_drug == "PARP":
    if germline_status == "positive":
        efficacy_factor = 1.0
    elif hrd_score is not None:
        if hrd_score >= 42.0:
            efficacy_factor = 1.0  # Rescue
        else:
            efficacy_factor = 0.6  # Penalty
    else:
        efficacy_factor = 0.8  # Unknown
    
    # Adjust prediction confidence or re-rank drugs
    adjusted_confidence = confidence * efficacy_factor
    if adjusted_confidence < min_fit_threshold:
        return "NONE", fit_scores  # Penalty too strong, predict NONE
```

---

## GDSC2 DATA AVAILABILITY

### What We Have:
- ✅ **Mutations** (somatic, not germline)
- ✅ **DDR pathway scores** (from mutations)
- ✅ **Gene-level CNA matrix** (`OmicsCNGeneWGS.csv`)
- ❌ **HRD scores** (NOT in GDSC2 dataset)
- ❌ **Germline status** (NOT in GDSC2 dataset)

### What We Need:
- ⚠️ **Genome-wide HRD proxy** (LOH/LST/TAI, not just gene-level CNA)
- ⚠️ **Germline status** (all cell lines assumed germline-negative)

---

## RECOMMENDATIONS

### Immediate (1-2 days)

**Option A: Use HRD Proxy (if CNA data available)**
1. Compute HRD proxy from copy number alterations (LOH/LST/ntAI)
2. Integrate HRD rescue logic into 7D prediction
3. Test on GDSC2 with HRD proxy
4. **Expected:** Improved accuracy (65-70%), reduced PARP FPR (<10%)

**Option B: Simulate HRD Status (for testing)**
1. Use DDR pathway score as HRD proxy (DDR ≥ 0.60 → HRD-high)
2. Implement HRD rescue logic
3. Test on GDSC2 with simulated HRD
4. **Expected:** Proof-of-concept for HRD integration

### Medium-Term (1 week)

**Option C: Integrate Full WIWFM Sporadic Gates**
1. Import `apply_parp_gates` from `parp_gates.py`
2. Apply to 7D predictions as post-processing
3. Test on GDSC2 with HRD proxy
4. **Expected:** Match WIWFM performance

---

## KEY INSIGHT (UPDATED)

**The WIWFM framework operates in a richer, clinically realistic feature space.**

- ✅ Germline/HRD gating (penalty/rescue) — **Requires patient-level data**
- ✅ Gene-specific boosts (integrated)
- ✅ S/P/E scoring (multi-modal)
- ✅ Confidence capping (completeness-aware)

**7D is a mechanistic backbone, not a standalone PARP recommender.**

**Domain Mismatch:**
- WIWFM: Patients with gBRCA status, HRD scores, PTPI, clinical context
- 7D (GDSC2): Cell lines without germline, proper HRD, or clinical features

**Right Architecture:** 7D as backbone + HRD + clinical gates = full PARP module

**See:** `7D_STRATEGIC_REFRAMING.md` for full strategic reframing.

---

## NEXT STEPS

1. ✅ **Document WIWFM logic** (this audit)
2. 🔄 **Check if GDSC2 has CNA data** (for HRD proxy)
3. ⏳ **Implement HRD rescue in 7D** (adjust DDR thresholds)
4. ⏳ **Test with HRD proxy** (validate improvement)
5. ⏳ **Compare 7D+HRD vs baseline** (prove improvement)

---

**Status:** ✅ **CRITICAL GAP IDENTIFIED** — HRD rescue mechanism is the missing piece for accurate PARP prediction.

---

## ✅ NEW: HRD Proxy Ingestion Added

We added **optional HRD proxy ingestion** to the 7D validator so we can use **real CNA-derived HRD** when available.

### How to use
- Provide a file with HRD proxy scores keyed by **ModelID** or **COSMIC_ID**.
- Supported formats:
  - **JSON**: `{ "ACH-000001": 55.0, "905933": 62.0 }`
  - **CSV**: columns like `ModelID` + `HRD_SCORE` (or `HRD`, `hrd_proxy`)

### CLI example
```
python3 publications/synthetic_lethality/code/gdsc2_7d_validation.py \
  --max_cell_lines 500 \
  --use_7d \
  --evo2_api_base none \
  --mutation_scoring simple_counts \
  --min_ddr_threshold 0.60 \
  --min_fit_threshold 0.30 \
  --hrd_proxy_file /path/to/depmap_hrd_proxy.csv \
  --out gdsc2_7d_hrd_rescue_n500.json
```

### Why this matters
- **Mutation-only HRD proxy is too sparse** (only captures HRR-mutated cases)
- **CNA-based HRD** captures genome instability (LOH/LST/TAI) → should unlock the 65–70% target

---

## ✅ CNA Proxy Test Results (n=500)

**Input CNA:** `publications/synthetic_lethality/data/OmicsCNGeneWGS.csv`  
**Receipt:** `gdsc2_7d_hrd_cna_n500.json`

### Results
- **Accuracy:** 61.6% (baseline 62.2%)
- **Macro F1:** 0.181 (baseline 0.178)
- **PARP FPR:** 7.6% (baseline 7.4%)
- **ATR/WEE1/DNA_PK recall:** 0.0 (still collapsed)

### Interpretation
- Gene-level CNA proxy **does not materially improve** predictions.
- Likely needs **genome-wide HRD metrics** (LOH/LST/TAI) + **biallelic status**.

### Command used
```
python3 publications/synthetic_lethality/code/gdsc2_7d_validation.py \
  --max_cell_lines 500 \
  --use_6d \
  --evo2_api_base none \
  --mutation_scoring simple_counts \
  --min_ddr_threshold 0.60 \
  --min_fit_threshold 0.30 \
  --hrd_proxy_file publications/synthetic_lethality/data/OmicsCNGeneWGS.csv \
  --out gdsc2_7d_hrd_cna_n500.json
```

