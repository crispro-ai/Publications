# Editor Fixes for Cancer Research Communications

**MS# CRC-26-0061**  
**Issues to Address:**
1. Table S1 legend missing
2. Figure labels and table titles missing

---

## 1. Table S1 Legend

**Table S1: 38 Primary Metastatic Genes with Clinical Trial Evidence**

This table lists the 38 primary metastatic genes used for Target-Lock validation, including their associated clinical trial identifiers (NCT IDs) and PubMed IDs (PMIDs) supporting their role in metastasis. Genes were curated from FDA oncology approvals and clinical trials, ensuring non-circular validation (gene selection preceded Target-Lock score computation). The table includes gene symbols, metastatic steps where each gene is mechanistically essential, NCT IDs for relevant clinical trials, and PMIDs for supporting literature.

**Note:** Table S1 data is available in `oncology-coPilot/oncology-backend-minimal/api/config/metastasis_interception_rules.json` and will be provided as a CSV file in the supplementary materials.

---

## 2. Figure Labels (Add to Manuscript)

Add the following figure legends throughout the manuscript where figures are referenced:

**Figure 1:** Multi-modal CRISPR design framework for metastasis interception. The platform integrates Evo2 (sequence modeling), Enformer (chromatin accessibility), and AlphaFold 3 (structural validation) to generate stage-specific anti-metastatic CRISPR therapeutics. Workflow: (1) Target-Lock scoring (multi-signal integration), (2) Guide RNA design (PAM-aware candidate generation), (3) Efficacy prediction (Evo2 delta scoring), (4) Safety assessment (off-target analysis), (5) Structural validation (AlphaFold 3 pre-screening), (6) Assassin score ranking (composite weighting).

**Figure 2:** Target-Lock score heatmap across 8 metastatic steps and 38 primary genes (304 gene-step combinations). Color intensity represents Target-Lock score (0-1 scale), with darker colors indicating higher scores. Genes with known mechanistic roles in specific steps (positive labels) are highlighted. Per-step AUROC: 0.988 ± 0.035, AUPRC: 0.962 ± 0.055.

**Figure 3:** Structural validation of 15 guide RNA:DNA complexes using AlphaFold 3 Server. (A) pLDDT distribution (mean 65.6 ± 1.8). (B) iPTM distribution (mean 0.36 ± 0.01). (C) Structural confidence composite metric. All 15 guides achieved 100% pass rate with revised RNA-DNA acceptance criteria (pLDDT ≥50, iPTM ≥0.30).

**Figure 4:** Per-step ROC curves for Target-Lock validation. Each curve represents one of 8 metastatic steps, showing true positive rate vs false positive rate. Mean AUROC across all steps: 0.988 ± 0.035 (5000-bootstrap 95% CI).

**Figure 5:** Step-specificity matrix (8×8 confusion matrix) comparing predicted step assignment (step with highest Target-Lock score) to true step assignment (ground truth labels). Diagonal dominance indicates step-specific signal. Fisher's exact test enrichment p-values shown for each step.

**Figure 6:** Precision@K analysis for Target-Lock ranking. Bars show precision at K=3, 5, and 10 top-ranked genes per step. Precision@3 = 1.000 across all steps, demonstrating perfect top-3 ranking.

**Figure 7:** Ablation study quantifying signal importance. Bars show AUROC change when each signal (Functionality, Essentiality, Regulatory, Chromatin) is removed from Target-Lock computation. Negative values indicate performance drop, with larger drops indicating greater signal importance.

**Figure S1:** Confounder analysis testing for correlation between Target-Lock scores and gene properties (length, GC content, exon count). Spearman correlations ρ<0.3 indicate minimal confounding.

**Figure S2:** Calibration curves (reliability diagrams) showing predicted Target-Lock score vs observed frequency in 5 quantile bins per step. Well-calibrated predictions should align with the diagonal.

**Figure S3:** Effect sizes (Cohen's d) for each biological signal (Functionality, Essentiality, Regulatory, Chromatin) comparing relevant vs non-relevant genes per step. Effect sizes >0.8 indicate large practical significance.

---

## 3. Table Titles (Add to Manuscript)

Add the following table titles where tables are referenced:

**Table 1:** Competitive comparison of CRISPR design tools. Features compared: sequence-level prediction, structural validation, stage-specific targeting, multi-modal integration, foundation model integration. Our platform uniquely combines all features.

**Table 2:** Performance metrics for Target-Lock validation across 8 metastatic steps. Metrics include: AUROC (with 95% bootstrap CI), AUPRC (with 95% bootstrap CI), Precision@3, Precision@5, Precision@10, Fisher's exact p-value, and Cohen's d effect size.

**Table S1:** 38 primary metastatic genes with clinical trial evidence (NCT IDs and PMIDs). Columns: Gene symbol, Metastatic steps, NCT IDs, PMIDs, FDA approval status.

**Table S2:** Hold-out validation metrics (28 train / 10 test genes). Per-step AUROC and AUPRC for training and test sets, demonstrating generalization to unseen genes.

**Table S3:** Prospective validation genes (11 FDA-approved metastatic targets, 2024-2025). Columns: Gene symbol, FDA approval date, NCT ID, Indication, Priority score, Mean Target-Lock score, Negative control status.

**Table S4:** Structural validation details for 15 guide RNA:DNA complexes. Columns: Guide name, Gene, Metastatic step, pLDDT, iPTM, Disorder fraction, Clashes, Structural confidence, Verdict (PASS/REVIEW).

---

## Implementation Notes

1. **Table S1 Creation:** Extract gene list with NCT IDs and PMIDs from `metastasis_interception_rules.json` and create CSV/LaTeX table file in `submission/tables/table_s1_genes_nct_pmid.csv` and `.tex`

2. **Figure Legends:** Insert figure legends immediately after first mention of each figure in the Results section, or create a dedicated "Figure Legends" section before References.

3. **Table Titles:** Insert table titles immediately after first mention of each table, or create a dedicated "Table Titles" section before References.

4. **Formatting:** Follow Cancer Research Communications style guide for figure/table formatting.
