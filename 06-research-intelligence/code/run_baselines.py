#!/usr/bin/env python3
"""
Sprint 8: Run Baselines

Run PubMed abstract-only search (no LLM) on 100 queries
Run ChatGPT-4 direct query on 100 queries  
Run keyword matching baseline on 100 queries
Compute same metrics for baselines
Output: baseline_results.json with baseline metrics
"""

import json
import sys
import asyncio
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime

# Add parent directories to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root / "oncology-coPilot" / "oncology-backend-minimal"))

try:
    from api.services.research_intelligence.portals.pubmed_enhanced import EnhancedPubMedPortal
    from api.services.multi_llm_service import MultiLLMService
except ImportError as e:
    print(f"⚠️ Import error: {e}")
    EnhancedPubMedPortal = None
    MultiLLMService = None


async def run_pubmed_abstract_only(query_data: Dict[str, Any], portal) -> Dict[str, Any]:
    """Baseline 1: PubMed abstract-only (no LLM synthesis)."""
    query_id = query_data.get('query_id', 'unknown')
    question = query_data.get('question', '')
    source_data = query_data.get('source_data', {})
    
    # Convert to PubMed query
    from generate_pubmed_ground_truth import convert_question_to_pubmed_query
    search_query = convert_question_to_pubmed_query(question, source_data)
    
    try:
        # Search PubMed (no LLM, just get abstracts)
        results = await portal.search_with_analysis(
            query=search_query,
            max_results=20,
            analyze_keywords=True,
            include_trends=False
        )
        
        articles = results.get('articles', [])
        
        # Extract keywords from abstracts (simple extraction, no LLM)
        all_keywords = []
        for article in articles[:10]:
            abstract = article.get('abstract', article.get('AB', ''))
            if abstract:
                words = abstract.lower().split()
                meaningful_words = [w.strip('.,;:!?()[]{}') for w in words if len(w) > 4 and w.isalpha()]
                all_keywords.extend(meaningful_words)
        
        from collections import Counter
        keyword_counts = Counter(all_keywords)
        top_keywords = [word for word, count in keyword_counts.most_common(20)]
        
        return {
            "query_id": query_id,
            "baseline": "pubmed_abstract_only",
            "mechanisms": top_keywords[:10],  # Top keywords as "mechanisms"
            "paper_count": len(articles)
        }
    except Exception as e:
        return {
            "query_id": query_id,
            "baseline": "pubmed_abstract_only",
            "error": str(e),
            "mechanisms": [],
            "paper_count": 0
        }


async def run_chatgpt_direct(query_data: Dict[str, Any], llm_service) -> Dict[str, Any]:
    """Baseline 2: ChatGPT-4 direct query (no multi-portal)."""
    query_id = query_data.get('query_id', 'unknown')
    question = query_data.get('question', '')
    
    try:
        prompt = f"""Extract the key mechanisms from this research question. Return only a JSON array of mechanism names.

Question: {question}

Return format: ["mechanism1", "mechanism2", ...]"""
        
        response = await llm_service.generate_response(
            prompt=prompt,
            model="gpt-4",
            temperature=0.3
        )
        
        # Parse response (try to extract JSON array)
        import re
        json_match = re.search(r'\[.*?\]', response, re.DOTALL)
        if json_match:
            mechanisms = json.loads(json_match.group())
        else:
            # Fallback: extract quoted strings
            mechanisms = re.findall(r'"([^"]+)"', response)
        
        return {
            "query_id": query_id,
            "baseline": "chatgpt_direct",
            "mechanisms": mechanisms[:10],
            "raw_response": response[:200]
        }
    except Exception as e:
        return {
            "query_id": query_id,
            "baseline": "chatgpt_direct",
            "error": str(e),
            "mechanisms": []
        }


def run_keyword_matching(query_data: Dict[str, Any], ground_truth: Dict[str, Any]) -> Dict[str, Any]:
    """Baseline 3: Keyword matching (simple string matching)."""
    query_id = query_data.get('query_id', 'unknown')
    question = query_data.get('question', '').lower()
    
    # Simple keyword extraction from question
    common_mechanisms = [
        'apoptosis', 'proliferation', 'angiogenesis', 'metabolism', 'resistance',
        'inhibition', 'activation', 'pathway', 'signaling', 'dna repair',
        'cell cycle', 'inflammation', 'oxidative stress', 'autophagy'
    ]
    
    found_mechanisms = [m for m in common_mechanisms if m in question]
    
    return {
        "query_id": query_id,
        "baseline": "keyword_matching",
        "mechanisms": found_mechanisms
    }


async def run_baselines():
    """Run all baseline methods."""
    print("=" * 80)
    print("SPRINT 8: RUN BASELINES")
    print("=" * 80)
    
    # Load validation queries
    queries_file = Path(__file__).parent.parent / "sprint4_results" / "validation_queries_100.json"
    if not queries_file.exists():
        print(f"❌ Validation queries not found: {queries_file}")
        return
    
    with open(queries_file, 'r') as f:
        queries_data = json.load(f)
    
    queries = queries_data.get('queries', [])
    print(f"\n📊 Loaded {len(queries)} queries")
    
    # Load ground truth for keyword matching
    gt_file = Path(__file__).parent.parent / "sprint5_results" / "pubmed_ground_truth.json"
    gt_lookup = {}
    if gt_file.exists():
        with open(gt_file, 'r') as f:
            gt_data = json.load(f)
            gt_lookup = {gt['query_id']: gt for gt in gt_data.get('ground_truth', [])}
    
    # Initialize services
    portal = None
    if EnhancedPubMedPortal:
        try:
            import os
            from dotenv import load_dotenv
            load_dotenv(project_root / ".env")
            email = os.getenv('NCBI_USER_EMAIL', 'fahad@crispro.ai')
            api_key = os.getenv('NCBI_USER_API_KEY') or os.getenv('NCBI_API_KEY')
            portal = EnhancedPubMedPortal(email=email, api_key=api_key)
            print("✅ PubMed portal initialized")
        except Exception as e:
            print(f"⚠️ PubMed portal not available: {e}")
    
    llm_service = None
    if MultiLLMService:
        try:
            llm_service = MultiLLMService()
            print("✅ LLM service initialized")
        except Exception as e:
            print(f"⚠️ LLM service not available: {e}")
    
    # Run baselines
    print(f"\n🔬 Running baselines on {len(queries)} queries...")
    
    baseline_results = {
        "pubmed_abstract_only": [],
        "chatgpt_direct": [],
        "keyword_matching": []
    }
    
    for i, query in enumerate(queries, 1):
        query_id = query.get('query_id', f'query_{i}')
        
        # Baseline 1: PubMed abstract-only
        if portal:
            result1 = await run_pubmed_abstract_only(query, portal)
            baseline_results["pubmed_abstract_only"].append(result1)
            await asyncio.sleep(1)  # Rate limiting
        
        # Baseline 2: ChatGPT direct
        if llm_service:
            result2 = await run_chatgpt_direct(query, llm_service)
            baseline_results["chatgpt_direct"].append(result2)
            await asyncio.sleep(1)
        
        # Baseline 3: Keyword matching
        gt = gt_lookup.get(query_id, {})
        result3 = run_keyword_matching(query, gt)
        baseline_results["keyword_matching"].append(result3)
        
        if i % 10 == 0:
            print(f"  ✅ Processed {i}/{len(queries)} queries")
    
    # Save output
    output_dir = Path(__file__).parent.parent / "sprint8_results"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    output_file = output_dir / "baseline_results.json"
    
    output = {
        "timestamp": datetime.now().isoformat(),
        "total_queries": len(queries),
        "baseline_results": baseline_results
    }
    
    with open(output_file, 'w') as f:
        json.dump(output, f, indent=2)
    
    print("\n" + "=" * 80)
    print("✅ BASELINE RESULTS GENERATED")
    print("=" * 80)
    print(f"Output file: {output_file}")
    
    return output


if __name__ == "__main__":
    asyncio.run(run_baselines())


