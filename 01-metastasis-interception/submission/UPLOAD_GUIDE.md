# Upload Guide for Cancer Research Communications

**MS# CRC-26-0061**  
**Base Directory:** `/Users/fahadkiani/Desktop/development/crispr-assistant-main/publications/01-metastasis-interception/submission/`

---

## What the Editor Needs (Missing Items)

### 1. Table S1 Legend
**Status:** ❌ Missing  
**Location:** Needs to be added to manuscript  
**Action:** Add legend text to manuscript (see EDITOR_FIXES.md)

### 2. Figure Labels
**Status:** ❌ Missing  
**Location:** Needs to be added to manuscript  
**Action:** Add figure legends to manuscript (see EDITOR_FIXES.md)

### 3. Table Titles
**Status:** ❌ Missing  
**Location:** Needs to be added to manuscript  
**Action:** Add table titles to manuscript (see EDITOR_FIXES.md)

---

## What to Upload to Submission Portal

### 1. Cover Letter
**Upload as:** "Cover Letter (not shown to reviewers)"  
**File:** `submission/cover_letter/COVER_LETTER.md`  
**Format:** Convert to PDF/Word before upload

### 2. Article File (Main Manuscript)
**Upload as:** "Article File"  
**File:** `submission/article_file/MANUSCRIPT.md`  
**Format:** Convert to PDF/Word before upload  
**⚠️ IMPORTANT:** Add figure labels and table titles to this file BEFORE converting

### 3. Figures (15 figures)
**Upload as:** "Figure" (one file per upload)  
**Location:** `submission/figures/`  
**Format:** PNG or SVG (use PNG for submission, 300 DPI minimum)

**Upload these files:**
1. `figures/Kiani_Figure1.png` - Figure 1
2. `figures/F2_REAL_target_lock_heatmap.png` - Figure 2
3. `figures/figure_6_structural_validation.png` - Figure 3
4. `figures/figure2a_per_step_roc.png` - Figure 4
5. `figures/figure2b_specificity_matrix.png` - Figure 5
6. `figures/figure2c_precision_at_k.png` - Figure 6
7. `figures/figure2d_ablation.png` - Figure 7
8. `figures/figure_s1_confounders.png` - Figure S1
9. `figures/figure_s2_calibration_curves.png` - Figure S2
10. `figures/figure_s3_effect_sizes.png` - Figure S3
11. `figures/F3_efficacy_distribution.png` - (if needed)
12. `figures/F4_safety_distribution.png` - (if needed)
13. `figures/F5_assassin_score_distribution.png` - (if needed)

**Note:** Each figure needs a label/legend in the manuscript text

### 4. Tables (4 tables + Table S1 needs to be created)
**Upload as:** "Table" (one file per upload)  
**Location:** `submission/tables/`  
**Format:** CSV or LaTeX (.tex)

**Upload these files:**
1. `tables/table2_performance_metrics.csv` - Table 2
2. `tables/table_s2_validation_metrics.csv` - Table S2
3. `tables/table_s4_structural_validation.csv` - Table S4
4. `figures/publication/TABLE1_COMPETITIVE_COMPARISON.md` - Table 1 (convert to CSV/LaTeX)

**⚠️ MISSING:** Table S1 (38 genes with NCT IDs and PMIDs)  
**Action:** Need to create `tables/table_s1_genes_nct_pmid.csv` from `metastasis_interception_rules.json`

### 5. Supplementary Data (Public)
**Upload as:** "Supplementary Data"  
**Location:** `submission/supplementary_data/`  
**Format:** Individual files or ZIP archive

**Upload:**
- All CSV/JSON files in `supplementary_data/` (27 files total)
- Structural validation files in `supplementary_data/structural_validation/` (15 guides × 3 files each = 45 files)

### 6. Supplementary Data (Review Only)
**Upload as:** "Supplementary Data (for Review only)"  
**Location:** `submission/supplementary_data_review_only/`  
**Format:** Individual files

**Upload:**
- All 8 markdown files in `supplementary_data_review_only/`

---

## Quick Fix Checklist

Before uploading, you need to:

- [ ] **Create Table S1** - Extract 38 genes with NCT IDs/PMIDs from JSON config
- [ ] **Add Table S1 legend** to manuscript
- [ ] **Add all figure labels** to manuscript (9 figures)
- [ ] **Add all table titles** to manuscript (6 tables)
- [ ] **Convert MANUSCRIPT.md to PDF/Word** for upload
- [ ] **Verify all figure files exist** in `submission/figures/`
- [ ] **Verify all table files exist** in `submission/tables/`

---

## File Locations Summary

```
submission/
├── article_file/
│   └── MANUSCRIPT.md          ← Add labels/titles here, then convert to PDF
├── cover_letter/
│   └── COVER_LETTER.md        ← Upload as-is
├── figures/                    ← 15 PNG files to upload
│   ├── Kiani_Figure1.png
│   ├── F2_REAL_target_lock_heatmap.png
│   └── ... (13 more)
├── tables/                     ← 4 CSV files + need to create Table S1
│   ├── table2_performance_metrics.csv
│   ├── table_s2_validation_metrics.csv
│   ├── table_s4_structural_validation.csv
│   └── table_s1_genes_nct_pmid.csv  ← NEED TO CREATE
├── supplementary_data/         ← 27 CSV/JSON files + 45 structural files
└── supplementary_data_review_only/  ← 8 markdown files
```

---

## Next Steps

1. **Create Table S1** (I can do this - need access to `metastasis_interception_rules.json`)
2. **Add labels/titles to manuscript** (I can do this - see EDITOR_FIXES.md)
3. **Convert manuscript to PDF** (You do this - use pandoc or Word)
4. **Upload to portal** (You do this - follow portal instructions)
