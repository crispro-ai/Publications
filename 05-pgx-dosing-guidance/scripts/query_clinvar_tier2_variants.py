#!/usr/bin/env python3
"""
Tier 2 Heuristic Validation - ClinVar Lookup
==============================================
Queries ClinVar for each variant from tier2_validation_cases.json
and extracts pathogenicity submission counts.

Output: reports/tier2_clinvar_lookups.json

Usage:
    python query_clinvar_tier2_variants.py
"""

import json
import time
import requests
from typing import Dict, Optional, List
from datetime import datetime
from pathlib import Path

CLINVAR_BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
CLINVAR_WEB_API = "https://www.ncbi.nlm.nih.gov/clinvar/variation/"

def normalize_variant_to_hgvs(gene: str, variant: str) -> str:
    """Normalize variant notation to HGVS format for ClinVar lookup"""
    # If already in HGVS format (c.xxx), return as-is
    if variant.startswith("c.") or variant.startswith("p.") or variant.startswith("g."):
        return variant
    
    # For star alleles, we'll need to map to HGVS
    # This is a simplified mapping - in practice, would need PharmVar
    star_to_hgvs = {
        "UGT1A1": {
            "*6": "c.211G>A",  # rs4148323
            "*36": "c.-3279T>G",  # TA6 (promoter)
            "*37": "c.-3279T>G",  # TA7 (promoter) - same as *28
            "*60": "c.686C>A",  # rs4124874
            "*93": "c.1091C>T",  # rs10929302
        }
    }
    
    if gene in star_to_hgvs and variant in star_to_hgvs[gene]:
        return star_to_hgvs[gene][variant]
    
    return variant

def search_clinvar_variant(gene: str, variant: str) -> Optional[Dict]:
    """Search ClinVar for a variant using Entrez API"""
    # Normalize variant
    hgvs = normalize_variant_to_hgvs(gene, variant)
    
    # Build search query
    query = f'"{gene}"[Gene] AND "{hgvs}"[Variant]'
    
    try:
        # Search ClinVar database
        url = f"{CLINVAR_BASE_URL}/esearch.fcgi"
        params = {
            "db": "clinvar",
            "term": query,
            "retmax": 5,
            "retmode": "json"
        }
        
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        variation_ids = data.get("esearchresult", {}).get("idlist", [])
        
        if not variation_ids:
            return None
        
        # Fetch variation details (use first match)
        variation_id = variation_ids[0]
        
        # Get summary
        summary_url = f"{CLINVAR_BASE_URL}/esummary.fcgi"
        summary_params = {
            "db": "clinvar",
            "id": variation_id,
            "retmode": "json"
        }
        
        summary_response = requests.get(summary_url, params=summary_params, timeout=30)
        summary_response.raise_for_status()
        summary_data = summary_response.json()
        
        variation_data = summary_data.get("result", {}).get(variation_id, {})
        
        # Extract pathogenicity counts from clinical significance
        clinical_significance = variation_data.get("clinical_significance", {})
        
        # Count submissions by interpretation
        pathogenic_count = 0
        likely_pathogenic_count = 0
        vus_count = 0
        likely_benign_count = 0
        benign_count = 0
        
        # Parse clinical significance descriptions
        description = clinical_significance.get("description", "")
        review_status = clinical_significance.get("review_status", "")
        
        # Try to extract counts from variation data
        # Note: ClinVar API structure may vary - this is a simplified extraction
        # In practice, would need to parse full XML or use ClinVar web scraping
        
        return {
            "variation_id": variation_id,
            "gene": gene,
            "variant": variant,
            "variant_hgvs": hgvs,
            "clinical_significance": description,
            "review_status": review_status,
            "pathogenic_count": pathogenic_count,  # Will be populated from detailed lookup
            "likely_pathogenic_count": likely_pathogenic_count,
            "vus_count": vus_count,
            "likely_benign_count": likely_pathogenic_count,
            "benign_count": benign_count,
            "conflicting_interpretations": "Unknown",  # Needs detailed parsing
            "lookup_method": "entrez_api",
            "lookup_date": datetime.now().isoformat(),
            "notes": "Pathogenicity counts require detailed ClinVar XML parsing or web scraping"
        }
        
    except Exception as e:
        print(f"  ❌ Error querying ClinVar for {gene} {variant}: {e}")
        return None

def scrape_clinvar_pathogenicity_counts(variation_id: str) -> Dict[str, int]:
    """
    Scrape ClinVar web page to count pathogenicity submissions.
    Uses same approach as codebase: count occurrences in HTML text.
    """
    url = f"https://www.ncbi.nlm.nih.gov/clinvar/variation/{variation_id}/"
    
    try:
        response = requests.get(url, timeout=30, headers={
            'User-Agent': 'Mozilla/5.0 (compatible; research tool)'
        })
        response.raise_for_status()
        text = response.text.lower()
        
        def _count(html_text: str, search_term: str) -> int:
            """Count occurrences of search term in HTML (case-insensitive)"""
            try:
                return html_text.count(search_term.lower())
            except Exception:
                return 0
        
        counts = {
            "pathogenic_count": _count(text, "pathogenic"),
            "likely_pathogenic_count": _count(text, "likely pathogenic"),
            "vus_count": _count(text, "uncertain significance"),
            "benign_count": _count(text, "benign"),
            "likely_benign_count": _count(text, "likely benign"),
        }
        
        # Check for conflicting interpretations
        conflicting = "conflicting" in text or "conflict" in text
        
        return {
            **counts,
            "conflicting_interpretations": "Yes" if conflicting else "No",
            "scrape_url": url
        }
        
    except Exception as e:
        print(f"    ⚠️  Web scrape failed: {e}")
        return {
            "pathogenic_count": 0,
            "likely_pathogenic_count": 0,
            "vus_count": 0,
            "benign_count": 0,
            "likely_benign_count": 0,
            "conflicting_interpretations": "Unknown",
            "scrape_url": url,
            "scrape_error": str(e)
        }

def lookup_clinvar_web(gene: str, variant: str) -> Optional[Dict]:
    """Alternative: Use web scraping for ClinVar (fallback)"""
    # Try to find variation ID via web search
    search_url = f"https://www.ncbi.nlm.nih.gov/clinvar/?term={gene}%20{variant}"
    try:
        response = requests.get(search_url, timeout=30, headers={
            'User-Agent': 'Mozilla/5.0 (compatible; research tool)'
        })
        # Extract variation ID from redirect or search results
        # This is a simplified approach - may need more sophisticated parsing
        if "variation/" in response.url:
            variation_id = response.url.split("variation/")[1].split("/")[0]
            counts = scrape_clinvar_pathogenicity_counts(variation_id)
            return {
                "variation_id": variation_id,
                "gene": gene,
                "variant": variant,
                **counts,
                "lookup_method": "web_scrape",
                "lookup_date": datetime.now().isoformat()
            }
    except Exception:
        pass
    return None

def main():
    # Load validation cases
    cases_path = Path("reports/tier2_validation_cases.json")
    if not cases_path.exists():
        print(f"❌ Error: {cases_path} not found")
        print("   Run extract_tier2_validation_cases.py first")
        return
    
    with open(cases_path, 'r') as f:
        cases_data = json.load(f)
    
    cases = cases_data.get("cases", [])
    print(f"Loaded {len(cases)} cases from {cases_path}")
    
    # Get unique variants
    unique_variants = {}
    for case in cases:
        gene = case.get("gene")
        variant = case.get("variant")
        if gene and variant:
            key = f"{gene}:{variant}"
            if key not in unique_variants:
                unique_variants[key] = {"gene": gene, "variant": variant}
    
    print(f"\nFound {len(unique_variants)} unique variants to query")
    print("="*70)
    
    # Query ClinVar for each variant
    clinvar_lookups = []
    
    for i, (key, variant_info) in enumerate(unique_variants.items(), 1):
        gene = variant_info["gene"]
        variant = variant_info["variant"]
        
        print(f"\n[{i}/{len(unique_variants)}] Querying ClinVar: {gene} {variant}")
        
        lookup_result = search_clinvar_variant(gene, variant)
        
        if lookup_result:
            variation_id = lookup_result.get('variation_id')
            if variation_id:
                # Scrape web page for pathogenicity counts
                print(f"    Scraping ClinVar web page for counts...")
                counts = scrape_clinvar_pathogenicity_counts(variation_id)
                lookup_result.update(counts)
                lookup_result["lookup_method"] = "entrez_api_plus_web_scrape"
            clinvar_lookups.append(lookup_result)
            print(f"  ✅ Found variation ID: {variation_id}")
            if variation_id:
                print(f"    Pathogenicity counts: P={lookup_result.get('pathogenic_count', 0)}, "
                      f"LP={lookup_result.get('likely_pathogenic_count', 0)}, "
                      f"B={lookup_result.get('benign_count', 0)}, "
                      f"LB={lookup_result.get('likely_benign_count', 0)}, "
                      f"VUS={lookup_result.get('vus_count', 0)}")
        else:
            # Create placeholder for manual lookup
            clinvar_lookups.append({
                "gene": gene,
                "variant": variant,
                "variant_hgvs": normalize_variant_to_hgvs(gene, variant),
                "variation_id": None,
                "pathogenic_count": None,
                "likely_pathogenic_count": None,
                "vus_count": None,
                "likely_benign_count": None,
                "benign_count": None,
                "conflicting_interpretations": "Unknown",
                "lookup_method": "manual_required",
                "lookup_date": datetime.now().isoformat(),
                "notes": "ClinVar API lookup failed - requires manual web lookup"
            })
            print(f"  ⚠️  No ClinVar match found - trying web scrape...")
            # Try web scraping as fallback
            web_result = lookup_clinvar_web(gene, variant)
            if web_result:
                clinvar_lookups[-1] = web_result
                print(f"    ✅ Web scrape found variation ID: {web_result.get('variation_id')}")
            else:
                print(f"    ⚠️  Web scrape also failed - manual lookup required")
        
        time.sleep(1.0)  # Rate limiting (be polite to ClinVar servers)
    
    # Save results
    output_path = Path("reports/tier2_clinvar_lookups.json")
    output_data = {
        "lookup_date": datetime.now().isoformat(),
        "total_variants_queried": len(unique_variants),
        "successful_lookups": sum(1 for l in clinvar_lookups if l.get("variation_id")),
        "manual_lookups_required": sum(1 for l in clinvar_lookups if not l.get("variation_id")),
        "lookups": clinvar_lookups
    }
    
    with open(output_path, 'w') as f:
        json.dump(output_data, f, indent=2)
    
    print(f"\n✅ Saved {len(clinvar_lookups)} ClinVar lookups to {output_path}")
    print(f"\nSummary:")
    print(f"  - Successful API lookups: {output_data['successful_lookups']}")
    print(f"  - Manual lookups required: {output_data['manual_lookups_required']}")
    print(f"\n⚠️  NOTE: ClinVar Entrez API provides limited pathogenicity count data.")
    print(f"   For detailed submission counts, use:")
    print(f"   1. ClinVar web interface: https://www.ncbi.nlm.nih.gov/clinvar/")
    print(f"   2. ClinVar XML download: https://ftp.ncbi.nlm.nih.gov/pub/clinvar/xml/")
    print(f"   3. Manual curation from case report publications")

if __name__ == "__main__":
    main()



