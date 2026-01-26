# Clinical Outcomes Validation Protocol (Publication-Grade)

**Project:** PGx Dosing Guidance (Outcome-Linked Validation)  
**Folder:** `publications/05-pgx-dosing-guidance/`  
**Status:** Draft protocol (ready to execute / cite)  

---

## Purpose (what “validated” means here)

This validation is **clinical-outcomes anchored**. We validate *claims* about PGx decision support using **real, outcome-linked cohorts** (not synthetic patient simulations, and not “tests passed”).

Validation deliverables are **machine-readable receipts** that:
- preserve extracted outcome tables,
- compute effect sizes from those tables,
- and allow independent recomputation/audit of every manuscript number.

---

## Primary claims (what we are proving)

### Claim A — Toxicity prevention (DPYD/UGT1A1; PREPARE)
**Question:** In patients with actionable genotypes, does genotype-guided dosing reduce clinically relevant toxicity compared with control?  
**Evidence standard:** outcome-linked, table-derived arm × stratum rates.

### Claim B — Specificity via negative controls (PREPARE)
**Question:** In nonactionable genotypes (true negatives), do outcomes remain similar across arms, supporting specificity (no “fake benefit” signal)?  
**Evidence standard:** outcome-linked negative controls with documented outcomes.

### Claim C — Borderline efficacy phenotype risk (CYP2C19–clopidogrel)
**Question:** Do Poor/Intermediate metabolizers have materially higher ischemic event risk on clopidogrel vs Extensive metabolizers?  
**Evidence standard:** outcome-linked phenotype-stratified event rates.

### Claim D — Tier 2 heuristic safety threshold
**Question:** For rare/high-consequence variants outside CPIC, does Tier 2 operate as a high-sensitivity screen with 0 false negatives in retrospective outcome-labeled cases?  
**Evidence standard:** retrospective case set with toxicity outcomes and explicit "flag for review" behavior.

### Claim E — Trial failure prevention (Safety Gate)
**Question:** Would application of the Safety Gate to trial enrollment have prevented toxicity events in patients with actionable PGx variants?  
**Evidence standard:** PREPARE trial projection (applying intervention rates to control arm) + Tier 2 retrospective case detection.  
**Validated:** January 8, 2026

---

## Cohorts (ground truth sources)

### Cohort 1: PREPARE secondary analysis (DPYD/UGT1A1)
- **PMID/PMC:** 39641926 / PMC11624585
- **Outcome type:** clinically relevant toxic effects (table-level)
- **Total:** 563
  - Control: 311
  - Intervention: 252
- **Strata:**
  - Actionable carriers: 40 (23 control, 17 intervention)
  - Nonactionable (negative controls): 523 (288 control, 235 intervention)
- **Primary receipt:** `reports/prepare_outcome_validation.json`

### Cohort 2: CYP2C19 clopidogrel-treated subset
- **PMID/PMC:** 40944685 / PMC12673833
- **Outcome type:** symptomatic ischemic stroke/TIA (table-level)
- **Total (clopidogrel subset):** 210
  - Extensive metabolizer: 106
  - Poor/Intermediate: 104
- **Primary receipt:** `reports/cyp2c19_clopidogrel_efficacy_validation.json`

### Cohort 3: Tier 2 retrospective case set
- **Size:** 21 total cases (16 scorable, 6 toxicity-positive in receipt summary)
- **Primary receipt:** `reports/tier2_heuristic_validation_results.json`

### Cohort 4: Trial Failure Prevention (Combined)
- **Sources:** PREPARE + Tier 2
- **Validation type:** Projection + retrospective detection
- **Primary receipt:** `reports/trial_failure_prevention_validation.json`
- **Key metrics:**
  - Prevented toxicities: 7/8 (87.5% prevention rate)
  - Tier 2 detection: 8/8 severe cases flagged
  - Gene coverage: 100%

### Combined publication receipt (single "source of truth")
- **Receipt:** `reports/publication_receipt_v3.json`
- **Role:** canonical link from manuscript version → cohort receipts → key metrics.

---

## Endpoints (clinically meaningful, publication-ready)

### PREPARE endpoints
- **Primary endpoint:** toxicity event rate in **actionable carriers**, control vs intervention.
- **Negative control endpoint:** toxicity event rate in **nonactionable**, control vs intervention.

### CYP2C19 endpoints
- **Primary endpoint:** event rate ratio (PM/IM vs EM) in clopidogrel-treated subset.

### Tier 2 endpoints
- **Primary endpoint:** sensitivity (toxicity-positive cases flagged/acted on).
- **Safety threshold:** **0 false negatives** in retrospective, outcome-labeled positives.

---

## Analysis plan (minimal computation, maximal clinical grounding)

We do not “train a model.” We compute **clinically interpretable effect sizes** directly from outcome tables:
- Relative Risk Reduction (RRR) for PREPARE actionable carriers.
- Risk Ratio (RR) for CYP2C19 phenotype strata.
- Exact tests as supplementary (Fisher’s exact), with explicit note when manuscript uses paper-reported p-values vs receipt recomputation.

All calculations must be reproducible from receipt-contained `raw_table_data`.

---

## Product correctness vs clinical validation (explicit separation)

### Clinical validation (publication)
Anchored entirely on Cohort 1–3 outcomes + receipts + audit.

### Product correctness (implementation verification)
We verify that the system outputs **guideline-concordant actions** (e.g., “avoid”, “reduce”, “use alternative”) for representative diplotypes/variants. These checks are **not** used to claim effect sizes—only that the product behaves correctly given inputs.

---

## Key limitations (stated up front for reviewer trust)

- **Table-level outcomes (PREPARE, CYP2C19):** We do not have patient-level genotypes/outcomes, so we do not claim patient-level predictive modeling, AUC, or individualized calibration.
- **Counterfactual “trial failure prevention”:** Requires trial enrollment + protocol + adverse event attribution. Without that dataset, we treat it as a product hypothesis, not a validated clinical claim.
- **Tier 2:** Explicitly a high-sensitivity screen requiring expert pharmacist review (RUO; not a substitute for clinical adjudication).

---

## Acceptance criteria (what “validated for publication” means)

We are publication-ready when:
- `FINAL_AUDIT_REPORT.md` shows each manuscript claim is backed by a receipt.
- `reports/publication_receipt_v3.json` correctly links manuscript version → receipt files → key metrics.
- A reproducibility script can recompute:
  - PREPARE RRR and negative-control stability from `raw_table_data`.
  - CYP2C19 RR from `raw_table_data`.
- The manuscript clearly states limitations (table-level outcomes; RUO; Tier 2 review requirement).

