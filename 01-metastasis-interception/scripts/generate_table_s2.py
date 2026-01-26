#!/usr/bin/env python3
"""
Table S2: Complete Validation Metrics

Generate publication-ready supplementary table with all validation metrics:
- Per-step AUROC/AUPRC with CIs
- Precision@K
- Confusion matrix statistics
- Effect sizes
- Enrichment p-values

Author: Zo
Date: October 13, 2025
"""

import pandas as pd
from pathlib import Path

DATA_DIR = Path("publication/data")
OUTPUT_DIR = Path("publication/tables")
OUTPUT_DIR.mkdir(exist_ok=True, parents=True)

def load_all_metrics():
    """Load all computed validation metrics"""
    # Per-step validation (Day 1)
    per_step = pd.read_csv(DATA_DIR / "per_step_validation_metrics.csv")
    
    # Precision@K (Day 1)
    precision_k = pd.read_csv(DATA_DIR / "precision_at_k.csv")
    
    # Specificity/enrichment (Day 1)
    specificity = pd.read_csv(DATA_DIR / "specificity_enrichment.csv")
    
    # Effect sizes (Day 2)
    effect_sizes = pd.read_csv(DATA_DIR / "effect_sizes.csv")
    
    # Ablation (Day 1)
    ablation = pd.read_csv(DATA_DIR / "ablation_study.csv")
    
    return per_step, precision_k, specificity, effect_sizes, ablation

def merge_metrics(per_step, precision_k, specificity, effect_sizes):
    """Merge all metrics into single comprehensive table"""
    # Start with per-step as base
    table = per_step.copy()
    
    # Add Precision@3
    p3 = precision_k[['step', 'P@3']].rename(columns={'P@3': 'precision_at_3'})
    table = table.merge(p3, on='step', how='left')
    
    # Add diagonal dominance (computed from counts)
    specificity['diagonal_dominance'] = specificity['diagonal_count'] / specificity['total_true']
    diag = specificity[['step', 'diagonal_dominance']]
    table = table.merge(diag, on='step', how='left')
    
    # Add enrichment p-value
    enrich = specificity[['step', 'enrichment_pvalue']]
    table = table.merge(enrich, on='step', how='left')
    
    # Add effect size for target_lock_score
    effect_tl = effect_sizes[effect_sizes['signal'] == 'target_lock_score'][['step', 'cohens_d']].rename(columns={'cohens_d': 'effect_size_d'})
    table = table.merge(effect_tl, on='step', how='left')
    
    return table

def format_table_s2(table):
    """Format table for publication"""
    # Rename columns
    table = table.rename(columns={
        'step': 'Metastatic Step',
        'auroc': 'AUROC',
        'auroc_ci_lower': 'AUROC 95% CI Lower',
        'auroc_ci_upper': 'AUROC 95% CI Upper',
        'auprc': 'AUPRC',
        'auprc_ci_lower': 'AUPRC 95% CI Lower',
        'auprc_ci_upper': 'AUPRC 95% CI Upper',
        'precision_at_3': 'Precision@3',
        'diagonal_dominance': 'Diagonal Dominance',
        'enrichment_pvalue': 'Enrichment p-value',
        'effect_size_d': "Cohen's d"
    })
    
    # Format step names
    table['Metastatic Step'] = table['Metastatic Step'].str.replace('_', ' ').str.title()
    
    # Round numeric columns
    numeric_cols = ['AUROC', 'AUROC 95% CI Lower', 'AUROC 95% CI Upper',
                    'AUPRC', 'AUPRC 95% CI Lower', 'AUPRC 95% CI Upper',
                    'Precision@3', 'Diagonal Dominance', "Cohen's d"]
    for col in numeric_cols:
        if col in table.columns:
            table[col] = table[col].round(3)
    
    # Format p-values
    if 'Enrichment p-value' in table.columns:
        table['Enrichment p-value'] = table['Enrichment p-value'].apply(lambda x: f"{x:.2e}" if pd.notna(x) else "NA")
    
    return table

def main():
    print("=" * 80)
    print("🔥 DAY 2: TABLE S2 - COMPREHENSIVE VALIDATION METRICS")
    print("=" * 80)
    
    # Load all metrics
    per_step, precision_k, specificity, effect_sizes, ablation = load_all_metrics()
    
    # Merge into single table
    table = merge_metrics(per_step, precision_k, specificity, effect_sizes)
    
    # Format for publication
    table_s2 = format_table_s2(table)
    
    # Save CSV
    csv_path = OUTPUT_DIR / "table_s2_validation_metrics.csv"
    table_s2.to_csv(csv_path, index=False)
    print(f"✅ Saved CSV: {csv_path}")
    
    # Save LaTeX
    latex_path = OUTPUT_DIR / "table_s2_validation_metrics.tex"
    with open(latex_path, 'w') as f:
        f.write("% Table S2: Comprehensive Validation Metrics\n")
        f.write("% Generated: October 13, 2025\n\n")
        f.write(table_s2.to_latex(index=False, float_format="%.3f", caption="Comprehensive validation metrics per metastatic step with 1000-bootstrap 95% CIs (seed=42)"))
    print(f"✅ Saved LaTeX: {latex_path}")
    
    # Display summary
    print("\n📊 Table S2 Summary:")
    print(f"   Rows: {len(table_s2)}")
    print(f"   Columns: {len(table_s2.columns)}")
    print(f"\n   Columns included:")
    for col in table_s2.columns:
        print(f"      - {col}")
    
    print("\n✅ DAY 2 TASK 3 COMPLETE: Table S2 Generated")
    print("=" * 80)

if __name__ == "__main__":
    main()

