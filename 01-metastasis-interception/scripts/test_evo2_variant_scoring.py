#!/usr/bin/env python3
"""
Test Evo2 variant scoring endpoints

This service has different endpoints than the insights service.
Let's test what's available.
"""

import asyncio
import httpx
import json

API_BASE = "https://testing1235--main-evoservicewrapper-api.modal.run"
TEST_GENE = "RET"

async def test_score_variant():
    """Test /score_variant endpoint."""
    print(f"\n🔬 Testing /score_variant for {TEST_GENE}...")
    async with httpx.AsyncClient(timeout=120.0) as client:
        try:
            # RET is on chr10, position ~43609946
            # Example variant: chr10:43609946 A>G
            payload = {
                "chrom": "10",
                "pos": 43609946,
                "ref": "A",
                "alt": "G",
                "model_id": "evo2_1b"
            }
            resp = await client.post(
                f"{API_BASE}/score_variant",
                json=payload,
                timeout=120.0
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

async def test_score_delta():
    """Test /score_delta endpoint."""
    print(f"\n🔬 Testing /score_delta...")
    async with httpx.AsyncClient(timeout=120.0) as client:
        try:
            # Simple test: same sequence (should give delta=0)
            payload = {
                "ref_sequence": "ATCGATCGATCGATCGATCG",
                "alt_sequence": "ATCGATCGATCGATCGATCG"
            }
            resp = await client.post(
                f"{API_BASE}/score_delta",
                json=payload,
                timeout=120.0
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
    """Run tests."""
    print("=" * 70)
    print("EVO2 VARIANT SCORING API TEST")
    print("=" * 70)
    print(f"API Base: {API_BASE}")
    print(f"Test Gene: {TEST_GENE}")
    print()
    
    results = {}
    
    # Test score_delta (we know this works)
    results["score_delta"] = await test_score_delta()
    
    # Test score_variant
    results["score_variant"] = await test_score_variant()
    
    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    
    for endpoint, result in results.items():
        status = "✅ PASS" if result.get("success") else "❌ FAIL"
        print(f"{endpoint:20s}: {status}")
    
    all_passed = all(r.get("success", False) for r in results.values())
    print(f"\nOverall: {'✅ ALL TESTS PASSED' if all_passed else '❌ SOME TESTS FAILED'}")
    
    print("\n📝 NOTE: This is a lower-level Evo2 service.")
    print("   The insights endpoints (/api/insights/...) may be in a different service.")
    print("   We may need to find the insights service URL or adapt our approach.")
    
    return results

if __name__ == "__main__":
    asyncio.run(main())
