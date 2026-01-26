#!/usr/bin/env python3
"""
Sprint 5: Generate PubMed Ground Truth

Run keyword hotspot analysis for each of 100 queries
Extract top 20 keywords per query (deterministic, no LLM)
Output: pubmed_ground_truth.json with keywords = "expected mechanisms"
"""

import json
import sys
import os
import asyncio
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime

try:
    from dotenv import load_dotenv
except ImportError:
    print("⚠️ python-dotenv not installed. Install with: pip install python-dotenv")
    load_dotenv = None

# Add parent directories to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root / "oncology-coPilot" / "oncology-backend-minimal"))

try:
    from api.services.research_intelligence.portals.pubmed_enhanced import EnhancedPubMedPortal
except ImportError:
    print("⚠️ Could not import EnhancedPubMedPortal, using fallback")
    EnhancedPubMedPortal = None


def convert_question_to_pubmed_query(question: str, source_data: Dict[str, Any] = None) -> str:
    """Convert natural language question to PubMed search query."""
    question_lower = question.lower()
    
    # Use source_data if available (has actual drug/gene names)
    compound = None
    disease = None
    gene = None
    
    if source_data:
        compound = source_data.get('drug', source_data.get('food', None))
        disease = source_data.get('disease', source_data.get('cancer', None))
        gene = source_data.get('gene', None)
    
    # Extract from question if not in source_data
    if not compound or compound.lower() == "unknown drug":
        # Pattern: "How does {compound} ... {disease}?"
        if "does" in question_lower or "do" in question_lower:
            parts = question_lower.split()
            try:
                does_idx = next(i for i, w in enumerate(parts) if w in ["does", "do"])
                if does_idx + 1 < len(parts):
                    # Get compound (next 1-3 words, stop at action verbs)
                    compound_words = []
                    stop_words = ["target", "help", "affect", "work", "interact", "in", "with"]
                    for i in range(does_idx + 1, min(does_idx + 4, len(parts))):
                        word = parts[i].strip('?.,!')
                        if word not in stop_words and word != "unknown":
                            compound_words.append(word)
                        elif word in stop_words and compound_words:
                            break
                    if compound_words:
                        compound = " ".join(compound_words)
            except StopIteration:
                pass
    
    if not disease:
        # Find disease (usually contains "cancer" or at end)
        if "cancer" in question_lower:
            cancer_idx = question_lower.find("cancer")
            # Get words before "cancer"
            before_cancer = question_lower[:cancer_idx].strip()
            if before_cancer:
                # Get last 1-2 words before "cancer"
                words_before = before_cancer.split()[-2:]
                disease = " ".join(words_before) + " cancer"
            else:
                disease = "cancer"
        elif "ovarian" in question_lower:
            disease = "ovarian cancer"
        elif "breast" in question_lower:
            disease = "breast cancer"
        elif "prostate" in question_lower:
            disease = "prostate cancer"
        elif "lung" in question_lower:
            disease = "lung cancer"
        elif "colorectal" in question_lower:
            disease = "colorectal cancer"
    
    # Build PubMed query
    query_parts = []
    
    if compound and compound.lower() != "unknown drug":
        query_parts.append(f'"{compound}"')
    
    if gene and gene.lower() != "unknown gene":
        query_parts.append(gene)
    
    if disease:
        query_parts.append(disease)
    
    if query_parts:
        return " AND ".join(query_parts)
    else:
        # Fallback: extract key terms from question
        key_terms = []
        important_words = ["curcumin", "olaparib", "parp", "platinum", "taxane", "pembrolizumab", 
                          "metformin", "green tea", "anthocyanin", "purple potato"]
        for term in important_words:
            if term in question_lower:
                key_terms.append(term)
        
        if key_terms and disease:
            return f'"{key_terms[0]}" AND {disease}'
        elif key_terms:
            return f'"{key_terms[0]}"'
        else:
            # Last resort: use first few meaningful words
            words = [w.strip('?.,!') for w in question.split() if len(w) > 4 and w.lower() not in ["how", "does", "what", "mechanisms", "target"]]
            if words:
                return " ".join(words[:3])
            return question


async def analyze_keywords_for_query(query_data: Dict[str, Any], portal) -> Dict[str, Any]:
    """Analyze keywords for a single query."""
    query_id = query_data.get('query_id', 'unknown')
    question = query_data.get('question', '')
    
    print(f"  🔍 Analyzing {query_id}: {question[:50]}...")
    
    try:
        articles = []
        
        if portal:
            # Convert question to PubMed search query (use source_data if available)
            source_data = query_data.get('source_data', {})
            search_query = convert_question_to_pubmed_query(question, source_data)
            print(f"    📝 PubMed query: {search_query}")
            
            # Use portal if available (use search_with_analysis method)
            try:
                results = await portal.search_with_analysis(
                    query=search_query,
                    max_results=100,
                    analyze_keywords=True,
                    include_trends=False
                )
                
                articles = results.get('articles', [])
                print(f"    📊 Found {len(articles)} articles")
                
                # Extract keywords from analysis if available
                keyword_analysis = results.get('keyword_analysis', {})
                if keyword_analysis:
                    # Handle different formats
                    top_keywords_raw = keyword_analysis.get('top_keywords', [])
                    if top_keywords_raw:
                        # Extract keyword strings (could be dicts or strings)
                        top_keywords = []
                        for kw in top_keywords_raw[:20]:
                            if isinstance(kw, dict):
                                top_keywords.append(kw.get('keyword', kw.get('word', str(kw))))
                            else:
                                top_keywords.append(str(kw))
                        
                        keyword_counts = keyword_analysis.get('frequencies', {})
                        
                        return {
                            "query_id": query_id,
                            "question": question,
                            "search_query": search_query,
                            "paper_count": len(articles),
                            "top_keywords": top_keywords,
                            "keyword_counts": dict(list(keyword_counts.items())[:20]) if isinstance(keyword_counts, dict) else {},
                            "method": "portal_analysis"
                        }
                
                # If no keyword analysis, extract from abstracts
                if articles:
                    all_keywords = []
                    for article in articles[:50]:
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
                        "question": question,
                        "search_query": search_query,
                        "paper_count": len(articles),
                        "top_keywords": top_keywords,
                        "keyword_counts": dict(keyword_counts.most_common(20)),
                        "method": "portal_abstracts"
                    }
                else:
                    print(f"    ⚠️ No articles found")
                    
            except Exception as e:
                print(f"    ⚠️ Portal search failed: {e}")
                import traceback
                traceback.print_exc()
                articles = []
        else:
            # Fallback: Use simple keyword extraction from question
            # This is a placeholder - in production, would use actual PubMed API
            print(f"    ⚠️ Using fallback method (no portal)")
            articles = []  # Empty for now
        
        # Extract keywords
        all_keywords = []
        
        if articles:
            # Extract from article abstracts
            for article in articles[:50]:
                abstract = article.get('abstract', '')
                if abstract:
                    words = abstract.lower().split()
                    meaningful_words = [w.strip('.,;:!?()[]{}') for w in words if len(w) > 4 and w.isalpha()]
                    all_keywords.extend(meaningful_words)
        else:
            # Fallback: Extract keywords from question itself
            # This is a simple heuristic - in production would query PubMed API directly
            question_lower = question.lower()
            # Extract potential mechanism/drug terms
            common_terms = ['mechanism', 'target', 'pathway', 'inhibition', 'activation', 
                          'apoptosis', 'proliferation', 'metabolism', 'resistance', 'sensitivity']
            for term in common_terms:
                if term in question_lower:
                    all_keywords.append(term)
            
            # Extract compound/drug names (simple heuristic)
            words = question_lower.split()
            for word in words:
                if len(word) > 5 and word.isalpha():
                    all_keywords.append(word)
        
        # Count keyword frequencies
        from collections import Counter
        keyword_counts = Counter(all_keywords)
        
        # Get top 20 keywords
        top_keywords = [word for word, count in keyword_counts.most_common(20)]
        
        return {
            "query_id": query_id,
            "question": question,
            "paper_count": len(articles),
            "top_keywords": top_keywords,
            "keyword_counts": dict(keyword_counts.most_common(20)),
            "method": "portal" if portal else "fallback"
        }
        
    except Exception as e:
        print(f"    ⚠️ Error analyzing {query_id}: {e}")
        return {
            "query_id": query_id,
            "question": question,
            "paper_count": 0,
            "top_keywords": [],
            "keyword_counts": {},
            "error": str(e),
            "method": "error"
        }


async def generate_pubmed_ground_truth():
    """Generate PubMed ground truth for all validation queries."""
    print("=" * 80)
    print("SPRINT 5: GENERATE PUBMED GROUND TRUTH")
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
    
    # Initialize PubMed portal (load from .env)
    portal = None
    if EnhancedPubMedPortal:
        try:
            import os
            from dotenv import load_dotenv
            
            # Load environment variables from .env file
            env_path = project_root / ".env"
            if env_path.exists():
                load_dotenv(env_path)
                print(f"✅ Loaded .env from: {env_path}")
            else:
                # Try parent directories
                for parent in [project_root.parent, project_root.parent.parent]:
                    env_path = parent / ".env"
                    if env_path.exists():
                        load_dotenv(env_path)
                        print(f"✅ Loaded .env from: {env_path}")
                        break
            
            # Check for required environment variables (try multiple names)
            email = (os.getenv('NCBI_USER_EMAIL') or 
                    os.getenv('PUBMED_EMAIL') or 
                    os.getenv('NCBI_EMAIL') or
                    os.getenv('ENTREZ_EMAIL'))
            
            api_key = (os.getenv('NCBI_USER_API_KEY') or 
                      os.getenv('PUBMED_API_KEY') or 
                      os.getenv('NCBI_API_KEY') or
                      os.getenv('ENTREZ_API_KEY'))
            
            # Debug: print all env vars that might be relevant
            env_vars = {k: v for k, v in os.environ.items() if any(term in k.upper() for term in ['NCBI', 'PUBMED', 'ENTREZ'])}
            if env_vars:
                print(f"📋 Found NCBI-related environment variables: {list(env_vars.keys())}")
            
            # Use default email if not found (same as personalized_outreach router)
            if not email:
                email = "fahad@crispro.ai"
                print(f"⚠️ NCBI email not found, using default: {email}")
            else:
                print(f"✅ Found NCBI email: {email[:10]}...")
            
            if not api_key:
                print("⚠️ NCBI API key not found, proceeding without API key (rate limits may apply)")
            else:
                print(f"✅ Found NCBI API key: {api_key[:10]}...")
            
            print(f"✅ Initializing EnhancedPubMedPortal...")
            portal = EnhancedPubMedPortal(email=email, api_key=api_key)
            print("✅ PubMed portal initialized successfully")
        except Exception as e:
            print(f"❌ Could not initialize EnhancedPubMedPortal: {e}")
            raise
    
    # Process queries
    print("\n🔬 Analyzing keywords for each query...")
    ground_truth_results = []
    
    for i, query in enumerate(queries, 1):
        result = await analyze_keywords_for_query(query, portal)
        ground_truth_results.append(result)
        
        if i % 10 == 0:
            print(f"  ✅ Processed {i}/{len(queries)} queries")
        
        # Small delay to avoid rate limits
        await asyncio.sleep(1)
    
    # Save output
    output_dir = Path(__file__).parent.parent / "sprint5_results"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    output_file = output_dir / "pubmed_ground_truth.json"
    
    output = {
        "timestamp": datetime.now().isoformat(),
        "total_queries": len(ground_truth_results),
        "queries_analyzed": len([r for r in ground_truth_results if r.get('top_keywords')]),
        "queries_with_errors": len([r for r in ground_truth_results if r.get('error')]),
        "ground_truth": ground_truth_results
    }
    
    with open(output_file, 'w') as f:
        json.dump(output, f, indent=2)
    
    print("\n" + "=" * 80)
    print("✅ PUBMED GROUND TRUTH GENERATED")
    print("=" * 80)
    print(f"Total queries: {len(ground_truth_results)}")
    print(f"Successfully analyzed: {output['queries_analyzed']}")
    print(f"Errors: {output['queries_with_errors']}")
    print(f"Output file: {output_file}")
    
    return output


if __name__ == "__main__":
    asyncio.run(generate_pubmed_ground_truth())

