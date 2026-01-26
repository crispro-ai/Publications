#!/usr/bin/env python3
"""
Tier 2 Heuristic Validation - Apply Rules & Score
==================================================
Applies heuristic rules to each case based on ClinVar evidence
and scores against actual toxicity outcomes.

Output: reports/tier2_heuristic_validation_results.json

Usage:
    python apply_tier2_heuristic_rules.py
"""

import json
import argparse
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from pathlib import Path
from scipy.stats import fisher_exact
from scipy.stats import beta

def load_heuristic_rules(rules_path: str) -> Dict:
    """Load heuristic rules from JSON"""
    with open(rules_path, 'r') as f:
        return json.load(f)

def load_cases(cases_path: str) -> List[Dict]:
    """Load extracted cases"""
    with open(cases_path, 'r') as f:
        data = json.load(f)
        return data.get("cases", [])

def load_clinvar_lookups(clinvar_path: str) -> Dict[str, Dict]:
    """Load ClinVar lookups and create variant lookup dict"""
    with open(clinvar_path, 'r') as f:
        data = json.load(f)
        lookups = data.get("lookups", [])
        # Create lookup dict: "gene:variant" -> ClinVar data
        lookup_dict = {}
        for lookup in lookups:
            gene = lookup.get("gene")
            variant = lookup.get("variant")
            if gene and variant:
                key = f"{gene}:{variant}"
                lookup_dict[key] = lookup
        return lookup_dict

def apply_heuristic_rule(clinvar_data: Dict, rules: List[Dict]) -> Optional[Dict]:
    """
    Apply heuristic rules to determine dosing recommendation.
    Returns the first matching rule.
    """
    if not clinvar_data.get("variation_id"):
        return None  # No ClinVar data available
    
    p_count = clinvar_data.get("pathogenic_count", 0) or 0
    lp_count = clinvar_data.get("likely_pathogenic_count", 0) or 0
    b_count = clinvar_data.get("benign_count", 0) or 0
    lb_count = clinvar_data.get("likely_benign_count", 0) or 0
    vus_count = clinvar_data.get("vus_count", 0) or 0
    
    total_p_lp = p_count + lp_count
    total_b_lb = b_count + lb_count
    
    # Check each rule in order
    for rule in rules:
        condition = rule.get("condition", {})
        matches = True
        
        # Check each condition
        for key, value in condition.items():
            if key == "pathogenic_count":
                if not eval(f"{p_count} {value}"):
                    matches = False
                    break
            elif key == "likely_pathogenic_count":
                if not eval(f"{lp_count} {value}"):
                    matches = False
                    break
            elif key == "benign_count":
                if not eval(f"{b_count} {value}"):
                    matches = False
                    break
            elif key == "likely_benign_count":
                if not eval(f"{lb_count} {value}"):
                    matches = False
                    break
            elif key == "vus_count":
                if not eval(f"{vus_count} {value}"):
                    matches = False
                    break
            elif key == "total_pathogenic_likely_pathogenic":
                if not eval(f"{total_p_lp} {value}"):
                    matches = False
                    break
            elif key == "total_benign_likely_benign":
                if not eval(f"{total_b_lb} {value}"):
                    matches = False
                    break
        
        if matches:
            return {
                "rule_id": rule.get("rule_id"),
                "rule_name": rule.get("name"),
                "recommendation": rule.get("recommendation"),
                "adjustment_factor": rule.get("adjustment_factor"),
                "confidence": rule.get("confidence"),
                "flag_for_review": rule.get("flag_for_review", False),
                "flag_reason": rule.get("flag_reason"),
                "rationale": rule.get("rationale")
            }
    
    # No rule matched - default to SURFACE_EVIDENCE_ONLY
    return {
        "rule_id": "DEFAULT",
        "rule_name": "No Rule Matched",
        "recommendation": "SURFACE_EVIDENCE_ONLY",
        "adjustment_factor": None,
        "confidence": "VERY_LOW",
        "flag_for_review": False,
        "rationale": "ClinVar data available but no heuristic rule matched"
    }

def classify_outcome(system_rec: str, actual_grade: Optional[int], 
                    toxicity_occurred: Optional[bool]) -> str:
    """
    Classify case as TP/TN/FP/FN/INDETERMINATE based on evaluation criteria.
    """
    # Indeterminate cases (FLAG or SURFACE only)
    if system_rec in ["FLAG_FOR_EXPERT_REVIEW", "SURFACE_EVIDENCE_ONLY"]:
        return "INDETERMINATE"
    
    # Determine if actual outcome is positive (Grade 3-5) or negative (Grade 0-2 or no toxicity)
    if actual_grade is not None:
        is_positive = actual_grade >= 3
    elif toxicity_occurred is not None:
        is_positive = toxicity_occurred
    else:
        return "INDETERMINATE"  # No outcome data
    
    # Determine if system recommendation is positive (dose reduction) or negative (no action)
    is_system_positive = system_rec in ["REDUCE_50", "REDUCE_50_FLAG", "REDUCE_25_FLAG"]
    is_system_negative = system_rec in ["NO_ACTION"]
    
    if not (is_system_positive or is_system_negative):
        return "INDETERMINATE"  # Unclear recommendation
    
    # Classify
    if is_system_positive and is_positive:
        return "TP"  # True Positive
    elif is_system_negative and not is_positive:
        return "TN"  # True Negative
    elif is_system_positive and not is_positive:
        return "FP"  # False Positive
    elif is_system_negative and is_positive:
        return "FN"  # False Negative
    else:
        return "INDETERMINATE"

def calculate_confidence_interval(numerator: int, denominator: int, confidence: float = 0.95) -> Tuple[float, float]:
    """
    Calculate Clopper-Pearson exact confidence interval for a proportion.
    """
    if denominator == 0:
        return (0.0, 1.0)
    
    alpha = 1 - confidence
    lower = beta.ppf(alpha / 2, numerator, denominator - numerator + 1) if numerator > 0 else 0.0
    upper = beta.ppf(1 - alpha / 2, numerator + 1, denominator - numerator) if numerator < denominator else 1.0
    
    return (lower, upper)

def calculate_metrics(results: List[Dict]) -> Dict:
    """Calculate performance metrics from validation results"""
    # Count outcomes
    tp = sum(1 for r in results if r.get("outcome_classification") == "TP")
    tn = sum(1 for r in results if r.get("outcome_classification") == "TN")
    fp = sum(1 for r in results if r.get("outcome_classification") == "FP")
    fn = sum(1 for r in results if r.get("outcome_classification") == "FN")
    indeterminate = sum(1 for r in results if r.get("outcome_classification") == "INDETERMINATE")
    
    total_scorable = tp + tn + fp + fn
    
    # Calculate metrics with 95% CI (Clopper-Pearson)
    metrics = {
        "total_cases": len(results),
        "scorable_cases": total_scorable,
        "indeterminate_cases": indeterminate,
        "tp": tp,
        "tn": tn,
        "fp": fp,
        "fn": fn
    }
    
    # Sensitivity: TP / (TP + FN)
    if tp + fn > 0:
        sensitivity = tp / (tp + fn)
        sens_ci = calculate_confidence_interval(tp, tp + fn)
        metrics["sensitivity"] = {
            "value": sensitivity,
            "95_ci_lower": sens_ci[0],
            "95_ci_upper": sens_ci[1],
            "formula": f"{tp} / ({tp} + {fn})"
        }
    else:
        metrics["sensitivity"] = {"value": None, "note": "No positive cases"}
    
    # Specificity: TN / (TN + FP)
    if tn + fp > 0:
        specificity = tn / (tn + fp)
        spec_ci = calculate_confidence_interval(tn, tn + fp)
        metrics["specificity"] = {
            "value": specificity,
            "95_ci_lower": spec_ci[0],
            "95_ci_upper": spec_ci[1],
            "formula": f"{tn} / ({tn} + {fp})"
        }
    else:
        metrics["specificity"] = {"value": None, "note": "No negative cases"}
    
    # PPV: TP / (TP + FP)
    if tp + fp > 0:
        ppv = tp / (tp + fp)
        ppv_ci = calculate_confidence_interval(tp, tp + fp)
        metrics["ppv"] = {
            "value": ppv,
            "95_ci_lower": ppv_ci[0],
            "95_ci_upper": ppv_ci[1],
            "formula": f"{tp} / ({tp} + {fp})"
        }
    else:
        metrics["ppv"] = {"value": None, "note": "No positive predictions"}
    
    # NPV: TN / (TN + FN)
    if tn + fn > 0:
        npv = tn / (tn + fn)
        npv_ci = calculate_confidence_interval(tn, tn + fn)
        metrics["npv"] = {
            "value": npv,
            "95_ci_lower": npv_ci[0],
            "95_ci_upper": npv_ci[1],
            "formula": f"{tn} / ({tn} + {fn})"
        }
    else:
        metrics["npv"] = {"value": None, "note": "No negative predictions"}
    
    # Accuracy: (TP + TN) / Total
    if total_scorable > 0:
        accuracy = (tp + tn) / total_scorable
        acc_ci = calculate_confidence_interval(tp + tn, total_scorable)
        metrics["accuracy"] = {
            "value": accuracy,
            "95_ci_lower": acc_ci[0],
            "95_ci_upper": acc_ci[1],
            "formula": f"({tp} + {tn}) / {total_scorable}"
        }
    else:
        metrics["accuracy"] = {"value": None, "note": "No scorable cases"}
    
    return metrics

def main():
    parser = argparse.ArgumentParser(description="Apply Tier 2 heuristic rules and score cases")
    parser.add_argument("--rules", type=str, default="reports/tier2_heuristic_rules.json")
    parser.add_argument("--cases", type=str, default="reports/tier2_validation_cases.json")
    parser.add_argument("--clinvar", type=str, default="reports/tier2_clinvar_lookups.json")
    parser.add_argument("--output", type=str, default="reports/tier2_heuristic_validation_results.json")
    args = parser.parse_args()
    
    print("="*70)
    print("TIER 2 HEURISTIC RULE VALIDATION")
    print("="*70)
    print(f"Rules: {args.rules}")
    print(f"Cases: {args.cases}")
    print(f"ClinVar: {args.clinvar}")
    print(f"Output: {args.output}")
    print()
    
    # Load data
    print("Loading data...")
    rules_data = load_heuristic_rules(args.rules)
    cases = load_cases(args.cases)
    clinvar_lookups = load_clinvar_lookups(args.clinvar)
    
    print(f"  - Rules: {len(rules_data.get('rules', []))}")
    print(f"  - Cases: {len(cases)}")
    print(f"  - ClinVar lookups: {len(clinvar_lookups)}")
    print()
    
    # Apply rules and score
    print("Applying heuristic rules and scoring cases...")
    results = []
    
    for case in cases:
        case_id = case.get("case_id")
        gene = case.get("gene")
        variant = case.get("variant")
        pmid = case.get("pmid")
        toxicity_grade = case.get("toxicity_grade")
        toxicity_occurred = case.get("toxicity_occurred")
        
        # Look up ClinVar data
        variant_key = f"{gene}:{variant}"
        clinvar_data = clinvar_lookups.get(variant_key)
        
        if not clinvar_data:
            # No ClinVar data - mark as indeterminate
            result = {
                "case_id": case_id,
                "pmid": pmid,
                "gene": gene,
                "variant": variant,
                "clinvar_available": False,
                "system_recommendation": None,
                "rule_applied": None,
                "outcome_classification": "INDETERMINATE",
                "reason": "No ClinVar data available for this variant",
                "toxicity_grade": toxicity_grade,
                "toxicity_occurred": toxicity_occurred
            }
            results.append(result)
            continue
        
        # Apply heuristic rule
        rule_result = apply_heuristic_rule(clinvar_data, rules_data.get("rules", []))
        
        if not rule_result:
            # Rule application failed
            result = {
                "case_id": case_id,
                "pmid": pmid,
                "gene": gene,
                "variant": variant,
                "clinvar_available": True,
                "system_recommendation": None,
                "rule_applied": None,
                "outcome_classification": "INDETERMINATE",
                "reason": "Heuristic rule application failed",
                "toxicity_grade": toxicity_grade,
                "toxicity_occurred": toxicity_occurred
            }
            results.append(result)
            continue
        
        # Classify outcome
        outcome_class = classify_outcome(
            rule_result["recommendation"],
            toxicity_grade,
            toxicity_occurred
        )
        
        result = {
            "case_id": case_id,
            "pmid": pmid,
            "gene": gene,
            "variant": variant,
            "clinvar_available": True,
            "clinvar_variation_id": clinvar_data.get("variation_id"),
            "clinvar_pathogenic_count": clinvar_data.get("pathogenic_count", 0),
            "clinvar_likely_pathogenic_count": clinvar_data.get("likely_pathogenic_count", 0),
            "clinvar_benign_count": clinvar_data.get("benign_count", 0),
            "clinvar_likely_benign_count": clinvar_data.get("likely_benign_count", 0),
            "clinvar_vus_count": clinvar_data.get("vus_count", 0),
            "clinvar_conflicting": clinvar_data.get("conflicting_interpretations", "Unknown"),
            "system_recommendation": rule_result["recommendation"],
            "rule_applied": rule_result["rule_id"],
            "rule_name": rule_result["rule_name"],
            "adjustment_factor": rule_result["adjustment_factor"],
            "confidence": rule_result["confidence"],
            "flag_for_review": rule_result["flag_for_review"],
            "rationale": rule_result["rationale"],
            "outcome_classification": outcome_class,
            "toxicity_grade": toxicity_grade,
            "toxicity_occurred": toxicity_occurred,
            "drug": case.get("drug")
        }
        results.append(result)
    
    # Calculate metrics
    print("\nCalculating performance metrics...")
    metrics = calculate_metrics(results)
    
    # Save results
    output_data = {
        "validation_date": datetime.now().isoformat(),
        "rules_version": rules_data.get("version"),
        "total_cases": len(results),
        "results": results,
        "performance_metrics": metrics
    }
    
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(output_data, f, indent=2)
    
    print(f"\n✅ Saved validation results to {output_path}")
    print(f"\nPerformance Summary:")
    print(f"  - Total cases: {metrics['total_cases']}")
    print(f"  - Scorable cases: {metrics['scorable_cases']}")
    print(f"  - Indeterminate: {metrics['indeterminate_cases']}")
    print(f"  - TP: {metrics['tp']}, TN: {metrics['tn']}, FP: {metrics['fp']}, FN: {metrics['fn']}")
    
    if metrics.get("sensitivity", {}).get("value") is not None:
        sens = metrics["sensitivity"]
        print(f"  - Sensitivity: {sens['value']:.3f} (95% CI: {sens['95_ci_lower']:.3f}-{sens['95_ci_upper']:.3f})")
    
    if metrics.get("specificity", {}).get("value") is not None:
        spec = metrics["specificity"]
        print(f"  - Specificity: {spec['value']:.3f} (95% CI: {spec['95_ci_lower']:.3f}-{spec['95_ci_upper']:.3f})")
    
    if metrics.get("ppv", {}).get("value") is not None:
        ppv = metrics["ppv"]
        print(f"  - PPV: {ppv['value']:.3f} (95% CI: {ppv['95_ci_lower']:.3f}-{ppv['95_ci_upper']:.3f})")
    
    if metrics.get("npv", {}).get("value") is not None:
        npv = metrics["npv"]
        print(f"  - NPV: {npv['value']:.3f} (95% CI: {npv['95_ci_lower']:.3f}-{npv['95_ci_upper']:.3f})")
    
    if metrics.get("accuracy", {}).get("value") is not None:
        acc = metrics["accuracy"]
        print(f"  - Accuracy: {acc['value']:.3f} (95% CI: {acc['95_ci_lower']:.3f}-{acc['95_ci_upper']:.3f})")

if __name__ == "__main__":
    main()







