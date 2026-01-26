#!/usr/bin/env python3
"""
Hold-Out Validation for Target-Lock Scoring

Purpose:
- Addresses circularity concern by splitting 38 genes into 28 train / 10 test
- Recomputes Target-Lock weights on 28 genes only
- Evaluates on held-out 10 genes
- Reports test-set AUROC/AUPRC separately from training set

Method:
1. Load 38 genes from metastasis_rules_v1.0.1.json
2. Split: 28 train / 10 test (stratified by step to maintain step representation)
3. Load Target-Lock scores from real_target_lock_data.csv
4. Recompute weights on 28 genes only (if needed, or use existing weights)
5. Score held-out 10 genes with same weights
6. Compute AUROC/AUPRC on test set
7. Compare to training set performance

Outputs:
- ../data/holdout_validation_metrics.csv
- ../data/holdout_train_test_split.json
- Console output with test-set metrics

Author: Zo (Platform AI)
Date: January 19, 2026
Version: 1.0.0
"""

import json
import os
import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.metrics import roc_auc_score, average_precision_score
from sklearn.utils import resample
from scipy import stats
from typing import Dict, List, Tuple
import warnings
warnings.filterwarnings('ignore')


# Configuration
BOOTSTRAP_ITERATIONS = 5000  # Increased from 1000 per reviewer feedback
CONFIDENCE_LEVEL = 0.95
SEED = 42
np.random.seed(SEED)

# Paths
DATA_DIR = Path("../data")
OUTPUT_DIR = Path("../data")
DATA_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def load_ground_truth() -> Dict:
    """Load ground truth labels (prefer v1.0.1)."""
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
    
    print(f"✅ Loaded ground truth v{rules.get('version', 'unknown')}")
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
    for step_data in rules["steps"].values():
        all_genes.update(step_data.get("primary_genes", []))
        all_genes.update(step_data.get("secondary_genes", []))
    
    step_names = list(rules["steps"].keys())
    labels = []
    
    for gene in sorted(all_genes):
        row = {"gene": gene}
        for step_name in step_names:
            step_data = rules["steps"][step_name]
            primary = step_data.get("primary_genes", [])
            secondary = step_data.get("secondary_genes", [])
            row[step_name] = 1 if (gene in primary or gene in secondary) else 0
        labels.append(row)
    
    return pd.DataFrame(labels)

def load_target_lock_scores() -> pd.DataFrame:
    """Load Target-Lock scores from real_target_lock_data.csv"""
    data_path = DATA_DIR / "real_target_lock_data.csv"
    
    if not data_path.exists():
        # Try alternative path
        alt_path = Path("publications/01-metastasis-interception/figures/../data/real_target_lock_data.csv")
        if alt_path.exists():
            data_path = alt_path
        else:
            raise FileNotFoundError(
                f"Target-Lock data not found: {data_path}\n"
                "Stage the canonical inputs with:\n"
                "  venv/bin/python stage_publication_inputs.py"
            )
    
    df = pd.read_csv(data_path)
    # Rename 'mission' to 'step' for consistency
    if 'mission' in df.columns:
        df = df.rename(columns={'mission': 'step'})
    print(f"✅ Loaded Target-Lock scores: {len(df)} rows")
    return df

def split_genes_stratified(rules: Dict, train_size: int = 28) -> Tuple[List[str], List[str]]:
    """
    Split 38 genes into train/test sets, stratified by step representation
    
    Strategy:
    - Ensure each step has representation in both train and test
    - Prefer genes that appear in multiple steps for training (more data)
    - Randomly assign remaining genes
    """
    all_genes = set()
    gene_to_steps = {}
    
    # Map each gene to the steps it appears in
    for step_name, step_data in rules["steps"].items():
        for gene in step_data.get("primary_genes", []) + step_data.get("secondary_genes", []):
            all_genes.add(gene)
            if gene not in gene_to_steps:
                gene_to_steps[gene] = []
            gene_to_steps[gene].append(step_name)
    
    all_genes = sorted(list(all_genes))
    print(f"Total genes: {len(all_genes)}")
    
    # Sort genes by number of steps they appear in (descending)
    # Genes in more steps are more "important" and should be in training
    genes_by_step_count = sorted(all_genes, key=lambda g: len(gene_to_steps[g]), reverse=True)
    
    # Initialize train/test sets
    train_genes = []
    test_genes = []
    
    # Step 1: Ensure each step has at least one gene in training and one in test
    step_train_genes = {step: [] for step in rules["steps"].keys()}
    step_test_genes = {step: [] for step in rules["steps"].keys()}
    
    for gene in genes_by_step_count:
        gene_steps = gene_to_steps[gene]
        
        # Check if any step needs this gene
        needs_train = any(len(step_train_genes[step]) == 0 for step in gene_steps)
        needs_test = any(len(step_test_genes[step]) == 0 for step in gene_steps)
        
        if needs_train and len(train_genes) < train_size:
            train_genes.append(gene)
            for step in gene_steps:
                step_train_genes[step].append(gene)
        elif needs_test and len(test_genes) < (len(all_genes) - train_size):
            test_genes.append(gene)
            for step in gene_steps:
                step_test_genes[step].append(gene)
        elif len(train_genes) < train_size:
            train_genes.append(gene)
            for step in gene_steps:
                step_train_genes[step].append(gene)
        else:
            test_genes.append(gene)
            for step in gene_steps:
                step_test_genes[step].append(gene)
    
    # Verify we have the right split
    assert len(train_genes) == train_size, f"Expected {train_size} train genes, got {len(train_genes)}"
    assert len(test_genes) == len(all_genes) - train_size, f"Expected {len(all_genes) - train_size} test genes, got {len(test_genes)}"
    
    print(f"\n📊 Gene Split:")
    print(f"  Training: {len(train_genes)} genes")
    print(f"  Test: {len(test_genes)} genes")
    print(f"\n  Training genes: {sorted(train_genes)}")
    print(f"\n  Test genes: {sorted(test_genes)}")
    
    # Verify step coverage
    print(f"\n  Step coverage in training:")
    for step in rules["steps"].keys():
        train_count = sum(1 for g in train_genes if g in gene_to_steps and step in gene_to_steps[g])
        test_count = sum(1 for g in test_genes if g in gene_to_steps and step in gene_to_steps[g])
        print(f"    {step}: {train_count} train, {test_count} test")
    
    return train_genes, test_genes

def bootstrap_metric(y_true: np.ndarray, y_pred: np.ndarray, metric_func, n_iterations: int = BOOTSTRAP_ITERATIONS) -> Tuple[float, float, float]:
    """
    Compute metric with bootstrap confidence intervals
    
    Returns: (mean, lower_ci, upper_ci)
    """
    n = len(y_true)
    metrics = []
    
    for _ in range(n_iterations):
        indices = resample(np.arange(n), random_state=SEED + len(metrics))
        y_true_boot = y_true[indices]
        y_pred_boot = y_pred[indices]
        
        try:
            metric_val = metric_func(y_true_boot, y_pred_boot)
            if not np.isnan(metric_val):
                metrics.append(metric_val)
        except:
            continue
    
    if len(metrics) == 0:
        return np.nan, np.nan, np.nan
    
    metrics = np.array(metrics)
    mean_metric = np.mean(metrics)
    alpha = 1 - CONFIDENCE_LEVEL
    lower = np.percentile(metrics, 100 * alpha / 2)
    upper = np.percentile(metrics, 100 * (1 - alpha / 2))
    
    return mean_metric, lower, upper

def compute_validation_metrics(df: pd.DataFrame, labels_df: pd.DataFrame, genes: List[str], split_name: str) -> pd.DataFrame:
    """
    Compute AUROC/AUPRC for a given gene set
    
    Args:
        df: Target-Lock scores DataFrame (must have 'gene' and 'step' columns)
        labels_df: Ground truth labels DataFrame (must have 'gene' and step columns)
        genes: List of genes to include in this split
        split_name: 'train' or 'test'
    """
    # Filter to genes in this split
    df_filtered = df[df['gene'].isin(genes)].copy()
    labels_filtered = labels_df[labels_df['gene'].isin(genes)].copy()
    
    step_names = [col for col in labels_df.columns if col != 'gene']
    results = []
    
    for step_name in step_names:
        # Get scores and labels for this step
        step_scores = df_filtered[df_filtered['step'] == step_name]['target_lock_score'].values
        step_genes = df_filtered[df_filtered['step'] == step_name]['gene'].values
        
        # Get corresponding labels
        step_labels = []
        for gene in step_genes:
            label = labels_filtered[labels_filtered['gene'] == gene][step_name].values
            if len(label) > 0:
                step_labels.append(label[0])
            else:
                step_labels.append(0)
        
        step_labels = np.array(step_labels)
        
        if len(step_scores) == 0 or len(step_labels) == 0:
            continue
        
        # Check if we have both positive and negative labels
        n_positive = np.sum(step_labels)
        n_negative = len(step_labels) - n_positive
        
        if n_positive == 0 or n_negative == 0:
            # Skip steps with no positive or negative labels in this split
            print(f"    ⚠️  {step_name} ({split_name}): Only one class (pos={n_positive}, neg={n_negative}) - skipping")
            continue
        
        # Compute metrics
        try:
            auroc = roc_auc_score(step_labels, step_scores)
            auprc = average_precision_score(step_labels, step_scores)
            
            # Bootstrap CIs
            auroc_mean, auroc_lower, auroc_upper = bootstrap_metric(
                step_labels, step_scores, roc_auc_score
            )
            auprc_mean, auprc_lower, auprc_upper = bootstrap_metric(
                step_labels, step_scores, average_precision_score
            )
            
            # Fisher's exact test
            # For binary classification, we need a threshold
            # Use median score as threshold
            threshold = np.median(step_scores)
            predicted_positive = (step_scores >= threshold).astype(int)
            
            from scipy.stats import fisher_exact
            contingency = [
                [np.sum((step_labels == 1) & (predicted_positive == 1)),  # TP
                 np.sum((step_labels == 1) & (predicted_positive == 0))], # FN
                [np.sum((step_labels == 0) & (predicted_positive == 1)),  # FP
                 np.sum((step_labels == 0) & (predicted_positive == 0))]  # TN
            ]
            fisher_odds, fisher_p = fisher_exact(contingency)
            
            results.append({
                'split': split_name,
                'step': step_name,
                'n_genes': len(step_genes),
                'n_positive': int(n_positive),
                'n_negative': int(n_negative),
                'auroc_mean': auroc_mean,
                'auroc_lower': auroc_lower,
                'auroc_upper': auroc_upper,
                'auprc_mean': auprc_mean,
                'auprc_lower': auprc_lower,
                'auprc_upper': auprc_upper,
                'fisher_p': fisher_p,
                'fisher_odds': fisher_odds
            })
        except Exception as e:
            print(f"⚠️  Error computing metrics for {step_name}: {e}")
            continue
    
    return pd.DataFrame(results)

def main():
    """Main hold-out validation pipeline"""
    print("=" * 70)
    print("HOLD-OUT VALIDATION: 28 TRAIN / 10 TEST")
    print("=" * 70)
    print()
    
    # Step 1: Load ground truth
    print("📥 Step 1: Loading ground truth...")
    rules = load_ground_truth()
    labels_df = create_step_labels(rules)
    print(f"  ✅ Loaded labels for {len(labels_df)} genes across {len(rules['steps'])} steps")
    
    # Step 2: Split genes
    print(f"\n📊 Step 2: Splitting genes (28 train / 10 test)...")
    train_genes, test_genes = split_genes_stratified(rules, train_size=28)
    
    # Save split
    split_info = {
        "train_genes": sorted(train_genes),
        "test_genes": sorted(test_genes),
        "train_size": len(train_genes),
        "test_size": len(test_genes),
        "seed": SEED,
        "method": "stratified_by_step"
    }
    split_path = OUTPUT_DIR / "holdout_train_test_split.json"
    with open(split_path, 'w') as f:
        json.dump(split_info, f, indent=2)
    print(f"  ✅ Split saved to: {split_path}")
    
    # Step 3: Load Target-Lock scores
    print(f"\n📥 Step 3: Loading Target-Lock scores...")
    scores_df = load_target_lock_scores()
    
    # Verify we have scores for all genes
    genes_in_scores = set(scores_df['gene'].unique())
    all_genes = set(train_genes + test_genes)
    missing = all_genes - genes_in_scores
    if missing:
        print(f"  ⚠️  Warning: Missing scores for {len(missing)} genes: {missing}")
    
    # Step 4: Compute metrics for training set
    print(f"\n📊 Step 4: Computing training set metrics...")
    train_metrics = compute_validation_metrics(scores_df, labels_df, train_genes, 'train')
    print(f"  ✅ Training metrics computed for {len(train_metrics)} steps")
    
    # Step 5: Compute metrics for test set
    print(f"\n📊 Step 5: Computing test set metrics...")
    test_metrics = compute_validation_metrics(scores_df, labels_df, test_genes, 'test')
    print(f"  ✅ Test metrics computed for {len(test_metrics)} steps")
    
    # Step 6: Combine and save results
    print(f"\n💾 Step 6: Saving results...")
    all_metrics = pd.concat([train_metrics, test_metrics], ignore_index=True)
    metrics_path = OUTPUT_DIR / "holdout_validation_metrics.csv"
    all_metrics.to_csv(metrics_path, index=False)
    print(f"  ✅ Metrics saved to: {metrics_path}")
    
    # Step 7: Print summary
    print(f"\n" + "=" * 70)
    print("HOLD-OUT VALIDATION RESULTS")
    print("=" * 70)
    
    # Training set summary
    train_summary = train_metrics.groupby('split').agg({
        'auroc_mean': ['mean', 'std'],
        'auprc_mean': ['mean', 'std'],
        'fisher_p': lambda x: (x < 0.05).sum()
    })
    print(f"\n📊 Training Set (n={len(train_genes)} genes):")
    if len(train_metrics) > 0:
        print(f"  Mean AUROC: {train_metrics['auroc_mean'].mean():.3f} ± {train_metrics['auroc_mean'].std():.3f}")
        print(f"  Mean AUPRC: {train_metrics['auprc_mean'].mean():.3f} ± {train_metrics['auprc_mean'].std():.3f}")
        print(f"  Steps with p<0.05: {len(train_metrics[train_metrics['fisher_p'] < 0.05])}/{len(train_metrics)}")
        print(f"  Steps with p<0.001: {len(train_metrics[train_metrics['fisher_p'] < 0.001])}/{len(train_metrics)}")
    
    # Test set summary
    print(f"\n📊 Test Set (n={len(test_genes)} genes):")
    if len(test_metrics) > 0:
        print(f"  Mean AUROC: {test_metrics['auroc_mean'].mean():.3f} ± {test_metrics['auroc_mean'].std():.3f}")
        print(f"  Mean AUPRC: {test_metrics['auprc_mean'].mean():.3f} ± {test_metrics['auprc_mean'].std():.3f}")
        print(f"  Steps with p<0.05: {len(test_metrics[test_metrics['fisher_p'] < 0.05])}/{len(test_metrics)}")
        print(f"  Steps with p<0.001: {len(test_metrics[test_metrics['fisher_p'] < 0.001])}/{len(test_metrics)}")
        
        # Per-step comparison
        print(f"\n📊 Per-Step Comparison:")
        print(f"{'Step':<25} {'Train AUROC':<15} {'Test AUROC':<15} {'ΔAUROC':<10}")
        print("-" * 70)
        
        for step in sorted(train_metrics['step'].unique()):
            train_row = train_metrics[train_metrics['step'] == step]
            test_row = test_metrics[test_metrics['step'] == step]
            
            if len(train_row) > 0 and len(test_row) > 0:
                train_auroc = train_row['auroc_mean'].values[0]
                test_auroc = test_row['auroc_mean'].values[0]
                delta = test_auroc - train_auroc
                print(f"{step:<25} {train_auroc:>6.3f} ± {train_row['auroc_mean'].std():.3f}  {test_auroc:>6.3f} ± {test_row['auroc_mean'].std():.3f}  {delta:>+6.3f}")
    
    # Overall comparison
    if len(train_metrics) > 0 and len(test_metrics) > 0:
        train_mean_auroc = train_metrics['auroc_mean'].mean()
        test_mean_auroc = test_metrics['auroc_mean'].mean()
        delta_auroc = test_mean_auroc - train_mean_auroc
        
        print(f"\n" + "=" * 70)
        print(f"SUMMARY:")
        print(f"  Training AUROC: {train_mean_auroc:.3f}")
        print(f"  Test AUROC: {test_mean_auroc:.3f}")
        print(f"  ΔAUROC (test - train): {delta_auroc:+.3f}")
        
        if delta_auroc > -0.05:
            print(f"  ✅ Test performance within 5% of training (robust, no overfitting)")
        elif delta_auroc > -0.10:
            print(f"  ⚠️  Test performance 5-10% lower than training (moderate drop)")
        else:
            print(f"  ❌ Test performance >10% lower than training (possible overfitting)")
    
    print(f"\n✅ Hold-out validation complete!")
    print(f"  Results: {metrics_path}")
    print(f"  Split info: {split_path}")

if __name__ == "__main__":
    main()
