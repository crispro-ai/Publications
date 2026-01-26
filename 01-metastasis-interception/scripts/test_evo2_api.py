#!/usr/bin/env python3
"""
Test Evo2 API endpoints for prospective validation

Tests the three Evo2 endpoints needed for Target-Lock scoring:
1. predict_protein_functionality_change
2. predict_gene_essentiality
3. predict_splicing_regulatory
"""

import asyncio
import httpx
import json
from typing import Dict, Any

# Test API base URL
API_BASE = "https://crispro--evo-service-evoservice1b-api-1b.modal.run"

# Test gene
TEST_GENE = "RET"  # One of our prospective validation genes

async def test_functionality(gene: str) -> Dict[str, Any]:
    """Test functionality endpoint."""
    print(f"\n🔬 Testing functionality for {gene}...")
    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            resp = await client.post(
                f"{API_BASE}/api/insights/predict_protein_functionality_change",
                json={"gene": gene, "hgvs_p": None, "model_id": "evo2_1b"},
                timeout=60.0
            )
            print(f"  Status: {resp.status_code}")
            if resp.status_code == 200:
                data = resp.json()
                print(f"  ✅ Response: {json.dumps(data, indent=2)}")
                return {"success": True, "data": data}
            else:
                print(f"  ❌ Error: {resp.text}")
                return {"success": False, "error": resp.text}
        except Exception as e:
            print(f"  ❌ Exception: {str(e)}")
            return {"success": False, "error": str(e)}

async def test_essentiality(gene: str) -> Dict[str, Any]:
    """Test essentiality endpoint."""
    print(f"\n🔬 Testing essentiality for {gene}...")
    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            resp = await client.post(
                f"{API_BASE}/api/insights/predict_gene_essentiality",
                json={"gene": gene, "variants": [], "model_id": "evo2_1b"},
                timeout=60.0
            )
            print(f"  Status: {resp.status_code}")
            if resp.status_code == 200:
                data = resp.json()
                print(f"  ✅ Response: {json.dumps(data, indent=2)}")
                return {"success": True, "data": data}
            else:
                print(f"  ❌ Error: {resp.text}")
                return {"success": False, "error": resp.text}
        except Exception as e:
            print(f"  ❌ Exception: {str(e)}")
            return {"success": False, "error": str(e)}

async def test_regulatory(gene: str) -> Dict[str, Any]:
    """Test regulatory endpoint (needs coordinates)."""
    print(f"\n🔬 Testing regulatory for {gene}...")
    # RET is on chromosome 10, position ~43609946 (example)
    # We'll use a placeholder position - in real usage, we'd fetch from Ensembl
    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            resp = await client.post(
                f"{API_BASE}/api/insights/predict_splicing_regulatory",
                json={
                    "chrom": "10",
                    "pos": 43609946,
                    "ref": "A",
                    "alt": "G",
                    "model_id": "evo2_1b"
                },
                timeout=60.0
            )
            print(f"  Status: {resp.status_code}")
            if resp.status_code == 200:
                data = resp.json()
                print(f"  ✅ Response: {json.dumps(data, indent=2)}")
                return {"success": True, "data": data}
            else:
                print(f"  ❌ Error: {resp.text}")
                return {"success": False, "error": resp.text}
        except Exception as e:
            print(f"  ❌ Exception: {str(e)}")
            return {"success": False, "error": str(e)}

async def main():
    """Run all tests."""
    print("=" * 70)
    print("EVO2 API TEST")
    print("=" * 70)
    print(f"API Base: {API_BASE}")
    print(f"Test Gene: {TEST_GENE}")
    print()
    
    results = {}
    
    # Test 1: Functionality
    results["functionality"] = await test_functionality(TEST_GENE)
    
    # Test 2: Essentiality
    results["essentiality"] = await test_essentiality(TEST_GENE)
    
    # Test 3: Regulatory
    results["regulatory"] = await test_regulatory(TEST_GENE)
    
    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    
    for endpoint, result in results.items():
        status = "✅ PASS" if result.get("success") else "❌ FAIL"
        print(f"{endpoint:20s}: {status}")
        if result.get("success") and "data" in result:
            # Extract score if available
            data = result["data"]
            if "functionality_score" in data:
                print(f"  Score: {data['functionality_score']}")
            elif "essentiality_score" in data:
                print(f"  Score: {data['essentiality_score']}")
            elif "regulatory_impact_score" in data:
                print(f"  Score: {data['regulatory_impact_score']}")
    
    # Overall status
    all_passed = all(r.get("success", False) for r in results.values())
    print(f"\nOverall: {'✅ ALL TESTS PASSED' if all_passed else '❌ SOME TESTS FAILED'}")
    
    return results

if __name__ == "__main__":
    results = asyncio.run(main())
