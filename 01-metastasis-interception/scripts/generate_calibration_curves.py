#!/usr/bin/env python3
"""
Calibration Curves (Reliability Diagrams)

Generate calibration curves showing predicted probability vs observed frequency
to assess model calibration per metastatic step.

Author: Zo
Date: October 13, 2025
"""

import json
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
from sklearn.calibration import calibration_curve

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

def generate_calibration_curves(rules, scores):
    """Generate calibration curves for each step"""
    fig, axes = plt.subplots(2, 4, figsize=(20, 10))
    axes = axes.flatten()
    
    steps = list(rules['steps'].keys())
    
    for idx, step in enumerate(steps):
        ax = axes[idx]
        
        # Get labels
        step_data = rules['steps'][step]
        primary = set(step_data.get('primary_genes', []))
        secondary = set(step_data.get('secondary_genes', []))
        relevant = primary | secondary
        
        # Get scores for this step
        step_scores = scores[scores['step'] == step].copy()
        if len(step_scores) == 0:
            ax.text(0.5, 0.5, 'Insufficient data', ha='center', va='center')
            ax.set_title(step.replace('_', ' ').title())
            continue
        
        step_scores['label'] = step_scores['gene'].apply(lambda g: 1 if g in relevant else 0)
        
        y_true = step_scores['label'].values
        y_prob = step_scores['target_lock_score'].values
        
        if len(np.unique(y_true)) < 2:
            ax.text(0.5, 0.5, 'Only one class', ha='center', va='center')
            ax.set_title(step.replace('_', ' ').title())
            continue
        
        # Compute calibration curve
        try:
            fraction_of_positives, mean_predicted_value = calibration_curve(
                y_true, y_prob, n_bins=5, strategy='quantile'
            )
            
            # Plot
            ax.plot([0, 1], [0, 1], 'k--', linewidth=1, label='Perfect calibration')
            ax.plot(mean_predicted_value, fraction_of_positives, 'o-', linewidth=2, 
                   label='Model', color='#1f77b4')
            
            ax.set_xlabel('Mean Predicted Score', fontsize=10)
            ax.set_ylabel('Fraction of Positives', fontsize=10)
            ax.set_title(step.replace('_', ' ').title(), fontsize=11)
            ax.legend(loc='lower right', fontsize=8)
            ax.grid(alpha=0.3)
            ax.set_xlim([0, 1])
            ax.set_ylim([0, 1])
        except Exception as e:
            ax.text(0.5, 0.5, f'Error: {str(e)}', ha='center', va='center', fontsize=8)
            ax.set_title(step.replace('_', ' ').title())
    
    plt.suptitle('Calibration Curves: Predicted Score vs Observed Frequency\n(Closer to diagonal = better calibrated)', 
                 fontsize=14, y=1.00)
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "figure_s2_calibration_curves.png", dpi=300, bbox_inches='tight')
    plt.savefig(OUTPUT_DIR / "figure_s2_calibration_curves.svg", bbox_inches='tight')
    print(f"✅ Saved calibration curves: {OUTPUT_DIR / 'figure_s2_calibration_curves.png'}")

def main():
    print("=" * 80)
    print("🔥 DAY 2: CALIBRATION CURVES")
    print("=" * 80)
    
    rules, scores = load_data()
    generate_calibration_curves(rules, scores)
    
    print("\n✅ DAY 2 TASK 1 COMPLETE: Calibration Curves Generated")
    print("=" * 80)

if __name__ == "__main__":
    main()


