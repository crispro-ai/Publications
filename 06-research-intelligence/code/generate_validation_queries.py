#!/usr/bin/env python3
"""
Sprint 4: Generate 100 Validation Queries

Extract 100 compound-disease pairs from existing data:
- 40 from Dosing Guidance (drug-gene pairs)
- 40 from Synthetic Lethality (mutation-drug pairs)
- 20 from Hypothesis Validator (food-cancer pairs)

Output: validation_queries_100.json with queries + source data
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime

# Add parent directories to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

def load_dosing_guidance_cases() -> List[Dict[str, Any]]:
    """Load 40 cases from Dosing Guidance validation data."""
    # Try curated file first (has actual drug names), then fallback to unified
    possible_paths = [
        project_root / "oncology-coPilot" / "oncology-backend-minimal" / "dosing_guidance_validation" / "data" / "extraction_all_genes_auto_curated.json",
        project_root / "oncology-coPilot" / "oncology-backend-minimal" / "dosing_guidance_validation" / "data" / "extraction_all_genes_curated.json",
        project_root / "oncology-coPilot" / "oncology-backend-minimal" / "dosing_guidance_validation" / "data" / "unified_validation_cases.json",
    ]
    
    all_cases = []
    
    for path in possible_paths:
        if path.exists():
            print(f"✅ Loading dosing guidance from: {path}")
            with open(path, 'r') as f:
                data = json.load(f)
            
            # Extract cases
            cases = []
            if isinstance(data, list):
                cases = [c for c in data if isinstance(c, dict) and c.get('gene')]
            elif isinstance(data, dict):
                # Try different keys
                if 'sources' in data:
                    # Nested structure: sources -> pubmed/pharmgkb -> list of cases
                    for source_type, source_cases in data.get('sources', {}).items():
                        if isinstance(source_cases, list):
                            cases.extend([c for c in source_cases if isinstance(c, dict) and c.get('gene')])
                elif 'cases' in data:
                    cases = [c for c in data['cases'] if isinstance(c, dict) and c.get('gene')]
                elif 'validation_cases' in data:
                    cases = [c for c in data['validation_cases'] if isinstance(c, dict) and c.get('gene')]
                else:
                    # Try to extract from values
                    for value in data.values():
                        if isinstance(value, list):
                            cases.extend([c for c in value if isinstance(c, dict) and c.get('gene')])
            
            all_cases.extend(cases)
            
            # If we got cases from curated file, prioritize it
            if path.name == 'extraction_all_genes_auto_curated.json' and cases:
                break
    
    # Deduplicate by case_id or pmid
    seen = set()
    unique_cases = []
    for case in all_cases:
        case_id = case.get('case_id') or case.get('pmid') or str(case)
        if case_id not in seen:
            seen.add(case_id)
            unique_cases.append(case)
    
    # Filter: must have gene, drug can be extracted later
    valid_cases = [c for c in unique_cases if c.get('gene') and c.get('gene', '').upper() in ['DPYD', 'UGT1A1', 'TPMT', 'NUDT15']]
    
    return valid_cases[:40] if valid_cases else []


def load_synthetic_lethality_cases() -> List[Dict[str, Any]]:
    """Load 40 cases from Synthetic Lethality validation data."""
    possible_paths = [
        project_root / "publications" / "synthetic_lethality" / "data" / "test_cases_100.json",
        project_root / "scripts" / "benchmark_sl" / "test_cases_100.json",
        project_root / "synthetic_lethality" / "data" / "test_cases_100.json",
    ]
    
    for path in possible_paths:
        if path.exists():
            print(f"✅ Loading synthetic lethality from: {path}")
            with open(path, 'r') as f:
                data = json.load(f)
            
            # Extract cases (limit to 40)
            cases = data if isinstance(data, list) else data.get('cases', []) or data.get('test_cases', [])
            return cases[:40]
    
    print("⚠️ Synthetic lethality data not found, using empty list")
    return []


def load_hypothesis_validator_cases() -> List[Dict[str, Any]]:
    """Load 20 cases from Hypothesis Validator food targets."""
    possible_paths = [
        project_root / ".cursor" / "ayesha" / "hypothesis_validator" / "data" / "food_targets.json",
        project_root / "hypothesis_validator" / "data" / "food_targets.json",
    ]
    
    for path in possible_paths:
        if path.exists():
            print(f"✅ Loading hypothesis validator from: {path}")
            try:
                with open(path, 'r') as f:
                    data = json.load(f)
            except:
                print(f"⚠️ Could not read {path}, using fallback")
                break
            
            # Extract food-cancer pairs (limit to 20)
            items = []
            
            if isinstance(data, list):
                items = data
            elif isinstance(data, dict):
                # Check for nested structure: {'foods': [list of compounds]}
                if 'foods' in data and isinstance(data['foods'], list):
                    # Extract individual compounds from nested list
                    for food_dict in data['foods']:
                        if isinstance(food_dict, dict) and food_dict.get('compound'):
                            items.append(food_dict)
                    print(f"  📊 Found {len(items)} compounds in nested structure")
                elif 'food_targets' in data:
                    items = data['food_targets'] if isinstance(data['food_targets'], list) else []
                elif 'targets' in data:
                    items = data['targets'] if isinstance(data['targets'], list) else []
                else:
                    # Check if it's a dict of food -> data structures
                    for key, value in list(data.items())[:20]:
                        if isinstance(value, dict):
                            # Extract compound name from structure
                            compound = value.get('compound', key)
                            items.append({'compound': compound, 'data': value})
                        elif isinstance(value, list):
                            items.append({'compound': key, 'targets': value})
                        else:
                            items.append({'compound': key, 'value': value})
            
            # Extract actual compound names and cancer types
            valid_items = []
            for item in items[:20]:
                if isinstance(item, dict):
                    compound = item.get('compound') or item.get('name') or list(item.keys())[0] if item else None
                    if compound and compound.lower() not in ['unknown', '']:
                        # Extract cancer type if available
                        data_dict = item.get('data', item)
                        ovarian_data = data_dict.get('ovarian_specific_data', {})
                        if ovarian_data:
                            valid_items.append({
                                'compound': compound,
                                'cancer': 'ovarian cancer',
                                'data': data_dict
                            })
                        else:
                            valid_items.append({
                                'compound': compound,
                                'cancer': 'cancer',  # Default
                                'data': data_dict
                            })
                elif isinstance(item, str):
                    if item.lower() not in ['unknown', '']:
                        valid_items.append({'compound': item, 'cancer': 'cancer'})
            
            if valid_items:
                print(f"  ✅ Extracted {len(valid_items)} valid compounds")
                return valid_items[:20]
    
    # Fallback: Use common cancer compounds from literature
    fallback_foods = [
        {'compound': 'curcumin', 'cancer': 'ovarian cancer'},
        {'compound': 'resveratrol', 'cancer': 'breast cancer'},
        {'compound': 'green tea', 'cancer': 'ovarian cancer'},
        {'compound': 'EGCG', 'cancer': 'ovarian cancer'},
        {'compound': 'vitamin D', 'cancer': 'ovarian cancer'},
        {'compound': 'omega-3', 'cancer': 'ovarian cancer'},
        {'compound': 'folate', 'cancer': 'ovarian cancer'},
        {'compound': 'NAC', 'cancer': 'ovarian cancer'},
        {'compound': 'quercetin', 'cancer': 'breast cancer'},
        {'compound': 'anthocyanin', 'cancer': 'breast cancer'},
        {'compound': 'lycopene', 'cancer': 'prostate cancer'},
        {'compound': 'sulforaphane', 'cancer': 'breast cancer'},
        {'compound': 'genistein', 'cancer': 'breast cancer'},
        {'compound': 'turmeric', 'cancer': 'ovarian cancer'},
        {'compound': 'fish oil', 'cancer': 'ovarian cancer'},
        {'compound': 'folic acid', 'cancer': 'ovarian cancer'},
        {'compound': 'vitamin B12', 'cancer': 'ovarian cancer'},
        {'compound': 'resveratrol', 'cancer': 'ovarian cancer'},
        {'compound': 'green tea extract', 'cancer': 'ovarian cancer'},
        {'compound': 'turmeric extract', 'cancer': 'ovarian cancer'}
    ]
    
    print("⚠️ Hypothesis validator data not found, using fallback compounds")
    return fallback_foods[:20]


def get_drug_for_gene(gene: str) -> str:
    """Get default drug for pharmacogene (from validation scripts)."""
    DRUG_MAPPING = {
        "DPYD": "5-fluorouracil",  # Will extract capecitabine from text if present
        "UGT1A1": "irinotecan",
        "TPMT": "6-mercaptopurine",
        "NUDT15": "6-mercaptopurine"
    }
    return DRUG_MAPPING.get(gene.upper(), None)


def create_query_from_dosing_case(case: Dict[str, Any], query_id: int) -> Dict[str, Any]:
    """Create a research query from a dosing guidance case."""
    if not isinstance(case, dict):
        return None
    
    gene = case.get('gene', case.get('gene_name', ''))
    if not gene or gene.lower() in ['unknown gene', 'unknown', '']:
        return None
    
    # Extract drug name (try multiple fields, ensure it's not "Unknown")
    drug = (case.get('drug') or 
            case.get('drug_name') or 
            case.get('medication') or 
            case.get('fetched_drug'))
    
    if not drug or drug.lower() in ['unknown drug', 'unknown', '']:
        # Try to extract from title/abstract if available
        title = case.get('fetched_title', '') or case.get('title', '')
        abstract = case.get('fetched_abstract', '') or case.get('abstract', '')
        text = f"{title} {abstract}".lower()
        
        # Common drug patterns (prioritize more specific first)
        drug_patterns = {
            'capecitabine': ['capecitabine', 'xeloda'],
            '5-fluorouracil': ['5-fluorouracil', '5-fu', 'fluorouracil', 'fluoropyrimidine'],
            'irinotecan': ['irinotecan', 'camptosar'],
            'mercaptopurine': ['mercaptopurine', '6-mp', '6-mercaptopurine'],
            'azathioprine': ['azathioprine'],
            'tegafur': ['tegafur']
        }
        
        for drug_name, patterns in drug_patterns.items():
            if any(p in text for p in patterns):
                drug = drug_name
                break
        
        # Fallback: Use gene-based drug mapping
        if not drug or drug.lower() in ['unknown drug', 'unknown', '']:
            drug = get_drug_for_gene(gene)
        
        if not drug or drug.lower() in ['unknown drug', 'unknown', '']:
            return None  # Skip if we can't find a drug
    
    gene = case.get('gene', case.get('gene_name', 'Unknown gene'))
    variant = (case.get('variant') or 
               case.get('variant_name') or 
               case.get('hgvs_p') or 
               case.get('hgvs_c') or 
               case.get('diplotype') or '')
    
    # Determine disease from context or default
    disease = (case.get('disease') or 
               case.get('cancer_type') or 
               case.get('condition') or 
               'cancer')
    
    # Create query
    if variant and variant != '':
        question = f"How does {drug} interact with {gene} {variant} in {disease}?"
    else:
        question = f"How does {drug} interact with {gene} in {disease}?"
    
    return {
        "query_id": f"DG_{query_id:03d}",
        "question": question,
        "source": "dosing_guidance",
        "source_data": {
            "case_id": case.get('case_id', case.get('id', f'DG_{query_id}')),
            "pmid": case.get('pmid', case.get('source_pmid', None)),
            "drug": drug,
            "gene": gene,
            "variant": variant,
            "disease": disease,
            "toxicity_occurred": case.get('toxicity_occurred', None),
            "toxicity_confidence": case.get('toxicity_confidence', None)
        },
        "context": {
            "disease": str(disease).lower().replace(' ', '_'),
            "treatment_line": "L1",
            "biomarkers": {str(gene): variant if variant else "WILDTYPE"}
        }
    }


def create_query_from_sl_case(case: Dict[str, Any], query_id: int) -> Dict[str, Any]:
    """Create a research query from a synthetic lethality case."""
    if not isinstance(case, dict):
        return None
    
    # Extract drug from ground_truth
    ground_truth = case.get('ground_truth', {})
    if isinstance(ground_truth, dict):
        effective_drugs = ground_truth.get('effective_drugs', [])
        drug = effective_drugs[0] if effective_drugs else 'PARP inhibitor'
    else:
        drug = 'PARP inhibitor'
    
    # Extract mutation info
    mutations = case.get('mutations', [])
    if mutations and isinstance(mutations, list) and len(mutations) > 0:
        first_mutation = mutations[0] if isinstance(mutations[0], dict) else {}
        gene = first_mutation.get('gene', case.get('gene', 'Unknown'))
        mutation = first_mutation.get('hgvs_p', first_mutation.get('variant', f"{gene} mutation"))
    else:
        gene = case.get('gene', 'Unknown')
        mutation = f"{gene} mutation"
    
    # Extract disease
    disease = case.get('disease', case.get('cancer_type', 'ovarian cancer'))
    if isinstance(disease, str):
        disease = disease.replace('_', ' ')
    
    question = f"What mechanisms does {drug} target in {disease}?"
    if mutation and mutation != f"{gene} mutation":
        question = f"What mechanisms does {drug} target in {disease} with {mutation}?"
    
    return {
        "query_id": f"SL_{query_id:03d}",
        "question": question,
        "source": "synthetic_lethality",
        "source_data": {
            "case_id": case.get('case_id', f'SL_{query_id}'),
            "drug": drug,
            "gene": gene,
            "mutation": mutation,
            "disease": disease,
            "ground_truth": ground_truth,
            "mutations": mutations
        },
        "context": {
            "disease": str(disease).lower().replace(' ', '_'),
            "treatment_line": "L1",
            "biomarkers": {str(gene): "MUTATED"}
        }
    }


def create_query_from_food_case(case: Any, query_id: int) -> Dict[str, Any]:
    """Create a research query from a hypothesis validator food case."""
    # Handle different data structures
    if isinstance(case, dict):
        food = case.get('food') or case.get('compound') or case.get('name', '')
        # Extract cancer type from nested data if available
        cancer = (case.get('cancer') or 
                 case.get('disease') or 
                 case.get('cancer_type') or
                 case.get('data', {}).get('ovarian_specific_data', {}).get('citation') and 'ovarian' or
                 'cancer')
        targets = case.get('targets', []) or case.get('data', {}).get('B_targets', [])
        pathways = case.get('pathways', [])
    elif isinstance(case, (list, tuple)) and len(case) >= 2:
        food = str(case[0])
        cancer = str(case[1]) if len(case) > 1 else 'cancer'
        targets = case[2] if len(case) > 2 and isinstance(case[2], list) else []
        pathways = case[3] if len(case) > 3 and isinstance(case[3], list) else []
    elif isinstance(case, str):
        food = case
        cancer = 'cancer'
        targets = []
        pathways = []
    else:
        food = str(case)
        cancer = "cancer"
        targets = []
        pathways = []
    
    # Ensure values are valid
    if not food or food.lower() in ['unknown', 'unknown food', '']:
        return None
    
    # Ensure cancer is a string
    if not isinstance(cancer, str):
        cancer = str(cancer) if cancer else 'cancer'
    
    # Default to common cancer types for food queries
    if cancer == 'cancer':
        cancer = 'ovarian cancer'  # Default for food research
    
    question = f"How does {food} help with {cancer}?"
    
    return {
        "query_id": f"HV_{query_id:03d}",
        "question": question,
        "source": "hypothesis_validator",
        "source_data": {
            "food": food,
            "cancer": cancer,
            "targets": targets,
            "pathways": pathways
        },
        "context": {
            "disease": cancer.lower().replace(' ', '_'),
            "treatment_line": "L1",
            "biomarkers": {}
        }
    }


def generate_validation_queries():
    """Generate 100 validation queries from existing data."""
    print("=" * 80)
    print("SPRINT 4: GENERATE 100 VALIDATION QUERIES")
    print("=" * 80)
    
    queries = []
    
    # Load data
    print("\n📊 Loading data sources...")
    dosing_cases = load_dosing_guidance_cases()
    sl_cases = load_synthetic_lethality_cases()
    food_cases = load_hypothesis_validator_cases()
    
    print(f"  - Dosing Guidance: {len(dosing_cases)} cases")
    print(f"  - Synthetic Lethality: {len(sl_cases)} cases")
    print(f"  - Hypothesis Validator: {len(food_cases)} cases")
    
    # Generate queries from dosing guidance (target 40, use all valid)
    print("\n🔬 Generating queries from Dosing Guidance...")
    valid_dg_queries = 0
    for i, case in enumerate(dosing_cases[:40], 1):
        query = create_query_from_dosing_case(case, i)
        if query:  # Skip None results
            queries.append(query)
            valid_dg_queries += 1
            if valid_dg_queries <= 10 or valid_dg_queries % 5 == 0:
                print(f"  ✅ {query['query_id']}: {query['question'][:60]}...")
    
    print(f"  📊 Generated {valid_dg_queries} valid queries from dosing guidance")
    
    # If we don't have enough, try to get more from unified file
    if valid_dg_queries < 40:
        print(f"  ⚠️  Only {valid_dg_queries} queries with drug names, attempting to extract more...")
        # Additional extraction logic already handled in create_query_from_dosing_case
    
    # Generate queries from synthetic lethality (40)
    print("\n🧬 Generating queries from Synthetic Lethality...")
    for i, case in enumerate(sl_cases[:40], 1):
        query = create_query_from_sl_case(case, i)
        if query:  # Skip None results
            queries.append(query)
            print(f"  ✅ {query['query_id']}: {query['question'][:60]}...")
    
    # Generate queries from hypothesis validator (target 20, use all valid)
    print("\n🍎 Generating queries from Hypothesis Validator...")
    valid_hv_queries = 0
    for i, case in enumerate(food_cases[:20], 1):
        query = create_query_from_food_case(case, i)
        if query:  # Skip None results
            queries.append(query)
            valid_hv_queries += 1
            if valid_hv_queries <= 10 or valid_hv_queries % 5 == 0:
                print(f"  ✅ {query['query_id']}: {query['question'][:60]}...")
    
    print(f"  📊 Generated {valid_hv_queries} valid queries from hypothesis validator")
    
    # Save output
    output_dir = Path(__file__).parent.parent / "sprint4_results"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    output_file = output_dir / "validation_queries_100.json"
    
    output = {
        "timestamp": datetime.now().isoformat(),
        "total_queries": len(queries),
        "source_breakdown": {
            "dosing_guidance": len([q for q in queries if q['source'] == 'dosing_guidance']),
            "synthetic_lethality": len([q for q in queries if q['source'] == 'synthetic_lethality']),
            "hypothesis_validator": len([q for q in queries if q['source'] == 'hypothesis_validator'])
        },
        "queries": queries
    }
    
    with open(output_file, 'w') as f:
        json.dump(output, f, indent=2)
    
    print("\n" + "=" * 80)
    print("✅ VALIDATION QUERIES GENERATED")
    print("=" * 80)
    print(f"Total queries: {len(queries)}")
    print(f"Output file: {output_file}")
    print(f"\nBreakdown:")
    print(f"  - Dosing Guidance: {output['source_breakdown']['dosing_guidance']}")
    print(f"  - Synthetic Lethality: {output['source_breakdown']['synthetic_lethality']}")
    print(f"  - Hypothesis Validator: {output['source_breakdown']['hypothesis_validator']}")
    
    return output


if __name__ == "__main__":
    generate_validation_queries()

