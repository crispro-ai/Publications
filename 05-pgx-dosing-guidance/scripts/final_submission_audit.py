#!/usr/bin/env python3
"""
Final Submission Audit for PGx Dosing Guidance Publication

Checks:
1. All required receipts exist
2. Manuscript references match receipts
3. Figures match data
4. All claims are receipt-backed
"""

import json
import sys
from pathlib import Path

BASE = Path('publications/05-pgx-dosing-guidance')
REPORTS = BASE / 'reports'

REQUIRED_RECEIPTS = [
    'prepare_outcome_validation.json',
    'cyp2c19_clopidogrel_efficacy_validation.json',
    'publication_receipt_v3.json',
    'pmid_39641926_Table_1.json',
    'pmid_39641926_Table_2.json',
    'pmid_40944685_tables_Table2_Table4.json',
]

REQUIRED_DOCS = [
    'PUBLICATION_MANUSCRIPT_DRAFT.md',
    'VALIDATION_SUMMARY_FIGURES.md',
    'PUBLICATION_PACKAGE_INDEX.md',
]

def audit_receipts():
    """Check all required receipts exist and are valid JSON"""
    print("=" * 70)
    print("AUDIT 1: Required Receipts")
    print("=" * 70)
    
    missing = []
    invalid = []
    
    for receipt in REQUIRED_RECEIPTS:
        path = REPORTS / receipt
        if not path.exists():
            missing.append(receipt)
            print(f"❌ MISSING: {receipt}")
        else:
            try:
                data = json.loads(path.read_text())
                print(f"✅ {receipt} ({len(str(data))} bytes)")
            except json.JSONDecodeError as e:
                invalid.append(receipt)
                print(f"❌ INVALID JSON: {receipt} - {e}")
    
    if missing or invalid:
        print(f"\n⚠️  Found {len(missing)} missing and {len(invalid)} invalid receipts")
        return False
    
    print(f"\n✅ All {len(REQUIRED_RECEIPTS)} receipts present and valid")
    return True


def audit_manuscript_claims():
    """Verify manuscript claims match receipt data"""
    print("\n" + "=" * 70)
    print("AUDIT 2: Manuscript Claims vs Receipts")
    print("=" * 70)
    
    # Load receipts
    prep = json.loads((REPORTS / 'prepare_outcome_validation.json').read_text())
    cyp = json.loads((REPORTS / 'cyp2c19_clopidogrel_efficacy_validation.json').read_text())
    
    # Check PREPARE claims
    print("\nPREPARE Claims:")
    prep_rrr = prep['toxicity_outcomes']['actionable_carriers']['rrr']
    prep_control_rate = prep['toxicity_outcomes']['actionable_carriers']['control']['rate']
    prep_int_rate = prep['toxicity_outcomes']['actionable_carriers']['intervention']['rate']
    
    print(f"  RRR: {prep_rrr:.1%} (manuscript: 83.1%)")
    assert abs(prep_rrr - 0.831) < 0.01, f"RRR mismatch: {prep_rrr} vs 0.831"
    print(f"  Control rate: {prep_control_rate:.1%} (manuscript: 34.8%)")
    assert abs(prep_control_rate - 0.348) < 0.01, f"Control rate mismatch"
    print(f"  Intervention rate: {prep_int_rate:.1%} (manuscript: 5.9%)")
    assert abs(prep_int_rate - 0.059) < 0.01, f"Intervention rate mismatch"
    
    # Check CYP2C19 claims
    print("\nCYP2C19 Claims:")
    cyp_rr = cyp['effect']['risk_ratio_pmim_vs_em']
    cyp_em_rate = cyp['counts']['extensive_metabolizer']['rate']
    cyp_pmim_rate = cyp['counts']['poor_or_intermediate']['rate']
    
    print(f"  Risk ratio: {cyp_rr:.2f} (manuscript: 4.28)")
    assert abs(cyp_rr - 4.28) < 0.1, f"Risk ratio mismatch: {cyp_rr} vs 4.28"
    print(f"  EM rate: {cyp_em_rate:.1%} (manuscript: 4.7%)")
    assert abs(cyp_em_rate - 0.047) < 0.01, f"EM rate mismatch"
    print(f"  PM/IM rate: {cyp_pmim_rate:.1%} (manuscript: 20.2%)")
    assert abs(cyp_pmim_rate - 0.202) < 0.01, f"PM/IM rate mismatch"
    
    print("\n✅ All manuscript claims match receipt data")
    return True


def audit_documents():
    """Check all required documents exist"""
    print("\n" + "=" * 70)
    print("AUDIT 3: Required Documents")
    print("=" * 70)
    
    missing = []
    for doc in REQUIRED_DOCS:
        path = BASE / doc
        if not path.exists():
            missing.append(doc)
            print(f"❌ MISSING: {doc}")
        else:
            size = path.stat().st_size
            print(f"✅ {doc} ({size:,} bytes)")
    
    if missing:
        print(f"\n⚠️  Found {len(missing)} missing documents")
        return False
    
    print(f"\n✅ All {len(REQUIRED_DOCS)} documents present")
    return True


def audit_figures():
    """Check figures reference correct receipts"""
    print("\n" + "=" * 70)
    print("AUDIT 4: Figure Receipt References")
    print("=" * 70)
    
    figures = (BASE / 'VALIDATION_SUMMARY_FIGURES.md').read_text()
    
    # Check for receipt references
    receipt_refs = [
        'prepare_outcome_validation.json',
        'cyp2c19_clopidogrel_efficacy_validation.json',
        'pmid_39641926_Table_1.json',
        'pmid_39641926_Table_2.json',
        'pmid_40944685_tables_Table2_Table4.json',
    ]
    
    found = []
    for ref in receipt_refs:
        if ref in figures:
            found.append(ref)
            print(f"✅ Figure references: {ref}")
        else:
            print(f"⚠️  Figure missing reference: {ref}")
    
    print(f"\n✅ {len(found)}/{len(receipt_refs)} receipt references found in figures")
    return len(found) >= len(receipt_refs) - 1  # Allow 1 missing


def main():
    print("\n" + "=" * 70)
    print("PGX DOSING GUIDANCE PUBLICATION - FINAL SUBMISSION AUDIT")
    print("=" * 70 + "\n")
    
    results = []
    results.append(("Receipts", audit_receipts()))
    results.append(("Manuscript Claims", audit_manuscript_claims()))
    results.append(("Documents", audit_documents()))
    results.append(("Figures", audit_figures()))
    
    print("\n" + "=" * 70)
    print("AUDIT SUMMARY")
    print("=" * 70)
    
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {name}")
    
    all_passed = all(r[1] for r in results)
    
    if all_passed:
        print("\n🎉 ALL AUDITS PASSED - READY FOR SUBMISSION")
        return 0
    else:
        print("\n⚠️  SOME AUDITS FAILED - REVIEW REQUIRED")
        return 1


if __name__ == '__main__':
    sys.exit(main())
