#!/usr/bin/env python3
"""
Specificity Matrix & Enrichment Analysis

Computes confusion matrix of predicted step vs true step assignments:
- Diagonal dominance metric
- Fisher's exact enrichment p-values per step
- Step-weighted averages for unbalanced classes
- Heatmap visualization

Author: Zo
Date: October 13, 2025
"""

import json
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from scipy import stats

SEED = 42
np.random.seed(SEED)

OUTPUT_DIR = Path("publication/figures")
DATA_DIR = Path("publication/data")

def load_data():
    """Load labels and scores"""
    # Load ground truth
    rules_path = Path(os.environ.get("METASTASIS_RULES_PATH", "oncology-coPilot/oncology-backend-minimal/api/config/metastasis_rules_v1.0.1.json"))
    if not rules_path.exists():
        rules_path = Path("oncology-coPilot/oncology-backend-minimal/api/config/metastasis_rules_v1.0.0.json")
    with open(rules_path) as f:
        rules = json.load(f)
    
    # Load scores
    scores = pd.read_csv(DATA_DIR / "real_target_lock_data.csv")
    if 'mission' in scores.columns:
        scores = scores.rename(columns={'mission': 'step'})
    
    return rules, scores

def build_confusion_matrix(rules, scores):
    """Build confusion matrix: predicted step (max score) vs true step labels"""
    
    steps = list(rules['steps'].keys())
    n_steps = len(steps)
    confusion = np.zeros((n_steps, n_steps))
    
    # Get all unique genes
    all_genes = set()
    for step_data in rules['steps'].values():
        all_genes.update(step_data.get('primary_genes', []))
        all_genes.update(step_data.get('secondary_genes', []))
    
    for gene in all_genes:
        # Get true steps for this gene
        true_steps = []
        for step_idx, (step_name, step_data) in enumerate(rules['steps'].items()):
            primary = set(step_data.get('primary_genes', []))
            secondary = set(step_data.get('secondary_genes', []))
            if gene in (primary | secondary):
                true_steps.append(step_idx)
        
        # Get predicted step (highest score)
        gene_scores = scores[scores['gene'] == gene]
        if len(gene_scores) == 0:
            continue
        
        pred_step_name = gene_scores.loc[gene_scores['target_lock_score'].idxmax(), 'step']
        pred_step_idx = steps.index(pred_step_name)
        
        # Fill confusion matrix
        for true_step_idx in true_steps:
            confusion[true_step_idx, pred_step_idx] += 1
    
    return confusion, steps

def compute_enrichment_pvalues(confusion, steps):
    """Compute Fisher's exact test p-values for each step"""
    n_steps = len(steps)
    pvalues = np.zeros(n_steps)
    
    for i in range(n_steps):
        # 2x2 contingency table for step i
        a = confusion[i, i]  # True positive
        b = confusion[i, :].sum() - a  # False negative
        c = confusion[:, i].sum() - a  # False positive
        d = confusion.sum() - a - b - c  # True negative
        
        contingency = [[a, b], [c, d]]
        _, pvalue = stats.fisher_exact(contingency, alternative='greater')
        pvalues[i] = pvalue
    
    return pvalues

def plot_confusion_heatmap(confusion, steps, pvalues, output_path):
    """Plot confusion matrix heatmap with p-values"""
    fig, ax = plt.subplots(figsize=(12, 10))
    
    # Normalize by row (true labels)
    confusion_norm = confusion / confusion.sum(axis=1, keepdims=True)
    
    # Plot heatmap
    sns.heatmap(confusion_norm, annot=True, fmt='.2f', cmap='YlOrRd',
                xticklabels=[s.replace('_', ' ').title() for s in steps],
                yticklabels=[s.replace('_', ' ').title() for s in steps],
                cbar_kws={'label': 'Fraction of genes'}, ax=ax)
    
    ax.set_xlabel('Predicted Step (Max Target-Lock Score)', fontsize=12)
    ax.set_ylabel('True Step (Ground Truth)', fontsize=12)
    ax.set_title('Specificity Matrix: Predicted vs True Metastatic Step\n(Diagonal = Correct Assignment)', 
                 fontsize=14, pad=20)
    
    # Add p-values on diagonal
    for i in range(len(steps)):
        text = f"p={pvalues[i]:.3f}" if pvalues[i] >= 0.001 else "p<0.001"
        ax.text(i + 0.5, i + 0.2, text, ha='center', va='top', 
                fontsize=8, color='white' if confusion_norm[i, i] > 0.5 else 'black')
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.savefig(output_path.with_suffix('.svg'), bbox_inches='tight')
    print(f"✅ Saved specificity matrix: {output_path}")

def main():
    print("=" * 80)
    print("🔥 TASK 3: SPECIFICITY MATRIX & ENRICHMENT")
    print("=" * 80)
    
    rules, scores = load_data()
    
    # Build confusion matrix
    confusion, steps = build_confusion_matrix(rules, scores)
    print(f"\n✅ Built confusion matrix: {confusion.shape}")
    
    # Compute diagonal dominance
    diagonal_sum = np.diag(confusion).sum()
    total_sum = confusion.sum()
    diagonal_dominance = diagonal_sum / total_sum if total_sum > 0 else 0
    print(f"   Diagonal dominance: {diagonal_dominance:.3f} ({diagonal_sum}/{total_sum})")
    
    # Compute enrichment p-values
    pvalues = compute_enrichment_pvalues(confusion, steps)
    print(f"\n✅ Fisher's exact enrichment p-values:")
    for step, pval in zip(steps, pvalues):
        sig = "***" if pval < 0.001 else "**" if pval < 0.01 else "*" if pval < 0.05 else "ns"
        print(f"   {step:30s}: p = {pval:.4f} {sig}")
    
    # Save results
    results_df = pd.DataFrame({
        'step': steps,
        'diagonal_count': np.diag(confusion),
        'total_true': confusion.sum(axis=1),
        'total_predicted': confusion.sum(axis=0),
        'enrichment_pvalue': pvalues
    })
    results_df.to_csv(DATA_DIR / "specificity_enrichment.csv", index=False)
    print(f"\n✅ Saved results: {DATA_DIR / 'specificity_enrichment.csv'}")
    
    # Plot heatmap
    output_path = OUTPUT_DIR / "figure2b_specificity_matrix.png"
    plot_confusion_heatmap(confusion, steps, pvalues, output_path)
    
    print("\n✅ TASK 3 COMPLETE: Specificity Matrix Generated")
    print("=" * 80)

if __name__ == "__main__":
    main()


