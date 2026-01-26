#!/usr/bin/env python3
"""
Quick test of rate limiting with 3 queries
"""

import asyncio
import sys
from pathlib import Path

# Load .env files
from dotenv import load_dotenv
project_root = Path(__file__).parent.parent.parent.parent
backend_env = project_root / "oncology-coPilot" / "oncology-backend-minimal" / ".env"
root_env = project_root / ".env"

if backend_env.exists():
    load_dotenv(backend_env, override=False)
if root_env.exists():
    load_dotenv(root_env, override=True)

sys.path.insert(0, str(project_root / "oncology-coPilot" / "oncology-backend-minimal"))

from api.services.research_intelligence.orchestrator import ResearchIntelligenceOrchestrator

# Import the rate-limited function
from run_validation_suite import run_ri_on_query

async def test_rate_limiting():
    """Test rate limiting with 3 queries."""
    print("=" * 60)
    print("RATE LIMITING TEST (3 queries)")
    print("=" * 60)
    
    orchestrator = ResearchIntelligenceOrchestrator()
    
    test_queries = [
        {
            "query_id": "test_1",
            "question": "What mechanisms does curcumin target in breast cancer?",
            "context": {"disease": "breast cancer", "compound": "curcumin"}
        },
        {
            "query_id": "test_2",
            "question": "How does vitamin D help with ovarian cancer?",
            "context": {"disease": "ovarian cancer", "compound": "vitamin D"}
        },
        {
            "query_id": "test_3",
            "question": "What evidence exists for green tea extract in cancer prevention?",
            "context": {"disease": "cancer", "compound": "green tea extract"}
        }
    ]
    
    results = []
    for i, query in enumerate(test_queries, 1):
        print(f"\n📋 Query {i}/3: {query['question'][:50]}...")
        result = await run_ri_on_query(query, orchestrator, max_retries=3)
        results.append(result)
        
        if 'error' in result:
            print(f"  ❌ Error: {result['error']}")
        else:
            print(f"  ✅ Success: {len(result.get('mechanisms', []))} mechanisms, {len(result.get('pathways', []))} pathways")
        
        # Delay between queries
        if i < len(test_queries):
            print(f"  ⏳ Waiting 2s before next query...")
            await asyncio.sleep(2)
    
    print("\n" + "=" * 60)
    print("TEST COMPLETE")
    print("=" * 60)
    print(f"Successful: {len([r for r in results if 'error' not in r])}/3")
    print(f"Total mechanisms: {sum(len(r.get('mechanisms', [])) for r in results)}")
    print(f"Total pathways: {sum(len(r.get('pathways', [])) for r in results)}")

if __name__ == "__main__":
    asyncio.run(test_rate_limiting())

