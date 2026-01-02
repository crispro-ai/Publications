# Conservative tumor-context gating for sporadic cancers: a provenance-first approach for precision oncology without tumor NGS

## Abstract

**Background:** Most oncology patients are germline-negative (sporadic) and frequently lack immediately available tumor NGS at the time therapy options are discussed. In this setting, decision support systems can silently extrapolate from incomplete inputs and emit overconfident recommendations.

**Methods:** We implemented a conservative, provenance-first tumor-context layer consisting of (i) a structured TumorContext schema with explicit biomarker fields (TMB, MSI status, HRD score) and a completeness score mapped to three intake levels (L0/L1/L2); (ii) a Quick Intake pathway that creates TumorContext under partial information; and (iii) deterministic sporadic gates applied per drug to adjust efficacy and/or confidence. Gates include a PARP inhibitor penalty for germline-negative, HRD-low contexts with rescue for HRD-high tumors; an immunotherapy (checkpoint inhibitor) boost for strong tumor biomarkers; and confidence caps based on TumorContext completeness. Each adjustment emits structured provenance (`sporadic_gates_provenance`).

**Results:** Unit tests passed (8/8; receipt `receipts/pytest_sporadic_gates.txt`) and a standalone validation script passed (6/6; receipts `receipts/validate_sporadic_gates.txt` and `receipts/validate_sporadic_gates_report.json`). Quick Intake executed successfully for 15/15 cancer types (receipt `receipts/quick_intake_15cancers.json`). An end-to-end smoke test (Quick Intake -> efficacy prediction) produced provenance-bearing drug outputs (receipts `receipts/e2e_tumor_context.json`, `receipts/e2e_efficacy_response.json`, `receipts/e2e_sporadic_workflow.txt`).

On a 25-case scenario suite exercising thresholds (`/Users/fahadkiani/Desktop/development/crispr-assistant-main/publications/sporadic_cancer/data/scenario_suite_25_20251231_080940.json`), sporadic gates modified efficacy in **13/25** cases and confidence in **13/25** cases. System outputs matched a naive-rule implementation in **23/25** efficacy outcomes and **25/25** confidence outcomes (receipt `receipts/benchmark_gate_effects.json`).

**Conclusions:** A conservative tumor-context gating layer provides transparent, reproducible adjustments that reduce overconfidence under incomplete intake and clearly communicate which biomarkers drove changes. This design supports safe iteration toward full tumor NGS integration while remaining operational for the sporadic majority.

## Results (receipts + figures)

### Receipts

- Scenario suite: `/Users/fahadkiani/Desktop/development/crispr-assistant-main/publications/sporadic_cancer/data/scenario_suite_25_20251231_080940.json`
- Benchmark receipt: `/Users/fahadkiani/Desktop/development/crispr-assistant-main/publications/sporadic_cancer/receipts/benchmark_gate_effects.json`
- Unit tests: `receipts/pytest_sporadic_gates.txt`
- Validator receipts: `receipts/validate_sporadic_gates.txt`, `receipts/validate_sporadic_gates_report.json`
- E2E receipts: `receipts/e2e_tumor_context.json`, `receipts/e2e_efficacy_response.json`, `receipts/e2e_sporadic_workflow.txt`

### Figures

- Figure 1: `figures/figure_1_architecture.png`
- Figure 2: `figures/figure_2_parp_gates.png`
- Figure 3: `figures/figure_3_confidence_caps.png`
