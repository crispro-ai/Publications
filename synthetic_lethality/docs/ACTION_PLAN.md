# Action Plan: 7D Framework Strategic Reframing

**Date:** 2026-01-18  
**Status:** Ready for execution

---

## 🎯 Current State

### What We Have
- ✅ **7D mechanism vector** (62.2% accuracy on GDSC2, 7.4% PARP FPR)
- ✅ **HRD proxy infrastructure** (CNA matrix ingestion, mutation-based fallback)
- ✅ **GDSC2 validation framework** (n=500, stable, transparent)
- ✅ **Strategic reframing** (7D = backbone, not standalone recommender)

### What We're Missing
- ❌ Patient-level PARP module (gBRCA/HRD gates + PTPI + 7D + on-treatment)
- ❌ Clinical context integration (PTPI, prior platinum, CA-125)
- ❌ Full-stack validation (patient cohorts, ORR/PFS/OS)

---

## 📋 PHASE 1: Reframe GDSC2 Benchmark (Immediate - This Week)

### Task 1.1: Accept Current Performance ✅
- **Status:** Already done
- **Action:** Document 60-65% accuracy as acceptable for mechanistic signal
- **Why:** Cell lines lack clinical context (gBRCA, HRD, PTPI)

### Task 1.2: Update Documentation ✅
- **Status:** Already done
- **Action:** 
  - ✅ Created `7D_STRATEGIC_REFRAMING.md`
  - ✅ Updated audit documents
  - ✅ Updated SPD benchmark plan
- **Deliverable:** Documentation reflects reframing

### Task 1.3: Mark HRD Proxy as Experimental
- **Status:** TODO
- **Action:** Add `--experimental_hrd_gating` flag to validation script
- **Rationale:** HRD proxy is for testing direction, not final metric
- **Deliverable:** Flagged experimental feature in code

**Timeline:** 1 day

---

## 📋 PHASE 2: Design CrisPRO PARP Module Architecture (Short-Term - Next 2 Weeks)

### Task 2.1: Define Module Interface
- **Status:** TODO
- **Action:** Design PARP recommendation API contract
- **Inputs:**
  ```python
  {
    "germline_brca": "positive" | "negative" | "unknown",
    "hrd_score": float | None,  # 0-100 from assay
    "ptpi_weeks": float | None,  # Platinum-free interval
    "prior_platinum_response": bool | None,
    "mechanism_vector_7d": List[float],  # [DDR, MAPK, PI3K, ...]
    "tumor_context": Dict,  # Lineage, TMB, MSI, etc.
    "ca125_trend": Optional[str],  # "decreasing", "stable", "increasing"
  }
  ```
- **Outputs:**
  ```python
  {
    "recommendation": "PARP" | "NONE" | "CONSIDER_COMBO",
    "confidence": float,  # 0-1
    "rationale": str,
    "mechanism_rationale": Dict,  # 7D breakdown
    "clinical_factors": Dict,  # HRD/germline/PTPI impact
  }
  ```
- **Deliverable:** API specification document

### Task 2.2: Implement Meta-Model Logic
- **Status:** TODO
- **Action:** Build the joint function (gBRCA/HRD + PTPI + 7D)
- **Location:** New module or extend existing PARP service
- **Logic:**
  ```python
  def parp_recommendation_meta_model(
      germline_status: str,
      hrd_score: Optional[float],
      ptpi_weeks: Optional[float],
      ddr_mechanism: float,  # 7D DDR
      prior_platinum: bool,
      ...
  ) -> Dict[str, Any]:
      # 1. Baseline eligibility (gBRCA/HRD gates)
      # 2. Clinical favorability (PTPI boost/penalty)
      # 3. Mechanism check (7D DDR threshold)
      # 4. Combined recommendation
  ```
- **Deliverable:** Implementation in `oncology-backend-minimal/api/services/`

### Task 2.3: Integrate 7D as Backbone
- **Status:** TODO
- **Action:** Wire 7D mechanism vector into PARP module
- **Dependencies:** Existing `pathway_to_mechanism_vector.py`
- **Deliverable:** 7D vector passed to PARP meta-model

**Timeline:** 2 weeks

---

## 📋 PHASE 3: Build Patient-Level Capability Stack (Medium-Term - Next 4 Weeks)

### Task 3.1: Baseline PARP Eligibility (gBRCA/HRD Gates)
- **Status:** TODO
- **Action:** Port WIWFM PARP gates to PARP module
- **Source:** `oncology-coPilot/oncology-backend-minimal/api/services/efficacy_orchestrator/parp_gates.py`
- **Logic:**
  - gBRCA+ → No penalty (1.0x)
  - HRD-high (≥42) → Rescue (1.0x)
  - HRD-low (<42) → Penalty (0.6x)
  - HRD-unknown → Partial penalty (0.8x)
- **Deliverable:** Eligibility layer integrated

### Task 3.2: PTPI Clinical Favorability (Rafii Logic)
- **Status:** TODO
- **Action:** Implement PTPI-based boost/penalty
- **Source:** Rafii data showing PTPI >52 weeks doubles olaparib response
- **Logic:**
  - PTPI >52 weeks → Boost (1.2x)
  - PTPI <52 weeks → Penalty (0.8x, favor combos)
  - PTPI unknown → Neutral (1.0x)
- **Deliverable:** PTPI layer integrated

### Task 3.3: On-Treatment Behavior (CA-125, DDR Restoration)
- **Status:** TODO (Future)
- **Action:** Monitor on-treatment signals
- **Logic:** TBD (CA-125 kinetics, resistance emergence)
- **Deliverable:** On-treatment monitoring layer (Phase 4)

**Timeline:** 4 weeks

---

## 📋 PHASE 4: Validate Full Stack (Long-Term - Next 8 Weeks)

### Task 4.1: Collect Patient Cohorts
- **Status:** TODO
- **Action:** Identify validation cohorts
- **Candidates:**
  - Rafii gBRCA1/2 ovarian cohort (PTPI data)
  - TOPACIO (already validated for mechanism matching)
  - Other PARP trials with HRD/germline/PTPI data
- **Deliverable:** Cohort list + data access

### Task 4.2: Build Validation Framework
- **Status:** TODO
- **Action:** Create patient-level validation script
- **Metrics:**
  - PARP recommendation accuracy (full stack)
  - Mechanism vector contribution (ablation study)
  - Clinical interpretability (can we explain why?)
  - ORR/PFS/OS correlation (if available)
- **Deliverable:** Validation framework

### Task 4.3: Run Validation
- **Status:** TODO
- **Action:** Execute validation on patient cohorts
- **Hypothesis:** Full stack (gBRCA/HRD + PTPI + 7D) > HRD-only baseline
- **Deliverable:** Validation report + receipts

**Timeline:** 8 weeks

---

## 🚀 Immediate Next Steps (This Week)

### Day 1-2: Accept Reframing
- ✅ **DONE:** Documentation updated
- ✅ **DONE:** Strategic reframing document created
- **Remaining:** Mark HRD proxy as experimental flag

### Day 3-4: Design PARP Module Interface
- **Action:** Write API specification
- **Deliverable:** `PARP_MODULE_SPEC.md`
- **Owner:** Need to assign

### Day 5: Start Meta-Model Implementation
- **Action:** Begin coding the joint function
- **Deliverable:** Initial implementation draft

---

## 📊 Success Metrics

### Phase 1 (GDSC2 Reframing)
- ✅ Documentation reflects reframing
- ✅ HRD proxy marked experimental
- ✅ Team understands 7D = backbone

### Phase 2 (Module Design)
- ✅ API specification complete
- ✅ Meta-model logic implemented
- ✅ 7D integrated as backbone

### Phase 3 (Capability Stack)
- ✅ gBRCA/HRD gates integrated
- ✅ PTPI favorability integrated
- ✅ Full stack operational

### Phase 4 (Validation)
- ✅ Patient cohorts identified
- ✅ Validation framework built
- ✅ Results show full stack > HRD-only baseline

---

## 🎯 Key Principles

1. **7D is not broken** — It's a mechanistic backbone doing its job
2. **GDSC2 is impoverished** — Accept 60-65% as mechanistic signal validation
3. **Full stack matters** — gBRCA/HRD + PTPI + 7D + on-treatment = clinical PARP decision
4. **Stop optimizing 7D alone** — Build the stack, then validate

---

## 📝 Dependencies

### Technical Dependencies
- ✅ 7D mechanism vector computation (already exists)
- ✅ WIWFM PARP gates (already exists in `parp_gates.py`)
- ❌ PTPI data ingestion (need to identify source)
- ❌ Patient cohort data access (need to secure)

### External Dependencies
- **Manager approval** for PARP module architecture
- **Data access** for patient cohorts (Rafii, TOPACIO, etc.)
- **Clinical review** of meta-model logic

---

## 🔄 Iteration Plan

### Week 1: Reframe + Design
- Accept GDSC2 performance
- Design PARP module interface
- Start meta-model implementation

### Week 2-3: Build Core Stack
- Integrate gBRCA/HRD gates
- Integrate PTPI favorability
- Wire 7D as backbone

### Week 4-6: Test + Refine
- Unit tests for each layer
- Integration tests for full stack
- Clinical review of logic

### Week 7-8: Validate
- Patient cohort validation
- Ablation studies (7D contribution)
- Results analysis + reporting

---

**Status:** Ready to execute Phase 1 → Phase 2 → Phase 3 → Phase 4

**Next Action:** Design PARP module interface (Task 2.1)
