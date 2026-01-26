# Sparse Autoencoder Features from Evo2 for Platinum Resistance Prediction in Ovarian Cancer: A Validation Study with Critical Findings

**Authors:** [To be determined]

**Affiliations:** [To be determined]

**Corresponding Author:** [To be determined]

**Status:** ⚠️ **DRAFT - CRITICAL VALIDATION FINDINGS** 

**Important Note:** This manuscript documents a critical validation finding: initial results (AUROC 0.783) were invalidated due to data leakage. Corrected nested cross-validation reveals weak signal (AUROC 0.555) that does not meet publication thresholds. This draft serves as a cautionary example of the importance of rigorous validation methodology. Results require re-evaluation before publication.

---

## Abstract

**Background:** Resistance prediction in cancer typically relies on gene-level markers that treat all variants of the same gene identically. We explored whether sparse autoencoder (SAE) features extracted from protein language model (Evo2) activations could predict platinum resistance with improved accuracy and interpretable biological coherence.

**Methods:** We extracted SAE features from Evo2 layer-26 activations for 1,498 somatic variants across 149 TCGA ovarian cancer patients with platinum response labels (24 resistant/refractory, 125 sensitive). We identified 9 "diamond" features with large effect sizes (Cohen's d > 0.5, p < 0.05) that were elevated in resistant patients. We aggregated these features into DDR_bin (DNA Damage Repair pathway bin) based on gene enrichment analysis and trained a logistic regression classifier using 29 top features. We compared against a gene-level baseline (PROXY SAE) using DDR gene mutation counts.

**Results:** Initial analysis using standard 5-fold cross-validation with pre-selected features reported AUROC 0.783 ± 0.100 for TRUE SAE (29 features) vs. 0.628 ± 0.119 for PROXY SAE (DDR gene count). However, nested cross-validation (with feature selection inside CV folds) revealed significant data leakage, with corrected AUROC dropping to 0.478 ± 0.028 (worse than random). Testing pre-selected 9 diamond features with nested CV showed weak signal: AUROC 0.555 ± 0.146 with MAX aggregation vs. 0.463 ± 0.092 with MEAN aggregation. All 9 diamond features mapped to the DDR pathway, with TP53 as the dominant gene. DDR_bin scores were significantly higher in resistant patients (mean 0.160 vs 0.066, p = 0.0020, Cohen's d = 0.642).

**Conclusions:** Initial results were inflated by 30.5 percentage points due to data leakage in feature selection. Corrected nested CV validation reveals weak signal (AUROC 0.555) that is not publication-worthy for resistance prediction (threshold AUROC ≥0.65). MAX aggregation outperforms MEAN (0.555 vs 0.463), suggesting resistance may be driven by worst variants rather than average. The coherent DDR pathway mapping provides biological interpretability, but variant-level SAE features do not provide clinically meaningful resistance prediction in this cohort. **These findings highlight the critical importance of proper validation methodology and suggest alternative approaches (survival prediction, gene-level aggregation) may be more appropriate.**

**Keywords:** sparse autoencoder, protein language model, Evo2, platinum resistance, ovarian cancer, DNA damage repair, interpretable machine learning, nested cross-validation, data leakage

**Status:** ⚠️ **DRAFT - CRITICAL VALIDATION FINDINGS** - Results require re-evaluation before publication

---

## Introduction

Chemotherapy resistance remains a major obstacle in cancer treatment, with platinum resistance affecting approximately 25-30% of ovarian cancer patients within 6 months of initial therapy [1]. Current resistance prediction approaches rely primarily on gene-level markers—identifying mutations in known resistance genes such as TP53, BRCA1/2, or pathway-specific alterations [2,3]. While clinically useful, these approaches treat all variants of the same gene identically, ignoring variant-specific structural and functional differences that may impact resistance mechanisms.

Protein language models (PLMs) have emerged as powerful tools for understanding protein function and variant effects [4,5]. Models such as ESM-2 [6] and Evo2 [7] learn rich representations of protein sequences that capture evolutionary constraints, structural features, and functional motifs. However, the internal representations of these models remain largely opaque—a "black box" that limits clinical interpretability and regulatory acceptance.

Sparse autoencoders (SAEs) offer a solution to this interpretability challenge [8,9]. By training on the internal activations of neural networks, SAEs decompose polysemantic representations into monosemantic features—individual dimensions that correspond to interpretable concepts [10]. In the context of protein language models, SAE features may capture biologically meaningful patterns such as DNA repair motifs, protein-protein interaction sites, or post-translational modification signals.

We hypothesized that SAE features extracted from Evo2 activations would provide variant-level resistance prediction superior to gene-level aggregation, while maintaining interpretable pathway-level coherence. To test this, we developed a pipeline to extract SAE features from Evo2 layer-26 activations for somatic variants in ovarian cancer patients with platinum response labels, compared predictive performance against gene-level baselines, and mapped significant features to biological pathways.

---

## Methods

### Data Source and Cohort

We obtained somatic mutation data and platinum response labels for high-grade serous ovarian cancer (HGSOC) patients from The Cancer Genome Atlas (TCGA-OV) [11]. Platinum response was defined according to Gynecologic Oncology Group criteria: sensitive (platinum-free interval ≥6 months) or resistant/refractory (platinum-free interval <6 months or progression during first-line treatment).

For TRUE SAE feature extraction, we processed 149 patients with complete mutation data through the Evo2 + SAE pipeline. The cohort comprised 125 sensitive, 17 refractory, and 7 resistant patients. We combined refractory and resistant patients (n=24) as the positive class based on clinical similarity and treatment implications.

### PROXY SAE (Gene-Level Baseline)

We implemented a gene-level pathway aggregation approach (PROXY SAE) as a baseline comparator. For each patient, we computed DDR pathway burden as the count of mutated DNA damage repair genes, normalized by a factor of 3:

```
DDR_burden = min(1.0, count(mutations in DDR_GENES) / 3.0)
```

DDR_GENES included: BRCA1, BRCA2, ATM, ATR, CHEK1, CHEK2, RAD51, PALB2, MBD4, MLH1, MSH2, MSH6, PMS2, TP53, RAD50, NBN, FANCA, FANCD2, BLM, WRN, RECQL4, PARP1, PARP2.

### TRUE SAE Feature Extraction

We extracted layer-26 activations from the Evo2 7B protein language model [7] for each somatic variant. Variant sequences were constructed by extracting 256bp flanking regions around each mutation site from the GRCh37 reference genome. Activations were processed through a pre-trained sparse autoencoder (Goodfire/Evo-2-Layer-26-Mixed) to obtain 32,768 sparse features per variant.

For each patient, we aggregated features across all variants by summation:

```
patient_feature[i] = Σ_v feature[i, v] for all variants v in patient
```

### Diamond Feature Selection

We identified "diamond" features—those with significant differential activation between resistant and sensitive patients—using the following criteria:

1. Effect size: Cohen's d > 0.5 (medium-large effect)
2. Direction: Higher mean activation in resistant/refractory patients
3. Significance: p < 0.05 (Mann-Whitney U test, uncorrected)

Nine features met all criteria. We mapped each feature to biological pathways by analyzing the gene distribution of the top 30 variants with highest feature activation.

### DDR_bin Aggregation

All 9 diamond features were enriched for DDR pathway genes, with TP53 as the dominant gene (28/30 top-activating variants for Feature 27607). We aggregated them into a single pathway-level score (DDR_bin):

```
DDR_bin = mean(Feature_1407, Feature_6020, Feature_9738, Feature_12893, 
               Feature_16337, Feature_22868, Feature_26220, Feature_27607, Feature_31362)
```

### Classification and Validation

**Initial Analysis (Standard CV):**
We initially trained logistic regression classifiers with balanced class weights using:
1. **PROXY SAE**: Single feature (DDR gene count)
2. **TRUE SAE**: 29 features (9 diamonds + 20 additional top features by effect size)

Performance was evaluated using stratified 5-fold cross-validation. **However, this initial analysis had a critical flaw: features were pre-selected on the full dataset before CV, causing data leakage.**

**Corrected Analysis (Nested CV):**
To properly validate performance, we implemented nested cross-validation:
- **Outer CV**: 5-fold stratified split for model evaluation
- **Inner CV**: Feature selection performed independently within each training fold only
- **Feature selection**: Mann-Whitney U test with FDR correction (p < 0.05, Cohen's d > 0.5)
- **Pre-selected features test**: Also tested the 9 diamond features with nested CV using both MEAN and MAX aggregation

This nested CV approach prevents data leakage by ensuring feature selection never uses test set information.

### Statistical Analysis

Differences in DDR_bin scores between resistant and sensitive groups were assessed using the Mann-Whitney U test. Effect sizes were computed as Cohen's d. All analyses were performed in Python 3.11 using scikit-learn 1.3, scipy 1.11, and numpy 1.24.

---

## Results

### Cohort Characteristics

The final cohort comprised 149 HGSOC patients: 125 sensitive (84%) and 24 resistant/refractory (16%) to platinum-based chemotherapy. Patients harbored a median of 10 somatic mutations per patient (range: 1-89), with 1,498 total variants across the cohort.

### Initial Results vs. Corrected Validation

**Initial Analysis (Standard CV with Pre-selected Features):**
Initial head-to-head comparison using 5-fold cross-validation with pre-selected features reported:

| Method | Mean AUROC | Std | Features | Status |
|--------|------------|-----|----------|--------|
| **PROXY SAE** | 0.628 | ±0.119 | 1 (DDR gene count) | Baseline |
| **TRUE SAE** | **0.783** | ±0.100 | 29 features | ❌ **INVALID** (data leakage) |

**However, this analysis had critical data leakage: features were selected on the full dataset before CV, inflating performance estimates.**

**Corrected Analysis (Nested CV):**
Nested cross-validation with proper feature selection isolation revealed:

| Method | Mean AUROC | Std | Features | Status |
|--------|------------|-----|----------|--------|
| **TRUE SAE (nested CV, feature selection)** | **0.478** | ±0.028 | 0-12 per fold | ❌ Worse than random |
| **TRUE SAE (nested CV, 9 diamonds, MEAN)** | **0.463** | ±0.092 | 9 (pre-selected) | ❌ Worse than random |
| **TRUE SAE (nested CV, 9 diamonds, MAX)** | **0.555** | ±0.146 | 9 (pre-selected) | ⚠️ Weak signal |

**Key Findings:**
1. Original AUROC 0.783 was inflated by **30.5 percentage points** due to data leakage
2. Corrected performance with feature selection: **0.478 (worse than random)**
3. Pre-selected 9 diamond features show **weak signal** (AUROC 0.555) with MAX aggregation
4. MAX aggregation outperforms MEAN (0.555 vs 0.463), suggesting resistance driven by worst variants
5. Signal is **not publication-worthy** for resistance prediction (AUROC < 0.65 threshold)

### Diamond Features Map Coherently to DDR Pathway

Nine features met our diamond criteria (Cohen's d > 0.5, higher in resistant, p < 0.05). Remarkably, all 9 features showed enrichment for DNA damage repair genes when analyzing their top-activating variants (Figure 4):

| Feature | Cohen's d | p-value | Top Genes |
|---------|-----------|---------|-----------|
| 27607 | 0.635 | 0.0146 | TP53 (28), UBAP2L (1) |
| 16337 | 0.634 | 0.0247 | TP53 (25), MYH1 (2) |
| 26220 | 0.609 | 0.0215 | TP53 (28), ENTPD3 (1) |
| 12893 | 0.597 | 0.0246 | TP53 (24), CDH10 (1) |
| 6020 | 0.573 | 0.0324 | TP53 (21), BRCA1 (3) |
| 22868 | 0.544 | 0.0355 | TP53 (22), ATM (5) |
| 1407 | 0.537 | 0.0414 | TP53 (48), MBD4 (15) |
| 9738 | 0.530 | 0.0495 | TP53 (16), CHEK2 (8) |
| 31362 | 0.517 | 0.0466 | TP53 (19), RAD51 (4) |

This coherent mapping to DDR genes provides biological interpretability: platinum drugs cause DNA damage, and restoration of DNA repair capacity (indicated by elevated DDR feature activation) enables tumor cells to survive treatment.

### DDR_bin Distinguishes Resistant from Sensitive Patients

The aggregated DDR_bin score showed significant separation between groups (Figure 3):

- **Resistant patients**: mean DDR_bin = 0.160 (SD = 0.155)
- **Sensitive patients**: mean DDR_bin = 0.066 (SD = 0.098)
- **Mann-Whitney U**: p = 0.0020
- **Cohen's d**: 0.642 (medium-large effect)

---

## Discussion

**Critical Validation Finding:** Our initial analysis reported AUROC 0.783 for TRUE SAE, suggesting significant outperformance over gene-level markers. However, nested cross-validation revealed this result was invalid due to data leakage in feature selection. Corrected validation shows weak signal (AUROC 0.555 with pre-selected features, MAX aggregation) that does not meet publication thresholds for resistance prediction (AUROC ≥0.65).

This finding highlights the critical importance of proper validation methodology. The 30.5 percentage point inflation demonstrates how data leakage can dramatically overestimate model performance, potentially leading to false clinical claims.

### Biological Coherence

A key finding is the coherent mapping of all 9 diamond features to the DDR pathway. This was not guaranteed—SAE features could have captured diverse, unrelated biological signals. Instead, the resistance-elevated features consistently activated most strongly on TP53 and other DDR gene variants. This coherence provides biological plausibility: platinum agents (carboplatin, cisplatin) cause DNA crosslinks, and tumor cells with enhanced DNA repair capacity can survive treatment. The SAE features appear to capture variant-specific signals related to DNA repair restoration.

### Variant-Level Representation

PROXY SAE treats all mutations in a gene identically—a TP53 p.R175H mutation receives the same pathway contribution as TP53 p.R273H or any other TP53 variant. TRUE SAE, by extracting features from the actual variant sequence context, can distinguish between variants. This variant-level specificity likely explains the performance improvement, as different variants within the same gene can have vastly different structural and functional consequences.

### Clinical Implications

If validated in prospective cohorts, TRUE SAE resistance prediction could inform treatment decisions:

1. **Treatment intensification**: Patients with high DDR_bin scores may benefit from more aggressive first-line therapy or earlier consideration of PARP inhibitors
2. **Monitoring**: DDR_bin tracking over time could provide early warning of resistance emergence
3. **Trial stratification**: Clinical trials could use DDR_bin for patient stratification

### Limitations

Several critical limitations must be acknowledged:

1. **Data leakage in initial analysis**: The original AUROC 0.783 was invalid due to feature selection on the full dataset before CV. This inflated performance by 30.5 percentage points.

2. **Weak predictive signal**: Corrected nested CV validation reveals AUROC 0.555 (MAX aggregation) or 0.478 (with feature selection), which is below the publication threshold (AUROC ≥0.65) for resistance prediction.

3. **Small sample size**: The positive class (24 resistant) is small, limiting statistical power. Events per variable ratio is marginal, increasing overfitting risk.

4. **High variance**: MAX aggregation shows high variance (±0.146), indicating model instability. Fold AUROCs range from 0.400 to 0.784, suggesting results may not generalize.

5. **Single-cohort validation**: All results are from TCGA-OV; external validation in independent cohorts is essential but not yet performed.

6. **Retrospective design**: Prospective validation is needed before any clinical claims can be made.

7. **Computational cost**: TRUE SAE extraction requires GPU compute (~$0.10-0.30 per patient), compared to zero cost for gene-level PROXY SAE.

8. **Feature interpretation**: While features map to DDR pathway, the precise biological mechanisms captured by individual features remain unclear.

9. **Aggregation method dependency**: Results are highly sensitive to aggregation method (MAX vs MEAN), suggesting the signal may be driven by outlier variants rather than consistent pathway activation.

### Generalizability

To assess whether pathway-based prediction generalizes beyond ovarian cancer, we examined published validation of PROXY SAE in multiple myeloma (MMRF CoMMpass, n=219). DIS3 mutation showed 2.08× higher mortality risk (p=0.0145), consistent with DDR pathway involvement in treatment resistance across cancer types. TRUE SAE extraction for MM remains future work.

---

## Conclusions

**Critical Validation Finding:** Initial analysis reported AUROC 0.783 for SAE features, suggesting outperformance over gene-level markers. However, nested cross-validation revealed this result was invalid due to data leakage, with corrected performance showing weak signal (AUROC 0.555 with MAX aggregation) that does not meet publication thresholds.

**Key Findings:**
1. **Data leakage impact**: Original AUROC inflated by 30.5 percentage points due to feature selection on full dataset
2. **Corrected performance**: AUROC 0.555 (MAX aggregation) or 0.478 (with feature selection) - below publication threshold (≥0.65)
3. **Biological coherence**: All 9 diamond features map to DDR pathway, providing interpretability
4. **Aggregation matters**: MAX outperforms MEAN (0.555 vs 0.463), suggesting resistance driven by worst variants
5. **Signal too weak**: Current variant-level SAE approach does not provide clinically meaningful resistance prediction

**Implications:**
- Proper validation methodology is critical - data leakage can dramatically inflate performance estimates
- Variant-level SAE features show weak signal for resistance prediction in this cohort
- Alternative approaches (survival prediction, gene-level aggregation, different outcomes) may be more appropriate
- Results are hypothesis-generating and require external validation before any clinical claims

**This study serves as a cautionary example of the importance of rigorous validation methodology in biomarker development.**

---

## Data Availability

TCGA-OV data are available from the Genomic Data Commons (https://portal.gdc.cancer.gov/). SAE features and analysis code will be made available upon publication at [GitHub repository URL].

---

## Code Availability

Analysis scripts are available at: [GitHub repository URL]

Key scripts:
- `scripts/publication/head_to_head_proxy_vs_true.py` - AUROC comparison
- `scripts/publication/generate_roc_curves.py` - Figure 2
- `scripts/publication/generate_ddr_bin_distribution.py` - Figure 3
- `scripts/publication/generate_feature_pathway_mapping.py` - Figure 4
- `scripts/validation/validate_true_sae_diamonds.py` - Reproducibility validation

---

## Author Contributions

[To be determined]

---

## Competing Interests

[To be determined]

---

## References

[1] Lheureux S, et al. Epithelial ovarian cancer: Evolution of management in the era of precision medicine. CA Cancer J Clin. 2019;69(4):280-304.

[2] Patch AM, et al. Whole-genome characterization of chemoresistant ovarian cancer. Nature. 2015;521(7553):489-494.

[3] Konstantinopoulos PA, et al. Homologous recombination deficiency: exploiting the fundamental vulnerability of ovarian cancer. Cancer Discov. 2015;5(11):1137-1154.

[4] Meier J, et al. Language models enable zero-shot prediction of the effects of mutations on protein function. Adv Neural Inf Process Syst. 2021;34:29287-29303.

[5] Brandes N, et al. Genome-wide prediction of disease variant effects with a deep protein language model. Nat Genet. 2023;55(9):1512-1522.

[6] Lin Z, et al. Evolutionary-scale prediction of atomic-level protein structure with a language model. Science. 2023;379(6637):1123-1130.

[7] Nguyen E, et al. Evo: Generative genomic foundation models. bioRxiv. 2024.

[8] Bricken T, et al. Towards monosemanticity: Decomposing language models with dictionary learning. Anthropic. 2023.

[9] Cunningham H, et al. Sparse autoencoders find highly interpretable features in language models. ICLR. 2024.

[10] Templeton A, et al. Scaling monosemanticity: Extracting interpretable features from Claude 3 Sonnet. Anthropic. 2024.

[11] Cancer Genome Atlas Research Network. Integrated genomic analyses of ovarian carcinoma. Nature. 2011;474(7353):609-615.

