# Conservative tumor-context gating for sporadic cancers: a provenance-first approach for precision oncology without tumor NGS

## Abstract

**Background:** Most oncology patients are germline-negative (sporadic) and frequently lack immediately available tumor NGS at the time therapy options are discussed. In this setting, decision support systems can silently extrapolate from incomplete inputs and emit overconfident recommendations.

**Methods:** We implemented a conservative, provenance-first tumor-context layer consisting of (i) a structured `TumorContext` schema with explicit biomarker fields (TMB, MSI status, HRD score) and a completeness score mapped to three intake levels (L0/L1/L2); (ii) a Quick Intake pathway that creates `TumorContext` under partial information; and (iii) deterministic sporadic gates applied per drug to adjust efficacy and/or confidence. Gates include a PARP inhibitor penalty for germline-negative, HRD-low contexts with rescue for HRD-high tumors; an immunotherapy (checkpoint inhibitor) boost for strong tumor biomarkers; and confidence caps based on `TumorContext` completeness. Each adjustment emits structured provenance (`sporadic_gates_provenance`).

**Results (non-outcome validation):** We validate behavioral correctness and reproducibility, not clinical outcomes. A 25-case scenario suite exercising threshold boundaries (`data/scenario_suite_25_20251231_080940.json`) shows sporadic gates modified efficacy in **13/25** cases and confidence in **13/25** cases, with conformance to a naive reference implementation in **23/25** efficacy outcomes and **25/25** confidence outcomes (receipt `receipts/benchmark_gate_effects.json`). Quick Intake executed successfully for **15/15** cancer types (receipt `receipts/quick_intake_15cancers.json`). An end-to-end smoke test (Quick Intake → efficacy prediction) produced provenance-bearing drug outputs (receipts `receipts/e2e_tumor_context.json`, `receipts/e2e_efficacy_response.json`, `receipts/e2e_sporadic_workflow.txt`).

**Conclusions:** A conservative tumor-context gating layer provides transparent, reproducible adjustments that reduce overconfidence under incomplete intake and clearly communicate which biomarkers drove changes. This design supports safe iteration toward full tumor NGS integration while remaining operational for the sporadic majority.

---

## 1. Scope and claims

This manuscript is provenance-first and receipt-backed.

**Validated here (non-outcome):**
- Deterministic gate behavior (penalty/boost/caps) under controlled inputs.
- Conformance to a reference implementation over a scenario suite.
- Reproducible execution producing stable receipts.

**Explicitly not validated here:**
- Clinical outcomes, enrollment lift, or patient benefit.
- Comparative performance vs human trial navigators.
- Retrospective enrollment-ground-truth evaluation (not available in this bundle).

---

## 2. Methods

### 2.1 TumorContext schema and intake levels
`TumorContext` captures tumor biomarkers as explicit fields (e.g., TMB, MSI status, HRD score) and computes a completeness score mapped to three intake levels:
- **L0:** minimal / mostly priors
- **L1:** partial biomarker availability
- **L2:** near-complete tumor context

This allows the system to gate confidence based on what is actually known rather than implicitly assuming missing values.

### 2.2 Deterministic sporadic gates
Sporadic gates deterministically adjust per-drug outputs based on germline status and tumor biomarkers:
- **PARP penalty + HRD rescue:** penalize PARP under germline-negative + HRD-low; rescue when HRD-high.
- **Checkpoint boost:** boost IO confidence/efficacy under strong IO biomarkers (TMB/MSI).
- **Confidence caps:** cap confidence under incomplete `TumorContext` (L0/L1).

Each application emits `sporadic_gates_provenance`, including inputs used, thresholds, and the applied adjustment.

### 2.3 Scenario suite and reference implementation
We evaluate a scenario suite designed to stress threshold boundaries (e.g., HRD near rescue threshold, TMB near IO threshold, and varying completeness levels). A naive reference implementation encodes the same policy rules; conformance testing ensures observed adjustments match expected rule application.

---

## 3. Results (receipt-backed)

### 3.1 Scenario-suite behavior and conformance
On the 25-case scenario suite:
- Gate-modified efficacy: **13/25**
- Gate-modified confidence: **13/25**
- Conformance vs naive reference:
  - **23/25** efficacy outcomes
  - **25/25** confidence outcomes

**Receipts:**
- Scenario suite input: `data/scenario_suite_25_20251231_080940.json`
- Benchmark receipt: `receipts/benchmark_gate_effects.json`

### 3.2 Quick Intake coverage
Quick Intake produced valid `TumorContext` objects for **15/15** cancer types tested.

**Receipt:** `receipts/quick_intake_15cancers.json`

### 3.3 End-to-end smoke test with provenance
A smoke test exercising Quick Intake → efficacy prediction produced:
- A populated `TumorContext` object
- An efficacy response whose drugs include explicit sporadic provenance fields

**Receipts:**
- `receipts/e2e_tumor_context.json`
- `receipts/e2e_efficacy_response.json`
- `receipts/e2e_sporadic_workflow.txt`

---

## 4. Figures

- Figure 1: `figures/figure_1_architecture.png`
- Figure 2: `figures/figure_2_parp_gates.png`
- Figure 3: `figures/figure_3_confidence_caps.png`

---

## 5. Reproducibility

From the repo root:

```bash
python3 publications/sporadic_cancer/make_figures.py
python3 publications/sporadic_cancer/make_manuscript.py
```

Primary receipts referenced here:
- `receipts/pytest_sporadic_gates.txt`
- `receipts/validate_sporadic_gates.txt`
- `receipts/validate_sporadic_gates_report.json`
- `receipts/quick_intake_15cancers.json`
- `receipts/e2e_tumor_context.json`
- `receipts/e2e_efficacy_response.json`
- `receipts/e2e_sporadic_workflow.txt`
- `receipts/benchmark_gate_effects.json`

---

## 6.imitations and next steps

- No outcomes are evaluated in this bundle; future work requires prospective logging or retrospective enrollment mapping.
- Thresholds and caps are policy levers; the scenario suite should expand as policy evolves.
- Quick Intake is an operational bridge; full tumor NGS ingestion is required for robust L2 completeness in real workflows.
