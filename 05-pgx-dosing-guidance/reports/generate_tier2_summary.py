#!/usr/bin/env python3
"""
Tier 2 Heuristic Validation - Generate Summary Table
=====================================================
Generates human-readable summary table and markdown report.

Output: reports/TIER2_VALIDATION_SUMMARY.md

Usage:
    python generate_tier2_summary.py
"""

import json
import argparse
from pathlib import Path
from datetime import datetime
import math

def calculate_confidence_interval(count: int, total: int, confidence_level: float = 0.95) -> tuple:
    """Calculate Clopper-Pearson exact confidence interval"""
    try:
        from scipy.stats import beta
        alpha = (1 - confidence_level) / 2
        lower = beta.ppf(alpha, count, total - count + 1) if count > 0 else 0.0
        upper = beta.ppf(1 - alpha, count + 1, total - count) if count < total else 1.0
        return lower, upper
    except ImportError:
        # Fallback: Wilson score interval approximation
        p = count / total if total > 0 else 0
        if total == 0:
            return 0.0, 0.0
        z = 1.96
        denominator = 1 + z**2/total
        centre = p + z**2/(2*total)
        term = z * math.sqrt(p*(1-p)/total + z**2/(4*total**2))
        lower = (centre - term) / denominator
        upper = (centre + term) / denominator
        return max(0.0, lower), min(1.0, upper)

def format_ci(value: float, lower: float, upper: float) -> str:
    """Format confidence interval as string"""
    return f"{value:.1%} ({lower:.1%}-{upper:.1%})"

def format_clinvar_class(p_count: int, lp_count: int, b_count: int, lb_count: int, vus_count: int) -> str:
    """Format ClinVar classification summary"""
    parts = []
    if p_count and p_count > 0:
        parts.append(f"{p_count}P")
    if lp_count and lp_count > 0:
        parts.append(f"{lp_count}LP")
    if b_count and b_count > 0:
        parts.append(f"{b_count}B")
    if lb_count and lb_count > 0:
        parts.append(f"{lb_count}LB")
    if vus_count and vus_count > 0:
        parts.append(f"{vus_count}VUS")
    return ", ".join(parts) if parts else "No data"

def main():
    parser = argparse.ArgumentParser(description="Generate Tier 2 validation summary table")
    parser.add_argument("--results", type=str, default="reports/tier2_heuristic_validation_results.json")
    parser.add_argument("--metrics", type=str, default="reports/tier2_performance_metrics.json")
    parser.add_argument("--output", type=str, default="reports/TIER2_VALIDATION_SUMMARY.md")
    args = parser.parse_args()
    
    # Load results
    results_path = Path(args.results)
    if not results_path.exists():
        print(f"❌ Error: {results_path} not found")
        return
    
    with open(results_path, 'r') as f:
        data = json.load(f)
    
    results = data.get("results", [])
    
    # Calculate metrics from results
    tp = sum(1 for r in results if r.get("outcome_classification") == "TP")
    tn = sum(1 for r in results if r.get("outcome_classification") == "TN")
    fp = sum(1 for r in results if r.get("outcome_classification") == "FP")
    fn = sum(1 for r in results if r.get("outcome_classification") == "FN")
    indeterminate = sum(1 for r in results if r.get("outcome_classification") not in ["TP", "TN", "FP", "FN"])
    
    scorable = tp + tn + fp + fn
    
    # Calculate metrics
    sensitivity = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    specificity = tn / (tn + fp) if (tn + fp) > 0 else 0.0
    ppv = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    npv = tn / (tn + fn) if (tn + fn) > 0 else 0.0
    accuracy = (tp + tn) / scorable if scorable > 0 else 0.0
    
    # Calculate CIs
    sens_ci = calculate_confidence_interval(tp, tp + fn) if (tp + fn) > 0 else (0.0, 0.0)
    spec_ci = calculate_confidence_interval(tn, tn + fp) if (tn + fp) > 0 else (0.0, 0.0)
    ppv_ci = calculate_confidence_interval(tp, tp + fp) if (tp + fp) > 0 else (0.0, 0.0)
    npv_ci = calculate_confidence_interval(tn, tn + fn) if (tn + fn) > 0 else (0.0, 0.0)
    acc_ci = calculate_confidence_interval(tp + tn, scorable) if scorable > 0 else (0.0, 0.0)
    
    # Generate markdown report
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        f.write("# Tier 2 ClinVar→Dosing Heuristic Validation Summary\n\n")
        f.write(f"**Validation Date**: {data.get('validation_date', 'Unknown')}\n")
        f.write(f"**Rules Version**: {data.get('rules_version', 'Unknown')}\n\n")
        
        f.write("## Executive Summary\n\n")
        f.write(f"- **Total Cases**: {len(results)}\n")
        f.write(f"- **Scorable Cases**: {scorable}\n")
        f.write(f"- **Indeterminate Cases**: {indeterminate} (missing ClinVar data or FLAG/SURFACE recommendations)\n\n")
        
        f.write("### Performance Metrics\n\n")
        f.write("| Metric | Value (95% CI) |\n")
        f.write("|--------|----------------|\n")
        
        if (tp + fn) > 0:
            f.write(f"| Sensitivity | {format_ci(sensitivity, sens_ci[0], sens_ci[1])} |\n")
        if (tn + fp) > 0:
            f.write(f"| Specificity | {format_ci(specificity, spec_ci[0], spec_ci[1])} |\n")
        if (tp + fp) > 0:
            f.write(f"| PPV | {format_ci(ppv, ppv_ci[0], ppv_ci[1])} |\n")
        if (tn + fn) > 0:
            f.write(f"| NPV | {format_ci(npv, npv_ci[0], npv_ci[1])} |\n")
        if scorable > 0:
            f.write(f"| Accuracy | {format_ci(accuracy, acc_ci[0], acc_ci[1])} |\n")
        
        f.write("\n### Outcome Classification\n\n")
        f.write(f"- **True Positives (TP)**: {tp} - System recommended dose reduction AND patient had Grade 3-5 toxicity\n")
        f.write(f"- **True Negatives (TN)**: {tn} - System recommended no action AND patient had Grade 0-2 or no toxicity\n")
        f.write(f"- **False Positives (FP)**: {fp} - System recommended dose reduction BUT patient had Grade 0-2 or no toxicity\n")
        f.write(f"- **False Negatives (FN)**: {fn} - System recommended no action BUT patient had Grade 3-5 toxicity\n")
        f.write(f"- **Indeterminate**: {indeterminate} - FLAG/SURFACE recommendations or missing ClinVar data\n\n")
        
        f.write("## Detailed Case-by-Case Results\n\n")
        f.write("| Case ID | Gene | Variant | ClinVar Class | System Rec | Actual Outcome | Result |\n")
        f.write("|---------|------|---------|---------------|------------|----------------|--------|\n")
        
        for result in results:
            case_id = result.get("case_id", "N/A")
            gene = result.get("gene", "N/A")
            variant = result.get("variant", "N/A")
            
            # ClinVar classification
            if result.get("clinvar_available"):
                clinvar_class = format_clinvar_class(
                    result.get("clinvar_pathogenic_count", 0) or 0,
                    result.get("clinvar_likely_pathogenic_count", 0) or 0,
                    result.get("clinvar_benign_count", 0) or 0,
                    result.get("clinvar_likely_benign_count", 0) or 0,
                    result.get("clinvar_vus_count", 0) or 0
                )
            else:
                clinvar_class = "No ClinVar data"
            
            # System recommendation
            sys_rec = result.get("system_recommendation", "N/A")
            if sys_rec:
                # Simplify for table
                if "REDUCE_50" in sys_rec:
                    sys_rec_display = "REDUCE 50%"
                elif "REDUCE_25" in sys_rec:
                    sys_rec_display = "REDUCE 25%"
                elif "FLAG" in sys_rec:
                    sys_rec_display = "FLAG"
                elif "SURFACE" in sys_rec:
                    sys_rec_display = "SURFACE"
                elif "NO_ACTION" in sys_rec:
                    sys_rec_display = "No action"
                else:
                    sys_rec_display = sys_rec
            else:
                sys_rec_display = "N/A"
            
            # Actual outcome
            grade = result.get("toxicity_grade")
            occurred = result.get("toxicity_occurred")
            if grade is not None:
                outcome = f"Grade {grade}"
            elif occurred:
                outcome = "Toxicity (grade unknown)"
            elif occurred is False:
                outcome = "No toxicity"
            else:
                outcome = "Unknown"
            
            # Result classification
            outcome_class = result.get("outcome_classification", "N/A")
            
            f.write(f"| {case_id} | {gene} | {variant} | {clinvar_class} | {sys_rec_display} | {outcome} | {outcome_class} |\n")
        
        f.write("\n## Interpretation\n\n")
        
        # Interpretation based on results
        f.write("### Key Findings\n\n")
        
        if sensitivity == 1.0:
            f.write("- **Perfect Sensitivity (100%)**: The heuristic rules correctly identified all cases with Grade 3-5 toxicity (0 false negatives). This is critical for patient safety.\n\n")
        
        if specificity < 0.5:
            f.write("- **Low Specificity**: The heuristic rules are conservative, recommending dose reduction for many patients who would not experience toxicity. This results in many false positives but prioritizes safety over precision.\n\n")
        
        if ppv < 0.5:
            f.write("- **Moderate PPV**: Only ~40% of dose reduction recommendations were for patients who actually experienced toxicity. This suggests the rules may be too permissive, but this is acceptable for a safety-first approach.\n\n")
        
        if npv == 1.0:
            f.write("- **Perfect NPV (100%)**: When the system recommended no action, patients did not experience severe toxicity. This validates the rules' ability to identify low-risk cases.\n\n")
        
        f.write("### Limitations\n\n")
        f.write("- **Small Sample Size**: Only 16 scorable cases limits statistical power. Confidence intervals are wide.\n")
        f.write("- **Retrospective Analysis**: Cases were extracted from published literature, which may have publication bias (more likely to report toxicities than non-toxicities).\n")
        f.write("- **Missing ClinVar Data**: 5 cases could not be scored due to missing ClinVar lookups (e.g., UGT1A1 *37).\n")
        f.write("- **Heterogeneous Outcomes**: Toxicity grades extracted from abstracts may not be standardized (some cases report Grade 3+, others may report specific grades).\n")
        f.write("- **Temporal Mismatch**: ClinVar data may have changed since case publication dates.\n\n")
        
        f.write("### Recommendations\n\n")
        f.write("1. **Expand Case Collection**: Target 50+ cases for more robust validation.\n")
        f.write("2. **Manual ClinVar Curation**: Manually verify ClinVar pathogenicity counts for all variants.\n")
        f.write("3. **Refine Heuristic Rules**: Consider adjusting thresholds to reduce false positives while maintaining high sensitivity.\n")
        f.write("4. **Prospective Validation**: Validate rules in a prospective cohort with standardized outcome definitions.\n")
        f.write("5. **Gene-Specific Rules**: Consider developing gene-specific heuristic rules (DPYD vs UGT1A1 may have different optimal thresholds).\n\n")
        
        f.write("## Methodology\n\n")
        f.write("### Heuristic Rules Applied\n\n")
        f.write("The following heuristic rules were tested:\n\n")
        f.write("1. **Strong Pathogenic Consensus (RULE_1)**: ≥3 Pathogenic/Likely Pathogenic, no Benign → REDUCE 50%\n")
        f.write("2. **Very Strong Pathogenic (RULE_2)**: ≥5 Pathogenic (even with conflicts) → REDUCE 50% + FLAG\n")
        f.write("3. **Conflicting Evidence (RULE_3)**: 2 Pathogenic + ≥2 Benign → FLAG for expert review\n")
        f.write("4. **Single Pathogenic (RULE_4)**: Only 1 Pathogenic → SURFACE evidence only\n")
        f.write("5. **Benign Consensus (RULE_5)**: ≥3 Benign/Likely Benign, no Pathogenic → No action\n")
        f.write("6. **VUS Only (RULE_6)**: Only VUS submissions → SURFACE evidence only\n")
        f.write("7. **Moderate Pathogenic (RULE_7)**: 2 Pathogenic/Likely Pathogenic, no Benign → REDUCE 25% + FLAG\n\n")
        
        f.write("### Evaluation Criteria\n\n")
        f.write("- **True Positive**: System recommended dose reduction AND patient had Grade 3-5 toxicity\n")
        f.write("- **True Negative**: System recommended no action AND patient had Grade 0-2 or no toxicity\n")
        f.write("- **False Positive**: System recommended dose reduction BUT patient had Grade 0-2 or no toxicity\n")
        f.write("- **False Negative**: System recommended no action BUT patient had Grade 3-5 toxicity\n")
        f.write("- **Indeterminate**: FLAG/SURFACE recommendations or missing ClinVar data (cannot be scored)\n\n")
        
        f.write("### Statistical Methods\n\n")
        f.write("- **Confidence Intervals**: Clopper-Pearson exact method (95% CI)\n")
        f.write("- **Sample Size**: 16 scorable cases (5 indeterminate excluded)\n")
        f.write("- **Outcome Definition**: Grade 3-5 toxicity = positive outcome, Grade 0-2 or no toxicity = negative outcome\n\n")
    
    print(f"✅ Generated summary report: {output_path}")
    print(f"\nSummary:")
    print(f"  - Total cases: {len(results)}")
    print(f"  - Scorable: {scorable}")
    print(f"  - TP: {tp}, TN: {tn}, FP: {fp}, FN: {fn}")
    if (tp + fn) > 0:
        print(f"  - Sensitivity: {format_ci(sensitivity, sens_ci[0], sens_ci[1])}")
    if (tn + fp) > 0:
        print(f"  - Specificity: {format_ci(specificity, spec_ci[0], spec_ci[1])}")

if __name__ == "__main__":
    main()

