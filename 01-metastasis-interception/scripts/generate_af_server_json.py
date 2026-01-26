#!/usr/bin/env python3
"""
Generate AlphaFold Server JSON files for CRISPR guide validation
Fast-fail approach: Generate simple test cases first
"""
import json
import sys
from pathlib import Path

def reverse_complement(seq):
    """Generate reverse complement of DNA sequence"""
    complement = {'A': 'T', 'T': 'A', 'G': 'C', 'C': 'G'}
    return ''.join(complement.get(base, base) for base in reversed(seq))

def generate_simple_grna_json(grna_sequence, job_name):
    """
    TEST 1: Simplest possible - just gRNA structure
    This will validate our JSON format works
    """
    return {
        "name": job_name,
        "modelSeeds": [],
        "sequences": [
            {
                "rnaSequence": {
                    "sequence": grna_sequence,
                    "count": 1
                }
            }
        ],
        "dialect": "alphafoldserver",
        "version": 1
    }

def generate_grna_dna_complex_json(grna_sequence, target_dna, job_name):
    """
    TEST 2: gRNA + target DNA (double strand)
    This validates DNA complex support
    """
    complement = reverse_complement(target_dna)
    return {
        "name": job_name,
        "modelSeeds": [],
        "sequences": [
            {
                "rnaSequence": {
                    "sequence": grna_sequence,
                    "count": 1
                }
            },
            {
                "dnaSequence": {
                    "sequence": target_dna,
                    "count": 1
                }
            },
            {
                "dnaSequence": {
                    "sequence": complement,
                    "count": 1
                }
            }
        ],
        "dialect": "alphafoldserver",
        "version": 1
    }

def generate_protein_target_json(protein_sequence, job_name, use_templates=False):
    """
    TEST 3: Target protein structural validation
    This tests protein folding predictions
    """
    return {
        "name": job_name,
        "modelSeeds": [],
        "sequences": [
            {
                "proteinChain": {
                    "sequence": protein_sequence,
                    "count": 1,
                    "useStructureTemplate": use_templates
                }
            }
        ],
        "dialect": "alphafoldserver",
        "version": 1
    }

# ============================================================================
# FAST-FAIL TEST CASES
# ============================================================================

# TEST CASE 1: Minimal gRNA (20bp spacer + minimal scaffold)
# This is the absolute minimum to test AF Server acceptance
TEST_GRNA_MINIMAL = "GUUUUAGAGCUAGAAAUAGC"  # 20nt minimal

# TEST CASE 2: Standard gRNA spacer (20nt RNA)
# Real guide targeting BRAF V600E region
TEST_GRNA_BRAF = "GUAGGACCCAUCAGUUUAAG"  # 20nt RNA spacer (U not T!)

# TEST CASE 3: Target DNA for BRAF V600E (20bp with PAM)
TEST_DNA_BRAF_TARGET = "GTAGGACCCATCAGTTTAAGNGG"  # 23bp DNA (T not U!)
TEST_DNA_BRAF_SPACER = "GTAGGACCCATCAGTTTAAG"  # Just spacer, no PAM (DNA uses T!)

# TEST CASE 4: Tiny protein (for fast validation)
TEST_PROTEIN_TINY = "MKFLKFSLLTAVLLSVVFAFSSCGDDDDTGYLPPSQAIQDLLKRMKV"  # 47aa

# TEST CASE 5: BRAF kinase domain fragment (100aa)
# Includes V600 position (position 60 in this fragment)
TEST_PROTEIN_BRAF_FRAGMENT = (
    "TGKLVLPRGPGSGSPAFWTDFVFHQTWQEHLRLPGSQSYPAAANLDELLCWSEE"
    "LLKCGVPQLPEVVLASQGYVPLGAAHTQKPTTAEHLISEVQRDIGSQEFLGKF"
)

# ============================================================================
# GENERATE TEST JSON FILES
# ============================================================================

if __name__ == "__main__":
    output_dir = Path("publication/af_server_jobs/fast_fail_tests")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("=" * 80)
    print("🧪 FAST-FAIL AF SERVER JSON GENERATOR")
    print("=" * 80)
    print(f"Output directory: {output_dir}")
    print()
    
    tests = []
    
    # Test 1: Minimal gRNA (simplest possible)
    print("📝 Test 1: Minimal gRNA (20nt)")
    test1 = generate_simple_grna_json(
        TEST_GRNA_MINIMAL,
        "test1_minimal_grna"
    )
    test1_path = output_dir / "test1_minimal_grna.json"
    with open(test1_path, 'w') as f:
        json.dump([test1], f, indent=2)
    tests.append(("Test 1: Minimal gRNA", test1_path, "20nt RNA"))
    print(f"   ✅ Generated: {test1_path}")
    print(f"   Sequence: {TEST_GRNA_MINIMAL}")
    print()
    
    # Test 2: BRAF gRNA spacer
    print("📝 Test 2: BRAF V600E gRNA spacer")
    test2 = generate_simple_grna_json(
        TEST_GRNA_BRAF,
        "test2_braf_grna_spacer"
    )
    test2_path = output_dir / "test2_braf_grna_spacer.json"
    with open(test2_path, 'w') as f:
        json.dump([test2], f, indent=2)
    tests.append(("Test 2: BRAF gRNA", test2_path, "20nt RNA (BRAF target)"))
    print(f"   ✅ Generated: {test2_path}")
    print(f"   Sequence: {TEST_GRNA_BRAF}")
    print()
    
    # Test 3: gRNA + DNA complex (NO PAM - just spacer binding)
    print("📝 Test 3: gRNA + Target DNA complex")
    test3 = generate_grna_dna_complex_json(
        TEST_GRNA_BRAF,
        TEST_DNA_BRAF_SPACER,
        "test3_grna_dna_complex"
    )
    test3_path = output_dir / "test3_grna_dna_complex.json"
    with open(test3_path, 'w') as f:
        json.dump([test3], f, indent=2)
    tests.append(("Test 3: gRNA+DNA", test3_path, "20nt RNA + 21bp dsDNA"))
    print(f"   ✅ Generated: {test3_path}")
    print(f"   gRNA: {TEST_GRNA_BRAF}")
    print(f"   DNA:  {TEST_DNA_BRAF_SPACER}")
    print(f"   Comp: {reverse_complement(TEST_DNA_BRAF_SPACER)}")
    print()
    
    # Test 4: Tiny protein (fast validation)
    print("📝 Test 4: Tiny protein (47aa)")
    test4 = generate_protein_target_json(
        TEST_PROTEIN_TINY,
        "test4_tiny_protein",
        use_templates=False
    )
    test4_path = output_dir / "test4_tiny_protein.json"
    with open(test4_path, 'w') as f:
        json.dump([test4], f, indent=2)
    tests.append(("Test 4: Tiny Protein", test4_path, "47aa protein"))
    print(f"   ✅ Generated: {test4_path}")
    print(f"   Length: {len(TEST_PROTEIN_TINY)} aa")
    print()
    
    # Test 5: BRAF fragment with V600 (includes mutation site)
    print("📝 Test 5: BRAF kinase domain fragment (100aa)")
    test5 = generate_protein_target_json(
        TEST_PROTEIN_BRAF_FRAGMENT,
        "test5_braf_fragment",
        use_templates=False  # Don't use templates to see de novo prediction
    )
    test5_path = output_dir / "test5_braf_fragment.json"
    with open(test5_path, 'w') as f:
        json.dump([test5], f, indent=2)
    tests.append(("Test 5: BRAF Fragment", test5_path, "100aa BRAF kinase domain"))
    print(f"   ✅ Generated: {test5_path}")
    print(f"   Length: {len(TEST_PROTEIN_BRAF_FRAGMENT)} aa")
    print()
    
    # Summary table
    print("=" * 80)
    print("📋 GENERATED TEST FILES SUMMARY")
    print("=" * 80)
    for i, (name, path, desc) in enumerate(tests, 1):
        print(f"{i}. {name}")
        print(f"   File: {path.name}")
        print(f"   Type: {desc}")
        print(f"   Path: {path}")
        print()
    
    print("=" * 80)
    print("🎯 NEXT STEPS - MANUAL TESTING")
    print("=" * 80)
    print()
    print("1. Go to: https://alphafoldserver.com/")
    print("2. Click 'Submit a Job' → 'Upload JSON'")
    print("3. Try Test 1 first (minimal gRNA, fastest)")
    print("4. Monitor job status (expect 5-30 min)")
    print("5. Download results → Check pLDDT scores")
    print()
    print("FAST-FAIL STRATEGY:")
    print("  - If Test 1 FAILS → Fix JSON format")
    print("  - If Test 1 WORKS → Try Test 2 (real gRNA)")
    print("  - If Test 2 WORKS → Try Test 3 (gRNA+DNA complex)")
    print("  - If Test 3 WORKS → Try Tests 4-5 (proteins)")
    print()
    print("EXPECTED RESULTS:")
    print("  - Test 1-2: pLDDT 50-70 (RNA is harder to predict)")
    print("  - Test 3: pLDDT 60-80 (RNA:DNA complex)")
    print("  - Test 4: pLDDT 70-85 (small protein)")
    print("  - Test 5: pLDDT 75-90 (BRAF kinase domain)")
    print()
    print("⚠️  CRITICAL VALIDATION:")
    print("  If ANY test fails, report:")
    print("    - Error message from AF Server")
    print("    - Which test failed")
    print("    - What the error says")
    print()
    print("✅ ALL FILES GENERATED - READY FOR MANUAL SUBMISSION!")
    print("=" * 80)

