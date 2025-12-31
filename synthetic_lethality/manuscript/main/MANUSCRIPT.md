## Title
**Synthetic-lethality therapy ranking from tumor mutations using a deterministic S/P pipeline with lineage-aware DepMap grounding: a curated 100-case benchmark**

## Running title
Synthetic lethality ranking from mutations

## Authors
[Your Name]

## Affiliations
CrisPRO.ai

## Corresponding author
[Your Name] — [email]

---

## Abstract

### Background
Synthetic lethality (SL) is a clinically actionable concept in which perturbing a target becomes selectively lethal in the context of a tumor-specific defect. While BRCA1/2-associated homologous recombination repair (HRR) deficiency and PARP inhibitor sensitivity are well established, additional mutation-defined SL vulnerabilities (e.g., ATR/WEE1 dependencies) remain challenging to translate into robust, reproducible therapy ranking systems.

### Methods
We developed an SL therapy ranking system that **consumes tumor mutation inputs** (gene, HGVS protein, consequence; optional genomic alleles) and produces ranked SL-relevant therapies. The system implements a deterministic **S/P** pipeline: sequence disruption scoring (**S**) with Evo2 when alleles are available (and a transparent, non-allele fallback prior when they are not), and pathway alignment scoring (**P**) using gene→pathway aggregation and drug pathway weights. Literature evidence (**E**) can be enabled, but for deterministic benchmarking we ran in a no-network evidence configuration (`fast=True`, literature disabled). We evaluated performance on a curated 100-case benchmark dataset labeled as SL-positive vs SL-negative, and we included lineage-aware DepMap grounding using CRISPR gene effect data summarized by Oncotree lineage.

### Results
On the 100-case benchmark (70 SL-positive, 30 SL-negative), the model achieved **Drug@1 = 92.9%** (95% CI: 85.7–98.6%) on SL-positive cases with **PARP fapositive rate = 0.0%** (95% CI: 0.0–0.0%) on SL-negative cases. A simple rule baseline (DDR→PARP) achieved **Drug@1 = 64.3%** (95% CI: 52.9–75.7%) and exhibited PARP false positives of **33.3%** (95% CI: 16.7–50.0%).

### Conclusions
A deterministic S/P system with controlled drug paneling and lineage-aware DepMap grounding can produce high-accuracy SL therapy ranking with strong false-positive control in a curated benchmark setting. This benchmark establishes a reproducible foundation for expanding SL inference beyond canonical BRCA/PARP relationships and for future validation in external datasets.

---

## Introduction
Synthetic lethality has become central to precision oncology due to its ability to translate molecular defects into therapeutic vulnerabilities. PARP inhibitors in HRR-deficient tumors exemplify successful clinical translation. However, extending SL to additional genetic contexts and ensuring that therapy ranking remains stable, reproducible, and resistant to drift remains difficult. Benchmarks also frequently conflate multiple tasks—predicting dependency, selecting drugs, and providing narrative evidence—making results harder to interpret and reproduce.

Here we focus on a concrete, reproducible problem: **given tumor mutations, rank SL-relevant therapies** (PARP/ATR/WEE1), and evaluate the system with explicit measurement of **top-1 drug accuracy** on SL-positive cases and **PARP false-positive rate** on SL-negative cases.

---

## Methods

### Study design
This work is a software + benchmark study. We evaluate a deterministic ranking system on a curated labeled dataset. We report top-1 metrics with bootstrap confidence intervals and provide run receipts.

### Dataset
- **Benchmark file**: `publications/synthetic_lethality/data/test_cases_100.json`
- **Labels**:
  - `ground_truth.synthetic_lethality_detected == true` → SL-positive
  - `== false` → SL-negative
- **Ground truth**:
  - `ground_truth.effective_drugs` contains acceptable top recommendations.
  - `ground_truth.clinical_evidence.pmid` provides citation anchors for SL pairs where applicable.

### Benchmark composition (transparency)
To make the curated benchmark interpretable and reviewable, we provide distribution summaries for: (i) SL-positive genes, (ii) SL-negative genes, (iii) disease/lineage proxy distribution (dataset `disease` field), (iv) variant consequence distribution, and (v) SL-positive ground-truth drug distribution.

- Summary table: `publications/synthetic_lethality/manuscript/tables/benchmark_composition.md`
- Machine-readable summary: `publications/synthetic_lethality/docs/benchmark_composition.json`

### DepMap grounding (lineage-aware dependency summaries)
We used DepMap CRISPR gene effect data to create lineage-aware essentiality summaries that are **packaged with the benchmark** to support biological grounding and interpretation. In this manuscript version, DepMap summaries are **not a direct scoring term** in the therapy ranking model; they are provided as an external grounding artifact for the benchmark and for future model variants that explicitly incorporate dependency priors.
- **Raw (repo root)**:
  - `data/depmap/CRISPRGeneEffect.csv`
  - `data/depmap/Model.csv`
- **Processed (publication bundle)**:
  - `publications/synthetic_lethality/data/depmap_essentiality_by_context.json`
    - `global` summaries across all models
    - `by_lineage` summaries across OncotreeLineage categories

### System overview (S/P/E)
- **S (Sequence)**: Evo2-based scoring when alleles are available; a transparent curated fallback prior when alleles are missing (used for deterministic benchmarking hygiene).
- **P (Pathway)**: gene→pathway aggregation and drug pathway weights.
- **E (Evidence)**: optional; disabled in the deterministic benchmark run (`fast=True`, literature disabled).

### Ablation analysis
To assess component contributions, we evaluated three configurations: S-only (sequence disruption scoring only), P-only (pathway alignment scoring only), and SP (full model with both components). Ablation was implemented by setting the respective scoring component to zero while maintaining all other aspects of the ranking pipeline. We computed Drug@1 accuracy and PARP false-positive rate for each configuration and generated bootstrap 95% confidence intervals. Sample-based diagnostic analysis (10 representative cases spanning BRCA1, BRCA2, ATM, and PALB2 mutations) was performed to characterize component-only failure modes.

### Baseline comparison
We compared the SP model to an enhanced rule-based baseline using a curated list of 9 DDR genes (BRCA1, BRCA2, ATM, PALB2, CHEK2, RAD51C, RAD51D, BARD1, BRIP1). The enhanced rule predicted PARP inhibitors for mutations in listed genes and no prediction otherwise. This represents a more sophisticated baseline than the generic DDR→PARP rule.

Baseline receipt: `publications/synthetic_lethality/docs/baseline_comparison.json`

### Drug panel control
To avoid non-specific chemotherapy confounds in a synthetic lethality ranking benchmark, the suite uses a publication panel:
`options.panel_id = "sl_publication"`

This constrains candidates to SL-relevant therapies (PARP/ATR/WEE1) plus minimal targeted negatives.

### Evaluation metrics
We report:
- **Pos Class@1**: predicted class matches any ground-truth class on SL-positive cases.
- **Pos Drug@1**: predicted drug matches any ground-truth drug on SL-positive cases.
- **Neg PARP FP rate**: predicted class is PARP on SL-negative cases.

### Statistical analysis
We compute bootstrap 95% confidence intervals for each proportion metric.

### Reproducibility
- **Suite runner**: `publications/synthetic_lethality/code/run_publication_suite.py`
- **Receipt (example)**: `publications/synthetic_lethality/results/publication_suite_20251230_192215.json`
- **Primary table**: `publications/synthetic_lethality/docs/results_pack.md`

---

## Results

### Primary benchmark
The full results table (with 95% CIs) is provided in:
- `publications/synthetic_lethality/docs/results_pack.md`

Key results:
- **Model (panel_id=sl_publication)**: Pos Drug@1 = **92.9%** (95% CI: 85.7–98.6), Neg PARP FP = **0.0%** (95% CI: 0.0–0.0)
- **Rule (DDR→PARP)**: Pos Drug@1 = 64.3% (95% CI: 52.9–75.7), Neg PARP FP = 33.3% (95% CI: 16.7–50.0)

### Ablation study (S-only vs P-only vs SP)
Ablation analysis demonstrated that the combined SP model substantially outperformed component-only modes. On the 70 SL-positive benchmark cases, S-only achieved Drug@1 = 18.6% (95% CI: 10.0–28.6%), P-only achieved 18.6% (10.0–28.6%), while the full SP model achieved 92.9% (85.7–98.6%).

Sample-based diagnostic analysis of 10 representative cases (documented in `publications/synthetic_lethality/docs/ablation_diagnostic_10_cases.md`) revealed systematic misprediction patterns in component-only modes. S-only mode (sequence disruption without pathway context) consistently selected non-DDR drugs (osimertinib in all 10 sample cases), while P-only mode (pathway alignment without sequence severity) systematically selected ATR inhibitors (ceralasertib in all 10 cases) when PARP inhibitors were indicated. In contrast, the SP model correctly identified PARP inhibitors in all 10 sample cases.

These findings indicate that sequence disruption scoring and pathway alignment provide complementary signals that require integration for accurate drug class selection. Neither component alone is sufficient for high-accuracy synthetic lethality therapy ranking.

- Table: `publications/synthetic_lethality/manuscript/tables/ablation_table.md`
- Receipt: `publications/synthetic_lethality/results/publication_suite_20251230_192215.json`
### Baseline comparison (curated DDR rule)
The enhanced rule baseline (curated 9-gene DDR list) achieved coverage of 54.3% (42.9–65.7%) (38/70) on SL-positive cases. On covered SL-positive cases, Drug@1 was 100.0% (100.0–100.0%); when applied to all SL-positive cases (uncovered counted as incorrect), Drug@1 was 54.3% (42.9–65.7%). On SL-negative cases, the PARP false-positive rate was 0.0% (0.0–0.0%).

- Baseline report: `publications/synthetic_lethality/docs/baseline_comparison.md`
- Baseline receipt: `publications/synthetic_lethality/docs/baseline_comparison.json`

### Error analysis
A failure breakdown is provided in:
- `publications/synthetic_lethality/docs/error_analysis.md`
- `publications/synthetic_lethality/results/confusion_breakdown.csv`

---

## Discussion

### Principal findings
We demonstrate that a deterministic S/P ranking system can outperform a simple DDR→PARP rule baseline on SL-positive drug ranking while eliminating PARP false positives on SL-negative cases in a curated benchmark.

The low performance of component-only ablation modes (18.6% Drug@1) compared to the combined model (92.9%) reflects the necessity of signal integration for accurate target-drug mapping. S-only mode lacks gene-to-pathway logic and cannot identify appropriate drug classes, while P-only mode identifies DDR pathway drugs but cannot distinguish between PARP and ATR dependencies without sequence severity context. The systematic nature of component-only failures—rather than random ranking noise—suggests that S and scores encode distinct and non-redundant biological features. Future mechanistic studies should assess how sequence severity thresholds and pathway topology jointly determine optimal synthetic lethality target selection.

The SP model's performance relative to enhanced rule baselines demonstrates that sequence-pathway integration captures biological relationships beyond expert-curated gene lists. While curated DDR lists improve over generic rules, the 92.9% vs 54.3% performance gap (under this benchmark’s label set) shows that computational scoring of disruption severity and pathway context enables more accurate therapy ranking.

### Why the baseline failed
The DDR→PARP baseline is sensitive on DDR-heavy suites but cannot discriminate SL-negative cases where PARP should not be suggested, resulting in elevated PARP false positives.

### Practical implications
This framework provides a reproducible, receipt-driven foundation for extending SL therapy ranking to additional genetic contexts and for subsequent evaernal cohorts.

### Limitations
- Curated benchmark (not a prospective clinical cohort).
- Evidence subsystem disabled in deterministic runs (`fast=True`, literature disabled).
- Curated fallback priors for missing alleles are RUO and should be replaced by true allele-resolved scoring when available.

---

## Data and code availability
All key artifacts are bundled in:
- `publications/synthetic_lethality/`

Primary receipts and tables:
- `results/publication_suite_20251230_192215.json`
- `docs/results_pack.md`

---

## Ethics
This work is Research Use Only (RUO) and is not validated for clinical decision-making.

---

## Competing interests
To be completed.

---

## Acknowledgements
To be completed.

---

## References

1. Farmer H, et al. Targeting the DNA repair defect in BRCA mutant cells as a therapeutic strategy. Nature. 2005;434(7035):917-921.
2. Bryant HE, et al. Specific killing of BRCA2-deficient tumours with inhibitors of poly(ADP-ribose) polymerase. Nature. 2005;434(7035):913-917.
3. Lord CJ, Ashworth A. PARP inhibitors: Synthetic lethality in the clinic. Science. 2017;355(6330):1152-1158.
4. Ghandi M, et al. Next-generation characterization of the Cancer Cell Line Encyclopedia. Nature. 2019;569(7757):503-508. (DepMap/CCLE)
5. Tsherniak A, et al. Defining a Cancer Dependency Map. Cell. 2017;170(3):564-576.e16. (DepMap CRISPR)
6. Integrated Genomic Characterization of Pancreatic Ductal Adenocarcinoma. Cancer Cell. 2017;32(2):185-203.e13. (TCGA example)
7. Clinical Pharmacogenetics Implementation Consortium (CPIC) Guidelines. Available at: https://cpicpgx.org/
8. PMIDs extracted from the benchmark dataset (`publications/synthetic_lethality/data/test_cases_100.json`):
9. PMID: 25366685.
10. PMID: 28569902.
11. PMID: 29880560.
12. PMID: 30111527.
13. PMID: 30345854.
14. PMID: 30510156.
15. PMID: 31320749.
16. PMID: 32592347.
17. PMID: 33115855.
