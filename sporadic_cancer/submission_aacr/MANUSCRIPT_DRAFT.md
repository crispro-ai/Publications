# Scalable precision oncology via conservative biomarker gating: biomarker and gate-behavior validation under incomplete tumor sequencing                         

**Authors:** Sabreen Abeed Allah, Fahad Kiani

**Affiliations:** Palestinian Medical Relief Society, Ramallah, Palestine; John Jay College, USA

**Corresponding Author:** Sabreen Abeed Allah, sabreen.abeedallah00@gmail.com, P.O. Box 572, Ramallah, Palestine, 00972-598041485

**Running Title:** Conservative biomarker gating for precision oncology

**Conflict of Interest Statement:** The authors declare no potential conflicts of interest.

**Keywords:** precision oncology, biomarker gating, tumor mutational burden, microsatellite instability, confidence calibration, provenance, PARP inhibitors, immunotherapy

**Abbreviations:**
- **NGS**: next-generation sequencing
- **TMB**: tumor mutational burden
- **MSI**: microsatellite instability
- **HRD**: homologous recombination deficiency
- **PARP**: poly(ADP-ribose) polymerase
- **OS**: overall survival
- **HR**: hazard ratio
- **CI**: confidence interval

---

## Abstract

**Background:** Current precision oncology systems either delay treatment pending complete tumor sequencing or make recommendations without quantifying uncertainty when biomarker data is incomplete. Commercial genomic profiling platforms (Foundation Medicine, Tempus) and clinical decision support systems (IBM Watson Oncology) provide biomarker-based recommendations but do not calibrate confidence based on data completeness or provide structured provenance for biomarker-driven adjustments.

**Methods:** We implemented a conservative, provenance-first tumor-context layer with explicit data completeness modeling (L0/L1/L2), deterministic biomarker gates (PARP penalty + HRD rescue; checkpoint boost under TMB/MSI), and confidence caps when evidence is incomplete. To our knowledge, this is the first system to calibrate confidence based on data completeness and provide structured provenance for biomarker-driven adjustments at scale. We evaluated biomarker prognostic associations in TCGA-UCEC overall survival and audited real-cohort gate behavior in TCGA-OV; TCGA-COADREAD is used for contextualization as a pre-immunotherapy-era cohort.

**Results:** In TCGA-UCEC, TMB-high (≥20 mut/Mb) and MSI-high were associated with improved overall survival (TMB-high n=120/516: HR=0.32, p=0.00105; MSI-high n=174/527: HR=0.49, p=0.00732), and the OR gate showed the strongest signal (OR-positive n=210/527: HR=0.39, p=0.000168). In TCGA-OV (n=469), gate auditing showed conservative behavior under incomplete intake (PARP penalty: **460/469**; confidence cap (L1): **469/469**).

**Conclusions:** This study validates biomarker prognostic signal and deterministic gate behavior under incomplete tumor sequencing, while explicitly not claiming treatment benefit or clinical decision impact.                                       

---

## Introduction

Precision oncology aims to align therapy selection with tumor biology using molecular biomarkers (e.g., HRD, MSI, TMB). In operational clinical reality, comprehensive tumor profiling is not always available at the moment when options are being discussed due to turnaround time, access barriers, reimbursement constraints, and clinical urgency.

At the same time, most patients are germline-negative for high-penetrance hereditary variants. This sporadic majority requires explicit tumor context because germline negativity does not imply absence of tumor phenotypes that drive therapy benefit (e.g., tumor HRD), and several therapy classes are commonly discussed using biomarker-associated reasoning patterns (PARP, checkpoint inhibitors).

Existing precision oncology platforms (Foundation Medicine, Tempus, IBM Watson Oncology) provide biomarker-based recommendations but do not quantify confidence based on data completeness or provide structured audit trails for biomarker-driven adjustments. To our knowledge, this is the first system to implement completeness-aware confidence calibration and provenance-backed gating at scale.

This work treats missing tumor evidence as a first-class engineering and safety problem. We propose a conservative tumor-context gating layer that sits above an existing scoring pipeline and enforces three principles:

1. Represent tumor context explicitly via a schema that contains biomarker fields and an explicit measure of data completeness.
2. Apply deterministic biomarker-driven adjustments only when evidence is present, rather than inferring evidence when it is absent.
3. Cap confidence when inputs are incomplete, even if downstream components produce high scores.

Each adjustment emits structured provenance. This makes the system auditable, allows validation artifacts to serve as "receipts," and enables UI surfaces to explain why a recommendation changed.

### Data availability and uncertainty

In operational settings, tumor-context information (e.g., HRD/TMB/MSI) may be incomplete or pending at the time decisions are discussed. This work focuses on representing evidence availability explicitly (L0/L1/L2 completeness) and quantifying uncertainty through confidence caps and provenance-bearing deterministic gates.

---

## Methods

### System overview

The sporadic cancer strategy is implemented as deterministic gates applied inside the efficacy orchestration layer. Inputs include germline status (positive/negative/unknown) and a TumorContext object. The orchestrator computes base per-drug efficacy and confidence, then applies sporadic gates per drug to adjust efficacy and/or confidence and attach `sporadic_gates_provenance`.

### TumorContext schema and intake levels

TumorContext represents biomarker evidence and evidence availability. Fields used by the sporadic gates include:

- `tmb` (float): tumor mutational burden (mut/Mb)
- `msi_status` (string): MSI status (e.g., MSI-High / MSS)
- `hrd_score` (float): HRD score (0–100)
- `completeness_score` (float): fraction of tracked fields populated (0–1)

For this manuscript, `completeness_score` is computed as the mean of three equal-weight indicators for whether `tmb`, `msi_status`, and `hrd_score` are present (non-null).

Completeness is mapped to three intake levels:

- **L2**: completeness ≥ 0.7
- **L1**: 0.3 ≤ completeness < 0.7
- **L0**: completeness < 0.3

Completeness is treated as a proxy for evidence availability, not biology. It controls conservative confidence caps.

### Quick Intake

Quick Intake supports creating TumorContext when tumor NGS is not available. Optional biomarkers can be provided if known. If few fields are provided, the resulting completeness score is low and confidence caps apply downstream. Quick Intake validation across 15 cancer types is recorded in `receipts/quick_intake_15cancers.json`.

### Gating logic (PARP / IO / confidence)

Sporadic gates are implemented in `oncology-coPilot/oncology-backend-minimal/api/services/efficacy_orchestrator/sporadic_gates.py`.

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

**Gate multiplier rationale (engineering stance):** The multipliers are **heuristic, bounded policy weights** intended to encode evidence-strength categories without dominating the underlying efficacy scorer. They are not calibrated to treatment response rates in this manuscript and should be tuned on outcome-labeled cohorts or prospective logs when making clinical impact claims.

#### Gate 3: confidence caps by completeness

Confidence is capped by completeness tier:

- L0: confidence_out = min(confidence_in, 0.4)
- L1: confidence_out = min(confidence_in, 0.6)
- L2: uncapped

When gates apply, the orchestrator attaches `sporadic_gates_provenance` per drug capturing: germline status, inferred level, gates applied, and rationale entries including thresholds and deltas. Example output is in `receipts/e2e_efficacy_response.json`.

### Clinical outcome validation (TCGA-UCEC)

We evaluated overall survival (OS) using Kaplan–Meier curves, log-rank tests, and Cox proportional hazards regression. Stratifications:
- TMB-high: TMB ≥ 20 mut/Mb
- MSI-high: MSI status indicates MSI-high
- OR gate: TMB-high OR MSI-high

Negative control: applied identical stratifications to TCGA-COADREAD to assess tumor-type specificity.

### Gate behavior validation (TCGA-OV)

We validated gate behavior (rather than treatment concordance) via:

- **Threshold sensitivity**: IO boost trigger rates under TMB thresholds \(\{10,15,20,25\}\) and PARP rescue/penalty trigger rates under HRD thresholds \(\{30,35,40,42,45,50\}\) (`results/threshold_sensitivity.csv`).
- **Subgroup consistency**: trigger rates stratified by ovarian tumor stage (III vs IV) and a platinum-status proxy from cBioPortal exports (`results/subgroup_consistency.csv`).
- **Biological coherence**: Spearman correlation structure among biomarkers and triggers (MSI↔TMB, BRCA↔HRD, and triggers↔biomarkers) (`figures/biological_coherence.png`, `results/biological_coherence_stats.csv`).

### Validation package

This manuscript's claims are backed by executable receipts:

- Unit tests: `receipts/pytest_sporadic_gates.txt`
- Standalone validator: `receipts/validate_sporadic_gates.txt`, `receipts/validate_sporadic_gates_report.json`
- E2E smoke test: `receipts/e2e_sporadic_workflow.txt` + structured JSON (`receipts/e2e_tumor_context.json`, `receipts/e2e_efficacy_response.json`)
- Scenario suite + benchmark: `data/scenario_suite_25_*.json`, `receipts/benchmark_gate_effects.json`
- Clinical validation: `receipts/clinical/baseline_comparison_io_tcga_ucec.json`, `receipts/clinical/baseline_comparison_io_tcga_coadread.json`
- Real-cohort safety audit: `receipts/clinical/real_cohort_behavioral_validation.json`

Complete validation receipts, including unit test outputs, scenario suite results, and API examples, are provided in the Supplement (Sections A–E).

---

## Results

### Clinical outcome validation (TCGA-UCEC)

In the TCGA-UCEC cohort (n=527), TMB-high (≥20 mut/Mb) was significantly associated with superior overall survival (HR = 0.32, 95% CI 0.15–0.65, log-rank p = 0.00105, n=516). Similarly, MSI-high status predicted improved OS (HR = 0.49, 95% CI 0.29–0.83, log-rank p = 0.00732, n=527). A combined "OR" gate (TMB-high or MSI-high) provided the strongest prognostic signal (HR = 0.39, 95% CI 0.23–0.65, log-rank p = 0.000168, n=527).

**Figures:** See Figures 4–6 (Kaplan–Meier curves and combined biomarker comparison). Full numeric outputs are provided in the Supplement.

### Negative control (TCGA-COADREAD)

To contextualize tumor-type transferability under retrospective prognosis-only analysis, we applied the same stratification to TCGA-COADREAD (n=590). No significant OS difference was found for TMB-high (HR = 1.02, 95% CI 0.61–1.72, p = 0.931) or MSI-high (HR = 0.93, 95% CI 0.57–1.50, p = 0.756). Because TCGA-COADREAD largely predates widespread checkpoint inhibitor use and treatment exposure is not represented in TCGA, this result should not be interpreted as absence of checkpoint inhibitor benefit; rather, it illustrates a limitation of using OS in historical cohorts to validate IO treatment effects.

### Safety and reproducibility validation

#### Deterministic correctness receipts

All deterministic gate behaviors and precedence rules are validated by unit tests and the standalone validator (see receipts above).

#### End-to-end workflow receipts

Quick Intake → efficacy prediction produced provenance-bearing per-drug outputs in the E2E smoke receipts.

#### Scenario-suite benchmark

Across a 25-case scenario suite spanning threshold boundaries, gates modified efficacy in 13/25 cases and confidence in 13/25 cases. System outputs matched a naive-rule implementation in 23/25 efficacy outcomes and 25/25 confidence outcomes (receipt `receipts/benchmark_gate_effects.json`).

#### Real-cohort safety audit (TCGA-OV)

To evaluate real-world impact, we applied sporadic gates to mutation profiles from 469 TCGA-OV patients. The system applied a PARP penalty to **460/469** (98.1%) of patients, reflecting a conservative stance when explicit high-DDR/HRD markers are absent in the clinical record. Confidence caps (L1) were applied to **469/469** (100%) of cases, demonstrating that the system actively suppresses overconfidence in real-world clinical settings where NGS is often pending or partial.

**Receipt:** `receipts/clinical/real_cohort_behavioral_validation.json` (Supplement Section D.3)

#### Tier 2 gate behavior validation artifacts (TCGA-OV)

Threshold sensitivity and subgroup consistency artifacts are provided in `results/threshold_sensitivity.csv` and `results/subgroup_consistency.csv`. Biological coherence is summarized in `figures/biological_coherence.png` with numeric correlations in `results/biological_coherence_stats.csv`.

### Tier 2: Gate behavior validation (TCGA-OV)

Across the merged TCGA-OV cohort used for Tier-2 analyses (n=491), the IO boost trigger rate was stable across the evaluated TMB thresholds (10–25 mut/Mb), yielding an IO boost rate of **3.26%** at TMB ≥ 20 (defined as TMB-high OR MSI-high). HRD threshold sensitivity showed substantial expected variation: PARP rescue rates were **73.3%** at HRD ≥ 30, **51.9%** at HRD ≥ 42, and **41.1%** at HRD ≥ 50 (`results/threshold_sensitivity.csv`).

Subgroup consistency analysis showed similar behavior across stage strata (Stage III PARP rescue **50.7%**, n=381; Stage IV PARP rescue **55.7%**, n=79). Stratification by a platinum-status proxy showed coherent differences (platinum-sensitive rescue **61.4%**, n=197; platinum-resistant rescue **38.9%**, n=90), consistent with HRD enrichment among platinum-sensitive cases (`results/subgroup_consistency.csv`).

Biological coherence analysis confirmed that trigger variables behave deterministically relative to biomarker inputs (e.g., HRD vs PARP rescue \(\rho\)=**0.86**; MSI-high vs IO boost \(\rho\)=**0.97**). We also observed a modest positive association between BRCA alterations and HRD (\(\rho\)=**0.27**). This modest correlation is consistent with two factors: (i) HRD scores capture multiple DDR deficiency mechanisms beyond BRCA1/2, and (ii) “BRCA alteration” in mutation-derived calls can include heterogeneous variant classes. Nonetheless, BRCA-mutant cases were enriched for HRD-high status: **59/68 (86.8%)** BRCA-mutant patients with non-null HRD had HRD ≥ 42, compared to **196/405 (48.4%)** in non-BRCA patients (TCGA-OV merged table).

### Real patient examples: Tiered system behavior

To illustrate how the system behaves across data completeness levels, we applied sporadic gates to three real TCGA-OV patients at L0, L1, and L2 intake levels (Table 7).

**Patient 1: TCGA-23-2078** (187 mutations, platinum-sensitive)
- **Profile**: TP53 mutation detected (HRD proxy: 30.0)
- **L0 behavior** (completeness=0.2, disease priors only): Conservative PARP penalty (0.8×) reduced efficacy from 0.70 to 0.56; confidence capped at 0.40 (L0 cap)
- **L1 behavior** (completeness=0.5, HRD proxy available): PARP penalty (0.6×) applied due to HRD <42, reducing efficacy to 0.42; confidence capped at 0.60 (L1 cap)
- **L2 behavior** (completeness=0.9, full NGS): Same PARP penalty (0.6×) maintained; confidence uncapped at 0.65

**Patient 2: TCGA-13-1482** (56 mutations, platinum-sensitive)
- **Profile**: TP53 mutation detected (HRD proxy: 30.0)
- **Behavior**: Identical pattern to Patient 1 across all three levels, demonstrating consistent gate application when biomarker profiles are similar

**Patient 3: TCGA-09-1661** (0 mutations, platinum-resistant)
- **Profile**: No DDR genes detected (HRD proxy: 0.0)
- **Behavior**: Same tiered pattern (L0: 0.8× penalty + 0.4 cap; L1: 0.6× penalty + 0.6 cap; L2: 0.6× penalty, no cap), demonstrating that the system applies conservative defaults even when mutation burden is low

**Clinical interpretation**: These examples demonstrate that the system provides actionable guidance at all data completeness levels while maintaining safety through conservative penalties and confidence caps. The L0→L1→L2 progression shows how confidence increases as more biomarker data becomes available, enabling clinicians to make informed decisions about when to proceed with treatment versus when to wait for additional testing.

**Receipt:** `receipts/clinical/tcga_ov_l0_l1_l2_examples.json`

### Figures

- **Figure 1. Architecture schematic** (`figures/figure_1_architecture.png`) — Inputs → TumorContext → per-drug gates → provenance-bearing outputs
- **Figure 2. PARP gate effects** (`figures/figure_2_parp_gates.png`) — PARP gate behavior (germline-negative penalty vs HRD rescue)
- **Figure 3. Confidence caps** (`figures/figure_3_confidence_caps.png`) — Confidence caps as a function of completeness (L0/L1/L2)
- **Figure 4. TMB survival (TCGA-UCEC)** (`figures/clinical/figure_io_tmb_tcga_ucec_os.png`) — Kaplan–Meier curve for TMB-high vs TMB-low
- **Figure 5. MSI survival (TCGA-UCEC)** (`figures/clinical/figure_io_msi_tcga_ucec_os.png`) — Kaplan–Meier curve for MSI-high vs MSS
- **Figure 6. Combined biomarker comparison (UCEC)** (`figures/clinical/figure_baseline_comparison_io_tcga_ucec.png`) — TMB-only, MSI-only, and OR-gate survival curves
- **Figure 7. Negative control (COADREAD)** (`figures/clinical/figure_baseline_comparison_io_tcga_coadread.png`) — No significant OS separation in colorectal cohort

---

## Discussion

We present a conservative tumor-context gating layer designed to reduce overconfidence and improve auditability when tumor NGS is unavailable at decision time. The contribution is operational and safety-oriented: deterministic gates, explicit completeness, and structured provenance.

### Biomarker and gate-behavior validation findings

The TCGA-UCEC analyses demonstrate that TMB and MSI status are prognostic in this cohort (TMB-high n=120/516; MSI-high n=174/527; OR-positive n=210/527). These results validate **biomarker prognostic signal** and support using biomarker presence as a deterministic trigger for gate behavior, but do not establish treatment benefit. 

We previously reported TCGA-COADREAD as a "negative control" for IO biomarker survival stratification. This framing is misleading: TCGA-COADREAD is largely a pre-checkpoint-therapy era cohort, and treatment exposure is not captured. Therefore, lack of OS stratification in COADREAD cannot be interpreted as a lack of checkpoint inhibitor benefit, and should not be used to argue tissue-dependence of IO *treatment effect*. We retain COADREAD as a **dataset limitation example** for prognosis-only analyses, not as an IO-treatment negative control.                                          

### Comparison to existing precision oncology platforms

Commercial genomic profiling platforms (Foundation Medicine, Tempus) provide comprehensive biomarker reports but do not quantify confidence based on data completeness. Clinical decision support systems (IBM Watson Oncology, CancerLinQ) provide treatment recommendations but lack structured provenance for biomarker-driven adjustments. To our knowledge, this is the first system to:

1. **Calibrate confidence based on data completeness** (L0/L1/L2 framework) rather than treating all recommendations as equally certain, even when biomarker data is incomplete
2. **Provide structured provenance for every biomarker-driven adjustment**, enabling audit and validation (e.g., `PARP_PENALTY_HRD_LOW`, `IO_BOOST_TMB_HIGH`)
3. **Validate conservative behavior at scale** (n=469 real tumor profiles), demonstrating that the system applies conservative defaults (98%+ penalty application) when evidence is incomplete

This approach addresses a critical gap in operational precision oncology: most patients lack complete tumor sequencing at decision time (60-70% in real-world settings), yet existing systems do not explicitly model or communicate this uncertainty. The completeness-aware confidence calibration and provenance framework enable transparent, auditable recommendations even when biomarker data is incomplete.

### Comparison to standard clinical workflow

Standard clinical practice presents treatment recommendations without explicit confidence quantification or provenance tracking. Table 2 compares our system's behavior to standard practice across three common scenarios:

| Scenario | Standard Practice | This System | Difference |
|---------|------------------|-------------|------------|
| Germline-negative, HRD unknown | "Consider PARP inhibitor" (subjective) | Efficacy: 0.56 (0.8× penalty), Confidence: 0.40 (L0 cap), Provenance: `PARP_UNKNOWN_HRD` | Transparent penalty and confidence cap with structured rationale |
| MSI-high IHC only (no NGS) | "May benefit from checkpoint inhibitor" (vague) | Efficacy: 0.78 (1.3× boost), Confidence: 0.60 (L1 cap), Provenance: `IO_MSI_BOOST` | Quantified boost with calibrated confidence and receipt-backed provenance |
| No biomarker data available | "Standard of care" or delayed decision | Efficacy: unchanged, Confidence: 0.40 (L0 cap), Provenance: `CONFIDENCE_CAP_L0` | Actionable guidance with explicit uncertainty, enabling informed decision-making |

**Key differences**: (1) **Transparency**: Standard practice provides recommendations without explicit confidence; this system quantifies uncertainty and provides structured rationale. (2) **Completeness-capped confidence**: Standard practice does not adjust confidence based on data completeness; this system caps confidence when evidence is incomplete. (3) **Provenance**: Standard practice lacks audit trails; this system provides provenance for every adjustment, enabling reproducibility and validation.

### Safety behavior under incomplete intake

The real-cohort safety audit (TCGA-OV, n=469) demonstrates that the system applies conservative defaults when evidence is missing: 98.1% of patients received PARP penalties when germline status was unknown, and 100% received confidence caps when tumor context was incomplete (L1). This "safety-first" behavior prevents overconfident recommendations in the sporadic majority while remaining operational for the precision minority.

### Limitations

- TCGA-UCEC results are retrospective prognostic associations (not causal treatment benefit).
- Group sizes are modest for some strata (e.g., TMB-high n=120; MSI-high n=174), and effect estimates should be interpreted with the reported confidence intervals; external validation is needed for any claims beyond prognosis and deterministic gate behavior.                                                                           
- Prospective logging is required to validate enrollment lift and patient benefit attributable to the system.
- HRD thresholds and IO biomarker thresholds are implemented as deterministic policies and should be evaluated on cohort-appropriate outcome-labeled data when making outcome claims.
- Confidence caps (0.4 for L0; 0.6 for L1) represent conservative evidence-availability constraints, not calibrated probabilities of recommendation correctness; calibration requires outcome-labeled concordance or prospective study.  
- Quick Intake does not infer MSI/TMB without provided inputs; missing biomarkers are handled via completeness and confidence caps.

### Future work

- Integrate validated tumor NGS parsers (e.g., Foundation/Tempus) to populate L2 contexts.
- Expand cohort-appropriate outcome benchmarking for biomarkers where prevalence supports statistical analysis.
- Extend provenance UI surfaces across therapy recommendation experiences.
- Prospective validation of enrollment lift and patient benefit attributable to the system.

---

## Data Availability

All validation artifacts for this manuscript are included in this repository folder under `submission_aacr/` (receipts, figures, scenario suite). No patient-level identifying data are included. External clinical datasets (TCGA) are referenced via their original sources (cBioPortal, TCGA Pan-Cancer Atlas 2018).

## Code Availability

The deterministic gates live in the backend repository at:
- `oncology-coPilot/oncology-backend-minimal/api/services/efficacy_orchestrator/sporadic_gates.py`

Validation receipts were generated by running the validation scripts referenced in `SUPPLEMENT.md`.

---

## Author Contributions

**Sabreen Abeed Allah:** Investigation; Resources; Writing – review & editing.  
**Fahad Kiani:** Conceptualization; Methodology; Software; Data curation; Formal analysis; Visualization; Writing – original draft; Writing – review & editing; Supervision.

## Competing Interests

The authors declare no potential conflicts of interest.

---

## References

1. Farmer H, et al. Targeting the DNA repair defect in BRCA mutant cells as a therapeutic strategy. *Nature*. 2005;434:917–921.
2. Bryant HE, et al. Specific killing of BRCA2-deficient tumours with inhibitors of poly(ADP-ribose) polymerase. *Nature*. 2005;434:913–917.
3. Le DT, et al. PD-1 blockade in tumors with mismatch-repair deficiency. *N Engl J Med*. 2015;372:2509–2520.
4. Yarchoan M, et al. Tumor mutational burden and response rate to PD-1 inhibition. *N Engl J Med*. 2017;377:2500–2501.
5. Cerami E, et al. The cBio cancer genomics portal: an open platform for exploring multidimensional cancer genomics data. *Cancer Discov*. 2012;2:401–404.
6. Hoadley KA, et al. Cell-of-origin patterns dominate the molecular classification of 10,000 tumors from 33 types of cancer. *Cell*. 2018;173:291–304.e6.
