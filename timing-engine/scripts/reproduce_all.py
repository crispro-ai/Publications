#!/usr/bin/env python3
"""
TIMING ENGINE VALIDATION - MASTER REPRODUCTION SCRIPT

This script reproduces all tables, figures, and statistics from the manuscript:
"A Pan-Cancer Timing and Chemosensitivity Engine for Standardized Treatment History Analysis"

Usage:
    python reproduce_all.py

Output:
    - tables/table1_cohort.csv
    - tables/table2_error_bins.csv
    - tables/table3_confusion.csv
    - tables/table4_boundary.csv
    - figures/fig2_error_histogram.png
    - figures/fig3_confusion_matrix.png
    - supplementary/full_validation_results.csv
    - supplementary/statistics_summary.txt
"""

import pandas as pd
import numpy as np
from scipy import stats
from pathlib import Path
import sys

# Optional: matplotlib for figures
try:
    import matplotlib.pyplot as plt
    import seaborn as sns
    HAS_PLOTTING = True
except ImportError:
    print("Warning: matplotlib/seaborn not available. Skipping figure generation.")
    HAS_PLOTTING = False

# =============================================================================
# CONFIGURATION
# =============================================================================

DATA_FILE = Path("oncology-coPilot/oncology-backend-minimal/data/TCGA-OV/ds_cci.17.00096-1.xlsx")
OUTPUT_DIR = Path("publications/timing-engine")

# Columns from Villalobos Data Supplement 1
PLATINUM_COL = 'Last day of platinum 1st line'
PROGRESSION_COL = 'days_to_tumor_recurrence'
PFI_GROUND_TRUTH_COL = 'Days off platinum prior to recurrence 1st line'
PATIENT_ID_COL = 'bcr_patient_barcode'

# PFI category thresholds (days)
THRESHOLD_RESISTANT = 180    # <6 months
THRESHOLD_SENSITIVE = 365    # >12 months

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def categorize_pfi(days):
    """Categorize PFI into clinical categories"""
    if pd.isna(days):
        return 'Missing'
    elif days < 0:
        return 'Negative (Invalid)'
    elif days < THRESHOLD_RESISTANT:
        return '<6m'
    elif days < THRESHOLD_SENSITIVE:
        return '6-12m'
    else:
        return '>12m'

def wilson_ci(successes, n, confidence=0.95):
    """Wilson score interval for binomial proportion"""
    if n == 0:
        return (0, 0)
    z = stats.norm.ppf(1 - (1-confidence)/2)
    p = successes / n
    denom = 1 + z**2/n
    center = (p + z**2/(2*n)) / denom
    offset = z * np.sqrt(p*(1-p)/n + z**2/(4*n**2)) / denom
    return (max(0, center - offset), min(1, center + offset))

def format_ci(value, n, ci):
    """Format value with 95% CI"""
    return f"{value}/{n} ({100*value/n:.1f}%; 95% CI: {100*ci[0]:.1f}%-{100*ci[1]:.1f}%)"

# =============================================================================
# MAIN SCRIPT
# =============================================================================

def main():
    print("="*80)
    print("TIMING ENGINE VALIDATION - REPRODUCTION SCRIPT")
    print("="*80)
    print()
    
    # Create output directories
    (OUTPUT_DIR / "tables").mkdir(parents=True, exist_ok=True)
    (OUTPUT_DIR / "figures").mkdir(parents=True, exist_ok=True)
    (OUTPUT_DIR / "supplementary").mkdir(parents=True, exist_ok=True)
    
    # =========================================================================
    # STEP 1: LOAD DATA
    # =========================================================================
    print("STEP 1: Loading data...")
    
    if not DATA_FILE.exists():
        print(f"ERROR: Data file not found: {DATA_FILE}")
        print("Please download from: https://ascopubs.org/doi/suppl/10.1200/CCI.17.00096")
        sys.exit(1)
    
    df = pd.read_excel(DATA_FILE, sheet_name='Master clinical dataset')
    print(f"  Loaded: {len(df)} rows, {df[PATIENT_ID_COL].nunique()} unique patients")
    print()
    
    # =========================================================================
    # STEP 2: EXTRACT VALIDATION COHORT
    # =========================================================================
    print("STEP 2: Extracting validation cohort...")
    
    # Convert to numeric
    platinum = pd.to_numeric(df[PLATINUM_COL], errors='coerce')
    progression = pd.to_numeric(df[PROGRESSION_COL], errors='coerce')
    pfi_gt = pd.to_numeric(df[PFI_GROUND_TRUTH_COL], errors='coerce')
    
    print(f"  '{PLATINUM_COL}': {platinum.notna().sum()}/{len(df)}")
    print(f"  '{PROGRESSION_COL}': {progression.notna().sum()}/{len(df)}")
    print(f"  '{PFI_GROUND_TRUTH_COL}': {pfi_gt.notna().sum()}/{len(df)}")
    
    # Validation cohort
    valid_mask = platinum.notna() & progression.notna() & pfi_gt.notna()
    val_df = df[valid_mask].copy()
    print(f"  Validation cohort (all 3 fields): {len(val_df)}")
    print()
    
    # =========================================================================
    # STEP 3: COMPUTE PFI
    # =========================================================================
    print("STEP 3: Computing PFI from independent fields...")
    
    val_df['computed_pfi'] = (
        pd.to_numeric(val_df[PROGRESSION_COL], errors='coerce') -
        pd.to_numeric(val_df[PLATINUM_COL], errors='coerce')
    )
    val_df['ground_truth_pfi'] = pd.to_numeric(val_df[PFI_GROUND_TRUTH_COL], errors='coerce')
    val_df['diff'] = val_df['computed_pfi'] - val_df['ground_truth_pfi']
    val_df['abs_diff'] = val_df['diff'].abs()
    val_df['computed_category'] = val_df['computed_pfi'].apply(categorize_pfi)
    val_df['gt_category'] = val_df['ground_truth_pfi'].apply(categorize_pfi)
    
    print("  PFI computed from: days_to_tumor_recurrence - Last day of platinum 1st line")
    print()
    
    # =========================================================================
    # TABLE 1: VALIDATION COHORT PFI DISTRIBUTION
    # =========================================================================
    print("GENERATING TABLE 1: Validation Cohort PFI Distribution...")
    
    table1 = pd.DataFrame({
        'Category': ['<6m (Resistant)', '6-12m (Partially Sensitive)', '>12m (Sensitive)', 'Negative/Invalid'],
        'n': [
            ((val_df['ground_truth_pfi'] >= 0) & (val_df['ground_truth_pfi'] < 180)).sum(),
            ((val_df['ground_truth_pfi'] >= 180) & (val_df['ground_truth_pfi'] < 365)).sum(),
            (val_df['ground_truth_pfi'] >= 365).sum(),
            (val_df['ground_truth_pfi'] < 0).sum()
        ]
    })
    table1['%'] = (table1['n'] / len(val_df) * 100).round(1)
    
    table1.to_csv(OUTPUT_DIR / "tables/table1_cohort.csv", index=False)
    print(table1)
    print()
    
    # =========================================================================
    # TABLE 2: ERROR DISTRIBUTION BY MAGNITUDE
    # =========================================================================
    print("GENERATING TABLE 2: Error Distribution by Magnitude...")
    
    table2 = pd.DataFrame({
        'Error Bin': ['Exact match (0 days)', '1-7 days', '8-30 days', '31-90 days', '>90 days'],
        'n': [
            (val_df['abs_diff'] == 0).sum(),
            ((val_df['abs_diff'] > 0) & (val_df['abs_diff'] <= 7)).sum(),
            ((val_df['abs_diff'] > 7) & (val_df['abs_diff'] <= 30)).sum(),
            ((val_df['abs_diff'] > 30) & (val_df['abs_diff'] <= 90)).sum(),
            (val_df['abs_diff'] > 90).sum()
        ]
    })
    table2['%'] = (table2['n'] / len(val_df) * 100).round(1)
    table2['Cumulative %'] = table2['%'].cumsum()
    
    table2.to_csv(OUTPUT_DIR / "tables/table2_error_bins.csv", index=False)
    print(table2)
    print()
    
    # =========================================================================
    # TABLE 3: CONFUSION MATRIX
    # =========================================================================
    print("GENERATING TABLE 3: Confusion Matrix...")
    
    # Filter to valid (non-negative) cases
    valid_for_cat = (val_df['computed_pfi'] >= 0) & (val_df['ground_truth_pfi'] >= 0)
    cat_df = val_df[valid_for_cat]
    
    confusion = pd.crosstab(
        cat_df['gt_category'],
        cat_df['computed_category'],
        rownames=['Ground Truth'],
        colnames=['Computed'],
        margins=True
    )
    
    confusion.to_csv(OUTPUT_DIR / "tables/table3_confusion.csv")
    print(confusion)
    print()
    
    # =========================================================================
    # TABLE 4: BOUNDARY ANALYSIS
    # =========================================================================
    print("GENERATING TABLE 4: Boundary Analysis...")
    
    near_6m = ((cat_df['ground_truth_pfi'] >= 166) & (cat_df['ground_truth_pfi'] <= 194)).sum()
    near_12m = ((cat_df['ground_truth_pfi'] >= 351) & (cat_df['ground_truth_pfi'] <= 379)).sum()
    
    mismatches = cat_df[cat_df['computed_category'] != cat_df['gt_category']]
    boundary_mismatches_6m = len(mismatches[
        (mismatches['ground_truth_pfi'] >= 166) & (mismatches['ground_truth_pfi'] <= 194)
    ])
    boundary_mismatches_12m = len(mismatches[
        (mismatches['ground_truth_pfi'] >= 351) & (mismatches['ground_truth_pfi'] <= 379)
    ])
    
    table4 = pd.DataFrame({
        'Threshold': ['180 days (6 months)', '365 days (12 months)'],
        'Boundary (±14 days)': ['166-194 days', '351-379 days'],
        'n at boundary': [near_6m, near_12m],
        'Mismatches at boundary': [boundary_mismatches_6m, boundary_mismatches_12m]
    })
    
    table4.to_csv(OUTPUT_DIR / "tables/table4_boundary.csv", index=False)
    print(table4)
    print()
    
    # =========================================================================
    # STATISTICS SUMMARY
    # =========================================================================
    print("COMPUTING STATISTICS WITH 95% CIs...")
    
    n_total = len(val_df)
    n_valid_cat = len(cat_df)
    
    exact_match = (val_df['abs_diff'] == 0).sum()
    exact_ci = wilson_ci(exact_match, n_total)
    
    cat_match = (cat_df['computed_category'] == cat_df['gt_category']).sum()
    cat_ci = wilson_ci(cat_match, n_valid_cat)
    
    n_invalid = (val_df['computed_pfi'] < 0).sum()
    invalid_ci = wilson_ci(n_invalid, n_total)
    
    stats_summary = f"""
TIMING ENGINE VALIDATION - STATISTICS SUMMARY
=============================================

Dataset: Villalobos 2018 TCGA-OV (Data Supplement 1)
File: ds_cci.17.00096-1.xlsx

COHORT SUMMARY
--------------
Total rows in data: {len(df)}
Unique patients: {df[PATIENT_ID_COL].nunique()}
Validation cohort (all fields): {n_total}
Valid for category analysis: {n_valid_cat}

PRIMARY OUTCOMES
----------------
Exact-day match: {format_ci(exact_match, n_total, exact_ci)}
Category agreement: {format_ci(cat_match, n_valid_cat, cat_ci)}
Invalid (negative PFI): {format_ci(n_invalid, n_total, invalid_ci)}

CATEGORY BREAKDOWN
------------------
Category mismatches: {n_valid_cat - cat_match}/{n_valid_cat}
Mismatches at boundaries: {boundary_mismatches_6m + boundary_mismatches_12m}/{n_valid_cat - cat_match}

ERROR DISTRIBUTION
------------------
0 days (exact): {(val_df['abs_diff'] == 0).sum()}
1-7 days: {((val_df['abs_diff'] > 0) & (val_df['abs_diff'] <= 7)).sum()}
8-30 days: {((val_df['abs_diff'] > 7) & (val_df['abs_diff'] <= 30)).sum()}
31-90 days: {((val_df['abs_diff'] > 30) & (val_df['abs_diff'] <= 90)).sum()}
>90 days: {(val_df['abs_diff'] > 90).sum()}

Generated: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
    
    with open(OUTPUT_DIR / "supplementary/statistics_summary.txt", 'w') as f:
        f.write(stats_summary)
    
    print(stats_summary)
    
    # =========================================================================
    # FULL VALIDATION RESULTS
    # =========================================================================
    print("SAVING FULL VALIDATION RESULTS...")
    
    val_df[[PATIENT_ID_COL, PLATINUM_COL, PROGRESSION_COL, PFI_GROUND_TRUTH_COL,
            'computed_pfi', 'ground_truth_pfi', 'diff', 'abs_diff',
            'computed_category', 'gt_category']].to_csv(
        OUTPUT_DIR / "supplementary/full_validation_results.csv", index=False
    )
    print(f"  Saved to: {OUTPUT_DIR / 'supplementary/full_validation_results.csv'}")
    print()
    
    # =========================================================================
    # FIGURES
    # =========================================================================
    if HAS_PLOTTING:
        print("GENERATING FIGURES...")
        
        # Figure 2: Error Histogram
        fig, ax = plt.subplots(figsize=(8, 5))
        bins = ['0', '1-7', '8-30', '31-90', '>90']
        counts = [
            (val_df['abs_diff'] == 0).sum(),
            ((val_df['abs_diff'] > 0) & (val_df['abs_diff'] <= 7)).sum(),
            ((val_df['abs_diff'] > 7) & (val_df['abs_diff'] <= 30)).sum(),
            ((val_df['abs_diff'] > 30) & (val_df['abs_diff'] <= 90)).sum(),
            (val_df['abs_diff'] > 90).sum()
        ]
        colors = ['#2ecc71', '#3498db', '#3498db', '#e74c3c', '#e74c3c']
        bars = ax.bar(bins, counts, color=colors, edgecolor='black')
        ax.set_xlabel('Absolute Error (days)', fontsize=12)
        ax.set_ylabel('Number of Patients', fontsize=12)
        ax.set_title('Error Distribution: Computed vs Reference PFI', fontsize=14)
        for bar, count in zip(bars, counts):
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 2, 
                    str(count), ha='center', fontsize=10)
        plt.tight_layout()
        plt.savefig(OUTPUT_DIR / 'figures/fig2_error_histogram.png', dpi=300)
        print(f"  Saved: fig2_error_histogram.png")
        plt.close()
        
        # Figure 3: Confusion Matrix
        fig, ax = plt.subplots(figsize=(7, 6))
        cm_data = [
            [((cat_df['gt_category'] == '<6m') & (cat_df['computed_category'] == '<6m')).sum(),
             ((cat_df['gt_category'] == '<6m') & (cat_df['computed_category'] == '6-12m')).sum(),
             ((cat_df['gt_category'] == '<6m') & (cat_df['computed_category'] == '>12m')).sum()],
            [((cat_df['gt_category'] == '6-12m') & (cat_df['computed_category'] == '<6m')).sum(),
             ((cat_df['gt_category'] == '6-12m') & (cat_df['computed_category'] == '6-12m')).sum(),
             ((cat_df['gt_category'] == '6-12m') & (cat_df['computed_category'] == '>12m')).sum()],
            [((cat_df['gt_category'] == '>12m') & (cat_df['computed_category'] == '<6m')).sum(),
             ((cat_df['gt_category'] == '>12m') & (cat_df['computed_category'] == '6-12m')).sum(),
             ((cat_df['gt_category'] == '>12m') & (cat_df['computed_category'] == '>12m')).sum()]
        ]
        categories = ['<6m', '6-12m', '>12m']
        sns.heatmap(cm_data, annot=True, fmt='d', cmap='Blues',
                    xticklabels=categories, yticklabels=categories,
                    cbar_kws={'label': 'Count'}, ax=ax)
        ax.set_xlabel('Computed Category', fontsize=12)
        ax.set_ylabel('Ground Truth Category', fontsize=12)
        ax.set_title(f'PFI Category Confusion Matrix (n={len(cat_df)})', fontsize=14)
        plt.tight_layout()
        plt.savefig(OUTPUT_DIR / 'figures/fig3_confusion_matrix.png', dpi=300)
        print(f"  Saved: fig3_confusion_matrix.png")
        plt.close()
    
    # =========================================================================
    # DONE
    # =========================================================================
    print()
    print("="*80)
    print("REPRODUCTION COMPLETE")
    print("="*80)
    print()
    print("Output files:")
    print(f"  - {OUTPUT_DIR}/tables/table1_cohort.csv")
    print(f"  - {OUTPUT_DIR}/tables/table2_error_bins.csv")
    print(f"  - {OUTPUT_DIR}/tables/table3_confusion.csv")
    print(f"  - {OUTPUT_DIR}/tables/table4_boundary.csv")
    print(f"  - {OUTPUT_DIR}/supplementary/statistics_summary.txt")
    print(f"  - {OUTPUT_DIR}/supplementary/full_validation_results.csv")
    if HAS_PLOTTING:
        print(f"  - {OUTPUT_DIR}/figures/fig2_error_histogram.png")
        print(f"  - {OUTPUT_DIR}/figures/fig3_confusion_matrix.png")
    print()

if __name__ == "__main__":
    main()
