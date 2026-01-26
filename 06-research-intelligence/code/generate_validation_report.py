#!/usr/bin/env python3
"""
Generate Comprehensive Validation Report

Consolidate results from Sprints 5, 6, 7, 8 into a single validation report.
Includes: metrics summary, baseline comparisons, key findings.
"""

import json
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime

def generate_validation_report():
    """Generate comprehensive validation report."""
    print("=" * 80)
    print("GENERATING VALIDATION REPORT")
    print("=" * 80)
    
    base_dir = Path(__file__).parent.parent
    
    # Load all results
    results = {}
    
    # Sprint 5: Ground Truth
    gt_file = base_dir / "sprint5_results" / "pubmed_ground_truth.json"
    if gt_file.exists():
        with open(gt_file, 'r') as f:
            results['ground_truth'] = json.load(f)
        print("✅ Loaded ground truth")
    
    # Sprint 6: Validation Results
    val_file = base_dir / "sprint6_results" / "validation_results.json"
    if val_file.exists():
        with open(val_file, 'r') as f:
            results['validation'] = json.load(f)
        print("✅ Loaded validation results")
    
    # Sprint 7: Metrics
    metrics_file = base_dir / "sprint7_results" / "metrics_summary.json"
    if metrics_file.exists():
        with open(metrics_file, 'r') as f:
            results['metrics'] = json.load(f)
        print("✅ Loaded metrics")
    
    # Sprint 8: Baselines
    baseline_file = base_dir / "sprint8_results" / "baseline_results.json"
    if baseline_file.exists():
        with open(baseline_file, 'r') as f:
            results['baselines'] = json.load(f)
        print("✅ Loaded baseline results")
    
    # Generate report
    report = {
        "timestamp": datetime.now().isoformat(),
        "summary": {
            "total_queries": results.get('validation', {}).get('total_queries', 0),
            "successful_queries": results.get('validation', {}).get('successful', 0),
            "average_precision": results.get('metrics', {}).get('average_precision', 0),
            "average_recall": results.get('metrics', {}).get('average_recall', 0),
            "average_f1": results.get('metrics', {}).get('average_f1', 0)
        },
        "detailed_results": results
    }
    
    # Save report
    output_file = base_dir / "VALIDATION_REPORT.json"
    with open(output_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    print("\n" + "=" * 80)
    print("✅ VALIDATION REPORT GENERATED")
    print("=" * 80)
    print(f"Output: {output_file}")
    print(f"\nSummary:")
    print(f"  Total queries: {report['summary']['total_queries']}")
    print(f"  Successful: {report['summary']['successful_queries']}")
    print(f"  Avg Precision: {report['summary']['average_precision']:.3f}")
    print(f"  Avg Recall: {report['summary']['average_recall']:.3f}")
    print(f"  Avg F1: {report['summary']['average_f1']:.3f}")
    
    return report


if __name__ == "__main__":
    generate_validation_report()


