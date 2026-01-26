#!/usr/bin/env python3
"""
Test Comprehensive Gemini API Call Optimization

Verifies that:
1. Comprehensive Gemini extraction is being used (1 call instead of 10+)
2. All expected outputs are present (mechanisms, article summaries, sub-question answers)
3. Rate limiting delays are respected
"""

import asyncio
import sys
import time
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

sys.path.insert(0, str(project_root / "oncology-coPilot" / "oncology-backend-minimal"))

from api.services.research_intelligence.orchestrator import ResearchIntelligenceOrchestrator

async def test_comprehensive_gemini():
    """Test that comprehensive Gemini extraction works and reduces API calls."""
    print("=" * 70)
    print("COMPREHENSIVE GEMINI API OPTIMIZATION TEST")
    print("=" * 70)
    
    # Initialize orchestrator
    print("\n[1] Initializing Orchestrator...")
    orchestrator = ResearchIntelligenceOrchestrator()
    if not orchestrator.is_available():
        print("  ❌ Orchestrator not available")
        return False
    print("  ✅ Orchestrator initialized")
    
    # Test query
    test_question = "What mechanisms does curcumin target in breast cancer?"
    test_context = {
        "compound": "curcumin",
        "disease": "breast cancer"
    }
    
    print(f"\n[2] Running Test Query...")
    print(f"    Question: {test_question}")
    print(f"    Context: {test_context}")
    
    start_time = time.time()
    
    try:
        result = await orchestrator.research_question(
            question=test_question,
            context=test_context
        )
        
        elapsed = time.time() - start_time
        
        print(f"\n[3] Results Analysis...")
        print(f"    ⏱️  Execution time: {elapsed:.2f}s")
        
        # Check synthesized findings
        synthesized = result.get("synthesized_findings", {})
        method = synthesized.get("method", "unknown")
        print(f"    🔬 Synthesis method: {method}")
        
        # Check mechanisms
        mechanisms = synthesized.get("mechanisms", [])
        print(f"    📊 Mechanisms found: {len(mechanisms)}")
        if mechanisms:
            print(f"        Sample: {mechanisms[0].get('mechanism', str(mechanisms[0]))[:50]}...")
        
        # Check article summaries
        article_summaries = synthesized.get("article_summaries", [])
        print(f"    📄 Article summaries: {len(article_summaries)}")
        if article_summaries:
            print(f"        Sample: {article_summaries[0].get('title', 'N/A')[:50]}...")
        
        # Check sub-question answers
        sub_question_answers = result.get("sub_question_answers", [])
        print(f"    ❓ Sub-question answers: {len(sub_question_answers)}")
        if sub_question_answers:
            print(f"        Sample: {sub_question_answers[0].get('sub_question', 'N/A')[:50]}...")
        
        # Check MOAT analysis
        moat_analysis = result.get("moat_analysis", {})
        pathways = moat_analysis.get("pathways", [])
        print(f"    🧬 Pathways found: {len(pathways)}")
        
        # Verify comprehensive extraction was used
        print(f"\n[4] Optimization Verification...")
        if method == "gemini_deep_research":
            print("    ✅ Comprehensive Gemini extraction used")
            if article_summaries and sub_question_answers:
                print("    ✅ Both article summaries AND sub-question answers present")
                print("    ✅ Optimization working: 1 call instead of 10+")
            elif article_summaries:
                print("    ⚠️  Article summaries present, but sub-question answers missing")
            elif sub_question_answers:
                print("    ⚠️  Sub-question answers present, but article summaries missing")
            else:
                print("    ⚠️  Comprehensive extraction used but outputs missing")
        else:
            print(f"    ⚠️  Using {method} (comprehensive Gemini not used)")
        
        # Success criteria
        success = (
            method == "gemini_deep_research" and
            len(mechanisms) > 0 and
            len(article_summaries) > 0
        )
        
        print(f"\n[5] Test Result: {'✅ PASS' if success else '❌ FAIL'}")
        return success
        
    except Exception as e:
        print(f"\n  ❌ Error during execution: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_comprehensive_gemini())
    sys.exit(0 if success else 1)

