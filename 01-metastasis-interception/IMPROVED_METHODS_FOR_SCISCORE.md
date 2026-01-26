## METHODS

### Platform Architecture

#### Multi-Modal Integration Framework

We developed a multi-modal CRISPR guide design platform integrating three state-of-the-art machine learning models: Evo2 (sequence modeling), Enformer (chromatin accessibility), and AlphaFold3 (structural validation). The platform orchestrates these models through a unified API to generate stage-specific anti-metastatic CRISPR therapeutics.

**Evo2 Sequence Oracle (9.3T tokens):** We employed the Evo2-7B model (Arc Institute, 2024), a genomic foundation model trained on 9.3 trillion tokens spanning all domains of life¹². Evo2 uses StripedHyena 2 architecture with 1M token context window and single-nucleotide resolution. We deployed Evo2 via Modal cloud infrastructure (A100 GPUs, 64GB RAM per instance) for on-demand variant scoring and guide generation. Evo2 model versions were locked to `evo2_1b`, `evo2_7b`, and `evo2_40b` for reproducibility.

**Enformer Chromatin Prediction:** We deployed DeepMind's Enformer model (Avsec et al., 2021) as a FastAPI web service on Modal and queried it during dataset regeneration via `ENFORMER_URL`. For each gene in the 38-gene validation universe, we evaluated chromatin at the gene transcription start site (TSS) obtained via Ensembl symbol lookup (GRCh38). For each query, the service fetches the required 393,216 bp reference sequence window from Ensembl REST centered at the TSS and runs Enformer inference. Because Enformer outputs thousands of tracks, we report an accessibility proxy by averaging model outputs in the central bins and applying a logistic transform to map to [0,1]. All chromatin outputs carry provenance (`method=deepmind_enformer_tfhub`) and are audited in `publication/data/chromatin_audit_enformer_38genes.csv` (with the frozen TSS map in `publication/data/gene_tss_grch38_38genes.csv`).

**Structural Validation (AlphaFold 3 Server):** We validated guide RNA:DNA complex structures using the AlphaFold 3 Server JSON API (Google DeepMind, 2024)¹³. For each guide, we constructed a biomolecular assembly comprising (i) a 96-nucleotide RNA molecule (20nt spacer + 76nt scaffold) and (ii) a 60-basepair double-stranded DNA target sequence. Assemblies were submitted as JSON specifications via the AlphaFold Server web interface, which performs MSA generation, template search, and structure prediction internally.

**Quality Metrics:** We extracted four confidence metrics from AlphaFold 3 outputs: (i) **pLDDT** (per-residue confidence, 0-100), averaged across all residues; (ii) **iPTM** (interface predicted TM-score, 0-1), quantifying interface quality; (iii) **fraction_disordered** (fraction of residues with pLDDT <50); and (iv) **has_clash** (binary flag for steric conflicts).

**Acceptance Criteria (RNA-DNA Specific):** We established revised acceptance thresholds tailored to RNA-DNA hybrid dynamics: pLDDT ≥50 (ordered structure), iPTM ≥0.30 (sufficient interface confidence), disorder <50% (majority ordered), and no clashes. These criteria reflect the inherently greater conformational flexibility of RNA-DNA hybrids compared to protein-protein interfaces (typical iPTM 0.3-0.5 vs 0.6-0.9 for proteins)¹³. Our thresholds were calibrated based on the reported iPTM ranges for nucleic acid complexes¹³, not as a recommendation from AlphaFold authors. Guides meeting all four criteria were classified as "PASS."

**Validation Cohort:** We validated 15 guide:DNA complexes representing the top 2 guides per metastatic step (8 steps total). All structures were predicted within 5-10 minutes per job. Complete structural data (mmCIF files, confidence JSONs, PAE matrices) are archived in Supplementary Data S1.

#### Target-Lock Scoring Algorithm

**Multi-Signal Integration:** The Target-Lock score aggregates four biological signals per gene per metastatic step:

```
Target_Lock = 0.35×Functionality + 0.35×Essentiality + 0.15×Chromatin + 0.15×Regulatory
```

**Functionality (Evo2 protein impact):** Protein functionality change was predicted using Evo2 multi-window scoring. For each missense variant, we computed `delta_likelihood_score` across 8192bp context windows and exon-specific contexts. Functionality score = `1 / (1 + exp(-delta/10))`, mapping negative deltas (disruptive) to high scores [0,1].

**Essentiality (Evo2 gene-level):** Gene essentiality integrated truncation-impact analysis with Evo2 magnitude scoring. For frameshifts and nonsense mutations, we assigned essentiality=1.0 deterministically. For missense variants, we computed aggregate Evo2 delta magnitude across gene exons and normalized to [0,1] using gene-specific calibration (see Calibration section).

**Chromatin (Enformer accessibility):** Chromatin accessibility was computed using Enformer (Modal-deployed, audited) at gene transcription start sites. For each gene in the 38-gene validation universe, we evaluated chromatin at the TSS obtained via Ensembl symbol lookup (GRCh38). The service fetches the required 393,216 bp reference sequence window from Ensembl REST centered at the TSS and runs Enformer inference. Chromatin contributes only 15% weight to Target-Lock; ablation analysis shows that removing chromatin (3-signal approach) achieves AUROC 0.989 ± 0.017, demonstrating robustness of the core signals (Functionality 35%, Essentiality 35%, Regulatory 15%).

**Regulatory (Evo2 noncoding impact):** Regulatory impact for noncoding/splice variants was estimated using Evo2 minimum delta across multi-window contexts. Regulatory score = `|min_delta| / (|min_delta| + 1)`, capturing splicing disruption magnitude.

#### Gene-Specific Calibration

To enable cross-gene comparison, we implemented gene-specific percentile calibration. For each gene, we precomputed a calibration snapshot by scoring 10,000 random missense variants and mapping raw Evo2 deltas to percentile ranks [0,1]. During prediction, raw scores were transformed to calibrated percentiles using the gene's snapshot. Calibration snapshots were stored with provenance (seed=42, n=10,000, computation date) and versioned for reproducibility.

#### Guide RNA Design & Efficacy Prediction

**PAM Site Identification:** We scanned target genes for NGG PAM sites (SpCas9) and extracted 20bp spacer sequences upstream of each PAM. For each candidate spacer, we extracted ±150bp genomic context (300bp total) to provide Evo2 with sufficient information for contextual scoring.

**Evo2 Efficacy Scoring:** Guide efficacy was predicted using Evo2 delta scoring on the spacer-in-context. We computed `delta_likelihood_score` comparing spacer sequence to genomic background and transformed via sigmoid: `efficacy = 1 / (1 + exp(delta/10))`. Higher delta magnitude (indicating sequence disruption) correlated with higher predicted efficacy.

**Off-Target Safety Validation:** Genome-wide off-target search employed minimap2 (RRID:SCR_018550) for rapid alignment followed by BLAST (RRID:SCR_004870) for mismatch quantification. For each guide, we identified all GRCh38 sites with ≤3 mismatches and computed safety score via exponential decay: `safety = exp(-0.5 × total_off_target_hits)`. This penalizes guides with multiple near-perfect off-target matches.

**Mission-Fit Weighting:** For stage-specific design, we weighted guides by their relevance to target step. Guides targeting primary_genes (core drivers) received weight=1.0; secondary_genes received weight=0.5. Mission-fit = weighted mean of Target-Lock scores for genes hit by the guide.

**Assassin Score (Composite Ranking):** Final guide ranking integrated efficacy, safety, mission-fit, and structural confidence:

```
Assassin = 0.37×Efficacy + 0.30×Safety + 0.30×Mission + 0.03×Structure
```

Structural confidence (+0.03 bounded lift) was applied only to guides passing AlphaFold3 validation criteria.

### Validation Strategy

#### Sample Size Justification and Power Analysis

**Primary Validation Cohort:** We selected 38 primary metastatic genes based on FDA oncology approvals and clinical trial enrollment (NCT IDs), yielding 304 gene-step combinations (38 genes × 8 steps). This sample size was determined by: (1) clinical relevance (all genes have FDA-approved metastatic cancer indications), (2) statistical power (50 positive labels across 304 combinations provides 16% positive rate, sufficient for AUROC estimation with bootstrap CIs), and (3) practical constraints (computational cost of Evo2 scoring scales with gene count). No formal power calculation was performed as this is a validation study of an existing scoring system rather than a hypothesis-testing study. The 38-gene set represents the current clinical gold standard for stage-specific metastatic drivers.

**Structural Validation Cohort:** We validated 15 guide:DNA complexes (top 2 per step) to balance AlphaFold 3 Server computational costs with statistical power. This sample size was selected to: (1) provide coverage across all 8 metastatic steps, (2) enable per-step structural quality assessment, and (3) demonstrate structural validation feasibility at publication scale. With 15 guides and 100% pass rate, we can reject the null hypothesis (pass rate <50%) with p<0.001 (binomial test, one-tailed).

**Hold-Out Validation:** We split the 38-gene set into 28 training and 10 test genes (stratified by metastatic step) to assess generalization. The 10-gene test set size was constrained by the total gene count but provides sufficient data for AUPRC estimation (test AUPRC 0.790 with 95% CI).

**Prospective Validation:** We analyzed 11 newly FDA-approved metastatic targets (2024-2025) plus 8 negative controls (19 genes total, 152 data points). This sample size was determined by the number of FDA approvals in the specified time window and provides sufficient power for discrimination analysis (AUROC 1.000, AUPRC 1.000).

#### Inclusion and Exclusion Criteria

**Gene Selection Criteria (Primary Validation):**
- **Inclusion:** Genes with FDA-approved metastatic cancer indications or active Phase III clinical trials with metastatic endpoints (NCT IDs documented)
- **Exclusion:** Genes without explicit metastatic indication, genes with only early-stage approvals, non-gene-targeted therapies (immunotherapies, cell therapies)

**Prospective Validation Gene Selection:**
- **Inclusion:** FDA-approved gene-targeted oncology drugs (January 2023 - December 2025) with explicit metastatic indication
- **Exclusion:** Genes already in 38-gene training set (e.g., MET), non-metastatic indications, immunotherapies, cell therapies

**Structural Validation Guide Selection:**
- **Inclusion:** Top 2 guides per metastatic step based on Assassin score (efficacy + safety + mission-fit)
- **Exclusion:** Guides with off-target hits >10, guides targeting non-primary genes

#### Per-Step ROC/PR Analysis

We validated Target-Lock scores against 38 primary metastatic genes curated from FDA oncology approvals and clinical trials (see Supplementary Table S1 for NCT IDs and PMIDs). The ground truth comprises 38 genes from `metastasis_rules_v1.0.1.json`, yielding 304 gene-step combinations (38 genes × 8 steps). For validation, we focused on 304 primary gene-step combinations (38 primary genes × 8 steps) to minimize label noise from secondary/indirect mechanisms. Of these 304 combinations, 50 represent positive labels (genes mechanistically essential for a given step, e.g., MMP2/MMP9 for local_invasion, BRAF/KRAS/MET for metastatic_colonization), resulting in a 16% positive rate (50/304) typical of highly selective pathway analyses.

**Dataset Circularity Mitigation:** To address potential circularity (genes selected for strong Evo2 signal), we: (1) curated genes based on clinical trial enrollment (NCT IDs) and FDA approvals, not computational signal; (2) validated that gene selection preceded Target-Lock score computation; (3) performed confounder analysis showing minimal correlation (ρ<0.3) between Target-Lock scores and gene properties (length, GC%, exon count); and (4) computed effect sizes (Cohen's d) to quantify practical significance beyond p-values. We further addressed circularity through three complementary validation strategies: **Hold-out validation** (28 train / 10 test genes) demonstrating generalization to unseen genes (see `HOLDOUT_VALIDATION_RESULTS.md`); **External dataset validation** using TCGA-OV metastasis-associated genes (see `TCGA_EXTERNAL_VALIDATION_RESULTS.md`); and **Prospective validation** on 11 newly FDA-approved metastatic cancer targets (2024-2025) not present in the original training set, achieving AUPRC 1.000 and Precision@3 = 1.000 (see `PROSPECTIVE_VALIDATION_RESULTS.md`). All validation results are archived in the `data/` directory with complete provenance.

For each step, we computed:
- **AUROC/AUPRC:** Area under ROC and precision-recall curves with 5,000-bootstrap 95% confidence intervals (seed=42, stratified resampling) using scikit-learn v1.3.0 (RRID:SCR_019053).
- **Precision@K:** Precision at K=3,5,10 top-ranked genes, representing clinical decision thresholds (limited validation capacity).
- **Calibration Curves:** Reliability diagrams showing predicted score vs observed frequency in 5 quantile bins per step.

#### Specificity Matrix

To assess step-specificity, we constructed an 8×8 confusion matrix comparing predicted step assignment (step with highest Target-Lock score) to true step assignment (ground truth labels). Diagonal dominance (ratio of correct assignments) quantified step-specific signal. Fisher's exact test computed enrichment p-values for each step using scipy.stats v1.11.0 (RRID:SCR_008058).

#### Effect Size Analysis

For each biological signal (functionality, essentiality, chromatin, regulatory), we computed Cohen's d effect sizes comparing relevant vs non-relevant genes per step:

```
d = (mean_relevant - mean_non_relevant) / pooled_std
```

Effect sizes quantified practical significance beyond p-values: |d|<0.2 (negligible), <0.5 (small), <0.8 (medium), ≥0.8 (large). All effect size calculations used numpy v1.24.0 (RRID:SCR_008633) and pandas v2.0.0 (RRID:SCR_018214).

#### Ablation Study

To rank signal importance, we performed leave-one-out ablation. For each signal, we recomputed Target-Lock scores with that signal set to zero and measured AUROC drop per step. Signals with larger AUROC drops contribute more information.

#### Confounder Analysis

We tested for confounding by gene properties (length, GC content, exon count) via Spearman's rank correlation (scipy.stats.spearmanr, RRID:SCR_008058) with Target-Lock scores. Spearman correlation assumptions were verified: (1) data are at least ordinal scale (gene properties are continuous), (2) variables represent paired observations (each gene has both property and score), (3) monotonic relationship assumption (no significant outliers detected via visual inspection). Correlations ρ<0.3 indicated minimal confounding. All correlation coefficients (ρ), p-values, and degrees of freedom are reported in Supplementary Table S2.

### Computational Infrastructure & Reproducibility

All analyses were performed on Modal cloud platform with fixed random seeds (seed=42 throughout) to ensure reproducibility. Evo2 predictions used locked model IDs (`evo2_1b`, `evo2_7b`, `evo2_40b`) with deterministic inference. Evo2 service was accessed via `https://crispro--evo-service-evoservice1b-api-1b.modal.run` for variant scoring endpoints (`/score_variant_multi`, `/score_variant_exon`). Gene coordinates (GRCh38) were validated against Ensembl canonical transcripts (RRID:SCR_002344) and cached for reproducibility (see `GENE_COORDINATES_SOLUTION.md`). Enformer and AlphaFold3 containers were pinned to specific digests (see Supplementary Methods for exact hashes).

**Code Availability:** Complete source code, configuration files, and reproduction scripts are available at GitHub (https://github.com/[URL_TO_BE_ADDED_UPON_ACCEPTANCE]) and will be archived with a permanent DOI on Zenodo upon manuscript acceptance. The one-command reproduction script (`./scripts/reproduce_all_resubmission.sh`) enables full replication of all analyses in <10 minutes on a standard workstation.

**Protocol Information:** Detailed step-by-step reproduction protocols are provided in `REPRODUCIBILITY.md` (included in Supplementary Data). The reproduction script (`./scripts/reproduce_all_resubmission.sh`) executes the complete analysis pipeline: (1) environment setup (Python 3.10+, virtual environment creation), (2) dependency installation (requirements.txt), (3) data staging (ground truth files), (4) validation metric computation (per-step ROC/PR, specificity, precision@K, ablation, confounders), (5) enhanced validation (calibration curves, effect sizes, tables), and (6) hold-out validation. All scripts are version-controlled and include inline documentation.

### Statistical Analysis

All statistical tests were two-tailed with α=0.05. Statistical analyses were performed using Python 3.10 with the following packages: scikit-learn v1.3.0 (RRID:SCR_019053) for machine learning metrics (AUROC, AUPRC, precision@K), scipy.stats v1.11.0 (RRID:SCR_008058) for statistical tests (Fisher's exact test, Spearman correlation, bootstrap resampling), numpy v1.24.0 (RRID:SCR_008633) for numerical computations, and pandas v2.0.0 (RRID:SCR_018214) for data manipulation.

**Bootstrap Confidence Intervals:** Bootstrap confidence intervals used percentile method (2.5%, 97.5%) with 5,000 iterations for tight confidence intervals. Stratified bootstrap resampling was employed to maintain class balance (positive/negative labels) across resamples. All bootstrap analyses used fixed random seed (seed=42) for reproducibility.

**Multiple Testing Correction:** Multiple testing correction was not applied given exploratory nature of per-step analyses (8 comparisons), but Bonferroni-corrected p-values are reported in Supplementary Materials. Effect sizes are reported alongside p-values to assess practical significance.

**Spearman's Rank Correlation:** Spearman correlation was used to test for confounding by gene properties (length, GC content, exon count). Assumptions were verified: (1) data are at least ordinal scale (all variables are continuous), (2) variables represent paired observations (each gene has both property and Target-Lock score), (3) monotonic relationship with no significant outliers (verified via visual inspection of scatter plots). Correlation coefficients (ρ), degrees of freedom (df), exact p-values, and sample sizes (n) are reported for all correlations in Supplementary Table S2.

**Fisher's Exact Test:** Fisher's exact test was used to compute enrichment p-values for step-specificity analysis. All p-values, odds ratios, and 95% confidence intervals are reported in Supplementary Table S2.

### Bias Reduction and Blinding

As a computational study without experimental subjects, traditional blinding procedures (investigator blinding, subject blinding) are not applicable. However, we implemented several bias reduction strategies: (1) **Automated scoring:** All Target-Lock scores were computed using deterministic algorithms with fixed random seeds, eliminating human bias in score assignment; (2) **Pre-specified criteria:** Structural acceptance criteria (pLDDT ≥50, iPTM ≥0.30) were established before structural validation, preventing post-hoc threshold adjustment; (3) **Independent validation:** Hold-out, external (TCGA), and prospective validations were performed on datasets independent of the primary validation set, reducing overfitting risk; (4) **Automated analysis:** All statistical tests and metric computations were performed programmatically using versioned scripts, eliminating manual calculation errors.

### Research Use Only (RUO) Disclaimer

This computational framework is for research purposes only and has not been validated for clinical use. All predictions require experimental validation before therapeutic application.

## DATA AVAILABILITY

All data, code, and structural files are publicly available. Files are organized by submission category:

### Code Repository
- **GitHub**: https://github.com/[URL_TO_BE_ADDED_UPON_ACCEPTANCE]
- **Zenodo DOI**: [DOI to be added upon acceptance]
- **Reproduction Script**: `scripts/reproduce_all_resubmission.sh` (in publication directory; one-command reproduction)
- **Model Versions**: Evo2 (evo2_1b, evo2_7b), AlphaFold 3 Server API v1.0

### Supplementary Data S1: Structural Validation
**Upload as: "Supplementary Data"**

15 guide:DNA complex structures with complete confidence metrics:
- 15 mmCIF structure files (`.cif`)
- 15 confidence JSON files (pLDDT, iPTM, PAE metrics)
- 15 PAE matrix JSON files
- Summary: `structural_validation/structural_metrics_summary.csv`
- Per-guide directories: `structural_validation/[guide_name]/` (15 guides total)
- Guide validation dataset: `data/real_guide_validation_dataset.csv` - Complete guide sequences with structural metrics (pLDDT, iPTM, structural_confidence, structural_verdict) for all designed guides

**Guides validated:** BRAF_04, BRAF_14, TWIST1_10, TWIST1_11, MMP2_07, MMP2_08, BCL2_12, BCL2_13, ICAM1_00, ICAM1_01, CXCR4_03, CXCR4_06, VEGFA_02, VEGFA_05, MET_09

### Supplementary Data S2: Validation Datasets
**Upload as: "Supplementary Data"**

**Primary Validation (38 genes, 304 data points):**
- `data/real_target_lock_data.csv` - Complete Target-Lock scores (38 genes × 8 steps, all 4 signals)
- `data/per_step_validation_metrics.csv` - AUROC/AUPRC per step (8 steps)
- `data/precision_at_k.csv` - Precision@K rankings (K=3,5,10)
- `data/ablation_study.csv` - Signal importance (3-signal vs 4-signal)
- `data/effect_sizes.csv` - Cohen's d effect sizes
- `data/confounder_analysis.csv` - Gene property correlations
- `data/specificity_enrichment.csv` - Step-specificity matrix
- `data/target_lock_heatmap_data.csv` - Heatmap data

**Hold-Out Validation (28 train / 10 test):**
- `data/holdout_train_test_split.json` - Gene split
- `data/holdout_validation_metrics.csv` - Training/test metrics
- `HOLDOUT_VALIDATION_RESULTS.md` - Complete report

**External Validation (TCGA):**
- `TCGA_EXTERNAL_VALIDATION_RESULTS.md` - Complete TCGA analysis

**Prospective Validation (11 FDA-approved genes + 8 negatives, 152 data points):**
- `data/prospective_validation_genes_agent.csv` - 11 FDA-approved genes (2024-2025)
- `data/prospective_validation_target_lock_scores.csv` - Scores (11 genes × 8 steps)
- `data/prospective_validation_with_negatives_scores.csv` - Scores with negatives (19 genes × 8 steps)
- `data/prospective_validation_with_negatives_labels.csv` - Labels with negatives
- `data/prospective_validation_with_negatives_metrics.json` - Metrics (AUROC 1.000, AUPRC 1.000)
- `PROSPECTIVE_VALIDATION_RESULTS.md` - Complete report
- `FDA_APPROVAL_SELECTION_ANALYSIS.md` - Selection process

**Ground Truth:**
- `oncology-coPilot/oncology-backend-minimal/api/config/metastasis_interception_rules.json` - 38 genes with NCT IDs and PMIDs

### Figures
**Upload as: "Figure" (one file per figure)**

**Main Figures:**
- Figure 1: `figures/Kiani_Figure1.png` / `.svg` - Main workflow diagram
- Figure 2: `figures/F2_REAL_target_lock_heatmap.png` / `.svg` - Target-Lock heatmap
- Figure 3: `figures/figure_6_structural_validation.png` / `.svg` - Structural validation
- Figure 4: `figures/figure2a_per_step_roc.png` / `.svg` - Per-step ROC curves
- Figure 5: `figures/figure2b_specificity_matrix.png` / `.svg` - Specificity matrix
- Figure 6: `figures/figure2c_precision_at_k.png` / `.svg` - Precision@K
- Figure 7: `figures/figure2d_ablation.png` / `.svg` - Ablation study

**Supplementary Figures:**
- Figure S1: `figures/figure_s1_confounders.png` / `.svg` - Confounder analysis
- Figure S2: `figures/figure_s2_calibration_curves.png` / `.svg` - Calibration curves
- Figure S3: `figures/figure_s3_effect_sizes.png` / `.svg` - Effect sizes

**Figure Legends:** `figures/LEGENDS.md`

### Tables
**Upload as: "Table" (one file per table)**

- Table 1: `figures/publication/TABLE1_COMPETITIVE_COMPARISON.md` - Competitive comparison
- Table 2: `tables/table2_performance_metrics.csv` / `.tex` - Performance metrics
- Table S2: `tables/table_s2_validation_metrics.csv` / `.tex` - Validation metrics (per-step)
- Table S3: `data/prospective_validation_genes_agent.csv` - Prospective validation genes
- Table S4: `tables/table_s4_structural_validation.csv` / `.tex` - Structural validation details

### Supplementary Methods
**Upload as: "Supplementary Data (for Review only)"**

- `supplementary/structural_validation_details.md` - Detailed structural validation methodology
- `supplementary/terms_of_use.md` - AlphaFold 3 terms of use
- `REPRODUCIBILITY.md` - Complete reproduction instructions

### Supporting Documentation
**Upload as: "Supplementary Data (for Review only)" or include in code repository**

- `DATA_AND_SUPPLEMENTS.md` - Complete file inventory
- `PEER_REVIEW_RESPONSES.md` - Peer review responses
- `VALIDATION_STRATEGY.md` - Validation strategy documentation
- `GENE_COORDINATES_SOLUTION.md` - Gene coordinate validation
- `EVO2_SERVICE_URL_FINDINGS.md` - Evo2 API integration

All data are provided under Creative Commons Attribution 4.0 International License (CC BY 4.0).
