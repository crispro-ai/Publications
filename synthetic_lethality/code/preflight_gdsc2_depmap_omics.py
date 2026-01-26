#!/usr/bin/env python3
"""Preflight: join DepMap Model.csv ↔ GDSC2 ↔ OmicsSomaticMutations for the preclinical SL benchmark.

Purpose (deliverable hygiene):
- Prove the join keys exist and quantify coverage.
- Quantify label distribution for PARP/ATR/WEE1/DNA-PK vs NONE under a transparent rule.
- Write a small JSON receipt under publications/synthetic_lethality/results/.
"""

from __future__ import annotations

import argparse
import json
import os
from collections import Counter
from typing import Dict, Optional

import pandas as pd


PARP_DRUGS = {"Olaparib", "Niraparib", "Talazoparib", "Rucaparib", "Veliparib"}
ATR_DRUGS = {"AZD6738", "VE-822", "VE821"}
WEE1_DRUGS = {"MK-1775"}  # AZD1775 often appears as MK-1775 in GDSC
DNAPK_DRUGS = {"NU7441"}

DRUG_TO_CLASS: Dict[str, str] = {}
for d in PARP_DRUGS:
    DRUG_TO_CLASS[d] = "PARP"
for d in ATR_DRUGS:
    DRUG_TO_CLASS[d] = "ATR"
for d in WEE1_DRUGS:
    DRUG_TO_CLASS[d] = "WEE1"
for d in DNAPK_DRUGS:
    DRUG_TO_CLASS[d] = "DNA_PK"


def safe_mkdir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def normalize_cosmic_id(x) -> Optional[str]:
    try:
        if pd.isna(x):
            return None
        return str(int(float(x)))
    except Exception:
        return None


def compute_label_from_z(
    z_by_class: Dict[str, float],
    z_sensitive_threshold: float,
    min_margin: float,
) -> str:
    """Label rule (transparent, preclinical).

    - Compute mean Z_SCORE per drug class for each cell line.
    - Pick class with minimum (most negative) mean Z.
    - Require: best_z <= z_sensitive_threshold, else NONE.
    - Require: (second_best_z - best_z) >= min_margin, else NONE (ambiguous).
    """
    if not z_by_class:
        return "NONE"

    items = [(k, float(v)) for k, v in z_by_class.items() if v is not None]
    if not items:
        return "NONE"

    items.sort(key=lambda kv: kv[1])  # more negative = more sensitive
    best_class, best_z = items[0]
    if best_z > z_sensitive_threshold:
        return "NONE"

    if len(items) >= 2:
        second_z = items[1][1]
        if (second_z - best_z) < min_margin:
            return "NONE"

    return best_class


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--z_sensitive_threshold", type=float, default=-0.8)
    ap.add_argument("--min_margin", type=float, default=0.25)
    ap.add_argument("--max_lines", type=int, default=5000, help="Cap number of ModelIDs analyzed for fast preflight.")
    ap.add_argument("--out", type=str, default="gdsc2_depmap_omics_preflight.json")
    args = ap.parse_args()

    root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    data_dir = os.path.join(root, "data")
    results_dir = os.path.join(root, "results")
    safe_mkdir(results_dir)

    gdsc_path = os.path.join(data_dir, "GDSC2_fitted_dose_response_27Oct23.xlsx")
    omics_path = os.path.join(data_dir, "OmicsSomaticMutations.csv")
    model_path = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "..", "..", "data", "depmap", "Model.csv")
    )

    for p in (gdsc_path, omics_path, model_path):
        if not os.path.exists(p):
            raise FileNotFoundError(p)

    model_df = pd.read_csv(
        model_path,
        usecols=["ModelID", "COSMICID", "OncotreeLineage"],
        low_memory=False,
    ).dropna(subset=["COSMICID", "ModelID"])
    model_df["COSMIC_ID"] = model_df["COSMICID"].apply(normalize_cosmic_id)
    model_df = model_df.dropna(subset=["COSMIC_ID"])
    model_df["ModelID"] = model_df["ModelID"].astype(str)
    model_df["OncotreeLineage"] = model_df["OncotreeLineage"].astype(str)
    model_df = model_df[["ModelID", "COSMIC_ID", "OncotreeLineage"]].drop_duplicates()

    usecols_g = ["COSMIC_ID", "DRUG_NAME", "AUC", "Z_SCORE"]
    gdsc = pd.read_excel(gdsc_path, engine="openpyxl", usecols=usecols_g)
    gdsc["COSMIC_ID"] = gdsc["COSMIC_ID"].apply(normalize_cosmic_id)
    gdsc = gdsc.dropna(subset=["COSMIC_ID", "DRUG_NAME"])
    gdsc = gdsc[gdsc["DRUG_NAME"].isin(set(DRUG_TO_CLASS.keys()))].copy()
    gdsc["drug_class"] = gdsc["DRUG_NAME"].map(DRUG_TO_CLASS)

    gdsc = gdsc.merge(model_df, on="COSMIC_ID", how="inner")

    classes_per_line = gdsc.groupby("ModelID")["drug_class"].nunique().sort_values(ascending=False)
    candidate_ids = classes_per_line.index.astype(str).tolist()[: max(1, int(args.max_lines))]
    gdsc = gdsc[gdsc["ModelID"].astype(str).isin(set(candidate_ids))].copy()

    labels: Dict[str, str] = {}
    lineage_by_id: Dict[str, str] = {}
    for mid, g in gdsc.groupby("ModelID"):
        mid = str(mid)
        lineage_by_id[mid] = str(g["OncotreeLineage"].iloc[0])
        z_by_class = g.groupby("drug_class")["Z_SCORE"].mean().to_dict()
        labels[mid] = compute_label_from_z(
            z_by_class=z_by_class,
            z_sensitive_threshold=float(args.z_sensitive_threshold),
            min_margin=float(args.min_margin),
        )

    label_counts = Counter(labels.values())
    lineage_counts = Counter(lineage_by_id.values())

    # Omics coverage estimate: stream and count unique ModelID hits
    want = set(labels.keys())
    seen = set()
    for chunk in pd.read_csv(omics_path, usecols=["ModelID"], chunksize=300000):
        chunk["ModelID"] = chunk["ModelID"].astype(str)
        hit = set(chunk[chunk["ModelID"].isin(want)]["ModelID"].unique().tolist())
        if hit:
            seen |= hit
        if len(seen) >= len(want):
            break

    receipt = {
        "inputs": {
            "gdsc_path": os.path.relpath(gdsc_path, root),
            "omics_path": os.path.relpath(omics_path, root),
            "model_path": os.path.relpath(model_path, os.path.abspath(os.path.join(root, "..", ".."))),
            "drug_classes": sorted(set(DRUG_TO_CLASS.values())),
            "z_sensitive_threshold": float(args.z_sensitive_threshold),
            "min_margin": float(args.min_margin),
            "max_lines": int(args.max_lines),
        },
        "counts": {
            "n_gdsc_rows_after_filter": int(len(gdsc)),
            "n_candidate_model_ids": int(len(labels)),
            "n_with_omics_mutations": int(len(seen)),
            "n_missing_omics_mutations": int(len(labels) - len(seen)),
        },
        "label_distribution": dict(label_counts),
        "top_lineages": dict(lineage_counts.most_common(15)),
        "notes": [
            "This is a preclinical benchmark (cell-line outcomes).",
            "Label is derived from mean GDSC2 Z_SCORE per drug class with ambiguity gating.",
            "Next step: build a balanced evaluation split and run S/P/(DepMap) predictors with Evo2 scoring.",
        ],
    }

    out_path = os.path.join(results_dir, args.out)
    with open(out_path, "w") as f:
        json.dump(receipt, f, indent=2)

    print("Wrote preflight receipt:", out_path)
    print("label_distribution:", receipt["label_distribution"])
    print("n_with_omics_mutations:", receipt["counts"]["n_with_omics_mutations"], "/", receipt["counts"]["n_candidate_model_ids"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
