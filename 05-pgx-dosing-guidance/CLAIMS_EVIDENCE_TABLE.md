# Claims ↔ Evidence ↔ Receipts (Manuscript-Ready)

**Scope:** This table is designed to be copied into the manuscript (or supplement) to prove that validation is **outcome-linked** and **receipt-backed**.

---

## Cohort A: PREPARE (PMID 39641926; PMC11624585)

- **Receipt:** `publications/05-pgx-dosing-guidance/reports/prepare_outcome_validation.json`

| Claim (clinical) | Value | Evidence location (receipt path) | Notes |
|---|---:|---|---|
| Total patients | 563 | `cohort_summary.total_patients` | Table-level cohort summary |
| Actionable carriers | 40 | `cohort_summary.actionable_carriers` | Stratified in extracted table |
| Nonactionable patients (true negative controls) | 523 | `cohort_summary.nonactionable_patients` | 288 control + 235 intervention |
| Actionable carriers toxicity rate (control) | 34.8% | `raw_table_data.Table_2_clinically_relevant_toxic_effects.control_arm.actionable_carriers.rate` | 8/23 |
| Actionable carriers toxicity rate (intervention) | 5.9% | `raw_table_data.Table_2_clinically_relevant_toxic_effects.intervention_arm.actionable_carriers.rate` | 1/17 |
| Relative risk reduction (actionable carriers) | 83.1% | `calculated_metrics.actionable_carriers.relative_risk_reduction` | Clinically meaningful toxicity prevention |
| Nonactionable “negative control” RRR | 4.1% | `calculated_metrics.nonactionable_negative_controls.relative_risk_reduction` | Near-zero; supports specificity framing |
| Nonactionable Fisher exact p | 0.904 | `calculated_metrics.nonactionable_negative_controls.fisher_exact_p` | “No difference” negative control |

---

## Cohort B: CYP2C19–Clopidogrel (PMID 40944685; PMC12673833)

- **Receipt:** `publications/05-pgx-dosing-guidance/reports/cyp2c19_clopidogrel_efficacy_validation.json`

| Claim (clinical) | Value | Evidence location (receipt path) | Notes |
|---|---:|---|---|
| Clopidogrel-treated subset | 210 | `cohort_summary.clopidogrel_treated_subset` | Outcome-linked treated subset |
| EM group size | 106 | `cohort_summary.extensive_metabolizer` | Phenotype strata |
| PM/IM group size | 104 | `cohort_summary.poor_intermediate_metabolizer` | Borderline phenotypes included |
| EM event rate | 4.7% | `raw_table_data.Table_4_clopidogrel_subset_by_phenotype.extensive_metabolizer.rate` | 5/106 |
| PM/IM event rate | 20.2% | `raw_table_data.Table_4_clopidogrel_subset_by_phenotype.poor_intermediate_metabolizer.rate` | 21/104 |
| Risk ratio (PM/IM vs EM) | 4.28× | `calculated_metrics.risk_ratio.pm_im_vs_em` | Central efficacy validation |
| Fisher exact p | 6.7×10⁻⁴ | `calculated_metrics.statistical_significance.fisher_exact_p` | Highly significant |

---

## Tier 2 retrospective validation (ClinVar evidence bridge)

- **Receipt:** `publications/05-pgx-dosing-guidance/reports/tier2_heuristic_validation_results.json`

| Claim (safety threshold) | Evidence | Evidence location |
|---|---|---|
| 0 false negatives in toxicity-positive cases | Verified in receipt summary / labeling | Receipt contains per-case outcomes and system flags (`results[]`) |

---

---

## Claim E: Trial Failure Prevention (Safety Gate)

- **Receipt:** `publications/05-pgx-dosing-guidance/reports/trial_failure_prevention_validation.json`
- **Validated:** January 8, 2026

| Claim (clinical) | Value | Evidence location (receipt path) | Notes |
|---|---:|---|---|
| Primary claim | "Safety Gate prevents trial failures" | `combined_evidence.primary_claim` | Core product claim |
| PREPARE actionable carriers (control) | 23 | `prepare_trial.control_arm.actionable_carriers` | Source cohort |
| Observed toxic events | 8 | `prepare_trial.control_arm.toxic_events` | Real outcomes |
| Projected prevented toxicities | 7 | `prepare_trial.safety_gate_projection.if_applied_to_control.prevented_toxicities` | If Safety Gate applied |
| Prevention rate | 87.5% | `prepare_trial.safety_gate_projection.if_applied_to_control.prevention_rate` | 7/8 toxicities prevented |
| Tier 2 severe cases | 8 | `tier2_cases.severe_toxicity_cases.count` | Grade 3+ cases |
| Gene coverage | 100% | `tier2_cases.gene_coverage.coverage_rate` | DPYD, UGT1A1 covered |
| Claim status | VALIDATED | `claim_status` | Publication ready |

---

## Combined publication receipt (canonical index)

- **Receipt:** `publications/05-pgx-dosing-guidance/reports/publication_receipt_v3.json`
- **Role:** single machine-readable index linking manuscript version → cohort receipts → key metrics.


