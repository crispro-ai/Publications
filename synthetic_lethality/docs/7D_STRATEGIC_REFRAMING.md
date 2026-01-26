# 7D Framework: Strategic Reframing (Manager Directive)

**Date:** 2026-01-18  
**Status:** ✅ **DOMAIN MISMATCH CORRECTED** — 7D is mechanistic backbone, not standalone PARP recommender

---

## 🎯 CORE INSIGHT: Domain Mismatch

### WIWFM vs 7D Evaluation Context

| Dimension | WIWFM (Sporadic Gates) | 7D (GDSC2 Validation) |
|-----------|------------------------|----------------------|
| **Domain** | **Patients** (clinical) | **Cell lines** (preclinical) |
| **Germline Status** | ✅ Available (gBRCA+/-) | ❌ Not available (assumed negative) |
| **HRD Score** | ✅ Calibrated assay (0-100) | ⚠️ Approximated from sparse CNA |
| **PTPI** | ✅ Available (platinum-free interval) | ❌ Not available |
| **Clinical Context** | ✅ Full (prior platinum, CA-125, etc.) | ❌ Minimal (mutations only) |
| **Feature Space** | ✅ **Rich, clinically realistic** | ❌ **Deliberately impoverished** |

**Bottom Line:** WIWFM operates in a richer, clinically realistic feature space; 7D is being judged in a deliberately impoverished one.

---

## ❌ What Was Wrong: Asking 7D to Do Too Much

### The Mistake
We treated **"7D alone on GDSC2"** as the benchmark that must reach 70%+ accuracy as a **standalone PARP recommender**.

### The Reality
7D is a **mechanistic backbone** that describes **how the tumor escapes** (pathway disruption), but PARP decisions require:
- **HRD/germline context** (WIWFM gates)
- **Clinical behavior** (PTPI, prior platinum)
- **Confidence/completeness** (what's missing matters)

**Net Effect:** 7D is a nice mechanism vector, but you're asking it to be a standalone PARP recommender without the clinical and HRD context that actually drives PARP decisions.

---

## ✅ What 7D Actually Is (And Should Be)

### 7D's Role: Mechanistic Backbone

**7D Framework = Pathway Disruption Descriptor**

- ✅ Describes **how the tumor escapes** (DDR/MAPK/PI3K/VEGF/HER2/IO/Efflux)
- ✅ Provides **mechanistic rationale** for drug targeting
- ✅ Works **without clinical context** (pure mechanism)
- ❌ **Cannot decide PARP eligibility alone** (needs HRD + clinical gates)

### Analogy
- **7D = "The tumor has DDR disruption (0.85)"**
- **WIWFM + Clinical = "Should we use PARP? Yes, because gBRCA + HRD-high + PTPI >52 weeks"**

**7D tells you WHAT's broken; clinical context tells you IF it matters.**

---

## 🔍 What's Actually Missing in 7D (Conceptually)

### Gap 1: No Explicit HRD/Germline Rescue/Penalty Layer

**Current 7D:**
- Binary DDR threshold (≥0.60) → PARP
- No differentiation for gBRCA vs somatic-only
- No HRD-high "forgiveness" for borderline DDR

**Needed:**
- gBRCA or HRD-high → **Rescue** (lower DDR threshold, e.g., ≥0.40)
- HRD-low/germline-negative → **Penalty** (raise bar, e.g., ≥0.70)

**Clinical Example:**
- Rafii gBRCA1/2 ovarian cohort → Should get PARP even if DDR = 0.45 (below default threshold)
- HRD-low, germline-negative → Should NOT get PARP even if DDR = 0.55 (above default threshold)

### Gap 2: No Clinical Behavior Features (PTPI)

**Current 7D:**
- Blind to platinum-free interval (PTPI)
- Blind to prior platinum response
- Blind to CA-125 kinetics

**Clinical Evidence:**
- Rafii shows **PTPI >52 weeks nearly doubles olaparib response** vs <52 weeks for gBRCA-mut ovarian cancer
- WIWFM (and real clinicians) implicitly encode platinum-like history and HRD context
- 7D is blind to both baseline HRD and time-based behavior

**Needed:**
- PTPI >52 weeks → Boost PARP confidence
- PTPI <52 weeks → Penalize PARP (favor combos/trials)

### Gap 3: No Confidence / Completeness Caps

**Current 7D:**
- Acts as if a half-observed tumor is fully observed
- No penalty for missing germline status
- No penalty for missing HRD score

**WIWFM Approach:**
- Caps confidence when key axes (germline, HRD) are missing
- Applies 0.8x penalty for HRD-unknown (vs 1.0x for HRD-high, 0.6x for HRD-low)

**Needed:**
- Missing germline → Lower confidence cap (e.g., 0.7 max)
- Missing HRD → Apply unknown penalty (0.8x)

---

## 🧪 Why the HRD Proxy Experiment "Failed" (Expected)

### The Experiment
- Used gene-level CNA matrix (`OmicsCNGeneWGS.csv`)
- Computed HRD proxy from HRR gene copy losses
- Applied WIWFM-style HRD rescue logic
- **Result:** No improvement (61.6% vs 62.2% baseline)

### Why It Was Expected to Fail

**Gene-level CNA ≠ Genomic Scar HRD:**
- CNA matrix: Gene copy estimates (median ~1.0)
- True HRD: LOH/LST/TAI (genome-wide instability)
- Missing: Biallelic loss logic (CN + mutation zygosity)

**This doesn't mean HRD rescue is a bad idea; it means this particular HRD proxy is too weak to reveal the power of the gating logic.**

### The Right Conclusion

**❌ Wrong:** "HRD-aware gating doesn't work"  
**✅ Right:** "This HRD proxy is insufficient; need better HRD or switch to patient-level data"

---

## 🛠️ Course Correction (Without Throwing Away 7D)

### Short-Term: Within GDSC2 (Experimental)

**Treat HRD proxy as experimental:**
- Use only to test **direction of gating** (does it shift predictions?)
- Not as a final metric for deployment

**Implement Option 2 (post-hoc efficacy factor):**
- Apply as **confidence/ranking modifier**, not hard rejection
- Down-weight low-HRD PARP calls rather than zeroing them
- Keep experimental flag: `--experimental_hrd_gating`

### Medium-Term: Where CrisPRO Actually Lives (Patients)

**Make 7D one feature among many in CrisPRO's PARP module:**

```
CrisPRO PARP Recommendation Stack:
├─ 1. Baseline PARP Eligibility
│  ├─ gBRCA status (germline testing)
│  └─ HRD score (assay: Myriad, FoundationOne, etc.)
│
├─ 2. Clinical Favorability (Rafii PTPI)
│  ├─ PTPI >52 weeks → Boost
│  ├─ PTPI <52 weeks → Penalty (favor combos)
│  └─ Prior platinum response → Signal
│
├─ 3. Mechanism Vector (7D/SAE) ← YOUR BACKBONE
│  ├─ DDR pathway disruption (0-1)
│  ├─ Pathway-specific rationale
│  └─ Multi-dimensional escape description
│
└─ 4. On-Treatment Behavior
   ├─ CA-125 kinetics
   ├─ DDR restoration signals
   └─ Resistance emergence
```

**Meta-Model / Rules:**
```python
def parp_recommendation_meta_model(
    germline_status: str,      # "positive", "negative", "unknown"
    hrd_score: Optional[float], # 0-100
    ptpi_weeks: Optional[float], # Platinum-free interval
    ddr_mechanism: float,       # 7D DDR score (0-1)
    prior_platinum: bool,       # Prior platinum response
    ...
) -> Dict[str, Any]:
    """
    PARP is a joint function of:
    - HRD/germline + recent platinum behavior + mechanism state
    NOT just "DDR ≥ 0.6"
    """
    
    # Base eligibility
    if germline_status == "positive":
        parp_eligible = True
        ddr_threshold = 0.40  # Lower for gBRCA
    elif hrd_score is not None:
        if hrd_score >= 42.0:
            parp_eligible = True
            ddr_threshold = 0.45  # Lower for HRD-high
        else:
            parp_eligible = False  # HRD-low → not eligible
            ddr_threshold = 0.70  # Higher bar if we proceed
    else:
        parp_eligible = True  # Unknown HRD → proceed with caution
        ddr_threshold = 0.60  # Default
        confidence_cap = 0.8  # Lower confidence
    
    # Clinical boost (PTPI)
    if ptpi_weeks and ptpi_weeks > 52:
        clinical_factor = 1.2  # Boost for long PTPI
    elif ptpi_weeks and ptpi_weeks < 52:
        clinical_factor = 0.8  # Penalty for short PTPI
    else:
        clinical_factor = 1.0  # Unknown
    
    # Mechanism check (7D DDR)
    if ddr_mechanism >= ddr_threshold:
        mechanism_eligible = True
    else:
        mechanism_eligible = False
    
    # Final decision
    if parp_eligible and mechanism_eligible:
        confidence = (ddr_mechanism * clinical_factor)
        if 'confidence_cap' in locals():
            confidence = min(confidence, confidence_cap)
        return {
            "recommend": "PARP",
            "confidence": confidence,
            "rationale": f"gBRCA={germline_status}, HRD={hrd_score}, PTPI={ptpi_weeks}w, DDR={ddr_mechanism:.2f}"
        }
    else:
        return {
            "recommend": "NONE" if not parp_eligible else "CONSIDER_COMBO",
            "confidence": 0.0,
            "rationale": f"Eligibility fail: gBRCA={germline_status}, HRD={hrd_score}, DDR={ddr_mechanism:.2f} < {ddr_threshold}"
        }
```

**This is exactly what Rafii's PTPI data + WIWFM's HRD/germline gates are telling you:** PARP is a joint function of HRD/germline + recent platinum behavior + mechanism state, **not just "DDR ≥ 0.6."**

---

## ✅ Practical Next Move

### Stop This

**❌ Stop:** Treating "7D alone on GDSC2" as the benchmark that must reach 70%+

### Accept This

**✅ Accept:** 7D as a mechanistic backbone that needs HRD + clinical gates to be clinically meaningful

### Build This

**✅ Build:** Small capability stack for CrisPRO / ovarian PARP module:

1. **Baseline PARP Eligibility** (BRCA/HRD)
2. **PTPI-based Clinical Favorability** (from Rafii)
3. **Mechanism Vector** (7D/SAE) ← Your backbone
4. **On-Treatment Behavior** (CA-125, DDR restoration)

**Then 7D is doing exactly what it should:**
- ✅ Describing **how the tumor escapes** (mechanistic rationale)
- ✅ Providing **pathway-level signal** (DDR = 0.85 means high vulnerability)
- ✅ Enabling **multi-dimensional matching** (trial mechanism alignment)

**While WIWFM-style gates + Rafii-style PTPI + HRD define whether PARP should still be on the table.**

---

## 📊 Updated Evaluation Framework

### GDSC2 Benchmark (Preclinical Proxy)

**Purpose:** Validate 7D mechanism vector computation, not PARP recommendation

**What We're Actually Testing:**
- ✅ Can we compute accurate DDR pathway scores from mutations?
- ✅ Do DDR scores correlate with PARP sensitivity in cell lines?
- ✅ Is the mechanism vector stable and interpretable?

**What We're NOT Testing:**
- ❌ Can 7D alone predict PARP eligibility? (No, needs HRD + clinical)
- ❌ Will 7D reach 70%+ accuracy? (No, cell lines lack clinical context)
- ❌ Should we deploy 7D as standalone PARP recommender? (No, it's a backbone)

**Acceptable Performance:**
- Accuracy: 60-65% (mechanistic signal, not clinical decision)
- PARP FPR: <10% (safety-first, but not final clinical gate)
- Correlation: DDR vs PARP Z-score (r > 0.3 acceptable for mechanism signal)

### Patient-Level Validation (Where It Matters)

**Purpose:** Validate 7D as backbone within full PARP recommendation stack

**Test Stack:**
```
Full PARP Module:
├─ gBRCA/HRD gates (WIWFM)
├─ PTPI clinical favorability (Rafii)
├─ 7D mechanism vector (mechanistic backbone)
└─ On-treatment behavior (CA-125, DDR restoration)
```

**Metrics:**
- PARP recommendation accuracy (full stack)
- Mechanism vector contribution (does it improve vs HRD-only?)
- Clinical interpretability (can we explain why?)

---

## 📝 Implementation Roadmap

### Phase 1: Reframe GDSC2 Benchmark (Immediate)

**Tasks:**
1. ✅ Update documentation to reflect domain mismatch
2. ✅ Accept 60-65% accuracy as acceptable for mechanistic signal
3. ✅ Document 7D as backbone, not standalone recommender
4. ✅ Keep HRD proxy experimental (test direction, not final metric)

### Phase 2: Build CrisPRO PARP Module (Medium-Term)

**Tasks:**
1. Design capability stack (gBRCA/HRD + PTPI + 7D + on-treatment)
2. Integrate 7D as one feature among many
3. Implement meta-model (joint function of all layers)
4. Test on patient cohorts (Rafii, TOPACIO, etc.)

### Phase 3: Validate Full Stack (Long-Term)

**Tasks:**
1. Patient-level validation (ORR, PFS, OS)
2. Mechanism vector contribution analysis
3. Clinical interpretability testing
4. Publication-ready results

---

## 🎯 Key Takeaways

1. **7D is not broken** — It's a mechanistic backbone doing its job
2. **GDSC2 is impoverished** — Cell lines lack clinical context (gBRCA, HRD, PTPI)
3. **HRD proxy "failure" was expected** — Gene-level CNA ≠ genomic scar HRD
4. **Right architecture:** 7D as backbone + HRD + clinical gates = full PARP module
5. **Stop optimizing 7D alone** — Build the stack, then validate

---

**Status:** ✅ **STRATEGIC REFRAMING COMPLETE** — 7D is mechanistic backbone, not standalone PARP recommender
