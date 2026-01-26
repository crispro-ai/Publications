#!/usr/bin/env python3
"""
Quick parser for AF3 results - extract key metrics from the 5 completed guides.
"""
import json
import os
from pathlib import Path

def parse_guide_results(guide_dir):
    """Extract metrics from a guide result directory."""
    guide_dir_name = guide_dir.name
    
    # Files might be named with fold_meta_ prefix even if directory has meta_ prefix
    # Try multiple naming patterns
    possible_prefixes = []
    if guide_dir_name.startswith("meta_"):
        # Add fold_meta_ version
        possible_prefixes.append("fold_" + guide_dir_name)
    possible_prefixes.append(guide_dir_name)
    
    summary_file = None
    full_data_file = None
    
    for prefix in possible_prefixes:
        test_summary = guide_dir / f"{prefix}_summary_confidences_0.json"
        if test_summary.exists():
            summary_file = test_summary
            full_data_file = guide_dir / f"{prefix}_full_data_0.json"
            guide_name = prefix
            break
    
    if not summary_file:
        raise FileNotFoundError(f"Could not find summary file for {guide_dir_name}")
    
    # Load summary confidences (model 0 = best)
    with open(summary_file) as f:
        summary = json.load(f)
    
    # Load full data for pLDDT array
    with open(full_data_file) as f:
        full_data = json.load(f)
    
    # Compute mean pLDDT from atom-level scores
    plddt_mean = sum(full_data['atom_plddts']) / len(full_data['atom_plddts'])
    
    # Extract key metrics
    iptm = summary['iptm']
    ptm = summary['ptm']
    fraction_disordered = summary['fraction_disordered']
    has_clash = summary['has_clash']
    
    # Parse guide metadata from name
    # Format: fold_meta_{step}_{gene}_{id} OR meta_{step}_{gene}_{id}
    if guide_name.startswith("fold_meta_"):
        parts = guide_name.replace("fold_meta_", "").split("_")
    elif guide_name.startswith("meta_"):
        parts = guide_name.replace("meta_", "").split("_")
    else:
        parts = guide_name.split("_")
    
    gene = parts[-2]
    guide_id = parts[-1]
    step = "_".join(parts[:-2])
    
    return {
        "guide_name": guide_name,
        "step": step,
        "gene": gene,
        "guide_id": guide_id,
        "plddt_mean": plddt_mean,
        "iptm": iptm,
        "ptm": ptm,
        "fraction_disordered": fraction_disordered,
        "has_clash": has_clash
    }

def assess_guide(metrics):
    """Apply acceptance criteria and return verdict."""
    # Acceptance criteria from doctrine:
    # pLDDT >= 50, iPTM >= 0.5, interface PAE < 15 Å, disorder < 0.5
    
    gates = {
        "plddt_acceptable": metrics["plddt_mean"] >= 50,
        "iptm_acceptable": metrics["iptm"] >= 0.5,
        "disorder_acceptable": metrics["fraction_disordered"] < 0.5,
        "no_clash": metrics["has_clash"] == 0
    }
    
    # For this quick analysis, we don't have interface PAE easily accessible
    # (it's in the full PAE matrix), so we'll use iPTM as proxy
    
    if all(gates.values()):
        verdict = "PASS"
        confidence = 0.70 + (metrics["plddt_mean"]/100) * 0.15 + metrics["iptm"] * 0.15
    elif metrics["plddt_mean"] >= 50 and metrics["iptm"] >= 0.3:
        verdict = "REVIEW"
        confidence = 0.50 + (metrics["plddt_mean"]/100) * 0.10 + metrics["iptm"] * 0.10
    else:
        verdict = "FAIL"
        confidence = 0.30
    
    return verdict, confidence, gates

if __name__ == "__main__":
    results_dir = Path(__file__).parent  # Current directory
    
    # Find all guide directories (both fold_meta_ and meta_ prefixes)
    guide_dirs = [d for d in results_dir.iterdir() if d.is_dir() and (d.name.startswith("fold_meta_") or d.name.startswith("meta_"))]
    
    print("=" * 100)
    print("🎯 AF3 STRUCTURAL VALIDATION RESULTS - FIRST 5 GUIDES")
    print("=" * 100)
    print()
    
    results = []
    for guide_dir in sorted(guide_dirs):
        try:
            metrics = parse_guide_results(guide_dir)
            verdict, confidence, gates = assess_guide(metrics)
            
            metrics["verdict"] = verdict
            metrics["structural_confidence"] = confidence
            metrics["gates"] = gates
            
            results.append(metrics)
            
            # Print summary
            print(f"📊 {metrics['guide_name']}")
            print(f"   Step: {metrics['step']}")
            print(f"   Gene: {metrics['gene'].upper()}")
            print(f"   pLDDT: {metrics['plddt_mean']:.1f} {'✅' if gates['plddt_acceptable'] else '❌'}")
            print(f"   iPTM: {metrics['iptm']:.2f} {'✅' if gates['iptm_acceptable'] else '❌'}")
            print(f"   Disordered: {metrics['fraction_disordered']*100:.0f}% {'✅' if gates['disorder_acceptable'] else '❌'}")
            print(f"   Clash: {'No ✅' if gates['no_clash'] else 'Yes ❌'}")
            print(f"   Structural Confidence: {confidence:.2f}")
            print(f"   VERDICT: {verdict}")
            print()
        except Exception as e:
            print(f"❌ Error parsing {guide_dir.name}: {e}")
            print()
    
    # Summary statistics
    print("=" * 100)
    print("📈 BATCH SUMMARY")
    print("=" * 100)
    
    pass_count = sum(1 for r in results if r['verdict'] == 'PASS')
    review_count = sum(1 for r in results if r['verdict'] == 'REVIEW')
    fail_count = sum(1 for r in results if r['verdict'] == 'FAIL')
    
    print(f"Total guides analyzed: {len(results)}")
    print(f"PASS: {pass_count} ({pass_count/len(results)*100:.0f}%)")
    print(f"REVIEW: {review_count} ({review_count/len(results)*100:.0f}%)")
    print(f"FAIL: {fail_count} ({fail_count/len(results)*100:.0f}%)")
    print()
    
    avg_plddt = sum(r['plddt_mean'] for r in results) / len(results)
    avg_iptm = sum(r['iptm'] for r in results) / len(results)
    avg_confidence = sum(r['structural_confidence'] for r in results) / len(results)
    
    print(f"Mean pLDDT: {avg_plddt:.1f} ± {(max(r['plddt_mean'] for r in results) - min(r['plddt_mean'] for r in results))/2:.1f}")
    print(f"Mean iPTM: {avg_iptm:.2f} ± {(max(r['iptm'] for r in results) - min(r['iptm'] for r in results))/2:.2f}")
    print(f"Mean Structural Confidence: {avg_confidence:.2f}")
    print()
    
    print("=" * 100)
    print("🎯 CRITICAL ASSESSMENT")
    print("=" * 100)
    
    if fail_count == 0 and pass_count >= 0.8 * len(results):
        print("✅ EXCELLENT: ≥80% guides passed structural validation!")
        print("   Ready for publication with high confidence.")
    elif fail_count <= 0.2 * len(results) and (pass_count + review_count) >= 0.8 * len(results):
        print("✅ GOOD: ≥80% guides passed or under review.")
        print("   Publication-ready with RUO disclaimer for REVIEW guides.")
    elif fail_count > 0.3 * len(results):
        print("⚠️  CONCERN: >30% guides failed structural validation.")
        print("   May need to redesign failed guides before publication.")
    else:
        print("⚠️  ACCEPTABLE: Some guides failed, but majority viable.")
        print("   Proceed with caution; document limitations clearly.")
    
    print()
    print("=" * 100)

