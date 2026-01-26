#!/usr/bin/env python3
"""Validate multiclass synthetic-lethality drug selection on GDSC2 using allele-resolved variants.

Core idea (receipt-driven, not marketing):
- Join GDSC2 dose response (COSMIC_ID) -> DepMap ModelID
- Pull allele-resolved somatic variants from OmicsSomaticMutations (DepMap)
- Score SNVs with deployed Evo2 service (variant-analysis-evo2) to get delta_score
- Aggregate per cell line into mechanism scores for PARP/ATR/WEE1/DNA-PK
- Evaluate predictions vs GDSC2 sensitivity patterns

Notes:
- This uses the deployed Modal app `variant-analysis-evo2` for scoring. That service takes (pos, alt, genome, chrom).
- This script keeps runtime sane by (a) limiting to SNVs and (b) capping variants per cell line.
- Outputs receipts under publications/synthetic_lethality/results/

RUO.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import random
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Tuple

import pandas as pd


# -------------------------
# Drug class mapping
# -------------------------

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


# -------------------------
# Gene sets (mechanistic)
# -------------------------

HRR_GENES = {"BRCA1", "BRCA2", "PALB2", "RAD51C", "RAD51D", "BRIP1", "BARD1", "CDK12"}
BER_GENES = {"MBD4"}
CHECKPOINT_GENES = {"TP53"}
ATR_AXIS_GENES = {"ATR", "CHEK1"}
DNAPK_GENES = {"PRKDC"}
DDR_BROAD = set().union(HRR_GENES, BER_GENES, CHECKPOINT_GENES, ATR_AXIS_GENES, DNAPK_GENES, {"ATM", "CHEK2", "ARID1A"})


# -------------------------
# Utilities
# -------------------------

def safe_mkdir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def normalize_cosmic_id(x) -> Optional[str]:
    try:
        if pd.isna(x):
            return None
        # COSMICID may be float in CSV
        return str(int(float(x)))
    except Exception:
        return None


def drug_class(drug: str) -> Optional[str]:
    return DRUG_TO_CLASS.get(drug)


def delta_to_disruption(delta: Optional[float]) -> Optional[float]:
    if delta is None:
        return None
    # In Evo2 scoring, delta = alt_ll - ref_ll; more negative => more disruptive.
    return max(0.0, -float(delta))


# -------------------------
# Evo2 scorer wrapper
# -------------------------

@dataclass
class Evo2Hit:
    chrom: str
    pos: int
    alt: str
    delta_score: float
    reference: Optional[str] = None
    prediction: Optional[str] = None
    confidence: Optional[float] = None


class Evo2VariantScorer:
    """Thin wrapper around deployed Modal app `variant-analysis-evo2`.

    The deployed signature is:
      analyze_single_variant(pos, alt, genome, chrom)

    Returns dict like:
      { reference, alternative, delta_score, prediction, classification_confidence, position }
    """

    def __init__(self, app_name: str = "variant-analysis-evo2", cls_name: str = "Evo2Model"):
        import modal

        self._modal = modal
        self._cls = modal.Cls.from_name(app_name, cls_name)
        self._obj = self._cls()

    def score_snv(self, chrom: str, pos: int, alt: str, genome: str = "hg38") -> Evo2Hit:
        out = self._obj.analyze_single_variant.remote(int(pos), str(alt).upper(), genome, str(chrom))
        if not isinstance(out, dict) or "delta_score" not in out:
            raise RuntimeError(f"Unexpected response from Evo2 scorer: {type(out)} {str(out)[:200]}")
        return Evo2Hit(
            chrom=str(chrom),
            pos=int(pos),
            alt=str(alt).upper(),
            delta_score=float(out.get("delta_score")),
            reference=out.get("reference"),
            prediction=out.get("prediction"),
            confidence=float(out.get("classification_confidence")) if out.get("classification_confidence") is not None else None,
        )


# -------------------------
# Core pipeline
# -------------------------

@dataclass
class CellLineFeatures:
    model_id: str
    # max disruptions per bucket
    hrr_max: float
    ber_max: float
    checkpoint_max: float
    atr_axis_max: float
    dnapk_max: float
    ddr_broad_max: float
    # for provenance
    n_variants_scored: int
    n_variants_considered: int


def pick_variants_for_cellline(df: pd.DataFrame, max_variants: int) -> pd.DataFrame:
    """Choose a bounded set of variants to score for a cell line.

    Heuristic ordering (cheap):
    - keep SNVs only (variant-analysis-evo2 supports alt-only)
    - prioritize HIGH impact if present, else MODERATE, else anything
    """
    x = df.copy()
    # filter SNVs with 1bp alt
    x = x[
        (x["VariantType"].astype(str).str.lower() == "snv")
        & (x["Alt"].astype(str).str.len() == 1)
    ]
    if len(x) == 0:
        return x

    impact = x.get("VepImpact")
    if impact is not None:
        imp = x["VepImpact"].astype(str).str.upper()
        rank = imp.map({"HIGH": 0, "MODERATE": 1, "LOW": 2}).fillna(3)
        x = x.assign(_rank=rank).sort_values(["_rank"])  # stable
        x = x.drop(columns=["_rank"])

    return x.head(max_variants)


def compute_features_for_cellline(
    scorer: Evo2VariantScorer,
    model_id: str,
    muts: pd.DataFrame,
    max_variants: int,
    cache: Dict[str, Dict],
    genome: str = "hg38",
) -> CellLineFeatures:
    subset = pick_variants_for_cellline(muts, max_variants=max_variants)
    n_considered = int(len(subset))

    # bucketed maxima
    hrr_max = 0.0
    ber_max = 0.0
    checkpoint_max = 0.0
    atr_axis_max = 0.0
    dnapk_max = 0.0
    ddr_broad_max = 0.0

    scored = 0
    for _, r in subset.iterrows():
        chrom_raw = str(r["Chrom"])
        chrom = chrom_raw if chrom_raw.startswith("chr") else f"chr{chrom_raw}"
        pos = int(r["Pos"])
        alt = str(r["Alt"]).upper()
        ref = None if pd.isna(r.get("Ref")) else str(r.get("Ref")).upper()
        gene = str(r["HugoSymbol"]).upper()

        key = f"{genome}:{chrom}:{pos}:{alt}"
        if key in cache:
            out = cache[key]
        else:
            hit = scorer.score_snv(chrom=chrom, pos=pos, alt=alt, genome=genome)
            out = {
                "delta_score": hit.delta_score,
                "disruption": delta_to_disruption(hit.delta_score),
                "reference": hit.reference,
                "prediction": hit.prediction,
                "confidence": hit.confidence,
            }
            cache[key] = out

        # Strict REF validation (no redeploy): accept only if Omics Ref matches the service-returned reference.
        if ref and out.get("reference") and str(out["reference"]).upper() != ref:
            continue

        scored += 1
        d = float(out.get("disruption") or 0.0)

        if gene in HRR_GENES:
            hrr_max = max(hrr_max, d)
        if gene in BER_GENES:
            ber_max = max(ber_max, d)
        if gene in CHECKPOINT_GENES:
            checkpoint_max = max(checkpoint_max, d)
        if gene in ATR_AXIS_GENES:
            atr_axis_max = max(atr_axis_max, d)
        if gene in DNAPK_GENES:
            dnapk_max = max(dnapk_max, d)
        if gene in DDR_BROAD:
            ddr_broad_max = max(ddr_broad_max, d)

    return CellLineFeatures(
        model_id=str(model_id),
        hrr_max=hrr_max,
        ber_max=ber_max,
        checkpoint_max=checkpoint_max,
        atr_axis_max=atr_axis_max,
        dnapk_max=dnapk_max,
        ddr_broad_max=ddr_broad_max,
        n_variants_scored=scored,
        n_variants_considered=n_considered,
    )


def predict_class(feat: CellLineFeatures, thresholds: Dict[str, float]) -> str:
    # Mechanism scores (simple, explicit)
    parp = max(feat.hrr_max, feat.ber_max)
    atr = max(feat.ddr_broad_max, feat.atr_axis_max)
    wee1 = feat.checkpoint_max
    dnapk = feat.dnapk_max

    # Conservative gating per-class
    scores = {
        "PARP": parp if parp >= thresholds.get("PARP", float("inf")) else 0.0,
        "ATR": atr if atr >= thresholds.get("ATR", float("inf")) else 0.0,
        "WEE1": wee1 if wee1 >= thresholds.get("WEE1", float("inf")) else 0.0,
        "DNA_PK": dnapk if dnapk >= thresholds.get("DNA_PK", float("inf")) else 0.0,
    }

    best = max(scores.items(), key=lambda kv: kv[1])
    if best[1] <= 0.0:
        return "NONE"
    return best[0]


def compute_ground_truth_class(g: pd.DataFrame) -> str:
    """Define in-vitro 'best class' as class with minimum mean AUC.

    'NONE' if all class means are above a hard threshold.
    """
    # AUC: lower is more sensitive
    by_class = g.groupby("drug_class")["AUC"].mean().to_dict()
    if not by_class:
        return "NONE"
    best_class, best_auc = min(by_class.items(), key=lambda kv: kv[1])

    # conservative none gate: if best AUC is still very high
    if best_auc >= 0.9:
        return "NONE"
    return str(best_class)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n_cell_lines", type=int, default=50)
    ap.add_argument("--max_variants_per_line", type=int, default=12)
    ap.add_argument("--seed", type=int, default=1337)
    ap.add_argument("--out_prefix", type=str, default="gdsc2_multiclass_evo2")
    args = ap.parse_args()

    random.seed(args.seed)

    root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    data_dir = os.path.join(root, "data")
    results_dir = os.path.join(root, "results")
    safe_mkdir(results_dir)

    gdsc_path = os.path.join(data_dir, "GDSC2_fitted_dose_response_27Oct23.xlsx")
    mut_path = os.path.join(data_dir, "OmicsSomaticMutations.csv")
    model_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "data", "depmap", "Model.csv"))

    if not os.path.exists(gdsc_path):
        raise FileNotFoundError(gdsc_path)
    if not os.path.exists(mut_path):
        raise FileNotFoundError(mut_path)
    if not os.path.exists(model_path):
        raise FileNotFoundError(model_path)

    # Load mapping COSMIC_ID -> ModelID
    model_df = pd.read_csv(model_path, usecols=["ModelID", "COSMICID"]).dropna(subset=["COSMICID"])
    model_df["COSMIC_ID"] = model_df["COSMICID"].apply(normalize_cosmic_id)
    model_df = model_df.dropna(subset=["COSMIC_ID"])
    model_df = model_df[["ModelID", "COSMIC_ID"]].drop_duplicates()

    # Load GDSC subset for relevant drugs
    usecols_g = ["COSMIC_ID", "CELL_LINE_NAME", "DRUG_NAME", "AUC", "LN_IC50"]
    gdsc = pd.read_excel(gdsc_path, engine="openpyxl", usecols=usecols_g)
    gdsc["COSMIC_ID"] = gdsc["COSMIC_ID"].apply(normalize_cosmic_id)
    gdsc = gdsc.dropna(subset=["COSMIC_ID"])
    gdsc = gdsc[gdsc["DRUG_NAME"].isin(set(DRUG_TO_CLASS.keys()))].copy()
    gdsc["drug_class"] = gdsc["DRUG_NAME"].map(DRUG_TO_CLASS)

    # Join to ModelID
    gdsc = gdsc.merge(model_df, on="COSMIC_ID", how="inner")

    # Choose cell lines with coverage across >=2 classes
    per_line = gdsc.groupby("ModelID")["drug_class"].nunique().reset_index(name="n_classes")
    candidates = per_line[per_line["n_classes"] >= 2]["ModelID"].astype(str).tolist()
    if len(candidates) < args.n_cell_lines:
        chosen = candidates
    else:
        chosen = random.sample(candidates, args.n_cell_lines)

    gdsc_sub = gdsc[gdsc["ModelID"].astype(str).isin(set(chosen))].copy()

    # Build ground truth per line
    gt = {}
    for mid, group in gdsc_sub.groupby("ModelID"):
        gt[str(mid)] = compute_ground_truth_class(group)

    # Load mutations only for these model IDs (streamed)
    want = set(chosen)
    usecols_m = ["ModelID", "Chrom", "Pos", "Ref", "Alt", "VariantType", "HugoSymbol", "VepImpact"]
    chunks = []
    for chunk in pd.read_csv(mut_path, usecols=usecols_m, chunksize=200000):
        chunk["ModelID"] = chunk["ModelID"].astype(str)
        sub = chunk[chunk["ModelID"].isin(want)].copy()
        if len(sub):
            sub["HugoSymbol"] = sub["HugoSymbol"].astype(str).str.upper()
            sub = sub[sub["HugoSymbol"].isin(DDR_BROAD)]
            if len(sub):
                chunks.append(sub)
        if len(chunks) and sum(len(x) for x in chunks) > 500000:
            break
    muts = pd.concat(chunks, ignore_index=True) if chunks else pd.DataFrame(columns=usecols_m)

    # Evo2 scorer
    scorer = Evo2VariantScorer(app_name="variant-analysis-evo2", cls_name="Evo2Model")

    # Local cache for Evo2 calls (so reruns are cheap)
    cache_path = os.path.join(results_dir, f"{args.out_prefix}_evo2_cache.json")
    cache: Dict[str, Dict] = {}
    if os.path.exists(cache_path):
        try:
            cache = json.load(open(cache_path))
        except Exception:
            cache = {}

    feats: Dict[str, CellLineFeatures] = {}
    for mid in chosen:
        mm = muts[muts["ModelID"].astype(str) == str(mid)]
        feats[str(mid)] = compute_features_for_cellline(
            scorer=scorer,
            model_id=str(mid),
            muts=mm,
            max_variants=args.max_variants_per_line,
            cache=cache,
            genome="hg38",
        )

    # Save cache
    with open(cache_path, "w") as f:
        json.dump(cache, f)

    # Choose conservative thresholds from the observed distribution (90th percentile) to reduce FP
    # (This is a first-pass safety gate; future version should use held-out thresholds.)
    import numpy as np

    vals = {
        "PARP": [max(v.hrr_max, v.ber_max) for v in feats.values()],
        "ATR": [max(v.ddr_broad_max, v.atr_axis_max) for v in feats.values()],
        "WEE1": [v.checkpoint_max for v in feats.values()],
        "DNA_PK": [v.dnapk_max for v in feats.values()],
    }
    thresholds = {k: float(np.quantile([x for x in xs if x is not None], 0.90)) if len(xs) else float("inf") for k, xs in vals.items()}

    pred = {}
    for mid, f in feats.items():
        pred[mid] = predict_class(f, thresholds=thresholds)

    # Metrics
    y_true = [gt[mid] for mid in chosen]
    y_pred = [pred[mid] for mid in chosen]

    labels = ["PARP", "ATR", "WEE1", "DNA_PK", "NONE"]
    idx = {l: i for i, l in enumerate(labels)}
    cm = [[0 for _ in labels] for __ in labels]
    for t, p in zip(y_true, y_pred):
        cm[idx.get(t, idx["NONE"])][idx.get(p, idx["NONE"]) ] += 1

    acc = sum(1 for t, p in zip(y_true, y_pred) if t == p) / max(1, len(y_true))

    # FP rate for PARP: among GT != PARP, predicted PARP
    non_parp = [i for i, t in enumerate(y_true) if t != "PARP"]
    parp_fp = 0
    for i in non_parp:
        if y_pred[i] == "PARP":
            parp_fp += 1
    parp_fpr = parp_fp / max(1, len(non_parp))

    receipt = {
        "n_cell_lines": len(chosen),
        "max_variants_per_line": args.max_variants_per_line,
        "thresholds": thresholds,
        "accuracy": acc,
        "parp_false_positive_rate": parp_fpr,
        "labels": labels,
        "confusion_matrix": cm,
        "notes": [
            "Ground truth is in-vitro: best class = minimum mean AUC across drugs in class; NONE if best mean AUC >= 0.9.",
            "Predictor uses Evo2 disruption on capped DDR SNVs per cell line via deployed Modal app variant-analysis-evo2.",
            "Thresholds are set to 90th percentile of observed scores (safety-first; not yet held-out).",
        ],
        "per_cell_line": [
            {
                "ModelID": mid,
                "gt": gt[mid],
                "pred": pred[mid],
                "features": {
                    "hrr_max": feats[mid].hrr_max,
                    "ber_max": feats[mid].ber_max,
                    "checkpoint_max": feats[mid].checkpoint_max,
                    "atr_axis_max": feats[mid].atr_axis_max,
                    "dnapk_max": feats[mid].dnapk_max,
                    "ddr_broad_max": feats[mid].ddr_broad_max,
                    "n_variants_scored": feats[mid].n_variants_scored,
                    "n_variants_considered": feats[mid].n_variants_considered,
                },
            }
            for mid in chosen
        ],
    }

    out_path = os.path.join(results_dir, f"{args.out_prefix}_n{len(chosen)}.json")
    with open(out_path, "w") as f:
        json.dump(receipt, f, indent=2)

    print("Wrote receipt:", out_path)
    print("accuracy:", acc)
    print("parp_false_positive_rate:", parp_fpr)
    print("thresholds:", thresholds)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
