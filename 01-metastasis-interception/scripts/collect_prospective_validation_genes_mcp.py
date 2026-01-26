#!/usr/bin/env python3
"""
Collect Prospective Validation Genes using BioMed-MCP

Purpose:
- Use BioMed-MCP server to query ClinicalTrials.gov and PubMed
- Extract gene targets from trials and literature
- Filter to genes NOT in our 38-gene set
- Rank by priority (FDA approval > Phase III > literature)

Data Sources:
1. BioMed-MCP Clinical Trials Agent
2. BioMed-MCP PubMed Agent
3. Manual curation (if needed)

Outputs:
- ../data/prospective_validation_genes_mcp.csv
- ../data/prospective_validation_genes_curated_mcp.csv

Author: Zo (Platform AI)
Date: January 19, 2026
Version: 1.0.0
"""

import json
import os
import re
import asyncio
import pandas as pd
from pathlib import Path
from typing import Dict, List, Set, Optional
from datetime import datetime
from collections import defaultdict
import sys

# BioMed-MCP path in worktree
biomed_mcp_path = Path("/Users/fahadkiani/.cursor/worktrees/crispr-assistant-main/ebi/oncology-coPilot/oncology-backend-minimal/scripts/data_acquisition/mcp_servers/BioMed-MCP")
biomed_venv_python = biomed_mcp_path / ".venv" / "bin" / "python"

# Try to import MCP libraries
MCP_AVAILABLE = False
AGENTS_AVAILABLE = False
Client = None
StdioTransport = None

# First try: Use venv Python if available
if biomed_venv_python.exists() and biomed_mcp_path.exists():
    # Add to path for agent imports
    sys.path.insert(0, str(biomed_mcp_path))
    
    try:
        # Try importing from venv
        import subprocess
        result = subprocess.run(
            [str(biomed_venv_python), "-c", "import fastmcp; print('OK')"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            # fastmcp is available in venv - we'll use venv Python
            MCP_AVAILABLE = True
            USE_VENV_PYTHON = True
        else:
            USE_VENV_PYTHON = False
    except:
        USE_VENV_PYTHON = False
else:
    USE_VENV_PYTHON = False
    
    # Try importing agents directly
    try:
        sys.path.insert(0, str(biomed_mcp_path))
        from biomed_agents import PubMedAgent, ClinicalTrialsAgent
        AGENTS_AVAILABLE = True
    except ImportError:
        pass

# Second try: Import from current environment
if not MCP_AVAILABLE:
    try:
        from fastmcp.client import Client
        from fastmcp.client.transports import StdioTransport
        from dotenv import load_dotenv
        if biomed_mcp_path.exists():
            load_dotenv(biomed_mcp_path / ".env")
        MCP_AVAILABLE = True
        USE_VENV_PYTHON = False
    except ImportError:
        pass

if not MCP_AVAILABLE and not AGENTS_AVAILABLE:
    print("⚠️  Could not import MCP libraries or agents")
    print("   Falling back to manual curation approach")

# Configuration
OUTPUT_DIR = Path("publication/data")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Our 38 genes (to exclude)
OUR_38_GENES = {
    'ANGPT2', 'AXL', 'BCL2', 'BIRC5', 'BRAF', 'CCL2', 'CCR7', 'CLDN4', 'CTSD',
    'CXCL12', 'CXCR4', 'HIF1A', 'ICAM1', 'IL6', 'KRAS', 'MAP2K1', 'MCL1', 'MET',
    'MMP14', 'MMP2', 'MMP9', 'NOTCH1', 'NRAS', 'PLOD2', 'POSTN', 'PTGS2', 'PTK2',
    'S100A4', 'SELE', 'SNAI1', 'SRC', 'TGFB1', 'TGFBR1', 'TWIST1', 'VCAM1',
    'VEGFA', 'VEGFR2', 'ZEB1'
}

# Common gene name patterns (improved)
GENE_PATTERN = re.compile(r'\b([A-Z][A-Z0-9]{1,9})\b')

# Extensive exclusion list for common words
EXCLUDED_WORDS = {
    # Common English words (2-5 letters)
    'FOR', 'OF', 'THE', 'AND', 'TO', 'IN', 'ON', 'AT', 'IS', 'IT', 'AS', 'BE',
    'WITH', 'THIS', 'FROM', 'THAT', 'HAVE', 'HAS', 'HAD', 'WAS', 'WERE', 'ARE',
    'NOT', 'BUT', 'CAN', 'MAY', 'ALL', 'ONE', 'TWO', 'THREE', 'FOUR', 'FIVE',
    'SIX', 'SEVEN', 'EIGHT', 'NINE', 'TEN', 'FIRST', 'SECOND', 'THIRD',
    'AN', 'BY', 'UP', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII', 'IX', 'X',
    'NO', 'SO', 'DO', 'GO', 'WE', 'US', 'OR', 'IF', 'MY', 'ME', 'HE', 'SHE',
    'HIS', 'HER', 'ITS', 'OUR', 'YOUR', 'THEIR', 'THEM', 'THESE', 'THOSE',
    'NEW', 'OLD', 'BIG', 'SMALL', 'LONG', 'SHORT', 'HIGH', 'LOW', 'GOOD', 'BAD',
    'MORE', 'LESS', 'MOST', 'LEAST', 'MANY', 'FEW', 'SOME', 'ANY', 'EACH',
    'EVERY', 'BOTH', 'EITHER', 'NEITHER', 'OTHER', 'ANOTHER', 'SUCH', 'SAME',
    'VERY', 'TOO', 'QUITE', 'RATHER', 'MUCH', 'WELL', 'ALSO', 'ONLY', 'JUST',
    'STILL', 'YET', 'EVEN', 'ONCE', 'TWICE', 'AGAIN', 'THEN', 'NOW', 'HERE',
    'THERE', 'WHERE', 'WHEN', 'WHAT', 'WHICH', 'WHO', 'WHOM', 'WHOSE', 'WHY',
    'HOW', 'WHILE', 'UNTIL', 'SINCE', 'AFTER', 'BEFORE', 'DURING', 'AMONG',
    'BETWEEN', 'ABOUT', 'ABOVE', 'BELOW', 'UNDER', 'OVER', 'ACROSS', 'ALONG',
    'AROUND', 'THROUGH', 'TOWARD', 'TOWARDS', 'AGAINST', 'WITHIN', 'WITHOUT',
    'BESIDE', 'BESIDES', 'BEYOND', 'NEAR', 'NEARBY', 'FAR', 'AWAY', 'BACK',
    'DOWN', 'OUT', 'OFF', 'ONTO', 'INTO', 'UPON', 'AMID', 'AMIDST',
    # Medical/Clinical terms
    'FDA', 'NCT', 'PHASE', 'TRIAL', 'STUDY', 'PATIENT', 'CANCER', 'TUMOR',
    'METASTASIS', 'METASTATIC', 'APPROVED', 'ENROLLMENT', 'RESULTS',
    'EFFICACY', 'SAFETY', 'DOSE', 'MG', 'ML', 'ORAL', 'PO', 'USA',
    'EU', 'UK', 'DNA', 'RNA', 'MRNA', 'CDNA', 'PCR', 'RT', 'CT',
    'MRI', 'PET', 'SUV', 'OS', 'PFS', 'ORR', 'DCR', 'AE', 'SAE', 'DLT',
    'ADVERSE', 'EVENT', 'EFFECT', 'RESPONSE', 'TREATMENT', 'THERAPY',
    'CLINICAL', 'RESEARCH', 'PRACTICE', 'ASSESS', 'IDENTIFIED', 'DIVERSE',
    'EXECUTIVE', 'FOCUSING', 'REDUCING', 'TRIALS', 'DRUG', 'DRUGS',
    'GENE', 'GENES', 'GENETIC', 'GENOMIC', 'MUTATION', 'MUTATIONS',
    'VARIANT', 'VARIANTS', 'BIOMARKER', 'BIOMARKERS', 'PROTEIN', 'PROTEINS',
    'CELL', 'CELLS', 'TISSUE', 'TISSUES', 'ORGAN', 'ORGANS', 'BLOOD',
    'SAMPLE', 'SAMPLES', 'COHORT', 'COHORTS', 'GROUP', 'GROUPS',
    'RISK', 'RISKS', 'RATE', 'RATES', 'RATIO', 'RATIOS', 'SCORE', 'SCORES',
    'SIZE', 'SIZES', 'COUNT', 'COUNTS', 'NUMBER', 'NUMBERS', 'TOTAL', 'TOTALS',
    'MEAN', 'MEANS', 'MEDIAN', 'RANGE', 'RANGES', 'LIMIT', 'LIMITS',
    'TERM', 'TERMS', 'LONG', 'SHORT', 'CARE', 'COULD', 'LUNG', 'AREAS',
    'KEY', 'LEAD', 'BASED', 'GAPS', 'PMID', 'ROLE', 'PLANS', 'HOLDS',
    'NOVEL', 'FULLY', 'MORE', 'THESE', 'THEIR', 'ITS', 'NON', 'USE',
    # Common abbreviations
    'ET', 'AL', 'ETC', 'EG', 'IE', 'VS', 'VERSUS', 'VIA', 'PER', 'PRO',
    # Dates/Time
    'JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 'JUL', 'AUG', 'SEP', 'OCT',
    'NOV', 'DEC', 'YEAR', 'YEARS', 'MONTH', 'MONTHS', 'DAY', 'DAYS',
    # Numbers
    'ONE', 'TWO', 'THREE', 'FOUR', 'FIVE', 'SIX', 'SEVEN', 'EIGHT', 'NINE',
    # Other common words
    'DATA', 'ANALYSIS', 'METHOD', 'METHODS', 'RESULT', 'RESULTS', 'CONCLUSION',
    'BACKGROUND', 'OBJECTIVE', 'PURPOSE', 'AIM', 'GOAL', 'FINDING', 'FINDINGS',
    'SUMMARY', 'NEED', 'FUTURE', 'STUDIES', 'OUTCOMES', 'POTENTIAL', 'PROTOCOLS',
    'PATIENTS', 'EARLY', 'VARIOUS', 'SUGGEST', 'APPROACHES', 'FOCUS', 'TREATING',
    'EVALUATING', 'RECENT', 'ACROSS', 'AGENTS', 'AIMING', 'ALLELE', 'ALSO',
    'ATRIAL', 'AXIS', 'BASIS', 'BECOME', 'BEING', 'BETTER', 'BODILY', 'BRAIN',
    'COST', 'COSTS'
}

def load_our_38_genes() -> Set[str]:
    """Load our 38 genes from metastasis_rules_v1.0.1.json"""
    rules_path = Path(
        os.environ.get(
            "METASTASIS_RULES_PATH",
            "oncology-coPilot/oncology-backend-minimal/api/config/metastasis_rules_v1.0.1.json",
        )
    )
    if not rules_path.exists():
        rules_path = Path("oncology-coPilot/oncology-backend-minimal/api/config/metastasis_rules_v1.0.0.json")
    
    if not rules_path.exists():
        print(f"⚠️  Using hardcoded 38 genes")
        return OUR_38_GENES
    
    with open(rules_path) as f:
        rules = json.load(f)
    
    all_genes = set()
    for step_data in rules["steps"].values():
        all_genes.update(step_data.get("primary_genes", []))
        all_genes.update(step_data.get("secondary_genes", []))
    
    return all_genes

def validate_gene_symbol(gene: str) -> bool:
    """
    Validate if a string is likely a real gene symbol
    
    Uses heuristics based on known gene symbol patterns
    """
    # Length check
    if len(gene) < 2 or len(gene) > 10:
        return False
    
    # Exclude common words
    if gene in EXCLUDED_WORDS:
        return False
    
    # Exclude if in our 38 genes
    if gene in OUR_38_GENES:
        return False
    
    # Exclude if all digits
    if gene.isdigit():
        return False
    
    # Gene symbols are typically:
    # 1. All uppercase letters (BRAF, KRAS, EGFR)
    # 2. Mix of letters and numbers (TP53, CDK4, HER2)
    # 3. 2-6 characters for common genes
    
    # If all letters and > 5 chars, likely a word
    if gene.isalpha() and len(gene) > 5:
        return False
    
    # If has numbers, more likely to be gene (TP53, CDK4, etc.)
    has_numbers = any(c.isdigit() for c in gene)
    
    # Common gene patterns:
    # - 2-5 letters (BRAF, KRAS, EGFR, HER2)
    # - Letter(s) + number(s) (TP53, CDK4, VEGFR2)
    # - Number + letters (rare but possible)
    
    if gene.isalpha():
        # All letters: 2-5 chars likely gene
        return 2 <= len(gene) <= 5
    elif has_numbers:
        # Has numbers: 2-8 chars, must have at least one letter
        return 2 <= len(gene) <= 8 and any(c.isalpha() for c in gene)
    
    return False

def extract_genes_from_text(text: str) -> Set[str]:
    """
    Extract potential gene names from text
    
    Improved pattern matching with validation
    """
    if not text:
        return set()
    
    # Find all potential gene names
    matches = GENE_PATTERN.findall(text.upper())
    
    # Filter and validate
    genes = set()
    for m in matches:
        if validate_gene_symbol(m):
            genes.add(m)
    
    return genes

async def query_clinical_trials_mcp(client) -> List[Dict]:
    """Query ClinicalTrials.gov via BioMed-MCP"""
    print("\n📊 Querying ClinicalTrials.gov via BioMed-MCP...")
    
    results = []
    
    queries = [
        {
            "condition": "metastatic cancer",
            "study_phase": "Phase 3",
            "max_studies": 20,
            "analyze_trends": False
        },
        {
            "condition": "metastasis",
            "study_phase": "Phase 2",
            "max_studies": 20,
            "analyze_trends": False
        }
    ]
    
    for query in queries:
        try:
            print(f"  Querying: {query['condition']} - {query['study_phase']}...")
            result = await client.call_tool(
                "clinical_trials_research",
                query
            )
            
            # Extract text from result
            result_text = result.data if hasattr(result, 'data') else str(result)
            
            # Extract genes
            genes = extract_genes_from_text(result_text)
            
            # Extract NCT IDs
            nct_ids = re.findall(r'NCT\d{8}', result_text)
            
            results.append({
                "source": "ClinicalTrials.gov",
                "query": f"{query['condition']} - {query['study_phase']}",
                "genes": genes,
                "nct_ids": list(set(nct_ids)),
                "result_text": result_text[:500]  # First 500 chars
            })
            
            print(f"    ✅ Found {len(genes)} genes, {len(set(nct_ids))} NCT IDs")
            
        except Exception as e:
            print(f"    ❌ Error: {e}")
            continue
    
    return results

async def query_pubmed_mcp(client) -> List[Dict]:
    """Query PubMed via BioMed-MCP"""
    print("\n📊 Querying PubMed via BioMed-MCP...")
    
    results = []
    
    queries = [
        {
            "query": "metastasis driver genes 2024 2025",
            "max_papers": 15,
            "include_fulltext": True,
            "synthesize_findings": True
        },
        {
            "query": "metastatic cancer Phase 3 trials 2024",
            "max_papers": 15,
            "include_fulltext": True,
            "synthesize_findings": True
        },
        {
            "query": "FDA approved metastatic cancer drugs 2024 2025",
            "max_papers": 15,
            "include_fulltext": True,
            "synthesize_findings": True
        }
    ]
    
    for query in queries:
        try:
            print(f"  Querying: {query['query']}...")
            result = await client.call_tool(
                "biomedical_literature_search",
                query
            )
            
            # Extract text from result
            result_text = result.data if hasattr(result, 'data') else str(result)
            
            # Extract genes
            genes = extract_genes_from_text(result_text)
            
            # Extract PMIDs
            pmids = re.findall(r'\b\d{8}\b', result_text)  # Simple pattern
            
            results.append({
                "source": "PubMed",
                "query": query['query'],
                "genes": genes,
                "pmids": list(set(pmids[:10])),  # Limit to 10
                "result_text": result_text[:500]  # First 500 chars
            })
            
            print(f"    ✅ Found {len(genes)} genes, {len(set(pmids[:10]))} PMIDs")
            
        except Exception as e:
            print(f"    ❌ Error: {e}")
            continue
    
    return results

def consolidate_genes(trial_results: List[Dict], pubmed_results: List[Dict]) -> pd.DataFrame:
    """Consolidate genes from all sources and rank by priority"""
    print("\n📊 Consolidating genes...")
    
    gene_data = defaultdict(lambda: {
        "sources": [],
        "nct_ids": [],
        "pmids": [],
        "queries": [],
        "priority_score": 0
    })
    
    # Process trial results
    for result in trial_results:
        for gene in result["genes"]:
            gene_data[gene]["sources"].append("ClinicalTrials.gov")
            gene_data[gene]["nct_ids"].extend(result["nct_ids"])
            gene_data[gene]["queries"].append(result["query"])
            gene_data[gene]["priority_score"] += 10  # Higher weight for trials
    
    # Process PubMed results
    for result in pubmed_results:
        for gene in result["genes"]:
            gene_data[gene]["sources"].append("PubMed")
            gene_data[gene]["pmids"].extend(result["pmids"])
            gene_data[gene]["queries"].append(result["query"])
            gene_data[gene]["priority_score"] += 5  # Lower weight for literature
    
    # Convert to DataFrame
    results = []
    for gene, data in gene_data.items():
        results.append({
            "gene": gene,
            "sources": "; ".join(set(data["sources"])),
            "nct_ids": "; ".join(set(data["nct_ids"][:5])),  # Top 5
            "pmids": "; ".join(set(data["pmids"][:5])),  # Top 5
            "queries": "; ".join(set(data["queries"][:3])),  # Top 3
            "priority_score": data["priority_score"],
            "n_trials": len(set(data["nct_ids"])),
            "n_papers": len(set(data["pmids"]))
        })
    
    # Sort by priority score
    df = pd.DataFrame(results)
    df = df.sort_values("priority_score", ascending=False)
    
    print(f"  ✅ Consolidated {len(df)} unique genes")
    
    return df

async def query_clinical_trials_agents() -> List[Dict]:
    """Query ClinicalTrials.gov using agents directly"""
    print("\n📊 Querying ClinicalTrials.gov via BioMed agents...")
    
    try:
        from biomed_agents import ClinicalTrialsAgent
        agent = ClinicalTrialsAgent()
        
        results = []
        queries = [
            {"condition": "metastatic cancer", "study_phase": "Phase 3", "max_studies": 20},
            {"condition": "metastasis", "study_phase": "Phase 2", "max_studies": 20}
        ]
        
        for query in queries:
            print(f"  Querying: {query['condition']} - {query['study_phase']}...")
            result = await agent.research_condition(
                query["condition"],
                study_phase=query["study_phase"],
                max_studies=query["max_studies"]
            )
            
            result_text = str(result)
            genes = extract_genes_from_text(result_text)
            nct_ids = re.findall(r'NCT\d{8}', result_text)
            
            results.append({
                "source": "ClinicalTrials.gov",
                "query": f"{query['condition']} - {query['study_phase']}",
                "genes": genes,
                "nct_ids": list(set(nct_ids)),
                "result_text": result_text[:500]
            })
            
            print(f"    ✅ Found {len(genes)} genes, {len(set(nct_ids))} NCT IDs")
        
        return results
    except Exception as e:
        print(f"    ❌ Error using agents: {e}")
        return []

async def query_pubmed_agents() -> List[Dict]:
    """Query PubMed using agents directly"""
    print("\n📊 Querying PubMed via BioMed agents...")
    
    try:
        from biomed_agents import PubMedAgent
        agent = PubMedAgent()
        
        results = []
        queries = [
            "metastasis driver genes 2024 2025",
            "metastatic cancer Phase 3 trials 2024",
            "FDA approved metastatic cancer drugs 2024 2025"
        ]
        
        for query in queries:
            print(f"  Querying: {query}...")
            result = await agent.search_literature(
                query,
                max_papers=15,
                include_fulltext=True,
                synthesize_findings=True
            )
            
            result_text = str(result)
            genes = extract_genes_from_text(result_text)
            pmids = re.findall(r'\b\d{8}\b', result_text)
            
            results.append({
                "source": "PubMed",
                "query": query,
                "genes": genes,
                "pmids": list(set(pmids[:10])),
                "result_text": result_text[:500]
            })
            
            print(f"    ✅ Found {len(genes)} genes, {len(set(pmids[:10]))} PMIDs")
        
        return results
    except Exception as e:
        print(f"    ❌ Error using agents: {e}")
        return []

async def main_mcp():
    """Main collection pipeline using BioMed-MCP"""
    print("=" * 70)
    print("PROSPECTIVE VALIDATION GENE COLLECTION (BioMed-MCP)")
    print("=" * 70)
    print()
    
    # Load our 38 genes
    our_genes = load_our_38_genes()
    print(f"✅ Loaded {len(our_genes)} genes to exclude")
    
    if MCP_AVAILABLE:
        # Import Client and StdioTransport
        try:
            from fastmcp.client import Client
            from fastmcp.client.transports import StdioTransport
        except ImportError:
            print("❌ Could not import fastmcp.client")
            return
        
        # Setup MCP client - use venv Python if available
        if 'USE_VENV_PYTHON' in globals() and USE_VENV_PYTHON and biomed_venv_python.exists():
            python_cmd = str(biomed_venv_python)
        else:
            python_cmd = "python"
        
        transport = StdioTransport(
            command=python_cmd,
            args=["-m", "biomed_agents"],
            cwd=str(biomed_mcp_path)
        )
        client = Client(transport)
        
        print("\n🔌 Connecting to BioMed-MCP server...")
        
        async with client:
            try:
                # Query clinical trials
                trial_results = await query_clinical_trials_mcp(client)
                
                # Query PubMed
                pubmed_results = await query_pubmed_mcp(client)
                
                # Consolidate results
                df = consolidate_genes(trial_results, pubmed_results)
            except Exception as e:
                print(f"\n❌ Error during MCP collection: {e}")
                import traceback
                traceback.print_exc()
                return
                
    elif AGENTS_AVAILABLE:
        try:
            # Query clinical trials using agents directly
            trial_results = await query_clinical_trials_agents()
            
            # Query PubMed using agents directly
            pubmed_results = await query_pubmed_agents()
            
            # Consolidate results
            df = consolidate_genes(trial_results, pubmed_results)
        except Exception as e:
            print(f"\n❌ Error during collection: {e}")
            import traceback
            traceback.print_exc()
            return
    else:
        print("❌ Neither MCP nor agents available - cannot use BioMed-MCP")
        return
    
    try:
        # Save raw results
        raw_path = OUTPUT_DIR / "prospective_validation_genes_mcp.csv"
        df.to_csv(raw_path, index=False)
        print(f"\n💾 Saved raw results to: {raw_path}")
        
        # Show top 20
        print(f"\n📊 Top 20 candidate genes:")
        for i, (_, row) in enumerate(df.head(20).iterrows(), 1):
            print(f"  {i:2d}. {row['gene']:10s} | Score: {row['priority_score']:3d} | "
                  f"Trials: {row['n_trials']:2d} | Papers: {row['n_papers']:2d} | "
                  f"Sources: {row['sources']}")
        
        # Create curated list (top 15)
        curated = df.head(15)
        curated_path = OUTPUT_DIR / "prospective_validation_genes_curated_mcp.csv"
        curated.to_csv(curated_path, index=False)
        print(f"\n💾 Saved curated list (top 15) to: {curated_path}")
        
        print(f"\n✅ Collection complete!")
        print(f"  Total candidate genes: {len(df)}")
        print(f"  Curated (top 15): {len(curated)}")
        
    except Exception as e:
        print(f"\n❌ Error during collection: {e}")
        import traceback
        traceback.print_exc()

def main_manual():
    """Manual curation fallback"""
    print("=" * 70)
    print("PROSPECTIVE VALIDATION - MANUAL CURATION NEEDED")
    print("=" * 70)
    print()
    print("Since MCP is not available, please manually curate 10-15 genes from:")
    print("  1. Recent FDA approvals (2024-2025) for metastatic cancer")
    print("  2. Recent Phase III trials for metastasis")
    print("  3. Recent literature on metastasis drivers")
    print()
    print("Create: ../data/prospective_validation_genes_manual.csv")
    print("With columns: gene, source, nct_id (optional), fda_approval_date (optional), pmid (optional), priority_score")

def main():
    """Main entry point"""
    if MCP_AVAILABLE or AGENTS_AVAILABLE:
        asyncio.run(main_mcp())
    else:
        main_manual()

if __name__ == "__main__":
    main()
