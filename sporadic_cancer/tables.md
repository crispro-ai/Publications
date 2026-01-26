# Tables (Sporadic Cancer Strategy)

## Table 1. TumorContext fields used by sporadic gates

| Field | Type | Validation | Use in system | Example |
| --- | --- | --- | --- | --- |
| completeness_score | float | [0,1] | Data completeness fraction; used to assign L0/L1/L2 | 0.2 / 0.5 / 0.9 |
| tmb | float | ≥0 | Tumor mutational burden (mut/Mb); IO boosts | 25.0 |
| msi_status | str | {MSI-H, MSI-High, MSS, indeterminate, ...} | MSI status; IO boost when MSI-high | MSI-High |
| hrd_score | float | [0,100] | HRD score (GIS); PARP HRD rescue threshold 42 | 58.0 |
| somatic_mutations | list[str] | gene symbols | Optional; not required for gating | [TP53, BRCA1] |

## Table 2. Gate definitions (inputs, thresholds, effects)

| Gate | Inputs | Thresholds / decision | Effect | Provenance key(s) |
| --- | --- | --- | --- | --- |
| PARP germline/HRD gate | germline_status, hrd_score | germline+ → 1.0x; germline− & HRD≥42 → 1.0x; germline− & HRD<42 → 0.6x; unknown → 0.8x | Reduce PARP confidence in germline− HRD-low; rescue when HRD-high | PARP_HRD_LOW / PARP_HRD_RESCUE / PARP_UNKNOWN_* |
| IO boost gate (checkpoint drugs) | tmb, msi_status | if TMB≥20 → 1.35x; elif MSI-high → 1.30x; elif TMB≥10 ritize IO therapies when strong tumor biomarkers present | IO_TMB_BOOST / IO_MSI_BOOST |
| Confidence caps | completeness_score | L0 (<0.3) cap 0.4; L1 (0.3–<0.7) cap 0.6; L2 (≥0.7) no cap | Prevent overconfident outputs when intake is incomplete | CONFIDENCE_CAP_L0 / CONFIDENCE_CAP_L1 |

## Table 3. Test and scenario summary

| Artifact | What ran | Result | Receipt |
| --- | --- | --- | --- |
| Unit tests | pytest test_sporadic_gates.py | PASS | publications/sporadic_cancer/receipts/pytest_sporadic_gates.txt |
| Scenario suite | 25 synthetic cases through apply_sporadic_gates | 25 cases | data/scenario_suite_25_20251231_080940.json |
| Gate activations | PARP penalty/rescue | _reduced=6 | Scenario suite JSON |
| Gate activations | IO boost | io_boosted=7 | Scenario suite JSON |
| Gate activations | Confidence caps | conf_capped=5 | Scenario suite JSON |

## Table 4. Clinical validation (TCGA-UCEC overall survival)

| Biomarker Strategy | N | Positive | Negative | Log-rank p | Cox HR (Pos vs Neg) | 95% CI |
|---|---:|---:|---:|---:|---:|---|
| TMB-high (≥20 mut/Mb) | 516 | 120 | 396 | 0.001045 | 0.316 | 0.152–0.654 |
| MSI-high | 527 | 174 | 353 | 0.00732 | 0.491 | 0.289–0.835 |
| OR gate (TMB-high or MSI-high) | 527 | 210 | 317 | 0.000168 | 0.389 | 0.234–0.648 |

**Receipts:** `receipts/clinical/baseline_comparison_io_tcga_ucec.json`

## Table 5. Negative control (TCGA-COADREAD overall survival)

| Biomarker Strategy | N | Log-rank p | Cox HR (Pos vs Neg) | 95% CI |
|---|---:|---:|---:|---|
| TMB-high (≥20 mut/Mb) | 530 | 0.931 | 1.02 | 0.610–1.72 |
| MSI-high | 588 | 0.756 | 0.927 | 0.573–1.50 |
| OR gate (TMB-high or MSI-high) | 590 | 0.623 | 0.888 | 0.555–1.42 |

**Receipts:** `receipts/clinical/baseline_comparison_io_tcga_coadread.json`

## Table 6. Real-cohort safety audit (TCGA-OV)

| Metric | Value | N | Receipt |
|---|---:|---:|---|
| PARP penalty applied | 460 | 469 | `receipts/clinical/real_cohort_behavioral_validation.json` |
| Confidence cap (L1) applied | 469 | 469 | `receipts/clinical/real_cohort_behavioral_validation.json` |

## Table 7. Comparison to standard clinical workflow

| Scenario | Standard Practice | This System | Difference |
| --- | --- | --- | --- |
| Germline-negative HRD unknown | Vague recommendation, often no PARP inhibitor | PARP efficacy reduced (0.8x), confidence capped (L0/L1), provenance recorded | Quantified uncertainty, explicit rationale, auditable |
| MSI-high IHC only | Immunotherapy recommended, no explicit confidence | IO efficacy boosted (1.3x), confidence capped (L0/L1), provenance recorded | Calibrated confidence, receipt-backed, actionable feedback |
| No biomarker data | Broad recommendations, high uncertainty | Efficacy defaults, confidence capped (L0), provenance recorded | Safety-first, prevents overconfidence, transparent |

## Table 8. Real Patient Examples: Tiered System Behavior

| Patient ID | Mutations | HRD Proxy | Platinum Response | Level | TumorContext | Efficacy Change | Confidence Cap | Gates Applied | Clinical Interpretation |
|---|---|---|---|---|---|---|---|---|---|
| TCGA-23-2078 | 187 | 30.0 | Sensitive | L0 | `{"completeness_score": 0.2}` | -0.14 | L0 | PARP_UNKNOWN_HRD, CONFIDENCE_CAP_L0 | Conservative PARP penalty due to unknown HRD, capped confidence. |
| | | | | L1 | `{"completeness_score": 0.5, "hrd_score": 30.0, "tmb": 5.0, "msi_status": "MSI-Stable"}` | -0.28 | L1 | PARP_HRD_LOW, CONFIDENCE_CAP_L1 | HRD known but low, PARP penalty applied, confidence capped. |
| | | | | L2 | `{"completeness_score": 0.9, "hrd_score": 30.0, "tmb": 25.0, "msi_status": "MSI-Stable"}` | -0.28 | None | PARP_HRD_LOW | Full data, HRD low, PARP penalty applied, no confidence cap. |
| TCGA-13-1482 | 56 | 30.0 | Sensitive | L0 | `{"completeness_score": 0.2}` | -0.14 | L0 | PARP_UNKNOWN_HRD, CONFIDENCE_CAP_L0 | Similar to TCGA-23-2078 at L0, conservative. |
| | | | | L1 | `{"completeness_score": 0.5, "hrd_score": 30.0, "tmb": 5.0, "msi_status": "MSI-Stable"}` | -0.28 | L1 | PARP_HRD_LOW, CONFIDENCE_CAP_L1 | HRD known but low, PARP penalty, confidence capped. |
| | | | | L2 | `{"completeness_score": 0.9, "hrd_score": 30.0, "tmb": 25.0, "msi_status": "MSI-Stable"}` | -0.28 | None | PARP_HRD_LOW | Full data, HRD low, PARP penalty, no confidence cap. |
| TCGA-09-1661 | 0 | 0.0 | Resistant | L0 | `{"completeness_score": 0.2}` | -0.14 | L0 | PARP_UNKNOWN_HRD, CONFIDENCE_CAP_L0 | Conservative PARP penalty due to unknown HRD, capped confidence. |
| | | | | L1 | `{"completeness_score": 0.5, "hrd_score": 0.0, "tmb": 5.0, "msi_status": "MSI-Stable"}` | -0.14 | L1 | PARP_HRD_LOW, CONFIDENCE_CAP_L1 | HRD known and very low, PARP penalty, confidence capped. |
| | | | | L2 | `{"completeness_score": 0.9, "hrd_score": 0.0, "tmb": 25.0, "msi_status": "MSI-Stable"}` | -0.14 | None | PARP_HRD_LOW | Full data, HRD very low, PARP penalty, no confidence cap. |

Receipt: `receipts/clinical/tcga_ov_l0_l1_l2_examples.json`
