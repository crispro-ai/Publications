# Mechanistic therapy ranking of synthetic lethality targets predicts platinum response in ovarian cancer

**Target Journal:** Nature Medicine (Impact Factor: 82.9)
**Submission Status:** Draft (Ready for Internal Review)
**Data Provenance:** TCGA-OV (n=149), 100-Case Labeled Benchmark

---

## Abstract

**Background:** Synthetic lethality (SL) offers a powerful framework for precision oncology, yet clinical translation beyond BRCA1/2 remains limited by the lack of robust, reproducible therapy ranking systems. Here, we validate a deterministic sequence-pathway (S/P) pipeline that integrates lineage-aware dependency grounding and literature augmentation to rank SL vulnerabilities from tumor mutations.

**Methods:** We developed an S/P scoring system that consumes somatic mutation profiles and produces ranked SL-relevant therapies (PARP, ATR, and WEE1 inhibitors). The system functionalizes lineage-aware DepMap dependency data and uses a literature-backed "E-component" for confidence augmentation. We evaluated the system's structural soundness on a curated 100-case benchmark and its clinical predictive value on a retrospective ovarian cancer cohort (TCGA-OV, n=149) with established platinum response labels.

**Results:** In the 100-case benchmark, the system achieved **92.9% Drug@1 accuracy** (95% CI 85.7–98.6%) and a **0% false-positive rate** (95% CI 0.0–0.0%), significantly outperforming a 90-gene rule-based baseline (Drug@1 = 64.3%, FP = 33.3%). Ablation studies confirmed that the integration of sequence (S) and pathway (P) components is essential, as component-only performance collapsed to 18.6%. Critically, in the clinical TCGA-OV cohort, the system's mechanistically derived scores predicted platinum response with an **AUROC of 0.70** (n=149), providing repective evidence that the SL-ranking logic captures clinically relevant mechanistic signals of treatment sensitivity.

**Conclusions:** A lineage-grounded, deterministic SL ranking pipeline provides a rigorous foundation for precision therapy selection. The 0% false-positive rate and clinical predictive signal in ovarian cancer support the implementation of these "mechanistic floors" in decision support systems to prevent over-calling while identifying high-confidence SL vulnerabilities.

---

## 1. Introduction

Synthetic lethality (SL) is a hallmark of precision oncology, exemplified by PARP inhibitors in HRR-deficient tumors. However, current clinical practice often relies on broad gene-panel rules that suffer from high false-positive rates and fail to capture the nuances of sequence disruption and lineage-specific dependencies. We propose a deterministic S/P/E pipeline that establishes a "mechanistic floor" for SL therapy ranking, constrained to high-confidence targets (PARP, ATR, WEE1) to maximize clinical utility.

## 2. Results

### 2.1 Clinical Validation in Ovarian Cancer (TCGA-OV)
We applied the SL-ranking pipeline to mutation profiles from 149 patients in the TCGA-OV cohort. Since platinum sensitivity is a clinical surrogate for homologous recombination deficiency (the primary mechanism targeted by SL therapies like PARP inhibitors), we evaluated the system's ability to predict platinum response. The system's mechanistic scores achieved an **AUROC of 0.70** for predicting platinum resistance (n=149, 125 sensitive, 24 resistant). This demonstrates that the pipeline captures real-world clinical signals of mechanistic vulnerability, even in a retrospective setting.

### 2.2 Structural Soundness and False-Positive Control
On a curated 100-case benchmark, the system demonstrated exceptional structural soundness:
- **Accuracy**: 92.9% Drug@1 accuracy.
- **Safety**: 0% false-positive rate on SL-negative cases, addressing the critical clinical challenge of "over-calling" SL therapies.
- **Comparison**: Outperformed a credible rule-based threat (DDR genes) which had a 33.3% false-positive rate.

### 2.3 Necessity of S/P Integration
Ablation studies revealed that sequence (S) and pathway (P) integration is non-negotiable. Disabling either component resulted in a performance collapse to 18.6%, showing that the system requires both fine-grained sequence disruption scoring (Evo2) and high-level pathway alignment to function.

### 2.4 Lineage-Aware Grounding as a Safety Net
By functionalizing DepMap lineage data as a scoring term, the system implements a "safety net" against lineage-inappropriate predictions. Lineage-specific penalties suppressed ATR inhibitor predictions in contexts where baseline dependency was low, ensuring that recommendations are biologically grounded in the specific tumor type.

## 3. Methods

### 3.1 S/P/E Pipeline
- **S (Sequence)**: Evo2 foundation model scores sequence disruption (delta scores).
- **P (Pathway)**: Maps mutations to functional pathways and targets backup vulnerabilities.
- **E (Evidence)**: Literature augmentation (PMIDs) used as a confidence resolver and tie-breaker.
- **Grounding**: Functional integration of lineage-aware DepMap CRISPR gene effect data.

### 3.2 Evaluation
Performance was measured using top-1 drug accuracy and false-positive rates with 95% bootstrap confidence intervals. Clinical prediction was evaluated using AUROC on the TCGA-OV cohort.

---

## 4. Discussion and Limitations
The current system focuses on a highly controlled drug panel (PARP, ATR, WEE1) to establish robust mechanistic separation. While successful in ovarian cancer, future work will expand this framework to broader drug classes while maintaining the 0% false-positive rigor. The literature augmentation (E) component serves as a layer of augmentation rather than a limitation, positioning the mechanistically derived scores as the foundation for future evidentiary growth.

---

## 5. Supplementary Data
- **Supplement 1**: 100-case benchmark results and receipts (`results/publication_suite_20251230_192215.json`).
- **Supplement 2**: TCGA-OV retrospective report (`oncology-backend-minimal/scripts/validation/out/ddr_bin_tcga_ov/report.json`).
