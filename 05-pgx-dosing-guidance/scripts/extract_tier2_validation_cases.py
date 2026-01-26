#!/usr/bin/env python3
"""
Tier 2 Heuristic Validation - Case Report Extraction
====================================================
Extracts published case reports for non-CPIC DPYD/UGT1A1 variants
to validate ClinVar→dosing heuristic rules.

Target: 20-30 cases with:
- Non-CPIC variants (not *2A, *13, *2846A>T)
- Known toxicity outcomes (Grade 0-5)
- ClinVar lookup capability

Usage:
    python extract_tier2_validation_cases.py --output ../reports/tier2_validation_cases.json
"""

import json
import time
import argparse
import requests
from typing import List, Dict, Optional
from datetime import datetime
from pathlib import Path

NCBI_BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"

# Non-CPIC variants to target (exclude CPIC Level A variants)
NON_CPIC_VARIANTS = {
    "DPYD": [
        "c.496A>G",      # rs2297595
        "c.2194G>A",     # rs1801160
        "c.1003G>A",     # rs1801158
        "c.85T>C",       # rs1801265
        "c.1627A>G",     # rs1801159
        "c.2846A>T",     # rs67376798 (CPIC Level B, but include for validation)
    ],
    "UGT1A1": [
        "*6",            # rs4148323
        "*36",           # rs8175347 (TA6)
        "*37",           # rs8175347 (TA7)
        "*60",           # rs4124874
        "*93",           # rs10929302
    ]
}

# PubMed search queries for non-CPIC variants
PUBMED_QUERIES = [
    # DPYD non-CPIC variants
    '("DPYD" OR "DPD") AND ("c.496A>G" OR "rs2297595") AND ("fluoropyrimidine" OR "5-FU" OR "capecitabine") AND ("toxicity" OR "adverse")',
    '("DPYD" OR "DPD") AND ("c.2194G>A" OR "rs1801160") AND ("fluoropyrimidine" OR "5-FU" OR "capecitabine") AND ("toxicity" OR "adverse")',
    '("DPYD" OR "DPD") AND ("c.1003G>A" OR "rs1801158") AND ("fluoropyrimidine" OR "5-FU" OR "capecitabine") AND ("toxicity" OR "adverse")',
    '("DPYD" OR "DPD") AND ("c.85T>C" OR "rs1801265") AND ("fluoropyrimidine" OR "5-FU" OR "capecitabine") AND ("toxicity" OR "adverse")',
    '("DPYD" OR "DPD") AND ("c.1627A>G" OR "rs1801159") AND ("fluoropyrimidine" OR "5-FU" OR "capecitabine") AND ("toxicity" OR "adverse")',
    
    # UGT1A1 non-CPIC variants
    '("UGT1A1*6" OR "UGT1A1 *6" OR "rs4148323") AND "irinotecan" AND ("toxicity" OR "neutropenia" OR "diarrhea")',
    '("UGT1A1*36" OR "UGT1A1 *36" OR "TA6") AND "irinotecan" AND ("toxicity" OR "neutropenia" OR "diarrhea")',
    '("UGT1A1*37" OR "UGT1A1 *37" OR "TA7") AND "irinotecan" AND ("toxicity" OR "neutropenia" OR "diarrhea")',
    '("UGT1A1*60" OR "UGT1A1 *60" OR "rs4124874") AND "irinotecan" AND ("toxicity" OR "neutropenia" OR "diarrhea")',
    '("UGT1A1*93" OR "UGT1A1 *93" OR "rs10929302") AND "irinotecan" AND ("toxicity" OR "neutropenia" OR "diarrhea")',
    
    # Broader searches
    '("DPYD" OR "DPD deficiency") AND "fluoropyrimidine" AND "case report" AND "toxicity" NOT ("*2A" OR "*13" OR "rs3918290" OR "rs55886062")',
    '("UGT1A1") AND "irinotecan" AND "case report" AND ("toxicity" OR "neutropenia") NOT ("*28" OR "rs8175347")',
    
    # Additional variant searches
    '("DPYD" OR "DPD") AND ("rs2297595" OR "rs1801160" OR "rs1801158" OR "rs1801265") AND ("toxicity" OR "adverse event")',
    '("UGT1A1") AND ("rs4148323" OR "rs4124874" OR "rs10929302") AND "irinotecan" AND ("toxicity" OR "neutropenia")',
    
    # Cohort studies (may contain multiple cases)
    '("DPYD polymorphism" OR "DPYD variant") AND "fluoropyrimidine" AND ("cohort" OR "retrospective" OR "prospective") AND "toxicity"',
    '("UGT1A1 polymorphism" OR "UGT1A1 variant") AND "irinotecan" AND ("cohort" OR "retrospective" OR "prospective") AND "toxicity"',
    
    # Additional variant notations
    '("DPYD" OR "DPD") AND ("p.Ile560Val" OR "p.Val732Ile" OR "p.Arg235Trp") AND "toxicity"',
    '("UGT1A1") AND ("c.211G>A" OR "c.-3279T>G") AND "irinotecan" AND "toxicity"',
]

def search_pubmed(query: str, max_results: int = 20) -> List[str]:
    """Search PubMed and return PMIDs"""
    url = f"{NCBI_BASE_URL}/esearch.fcgi"
    params = {"db": "pubmed", "term": query, "retmax": max_results, "retmode": "json"}
    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        pmids = data.get("esearchresult", {}).get("idlist", [])
        count = int(data.get("esearchresult", {}).get("count", 0))
        print(f"  Query: {query[:80]}...")
        print(f"  Found {count} total, retrieved {len(pmids)} PMIDs")
        return pmids
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return []

def fetch_pubmed_summary(pmids: List[str]) -> List[Dict]:
    """Fetch PubMed summaries for PMIDs"""
    if not pmids:
        return []
    
    url = f"{NCBI_BASE_URL}/esummary.fcgi"
    params = {"db": "pubmed", "id": ",".join(pmids), "retmode": "json"}
    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        return [data["result"][pmid] for pmid in pmids if pmid in data.get("result", {})]
    except Exception as e:
        print(f"  ❌ Error fetching summaries: {e}")
        return []

def extract_variant_from_text(text: str, gene: str) -> Optional[str]:
    """Extract variant notation from text (HGVS or star allele)"""
    text_lower = text.lower()
    
    # DPYD variants
    if gene == "DPYD":
        for variant in NON_CPIC_VARIANTS["DPYD"]:
            if variant.lower() in text_lower:
                return variant
        # Try to find rsID patterns
        import re
        rsid_pattern = r'rs\d+'
        rsids = re.findall(rsid_pattern, text)
        for rsid in rsids:
            # Map known rsIDs to variants
            rsid_to_variant = {
                "rs2297595": "c.496A>G",
                "rs1801160": "c.2194G>A",
                "rs1801158": "c.1003G>A",
                "rs1801265": "c.85T>C",
                "rs1801159": "c.1627A>G",
            }
            if rsid in rsid_to_variant:
                return rsid_to_variant[rsid]
    
    # UGT1A1 variants
    elif gene == "UGT1A1":
        for variant in NON_CPIC_VARIANTS["UGT1A1"]:
            if f"*{variant}" in text or f"* {variant}" in text or variant in text:
                return f"*{variant}" if not variant.startswith("*") else variant
    
    return None

def extract_toxicity_grade(text: str) -> Optional[int]:
    """Extract toxicity grade from text (0-5)"""
    import re
    text_lower = text.lower()
    
    # Look for "Grade 3", "grade 4", "G3", "G4", etc.
    grade_patterns = [
        r'grade\s*(\d)',
        r'g(\d)',
        r'ctcae\s*grade\s*(\d)',
        r'grade\s*(\d)\s*toxicity',
    ]
    
    for pattern in grade_patterns:
        matches = re.findall(pattern, text_lower)
        if matches:
            grade = int(matches[0])
            if 0 <= grade <= 5:
                return grade
    
    # Look for fatal/death keywords (Grade 5)
    if any(word in text_lower for word in ["fatal", "death", "died", "lethal"]):
        return 5
    
    # Look for severe toxicity keywords (likely Grade 3+)
    if any(word in text_lower for word in ["severe", "life-threatening", "hospitalization"]):
        return 3  # Conservative estimate
    
    return None

def determine_gene_from_variant(variant: str) -> Optional[str]:
    """Determine gene from variant notation"""
    if variant.startswith("c.") or variant.startswith("rs"):
        return "DPYD"
    elif variant.startswith("*") or "UGT1A1" in variant:
        return "UGT1A1"
    return None

def main():
    parser = argparse.ArgumentParser(description="Extract Tier 2 validation cases from PubMed")
    parser.add_argument("--output", type=str, default="reports/tier2_validation_cases.json")
    parser.add_argument("--max-per-query", type=int, default=20)  # Increased from 10 to 20
    args = parser.parse_args()
    
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    print("="*70)
    print("TIER 2 VALIDATION CASE EXTRACTION")
    print("="*70)
    print(f"Target: 20-30 cases with non-CPIC variants")
    print(f"Output: {output_path}")
    print()
    
    all_pmids = set()
    
    # Search all queries
    print("STEP 1: Searching PubMed...")
    for i, query in enumerate(PUBMED_QUERIES, 1):
        print(f"\nQuery {i}/{len(PUBMED_QUERIES)}:")
        pmids = search_pubmed(query, max_results=args.max_per_query)
        all_pmids.update(pmids)
        time.sleep(0.5)  # Rate limiting
    
    print(f"\n✅ Total unique PMIDs: {len(all_pmids)}")
    
    # Fetch summaries
    print("\nSTEP 2: Fetching article summaries...")
    pmids_list = list(all_pmids)
    summaries = fetch_pubmed_summary(pmids_list)
    print(f"✅ Retrieved {len(summaries)} summaries")
    
    # Extract case information
    print("\nSTEP 3: Extracting case information...")
    cases = []
    case_counter = 1
    
    for summary in summaries:
        pmid = summary.get("uid", "")
        title = summary.get("title", "")
        abstract = summary.get("abstract", "")
        authors = summary.get("authors", [])
        pub_date = summary.get("pubdate", "")
        
        # Combine title and abstract for variant extraction
        full_text = f"{title} {abstract}".lower()
        
        # Determine gene and variant
        gene = None
        variant = None
        
        # Try to extract variant
        if "dpyd" in full_text or "dihydropyrimidine dehydrogenase" in full_text:
            gene = "DPYD"
            variant = extract_variant_from_text(f"{title} {abstract}", "DPYD")
        elif "ugt1a1" in full_text or "udp-glucuronosyltransferase" in full_text:
            gene = "UGT1A1"
            variant = extract_variant_from_text(f"{title} {abstract}", "UGT1A1")
        
        # Skip if no variant found or if CPIC variant
        if not variant:
            continue
        
        # Skip CPIC Level A variants
        cpic_variants = ["*2A", "*13", "c.1905+1G>A", "rs3918290", "rs55886062"]
        if any(cpic in variant for cpic in cpic_variants):
            continue
        
        # Extract toxicity grade
        toxicity_grade = extract_toxicity_grade(f"{title} {abstract}")
        
        # Determine drug
        drug = "Unknown"
        if "fluoropyrimidine" in full_text or "5-fu" in full_text or "5-fluorouracil" in full_text:
            drug = "5-fluorouracil"
        elif "capecitabine" in full_text:
            drug = "capecitabine"
        elif "irinotecan" in full_text:
            drug = "irinotecan"
        
        # Create case
        case = {
            "case_id": f"CASE-{case_counter:03d}",
            "pmid": pmid,
            "title": title,
            "authors": authors,
            "publication_date": pub_date,
            "gene": gene,
            "variant": variant,
            "variant_hgvs": variant,  # Will be normalized later
            "drug": drug,
            "toxicity_grade": toxicity_grade,
            "toxicity_occurred": toxicity_grade is not None and toxicity_grade >= 3,
            "extraction_method": "automated_from_abstract",
            "status": "needs_manual_curation",
            "notes": "Variant and toxicity grade extracted from abstract. Requires manual verification.",
            "extraction_date": datetime.now().isoformat()
        }
        
        cases.append(case)
        case_counter += 1
    
    # Save results
    output_data = {
        "extraction_date": datetime.now().isoformat(),
        "total_pmids_searched": len(all_pmids),
        "total_cases_extracted": len(cases),
        "genes": list(set(c["gene"] for c in cases if c.get("gene"))),
        "variants_found": list(set(c["variant"] for c in cases if c.get("variant"))),
        "cases": cases
    }
    
    with open(output_path, 'w') as f:
        json.dump(output_data, f, indent=2)
    
    print(f"\n✅ Saved {len(cases)} cases to {output_path}")
    print(f"\nSummary:")
    print(f"  - Genes: {', '.join(output_data['genes'])}")
    print(f"  - Unique variants: {len(output_data['variants_found'])}")
    print(f"  - Cases with toxicity grade: {sum(1 for c in cases if c.get('toxicity_grade') is not None)}")
    print(f"\n⚠️  NOTE: These cases require manual curation to verify:")
    print(f"  - Exact variant notation (HGVS)")
    print(f"  - Toxicity grade accuracy")
    print(f"  - Drug exposure details")
    print(f"  - Exclusion of CPIC variants")

if __name__ == "__main__":
    main()



