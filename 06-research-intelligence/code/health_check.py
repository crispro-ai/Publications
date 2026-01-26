#!/usr/bin/env python3
"""
Health Check for Research Intelligence System

Tests:
1. Environment variables loaded
2. PubMed portal connectivity
3. LLM service connectivity
4. Basic query execution
"""

import sys
import os
import asyncio
from pathlib import Path
from dotenv import load_dotenv

# Load .env files
project_root = Path(__file__).parent.parent.parent.parent
backend_env = project_root / "oncology-coPilot" / "oncology-backend-minimal" / ".env"
root_env = project_root / ".env"

if backend_env.exists():
    load_dotenv(backend_env, override=False)
if root_env.exists():
    load_dotenv(root_env, override=True)

# Add backend to path
sys.path.insert(0, str(project_root / "oncology-coPilot" / "oncology-backend-minimal"))

print("=" * 60)
print("RESEARCH INTELLIGENCE HEALTH CHECK")
print("=" * 60)

# Test 1: Environment Variables
print("\n[1] Checking Environment Variables...")
checks = {
    "NCBI_USER_EMAIL": os.getenv('NCBI_USER_EMAIL'),
    "NCBI_USER_API_KEY": os.getenv('NCBI_USER_API_KEY') or os.getenv('NCBI_API_KEY'),
    "GEMINI_API_KEY": os.getenv('GEMINI_API_KEY'),
    "GOOGLE_API_KEY": os.getenv('GOOGLE_API_KEY'),
}

all_set = True
for key, value in checks.items():
    if value and value not in ["your_email@example.com", "your_api_key_here"]:
        print(f"  ✅ {key}: {value[:20]}...")
    else:
        print(f"  ❌ {key}: NOT SET or placeholder")
        all_set = False

if not all_set:
    print("\n⚠️  Some credentials missing. Continuing with available services...")

# Test 2: Import Orchestrator
print("\n[2] Testing Orchestrator Import...")
try:
    from api.services.research_intelligence.orchestrator import ResearchIntelligenceOrchestrator
    print("  ✅ Orchestrator imported successfully")
except Exception as e:
    print(f"  ❌ Import failed: {e}")
    sys.exit(1)

# Test 3: Initialize Orchestrator
print("\n[3] Testing Orchestrator Initialization...")
try:
    orchestrator = ResearchIntelligenceOrchestrator()
    is_available = orchestrator.is_available()
    print(f"  ✅ Orchestrator initialized (available: {is_available})")
    
    # Check components
    print(f"    - PubMed Portal: {'✅' if orchestrator.pubmed else '❌'}")
    print(f"    - PubMed Parser: {'✅' if orchestrator.pubmed_parser else '❌'}")
    print(f"    - Question Formulator: {'✅' if orchestrator.question_formulator else '❌'}")
    print(f"    - Synthesis Engine: {'✅' if orchestrator.synthesis_engine else '❌'}")
    print(f"    - MOAT Integrator: {'✅' if orchestrator.moat_integrator else '❌'}")
except Exception as e:
    print(f"  ❌ Initialization failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 4: Simple PubMed Query
print("\n[4] Testing PubMed Portal (Simple Query)...")
async def test_pubmed():
    if not orchestrator.pubmed:
        print("  ⚠️  PubMed portal not available, skipping")
        return False
    
    try:
        # Simple test query
        test_query = "curcumin AND cancer"
        print(f"    Query: {test_query}")
        
        result = await orchestrator.pubmed.search_with_analysis(
            query=test_query,
            max_results=5,
            analyze_keywords=False
        )
        
        articles = result.get('articles', [])
        print(f"    ✅ PubMed query successful: {len(articles)} articles found")
        
        if articles:
            print(f"    Sample article: {articles[0].get('title', 'N/A')[:60]}...")
            return True
        else:
            print("    ⚠️  No articles returned (may be rate-limited or query issue)")
            return False
            
    except Exception as e:
        print(f"    ❌ PubMed query failed: {e}")
        import traceback
        traceback.print_exc()
        return False

pubmed_ok = asyncio.run(test_pubmed())

# Test 5: LLM Service
print("\n[5] Testing LLM Service (Synthesis Engine)...")
async def test_llm():
    if not orchestrator.synthesis_engine:
        print("  ⚠️  Synthesis engine not available, skipping")
        return False
    
    try:
        # Test simple synthesis
        test_findings = {
            "mechanisms": [],
            "evidence_summary": "Test evidence",
            "overall_confidence": 0.5
        }
        
        # Just check if LLM service is callable (don't actually call to avoid costs)
        has_llm = hasattr(orchestrator.synthesis_engine, 'llm') and orchestrator.synthesis_engine.llm is not None
        print(f"    ✅ LLM service available: {has_llm}")
        return has_llm
        
    except Exception as e:
        print(f"    ❌ LLM service check failed: {e}")
        return False

llm_ok = asyncio.run(test_llm())

# Test 6: Rate Limiting Check
print("\n[6] Checking Rate Limiting Configuration...")
try:
    # Check if PubMed portal has rate limiting
    if orchestrator.pubmed:
        has_rate_limit = hasattr(orchestrator.pubmed, 'rate_limiter') or hasattr(orchestrator.pubmed.searcher, 'rate_limiter')
        print(f"    PubMed rate limiting: {'✅ Configured' if has_rate_limit else '⚠️  Not configured'}")
    
    # Check LLM rate limiting
    if orchestrator.synthesis_engine and hasattr(orchestrator.synthesis_engine, 'llm'):
        llm = orchestrator.synthesis_engine.llm
        has_llm_rate_limit = hasattr(llm, 'rate_limiter') or hasattr(llm, '_rate_limit')
        print(f"    LLM rate limiting: {'✅ Configured' if has_llm_rate_limit else '⚠️  Not configured'}")
except Exception as e:
    print(f"    ⚠️  Rate limiting check failed: {e}")

# Summary
print("\n" + "=" * 60)
print("HEALTH CHECK SUMMARY")
print("=" * 60)
print(f"Environment Variables: {'✅' if all_set else '⚠️ '}")
print(f"Orchestrator: ✅")
print(f"PubMed Portal: {'✅' if pubmed_ok else '❌'}")
print(f"LLM Service: {'✅' if llm_ok else '⚠️ '}")

if pubmed_ok and llm_ok:
    print("\n✅ System is healthy and ready for validation!")
    sys.exit(0)
else:
    print("\n⚠️  System has issues. Review errors above.")
    sys.exit(1)

