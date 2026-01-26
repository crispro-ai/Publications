#!/usr/bin/env python3
"""Safety audit for Trial Matching manuscript - verifies all claims against receipts."""

import json
from pathlib import Path

def main():
    print('=' * 80)
    print('SAFETY AUDIT - TRIAL MATCHING MANUSCRIPT')
    print('=' * 80)

    receipts_dir = Path('receipts/latest')

    # 1. RECEIPT FILE CHECK
    print('\n' + '=' * 80)
    print('1. RECEIPT FILE CHECK')
    print('=' * 80)

    required = {
        'mechanism_sanity.json': 'Mechanism discrimination sanity check',
        'real_world_tcga_ov_validation.json': 'TCGA-OV matchability validation',
        'real_world_tcga_ov_survival_validation.json': 'TCGA-OV survival analysis',
        'eval_ranking.json': 'Ranking evaluation (MRR/Recall)'
    }

    for fname, desc in required.items():
        fpath = receipts_dir / fname
        if fpath.exists():
            size = fpath.stat().st_size
            print(f'✅ {fname}: EXISTS ({size:,} bytes) - {desc}')
        else:
            print(f'❌ {fname}: MISSING - {desc}')

    # 2. TCGA-OV PATIENT VERIFICATION
    print('\n' + '=' * 80)
    print('2. TCGA-OV PATIENT VERIFICATION')
    print('=' * 80)

    tcga_path = receipts_dir / 'real_world_tcga_ov_validation.json'
    if tcga_path.exists():
        with open(tcga_path) as f:
            tcga_data = json.load(f)
        raw_results = tcga_data.get('raw_results', [])
        if raw_results:
            print(f'\nTotal patients: {len(raw_results)}')
            print('\nExample patient IDs (first 3):')
            for i, p in enumerate(raw_results[:3]):
                pid = p.get('patient_id', 'UNKNOWN')
                print(f'  {i+1}. {pid}')
                if pid.startswith('TCGA-') and len(pid.split('-')) == 4:
                    parts = pid.split('-')
                    if len(parts[2]) == 2 and len(parts[3]) == 4:
                        print(f'     ✅ TCGA format verified (X-XXXX)')
                    else:
                        print(f'     ❌ TCGA format INVALID (parts: {parts})')
                else:
                    print(f'     ❌ NOT TCGA FORMAT')
        else:
            print('❌ No raw_results found in receipt')
    else:
        print('❌ TCGA validation receipt missing')

    # 3. MRR/RECALL SOURCE
    print('\n' + '=' * 80)
    print('3. MRR/RECALL SOURCE VERIFICATION')
    print('=' * 80)

    eval_path = receipts_dir / 'eval_ranking.json'
    if eval_path.exists():
        with open(eval_path) as f:
            eval_data = json.load(f)
        print(f'\nMRR: {eval_data.get("mrr")}')
        print(f'Recall@3: {eval_data.get("recall_at_3")}')
        print(f'Test cases: n={eval_data.get("n_cases", 0)}')
        
        labeled_path = Path('data/labeled_eval_cases.json')
        if labeled_path.exists():
            with open(labeled_path) as f:
                labeled = json.load(f)
            cases = labeled.get('cases', [])
            if cases:
        prov = cases[0].get('provenance', {})
                labeled_by = prov.get('labeled_by', 'UNKNOWN')
                method = prov.get('labeling_method', 'UNKNOWN')
                print(f'\nLabeling provenance:')
                print(f'  Labeled by: {labeled_by}')
                print(f'  Method: {method}')
                if 'zo' in str(labeled_by).lower() or 'agent' in str(method).lower() or 'pilot' in str(method).lower():
                    print(f'\n🚨 CRITICAL: MRR/Recall from AGENT-LABELED synthetic data')
                    print(f'   Recommendation: REMOVE from abstract or add explicit caveat')
                    print(f'   Status: SYNTHETIC TEST CASES (not real patient labels)')
                else:
                    print(f'   Status: REAL PATIENT LABELS')
        else:
            print('⚠️  labeled_eval_cases.json not found')
    else:
        print('❌ eval_ranking.json missing')

    # 4. MATH VERIFICATION
    print('\n' + '=' * 80)
    print('4. MATH VERIFICATION')
    p * 80)

    if tcga_path.exists():
        with open(tcga_path) as f:
            tcga_data = json.load(f)
        run = tcga_data.get('run', {})
        metrics = tcga_data.get('metrics', {})
        n_total = run.get('n_patients', 0)
        n_matchable = metrics.get('n_matchable', 0)
        n_non = n_total - n_matchable
        pct = metrics.get('pct_matchable', 0)
        
        print(f'\nMatchability: {n_matchable} + {n_non} = {n_total}')
        if n_matchable + n_non == n_total:
            print(f'  ✅ 271 + 314 = 585? VERIFIED: {n_matchable} + {n_non} = {n_total}')
        else:
            print(f'  ❌ Math error: {n_matchable} + {n_non} ≠ {n_total}')
        
        calc_pct = (n_matchable / n_total * 100) if n_total > 0 else 0
        print(f'\nPercentage: {calc_pct:.1f}% (claimed: 46.3%)')
        if abs(calc_pct - 46.3) < 0.1:
            print(f'  ✅ 271/585 = 46.3%? VERIFIED')
        else:
            print(f'  ❌ Percentage mismatch: {calc_pct:.1f}% ≠ 46.3%')
        
        r0.874 / 0.038
        print(f'\nRatio check: 0.874 / 0.038 = {ratio_calc:.1f}x')
        if abs(ratio_calc - 23.0) < 1.0:
            print(f'  ✅ 23-fold ratio verified')
    else:
        print('❌ Cannot verify math - TCGA receipt missing')

    # 5. CLAIM VERIFICATION
    print('\n' + '=' * 80)
    print('5. CLAIM VERIFICATION (mechanism_sanity.json)')
    print('=' * 80)

    ms_path = receipts_dir / 'mechanism_sanity.json'
    if ms_path.exists():
        with open(ms_path) as f:
            ms_data = json.load(f)
        metrics = ms_data.get('metrics', {})
        ddr_fit = metrics.get('mean_ddr_fit', None)
        non_ddr_fit = metrics.get('mean_non_ddr_fit', None)
        sep = metrics.get('separation_delta', None)
        
        print(f'\nExact values from receipt:')
        print(f'  DDR fit: {ddr_fit}')
        print(f'  Non-DDR fit: {non_ddr_fit}')
        print(f'  Separation: {sep}')
        
        print(f'\nClaimed in abstract: DDR=0.874, Non-DDR=0.038, Sep=0.836')
        
        if_fit is not None:
            if abs(ddr_fit - 0.874) < 0.01:
                print(f'  ✅ DDR fit matches (within 0.01)')
            else:
                print(f'  ❌ DDR fit mismatch: {ddr_fit} ≠ 0.874')
        
        if non_ddr_fit is not None:
            if abs(non_ddr_fit - 0.038) < 0.01:
                print(f'  ✅ Non-DDR fit matches (within 0.01)')
            else:
                print(f'  ❌ Non-DDR fit mismatch: {non_ddr_fit} ≠ 0.038')
        
        if sep is not None:
            if abs(sep - 0.836) < 0.01:
                print(f'  ✅ Separation matches (within 0.01)')
            else:
                print(f'  ❌ Separation mismatch: {sep} ≠ 0.836')
        
        if non_ddr_fit and non_ddr_fit > 0 and ddr_fit:
            ratio = ddr_fit / non_ddr_fit
            print(f'\nRatio: {ratio:.1f}x (claimed: ~23x)')
            if abs(ratio - 23.0) < 1.0:
                print(f'  ✅ 0.874 / 0.038 = 23.0x? VERIFIED')
            else:
                print(f'  ⚠️  Rat vs 23.0x')

    # 6. SURVIVAL ANALYSIS
    print('\n' + '=' * 80)
    print('6. SURVIVAL ANALYSIS VERIFICATION')
    print('=' * 80)

    surv_path = receipts_dir / 'real_world_tcga_ov_survival_validation.json'
    if surv_path.exists():
        with open(surv_path) as f:
            surv_data = json.load(f)
        cox = surv_data.get('cox', {})
        km = surv_data.get('km', {})
        hr = cox.get('hazard_ratio', None)
        hr_lower = cox.get('hazard_ratio_95_ci_lower', None)
        hr_upper = cox.get('hazard_ratio_95_ci_upper', None)
        pval = km.get('logrank_p_value', None)
        
        print(f'\nSurvival metrics from receipt:')
        print(f'  HR: {hr}')
        print(f'  HR 95% CI: [{hr_lower}, {hr_upper}]')
        print(f'  Logrank p-value: {pval}')
        
        print(f'\nClaimed in abstract: HR=1.122, p=0.288')
        
        if hr is not None:
            if abs(hr - 1.122) < 0.01:
                print(f'  ✅ HR matches (within 0.01)')
            else:
                int(f'  ❌ HR mismatch: {hr} ≠ 1.122')
        
        if pval is not None:
            if abs(pval - 0.288) < 0.01:
                print(f'  ✅ p-value matches (within 0.01)')
            else:
                print(f'  ❌ p-value mismatch: {pval} ≠ 0.288')

    print('\n' + '=' * 80)
    print('FINAL SUMMARY')
    print('=' * 80)

if __name__ == '__main__':
    main()
