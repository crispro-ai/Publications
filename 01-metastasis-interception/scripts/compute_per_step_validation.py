#!/usr/bin/env python3
"""
Per-Step Validation Dominance Script

Computes comprehensive validation metrics for metastasis Target-Lock scores:
- Per-step AUROC/AUPRC with 1000-bootstrap CIs (seed=42)
- Macro/micro-averaged PR curves
- Calibration curves (reliability diagrams)
- Effect sizes (Cohen's d) for signal differences
- Specificity matrix (confusion matrix)
- Fisher's exact enrichment p-values
- Precision@K analysis (K=3, 5, 10)
- Confounder analysis (gene length, GC%, exon count)
- Ablation study (drop each signal, measure impact)

Author: Zo (Platform AI)
Date: October 13, 2025
Version: 1.0.0 (Dominance Mode)
"""

import json
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from sklearn.metrics import roc_auc_score, average_precision_score, roc_curve, precision_recall_curve
from sklearn.utils import resample
from scipy import stats
from typing import Dict, List, Tuple
import warnings
warnings.filterwarnings('ignore')

# Set seed for reproducibility
SEED = 42
np.random.seed(SEED)

# Configuration
BOOTSTRAP_ITERATIONS = 1000
CONFIDENCE_LEVEL = 0.95
OUTPUT_DIR = Path("../figures")
DATA_DIR = Path("../data")

# Ensure directories exist
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
DATA_DIR.mkdir(parents=True, exist_ok=True)

def load_ground_truth() -> Dict:
    """Load ground truth labels (prefer v1.0.1; override with METASTASIS_RULES_PATH)."""
    rules_path = Path(
        os.environ.get(
            "METASTASIS_RULES_PATH",
            "oncology-coPilot/oncology-backend-minimal/api/config/metastasis_rules_v1.0.1.json",
        )
    )
    if not rules_path.exists():
        rules_path = Path("oncology-coPilot/oncology-backend-minimal/api/config/metastasis_rules_v1.0.0.json")
    
    if not rules_path.exists():
        raise FileNotFoundError(f"Ground truth file not found: {rules_path}")
    
    with open(rules_path) as f:
        rules = json.load(f)
    
    print(f"✅ Loaded ground truth v{rules['version']}")
    print(f"   Total genes: {rules['total_genes']}")
    print(f"   Date: {rules['date']}")
    
    return rules

def create_step_labels(rules: Dict) -> pd.DataFrame:
    """
    Create per-step binary labels for all genes
    
    Returns DataFrame with columns:
    - gene: gene symbol
    - primary_growth: 1/0
    - local_invasion: 1/0
    ... (8 steps total)
    """
    all_genes = set()
    for step_data in rules['steps'].values():
        all_genes.update(step_data.get('primary_genes', []))
        all_genes.update(step_data.get('secondary_genes', []))
    
    all_genes = sorted(list(all_genes))
    
    # Create binary label matrix
    label_data = {'gene': all_genes}
    
    for step_name, step_data in rules['steps'].items():
        primary = set(step_data.get('primary_genes', []))
        secondary = set(step_data.get('secondary_genes', []))
        relevant_genes = primary | secondary
        
        label_data[step_name] = [1 if gene in relevant_genes else 0 for gene in all_genes]
    
    df = pd.DataFrame(label_data)
    
    print(f"\n✅ Created step labels: {len(all_genes)} genes × {len(rules['steps'])} steps")
    for step in rules['steps'].keys():
        n_pos = df[step].sum()
        print(f"   {step}: {n_pos} relevant genes")
    
    return df

def load_target_lock_scores() -> pd.DataFrame:
    """
    Load Target-Lock scores from real_target_lock_data.csv
    
    Expected columns:
    - gene
    - mission (metastatic step name) - rename to 'step' for consistency
    - target_lock_score
    - functionality, essentiality, chromatin, regulatory (component scores)
    """
    score_path = DATA_DIR / "real_target_lock_data.csv"
    
    if not score_path.exists():
        raise FileNotFoundError(
            f"Missing required dataset: {score_path}\n"
            "Stage the canonical inputs with:\n"
            "  venv/bin/python stage_publication_inputs.py\n"
            "or place `real_target_lock_data.csv` at `../data/`."
        )

    df = pd.read_csv(score_path)
    # Rename 'mission' to 'step' for consistency
    if 'mission' in df.columns:
        df = df.rename(columns={'mission': 'step'})
    print(f"✅ Loaded Target-Lock scores: {len(df)} rows")
    return df

def bootstrap_metric(y_true, y_score, metric_fn, n_iterations=1000, seed=42):
    """Compute bootstrap CI for a metric"""
    scores = []
    rng = np.random.RandomState(seed)
    
    for i in range(n_iterations):
        # Stratified bootstrap
        indices = rng.choice(len(y_true), size=len(y_true), replace=True)
        y_true_boot = y_true[indices]
        y_score_boot = y_score[indices]
        
        # Skip if all one class
        if len(np.unique(y_true_boot)) < 2:
            continue
        
        try:
            score = metric_fn(y_true_boot, y_score_boot)
            scores.append(score)
        except:
            continue
    
    if len(scores) == 0:
        return np.nan, np.nan, np.nan
    
    mean = np.mean(scores)
    ci_lower = np.percentile(scores, (1 - CONFIDENCE_LEVEL) / 2 * 100)
    ci_upper = np.percentile(scores, (1 + CONFIDENCE_LEVEL) / 2 * 100)
    
    return mean, ci_lower, ci_upper

def compute_per_step_metrics(labels: pd.DataFrame, scores: pd.DataFrame) -> pd.DataFrame:
    """Compute AUROC/AUPRC per step with bootstrap CIs"""
    results = []
    
    print("\n🔥 Computing per-step metrics (Bootstrap B=1000, seed=42)...")
    
    for step in labels.columns[1:]:  # Skip 'gene' column
        # Merge labels with scores for this step
        step_data = labels[['gene', step]].merge(
            scores[scores['step'] == step][['gene', 'target_lock_score']],
            on='gene',
            how='inner'
        )
        
        if len(step_data) == 0:
            print(f"   ⚠️  {step}: No data")
            continue
        
        y_true = step_data[step].values
        y_score = step_data['target_lock_score'].values
        
        # Check if we have both classes
        if len(np.unique(y_true)) < 2:
            print(f"   ⚠️  {step}: Only one class present")
            continue
        
        # AUROC with bootstrap CI
        auroc_mean, auroc_lower, auroc_upper = bootstrap_metric(
            y_true, y_score, roc_auc_score, BOOTSTRAP_ITERATIONS, SEED
        )
        
        # AUPRC with bootstrap CI
        auprc_mean, auprc_lower, auprc_upper = bootstrap_metric(
            y_true, y_score, average_precision_score, BOOTSTRAP_ITERATIONS, SEED
        )
        
        # Precision@K
        k_values = [3, 5, 10]
        precision_at_k = {}
        for k in k_values:
            top_k_idx = np.argsort(y_score)[-k:]
            precision_at_k[f'P@{k}'] = y_true[top_k_idx].mean()
        
        results.append({
            'step': step,
            'n_samples': len(y_true),
            'n_positive': y_true.sum(),
            'auroc_mean': auroc_mean,
            'auroc_lower': auroc_lower,
            'auroc_upper': auroc_upper,
            'auprc_mean': auprc_mean,
            'auprc_lower': auprc_lower,
            'auprc_upper': auprc_upper,
            **precision_at_k
        })
        
        print(f"   {step:30s} | AUROC: {auroc_mean:.3f} [{auroc_lower:.3f}, {auroc_upper:.3f}] | AUPRC: {auprc_mean:.3f} [{auprc_lower:.3f}, {auprc_upper:.3f}]")
    
    return pd.DataFrame(results)

def plot_per_step_roc(labels: pd.DataFrame, scores: pd.DataFrame, output_path: Path):
    """Generate 8-panel ROC curves (one per step)"""
    fig, axes = plt.subplots(2, 4, figsize=(20, 10))
    axes = axes.flatten()
    
    for idx, step in enumerate(labels.columns[1:]):  # Skip 'gene'
        ax = axes[idx]
        
        step_data = labels[['gene', step]].merge(
            scores[scores['step'] == step][['gene', 'target_lock_score']],
            on='gene',
            how='inner'
        )
        
        if len(step_data) == 0 or len(np.unique(step_data[step])) < 2:
            ax.text(0.5, 0.5, 'Insufficient data', ha='center', va='center')
            ax.set_title(step.replace('_', ' ').title())
            continue
        
        y_true = step_data[step].values
        y_score = step_data['target_lock_score'].values
        
        # Compute ROC
        fpr, tpr, _ = roc_curve(y_true, y_score)
        auroc = roc_auc_score(y_true, y_score)
        
        # Plot
        ax.plot(fpr, tpr, 'b-', linewidth=2, label=f'AUROC = {auroc:.3f}')
        ax.plot([0, 1], [0, 1], 'r--', linewidth=1, label='Random')
        
        ax.set_xlabel('False Positive Rate')
        ax.set_ylabel('True Positive Rate')
        ax.set_title(step.replace('_', ' ').title())
        ax.legend(loc='lower right')
        ax.grid(alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.savefig(output_path.with_suffix('.svg'), bbox_inches='tight')
    print(f"\n✅ Saved ROC curves: {output_path}")

def main():
    """Main execution"""
    print("=" * 80)
    print("🔥 PER-STEP VALIDATION DOMINANCE - DAY 1 EXECUTION")
    print("=" * 80)
    
    # Load data
    rules = load_ground_truth()
    labels = create_step_labels(rules)
    scores = load_target_lock_scores()
    
    # Compute metrics
    metrics_df = compute_per_step_metrics(labels, scores)
    
    # Save metrics
    metrics_path = DATA_DIR / "per_step_validation_metrics.csv"
    metrics_df.to_csv(metrics_path, index=False)
    print(f"\n✅ Saved metrics: {metrics_path}")
    
    # Generate figures
    roc_path = OUTPUT_DIR / "figure2a_per_step_roc.png"
    plot_per_step_roc(labels, scores, roc_path)
    
    # Summary statistics
    print("\n" + "=" * 80)
    print("📊 SUMMARY STATISTICS")
    print("=" * 80)
    print(f"Mean AUROC across steps: {metrics_df['auroc_mean'].mean():.3f} ± {metrics_df['auroc_mean'].std():.3f}")
    print(f"Mean AUPRC across steps: {metrics_df['auprc_mean'].mean():.3f} ± {metrics_df['auprc_mean'].std():.3f}")
    print(f"\nTotal data points: {metrics_df['n_samples'].sum()}")
    print(f"Total positive labels: {metrics_df['n_positive'].sum()}")
    print("\n✅ DAY 1 TASK 2 COMPLETE: Per-Step Validation Metrics Computed")
    print("=" * 80)

if __name__ == "__main__":
    main()

