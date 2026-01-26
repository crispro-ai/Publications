#!/usr/bin/env python3
"""
STEP 2: Merge all TCGA-OV data sources
- Step 1 extracted data (BRCA, TMB, clinical)
- HRD from TCGA.HRD_withSampleID.txt
- MSI/TMB from tcga_ov_enriched_v2.json
- Output: One clean analysis table
"""

import pandas as pd
import json
import numpy as np
from pathlib import Path
import re

# Paths
DATA_DIR = Path("/Users/fahadkiani/Desktop/development/crispr-assistant-main/publications/sporadic_cancer/data")
ENRICHED_JSON = Path("/Users/fahadkiani/Desktop/development/crispr-assistant-main/oncology-coPilot/oncology-backend-minimal/biomarker_enriched_cohorts/data/tcga_ov_enriched_v2.json")
STEP1_OUTPUT = Path("/Users/fahadkiani/Desktop/development/crispr-assistant-main/publications/sporadic_cancer/submission_aacr/results/step1_extracted_data.csv")
OUTPUT_DIR = Path("/Users/fahadkiani/Desktop/development/crispr-assistant-main/publications/sporadic_cancer/submission_aacr/results")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

print("=" * 80)
print("STEP 2: MERGING ALL TCGA-OV DATA SOURCES")
print("=" * 80)

def _parse_wide_hrd_file(hrd_path: Path) -> pd.DataFrame:
    """
    Parse TCGA.HRD_withSampleID.txt, which is NOT a normal tabular file.
    It's a wide matrix: first row is sample IDs, subsequent rows are metrics
    (ai1, lst1, hrd-loh, HRD, ...).
    
    The file has inconsistent whitespace (sometimes missing delimiters), so we parse via regex.
    
    Returns: DataFrame with columns [sample_id, patient_id, hrd_score]
    """
    text = hrd_path.read_text(errors="ignore").splitlines()
    if not text:
        raise ValueError("HRD file empty")
    
    header = text[0]
    sample_ids = re.findall(r"TCGA-[0-9A-Z]{2}-[0-9A-Z]{4}-[0-9A-Z]{2}", header)
    if not sample_ids:
        raise ValueError("Could not extract TCGA sample IDs from HRD header row")
    
    # Find the HRD total row. Important: avoid matching 'hrd-loh' etc.
    hrd_row = None
    for line in text[1:]:
        if re.match(r"(?i)^HRD\s", line.strip()):
            hrd_row = line
            break
    if hrd_row is None:
        raise ValueError("Could not find 'HRD' row in HRD file")
    
    # Extract numeric values after the row label
    parts = hrd_row.strip().split()
    if len(parts) < 2:
        raise ValueError(f"HRD row too short to parse; row_preview={repr(hrd_row[:120])}")
    # parts[0] == 'HRD'
    values = []
    for tok in parts[1:]:
        if re.fullmatch(r"\d+", tok):
            values.append(float(tok))
    if not values:
        raise ValueError(f"Could not extract HRD numeric values from HRD row; row_preview={repr(hrd_row[:120])}")
    
    n = min(len(sample_ids), len(values))
    if len(sample_ids) != len(values):
        print(f"  ⚠️ HRD parse length mismatch: sample_ids={len(sample_ids)} values={len(values)}; using first n={n}")
    
    df = pd.DataFrame({
        "sample_id": sample_ids[:n],
        "hrd_score": values[:n],
    })
    df["patient_id"] = df["sample_id"].str[:12]
    return df

# 1. Load Step 1 data
print("\n[1/4] Loading Step 1 extracted data...")
step1_df = pd.read_csv(STEP1_OUTPUT)
print(f"  ✓ Loaded {len(step1_df)} patients from Step 1")

# 2. Load HRD data
print("\n[2/4] Loading HRD scores...")
hrd_file = DATA_DIR / "TCGA.HRD_withSampleID.txt"
if not hrd_file.exists():
    raise FileNotFoundError(f"HRD file not found: {hrd_file}")

try:
    hrd_long = _parse_wide_hrd_file(hrd_file)
    hrd_by_patient = hrd_long.groupby("patient_id")["hrd_score"].mean().reset_index()
    print(f"  ✓ Parsed HRD totals for {len(hrd_by_patient)} patients")
    print(f"  ✓ HRD range: {hrd_by_patient['hrd_score'].min():.1f} - {hrd_by_patient['hrd_score'].max():.1f}")
except Exception as e:
    print(f"  ⚠️ HRD file parse failed; will rely on enriched hrd_proxy only. Reason: {e}")
    hrd_by_patient = pd.DataFrame(columns=["patient_id", "hrd_score"])

# 3. Load enriched cohort JSON
print("\n[3/4] Loading enriched cohort (MSI/TMB)...")
with open(ENRICHED_JSON, 'r') as f:
    enriched_data = json.load(f)

patients_list = enriched_data.get("cohort", {}).get("patients", [])
if not isinstance(patients_list, list) or not patients_list:
    raise ValueError("Expected enriched_data['cohort']['patients'] to be a non-empty list")

enriched_df = pd.DataFrame(patients_list)
print(f"  ✓ Loaded {len(enriched_df)} patients from enriched cohort")

# Flatten outcomes if present
if "outcomes" in enriched_df.columns:
    outcomes_df = pd.json_normalize(enriched_df["outcomes"]).add_prefix("outcomes_")
    enriched_df = pd.concat([enriched_df.drop(columns=["outcomes"]), outcomes_df], axis=1)

# Extract MSI/TMB/HRD proxy fields from enriched data
needed_cols = [
    "patient_id",
    "tmb",
    "msi_status",
    "msi_score_mantis",
    "msi_sensor_score",
    "hrd_proxy",
    "brca_somatic",
    "germline_brca_status",
    "outcomes_os_days",
    "outcomes_os_event",
    "outcomes_pfs_days",
    "outcomes_pfs_event",
]
available_cols = [c for c in needed_cols if c in enriched_df.columns]
enriched_subset = enriched_df[available_cols].copy()

if "tmb" in enriched_subset.columns:
    enriched_subset = enriched_subset.rename(columns={"tmb": "tmb_enriched"})

print(f"  ✓ MSI status counts: {enriched_subset['msi_status'].value_counts(dropna=False).to_dict() if 'msi_status' in enriched_subset.columns else {}}")
print(f"  ✓ TMB (enriched) available: {enriched_subset['tmb_enriched'].notna().sum() if 'tmb_enriched' in enriched_subset.columns else 0} patients")
print(f"  ✓ HRD proxy available: {enriched_subset['hrd_proxy'].notna().sum() if 'hrd_proxy' in enriched_subset.columns else 0} patients")

# 4. Merge everything
print("\n[4/4] Merging all data sources...")
merged = step1_df.copy()

# Add stage + sample-level TMB if available (from ov_tcga_pub clinical sample file)
try:
    clinical_sample_path = DATA_DIR / "ov_tcga_pub" / "data_clinical_sample.txt"
    if clinical_sample_path.exists():
        cs = pd.read_csv(clinical_sample_path, sep="\t", skiprows=4, low_memory=False)
        cs = cs.rename(columns={"PATIENT_ID": "patient_id", "TUMOR_STAGE_2009": "tumor_stage_2009", "TMB_NONSYNONYMOUS": "tmb_nonsynonymous"})
        keep_cols = [c for c in ["patient_id", "tumor_stage_2009", "tmb_nonsynonymous"] if c in cs.columns]
        cs = cs[keep_cols].copy()
        # Aggregate to patient level
        agg = {}
        if "tumor_stage_2009" in cs.columns:
            agg["tumor_stage_2009"] = lambda x: next((v for v in x if pd.notna(v)), np.nan)
        if "tmb_nonsynonymous" in cs.columns:
            agg["tmb_nonsynonymous"] = "mean"
        cs_by_patient = cs.groupby("patient_id").agg(agg).reset_index()
        merged = merged.merge(cs_by_patient, on="patient_id", how="left")
        print(f"  ✓ Added tumor_stage_2009 for {merged['tumor_stage_2009'].notna().sum() if 'tumor_stage_2009' in merged.columns else 0} patients")
    else:
        print("  ⚠️ clinical sample file not found; skipping tumor_stage_2009")
except Exception as e:
    print(f"  ⚠️ Failed to merge clinical sample fields (stage/TMB_nonsynonymous): {e}")

# Merge HRD
merged = merged.merge(hrd_by_patient, on='patient_id', how='left')
print(f"  ✓ HRD merged: {merged['hrd_score'].notna().sum()} patients have HRD")

# Merge enriched data (MSI/TMB)
merged = merged.merge(enriched_subset, on='patient_id', how='left')
print(f"  ✓ Enriched data merged: {merged['msi_status'].notna().sum()} patients have MSI status")

# Prefer enriched TMB if available, otherwise use computed TMB
merged['tmb_final'] = merged['tmb_enriched'].fillna(merged['tmb_mut_per_mb'])
merged['tmb_source'] = merged.apply(
    lambda row: 'enriched' if pd.notna(row['tmb_enriched']) else ('computed' if pd.notna(row['tmb_mut_per_mb']) else 'missing'),
    axis=1
)

# HRD: prefer parsed HRD total, else fall back to enriched hrd_proxy (if present)
if "hrd_proxy" in merged.columns:
    merged["hrd_final"] = merged["hrd_score"].fillna(merged["hrd_proxy"])
    merged["hrd_source"] = merged.apply(
        lambda row: "hrd_total_file" if pd.notna(row["hrd_score"]) else ("enriched_proxy" if pd.notna(row.get("hrd_proxy")) else "missing"),
        axis=1
    )
else:
    merged["hrd_final"] = merged["hrd_score"]
    merged["hrd_source"] = merged["hrd_score"].apply(lambda x: "hrd_total_file" if pd.notna(x) else "missing")

# 5. Save merged table
output_file = OUTPUT_DIR / "tcga_ov_complete_analysis_table.csv"
merged.to_csv(output_file, index=False)
print(f"\n✓ Saved complete analysis table to: {output_file}")

# Summary
print("\n" + "=" * 80)
print("STEP 2 COMPLETE: MERGED DATA SUMMARY")
print("=" * 80)
print(f"Total patients: {len(merged)}")
print(f"BRCA mutations: {merged['has_brca_mutation'].sum()}")
print(f"TMB available: {merged['tmb_final'].notna().sum()} (source: {merged['tmb_source'].value_counts().to_dict()})")
print(f"HRD final available: {merged['hrd_final'].notna().sum()} (source: {merged['hrd_source'].value_counts().to_dict()})")
print(f"MSI status: {merged['msi_status'].notna().sum()}")
summary_fields = [c for c in ['tumor_stage_2009', 'os_status', 'os_months', 'dfs_status', 'dfs_months', 'platinum_status'] if c in merged.columns]
print(f"Clinical fields present: {summary_fields}")
if summary_fields:
    print(f"Clinical non-null counts: {merged[summary_fields].notna().sum().to_dict()}")
print("\nNEXT STEP: Generate threshold sensitivity analysis")
print("=" * 80)
