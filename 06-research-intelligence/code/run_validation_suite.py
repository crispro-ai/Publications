#!/usr/bin/env python3
"""
Sprint 6: Run Research Intelligence on 100 Queries

Run Research Intelligence orchestrator on all 100 queries
Extract predictions: mechanisms, pathways, evidence_tier, confidence
Output: validation_results.json with predictions for all queries

Rate Limiting:
- 2 second delay between queries (configurable via QUERY_DELAY_SECONDS)
- Exponential backoff for rate limit errors (429, quota, permission denied)
- Max 3 retries per query with exponential backoff (2^attempt seconds)
"""

import json
import sys
import asyncio
import os
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime

# Rate limiting configuration
QUERY_DELAY_SECONDS = float(os.getenv('QUERY_DELAY_SECONDS', '2.0'))  # Delay between queries
MAX_RETRIES = int(os.getenv('MAX_RETRIES', '3'))  # Max retries for rate limit errors

# Load .env file first - load both backend and root to get all credentials
try:
    from dotenv import load_dotenv
    project_root = Path(__file__).parent.parent.parent.parent
    
    # Load backend .env first (base credentials)
    backend_env = project_root / "oncology-coPilot" / "oncology-backend-minimal" / ".env"
    if backend_env.exists():
        load_dotenv(backend_env, override=False)  # Don't override existing env vars
        print(f"✅ Loaded backend .env from {backend_env}")
    
    # Load root .env second (overrides/updates)
    root_env = project_root / ".env"
    if root_env.exists():
        load_dotenv(root_env, override=True)  # Override with root .env values
        print(f"✅ Loaded root .env from {root_env} (may override backend values)")
    
    # Verify credentials are set
    print(f"NCBI_USER_EMAIL: {os.getenv('NCBI_USER_EMAIL', 'NOT SET')}")
    api_key = os.getenv('NCBI_USER_API_KEY') or os.getenv('NCBI_API_KEY')
    print(f"NCBI_API_KEY: {api_key[:20]}..." if api_key else "NCBI_API_KEY: NOT SET")
    print(f"GEMINI_API_KEY: {os.getenv('GEMINI_API_KEY', 'NOT SET')[:20]}..." if os.getenv('GEMINI_API_KEY') else "GEMINI_API_KEY: NOT SET")
    print(f"GOOGLE_API_KEY: {os.getenv('GOOGLE_API_KEY', 'NOT SET')[:20]}..." if os.getenv('GOOGLE_API_KEY') else "GOOGLE_API_KEY: NOT SET")
except ImportError:
    print("⚠️ python-dotenv not available, using environment variables only")

# Add parent directories to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root / "oncology-coPilot" / "oncology-backend-minimal"))

try:
    from api.services.research_intelligence.orchestrator import ResearchIntelligenceOrchestrator
except ImportError as e:
    print(f"❌ Failed to import ResearchIntelligenceOrchestrator: {e}")
    sys.exit(1)


async def run_ri_on_query(query_data: Dict[str, Any], orchestrator, max_retries: int = 3) -> Dict[str, Any]:
    """Run Research Intelligence on a single query with retry logic for rate limits."""
    query_id = query_data.get('query_id', 'unknown')
    question = query_data.get('question', '')
    context = query_data.get('context', {})
    
    print(f"  🔬 Running RI on {query_id}: {question[:50]}...")
    
    start_time = datetime.now()
    
    for attempt in range(max_retries):
        try:
            result = await orchestrator.research_question(
                question=question,
                context=context
            )
            
            elapsed = (datetime.now() - start_time).total_seconds()
            
            # Extract predictions
            synthesized = result.get('synthesized_findings', {})
            moat_analysis = result.get('moat_analysis', {})
            
            predictions = {
                "query_id": query_id,
                "question": question,
                "elapsed_seconds": elapsed,
                "mechanisms": synthesized.get('mechanisms', []),
                "pathways": moat_analysis.get('pathways', []),
                "evidence_tier": synthesized.get('evidence_tier', None),
                "badges": synthesized.get('badges', []),
                "overall_confidence": synthesized.get('overall_confidence', None),
                "paper_count": result.get('portal_results', {}).get('pubmed', {}).get('article_count', 0),
                "has_sub_question_answers": bool(result.get('sub_question_answers')),
                "has_article_summaries": bool(synthesized.get('article_summaries')),
                "has_moat_analysis": bool(moat_analysis),
                "run_id": result.get('provenance', {}).get('run_id', None)
            }
            
            print(f"    ✅ Completed in {elapsed:.1f}s - {len(predictions['mechanisms'])} mechanisms, {len(predictions['pathways'])} pathways")
            
            return predictions
            
        except Exception as e:
            error_str = str(e)
            elapsed = (datetime.now() - start_time).total_seconds()
            
            # Check if it's a rate limit error
            is_rate_limit = (
                "429" in error_str or
                "rate limit" in error_str.lower() or
                "too many requests" in error_str.lower() or
                "quota" in error_str.lower() or
                "permission denied" in error_str.lower()
            )
            
            if is_rate_limit and attempt < max_retries - 1:
                # Exponential backoff: 2^attempt seconds
                wait_time = 2 ** attempt
                print(f"    ⚠️  Rate limit hit (attempt {attempt + 1}/{max_retries}), waiting {wait_time}s...")
                await asyncio.sleep(wait_time)
                continue
            elif attempt < max_retries - 1:
                # Not a rate limit error, but retry anyway with short delay
                print(f"    ⚠️  Error (attempt {attempt + 1}/{max_retries}): {e}")
                await asyncio.sleep(1)
                continue
            else:
                # Max retries reached
                print(f"    ❌ Failed after {max_retries} attempts: {e}")
                import traceback
                traceback.print_exc()
                
                return {
                    "query_id": query_id,
                    "question": question,
                    "elapsed_seconds": elapsed,
                    "error": str(e),
                    "error_type": "rate_limit" if is_rate_limit else "other",
                    "attempts": attempt + 1,
                    "mechanisms": [],
                    "pathways": [],
                    "evidence_tier": None,
                    "badges": [],
                    "overall_confidence": None
                }
    
    # Should never reach here, but just in case
    return {
        "query_id": query_id,
        "question": question,
        "elapsed_seconds": (datetime.now() - start_time).total_seconds(),
        "error": "Max retries exceeded",
        "mechanisms": [],
        "pathways": []
    }


async def run_validation_suite():
    """Run Research Intelligence on all validation queries."""
    print("=" * 80)
    print("SPRINT 6: RUN RESEARCH INTELLIGENCE ON 100 QUERIES")
    print("=" * 80)
    
    # Load validation queries
    queries_file = Path(__file__).parent.parent / "sprint4_results" / "validation_queries_100.json"
    
    if not queries_file.exists():
        print(f"❌ Validation queries file not found: {queries_file}")
        return
    
    with open(queries_file, 'r') as f:
        queries_data = json.load(f)
    
    queries = queries_data.get('queries', [])
    print(f"\n📊 Loaded {len(queries)} validation queries")
    
    # Initialize orchestrator
    print("\n🔧 Initializing Research Intelligence Orchestrator...")
    try:
        orchestrator = ResearchIntelligenceOrchestrator()
        if not orchestrator.is_available():
            print("⚠️ Orchestrator not fully available, but proceeding...")
        print("✅ Orchestrator initialized")
    except Exception as e:
        print(f"❌ Failed to initialize orchestrator: {e}")
        return
    
    # Process queries
    print(f"\n🚀 Running Research Intelligence on {len(queries)} queries...")
    print("   (This will take ~10-15 minutes)")
    
    results = []
    
    for i, query in enumerate(queries, 1):
        result = await run_ri_on_query(query, orchestrator, max_retries=MAX_RETRIES)
        results.append(result)
        
        if i % 10 == 0:
            print(f"  ✅ Processed {i}/{len(queries)} queries")
        
        # Rate limiting: delay between queries to avoid overwhelming APIs
        if i < len(queries):  # Don't delay after the last query
            await asyncio.sleep(QUERY_DELAY_SECONDS)
    
    # Save output
    output_dir = Path(__file__).parent.parent / "sprint6_results"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    output_file = output_dir / "validation_results.json"
    
    output = {
        "timestamp": datetime.now().isoformat(),
        "total_queries": len(results),
        "successful": len([r for r in results if 'error' not in r]),
        "failed": len([r for r in results if 'error' in r]),
        "total_mechanisms": sum(len(r.get('mechanisms', [])) for r in results),
        "total_pathways": sum(len(r.get('pathways', [])) for r in results),
        "results": results
    }
    
    with open(output_file, 'w') as f:
        json.dump(output, f, indent=2)
    
    print("\n" + "=" * 80)
    print("✅ VALIDATION RESULTS GENERATED")
    print("=" * 80)
    print(f"Total queries: {len(results)}")
    print(f"Successful: {output['successful']}")
    print(f"Failed: {output['failed']}")
    print(f"Total mechanisms extracted: {output['total_mechanisms']}")
    print(f"Total pathways identified: {output['total_pathways']}")
    print(f"Output file: {output_file}")
    
    return output


if __name__ == "__main__":
    asyncio.run(run_validation_suite())

