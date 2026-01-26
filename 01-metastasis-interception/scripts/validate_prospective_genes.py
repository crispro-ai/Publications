#!/usr/bin/env python3
"""
Validate Prospective Validation Genes

Post-processes MCP collection results to validate gene symbols against Ensembl
and filter out common words.

Author: Zo (Platform AI)
Date: January 19, 2026
"""

import pandas as pd
import requests
import time
from pathlib import Path
from typing import List, Tuple

OUTPUT_DIR = Path("publication/data")

def validate_gene_ensembl(gene: str) -> Tuple[bool, str]:
    """Validate gene symbol against Ensembl API"""
    try:
        url = f"https://rest.ensembl.org/lookup/symbol/homo_sapiens/{gene}?expand=0"
        response = requests.get(url, headers={"Content-Type": "application/json"}, timeout=5)
        if response.status_code == 200:
            data = response.json()
            return True, data.get('display_name', gene)
        elif response.status_code == 400:
            # Try with alias (e.g., VEGFR2 -> KDR)
            return False, "Not found"
        else:
            return False, f"HTTP {response.status_code}"
    except Exception as e:
        return False, str(e)

def main():
    """Validate genes from MCP collection"""
    input_path = OUTPUT_DIR / "prospective_validation_genes_mcp.csv"
    
    if not input_path.exists():
        print(f"❌ Input file not found: {input_path}")
        return
    
    df = pd.read_csv(input_path)
    print(f"📊 Validating {len(df)} candidate genes...")
    
    # Known real genes (from results)
    known_real = {'UGT1A1', 'TPMT', 'DPYD'}
    
    validated = []
    for _, row in df.iterrows():
        gene = row['gene']
        
        # Skip if known real
        if gene in known_real:
            validated.append({
                **row.to_dict(),
                'validated': True,
                'validation_method': 'Known PGx gene'
            })
            continue
        
        # Skip obvious common words
        common_words = {
            'SCALE', 'LARGE', 'AGENT', 'LIKE', 'RARE', 'SHOWS', 'POST', 'LACK',
            'DUE', 'USED', 'OFTEN', 'VIRAL', 'BEEN', 'PLUS', 'LINE', 'DOSES',
            'RAPID', 'OFFER', 'COVID', 'FREE', 'LOAD', 'SIDE', 'OBESE', 'BROAD',
            'TOPIC', 'MADE', 'SMITH', 'FATTY', 'LINKS', 'RCTS', 'QUERY', 'ACID',
            'LET', 'CROSS', 'BILE', 'DIET', 'PHYLA', 'MAJOR', 'GUT', 'FIELD',
            'SHIFT', 'SHOW', 'NEXT', 'TREND', 'REAL', 'INTER'
        }
        
        if gene in common_words:
            continue
        
        # Validate against Ensembl
        is_valid, reason = validate_gene_ensembl(gene)
        
        if is_valid:
            validated.append({
                **row.to_dict(),
                'validated': True,
                'validation_method': f'Ensembl: {reason}'
            })
            print(f"  ✅ {gene}: {reason}")
        else:
            # Still include but mark as unvalidated
            validated.append({
                **row.to_dict(),
                'validated': False,
                'validation_method': 'Not found in Ensembl'
            })
        
        time.sleep(0.1)  # Rate limiting
    
    # Create validated DataFrame
    validated_df = pd.DataFrame(validated)
    
    # Sort by validated status and priority score
    validated_df = validated_df.sort_values(
        ['validated', 'priority_score'],
        ascending=[False, False]
    )
    
    # Save validated results
    output_path = OUTPUT_DIR / "prospective_validation_genes_validated.csv"
    validated_df.to_csv(output_path, index=False)
    print(f"\n💾 Saved validated results to: {output_path}")
    
    # Show validated genes
    validated_only = validated_df[validated_df['validated'] == True]
    print(f"\n📊 Validated genes: {len(validated_only)}")
    print(f"\nTop validated genes:")
    for i, (_, row) in enumerate(validated_only.head(20).iterrows(), 1):
        print(f"  {i:2d}. {row['gene']:10s} | Score: {row['priority_score']:3d} | "
              f"Trials: {row['n_trials']:2d} | Papers: {row['n_papers']:2d} | "
              f"Method: {row['validation_method']}")
    
    # Create final curated list (top 15 validated)
    curated = validated_only.head(15)
    curated_path = OUTPUT_DIR / "prospective_validation_genes_final.csv"
    curated.to_csv(curated_path, index=False)
    print(f"\n💾 Saved final curated list (top 15 validated) to: {curated_path}")
    
    print(f"\n✅ Validation complete!")
    print(f"  Total candidates: {len(df)}")
    print(f"  Validated: {len(validated_only)}")
    print(f"  Final curated: {len(curated)}")

if __name__ == "__main__":
    main()
