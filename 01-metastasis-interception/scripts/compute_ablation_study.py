#!/usr/bin/env python3
"""
Ablation Study: Signal Importance

Drop each signal (functionality, chromatin, essentiality, regulatory) and measure impact:
- Recompute Target-Lock scores without each signal
- Measure AUROC drop per signal per step
- Rank signal importance with confidence intervals

Author: Zo
Date: October 13, 2025
"""

import json
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
from sklearn.metrics import roc_auc_score

SEED = 42
np.random.seed(SEED)

OUTPUT_DIR = Path("publication/figures")
DATA_DIR = Path("publication/data")

WEIGHTS = {
    'functionality': 0.35,
    'essentiality': 0.35,
    'chromatin': 0.15,
    'regulatory': 0.15
}

SIGNALS = ['functionality', 'essentiality', 'chromatin', 'regulatory']

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

def recompute_target_lock(scores_df, exclude_signal=None):
    """Recompute Target-Lock score excluding one signal"""
    weights = WEIGHTS.copy()
    
    if exclude_signal:
        # Zero out excluded signal and renormalize
        weights[exclude_signal] = 0
        total = sum(weights.values())
        weights = {k: v/total for k, v in weights.items()}
    
    new_scores = (
        scores_df['functionality'] * weights['functionality'] +
        scores_df['essentiality'] * weights['essentiality'] +
        scores_df['chromatin'] * weights['chromatin'] +
        scores_df['regulatory'] * weights['regulatory']
    )
    
    return new_scores

def compute_ablation_per_step(rules, scores):
    """Compute AUROC drop for each signal per step"""
    results = []
    steps = list(rules['steps'].keys())
    
    for step in steps:
        # Get labels
        step_data = rules['steps'][step]
        primary = set(step_data.get('primary_genes', []))
        secondary = set(step_data.get('secondary_genes', []))
        relevant = primary | secondary
        
        # Get scores for this step
        step_scores = scores[scores['step'] == step].copy()
        if len(step_scores) == 0:
            continue
        
        step_scores['label'] = step_scores['gene'].apply(lambda g: 1 if g in relevant else 0)
        
        y_true = step_scores['label'].values
        
        if len(np.unique(y_true)) < 2:
            continue
        
        # Baseline AUROC (all signals)
        y_full = step_scores['target_lock_score'].values
        try:
            auroc_full = roc_auc_score(y_true, y_full)
        except:
            continue
        
        result = {'step': step, 'auroc_full': auroc_full}
        
        # Ablation for each signal
        for signal in SIGNALS:
            y_ablated = recompute_target_lock(step_scores, exclude_signal=signal).values
            try:
                auroc_ablated = roc_auc_score(y_true, y_ablated)
                delta = auroc_full - auroc_ablated
                result[f'{signal}_auroc'] = auroc_ablated
                result[f'{signal}_delta'] = delta
            except:
                result[f'{signal}_auroc'] = np.nan
                result[f'{signal}_delta'] = np.nan
        
        results.append(result)
    
    return pd.DataFrame(results)

def plot_ablation_bars(results_df, output_path):
    """Plot ablation impact as grouped bar chart"""
    fig, ax = plt.subplots(figsize=(14, 8))
    
    # Compute mean delta per signal
    signal_deltas = {}
    for signal in SIGNALS:
        col = f'{signal}_delta'
        if col in results_df.columns:
            mean_delta = results_df[col].mean()
            std_delta = results_df[col].std()
            signal_deltas[signal] = (mean_delta, std_delta)
    
    # Sort by impact
    sorted_signals = sorted(signal_deltas.items(), key=lambda x: abs(x[1][0]), reverse=True)
    
    signals_sorted = [s[0] for s in sorted_signals]
    means = [s[1][0] for s in sorted_signals]
    stds = [s[1][1] for s in sorted_signals]
    
    x = np.arange(len(signals_sorted))
    colors = ['#d62728' if m < 0 else '#2ca02c' for m in means]
    
    bars = ax.bar(x, means, yerr=stds, color=colors, alpha=0.7, capsize=5)
    
    ax.axhline(0, color='black', linewidth=0.8, linestyle='--')
    ax.set_xlabel('Signal', fontsize=12)
    ax.set_ylabel('AUROC Drop When Excluded (Δ)', fontsize=12)
    ax.set_title('Ablation Study: Signal Importance\n(Larger drop = More important signal)', fontsize=14)
    ax.set_xticks(x)
    ax.set_xticklabels([s.title() for s in signals_sorted])
    ax.grid(axis='y', alpha=0.3)
    
    # Add value labels
    for i, (bar, mean, std) in enumerate(zip(bars, means, stds)):
        height = bar.get_height()
        label = f'{mean:.3f}'
        ax.text(bar.get_x() + bar.get_width()/2., height,
                label, ha='center', va='bottom' if height > 0 else 'top', fontsize=10)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.savefig(output_path.with_suffix('.svg'), bbox_inches='tight')
    print(f"✅ Saved ablation chart: {output_path}")

def main():
    print("=" * 80)
    print("🔥 TASK 5: ABLATION STUDY")
    print("=" * 80)
    
    rules, scores = load_data()
    
    # Compute ablation per step
    results_df = compute_ablation_per_step(rules, scores)
    print(f"\n✅ Computed ablation for {len(results_df)} steps")
    
    # Print per-step results
    print("\n📊 Per-Step AUROC Drops:")
    for _, row in results_df.iterrows():
        print(f"\n   {row['step']}:")
        print(f"      Full model: {row['auroc_full']:.3f}")
        for signal in SIGNALS:
            delta_col = f'{signal}_delta'
            if delta_col in row and not pd.isna(row[delta_col]):
                print(f"      -{signal:15s}: Δ = {row[delta_col]:+.3f}")
    
    # Aggregate signal importance
    print("\n📊 Signal Importance Ranking (Mean AUROC Drop):")
    signal_importance = []
    for signal in SIGNALS:
        delta_col = f'{signal}_delta'
        if delta_col in results_df.columns:
            mean_delta = results_df[delta_col].mean()
            std_delta = results_df[delta_col].std()
            signal_importance.append((signal, mean_delta, std_delta))
            print(f"   {signal:15s}: {mean_delta:+.3f} ± {std_delta:.3f}")
    
    # Sort and display ranking
    signal_importance.sort(key=lambda x: abs(x[1]), reverse=True)
    print("\n🏆 Importance Ranking (most → least):")
    for i, (signal, mean, std) in enumerate(signal_importance, 1):
        print(f"   {i}. {signal.title():15s} (Δ = {mean:+.3f})")
    
    # Save results
    results_df.to_csv(DATA_DIR / "ablation_study.csv", index=False)
    print(f"\n✅ Saved results: {DATA_DIR / 'ablation_study.csv'}")
    
    # Plot
    output_path = OUTPUT_DIR / "figure2d_ablation.png"
    plot_ablation_bars(results_df, output_path)
    
    print("\n✅ TASK 5 COMPLETE: Ablation Study Done")
    print("=" * 80)

if __name__ == "__main__":
    main()


