#!/usr/bin/env python3
"""
STEP 1: Extract what we can from existing ov_tcga_pub data
- BRCA mutations (from data_mutations.txt)
- Compute TMB from mutations
- Extract clinical fields (stage, age, OS, DFS, PLATINUM_STATUS)
- NO FAKE DATA - only real extraction
"""

import pandas as pd
import numpy as np
from pathlib import Path
import json

# Paths
DATA_DIR = Path("/Users/fahadkiani/Desktop/development/crispr-assistant-main/publications/sporadic_cancer/data/ov_tcga_pub")
OUTPUT_DIR = Path("/Users/fahadkiani/Desktop/development/crispr-assistant-main/publications/sporadic_cancer/submission_aacr/results")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

print("=" * 80)
print("STEP 1: EXTRACTING EXISTING DATA FROM ov_tcga_pub")
print("=" * 80)

# 1. Load mutations
print("\n[1/4] Loading mutations...")
mutations_file = DATA_DIR / "data_mutations.txt"
if not mutations_file.exists():
    raise FileNotFoundError(f"Mutations file not found: {mutations_file}")

# cBioPortal format: skip version header and comment lines
# Find the actual header row (starts with Hugo_Symbol)
with open(mutations_file, 'r') as f:
    for i, line in enumerate(f):
        if line.startswith('Hugo_Symbol'):
            skip_rows = i
            break
    else:
        skip_rows = 0

mutations_df = pd.read_csv(mutations_file, sep="\t", skiprows=skip_rows, low_memory=False)
print(f"  ✓ Loaded {len(mutations_df)} mutations from {mutations_df['Tumor_Sample_Barcode'].nunique()} samples")

# 2. Extract BRCA mutations
print("\n[2/4] Extracting BRCA mutations...")
brca_genes = ["BRCA1", "BRCA2"]
brca_mutations = mutations_df[mutations_df["Hugo_Symbol"].isin(brca_genes)].copy()

brca_mutations["sample_id"] = brca_mutations["Tumor_Sample_Barcode"].astype(str)
brca_mutations["patient_id"] = brca_mutations["sample_id"].str[:12]
brca_by_patient = (
    brca_mutations.groupby("patient_id")
    .agg(
        brca_genes=("Hugo_Symbol", lambda x: ",".join(sorted(set(x)))),
        variant_types=("Variant_Classification", lambda x: ",".join(sorted(set(x)))),
        brca_mutation_count=("Hugo_Symbol", "size"),
    )
    .reset_index()
)
brca_by_patient["has_brca_mutation"] = True

print(f"  ✓ Found BRCA mutations in {len(brca_by_patient)} patients")

# 3. Compute TMB (mutations per Mb)
print("\n[3/4] Computing TMB from mutations...")
# Exome size: ~38 Mb (standard for TMB calculation)
EXOME_SIZE_MB = 38.0

# Count non-silent mutations per sample
non_silent = mutations_df[~mutations_df["Variant_Classification"].isin([
    "Silent", "Intron", "IGR", "5'UTR", "3'UTR", "RNA"
])]

tmb_by_patient = non_silent.groupby("Tumor_Sample_Barcode").size().reset_index(name="mutation_count")
tmb_by_patient["tmb_mut_per_mb"] = tmb_by_patient["mutation_count"] / EXOME_SIZE_MB

# Normalize patient IDs (remove sample suffix if present)
tmb_by_patient["patient_id"] = tmb_by_patient["Tumor_Sample_Barcode"].str[:12]

print(f"  ✓ Computed TMB for {len(tmb_by_patient)} samples")
print(f"  ✓ TMB range: {tmb_by_patient['tmb_mut_per_mb'].min():.2f} - {tmb_by_patient['tmb_mut_per_mb'].max():.2f} mut/Mb")

# 4. Load clinical data
print("\n[4/4] Loading clinical data...")
clinical_file = DATA_DIR / "data_clinical_patient.txt"
if not clinical_file.exists():
    raise FileNotFoundError(f"Clinical file not found: {clinical_file}")

# Skip header rows (usually 4-5 rows)
clinical_df = pd.read_csv(clinical_file, sep="\t", skiprows=4, low_memory=False)
print(f"  ✓ Loaded clinical data for {len(clinical_df)} patients")

# Extract relevant fields
clinical_fields = [
    "PATIENT_ID", "AGE", "AJCC_STAGE", "OS_STATUS", "OS_MONTHS",
    "DFS_STATUS", "DFS_MONTHS", "PLATINUM_STATUS"
]

available_fields = [f for f in clinical_fields if f in clinical_df.columns and f != "PATIENT_ID"]
clinical_subset = clinical_df[["PATIENT_ID"] + available_fields].copy()
clinical_subset = clinical_subset.rename(columns={"PATIENT_ID": "patient_id"})
# Lowercase other columns but keep patient_id
for col in clinical_subset.columns:
    if col != "patient_id":
        clinical_subset = clinical_subset.rename(columns={col: col.lower()})

print(f"  ✓ Extracted fields: {available_fields}")

# 5. Merge everything
print("\n[5/5] Merging data...")
# Start with clinical data as base
merged = clinical_subset.copy()

# Merge BRCA mutations
merged = merged.merge(
    brca_by_patient[["patient_id", "brca_genes", "variant_types", "brca_mutation_count"]],
    on="patient_id",
    how="left"
)
merged["has_brca_mutation"] = merged["brca_genes"].notna()

# Merge TMB (aggregate by patient if multiple samples)
tmb_agg = tmb_by_patient.groupby("patient_id")["tmb_mut_per_mb"].mean().reset_index()
merged = merged.merge(tmb_agg, on="patient_id", how="left")

print(f"  ✓ Merged data for {len(merged)} patients")
print(f"  ✓ BRCA mutations: {merged['has_brca_mutation'].sum()} patients")
print(f"  ✓ TMB computed: {merged['tmb_mut_per_mb'].notna().sum()} patients")

# 6. Save results
output_file = OUTPUT_DIR / "step1_extracted_data.csv"
merged.to_csv(output_file, index=False)
print(f"\n✓ Saved extracted data to: {output_file}")

# Summary
print("\n" + "=" * 80)
print("STEP 1 COMPLETE: EXTRACTED DATA SUMMARY")
print("=" * 80)
print(f"Total patients: {len(merged)}")
print(f"BRCA mutations: {merged['has_brca_mutation'].sum()}")
print(f"TMB computed: {merged['tmb_mut_per_mb'].notna().sum()}")
print(f"Clinical fields: {len(available_fields)}")
print("\nNEXT STEP: Use MCP servers to fetch MSI and HRD data")
print("=" * 80)
