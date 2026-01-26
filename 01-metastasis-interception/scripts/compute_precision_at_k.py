#!/usr/bin/env python3
"""
Precision@K Analysis

Computes precision at top K predictions for clinical decision thresholds:
- K=3, 5, 10 (standard clinical cutoffs)
- Per-step precision-recall curves
- Macro-averaged P@K across steps

Author: Zo
Date: October 13, 2025
"""

import json
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
from sklearn.metrics import precision_recall_curve

SEED = 42
np.random.seed(SEED)

OUTPUT_DIR = Path("publication/figures")
DATA_DIR = Path("publication/data")

def load_data():
    rules_path = Path(os.environ.get("METASTASIS_RULES_PATH", "oncology-coPilot/oncology-backend-minimal/api/config/metastasis_rules_v1.0.1.json"))
    if not rules_path.exists():
        rules_path = Path("oncology-coPilot/oncology-backend-minimal/api/config/metastasis_rules_v1.0.0.json")
    with open(rules_path) as f:
        rules = json.load(f)
    
    scores = pd.read_csv(DATA_DIR / "real_target_lock_data.csv")
    if 'mission' in scores.columns:
        scores = scores.rename(columns={'mission': 'step'})
    
    return rules, scores

def compute_precision_at_k(y_true, y_score, k):
    """Compute precision@K"""
    top_k_idx = np.argsort(y_score)[-k:]
    return y_true[top_k_idx].mean()

def analyze_per_step_precision_at_k(rules, scores):
    """Compute P@K for each step"""
    results = []
    k_values = [3, 5, 10]
    
    steps = list(rules['steps'].keys())
    
    for step in steps:
        # Get labels
        all_genes = set()
        for step_data in rules['steps'].values():
            all_genes.update(step_data.get('primary_genes', []))
            all_genes.update(step_data.get('secondary_genes', []))
        
        step_data = rules['steps'][step]
        primary = set(step_data.get('primary_genes', []))
        secondary = set(step_data.get('secondary_genes', []))
        relevant = primary | secondary
        
        # Get scores for this step
        step_scores = scores[scores['step'] == step].copy()
        if len(step_scores) == 0:
            continue
        
        # Merge with labels
        step_scores['label'] = step_scores['gene'].apply(lambda g: 1 if g in relevant else 0)
        
        y_true = step_scores['label'].values
        y_score = step_scores['target_lock_score'].values
        
        if len(y_true) < max(k_values):
            continue
        
        result = {'step': step, 'n_genes': len(y_true), 'n_relevant': y_true.sum()}
        for k in k_values:
            if len(y_true) >= k:
                result[f'P@{k}'] = compute_precision_at_k(y_true, y_score, k)
        
        results.append(result)
    
    return pd.DataFrame(results)

def plot_precision_at_k_bars(results_df, output_path):
    """Plot P@K bar chart"""
    fig, ax = plt.subplots(figsize=(14, 8))
    
    steps = results_df['step'].values
    x = np.arange(len(steps))
    width = 0.25
    
    k_values = [3, 5, 10]
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c']
    
    for i, k in enumerate(k_values):
        col = f'P@{k}'
        if col in results_df.columns:
            values = results_df[col].fillna(0).values
            ax.bar(x + i * width, values, width, label=f'P@{k}', color=colors[i], alpha=0.8)
    
    ax.set_xlabel('Metastatic Step', fontsize=12)
    ax.set_ylabel('Precision@K', fontsize=12)
    ax.set_title('Precision@K Analysis: Top-Ranked Gene Accuracy by Step', fontsize=14)
    ax.set_xticks(x + width)
    ax.set_xticklabels([s.replace('_', ' ').title() for s in steps], rotation=45, ha='right')
    ax.legend()
    ax.grid(axis='y', alpha=0.3)
    ax.set_ylim(0, 1.0)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.savefig(output_path.with_suffix('.svg'), bbox_inches='tight')
    print(f"✅ Saved P@K chart: {output_path}")

def main():
    print("=" * 80)
    print("🔥 TASK 4: PRECISION@K ANALYSIS")
    print("=" * 80)
    
    rules, scores = load_data()
    
    # Compute P@K per step
    results_df = analyze_per_step_precision_at_k(rules, scores)
    print(f"\n✅ Computed P@K for {len(results_df)} steps:")
    print(results_df.to_string(index=False))
    
    # Macro-averaged P@K
    print("\n📊 Macro-averaged Precision@K:")
    for k in [3, 5, 10]:
        col = f'P@{k}'
        if col in results_df.columns:
            mean_pk = results_df[col].mean()
            std_pk = results_df[col].std()
            print(f"   P@{k}: {mean_pk:.3f} ± {std_pk:.3f}")
    
    # Save results
    results_df.to_csv(DATA_DIR / "precision_at_k.csv", index=False)
    print(f"\n✅ Saved results: {DATA_DIR / 'precision_at_k.csv'}")
    
    # Plot
    output_path = OUTPUT_DIR / "figure2c_precision_at_k.png"
    plot_precision_at_k_bars(results_df, output_path)
    
    print("\n✅ TASK 4 COMPLETE: Precision@K Analysis Done")
    print("=" * 80)

if __name__ == "__main__":
    main()


