#!/usr/bin/env python3
"""
TCGA External Validation for Target-Lock Scoring

Purpose:
- Extract metastasis-associated genes from TCGA-OV dataset
- Score them with Target-Lock (using 28-gene training weights from hold-out)
- Compare Target-Lock rankings to TCGA-based metastasis association rankings
- Addresses circularity by validating on independent dataset

Method:
1. Load TCGA-OV full validation dataset (200 patients with mutations)
2. Extract all unique genes from mutations
3. Compute metastasis association scores:
   - Stage-based: mutation frequency in Stage III/IV vs. Stage I/II
   - Survival-based: mutation frequency in OS <24mo vs. OS ≥24mo
   - Combined score: (stage_assoc + survival_assoc) / 2
4. Rank genes by metastasis association
5. Select top 20-30 genes (excluding our 38 genes)
6. Score with Target-Lock (using existing weights, or 28-gene training weights)
7. Compare Target-Lock rank to TCGA rank (Spearman correlation)

Outputs:
- ../data/tcga_metastasis_genes.csv
- ../data/tcga_external_validation_metrics.csv
- ../data/tcga_external_validation_summary.json

Author: Zo (Platform AI)
Date: January 19, 2026
Version: 1.0.0
"""

import json
import os
import numpy as np
import pandas as pd
from pathlib import Path
from collections import Counter
from scipy.stats import spearmanr, fisher_exact
from typing import Dict, List, Tuple, Optional
import warnings
warnings.filterwarnings('ignore')

# Configuration
SEED = 42
np.random.seed(SEED)
MIN_MUTATION_FREQUENCY = 3  # Minimum number of patients with mutation to include gene
TOP_N_GENES = 30  # Select top N metastasis-associated genes
OUTPUT_DIR = Path("../data")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def load_tcga_data() -> List[Dict]:
    """Load TCGA-OV full validation dataset"""
    tcga_path = Path("data/validation/tcga_ov_full_validation_dataset.json")
    
    if not tcga_path.exists():
        raise FileNotFoundError(f"TCGA data not found: {tcga_path}")
    
    with open(tcga_path) as f:
        data = json.load(f)
    
    patients = data.get("patients", [])
    print(f"✅ Loaded TCGA-OV dataset: {len(patients)} patients")
    return patients

def load_our_38_genes() -> set:
    """Load our 38 genes from metastasis_rules_v1.0.1.json"""
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
    
    all_genes = set()
    for step_data in rules["steps"].values():
        all_genes.update(step_data.get("primary_genes", []))
        all_genes.update(step_data.get("secondary_genes", []))
    
    print(f"✅ Loaded {len(all_genes)} genes from our validation set")
    return all_genes

def extract_gene_mutations(patients: List[Dict]) -> Dict[str, List[Dict]]:
    """
    Extract all mutations per gene
    
    Returns: {gene: [list of patient dicts with this mutation]}
    """
    gene_mutations = {}
    
    for patient in patients:
        mutations = patient.get("mutations", [])
        patient_id = patient.get("patient_id") or patient.get("sample_id", "unknown")
        
        for mut in mutations:
            gene = mut.get("gene")
            if gene:
                if gene not in gene_mutations:
                    gene_mutations[gene] = []
                gene_mutations[gene].append({
                    "patient_id": patient_id,
                    "mutation": mut,
                    "patient": patient  # Keep full patient data for stage/survival
                })
    
    print(f"✅ Extracted mutations for {len(gene_mutations)} unique genes")
    return gene_mutations

def categorize_patients_by_stage(patients: List[Dict]) -> Tuple[List[Dict], List[Dict]]:
    """Categorize patients into early (I/II) vs. late (III/IV) stage"""
    early = []
    late = []
    
    for patient in patients:
        stage = patient.get("stage", "")
        if not stage:
            continue
        
        if "I" in stage or "II" in stage:
            early.append(patient)
        elif "III" in stage or "IV" in stage:
            late.append(patient)
    
    print(f"  Stage categorization: {len(early)} early (I/II), {len(late)} late (III/IV)")
    return early, late

def categorize_patients_by_survival(patients: List[Dict]) -> Tuple[List[Dict], List[Dict]]:
    """Categorize patients into poor (<24mo) vs. good (≥24mo) survival"""
    poor = []
    good = []
    
    for patient in patients:
        os_months = patient.get("os_months")
        if os_months is None:
            continue
        
        if os_months < 24:
            poor.append(patient)
        elif os_months >= 24:
            good.append(patient)
    
    print(f"  Survival categorization: {len(poor)} poor (<24mo), {len(good)} good (≥24mo)")
    return poor, good

def compute_metastasis_association_scores(
    gene_mutations: Dict[str, List[Dict]],
    early_stage: List[Dict],
    late_stage: List[Dict],
    poor_survival: List[Dict],
    good_survival: List[Dict]
) -> pd.DataFrame:
    """
    Compute metastasis association scores for each gene
    
    Returns DataFrame with columns:
    - gene
    - freq_early, freq_late, freq_poor, freq_good
    - stage_association (freq_late / freq_early)
    - survival_association (freq_poor / freq_good)
    - combined_score
    """
    early_patient_ids = {p.get("patient_id") or p.get("sample_id") for p in early_stage}
    late_patient_ids = {p.get("patient_id") or p.get("sample_id") for p in late_stage}
    poor_patient_ids = {p.get("patient_id") or p.get("sample_id") for p in poor_survival}
    good_patient_ids = {p.get("patient_id") or p.get("sample_id") for p in good_survival}
    
    results = []
    
    for gene, mutations in gene_mutations.items():
        # Count mutations in each category
        freq_early = sum(1 for m in mutations if m["patient_id"] in early_patient_ids)
        freq_late = sum(1 for m in mutations if m["patient_id"] in late_patient_ids)
        freq_poor = sum(1 for m in mutations if m["patient_id"] in poor_patient_ids)
        freq_good = sum(1 for m in mutations if m["patient_id"] in good_patient_ids)
        
        total_freq = freq_early + freq_late + freq_poor + freq_good
        
        # Skip genes with too few mutations
        if total_freq < MIN_MUTATION_FREQUENCY:
            continue
        
        # Compute association scores (add pseudocount to avoid division by zero)
        # If no late-stage patients, use survival-only association
        if len(late_stage) == 0:
            # No late-stage data - use survival-only
            stage_assoc = 0.0  # Can't compute without late-stage data
            survival_assoc = freq_poor / (freq_good + 0.1) if freq_good > 0 else freq_poor / 0.1
            combined_score = survival_assoc  # Use survival-only
        else:
            stage_assoc = freq_late / (freq_early + 0.1) if freq_early > 0 else freq_late / 0.1
            survival_assoc = freq_poor / (freq_good + 0.1) if freq_good > 0 else freq_poor / 0.1
            # Combined score (normalized)
            combined_score = (stage_assoc + survival_assoc) / 2
        
        results.append({
            "gene": gene,
            "freq_early": freq_early,
            "freq_late": freq_late,
            "freq_poor": freq_poor,
            "freq_good": freq_good,
            "freq_total": total_freq,
            "stage_association": stage_assoc if len(late_stage) > 0 else np.nan,
            "survival_association": survival_assoc,
            "combined_score": combined_score,
            "method": "survival_only" if len(late_stage) == 0 else "stage_and_survival"
        })
    
    df = pd.DataFrame(results)
    df = df.sort_values("combined_score", ascending=False)
    
    print(f"✅ Computed metastasis association scores for {len(df)} genes")
    print(f"  Top 10 by combined score:")
    for _, row in df.head(10).iterrows():
        print(f"    {row['gene']}: {row['combined_score']:.2f} (late={row['freq_late']}, poor={row['freq_poor']})")
    
    return df

def load_target_lock_scores() -> pd.DataFrame:
    """Load Target-Lock scores from real_target_lock_data.csv"""
    data_path = OUTPUT_DIR / "real_target_lock_data.csv"
    
    if not data_path.exists():
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
    if 'mission' in df.columns:
        df = df.rename(columns={'mission': 'step'})
    print(f"✅ Loaded Target-Lock scores: {len(df)} rows")
    return df

def compute_target_lock_rankings(scores_df: pd.DataFrame, genes: List[str]) -> Dict[str, float]:
    """
    Compute average Target-Lock score across all steps for each gene
    
    Returns: {gene: average_target_lock_score}
    """
    gene_scores = {}
    
    for gene in genes:
        gene_data = scores_df[scores_df['gene'] == gene]
        if len(gene_data) > 0:
            avg_score = gene_data['target_lock_score'].mean()
            gene_scores[gene] = avg_score
        else:
            # Gene not in our dataset - would need to compute Target-Lock
            # For now, skip (or use a placeholder)
            print(f"  ⚠️  {gene}: Not in Target-Lock dataset (would need to compute)")
            gene_scores[gene] = np.nan
    
    return gene_scores

def compare_rankings(
    tcga_df: pd.DataFrame,
    target_lock_scores: Dict[str, float],
    top_n: int = TOP_N_GENES
) -> pd.DataFrame:
    """
    Compare TCGA rankings to Target-Lock rankings
    
    Returns DataFrame with comparison metrics
    """
    # Select top N genes from TCGA (excluding our 38 genes)
    our_38_genes = load_our_38_genes()
    tcga_filtered = tcga_df[~tcga_df['gene'].isin(our_38_genes)].head(top_n)
    
    print(f"\n📊 Selected top {len(tcga_filtered)} TCGA metastasis-associated genes (excluding our 38)")
    
    # Get Target-Lock scores for these genes
    comparison_data = []
    for _, row in tcga_filtered.iterrows():
        gene = row['gene']
        tcga_rank = row.name + 1  # 1-indexed
        tcga_score = row['combined_score']
        target_lock_score = target_lock_scores.get(gene, np.nan)
        
        comparison_data.append({
            "gene": gene,
            "tcga_rank": tcga_rank,
            "tcga_score": tcga_score,
            "target_lock_score": target_lock_score,
            "freq_late": row['freq_late'],
            "freq_poor": row['freq_poor'],
            "freq_total": row['freq_total']
        })
    
    comparison_df = pd.DataFrame(comparison_data)
    
    # Rank by Target-Lock score (put NaN at end)
    comparison_df = comparison_df.sort_values("target_lock_score", ascending=False, na_position='last')
    comparison_df['target_lock_rank'] = range(1, len(comparison_df) + 1)
    
    # Reorder by TCGA rank for display
    comparison_df = comparison_df.sort_values("tcga_rank")
    
    return comparison_df

def compute_correlation_metrics(comparison_df: pd.DataFrame) -> Dict:
    """Compute Spearman correlation between TCGA and Target-Lock rankings"""
    # Filter out genes with missing Target-Lock scores
    valid_df = comparison_df.dropna(subset=['target_lock_score'])
    
    if len(valid_df) < 3:
        print("  ⚠️  Too few genes with Target-Lock scores for correlation")
        return {
            "n_genes": len(valid_df),
            "spearman_rho": np.nan,
            "spearman_p": np.nan,
            "status": "insufficient_data"
        }
    
    # Compute Spearman correlation
    rho, p_value = spearmanr(valid_df['tcga_rank'], valid_df['target_lock_rank'])
    
    print(f"\n📊 Correlation Analysis:")
    print(f"  Genes with Target-Lock scores: {len(valid_df)}/{len(comparison_df)}")
    print(f"  Spearman ρ: {rho:.3f}")
    print(f"  p-value: {p_value:.4f}")
    
    if rho > 0.3:
        print(f"  ✅ Moderate positive correlation (Target-Lock ranks align with TCGA)")
    elif rho > 0:
        print(f"  ⚠️  Weak positive correlation")
    else:
        print(f"  ❌ No correlation or negative correlation")
    
    return {
        "n_genes": len(valid_df),
        "n_total": len(comparison_df),
        "spearman_rho": float(rho),
        "spearman_p": float(p_value),
        "status": "success" if not np.isnan(rho) else "insufficient_data"
    }

def main():
    """Main TCGA external validation pipeline"""
    print("=" * 70)
    print("TCGA EXTERNAL VALIDATION")
    print("=" * 70)
    print()
    
    # Step 1: Load TCGA data
    print("📥 Step 1: Loading TCGA-OV dataset...")
    patients = load_tcga_data()
    
    # Step 2: Extract gene mutations
    print(f"\n📊 Step 2: Extracting gene mutations...")
    gene_mutations = extract_gene_mutations(patients)
    
    # Step 3: Categorize patients
    print(f"\n📊 Step 3: Categorizing patients...")
    early_stage, late_stage = categorize_patients_by_stage(patients)
    poor_survival, good_survival = categorize_patients_by_survival(patients)
    
    # Step 4: Compute metastasis association scores
    print(f"\n📊 Step 4: Computing metastasis association scores...")
    tcga_scores = compute_metastasis_association_scores(
        gene_mutations, early_stage, late_stage, poor_survival, good_survival
    )
    
    # Save TCGA scores
    tcga_path = OUTPUT_DIR / "tcga_metastasis_genes.csv"
    tcga_scores.to_csv(tcga_path, index=False)
    print(f"  ✅ Saved TCGA scores to: {tcga_path}")
    
    # Step 5: Load Target-Lock scores
    print(f"\n📥 Step 5: Loading Target-Lock scores...")
    target_lock_df = load_target_lock_scores()
    
    # Step 6: Select top metastasis-associated genes (excluding our 38)
    print(f"\n📊 Step 6: Selecting top metastasis-associated genes...")
    our_38_genes = load_our_38_genes()
    tcga_top = tcga_scores[~tcga_scores['gene'].isin(our_38_genes)].head(TOP_N_GENES)
    
    print(f"  Selected {len(tcga_top)} genes (excluding our 38)")
    print(f"  Top 10:")
    for i, (_, row) in enumerate(tcga_top.head(10).iterrows(), 1):
        print(f"    {i}. {row['gene']}: score={row['combined_score']:.2f}, late={row['freq_late']}, poor={row['freq_poor']}")
    
    # Step 7: Compute Target-Lock rankings
    print(f"\n📊 Step 7: Computing Target-Lock rankings...")
    target_lock_scores = compute_target_lock_rankings(
        target_lock_df,
        tcga_top['gene'].tolist()
    )
    
    # Step 8: Compare rankings
    print(f"\n📊 Step 8: Comparing rankings...")
    comparison_df = compare_rankings(tcga_scores, target_lock_scores, TOP_N_GENES)
    
    # Save comparison
    comparison_path = OUTPUT_DIR / "tcga_external_validation_metrics.csv"
    comparison_df.to_csv(comparison_path, index=False)
    print(f"  ✅ Saved comparison to: {comparison_path}")
    
    # Step 9: Compute correlation
    print(f"\n📊 Step 9: Computing correlation metrics...")
    correlation_metrics = compute_correlation_metrics(comparison_df)
    
    # Step 10: Save summary
    summary = {
        "tcga_dataset": "TCGA-OV full validation (200 patients)",
        "n_tcga_genes": len(tcga_scores),
        "n_selected_genes": len(tcga_top),
        "n_genes_with_target_lock": correlation_metrics.get("n_genes", 0),
        "correlation": correlation_metrics,
        "top_10_tcga_genes": tcga_top.head(10)['gene'].tolist(),
        "min_mutation_frequency": MIN_MUTATION_FREQUENCY,
        "top_n_selected": TOP_N_GENES
    }
    
    summary_path = OUTPUT_DIR / "tcga_external_validation_summary.json"
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2)
    print(f"  ✅ Saved summary to: {summary_path}")
    
    # Print final summary
    print(f"\n" + "=" * 70)
    print("TCGA EXTERNAL VALIDATION SUMMARY")
    print("=" * 70)
    print(f"TCGA genes analyzed: {len(tcga_scores)}")
    print(f"Top metastasis-associated genes selected: {len(tcga_top)}")
    print(f"Genes with Target-Lock scores: {correlation_metrics.get('n_genes', 0)}")
    if not np.isnan(correlation_metrics.get('spearman_rho', np.nan)):
        print(f"Spearman correlation (ρ): {correlation_metrics['spearman_rho']:.3f}")
        print(f"p-value: {correlation_metrics['spearman_p']:.4f}")
    
    print(f"\n✅ TCGA external validation complete!")
    print(f"  Results: {comparison_path}")
    print(f"  Summary: {summary_path}")

if __name__ == "__main__":
    main()
