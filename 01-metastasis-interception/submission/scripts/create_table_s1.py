#!/usr/bin/env python3
"""
Create Table S1: 38 Primary Metastatic Genes with NCT IDs and PMIDs
"""

import json
import pandas as pd
from pathlib import Path

# Read the rules file
rules_path = Path("/Users/fahadkiani/.cursor/worktrees/crispr-assistant-main/oncology-coPilot/oncology-backend-minimal/api/config/metastasis_rules_v1.0.1.json")
with open(rules_path, 'r') as f:
    rules = json.load(f)

# Collect all genes with their steps, NCT IDs, and PMIDs
gene_data = []

# Process each step
for step_name, step_data in rules['steps'].items():
    # Primary genes
    for gene in step_data.get('primary_genes', []):
        trials = ', '.join(step_data.get('trials', []))
        pmids = ', '.join(step_data.get('pmids', []))
        gene_data.append({
            'Gene': gene,
            'Metastatic_Step': step_name.replace('_', ' ').title(),
            'Gene_Type': 'Primary',
            'NCT_IDs': trials,
            'PMIDs': pmids
        })
    
    # Secondary genes
    for gene in step_data.get('secondary_genes', []):
        trials = ', '.join(step_data.get('trials', []))
        pmids = ', '.join(step_data.get('pmids', []))
        gene_data.append({
            'Gene': gene,
            'Metastatic_Step': step_name.replace('_', ' ').title(),
            'Gene_Type': 'Secondary',
            'NCT_IDs': trials,
            'PMIDs': pmids
        })

# Process gene annotations for additional info
for gene, annotation in rules.get('gene_annotations', {}).items():
    # Update existing entries or add new ones
    for entry in gene_data:
        if entry['Gene'] == gene:
            if annotation.get('trial'):
                entry['NCT_IDs'] = annotation['trial']
            if annotation.get('pmids'):
                entry['PMIDs'] = ', '.join(annotation['pmids'])

# Create DataFrame
df = pd.DataFrame(gene_data)

# Sort by gene, then by step
df = df.sort_values(['Gene', 'Metastatic_Step'])

# Group by gene to combine steps
gene_summary = []
for gene in df['Gene'].unique():
    gene_rows = df[df['Gene'] == gene]
    steps = '; '.join(gene_rows['Metastatic_Step'].unique())
    primary_steps = gene_rows[gene_rows['Gene_Type'] == 'Primary']['Metastatic_Step'].tolist()
    secondary_steps = gene_rows[gene_rows['Gene_Type'] == 'Secondary']['Metastatic_Step'].tolist()
    
    # Collect all NCT IDs and PMIDs
    all_trials = set()
    all_pmids = set()
    for _, row in gene_rows.iterrows():
        if row['NCT_IDs']:
            all_trials.update(row['NCT_IDs'].split(', '))
        if row['PMIDs']:
            all_pmids.update(row['PMIDs'].split(', '))
    
    gene_summary.append({
        'Gene': gene,
        'Metastatic_Steps': steps,
        'Primary_Steps': '; '.join(primary_steps) if primary_steps else '',
        'Secondary_Steps': '; '.join(secondary_steps) if secondary_steps else '',
        'NCT_IDs': ', '.join(sorted(all_trials)) if all_trials else '',
        'PMIDs': ', '.join(sorted(all_pmids)) if all_pmids else ''
    })

df_summary = pd.DataFrame(gene_summary)
df_summary = df_summary.sort_values('Gene')

# Save as CSV
output_dir = Path(__file__).parent.parent / "tables"
output_dir.mkdir(exist_ok=True)
df_summary.to_csv(output_dir / "table_s1_genes_nct_pmid.csv", index=False)

# Also create LaTeX version
latex_table = df_summary.to_latex(index=False, escape=False, longtable=True)
with open(output_dir / "table_s1_genes_nct_pmid.tex", 'w') as f:
    f.write(latex_table)

print(f"✅ Created Table S1:")
print(f"  - CSV: {output_dir / 'table_s1_genes_nct_pmid.csv'}")
print(f"  - LaTeX: {output_dir / 'table_s1_genes_nct_pmid.tex'}")
print(f"  - Total genes: {len(df_summary)}")
print(f"\nFirst 5 rows:")
print(df_summary.head().to_string(index=False))
