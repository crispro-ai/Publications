# Evidence Tier Hierarchy - Trial Failure Prevention Claim

**Purpose:** Document evidence strength for "Safety Gate prevents trial failures" claim  
**Date:** January 13, 2025  
**Status:** Current evidence assessment + gap identification

---

## Evidence Hierarchy

| Evidence Tier | Description | CrisPRO Status | Clinical Impact |
|---------------|-------------|----------------|-----------------|
| **Retrospective** | Historical data analysis - applying Safety Gate to past trials that failed | ⚠️ **NOT DONE** | Would show what **COULD** have been prevented if Safety Gate existed |
| **Projection** | Modeling/simulation - applying Safety Gate logic to successful trial (PREPARE) | ✅ **DONE** | Estimates future benefit (87.5% prevention rate) |
| **Prospective observational** | Real-world deployment - Safety Gate used in active trials, outcomes tracked | ❌ **NOT DONE** | Would show actual prevention in real trials |
| **Randomized controlled** | Gold standard - RCT comparing trials with vs without Safety Gate | ❌ **NOT DONE** | Definitive proof of trial failure prevention |

---

## Current Evidence Assessment

### ✅ **PROJECTION (Done)**
**Source:** PREPARE Trial (PMID 39641926)  
**Method:** Applied Safety Gate logic retrospectively to PREPARE control arm  
**Finding:** Would prevent 7/8 toxicities (87.5% prevention rate)  
**Evidence Strength:** **MODERATE** - Demonstrates potential, not actual prevention  

**Limitations:**
- PREPARE trial **succeeded** (not a failed trial)
- Projection assumes Safety Gate intervention arm results (5.9% toxicity) would apply
- Does not address actual trial termination scenarios

**Receipt:** `reports/trial_failure_prevention_validation.json`

---

### ⚠️ **RETROSPECTIVE (Gap - Not Done)**
**What's Needed:**
- Find trial(s) that **actually terminated early** due to toxicity
- Extract patient genotypes for severe toxicity cases
- Apply Safety Gate algorithm retrospectively
- Calculate: Would Safety Gate have flagged these patients?

**Expected Output:**
> "Trial NCT# was terminated due to Grade 3-4 toxicity in 6/30 patients. Retrospective Safety Gate screening flagged 5/6 cases (83% sensitivity). If screening had been used, trial would have met safety threshold and continued to completion."

**Evidence Strength (If Done):** **HIGH** - Real-world validation on failed trials

---

### ❌ **PROSPECTIVE OBSERVATIONAL (Not Done)**
**What's Needed:**
- Deploy Safety Gate in active clinical trials
- Track outcomes: toxicity rates, trial completion rates
- Compare to historical controls

**Evidence Strength:** **VERY HIGH** - Real-world prevention demonstrated

---

### ❌ **RANDOMIZED CONTROLLED (Not Done)**
**What's Needed:**
- RCT comparing trials with vs without Safety Gate pre-screening
- Primary endpoint: Trial completion rate
- Secondary endpoints: Toxicity rates, time to termination

**Evidence Strength:** **HIGHEST** - Gold standard evidence

---

## Evidence Upgrade Path

### Current State: **PROJECTION** (Moderate Strength)
- Claim: "Safety Gate prevents trial failures"
- Evidence: PREPARE projection (87.5% prevention rate)
- Status: ⚠️ **UNDERSELLING** - Claim implies prevention, but evidence is projection

### Target State: **RETROSPECTIVE** (High Strength)
- Claim: "Safety Gate prevents trial failures"
- Evidence: Retrospective validation on **actual terminated trials**
- Status: ✅ **RECEIPT-BACKED** - Would show real-world validation

---

## Next Steps (From User Task)

1. ✅ **Document evidence tier** (THIS FILE) - COMPLETE
2. 🔄 **Find trials that failed due to toxicity** (In progress)
   - Search ClinicalTrials.gov for terminated trials
   - Focus: Oncology trials with fluoropyrimidines/thiopurines
   - Target: DPYD/TPMT variants implicated
3. ⏳ **Retrospectively apply Safety Gate** (Pending Step 2)
   - Extract patient genotypes
   - Apply Safety Gate algorithm
   - Calculate prevention rate

---

## Recommendation

**Current Claim Wording:**
> "Trial failure prevention projection: applying Safety Gate logic to the PREPARE control arm would prevent 7/8 toxicities (87.5% prevention rate)"

**Suggested Upgrade (After Step 2-3 Complete):**
> "Trial failure prevention: Retrospective Safety Gate screening on [NCT#] (terminated due to toxicity in 6/30 patients) would have flagged 5/6 severe cases (83% sensitivity), enabling trial continuation."

**This upgrades claim from "projection" to "validated on independent terminated trial".**
