# PGx Safety Integration → Advanced Care Plan: 10-Sprint Production Plan

**Created:** January 2026  
**Status:** Product-Focused Production Plan  
**Core Vision:** Integrate PGx safety into Advanced Care Plan to prevent trial failures and toxicity

---

## Executive Summary

**The Problem We're Solving:**
> "A patient matches a perfect trial (0.98 mechanism fit) but can't tolerate the drug due to PGx variants → trial failure, wasted resources, patient harm"

**What Actually Exists:**
- ✅ **Advanced Care Plan** (`/api/complete_care/v2`) - Complete orchestration: drug efficacy, trials, food, resistance
- ✅ **PGx Dosing Guidance** (`/api/dosing/guidance`) - 100% CPIC concordance, 100% sensitivity
- ✅ **Risk-Benefit Logic** - Validated (15/15 cases) but NOT in production
- ✅ **Frontend Care Plan** - `UniversalCompleteCare.jsx` displays full care plan
- ✅ **Trial Matching Validation** - 47 trials, TCGA-OV cohort (585 patients), mechanism fit validated
- ✅ **PGx Validation** - N=59 cases, outcome-linked data (PREPARE: 83.1% RRR, CYP2C19: 4.28× risk ratio)

**What's Missing:**
- ❌ PGx screening **NOT integrated** into care plan flow
- ❌ No safety gate that prevents "perfect trial match but can't tolerate drug"
- ❌ No unified feasibility score combining mechanism fit + efficacy + PGx safety
- ❌ **No integrated validation** combining trial matching + PGx safety

**The Plan:** Integrate PGx into existing Advanced Care Plan to deliver the Safety Gate capability, validated on combined trial matching + PGx cohorts.

---

## Validation Strategy (BEFORE Building)

**Critical:** We must define validation strategy BEFORE building. This ensures we can prove the product works.

### What We Need to Validate

**Core Hypothesis:** "Integrated Safety Gate prevents trial failures by screening for PGx variants before enrollment"

**Validation Questions:**
1. **Can we extract PGx variants from patient data?** (Sprint 1 validation)
2. **Does PGx screening correctly identify toxicity risks?** (Sprint 2 validation - reuse existing N=59 cohort)
3. **Does risk-benefit composition correctly combine efficacy + PGx?** (Sprint 3 validation - reuse existing 15/15 cases)
4. **Does Safety Gate prevent 'perfect trial match but can't tolerate' scenarios?** (Sprint 4-5 validation - NEW integrated cohort)
5. **Does integrated feasibility score predict trial success?** (Sprint 8 validation - outcome-linked cohort)

### Existing Validation Assets (What We Can Reuse)

#### 1. Trial Matching Validation (From `02-trial-matching/`)
**What Exists:**
- ✅ **47 trials** with MoA vectors validated
- ✅ **1 patient profile** (MBD4+TP53) with mechanism fit scores
- ✅ **TCGA-OV cohort** (585 patients) with mechanism fit validation
- ✅ **SME adjudication protocol** for ranking quality
- ✅ **Validation scripts** (`validate_real_world_tcga_ov_matchability.py`)

**Data Structure:**
```json
{
  "patient_id": "TCGA-XX-XXXX",
  "somatic_mutations": [...],
  "mechanism_vector": [0.88, 0.12, 0.15, ...],
  "trial_matches": [
    {
      "nct_id": "NCT...",
      "mechanism_fit": 0.98,
      "eligibility_score": 0.85
    }
  ]
}
```

**What We Can Build Upon:**
- Use same 47 trials for integrated validation
- Use TCGA-OV cohort (585 patients) - add PGx variants
- Use SME adjudication protocol for integrated feasibility ranking

#### 2. PGx Dosing Guidance Validation (From `05-pgx-dosing-guidance/`)
**What Exists:**
- ✅ **N=59 cases** validated (6 clinically evaluable with drug + toxicity)
- ✅ **Outcome-linked data:**
  - PREPARE trial: 83.1% RRR (n=40 actionable carriers)
  - CYP2C19 clopidogrel: 4.28× risk ratio (n=210)
- ✅ **Validation receipts:** `prepare_outcome_validation.json`, `cyp2c19_clopidogrel_efficacy_validation.json`
- ✅ **Tier 2 validation:** 100% sensitivity (6/6), 10% specificity (1/10)

**Data Structure:**
```json
{
  "case_id": "LIT-DPYD-001",
  "gene": "DPYD",
  "variant": "c.2846A>T",
  "drug": "5-FU",
  "toxicity_outcome": true,
  "system_recommendation": "REDUCE_50",
  "cpic_concordance": true
}
```

**What We Can Build Upon:**
- Reuse N=59 cases for PGx extraction validation (Sprint 1)
- Reuse outcome-linked data for feasibility score validation (Sprint 3)
- Expand cohort using same extraction methodology

### Ground Truth Requirements (What We Need)

#### For Sprint 1: PGx Extraction Validation
**Ground Truth Needed:**
- Patient VCF files with known PGx variants (DPYD, TPMT, UGT1A1, CYP2D6, CYP2C19)
- Expected output: List of pharmacogene variants extracted

**Available Data:**
- ✅ **TCGA germline data** (from existing PGx validation: 48 cases from GDC/TCGA)
- ✅ **cBioPortal studies** (MSK-IMPACT, colorectal studies)
- ⚠️ **Need:** More diverse VCF files with PGx variants (target: 20-30 VCF files)

**Validation Approach:**
1. Extract PGx variants from known VCF files
2. Compare extracted variants to ground truth (manual annotation)
3. Metrics: Precision, Recall, F1-score for pharmacogene detection

#### For Sprint 2: PGx Integration Validation
**Ground Truth Needed:**
- Patient profiles with germline variants + recommended drugs
- Expected output: PGx safety flags for each drug

**Available Data:**
- ✅ **N=59 PGx cases** (reuse existing validation cohort)
- ✅ **6 clinically evaluable cases** (drug + toxicity outcome)
- ⚠️ **Need:** More cases with drug recommendations (target: 20-30 cases)

**Validation Approach:**
1. Run care plan for patients with known PGx variants
2. Verify PGx screening flags correct drugs
3. Metrics: Sensitivity (toxicity detection), Specificity (false positive rate)

#### For Sprint 3: Risk-Benefit Composition Validation
**Ground Truth Needed:**
- Drug efficacy scores + PGx dosing guidance → Expected feasibility scores

**Available Data (REAL DATA ONLY):**
- ✅ **15 synthetic cases** (validated 100% pass rate) - for logic validation only
- ✅ **Outcome-linked real cases:**
  - PREPARE trial (n=563): Real variants + real outcomes
  - CYP2C19 clopidogrel (n=210): Real variants + real outcomes
- ⚠️ **Need:** More real patient cases with efficacy + PGx data (target: 10-15 additional)
  - **Source:** Find additional outcome-linked cohorts from PubMed
  - **Method:** Use `scripts/data_acquisition/pgx_outcomes/find_pgx_outcome_cohorts.py`

**Validation Approach:**
1. Use existing 15 synthetic cases (reuse validation)
2. Add real patient cases with efficacy + PGx data
3. Metrics: Feasibility score accuracy, action label correctness

#### For Sprint 4-5: Integrated Safety Gate Validation (NEW)
**Ground Truth Needed:**
- Patient profiles with:
  - Somatic mutations (for mechanism fit)
  - Germline variants (for PGx screening)
  - Trial matches (for safety gate)
  - Expected outcome: Trial success/failure OR toxicity occurrence

**Available Data (REAL DATA ONLY):**
- ✅ **Trial matching cohort:** TCGA-OV (585 patients) - has somatic mutations, mechanism fit
  - Source: `publications/02-trial-matching/scripts/validate_real_world_tcga_ov_matchability.py`
- ✅ **PGx cohort:** N=59 cases - has germline variants, PGx guidance
  - Source: Unified extraction pipeline (PubMed + cBioPortal + GDC)
- ✅ **Outcome-linked PGx data:**
  - PREPARE trial (n=563): Real variants + real outcomes
  - CYP2C19 clopidogrel (n=210): Real variants + real outcomes
- ⚠️ **Missing:** Combined cohort with BOTH somatic + germline + trial matches + outcomes
  - **Approach:** Match TCGA-OV patients with cBioPortal PGx variants (same study)
  - **Method:** Use `extract_pgx_validation_cohort.py` on TCGA PanCancer Atlas

**Validation Approach (NEW - Must Build):**
1. **Combine cohorts:** TCGA-OV patients + PGx variants (if available)
2. **Real data integration:** Match TCGA-OV patients with cBioPortal PGx variants (same study)
3. **Outcome-linked validation:** Use PREPARE/CYP2C19 outcome data to validate feasibility scores
4. **Metrics:**
   - Safety Gate accuracy: % of "perfect trial match but can't tolerate" scenarios caught
   - Feasibility score correlation: Does feasibility score predict trial success?
   - Trial failure prevention: How many failures would have been prevented?

#### For Sprint 6: Validation Expansion
**Ground Truth Needed:**
- More PGx cases with outcomes (target: N≥200)

**Available Data Sources:**
- ✅ **cBioPortal MCP tools** (12 tools available)
- ✅ **Existing extraction scripts** (`scripts/data_acquisition/pgx/`)
- ⚠️ **Need:** Identify studies with PGx variants + outcomes

**Validation Approach:**
1. Use cBioPortal MCP to find studies with PGx genes (DPYD, TPMT, UGT1A1)
2. Extract variants and outcomes
3. Run through PGx screening
4. Generate validation receipts (same format as existing)

### Integrated Validation Cohort (Combining Trial Matching + PGx)

**Goal:** Create a cohort that validates the integrated Safety Gate capability

**Approach 1: Combine Existing Cohorts**
```
TCGA-OV patients (585) + PGx variants (if available)
  ↓
For each patient:
  ├─ Somatic mutations → Mechanism fit (from trial matching)
  ├─ Germline variants → PGx screening (from PGx validation)
  └─ Combined → Feasibility score
```

**Approach 2: Outcome-Linked Validation (Best - Real Data)**
```
PREPARE trial patients (n=563) + Trial matching
  ↓
For each patient:
  ├─ Somatic mutations → Mechanism fit (if available)
  ├─ DPYD/UGT1A1 variants → PGx screening (known)
  ├─ Trial enrollment → Mechanism fit (if trial data available)
  └─ Toxicity outcome → Ground truth
  ↓
Validate: Does Safety Gate predict toxicity? (83.1% RRR)
```

### Validation Metrics (How We Prove It Works)

| Validation Stage | Metric | Ground Truth | Target |
|-----------------|--------|--------------|--------|
| **Sprint 1: PGx Extraction** | Precision/Recall | Manual VCF annotation | ≥95% precision, ≥90% recall |
| **Sprint 2: PGx Integration** | Sensitivity/Specificity | N=59 PGx cohort | Maintain 100% sensitivity, ≥90% specificity |
| **Sprint 3: Risk-Benefit** | Feasibility Accuracy | 15 synthetic + 10 real cases | 100% pass (synthetic), ≥90% accuracy (real) |
| **Sprint 4-5: Safety Gate** | Safety Gate Accuracy | Integrated cohort | ≥90% catch rate for "perfect match but can't tolerate" |
| **Sprint 6: Expansion** | Cohort Size | cBioPortal extraction | N≥200 cases |
| **Sprint 8: End-to-End** | Trial Failure Prevention | Outcome-linked cohort | ≥80% of preventable failures caught |

### Data Acquisition Plan (What We Need to Extract)

#### From Existing Sources:
1. **TCGA-OV cohort** (585 patients)
   - ✅ Somatic mutations (already have)
   - ⚠️ Germline variants (need to extract from cBioPortal or GDC)
   - ✅ Mechanism fit scores (already validated)

2. **PGx validation cohort** (N=59)
   - ✅ Germline variants (already have)
   - ✅ PGx guidance (already validated)
   - ❌ Somatic mutations (need to add for integration)

3. **PREPARE trial** (n=563)
   - ✅ DPYD/UGT1A1 variants (already extracted)
   - ✅ Toxicity outcomes (already validated)
   - ❌ Somatic mutations (need to extract if available)
   - ❌ Trial matches (need to add)

#### From New Sources (cBioPortal):
1. **Studies with PGx variants + outcomes**
   - Search: Studies with DPYD/TPMT/UGT1A1 variants
   - Extract: Variants, outcomes, treatment history
   - Target: N≥141 additional cases (to reach N≥200)

2. **Studies with both somatic + germline data**
   - Search: Studies with both tumor and germline sequencing
   - Extract: Somatic mutations, germline variants, outcomes
   - Target: 20-30 integrated cases

### Validation Scripts (What We Need to Build)

1. **`validate_pgx_extraction.py`** (Sprint 1)
   - Input: VCF files with known PGx variants
   - Output: Precision/Recall metrics
   - Ground truth: Manual annotation

2. **`validate_integrated_safety_gate.py`** (Sprint 4-5)
   - Input: Patient profiles with somatic + germline + trial matches
   - Output: Safety Gate accuracy, feasibility score correlation
   - Ground truth: Outcome-linked data (PREPARE, CYP2C19)

3. **`validate_trial_failure_prevention.py`** (Sprint 8)
   - Input: Historical trial enrollments with PGx variants
   - Output: % of failures that would have been prevented
   - Ground truth: Actual trial failures + toxicity events

### Building the Integrated Validation Cohort

**Goal:** Create a cohort that validates the integrated Safety Gate capability by combining trial matching + PGx data.

**Strategy 1: Combine Existing Cohorts (Realistic)**
```
Step 1: Start with TCGA-OV cohort (585 patients)
  ├─ Somatic mutations → Mechanism fit (already validated)
  └─ Missing: Germline variants

Step 2: Add PGx variants (if available in TCGA)
  ├─ Check: Does TCGA have germline data?
  └─ If yes: Extract DPYD/TPMT/UGT1A1 variants
  └─ If no: Use outcome-linked validation only (Strategy 2)

Step 3: Run integrated care plan
  ├─ Mechanism fit (from trial matching)
  ├─ PGx screening (from PGx extraction)
  └─ Feasibility score (from risk-benefit composition)

Step 4: Validate
  ├─ Compare feasibility scores to mechanism fit alone
  └─ Identify cases where PGx changes recommendation
```

**Strategy 2: Outcome-Linked Validation (Best - Real Data)**
```
Step 1: Start with PREPARE trial (n=563) - REAL DATA
  ├─ Real DPYD/UGT1A1 variants (extracted from PMC tables)
  ├─ Real toxicity outcomes (83.1% RRR validated)
  └─ Source: PMID 39641926 (PMC 11624585) - already extracted

Step 2: Extract from existing sources
  ├─ PREPARE data: Already extracted via `scripts/data_acquisition/pgx_outcomes/extract_pmc_tables.py`
  ├─ Receipts exist: `reports/prepare_outcome_validation.json`
  └─ Method: Entrez.elink() + Entrez.efetch() for PMC XML extraction

Step 3: Combine with trial matching (if available)
  ├─ Check: Does TCGA-OV have overlapping patients with PREPARE?
  └─ If yes: Match by patient ID → Add mechanism fit scores
  └─ If no: Use PREPARE outcome data alone (still validates PGx safety)

Step 4: Run integrated care plan
  ├─ PGx screening (from known PREPARE variants)
  ├─ Mechanism fit (if available from TCGA-OV overlap)
  └─ Feasibility score (from risk-benefit composition)

Step 5: Validate against outcomes
  ├─ Compare: Feasibility scores vs actual toxicity outcomes
  └─ Verify: Does Safety Gate predict toxicity? (83.1% RRR)
```

**Data Acquisition Scripts (REAL DATA ONLY):**

1. **`scripts/cohorts/extract_pgx_validation_cohort.py`** (EXISTS)
   - Extracts PGx variants from cBioPortal (TCGA PanCancer Atlas)
   - Uses direct cBioPortal API calls
   - Output: Germline variants + clinical data

2. **`scripts/data_acquisition/pgx_outcomes/extract_pmc_tables.py`** (EXISTS)
   - Extracts outcome-linked data from PubMed Central
   - Uses Entrez.elink() + Entrez.efetch() for PMC XML
   - Already extracted: PREPARE (PMID 39641926), CYP2C19 (PMID 40944685)

3. **`scripts/data_acquisition/pgx_outcomes/find_pgx_outcome_cohorts.py`** (EXISTS)
   - Finds additional PGx outcome cohorts from PubMed
   - Searches for studies with PGx variants + outcomes

4. **NEW: `scripts/data_acquisition/build_integrated_validation_cohort.py`**
```python
"""
Build integrated validation cohort combining trial matching + PGx data.
REAL DATA ONLY - NO SYNTHETIC DATA.

Approach:
1. Start with TCGA-OV cohort (585 patients) - has somatic mutations
2. Add PGx variants from cBioPortal:
   - Use extract_pgx_validation_cohort.py to get germline variants
   - Match patients by study ID
3. Add outcome-linked data from PMC:
   - Use existing PREPARE data (already extracted)
   - Use existing CYP2C19 data (already extracted)
4. Run integrated care plan for each patient
5. Generate validation receipts
"""
```

**Validation Script:** `scripts/validation/validate_integrated_cohort.py`
```python
"""
Validate integrated Safety Gate on combined cohort.

Metrics:
1. Safety Gate accuracy: % of "perfect match but can't tolerate" caught
2. Feasibility score correlation: Does feasibility predict outcomes?
3. Trial failure prevention: How many failures would have been prevented?
"""
```

### Validation Receipts (Machine-Readable Proof)

**Format:** JSON receipts (same as existing validation)
```json
{
  "validation_type": "integrated_safety_gate",
  "cohort_size": 200,
  "metrics": {
    "safety_gate_accuracy": 0.92,
    "feasibility_score_correlation": 0.85,
    "trial_failure_prevention": 0.83
  },
  "ground_truth_source": "PREPARE_trial_outcomes",
  "receipt_id": "...",
  "timestamp": "..."
}
```

---

## Product Capabilities (Not Features)

### Capability 1: Safety Gate Prevents Trial Failures
**What It Does:** Before recommending a trial, checks if patient can tolerate the drug. Prevents enrollment of patients who will experience severe toxicity.

**Why It Matters:** 
- Prevents trial failures (patient enrolled → can't tolerate → trial failure)
- Saves resources (no wasted enrollment)
- Prevents patient harm (no severe toxicity)

**Real Use Case:**
```
Patient: Ovarian cancer, HRD-high, perfect PARP trial match (0.98 mechanism fit)
BUT: DPYD c.2846A>T variant → Can't tolerate capecitabine (if part of trial protocol)

WITHOUT Safety Gate:
→ Patient enrolled → Severe toxicity → Trial failure → Wasted resources

WITH Safety Gate:
→ "⚠️ SAFETY GATE: DPYD variant detected. Capecitabine requires 50% dose reduction."
→ "✅ ACTION: Apply dose adjustment, patient can proceed"
→ Trial success, patient safe
```

### Capability 2: Integrated Feasibility Score
**What It Does:** Combines mechanism fit (trial matching) + drug efficacy (S/P/E) + PGx safety into a single score that predicts trial success.

**Why It Matters:**
- Single metric that predicts: "Will this patient succeed in this trial?"
- Prevents "high mechanism fit but can't tolerate" scenarios
- Enables ranking: "Trial A: 0.85 feasibility (high fit, safe) vs Trial B: 0.45 feasibility (high fit, but PGx risk)"

**Real Use Case:**
```
Trial A: PARP inhibitor
- Mechanism fit: 0.98 (excellent)
- Drug efficacy: 0.85 (high)
- PGx safety: 0.50 (MODERATE - requires dose adjustment)
- Feasibility: 0.68 (CONSIDER WITH MONITORING)

Trial B: PARP + ATR inhibitor
- Mechanism fit: 0.95 (excellent)
- Drug efficacy: 0.80 (high)
- PGx safety: 1.0 (LOW - no PGx issues)
- Feasibility: 0.80 (PREFERRED)

Result: Trial B ranked higher despite lower mechanism fit (safety matters)
```

### Capability 3: Proactive Toxicity Prevention
**What It Does:** Screens for PGx variants BEFORE prescribing, recommends dose adjustments, flags contraindications.

**Why It Matters:**
- Prevents severe toxicity (83.1% RRR in PREPARE trial)
- Reduces MedWatch reports (events that don't happen don't generate reports)
- Saves investigation time (proactive vs reactive)

**Real Use Case:**
```
Patient: Ovarian cancer, starting carboplatin + paclitaxel

WITHOUT PGx Screening:
→ Prescribe standard dose
→ Patient has DPYD variant (unknown)
→ Severe neutropenia → Hospitalization → MedWatch report → Investigation

WITH PGx Screening:
→ Screen before prescribing
→ DPYD variant detected → 50% dose reduction recommended
→ Patient tolerates treatment → No toxicity → No MedWatch report
```

---

## Data Workflow (Real Data, Not Synthetic)

### Current Care Plan Flow (Without PGx)
```
1. Patient Input
   ├─ Somatic mutations (VCF/NGS report)
   ├─ Disease type (ovarian, myeloma, etc.)
   ├─ Treatment history
   └─ Biomarkers (CA-125, PSA, etc.)

2. Processing
   ├─ Drug Efficacy (WIWFM) → S/P/E scores
   ├─ Trial Matching → Mechanism fit scores
   ├─ Food Validation → Mitigating foods
   └─ Resistance Playbook → Backup plans

3. Output
   └─ Complete Care Plan (drugs, trials, food, resistance)
```

### Enhanced Care Plan Flow (With PGx Integration)
```
1. Patient Input
   ├─ Somatic mutations (VCF/NGS report)
   ├─ Germline variants (VCF/NGS report) ← NEW
   ├─ Disease type
   ├─ Treatment history
   └─ Biomarkers

2. Processing
   ├─ Drug Efficacy (WIWFM) → S/P/E scores
   ├─ Trial Matching → Mechanism fit scores
   ├─ PGx Screening ← NEW
   │   ├─ Extract pharmacogene variants (DPYD, TPMT, UGT1A1)
   │   ├─ Check against recommended drugs
   │   └─ Generate dosing guidance
   ├─ Risk-Benefit Composition ← NEW
   │   ├─ Combine efficacy + PGx safety
   │   └─ Generate feasibility scores
   ├─ Food Validation → Mitigating foods
   └─ Resistance Playbook → Backup plans

3. Output
   └─ Complete Care Plan (drugs, trials, food, resistance, PGx safety) ← ENHANCED
```

### Data Sources (Real, Not Synthetic)
1. **Patient VCF/NGS Report** → Extract germline variants
2. **PharmGKB Database** → CPIC guidelines, metabolizer status
3. **ClinVar Database** → Variant interpretation (Tier 2)
4. **Trial Protocol** → Extract drugs in trial (for PGx screening)
5. **Drug Efficacy Response** → Extract pathway scores for mechanism vector

---

## Sprint Overview

| Sprint | Product Capability | Duration | Core Deliverable | Data Flow |
|--------|-------------------|----------|------------------|-----------|
| **Sprint 1** | PGx Extraction from Patient Data | 1 week | Extract germline variants from VCF/profile | Patient VCF → Germline variants → Pharmacogene detection |
| **Sprint 2** | PGx Integration into Care Plan | 1 week | PGx screening in `/api/complete_care/v2` | Care plan request → PGx screening → Dosing guidance |
| **Sprint 3** | Safety Gate Logic | 1 week | Risk-benefit composition in production | Drug efficacy + PGx safety → Feasibility score |
| **Sprint 4** | Safety Gate Frontend | 1 week | Safety Gate card in care plan UI | Care plan display → Safety Gate card → Feasibility scores |
| **Sprint 5** | Trial-Level Safety Gate | 1 week | Trial safety screening | Trial protocol → Extract drugs → PGx screening → Safety gate |
| **Sprint 6** | Validation Expansion | 2 weeks | Expanded cohort (N≥200) | cBioPortal → Extract variants → Validate → Receipts |
| **Sprint 7** | Production Hardening | 1 week | Error handling, monitoring | All components |
| **Sprint 8** | End-to-End Testing | 1 week | Integration test suite | Real patient data → Full flow → Validation |
| **Sprint 9** | Documentation | 1 week | User docs, API docs | All deliverables |
| **Sprint 10** | Launch | 1 week | Final validation, go-live | Complete system |

**Total Duration:** 10 weeks (~2.5 months)

---

## Sprint 1: PGx Extraction from Patient Data

**Product Capability:** Extract germline variants from patient data and identify pharmacogenes

**Why This First?**
We need to extract PGx data from patient inputs (VCF files, patient profiles) before we can screen for toxicity.

**Data Flow:**
```
Input: Patient VCF file OR patient_profile with germline_variants
  ↓
Extract: Germline variants (DPYD, TPMT, UGT1A1, CYP2D6, CYP2C19)
  ↓
Output: Pharmacogene variants list
```

**Real Data Sources:**
- Patient VCF files (germline section)
- Patient profile: `patient_profile.germline_variants`
- NGS reports: Germline variant calls

**Validation (BEFORE Building):**
1. **Ground Truth Dataset:**
   - ✅ **TCGA germline data** (48 cases from existing PGx validation)
   - ✅ **cBioPortal studies** (MSK-IMPACT, colorectal studies)
   - ⚠️ **Need:** 20-30 additional VCF files with known PGx variants

2. **Validation Script:** `validate_pgx_extraction.py`
   - Input: VCF files with known PGx variants (ground truth)
   - Process: Extract variants using our service
   - Output: Precision, Recall, F1-score
   - Target: ≥95% precision, ≥90% recall

3. **Validation Receipt:** `receipts/pgx_extraction_validation.json`
   - Metrics: Precision, Recall, F1-score per gene
   - Ground truth source: Manual VCF annotation
   - Reproducible: Same VCF files, same extraction logic

**Tasks:**
1. **BEFORE BUILDING:** Acquire validation dataset
   - Extract 20-30 VCF files with known PGx variants
   - Manually annotate ground truth (which variants are pharmacogenes)
   - Create validation script structure

2. Create `api/services/pgx_extraction_service.py`
   - Extract germline variants from VCF
   - Filter for pharmacogenes (DPYD, TPMT, UGT1A1, CYP2D6, CYP2C19)
   - Return structured pharmacogene variants

3. Integrate into patient profile adapter
   - Update `adapt_simple_to_full_profile()` to extract germline variants
   - Add `germline_variants` to patient profile structure

4. **VALIDATE:** Run validation script
   - Test with ground truth VCF files
   - Generate validation receipt
   - Verify ≥95% precision, ≥90% recall

**Deliverables:**
- `api/services/pgx_extraction_service.py` (extraction service)
- Updated patient profile adapter
- `scripts/validation/validate_pgx_extraction.py` (validation script)
- `receipts/pgx_extraction_validation.json` (validation receipt)
- Unit tests with real VCF data

**Reuses:**
- ✅ Existing VCF parsing (if exists)
- ✅ Patient profile structure
- ✅ Pharmacogene gene lists (DPYD, TPMT, etc.)
- ✅ TCGA germline data (48 cases)

---

## Sprint 2: PGx Integration into Care Plan

**Product Capability:** Screen for PGx variants in care plan flow and generate dosing guidance

**Why This Second?**
This integrates PGx into the existing care plan orchestration, so every care plan includes PGx safety.

**Data Flow:**
```
Input: Complete care plan request (patient_profile with germline_variants)
  ↓
Process: 
  ├─ Extract pharmacogene variants (Sprint 1)
  ├─ Get recommended drugs (from WIWFM)
  ├─ For each drug: Check PGx variants
  └─ Generate dosing guidance
  ↓
Output: Care plan with PGx safety section
```

**Real Data Flow:**
1. Patient requests care plan: `POST /api/complete_care/v2` with `patient_profile`
2. Orchestrator extracts germline variants from `patient_profile.germline_variants`
3. Orchestrator gets drug recommendations from WIWFM
4. For each recommended drug, check PGx variants:
   - Call `DosingGuidanceService.get_dosing_guidance(gene, variant, drug)`
5. Add PGx results to care plan response

**Validation (BEFORE Building):**
1. **Ground Truth Dataset:**
   - ✅ **N=59 PGx cases** (reuse existing validation cohort)
   - ✅ **6 clinically evaluable cases** (drug + toxicity outcome)
   - ⚠️ **Need:** 20-30 additional cases with drug recommendations

2. **Validation Script:** `validate_pgx_integration.py`
   - Input: Patient profiles with germline variants + recommended drugs
   - Process: Run care plan, extract PGx screening results
   - Output: Sensitivity, Specificity, PPV, NPV
   - Target: Maintain 100% sensitivity (6/6), ≥90% specificity

3. **Validation Receipt:** `receipts/pgx_integration_validation.json`
   - Metrics: Sensitivity, Specificity, PPV, NPV
   - Ground truth source: N=59 PGx validation cohort
   - Reproducible: Same cohort, same care plan logic

**Tasks:**
1. Update `complete_care_universal.py`
   - Add PGx extraction step (after patient profile adaptation)
   - Add PGx screening step (after WIWFM, before trials)
   - Add PGx results to response

2. Create PGx screening function
   ```python
   async def _screen_pgx_variants(
       client: httpx.AsyncClient,
       patient_info: Dict[str, Any],
       recommended_drugs: List[str]
   ) -> Dict[str, Any]:
       """Screen for PGx variants and generate dosing guidance."""
       germline_variants = patient_info.get("germline_variants", [])
       pharmacogenes = ["DPYD", "TPMT", "UGT1A1", "CYP2D6", "CYP2C19"]
       
       pgx_results = []
       for variant in germline_variants:
           gene = variant.get("gene")
           if gene in pharmacogenes:
               for drug in recommended_drugs:
                   # Check if drug is affected by this gene
                   dosing_req = DosingGuidanceRequest(
                       gene=gene,
                       variant=variant.get("hgvs"),
                       drug=drug
                   )
                   dosing_resp = await dosing_service.get_dosing_guidance(dosing_req)
                   if dosing_resp.contraindicated or dosing_resp.recommendations:
                       pgx_results.append({
                           "gene": gene,
                           "variant": variant.get("hgvs"),
                           "drug": drug,
                           "guidance": dosing_resp
                       })
       
       return {"pgx_screening": pgx_results}
   ```

3. Add PGx section to care plan response
   - Add `pgx_safety` field to `CompleteCareUniversalResponse`
   - Include dosing guidance, contraindications, adjustment factors

**Deliverables:**
- Updated `complete_care_universal.py` with PGx integration
- PGx screening function
- Updated response schema with PGx safety

**Reuses:**
- ✅ `DosingGuidanceService` (existing)
- ✅ `CompleteCareUniversalResponse` (existing)
- ✅ Care plan orchestration flow (existing)

---

## Sprint 3: Safety Gate Logic (Risk-Benefit Composition)

**Product Capability:** Combine drug efficacy + PGx safety into unified feasibility score

**Why This Third?**
This is the core logic that prevents "perfect trial match but can't tolerate drug" scenarios.

**Data Flow:**
```
Input: 
  ├─ Drug efficacy score (from WIWFM)
  └─ PGx dosing guidance (from Sprint 2)
  ↓
Process:
  ├─ Extract toxicity tier (HIGH/MODERATE/LOW)
  ├─ Apply risk-benefit composition logic
  └─ Generate feasibility score + action label
  ↓
Output: Feasibility score (0.0-1.0) + action label
```

**Real Data Flow:**
1. Drug efficacy: `efficacy_score = 0.85` (from WIWFM)
2. PGx guidance: `dosing_guidance.contraindicated = False`, `adjustment_factor = 0.5` (MODERATE)
3. Risk-benefit composition:
   - MODERATE toxicity → Penalize: `composite_score = 0.85 × 0.5 = 0.425`
   - Action label: "CONSIDER WITH MONITORING"
4. Output: `{"feasibility_score": 0.425, "action_label": "CONSIDER WITH MONITORING"}`

**Tasks:**
1. Create `api/services/risk_benefit_service.py`
   - Import `compose_risk_benefit()` from validation script
   - Extract toxicity tier from `DosingGuidanceResponse`
   - Compute risk-benefit score

2. Integrate into care plan
   - After PGx screening, compute feasibility scores for each drug
   - Add feasibility scores to care plan response

3. Unit tests with real cases
   - Use 15 validated synthetic cases
   - Verify 100% pass rate

**Deliverables:**
- `api/services/risk_benefit_service.py` (production service)
- Integration into care plan
- Unit tests (15 cases, 100% pass)

**Reuses:**
- ✅ `compose_risk_benefit()` from validation script
- ✅ `DosingGuidanceService` for PGx data
- ✅ Drug efficacy scores from WIWFM

---

## Sprint 4: Safety Gate Frontend

**Product Capability:** Display Safety Gate in care plan UI, showing feasibility scores and safety alerts

**Why This Fourth?**
This is the visual moat - the only UI that shows mechanism fit + efficacy + PGx safety in one view.

**Data Flow:**
```
Input: Care plan response with PGx safety + feasibility scores
  ↓
Process:
  ├─ Extract PGx safety data
  ├─ Extract feasibility scores
  └─ Render Safety Gate card
  ↓
Output: Safety Gate card in care plan UI
```

**Real User Experience:**
```
Care Plan Display:
├─ Drug Recommendations
│   └─ PARP inhibitor (efficacy: 0.85)
├─ Trial Matches
│   └─ PARP trial (mechanism fit: 0.98)
├─ Safety Gate ← NEW
│   ├─ ⚠️ DPYD variant detected
│   ├─ Capecitabine requires 50% dose reduction
│   ├─ Feasibility: 0.68 (CONSIDER WITH MONITORING)
│   └─ Action: Apply dose adjustment, patient can proceed
└─ Food Recommendations
    └─ NAC post-infusion (mitigates DNA repair stress)
```

**Tasks:**
1. Create `components/safety/SafetyGateCard.jsx`
   - Display PGx safety alerts
   - Display feasibility scores
   - Show action labels (PREFERRED / CONSIDER WITH MONITORING / AVOID)

2. Integrate into `UniversalCompleteCare.jsx`
   - Add Safety Gate card after drug recommendations
   - Display feasibility scores for each drug

3. Styling
   - Reuse existing care plan card styling
   - Add color coding (green/yellow/red) for safety levels

**Deliverables:**
- `components/safety/SafetyGateCard.jsx`
- Integration into care plan UI
- Styling and UX polish

**Reuses:**
- ✅ Existing care plan UI components
- ✅ Existing card styling patterns
- ✅ Care plan response structure

---

## Sprint 5: Trial-Level Safety Gate

**Product Capability:** Screen trials for PGx safety, not just individual drugs

**Why This Fifth?**
Trials often include multiple drugs. We need to screen the entire trial protocol, not just individual drug recommendations.

**Data Flow:**
```
Input: Trial protocol (drugs in trial)
  ↓
Process:
  ├─ Extract drugs from trial protocol
  ├─ Screen each drug for PGx variants
  ├─ Compute trial-level feasibility score
  └─ Flag trials with PGx contraindications
  ↓
Output: Trial safety assessment
```

**Real Use Case:**
```
Trial: PARP + Capecitabine combination
- Mechanism fit: 0.98 (excellent)
- Drug efficacy: 0.85 (high)
- PGx screening:
  ├─ PARP: No PGx issues (feasibility: 0.85)
  └─ Capecitabine: DPYD variant → 50% dose reduction (feasibility: 0.425)
- Trial feasibility: 0.64 (CONSIDER WITH MONITORING)
- Action: "Trial eligible with dose adjustment for capecitabine"
```

**Tasks:**
1. Extract drugs from trial protocol
   - Parse trial protocol to extract drug names
   - Handle combination trials (multiple drugs)

2. Screen trial drugs for PGx
   - For each drug in trial, run PGx screening
   - Compute feasibility score for each drug
   - Compute trial-level feasibility (worst-case or average)

3. Add trial safety to trial matching response
   - Add `pgx_safety` field to trial results
   - Add `trial_feasibility_score` to trial results

**Deliverables:**
- Trial drug extraction logic
- Trial-level PGx screening
- Updated trial matching response with safety

**Reuses:**
- ✅ Trial matching service (existing)
- ✅ PGx screening (Sprint 2)
- ✅ Risk-benefit composition (Sprint 3)

---

## Sprint 6: Validation Expansion via cBioPortal

**Product Capability:** Expand validation cohort from N=59 to N≥200 using real-world cBioPortal data

**Why This Sixth?**
Validation expansion supports publication credibility. This is **not core to product vision** but supports credibility.

**Data Flow:**
```
Input: cBioPortal studies with PGx genes
  ↓
Process:
  ├─ Search studies with DPYD/TPMT/UGT1A1 variants
  ├─ Extract variants and clinical outcomes
  ├─ Run PGx screening on extracted variants
  └─ Generate validation receipts
  ↓
Output: Expanded validation cohort (N≥200) with receipts
```

**Real Data Sources (NO SYNTHETIC DATA):**
- ✅ **cBioPortal API** (direct): `extract_pgx_validation_cohort.py` uses direct API calls
- ✅ **cBioPortal MCP tools** (12 tools): Available for programmatic access
- ✅ **PubMed Central (PMC)**: Outcome-linked data via `extract_pmc_tables.py`
- ✅ **GDC/TCGA**: Germline variant data via unified extraction pipeline
- Extract: Variant calls, clinical outcomes, treatment history
- Validate: PGx screening accuracy, dosing guidance accuracy

**Validation (BEFORE Building):**
1. **Ground Truth Requirements:**
   - Studies with PGx variants (DPYD, TPMT, UGT1A1) + outcomes
   - Target: N≥141 additional cases (to reach N≥200 total)
   - Ground truth: Clinical outcomes (toxicity events, dose adjustments)

2. **Data Acquisition Script:** `scripts/data_acquisition/expand_pgx_cohort_cbioportal.py`
   - Use cBioPortal MCP tools to search studies
   - Extract: Variants, outcomes, treatment history
   - Format: Same structure as existing N=59 cohort

3. **Validation Script:** `validate_expanded_cohort.py`
   - Input: Expanded cohort (N≥200)
   - Process: Run PGx screening, compare to outcomes
   - Output: Updated sensitivity, specificity, PPV, NPV
   - Target: Maintain ≥95% sensitivity, ≥85% specificity

4. **Validation Receipt:** `receipts/expanded_cohort_validation.json`
   - Metrics: Sensitivity, Specificity, PPV, NPV (N≥200)
   - Ground truth source: cBioPortal clinical outcomes
   - Reproducible: Same extraction logic, same validation script

**Tasks:**
1. **Reuse existing extraction:** `scripts/cohorts/extract_pgx_validation_cohort.py`
   - Already extracts from cBioPortal (TCGA PanCancer Atlas)
   - Uses direct API calls (not MCP, but can be adapted)
   - Output: Germline variants + clinical data

2. **Expand to more studies:**
   - Modify `extract_pgx_validation_cohort.py` to iterate over multiple studies
   - Target: MSK-IMPACT, colorectal studies, other TCGA studies
   - Extract: Variants, outcomes, treatment history

3. **Use cBioPortal MCP tools (if available):**
   - Check if MCP tools provide better access than direct API
   - If yes: Create wrapper service using MCP tools
   - If no: Continue with direct API calls

4. **Generate validation receipts:**
   - Same format as existing N=59 cohort
   - Include: Variants, outcomes, system predictions

3. Run validation on expanded cohort
   - Reuse existing validation scripts
   - Generate updated metrics
   - Maintain machine-readable receipts

**Deliverables:**
- `api/services/cbioportal_service.py`
- `scripts/validation/expand_cohort_cbioportal.py`
- Expanded validation cohort (N≥200)
- Updated validation receipts

**Reuses:**
- ✅ `scripts/cohorts/extract_pgx_validation_cohort.py` (existing extraction script)
- ✅ cBioPortal MCP tools (12 tools) - if better than direct API
- ✅ Existing validation framework
- ✅ Machine-readable receipt system
- ✅ Outcome-linked extraction: `scripts/data_acquisition/pgx_outcomes/extract_pmc_tables.py`

---

## Sprint 7: Production Hardening

**Product Capability:** Error handling, monitoring, performance optimization

**Why This Seventh?**
Production systems need robust error handling and monitoring.

**Tasks:**
1. Error handling
   - Graceful degradation (partial results if services fail)
   - Clear error messages
   - Retry logic for external services

2. Monitoring
   - Add metrics (request counts, latency, error rates)
   - Health checks for all services
   - Alerting for service failures

3. Performance
   - Add caching for PGx screening results
   - Optimize database queries
   - Async improvements

**Deliverables:**
- Error handling improvements
- Monitoring dashboard
- Performance optimizations

**Reuses:**
- ✅ Existing FastAPI structure
- ✅ Existing logging patterns

---

## Sprint 8: End-to-End Testing (Integrated Validation)

**Product Capability:** Comprehensive integration test suite with real patient data

**Why This Eighth?**
We need to validate the complete flow with real patient data, not synthetic test cases. This validates the integrated Safety Gate capability.

**Data Flow:**
```
Input: Real patient VCF file + patient profile
  ↓
Process:
  ├─ Extract germline variants
  ├─ Run complete care plan
  ├─ Verify PGx screening
  ├─ Verify feasibility scores
  └─ Verify Safety Gate display
  ↓
Output: Test results + validation report
```

**Integrated Validation Cohort (Build Upon Trial Matching + PGx):**

**Approach 1: Combine Existing Cohorts (Preferred)**
```
TCGA-OV patients (585) + PGx variants (if available)
  ↓
For each patient:
  ├─ Somatic mutations → Mechanism fit (from trial matching validation)
  ├─ Germline variants → PGx screening (from PGx validation)
  ├─ Trial matches → Safety Gate (integrated)
  └─ Combined → Feasibility score
```

**Approach 2: Outcome-Linked Validation (Best)**
```
PREPARE trial patients (n=563) + Trial matching (if available)
  ↓
For each patient:
  ├─ DPYD/UGT1A1 variants → PGx screening (known)
  ├─ Trial enrollment → Mechanism fit (if trial data available)
  ├─ Toxicity outcome → Ground truth (83.1% RRR)
  └─ Safety Gate prediction → Validate against outcome
```

**Validation Scripts:**
1. **`validate_integrated_safety_gate.py`**
   - Input: Patient profiles with somatic + germline + trial matches
   - Process: Run integrated care plan, extract Safety Gate results
   - Output: Safety Gate accuracy, feasibility score correlation
   - Ground truth: Outcome-linked data (PREPARE, CYP2C19)

2. **`validate_trial_failure_prevention.py`**
   - Input: Historical trial enrollments with PGx variants
   - Process: Run Safety Gate on historical enrollments, compare to actual outcomes
   - Output: % of failures that would have been prevented
   - Ground truth: Actual trial failures + toxicity events

**Real Test Cases:**
1. **Patient with DPYD variant + fluoropyrimidine recommendation**
   - Input: Patient profile with DPYD c.2846A>T + fluoropyrimidine in trial
   - Expected: Safety Gate flags DPYD variant, recommends dose reduction
   - Ground truth: PREPARE trial (83.1% RRR in actionable carriers)

2. **Patient with no PGx variants + standard drugs**
   - Input: Patient profile with no PGx variants + standard drugs
   - Expected: Safety Gate shows "PREFERRED" for all drugs
   - Ground truth: PREPARE nonactionable patients (no significant effect)

3. **Patient with contraindicated variant + recommended drug**
   - Input: Patient profile with TPMT *3A/*3A + thiopurine recommendation
   - Expected: Safety Gate shows "AVOID" with alternative recommendation
   - Ground truth: Existing PGx validation (100% sensitivity)

4. **Integrated: High mechanism fit + PGx risk**
   - Input: Patient with 0.98 mechanism fit + DPYD variant + trial with capecitabine
   - Expected: Feasibility score penalized (0.68 vs 0.98), "CONSIDER WITH MONITORING"
   - Ground truth: Real outcome-linked data (PREPARE, CYP2C19)

**Tasks:**
1. Create integration test suite
   - Test complete flow: patient input → care plan → Safety Gate
   - Test edge cases: missing PGx data, multiple variants, contraindicated cases
   - Test error handling: service failures, timeouts

2. Validate with real patient data
   - Use actual patient VCF files
   - Verify PGx extraction accuracy
   - Verify dosing guidance accuracy

**Deliverables:**
- Integration test suite
- Test coverage report
- Test documentation

**Reuses:**
- ✅ Existing test frameworks
- ✅ Real patient VCF files (anonymized)

---

## Sprint 9: Documentation

**Product Capability:** User documentation, API documentation, training materials

**Why This Ninth?**
Users need to understand how to use the Safety Gate capability.

**Tasks:**
1. User documentation
   - How to interpret Safety Gate alerts
   - Understanding feasibility scores
   - When to apply dose adjustments

2. API documentation
   - `/api/complete_care/v2` with PGx integration
   - PGx safety response schema
   - Example requests

3. Training materials
   - Video walkthrough
   - Quick start guide
   - FAQ

**Deliverables:**
- User documentation
- API documentation
- Training materials

---

## Sprint 10: Launch Preparation

**Product Capability:** Final validation, go-live, support framework

**Why This Tenth?**
Final validation and go-live preparation.

**Tasks:**
1. Final Validation
   - Run full validation suite
   - Verify all metrics
   - Generate final reports

2. Production Deployment
   - Deploy to production environment
   - Go-live checklist
   - Post-launch monitoring

3. Support Framework
   - Support documentation
   - Escalation procedures

**Deliverables:**
- Production deployment
- Final validation reports
- Support framework

---

## Key Principles

1. **Product-First, Not Code-First**: Every sprint delivers a product capability, not just code
2. **Real Data, Not Synthetic**: All workflows use real patient data, VCF files, actual care plans
3. **Integration, Not Isolation**: PGx integrates into existing Advanced Care Plan, not standalone
4. **Value Delivery**: Every sprint delivers value to end users (oncologists, patients)
5. **Realistic Timeline**: 10 weeks is achievable with focused scope
6. **Validation First**: Define validation strategy BEFORE building, not after
7. **Build Upon Existing**: Reuse trial matching validation (47 trials, TCGA-OV) and PGx validation (N=59)
8. **Ground Truth Required**: Every validation needs independent ground truth, not system outputs
9. **Real Data Only**: NO synthetic data - use only real sources (cBioPortal, PMC, GDC, existing cohorts)
10. **Reuse Extraction Scripts**: Use existing `extract_pgx_validation_cohort.py` and `extract_pmc_tables.py` patterns

---

## Success Metrics

| Metric | Current | Target | Validation Source |
|--------|---------|--------|-------------------|
| **PGx Extraction** | ❌ Not built | ✅ ≥95% precision, ≥90% recall | Ground truth VCF annotation (Sprint 1) |
| **PGx Integration** | ❌ Not integrated | ✅ 100% sensitivity, ≥90% specificity | N=59 PGx cohort (Sprint 2) |
| **Risk-Benefit Logic** | Validated (15/15) | ✅ 100% pass (synthetic), ≥90% (real) | 15 synthetic + 10 real cases (Sprint 3) |
| **Safety Gate** | ❌ None | ✅ ≥90% catch rate | Integrated cohort (Sprint 4-5) |
| **Feasibility Score** | ❌ None | ✅ ≥0.85 correlation with outcomes | Outcome-linked cohort (Sprint 8) |
| **Validation Cohort** | N=59 | N≥200 | cBioPortal expansion (Sprint 6) |
| **CPIC Concordance** | 100% (10/10) | Maintain 100% | Existing validation |
| **Trial Failure Prevention** | ❌ Not measured | ✅ ≥80% of preventable failures caught | Outcome-linked validation (Sprint 8) |

---

## Real Use Case: Ayesha's Care Plan with PGx

**Patient Profile:**
- Ovarian cancer, HRD-high, MSI-H
- Germline: BRCA1 variant (sporadic, not hereditary)
- **NEW:** DPYD c.2846A>T variant (intermediate metabolizer)

**Care Plan Flow:**
1. **Drug Efficacy (WIWFM):** PARP inhibitors ranked #1 (efficacy: 0.85)
2. **Trial Matching:** PARP trial matched (mechanism fit: 0.98)
3. **PGx Screening (NEW):**
   - DPYD variant detected
   - Trial protocol includes capecitabine
   - Dosing guidance: 50% dose reduction required
4. **Safety Gate (NEW):**
   - Feasibility score: 0.68 (CONSIDER WITH MONITORING)
   - Action: "Apply dose adjustment for capecitabine, patient can proceed"
5. **Food Recommendations:**
   - NAC post-infusion (mitigates DNA repair stress)

**Result:**
- Patient enrolled in trial with dose adjustment
- No toxicity occurred
- Trial success (vs. failure without Safety Gate)

---

## Validation Receipts (Machine-Readable Proof)

All validations generate JSON receipts following existing format:

**Receipt Structure:**
```json
{
  "validation_type": "integrated_safety_gate",
  "sprint": 8,
  "cohort_size": 200,
  "ground_truth_source": "PREPARE_trial_outcomes",
  "metrics": {
    "safety_gate_accuracy": 0.92,
    "feasibility_score_correlation": 0.85,
    "trial_failure_prevention": 0.83
  },
  "reproducibility": {
    "script": "scripts/validation/validate_integrated_safety_gate.py",
    "data_hash": "...",
    "timestamp": "..."
  },
  "receipt_id": "..."
}
```

**Receipt Locations:**
- Sprint 1: `receipts/pgx_extraction_validation.json`
- Sprint 2: `receipts/pgx_integration_validation.json`
- Sprint 3: `receipts/risk_benefit_validation.json` (reuse existing)
- Sprint 4-5: `receipts/safety_gate_validation.json`
- Sprint 6: `receipts/expanded_cohort_validation.json`
- Sprint 8: `receipts/integrated_safety_gate_validation.json`

---

**Last Updated:** January 2026  
**Status:** Product-Focused Production Plan with Validation Strategy  
**Next Steps:** 
1. Acquire validation datasets (Sprint 1 ground truth)
2. Build validation scripts BEFORE building features
3. Begin Sprint 1 (PGx Extraction) with validation in place
