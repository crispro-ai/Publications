#!/usr/bin/env python3
"""
Effect Sizes (Cohen's d)

Compute Cohen's d effect sizes for signal differences between relevant
and non-relevant genes per step.

Author: Zo
Date: October 13, 2025
"""

import json
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

SEED = 42
np.random.seed(SEED)

OUTPUT_DIR = Path("publication/figures")
DATA_DIR = Path("publication/data")

def cohens_d(group1, group2):
    """Compute Cohen's d effect size"""
    n1, n2 = len(group1), len(group2)
    var1, var2 = np.var(group1, ddof=1), np.var(group2, ddof=1)
    pooled_std = np.sqrt(((n1 - 1) * var1 + (n2 - 1) * var2) / (n1 + n2 - 2))
    
    if pooled_std == 0:
        return 0.0
    
    return (np.mean(group1) - np.mean(group2)) / pooled_std

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

def compute_effect_sizes(rules, scores):
    """Compute Cohen's d for each step and signal"""
    results = []
    steps = list(rules['steps'].keys())
    signals = ['functionality', 'essentiality', 'chromatin', 'regulatory', 'target_lock_score']
    
    for step in steps:
        step_data = rules['steps'][step]
        primary = set(step_data.get('primary_genes', []))
        secondary = set(step_data.get('secondary_genes', []))
        relevant = primary | secondary
        
        step_scores = scores[scores['step'] == step].copy()
        if len(step_scores) == 0:
            continue
        
        step_scores['is_relevant'] = step_scores['gene'].apply(lambda g: 1 if g in relevant else 0)
        
        relevant_genes = step_scores[step_scores['is_relevant'] == 1]
        non_relevant_genes = step_scores[step_scores['is_relevant'] == 0]
        
        if len(relevant_genes) == 0 or len(non_relevant_genes) == 0:
            continue
        
        for signal in signals:
            if signal not in step_scores.columns:
                continue
            
            relevant_vals = relevant_genes[signal].values
            non_relevant_vals = non_relevant_genes[signal].values
            
            d = cohens_d(relevant_vals, non_relevant_vals)
            
            # Interpretation
            if abs(d) < 0.2:
                interpretation = "negligible"
            elif abs(d) < 0.5:
                interpretation = "small"
            elif abs(d) < 0.8:
                interpretation = "medium"
            else:
                interpretation = "large"
            
            results.append({
                'step': step,
                'signal': signal,
                'cohens_d': d,
                'interpretation': interpretation,
                'n_relevant': len(relevant_vals),
                'n_non_relevant': len(non_relevant_vals),
                'mean_relevant': np.mean(relevant_vals),
                'mean_non_relevant': np.mean(non_relevant_vals)
            })
    
    return pd.DataFrame(results)

def plot_effect_sizes(results_df, output_path):
    """Plot effect sizes as grouped bar chart"""
    # Pivot for multi-signal display
    pivot = results_df.pivot(index='step', columns='signal', values='cohens_d')
    
    fig, ax = plt.subplots(figsize=(16, 8))
    
    pivot.plot(kind='bar', ax=ax, width=0.8, alpha=0.8)
    
    ax.axhline(0, color='black', linewidth=0.8, linestyle='--')
    ax.axhline(0.2, color='gray', linewidth=0.5, linestyle=':', alpha=0.5)
    ax.axhline(-0.2, color='gray', linewidth=0.5, linestyle=':', alpha=0.5)
    ax.axhline(0.5, color='gray', linewidth=0.5, linestyle=':', alpha=0.5)
    ax.axhline(-0.5, color='gray', linewidth=0.5, linestyle=':', alpha=0.5)
    
    ax.set_xlabel('Metastatic Step', fontsize=12)
    ax.set_ylabel("Cohen's d (Effect Size)", fontsize=12)
    ax.set_title("Effect Sizes: Relevant vs Non-Relevant Genes by Step\n(|d| > 0.5 = medium effect, |d| > 0.8 = large effect)", 
                 fontsize=14)
    ax.set_xticklabels([s.replace('_', ' ').title() for s in pivot.index], rotation=45, ha='right')
    ax.legend(title='Signal', bbox_to_anchor=(1.05, 1), loc='upper left')
    ax.grid(axis='y', alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.savefig(output_path.with_suffix('.svg'), bbox_inches='tight')
    print(f"✅ Saved effect sizes plot: {output_path}")

def main():
    print("=" * 80)
    print("🔥 DAY 2: EFFECT SIZES (COHEN'S D)")
    print("=" * 80)
    
    rules, scores = load_data()
    results_df = compute_effect_sizes(rules, scores)
    
    print(f"\n✅ Computed effect sizes for {len(results_df)} step-signal combinations")
    print("\n📊 Effect Size Summary:")
    
    for step in results_df['step'].unique():
        step_results = results_df[results_df['step'] == step]
        print(f"\n   {step}:")
        for _, row in step_results.iterrows():
            print(f"      {row['signal']:20s}: d = {row['cohens_d']:+.3f} ({row['interpretation']})")
    
    # Save results
    results_df.to_csv(DATA_DIR / "effect_sizes.csv", index=False)
    print(f"\n✅ Saved results: {DATA_DIR / 'effect_sizes.csv'}")
    
    # Plot
    output_path = OUTPUT_DIR / "figure_s3_effect_sizes.png"
    plot_effect_sizes(results_df, output_path)
    
    print("\n✅ DAY 2 TASK 2 COMPLETE: Effect Sizes Computed")
    print("=" * 80)

if __name__ == "__main__":
    main()


