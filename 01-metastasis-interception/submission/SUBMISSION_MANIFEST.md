# Submission File Manifest

**Date:** January 20, 2026  
**Journal:** Cancer Research Communications (AACR)

This manifest organizes all files by submission portal category.

---

## 1. Cover Letter
**Upload as: "Cover Letter (not shown to reviewers)"**
- `cover_letter/COVER_LETTER.md`

---

## 2. Article File
**Upload as: "Article File"**
- `article_file/MANUSCRIPT.md` (convert to PDF/Word before upload)

---

## 3. Figures
**Upload as: "Figure" (one file per upload)**

**Upload in this order (alphabetical):**

1. `figures/F2_REAL_target_lock_heatmap.png` / `.svg` - Figure 2: Target-Lock heatmap
2. `figures/F2_supp_component_scores.png` / `.svg` - Figure S: Component scores
3. `figures/F2_target_lock_heatmap.png` / `.svg` - Figure 2 (alternative): Target-Lock heatmap
4. `figures/F3_efficacy_distribution.png` / `.svg` - Figure 3: Efficacy distribution
5. `figures/F4_safety_distribution.png` / `.svg` - Figure 4: Safety distribution
6. `figures/F5_assassin_score_distribution.png` / `.svg` - Figure 5: Assassin score distribution
7. `figures/Kiani_Figure1.png` / `.svg` - Figure 1: Main workflow
8. `figures/figure2a_per_step_roc.png` / `.svg` - Figure 2a: Per-step ROC curves
9. `figures/figure2b_specificity_matrix.png` / `.svg` - Figure 2b: Specificity matrix
10. `figures/figure2c_precision_at_k.png` / `.svg` - Figure 2c: Precision@K
11. `figures/figure2d_ablation.png` / `.svg` - Figure 2d: Ablation study
12. `figures/figure_6_structural_validation.png` / `.svg` - Figure 6: Structural validation
13. `figures/figure_s1_confounders.png` / `.svg` - Figure S1: Confounder analysis
14. `figures/figure_s2_calibration_curves.png` / `.svg` - Figure S2: Calibration curves
15. `figures/figure_s3_effect_sizes.png` / `.svg` - Figure S3: Effect sizes

**Total:** 15 figure pairs (30 files: PNG + SVG) - Upload each separately

---

## 4. Tables
**Upload as: "Table" (one file per upload)**

**Upload in this order (alphabetical):**

1. `tables/table2_performance_metrics.csv` / `.tex` - Table 2: Performance metrics
2. `tables/table_s2_validation_metrics.csv` / `.tex` - Table S2: Validation metrics
3. `tables/table_s4_structural_validation.csv` / `.tex` - Table S4: Structural validation
4. `figures/publication/TABLE1_COMPETITIVE_COMPARISON.md` - Table 1: Competitive comparison

**Total:** 4 table files (upload each separately)

---

## 5. Supplementary Data
**Upload as: "Supplementary Data" (public, visible to reviewers)**

### Supplementary Data S1: Structural Validation
- `supplementary_data/structural_validation/` - 15 guide:DNA complexes
  - 15 mmCIF files
  - 15 confidence JSON files
  - 15 PAE matrix JSON files
  - Summary CSV

### Supplementary Data S2: Validation Datasets
**Upload in this order (alphabetical):**

1. `supplementary_data/ablation_study.csv` - Signal importance (3-signal vs 4-signal)
2. `supplementary_data/confounder_analysis.csv` - Gene property correlations
3. `supplementary_data/doench_2016_raw.csv` - Doench 2016 benchmark data
4. `supplementary_data/effect_sizes.csv` - Cohen's d effect sizes
5. `supplementary_data/guide_structural_details.csv` - Structural summary (15 guides)
6. `supplementary_data/guide_structural_details.json` - Structural summary (JSON)
7. `supplementary_data/guide_validation_dataset.csv` - Guide validation dataset
8. `supplementary_data/guide_validation_dataset.json` - Guide validation dataset (JSON)
9. `supplementary_data/per_step_validation_metrics.csv` - Per-step metrics (AUROC/AUPRC)
10. `supplementary_data/precision_at_k.csv` - Precision@K rankings (K=3,5,10)
11. `supplementary_data/prospective_validation_genes_agent.csv` - 11 FDA-approved genes
12. `supplementary_data/prospective_validation_genes_validated.csv` - Validated prospective genes
13. `supplementary_data/prospective_validation_labels.csv` - Prospective validation labels
14. `supplementary_data/prospective_validation_metrics.json` - Prospective validation metrics
15. `supplementary_data/prospective_validation_target_lock_scores.csv` - Prospective scores (11 genes)
16. `supplementary_data/prospective_validation_with_negatives_labels.csv` - Labels with negatives
17. `supplementary_data/prospective_validation_with_negatives_metrics.json` - Metrics with negatives
18. `supplementary_data/prospective_validation_with_negatives_scores.csv` - Scores with negatives (19 genes)
19. `supplementary_data/real_guide_validation_dataset.csv` - Guide validation dataset (all guides)
20. `supplementary_data/real_guide_validation_dataset.json` - Guide validation dataset (JSON)
21. `supplementary_data/real_target_lock_data.csv` - Primary validation (38 genes × 8 steps)
22. `supplementary_data/real_target_lock_data.json` - Primary validation (JSON)
23. `supplementary_data/real_target_lock_data_14genes_backup.csv` - Backup dataset (14 genes)
24. `supplementary_data/real_target_lock_data_24genes.csv` - Alternative dataset (24 genes)
25. `supplementary_data/specificity_enrichment.csv` - Step-specificity matrix
26. `supplementary_data/target_lock_heatmap_data.csv` - Heatmap data
27. `supplementary_data/target_lock_heatmap_data.json` - Heatmap data (JSON)

**Total:** 27 data files (package as ZIP or upload individually)

---

## 6. Supplementary Data (for Review only)
**Upload as: "Supplementary Data (for Review only)"**

**Upload in this order (alphabetical):**

1. `supplementary_data_review_only/DATA_AND_SUPPLEMENTS.md` - Complete file inventory
2. `supplementary_data_review_only/EVO2_SERVICE_URL_FINDINGS.md` - Evo2 API integration
3. `supplementary_data_review_only/GENE_COORDINATES_SOLUTION.md` - Gene coordinate validation
4. `supplementary_data_review_only/PEER_REVIEW_RESPONSES.md` - Peer review responses
5. `supplementary_data_review_only/REPRODUCIBILITY.md` - Reproduction instructions
6. `supplementary_data_review_only/structural_validation_details.md` - Structural methods
7. `supplementary_data_review_only/terms_of_use.md` - AlphaFold 3 terms
8. `supplementary_data_review_only/VALIDATION_STRATEGY.md` - Validation strategy documentation

---

## 7. Code Repository
**Reference in Data Availability section (not uploaded to portal):**
- GitHub: [URL to be added]
- Zenodo DOI: [to be added]
- Scripts: `scripts/` directory (28 Python scripts + 1 shell script)

---

## Notes:
- Convert `MANUSCRIPT.md` to PDF or Word before upload
- Figures should be high-resolution (300 DPI minimum)
- Tables can be CSV or TEX format
- Supplementary data can be packaged as ZIP files
