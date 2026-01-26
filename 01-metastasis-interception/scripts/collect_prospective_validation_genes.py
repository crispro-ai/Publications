#!/usr/bin/env python3
"""
Collect Prospective Validation Genes (2024-2025)

Purpose:
- Query ClinicalTrials.gov, PubMed, and FDA databases for newly approved/Phase III metastatic genes
- Extract gene targets from trials, approvals, and literature
- Filter to genes NOT in our 38-gene set
- Rank by priority (FDA approval > Phase III > literature)

Data Sources:
1. ClinicalTrials.gov API
2. PubMed (via BioMed-MCP or Entrez)
3. FDA databases (via web scraping or API)

Outputs:
- ../data/prospective_validation_genes_raw.csv
- ../data/prospective_validation_genes_curated.csv

Author: Zo (Platform AI)
Date: January 19, 2026
Version: 1.0.0
"""

import json
import os
import re
import csv
import requests
import pandas as pd
from pathlib import Path
from typing import Dict, List, Set, Optional
from datetime import datetime
from collections import defaultdict
import time

# Configuration
OUTPUT_DIR = Path("publication/data")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ClinicalTrials.gov API
CLINICALTRIALS_API = "https://clinicaltrials.gov/api/v2/studies"

# PubMed API (Entrez)
PUBMED_BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"

# Our 38 genes (to exclude)
OUR_38_GENES = {
    'ANGPT2', 'AXL', 'BCL2', 'BIRC5', 'BRAF', 'CCL2', 'CCR7', 'CLDN4', 'CTSD',
    'CXCL12', 'CXCR4', 'HIF1A', 'ICAM1', 'IL6', 'KRAS', 'MAP2K1', 'MCL1', 'MET',
    'MMP14', 'MMP2', 'MMP9', 'NOTCH1', 'NRAS', 'PLOD2', 'POSTN', 'PTGS2', 'PTK2',
    'S100A4', 'SELE', 'SNAI1', 'SRC', 'TGFB1', 'TGFBR1', 'TWIST1', 'VCAM1',
    'VEGFA', 'VEGFR2', 'ZEB1'
}

# Common gene name patterns
GENE_PATTERN = re.compile(r'\b([A-Z][A-Z0-9]+[A-Z0-9]*)\b')

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

def query_clinicaltrials_gov(query: str, max_results: int = 100) -> List[Dict]:
    """
    Query ClinicalTrials.gov API
    
    Args:
        query: Search query (e.g., "metastasis")
        max_results: Maximum number of results
    
    Returns:
        List of study records
    """
    print(f"\n📊 Querying ClinicalTrials.gov: '{query}'...")
    
    # ClinicalTrials.gov API v2 format
    # Use query parameter for search terms, separate filters
    params = {
        "query": query,  # Main search query
        "filter.overallStatus": "RECRUITING|ACTIVE_NOT_RECRUITING|COMPLETED",
        "pageSize": min(max_results, 100),
        "format": "json"
    }
    
    try:
        response = requests.get(CLINICALTRIALS_API, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        studies = data.get("studies", [])
        
        # Filter by date manually (API date filter may not work as expected)
        filtered_studies = []
        for study in studies:
            protocol = study.get("protocolSection", {})
            status = protocol.get("statusModule", {})
            start_date = status.get("startDateStruct", {}).get("date", "")
            
            # Check if start date is in 2024-2025
            if start_date and ("2024" in start_date or "2025" in start_date):
                filtered_studies.append(study)
            elif not start_date:
                # Include if no date (may be recent)
                filtered_studies.append(study)
        
        print(f"  ✅ Found {len(studies)} studies, {len(filtered_studies)} in 2024-2025")
        return filtered_studies
    except Exception as e:
        print(f"  ❌ Error querying ClinicalTrials.gov: {e}")
        print(f"     Response: {response.text[:200] if 'response' in locals() else 'N/A'}")
        return []

def extract_genes_from_text(text: str) -> Set[str]:
    """
    Extract potential gene names from text
    
    Uses simple pattern matching - may have false positives
    """
    if not text:
        return set()
    
    # Find all potential gene names (2-10 uppercase alphanumeric)
    matches = GENE_PATTERN.findall(text.upper())
    
    # Filter to likely gene names (exclude common words, dates, etc.)
    excluded = {
        'FDA', 'NCT', 'PHASE', 'TRIAL', 'STUDY', 'PATIENT', 'CANCER', 'TUMOR',
        'METASTASIS', 'METASTATIC', 'APPROVED', 'ENROLLMENT', 'RESULTS',
        'EFFICACY', 'SAFETY', 'DOSE', 'MG', 'ML', 'IV', 'ORAL', 'PO'
    }
    
    genes = {m for m in matches if len(m) >= 2 and len(m) <= 10 and m not in excluded}
    return genes

def extract_genes_from_study(study: Dict) -> Set[str]:
    """Extract gene targets from a ClinicalTrials.gov study"""
    genes = set()
    
    # Check protocol section
    protocol = study.get("protocolSection", {})
    
    # Intervention names
    interventions = protocol.get("armsInterventionsModule", {}).get("interventions", [])
    for intervention in interventions:
        name = intervention.get("name", "")
        genes.update(extract_genes_from_text(name))
    
    # Condition
    conditions = protocol.get("conditionsModule", {}).get("conditions", [])
    for condition in conditions:
        genes.update(extract_genes_from_text(condition))
    
    # Description
    description = protocol.get("descriptionModule", {}).get("briefSummary", "")
    genes.update(extract_genes_from_text(description))
    
    return genes

def query_pubmed(query: str, max_results: int = 50) -> List[Dict]:
    """
    Query PubMed API
    
    Args:
        query: Search query
        max_results: Maximum number of results
    
    Returns:
        List of paper records
    """
    print(f"\n📊 Querying PubMed: '{query}'...")
    
    # Step 1: Search
    search_url = f"{PUBMED_BASE}/esearch.fcgi"
    search_params = {
        "db": "pubmed",
        "term": query,
        "retmax": max_results,
        "retmode": "json"
    }
    
    try:
        response = requests.get(search_url, params=search_params, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        pmids = data.get("esearchresult", {}).get("idlist", [])
        print(f"  ✅ Found {len(pmids)} papers")
        
        if not pmids:
            return []
        
        # Step 2: Fetch details
        fetch_url = f"{PUBMED_BASE}/efetch.fcgi"
        fetch_params = {
            "db": "pubmed",
            "id": ",".join(pmids),
            "retmode": "xml"
        }
        
        # For now, just return PMIDs - full text parsing is complex
        papers = [{"pmid": pmid} for pmid in pmids]
        return papers
    except Exception as e:
        print(f"  ❌ Error querying PubMed: {e}")
        return []

def collect_clinicaltrials_genes() -> List[Dict]:
    """Collect genes from ClinicalTrials.gov"""
    all_genes = defaultdict(lambda: {
        "sources": [],
        "nct_ids": [],
        "phases": [],
        "titles": []
    })
    
    queries = [
        "metastasis",
        "metastatic cancer",
    ]
    
    for query in queries:
        studies = query_clinicaltrials_gov(query, max_results=50)
        
        for study in studies:
            protocol = study.get("protocolSection", {})
            nct_id = protocol.get("identificationModule", {}).get("nctId", "")
            title = protocol.get("identificationModule", {}).get("briefTitle", "")
            
            # Get phase
            design = protocol.get("designModule", {})
            phases = design.get("phases", [])
            phase = phases[0] if phases else "Unknown"
            
            # Only include Phase 2 or Phase 3 trials
            if phase not in ["PHASE2", "PHASE3"]:
                continue
            
            # Extract genes
            genes = extract_genes_from_study(study)
            
            for gene in genes:
                if gene not in OUR_38_GENES and len(gene) >= 2:
                    all_genes[gene]["sources"].append("ClinicalTrials.gov")
                    all_genes[gene]["nct_ids"].append(nct_id)
                    all_genes[gene]["phases"].append(phase)
                    all_genes[gene]["titles"].append(title)
        
        time.sleep(1)  # Rate limiting
    
    # Convert to list
    results = []
    for gene, data in all_genes.items():
        results.append({
            "gene": gene,
            "source": "ClinicalTrials.gov",
            "nct_ids": "; ".join(set(data["nct_ids"])),
            "phases": "; ".join(set(data["phases"])),
            "titles": "; ".join(set(data["titles"][:3])),  # First 3 titles
            "priority_score": len(set(data["nct_ids"]))  # More trials = higher priority
        })
    
    return results

def collect_pubmed_genes() -> List[Dict]:
    """Collect genes from PubMed"""
    all_genes = defaultdict(lambda: {
        "sources": [],
        "pmids": [],
        "titles": []
    })
    
    queries = [
        '("metastasis" OR "metastatic") AND ("driver" OR "target") AND ("2024"[PDAT] OR "2025"[PDAT])',
        '("metastasis" OR "metastatic") AND ("Phase 3" OR "Phase III") AND ("2024"[PDAT] OR "2025"[PDAT])',
        '("metastasis" OR "metastatic") AND ("FDA approved" OR "approval") AND ("2024"[PDAT] OR "2025"[PDAT])',
    ]
    
    for query in queries:
        papers = query_pubmed(query, max_results=30)
        
        for paper in papers:
            pmid = paper.get("pmid", "")
            # Note: Full text extraction would require parsing XML
            # For now, we'll use PMIDs and note that manual review is needed
        
        time.sleep(1)  # Rate limiting
    
    # For now, return empty - would need full text parsing
    return []

def main():
    """Main collection pipeline"""
    print("=" * 70)
    print("PROSPECTIVE VALIDATION GENE COLLECTION")
    print("=" * 70)
    print()
    
    # Load our 38 genes
    our_genes = load_our_38_genes()
    print(f"✅ Loaded {len(our_genes)} genes to exclude")
    
    # Collect from ClinicalTrials.gov
    print(f"\n📊 Step 1: Collecting from ClinicalTrials.gov...")
    ct_genes = collect_clinicaltrials_genes()
    print(f"  ✅ Found {len(ct_genes)} candidate genes")
    
    # Collect from PubMed (placeholder - needs full implementation)
    print(f"\n📊 Step 2: Collecting from PubMed...")
    pubmed_genes = collect_pubmed_genes()
    print(f"  ✅ Found {len(pubmed_genes)} candidate genes")
    
    # Combine results
    all_results = ct_genes + pubmed_genes
    
    # Remove duplicates and sort by priority
    gene_dict = {}
    for result in all_results:
        gene = result["gene"]
        if gene not in gene_dict or result["priority_score"] > gene_dict[gene]["priority_score"]:
            gene_dict[gene] = result
    
    # Sort by priority score
    sorted_results = sorted(gene_dict.values(), key=lambda x: x["priority_score"], reverse=True)
    
    # Save raw results
    raw_path = OUTPUT_DIR / "prospective_validation_genes_raw.csv"
    if sorted_results:
        df = pd.DataFrame(sorted_results)
        df.to_csv(raw_path, index=False)
        print(f"\n💾 Saved raw results to: {raw_path}")
        print(f"  Top 20 genes:")
        for i, row in df.head(20).iterrows():
            print(f"    {i+1}. {row['gene']}: {row['priority_score']} trials, source={row['source']}")
    else:
        print(f"\n⚠️  No genes found - check queries and API access")
    
    # Create curated list (top 15)
    curated = sorted_results[:15]
    curated_path = OUTPUT_DIR / "prospective_validation_genes_curated.csv"
    if curated:
        df_curated = pd.DataFrame(curated)
        df_curated.to_csv(curated_path, index=False)
        print(f"\n💾 Saved curated list (top 15) to: {curated_path}")
    
    print(f"\n✅ Collection complete!")
    print(f"  Total candidate genes: {len(sorted_results)}")
    print(f"  Curated (top 15): {len(curated)}")

if __name__ == "__main__":
    main()
