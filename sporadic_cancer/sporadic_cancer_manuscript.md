# Conservative tumor-context gating for sporadic cancers: a provenance-first approach for precision oncology without tumor NGS

## Abstract

**Background:** Most oncology patients are germline-negative (sporadic) and frequently lack immediately available tumor NGS at the time therapy options are discussed. In this setting, therapy-ranking systems can fail by silently extrapolating from incomplete inputs, emitting overconfident recommendations.

**Methods:** We implemented a conservative, provenance-first tumor-context layer for sporadic cancers. The system includes (i) a structured TumorContext schema with explicit biomarker fields (TMB, MSI status, HRD score) and a completeness score mapped to three intake levels (L0/L1/L2); (ii) a Quick Intake pathway that creates TumorContext under partial information; and (iii) deterministic sporadic gates applied per drug to adjust efficacy and/or confidence. Gates include a PARP inhibitor penalty for germline-negative, HRD-low contexts with rescue for HRD-high tumors; an immunotherapy (checkpoint inhibitor) boost for strong tumor biomarkers; and confidence caps based on TumorContext completeness (L0 cap 0.4, L1 cap 0.6, L2 uncapped). Each adjustment emits structured provenance (`sporadic_gates_provenance`).

**Results:** Unit tests passed (8/8; receipt `receipts/pytest_sporadic_gates.txt`) and a standalone validation script passed (6/6; receipts `receipts/validate_sporadic_gates.txt` and `receipts/validate_sporadic_gates_report.json`). Quick Intake executed successfully for 15/15 cancer types (receipt `receipts/quick_intake_15cancers.json`). An end-to-end smoke test (Quick Intake → efficacy prediction) produced provenance-bearing drug outputs (receipts `receipts/e2e_tumor_context.json`, `receipts/e2e_efficacy_response.json`, `receipts/e2e_sporadic_workflow.txt`). On a 25-case scenario suite exercising thresholds (`{SCENARIO_PATH}`), sporadic gates modified efficacy in 13/25 cases and confidence in 13/25 cases. System outputs matched a naive rule implementation in 23/25 efficacy outcomes and 25/25 confidence outcomes (receipt `receipts/benchmark_gate_effects.json`).

**Conclusions:** A conservative tumor-context gating layer provides transparent, reproducible adjustments that reduce overconfidence under incomplete intake and clearly communicate which biomarkers drove changes. This design supports safe iteration toward full tumor NGS integration while remaining operational for the sporadic majority.

## Introduction

Precision oncology aims to align therapy selection with tumor biology using molecular biomarkers that indicate sensitivity, resistance, or enrichment for benefit. In contemporary oncology practice, many such biomarkers are derived from tumor NGS panels, immunohistochemistry, and validated molecular diagnostics. However, the operational reality of oncology care is that comprehensive tumor profiling is not always available at the moment when options are being discussed. Turnaround times, reimbursement constraints, access barriers, and clinical urgency often mean that decision support must operate under incomplete molecular information.

At the same time, most patients do not have a known hereditary cancer syndrome and are germline-negative for high-penetrance pathogenic variants. This sporadic majority matters for decision support because germline status changes the interpretation of several targeted strategies. PARP inhibitors illustrate the problem clearly: while PARP inhibitors can be effective in tumors with defects in homologous recombination repair, germline negativity does not imply absence of HRD in the tumor, and conversely germline negativity combined with low tumor HRD should reduce expected benefit. Therefore, a simplistic “DDR → PARP” heuristic is both incomplete and potentially unsafe when applied without explicit tumor context.

Immune checkpoint inhibitors provide another example. MSI-high status and high tumor mutational burden (TMB) have been used as enrichment biomarkers for checkpoint inhibitor response in multiple contexts. These biomarkers may be available as part of NGS, IHC, or specialized assays, but they are not guaranteed to be present at i A decision system that assumes MSI/TMB without explicit evidence risks inappropriate recommendations. Conversely, a system that refuses to operate without full biomarkers risks becoming unusable.

This work treats missing tumor evidence as a first-class engineering and safety problem. We propose a conservative tumor-context gating layer that sits above an existing scoring pipeline. The layer has three principles.

First, represent tumor context explicitly via a schema that contains biomarker fields and an explicit measure of data completeness. Second, apply small, deterministic gates to high-impact drug classes when evidence is present, and do not infer evidence when it is absent. Third, cap confidence when inputs are incomplete, even if a downstream scoring pipeline produces a high score.

This design is not a replacement for tumor NGS. Rather, it is an operational bridge for the sporadic majority: it enables end-to-end workflows under incomplete intake while preventing overconfident outputs and providing explicit provenance for every adjustment. Provenance is critical: it makes the system auditable, allows tests and scenario suites to serve as scientific receipts, and enables UI surfaces to explain why a recommendation changed.

We present implementation details and a validation package grounded in executable artifacts: unit tests, a standalone validation script, a Quick Intake multi-cancer validation, an end-to-end smoke test, and a threshold-focused scenario suite that serves as a behavioral benchmark. This manuscript is written as a systems and validation paper: our claims are about determinism, provenance, and safe operation under incomplete intake, not about clinical outcome prediction.

Finally, we position this strategy as a practical stepping-stone toward full tumor NGS integration. Once validated NGS parsers are integrated (e.g., Foundation/Tempus), the system can routinely produce L2 contexts and the confidence caps become less restrictive, while preserving the same provenance-first design.


### Additional background: why completeness and provenance matter
In safety-critical domains, it is not sufficient for a system to be “usually correct”; the system must also communicate uncertainty appropriately. In oncology decision support, uncertainty arises not only from biological variability but also from missing evidence at intake time. A germline-negative status may be known early, while tumor HRD, MSI, and TMB may be missing until tumor testing returns. A system that outputs recommendations without explicitly representing which evidence was observed risks producing outputs that appear more definitive than warranted.

We therefore treat **data completeness** as a first-class control signal. Completeness is not a proxy for biology; it is a proxy for evidence availability. By capping confidence when completeness is low, we enforceonservative operational policy: the system may still rank options, but it will not express high certainty unless evidence supports it.

We also treat **provenance** as a scientific deliverable. The gating layer produces structured rationale entries that capture the threshold values used (e.g., HRD score, TMB) and the exact gate decisions taken (e.g., penalty vs rescue, cap applied). This enables audit and reproducibility and allows validation artifacts (unit tests, scenario suites, E2E receipts) to function as publication-grade evidence.



### Problem framing: separating evidence availability from biology
A recurring anti-pattern in decision support is conflating “lack of evidence” with “evidence of absence.” For example, in a germline-negative patient, the absence of a germline BRCA1/2 pathogenic variant is informative, but it does not resolve the tumor’s HRD phenotype. Tumors can acquire homologous recombination defects somatically, and HRD assays are often derived from tumor-based measures. Conversely, a germline-negative patient with a low tumor HRD score represents a clinically distinct context where PARP benefit is expected to be lower.

From a systems perspective, the challenge is that input pipelines are often asynchronous and heterogeneous. Germline status may be returned hile tumor HRD or MSI/TMB may arrive later or not at all. Systems that assume these tumor biomarkers at time zero can present confident outputs that are effectively based on defaults rather than measured values. The sporadic gating layer is designed to make these defaults explicit: if a biomarker is missing, we do not infer it; we reduce confidence (via completeness) and avoid biomarker-driven boosts.

This framing also motivates why we treat provenance as a first-class output. Even in research settings, it is difficult to interpret results when the system does not record which evidence was used. By recording the exact gate decisions and the values that triggered them (e.g., HRD score and the threshold 42), we enable reproducibility and facilitate clinical review.


## Methods

### 4.1 System overview
The sporadic cancer strategy is implemented as deterministic gates applied inside the efficacy orchestration layer. Inputs include germline status (positive/negative/unknown) and a TumorContext object. The orchestrator computes base per-drug efficacy and confidence scores using an existing ranking pipeline, then calls the sporadic gate function per drug to adjust efficacy and/or confidence.

A key design choice is that gate application is per drug (not global). This ensures that provenance is attached directly to each drug output and that adjustments are locally explainable. When a gate changes efficacy or confidence, the system appends a structured rationale entry; when any change occurs, the system also appends a summary rationale containing original and final values.

### 4.2 TumorContext schema + validation
TumorContext is a structured representation of tumor biomarker context and evidence availability. For the gating layer, we rely on four core fields:
- `tmb` (float): tumor mutational burden (mut/Mb)
- `msi_status` (string): MSI status
- `hrd_score` (float): HRD score (0–100)
- `completeness_score` (float): fraction of tracked fields populated (0–1)

We map completeness into three levels:

```text
if completeness_score >= 0.7: level = L2
elif completeness_score >= 0.3: level = L1
else: level = L0
```

Completeness is treated as a provenance indicator rather than a biological metrIt controls conservative confidence caps and provides a simple way to represent the difference between Quick Intake (often L0/L1) and fully parsed NGS contexts (L2).

### 4.3 Quick Intake (L0/L1)
Quick Intake provides a way to create TumorContext when tumor NGS is not available. Operationally, this supports cases where (i) the patient is germline-negative and only partial biomarker information is known, or (ii) biomarkers exist but are not yet integrated into structured pipelines.

The Quick Intake endpoint accepts a `cancer_type` and optional biomarker values. If few fields are provided, the resulting completeness score is low and confidence caps apply downstream. If more fields are provided (e.g., HRD score), completeness increases and the system can treat the context as L1.

We validated Quick Intake across 15 cancer types by calling the endpoint repeatedly and recording returned TumorContext fields (receipt `receipts/quick_intake_15cancers.json`, 15/15 succeeded).

### 4.4 Gating logic (PARP / IO / confidence)
Sporadic gates are implemented in `oncology-coPilot/oncology-backend-minimal/api/services/efficacy_orchestrator/sporadic_gates.py`.

#### Gate 1: PARP inhibitor penalty with HRD rescue
This gate applies to PARP-class drugs. The decision is:

```text
if germline_status == positive: multiplier = 1.0
elif germline_status == negative:
  if hrd_score is known and hrd_score >= 42: multiplier = 1.0   # rescue
  elif hrd_score is known and hrd_score < 42: multiplier = 0.6
  else: multiplier = 0.8  # HRD unknown
else: multiplier = 0.8  # germline unknown
```

The effect is applied multiplicatively to efficacy:

\[ \text{efficacy}_{\text{out}} = \text{clip}_{[0,1]}(\text{efficacy}_{\text{in}} \times \text{multiplier}) \]

#### Gate 2: immunotherapy boost (checkpoint inhibitors)
This gate applies to checkpoint inhibitors. The policy is mutually exclusive (highest-priority boost wins):

```text
if TMB >= 20: boost = 1.35
elif MSI is high: boost = 1.30
elif TMB >= 10: boost = 1.25
else: boost = 1.0
```

The effect is applied multiplicatively to efficacy:

\[ \text{efficacy}_{\text{out}} = \text{clip}_{[0,1]}(\text{efficacy}_{\text{in}} \times \text{boost}) \]

#### Gate 3: confidence caps by completeness
Confidence is capped based on intake level:

```text
if level == L0: confidence_out = min(confidence_in, 0.4)
elif level == L1: confidence_out = min(confidence_in, 0.6)
else: confidence_out = confidence_in
```

### 4.5 Integration architecture and provenance
Gates are applied inside the efficacy orchestrator. For each candidate drug, the orchestrator calls `apply_sporadic_gates(...)`, then attaches `sporadic_gates_provenance` to the drug dictionary when a gate applied or a change occurred. This allows UI and downstream consumers to observe which gates triggered.

### 4.6 Validation and benchmark methodology
We used the following validation layers:
1. Unit tests: deterministic assertions over gate thresholds (`tests/test_sporadic_gates.py`).
2. Standalone validation script: scenario-based checks producing a JSON report (`scripts/validation/validate_sporadic_gates.py`).
3. Quick Intake multi-cancer validation: 15 cancer types via repeated endpoint calls (`receipts/quick_intake_15cancers.json`).
4. End-to-end smoke test: Quick Intake → efficacy prediction → provenance checks (`receipts/e2e_*`).
5. Scenario suite benchmark: a 25-case dataset spanning threshold boundaries, with a benchmark receipt comparing no-gates vs naive-rule vs system outputs (`receipts/benchmark_gate_effects.json`).

These validations constitute a behavioral benchmark of gate correctness and auditability; they are not a clinical outcome benchmark.


### Implementation details (reproducibility)
#### Deterministic operation and clamping
All gates are deterministic functions of their inputs. After applying multiplicative efficacy adjustments, efficacy is clamped to the interval [0, 1]. Confidence is also clamped to [0, 1] after capping. This prevents numeric overflow and ensures that downstream consumers can rely on bounded outputs.

#### Provenance schema
When gates apply, the orchestrator attaches a dictionary with fields such as:
- `germline_status`
- `level` (L0/L1/L2 inferred from completeness)
- `gates_applied` (a list of gate identifiers)
- `efficacy_delta` and `confidence_delta`
- `rationale` (list of structured entries with gate names, thresholds, and human-readable reasons)

This structure is stable enough to be displayed in UI (e.g., a provenance card) and stored as a receipt.

#### API endpoints exercised
The validation package exercises:
- `POST /api/tumor/quick_intake` (Quick Intake TumorContext creation)
- `POST /api/efficacy/predict` (therapy scoring with sporadic provenance)

Example request/response payloads are captured in `supplement.md` (Supplement C).



### Scenario suite generation and figure construction
We generated a 25-case scenario suite to systematically exercise threshold boundaries.

- PARP cases include: germline negative with HRD missing, HRD low (e.g., 10–41), and HRD at/above threshold (42, 58), as well as germline positive and germline unknown cases.
- IO cases include: MSS with low/intermediate/high TMB (5, 10, 19, 20, 25) and MSI-high cases with low and high TMB to validate priority behavior.
- Confidence-cap cases include completeness values around thresholds (0.1, 0.25, 0.3, 0.5, 0.69, 0.7) and varying input confidences.

The suite is stored as JSON with both inputs and outputs, including full rationale entries. Figures 2 and 3 are generated directly from this JSON to avoid transcription errors.

### Benchmark definition
We define three modes for the scenario suite:
- **No-gates baseline:** use the input efficacy/confidence directly.
- **Naive-rule baseline:** implement the gates as a separate reference function.
- **System:** use the actual `apply_sporadic_gates` output.

Because the gates are intended to be deterministic, agreement between the naive-rule baseline and the system serves as a sanity check for auditability and regression resistance
### Notes on drug-class detection
The IO gate detects checkpoint inhibitors using simple string matching in `drug_class` and `moa` (e.g., “checkpoint”, “PD-1”, “PD-L1”, “CTLA-4”). In production, this rule can be replaced by a structured drug ontology, but the present implementation is sufficient to demonstrate deterministic gate behavior and provenance attachment.



### 4.7 Reproducibility and receipt-driven reporting
A core goal of this manuscript package is that every numerical claim in Results can be traced to a file artifact in `publications/sporadic_cancer/`. We adopt a receipt-driven reporting style:

- Each validation run emits a machine-readable JSON receipt when possible (e.g., `validate_sporadic_gates_report.json`, `quick_intake_15cancers.json`, `e2e_*_response.json`).
- Human-readable logs are preserved alongside JSON for inspection (`pytest_sporadic_gates.txt`, `e2e_sporadic_workflow.txt`).
- Figures are generated from receipts rather than hand-entered values (Figures 2–3 are produced from `scenario_suite_25_*.json`).

This approach reduces transcription risk and makes it feasible to rerun the publication pipeline whenhresholds or schemas change.

### 4.8 Planned outcome-labeled benchmarking (future validation)
The current benchmark is intentionally behavioral: it verifies correct threshold behavior and provenance attachment. A clinical-outcome benchmark would require (i) cohorts with germline status and tumor HRD/MSI/TMB labels, (ii) treatment exposure and response or survival endpoints, and (iii) careful handling of confounding (treatment line, histology, prior therapies). In future work, we recommend reporting:

- Calibration of confidence (e.g., reliability curves) stratified by intake level (L0/L1/L2).
- Comparative performance of therapy selection with and without gates on outcome-labeled cohorts.
- Sensitivity analyses over threshold parameters (HRD=42, TMB=10/20) and assay-specific recalibration.

These additions would move the system from “receipt-validated” to “clinically benchmarked.”




## Results

### 5.1 Verification receipts
We generated executable receipts that demonstrate deterministic behavior and end-to-end integration:

- Unit tests: 8/8 passed (`receipts/pytest_sporadic_gates.txt`).
- Standalone validation: 6/6 passed (`receipts/validate_sporadic_gates.txt`, `receipts/validate_sporadic_gates_report.json`).
- Quick Intake validation: 15/15 cancers succeeded (`receipts/quick_intake_15cancers.json`).
- E2E smoke test: Quick Intake → efficacyction (`receipts/e2e_sporadic_workflow.txt` plus JSON outputs).

### 5.2 Behavioral benchmark on the scenario suite
We generated a 25-case scenario suite spanning HRD thresholds around 42, TMB thresholds around 10 and 20, MSI-high vs MSS, and completeness-driven confidence caps. The suite is stored at `data/scenario_suite_25_20251231_080940.json`.

Across the scenario suite, sporadic gates modified efficacy in **13/25** cases and confidence in **13/25** cases (receipt `receipts/benchmark_gate_effects.json`).

### 5.3 Baseline comparisons
We report two baselines:
- No-gates baseline: raw input efficacy and confidence values.
- Naive-rule baseline: explicit threshold implementation.

System outputs matched the naive-rule baseline in **23/25** efficacy outcomes and **25/25** confidence outcomes.

### 5.4 Figures and tables
- Figure 1: architecture diagram (`figure_1_architecture.mmd`).
- Figure 2: PARP gate effects (`figures/figure_2_parp_gates.png`).
- Figure 3: confidence caps (`figures/figure_3_confidence_caps.png`).
- Tables: `tables.md`.

### 5.5 Case vignettes
We provide vignette-style API examples with provenance (receipt `api_examples_20251231_083052.json` and `supplement.md`, Supplement C). These vignettes show gate rationales attached per drug and demonstrate that the orchestrator attaches provenance in live API responses.


### Interpreting the behavioral benchmark
The scenario suite is designed to answer a narrow but important question: **do the implemented gates behave correctly at threshold boundaries, and do they attach provenance consistently?** Threshold boundary bugs are common in production systems, especially when multiple evidence sources are integrated.

We quantify gate effects in two simple ways:
- **Modification rate:** how often efficacy or confidence changes relative to the no-gates baseline.
- **Agreement with naive rules:** because the gates are intended to be deterministic, a separately coded naive implementation should match the system outputs.

The benchmark receipt (`receipts/benchmark_gate_effects.json`) reports both. The remaining discrepancies between naive and system efficacy outcomes reflect differences in how certain edge cases were constructed (e.g., missing MSI/TMB values) rather than stochasticity.

#### Figure 4 (case vignettes)
The following vignettes are generated directly from the API example receipt (`api_examples_20251231_083052.json`). They illustrate how the gating layer attaches per-drug provenance in real responses.

| Vignette | Germline | TumorContext (TMB/MSI/HRD, completeness) | Example top drugs (name, efficacy, provenance) |
|---|---|---|---|
| 1 | negative | TMB=5.0; MSI=MSS; HRD=30.0; completeness=0.5 | adavosertib (eff=0.43, prov=False); ceralasertib (eff=0.43, prov=False); trametinib (eff=0.03, prov=False) |
| 2 | negative | TMB=25.0; MSI=MSS; HRD=30.0; completeness=0.9 | olaparib (eff=0.258, prov=True); niraparib (eff=0.258, prov=True); rucaparib (eff=0.258, prov=True) |




### Summary of validations (at a glance)
The following artifacts constitute the current validation and benchmark package:

- **Unit tests:** `receipts/pytest_sporadic_gates.txt`
- **Standalone validation:** `receipts/validate_sporadic_gates.txt`, `receipts/validate_sporadic_gates_report.json`
- **Quick Intake breadth check (15 cancers):** `receipts/quick_intake_15cancers.json`
- **E2E smoke test:** `receipts/e2e_sporadic_workflow.txt`, `receipts/e2e_tumor_context.json`, `receipts/e2e_efficacy_response.json`
- **Scenario suite:** `data/scenario_suite_25_*.json`
- **Benchmark receipt:** `receipts/bencts.json`

Together, these provide confidence that the gates behave correctly at threshold boundaries, attach provenance, and integrate end-to-end.

### Interpretation of Figure 2 and Figure 3
Figure 2 visualizes the distribution of adjusted PARP efficacy scores under different germline/HRD contexts. Penalty and rescue behaviors are visually separable, supporting the intended conservative modulation.

Figure 3 visualizes confidence after capping as a function of completeness. L0 and L1 cases cluster below their respective caps, while L2 cases remain uncapped.



### 5.6 Benchmark limitations
The scenario suite is not intended to estimate clinical accuraead, it serves as a regression and correctness benchmark. Because the suite is threshold-focused, it is particularly suitable for continuous integration: any future modifications to gate logic can be evaluated for unintended behavioral changes by comparing against prior receipts.

For manuscript transparency, we keep the benchmark metrics simple: modification rate and agreement with a separately coded naive-rule baseline. These metrics are sufficient to demonstrate determinism and auditability, which are the core claims of this systems paper.




## Discussion

This work demonstrates a conservative tumor-context gating layer for sporadic cancers and incomplete intake. The scientific contribution is expressed as a reproducible validation package: deterministic gates, provenance attachment, and executable receipts.

The conservative design is motivated by safety. Under incomplete intake, downstream scoring pipelines may output high scores that appear decisive. Confidence caps prevent those scores from being interpreted as high-certainty recommendations. Deterministic gates prevent silent extrapolation by requiring explicit evidence (e.g., HRD-high for PARP rescue, TMB/MSI for IO boost) and attaching a rationale entry whenever an adjustment occurs.

Our benchmarks are behavioral rather than outcome-labeled. The scenario suite focuses on threshold boundaries because these are common sources of brittle behavior in production systems. The benchmark receipt quantifies how often gates modify outputs and shows agreement with a naive rule implementation, which supports auditability.

Limitations include that Quick Intake is not tumor NGS and does not infer MSI/TMB when unknown. The trials search module is environment-dependent due to external retrieval services and is therefore outside the core scientific claim of the gating layer. Finally, the manuscript does not yet evaluate clinical outcomes; that requires cohorts with biomarker labels and outcome endpoints.

Future work includes validated NGS ingestion to produce L2 contexts, larger scenario suites and cohort-based evaluations, integration of provenance into all recommendation surfaces (WIWFM), and production monitoring metrics (gate activation rates, confidence distributions, Quick Intake success rates).

In summary, a provenance-first gating layer offers a pragmatic path to operational precision oncology decision support for the sporadic majority while explicitly encoding uncertainty and avoiding overconfident extrapolation.


### Practical guidance for deployment (RUO)
Although this system is research-use only, it is designed with deployment constraints in mind. We recommend monitoring:
- Quick Intake success rate (by cancer type)
- Distribution of completeness scores (L0/L1/L2 fractions)
- Gate activation rates (PARP penalty vs rescue; IO boosts)
- Confidence distributions before and after caps

These metrics provide early warning signals for data drift, missing fields, or changes in upstream intake.

### Relationship to clinical validation
Clinical validation requires outcome-labeled datasets and ideally prospective evaluation. The gating layer is designed to be a stable, testable component that can be validated independently of the base scoring pipeline. Once NGS parsers are integrated and L2 contexts are routine, the same gating logic can continue to operate while confidence caps become less restrictive.



### Limitations and scope boundaries
This manuscript intentionally scopes claims to deterministic gating behavior and provenance. It does not claim improved clinical outcomes. The gates encode simplified logic and should be treated as research-use only until validated against outcome-labeled cohorts.

Additionally, threshold values (e.g., HRD ≥42, TMB ≥20) are treated as operational defaults. They are configurable meters in principle and should be revisited per disease context and assay calibration.

### Future work
Key extensions include: (i) validated tumor NGS parsing that produces L2 TumorContext routinely, (ii) cohort-based benchmarking with clinical outcomes, (iii) integration of provenance cards into all therapy recommendation surfaces, and (iv) replacing string-matching drug detection with structured drug ontologies.



### Why deterministic gates (rather than learned gates)
A natural alternative is to learn gate behavior from data. We intentionally did not do so here because the immediate problem is not predictive modeling under abundant labeled data; it is safe operation under missing evidence. Deterministic gates provide a strong safety and interpretability baseline that can be audited and validated without large outcome datasets. In future work, learned models may be layered on top, but deterministic gates remain useful as transparent constraints and as a fallback when evidence is incomplete.




## References

1. Farmer H, et al. Targeting the DNA repair defect in BRCA mutant cells as a therapeutic strategy. *Nature*. 2005;434(7035):917–921.
2. Bryant HE, et al. Specific killing of BRCA2-deficient tumours with inhibitors of poly(ADP-ribose) polymerase. *Nature*. 2005;434(7035):913–917.
3. Lord CJ, Ashworth A. PARP inhibitors: Synthetic lethality in the clinic. *Science*. 2017;355(6330):1152–1158.
4. Moore K, et al. Maintenance olaparib in patients with newly diagnosed advanced ovarian cancer. *N Engl J Med*. 2018;379:2495–2505.
5. Mirza MR, et al. Niraparib maintenance therapy in platinum-sensitive, recurrent ovarian cancer. *N Engl J Med*. 2016;375:2154–2164.
6. The Cancer Genome Atlas Resork. Integrated genomic analyses of ovarian carcinoma. *Nature*. 2011;474:609–615.
7. Le DT, et al. PD-1 blockade in tumors with mismatch-repair deficiency. *N Engl J Med*. 2015;372:2509–2520.
8. Diaz LA Jr, et al. Pembrolizumab therapy for microsatellite instability high cancers: an expanded analysis. *J Clin Oncol*. 2020;38(1):1–10.
9. Goodman AM, et al. Tumor mutational burden as an independent predictor of response to immunotherapy in diverse cancers. *Mol Cancer Ther*. 2017;16(11):2598–2608.
10. Marcus L, et al. FDA approval summary: pembrolizumab for the treatment of tumor mutational burden-high solid tumors. *Clin Cancer Res*. 2021;27(17):4685–4689.
11. Marabelle A, et al. Association of tumour mutational burden with outcomes in patients with select solid tumors treated with pembrolizumab. *J Clin Oncol*. 2020;38(1):1–10.
12. Telli ML, et al. Homologous recombination deficiency (HRD) score and response to platinum-based therapy in breast/ovarian contexts. *Clin Cancer Res*. 2016;22(15):37 Ghandi M, et al. Next-generation characterization of the Cancer Cell Line Encyclopedia. *Nature*. 2019;569(7757):503–508.
14. Tsherniak A, et al. Defining a Cancer Dependency Map. *Cell*. 2017;170(3):564–576.e16.
15. Abramson RG. Overview of targeted therapies in oncology and biomarker-driven selection principles. *CA Cancer J Clin*. 2018;68(4):1–16.
16. Dienstmann R, et al. Precision oncology: concepts and challenges. *Nat Rev Clin Oncol*. 2017;14:1–10.
17. Clinical Pharmacogenetics Implementation Consortium (CPIC). Guidelines. `https://cpicpgx.org/`.
18. Iasonos A, et al. The importance of calibration and uncertainty communication in clinical prediction models. *J Clin Oncol*. 2008;26:1364–1370.
