# Conservative tumor-context gating for sporadic cancers: a provenance-first approach for precision oncology when tumor NGS is unavailable

**Authors:** [To be determined]

**Affiliations:** [To be determined]

**Corresponding Author:** [To be determined]

**Running Title:** Provenance-first sporadic gating without tumor NGS

**Keywords:** tumor context, sporadic cancer, confidence calibration, provenance, PARP, immunotherapy, TMB, MSI, HRD

**Abbreviations:**
- **NGS**: next-generation sequencing
- **TMB**: tumor mutational burden
- **MSI**: microsatellite instability
- **HRD**: homologous recombination deficiency
- **PARP**: poly(ADP-ribose) polymerase

---

## Abstract

**Background:** Most oncology patients are germline-negative (sporadic) and frequently lack immediately available tumor NGS at the time therapy options are discussed. In this setting, decision support systems can silently extrapolate from incomplete inputs and emit overconfident recommendations.

**Methods:** We implemented a conservative, provenance-first tumor-context layer consisting of (i) a structured TumorContext schema with explicit biomarker fields (TMB, MSI status, HRD score) and a completeness score mapped to three intake levels (L0/L1/L2); (ii) a Quick Intake pathway that creates TumorContext under partial information; and (iii) deterministic sporadic gates applied per drug to adjust efficacy and/or confidence. Gates include a PARP inhibitor penalty for germline-negative, HRD-low contexts with rescue for HRD-high tumors; an immunotherapy (checkpoint inhibitor) boost for strong tumor biomarkers; and confidence caps based on TumorContext completeness. Each adjustment emits structured provenance (`sporadic_gates_provenance`).

**Results:** Unit tests passed (8/8; receipt `receipts/pytest_sporadic_gates.txt`) and a standalone validation script passed (6/6; receipts `receipts/validate_sporadic_gates.txt` and `receipts/validate_sporadic_gates_report.json`). Quick Intake executed successfully for 15/15 cancer types (receipt `receipts/quick_intake_15cancers.json`). An end-to-end smoke test (Quick Intake → efficacy prediction) produced provenance-bearing drug outputs (receipts `receipts/e2e_tumor_context.json`, `receipts/e2e_efficacy_response.json`, `receipts/e2e_sporadic_workflow.txt`). In a 25-case scenario suite exercising threshold boundaries (`data/scenario_suite_25_*.json`), sporadic gates modified efficacy in 13/25 cases and confidence in 13/25 cases, matching a naive-rule implementation in 23/25 efficacy outcomes and 25/25 confidence outcomes (receipt `receipts/benchmark_gate_effects.json`).

**Conclusions:** A conservative tumor-context gating layer provides transparent, reproducible adjustments that reduce overconfidence under incomplete intake and clearly communicate which biomarkers drove changes. This design supports safe iteration toward full tumor NGS integration while remaining erational for the sporadic majority.

---

## Introduction

Precision oncology aims to align therapy selection with tumor biology using molecular biomarkers (e.g., HRD, MSI, TMB). In operational clinical reality, comprehensive tumor profiling is not always available at the moment when options are being discussed due to turnaround time, access barriers, reimbursement constraints, and clinical urgency.

At the same time, most patients are germline-negative for high-penetrance hereditary variants. This sporadic majority requires explicit tumor context because germline negativity does not imply absence of tumor phenotypes that drive therapy benefit (e.g., tumor HRD), and several therapy classes are commonly discussed using biomarker-associated reasoning patterns (PARP, checkpoint inhibitors).

This work treats missing tumor evidence as a first-class engineering and safety problem. We propose a conservative tumor-context gating layer that sits above an existing scoring pipeline and enforces three principles:

1. Represent tumor context explicitly via a schema that contains biomarker fields and an explicit measure of data completeness.
2. Apply deterministic biomarker-driven adjustments only when evidence is present, rather than inferring evidence when it is absent.
3. Cap confidence when inputs are incomplete, even if downstream components produce high scores.

Each adjustment emits structured provenance. This makes the system auditable, allows validation artifacts to serve as “receipts,” and enables UI surfaces to explain why a recommendation changed.

---

## Methods

### System overview

The sporadic cancer strategy is implemented as deterministic gates applied inside the efficacy orchestration layer. Inputs include germline status (positive/negative/unknown) and a TumorContext object. The orchestrator computes base per-drug efficacy and confidence, then applies sporadic gates per drug to adjust efficacy and/or confidence and attach `sporadic_gates_provenance`.

### TumorContext schema and intake levels

Tuontext represents biomarker evidence and evidence availability. Fields used by the sporadic gates include:

- `tmb` (float): tumor mutational burden (mut/Mb)
- `msi_status` (string): MSI status (e.g., MSI-High / MSS)
- `hrd_score` (float): HRD score (0–100)
- `completeness_score` (float): fraction of tracked fields populated (0–1)

Completeness is mapped to three intake levels:

- **L2**: completeness ≥ 0.7
- **L1**: 0.3 ≤ completeness < 0.7
- **L0**: completeness < 0.3

Completeness is treated as a proxy for evidence availability, not biology. It controls conservative confidence caps.

### Quick Intake

Quick Intake supports creating TumorContext when tumor NGS is not available. Optional biomarkers can be provided if known. If few fields are provided, the resulting completeness score is low and confidence caps apply downstream. Quick Intake validation across 15 cancer types is recorded in `receipts/quick_intake_15cancers.json`.

### Gating logic (PARP / IO / confidence)

Sporadic gates are implemen- `oncology-coPilot/oncology-backend-minimal/api/services/efficacy_orchestrator/sporadic_gates.py`

#### Gate 1: PARP inhibitor penalty with HRD rescue

This gate applies to PARP-class drugs:

- germline positive → multiplier = 1.0
- germline negative:
  - HRD known and HRD ≥ 42 → multiplier = 1.0 (rescue)
  - HRD known and HRD < 42 → multiplier = 0.6
  - HRD unknown → multiplier = 0.8
- germline unknown → multiplier = 0.8

Efficacy is updated multiplicatively and clamped to [0,1].

#### Gate 2: immunotherapy boost (checkpoint inhibitors)

This gate applies to checkpoint inhibitors. Boost is mutually exclusive with precedence:

- TMB ≥ 20 → boost = 1.35
- else MSI-High → boost = 1.30
- else TMB ≥ 10 → boost = 1.25
- else boost = 1.0

Efficacy is updated multiplicatively and clamped to [0,1].

#### Gate 3: confidence caps by completeness

Confidence is capped by completeness tier:

- L0: confidence_out = min(confidence_in, 0.4)
- L1: confidence_out = min(confidence_in, 0.6)
- L2: uncappen gates apply, the orchestrator attaches `sporadic_gates_provenance` per drug capturing: germline status, inferred level, gates applied, and rationale entries including thresholds and deltas. Example output is in `receipts/e2e_efficacy_response.json`.

### Validation package

This manuscript’s claims are backed by executable receipts:

- Unit tests: `receipts/pytest_sporadic_gates.txt`
- Standalone validator: `receipts/validate_sporadic_gates.txt`, `receipts/validate_sporadic_gates_report.json`
- E2E smoke test: `receipts/e2e_sporadic_workflow.txt` + structured JSON (`receipts/e2e_tumor_context.json`, `receipts/e2e_efficacy_response.json`)
- Scenario suite + benchmark: `data/scenario_suite_25_*.json`, `receipts/benchmark_gate_effects.json`

---

## Results

### Deterministic correctness receipts

All deterministic gate behaviors and precedence rules are validated by unit tests and the standalone validator (see receipts above).

### End-to-end workflow receipts

Quick Intake → efficacy prediction producrovenance-bearing per-drug outputs in the E2E smoke receipts.

### Scenario-suite benchmark

Across a 25-case scenario suite spanning threshold boundaries, gates modified efficacy in 13/25 cases and confidence in 13/25 cases. System outputs matched a naive-rule implementation in 23/25 efficacy outcomes and 25/25 confidence outcomes (receipt `receipts/benchmark_gate_effects.json`).

### Figures

- **Figure 1. Architecture schematic** (`figures/figure_1_architecture.png`)
- **Figure 2. PARP gate effects** (`figures/figure_2_parp_gates.png`)
- **Figure 3. Confidence caps** (`figures/figure_3_confidence_caps.png`)

---

## Discussion

We present a conservative tumor-context gating layer designed to reduce overconfidence and improve auditability when tumor NGS is unavailable at decision time. The contribution is operational and safety-oriented: deterministic gates, explicit completeness, and structured provenance.

### Limitations

- This package validates *behavioral correctness* of gates and provenance, not clinical outcome benefit.
- HRD thresholds and IO biomarker thresholds are implemented as deterministic policies and should be evaluated on cohort-appropriate outcome-labeled data when making outcome claims.
- Quick Intake does not infer MSI/TMB without provided inputs; missing biomarkers are handled via completeness and confidence caps.

### Future work

- Integrate validated tumor NGS parsers (e.g., Foundation/Tempus) to populate L2 contexts.
- Expand cohort-appropriate outcome benchmarking for biomarkers where prevalence supports statistical analysis.
- Extend provenance UI surfaces across therapy recommendation experiences.

---

## Data Availability

All validation artifacts for this manuscript are included in this repository folder under `submission_aacr/` (receipts, figures, scenario suite). No patient-level identifying data are included. External clinical datasets (when used elsewhere in the platform) are referenced via their original sources.

## Code Availability

The deterministic gates live in the backend repository at:
- `oncology-coPilot/oncology-backend-minimal/api/services/efficacy_orchestrator/sporadic_gates.py`

Validation receipts were generated by running the validation scripts referenced in `SUPPLEMENT.md`.

---

## Author Contributions

[To be determined]

## Competing Interests

[To be determined]

---

## References

1. Farmer H, et al. Targeting the DNA repair defect in BRCA mutant cells as a therapeutic strategy. *Nature*. 2005;434:917–921.
2. Bryant HE, et al. Specific killing of BRCA2-deficient tumours with inhibitors of poly(ADP-ribose) polymerase. *Nature*. 2005;434:913–917.
3. Le DT, et al. PD-1 blockade in tumors with mismatch-repair deficiency. *N Engl J Med*. 2015;372:2509–2520.
