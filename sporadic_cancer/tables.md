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

## Table 4. Clinical Validation Summary (TCGA-UCEC, n=527)

| Strategy | Usable N | Hazard Ratio (Cox) | 95% Confidence Interval | log-rank p-value | Receipt |
| --- | --- | --- | --- | --- | --- |
| TMB-only (≥20 mut/Mb) | 516 | 0.32 | 0.15 - 0.65 | 0.00105 | `baseline_comparison_io_tcga_ucec.json` |
| MSI-only (MSI-H) | 527 | 0.49 | 0.29 - 0.83 | 0.00732 | `baseline_comparison_io_tcga_ucec.json` |
| OR-gate (TMB or MSI) | 527 | 0.39 | 0.23 - 0.65 | 0.00017 | `baseline_comparison_io_tcga_ucec.json` |
