#!/usr/bin/env python3
"""Benchmark (preclinical): multimodal S/P/D scoring on GDSC2 outcomes.

Abstraction we are delivering:
- S (Sequence): Evo2 delta disruption per allele-resolved variant (OmicsSomaticMutations)
- P (Pathway): mechanistic aggregation into drug-class scores (PARP/ATR/WEE1/DNA-PK)
- D (Dependency grounding): lineage-context essentiality priors (depmap_essentiality_by_context.json)
- Outcome label: in-vitro drug sensitivity class derived from GDSC2 Z_SCORE (transparent rule)

This is RUO / preclinical validation (cell lines), not patient outcome validation.
"""

from __future__ import annotations

import argparse
import json
import os
import random
from collections import Counter
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
import numpy as np

# -------------------------
# Drug class mapping
# -------------------------
PARP_DRUGS = {"Olaparib", "Niraparib", "Talazoparib", "Rucaparib", "Veliparib"}
ATR_DRUGS = {"AZD6738", "VE-822", "VE821"}
WEE1_DRUGS = {"MK-1775"}
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

LABELS = ["PARP", "ATR", "WEE1", "DNA_PK", "NONE"]

# -------------------------
# Gene sets (mechanistic)
# -------------------------
HRR_GENES = {"BRCA1", "BRCA2", "PALB2", "RAD51C", "RAD51D", "BRIP1", "BARD1", "CDK12"}
BER_GENES = {"MBD4"}
CHECKPOINT_GENES = {"TP53"}
ATR_AXIS_GENES = {"ATR", "CHEK1"}
DNAPK_GENES = {"PRKDC"}
DDR_BROAD = set().union(
    HRR_GENES,
    BER_GENES,
    CHECKPOINT_GENES,
    ATR_AXIS_GENES,
    DNAPK_GENES,
    {"ATM", "CHEK2", "ARID1A"},
)

# drug-target genes (for dependency grounding)
CLASS_TARGET_GENE = {
    "PARP": "PARP1",
    "ATR": "ATR",
    "WEE1": "WEE1",
    "DNA_PK": "PRKDC",
}


def safe_mkdir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def normalize_cosmic_id(x) -> Optional[str]:
    try:
        if pd.isna(x):
            return None
        return str(int(float(x)))
    except Exception:
        return None


def delta_to_disruption(delta: Optional[float]) -> float:
    if delta is None:
        return 0.0
    # delta = alt_ll - ref_ll; more negative => more disruptive
    return max(0.0, -float(delta))


def compute_label_from_z(
    z_by_class: Dict[str, float],
    z_sensitive_threshold: float,
    min_margin: float,
) -> str:
    if not z_by_class:
        return "NONE"

    items = [(k, float(v)) for k, v in z_by_class.items() if v is not None]
    if not items:
        return "NONE"

    items.sort(key=lambda kv: kv[1])
    best_class, best_z = items[0]
    if best_z > z_sensitive_threshold:
        return "NONE"

    if len(items) >= 2:
        second_z = items[1][1]
        if (second_z - best_z) < min_margin:
            return "NONE"

    return best_class


@dataclass
class CellLineFeatures:
    model_id: str
    lineage: str
    hrr_max: float
    ber_max: float
    checkpoint_max: float
    atr_axis_max: float
    dnapk_max: float
    ddr_broad_max: float
    n_variants_scored: int
    n_variants_considered: int
    # per-gene max raw disruptions (for gene-specific calibration)
    gene_raw_max: Dict[str, float] = field(default_factory=dict)


class Evo2VariantScorer:

    """Wrapper around deployed Modal app `variant-analysis-evo2`.

    Signature:
      analyze_single_variant(pos, alt, genome, chrom)

    Cache key used here: hg38:chrX:pos:ALT
    """

    def __init__(self, app_name: str = "variant-analysis-evo2", cls_name: str = "Evo2Model"):
        import modal

        self._cls = modal.Cls.from_name(app_name, cls_name)
        self._obj = self._cls()

    def score_snv(self, chrom: str, pos: int, alt: str, genome: str = "hg38") -> Dict:
        out = self._obj.analyze_single_variant.remote(int(pos), str(alt).upper(), genome, str(chrom))
        if not isinstance(out, dict) or "delta_score" not in out:
            raise RuntimeError(f"Unexpected response from Evo2 scorer: {type(out)} {str(out)[:200]}")
        return out


class EvoApiVariantScorer:
    """HTTP client for backend Evo endpoints (doctrine-aligned).

    Calls:
    - POST {api_base}/api/evo/score_variant_multi  -> {min_delta, ...}
    - POST {api_base}/api/evo/score_variant_exon   -> {exon_delta, ...}
    """

    def __init__(
        self,
        *,
        api_base: str,
        model_id: str = "evo2_1b",
        timeout_s: float = 60.0,
        exon_flank: int = 4096,
        windows: Optional[List[int]] = None,
    ):
        self.api_base = str(api_base).rstrip("/")
        self.model_id = str(model_id)
        self.timeout_s = float(timeout_s)
        self.exon_flank = int(exon_flank)
        self.windows = windows or [1024, 2048, 4096, 8192]

        try:
            import httpx  # noqa: F401
        except Exception as e:
            raise RuntimeError("httpx is required for --evo_api_base usage") from e

    def score_variant(
        self,
        *,
        assembly: str,
        chrom: str,
        pos: int,
        ref: str,
        alt: str,
    ) -> Dict[str, Any]:
        import httpx

        payload = {
            "assembly": str(assembly),
            "chrom": str(chrom).replace("chr", ""),
            "pos": int(pos),
            "ref": str(ref).upper(),
            "alt": str(alt).upper(),
            "model_id": self.model_id,
            "windows": list(self.windows),
        }

        with httpx.Client(timeout=self.timeout_s, follow_redirects=True) as client:
            r_multi = client.post(f"{self.api_base}/api/evo/score_variant_multi", json=payload)
            r_multi.raise_for_status()
            j_multi = r_multi.json() if r_multi.content else {}

            r_exon = client.post(
                f"{self.api_base}/api/evo/score_variant_exon",
                json={**payload, "flank": int(self.exon_flank)},
            )
            r_exon.raise_for_status()
            j_exon = r_exon.json() if r_exon.content else {}

        min_delta = j_multi.get("min_delta") if isinstance(j_multi, dict) else None
        exon_delta = j_exon.get("exon_delta") if isinstance(j_exon, dict) else None

        def _abs(x):
            try:
                return abs(float(x))
            except Exception:
                return 0.0

        disruption = max(_abs(min_delta), _abs(exon_delta))

        return {
            "min_delta": min_delta,
            "exon_delta": exon_delta,
            "disruption": disruption,
            "provenance": {
                "method": "evo_api_multi_exon",
                "api_base": self.api_base,
                "model_id": self.model_id,
                "windows": self.windows,
                "exon_flank": self.exon_flank,
                "upstream_multi": j_multi.get("upstream_service") if isinstance(j_multi, dict) else None,
                "upstream_exon": j_exon.get("upstream_service") if isinstance(j_exon, dict) else None,
            },
        }


def pick_variants_for_cellline(df: pd.DataFrame, max_variants: int) -> pd.DataFrame:
    """Pick variants to score for a cell line.

    Key change (SPE-aligned practical fix): prioritize variants in DDR target genes first,
    otherwise we waste budget scoring unrelated genes and S collapses to 0.
    """
    x = df.copy()
    x = x[(x["VariantType"].astype(str).str.lower() == "snv") & (x["Alt"].astype(str).str.len() == 1)]
    if len(x) == 0:
        return x

    # prioritize DDR genes (mechanistic target set)
    gene_col = "HugoSymbol" if "HugoSymbol" in x.columns else ("Gene" if "Gene" in x.columns else None)
    if gene_col is not None:
        g = x[gene_col].astype(str).str.upper()
        in_ddr = g.isin(DDR_BROAD)
        x_ddr = x[in_ddr].copy()
        x_other = x[~in_ddr].copy()
    else:
        x_ddr = x
        x_other = x.iloc[0:0]

    def _sort_by_impact(df_: pd.DataFrame) -> pd.DataFrame:
        if len(df_) == 0:
            return df_
        if "VepImpact" in df_.columns:
            imp = df_["VepImpact"].astype(str).str.upper()
            rank = imp.map({"HIGH": 0, "MODERATE": 1, "LOW": 2}).fillna(3)
            return df_.assign(_rank=rank).sort_values(["_rank"]).drop(columns=["_rank"])
        return df_

    x_ddr = _sort_by_impact(x_ddr)
    x_other = _sort_by_impact(x_other)

    out = pd.concat([x_ddr, x_other], ignore_index=True)
    return out.head(max_variants)


def load_depmap_grounding(depmap_path: str) -> Dict:
    return json.load(open(depmap_path))


def get_lineage_essentiality(depmap: Dict, lineage: str, gene: str) -> float:
    """Return essentiality_score in [0,1]. Fallback to global if missing."""
    gene = gene.upper()

    by_lineage = depmap.get("by_lineage", {})
    rec = by_lineage.get(lineage)
    if isinstance(rec, dict):
        g = rec.get(gene)
        if isinstance(g, dict) and g.get("essentiality_score") is not None:
            try:
                return float(g["essentiality_score"])
            except Exception:
                pass

    global_rec = depmap.get("global", {})
    if isinstance(global_rec, dict):
        g = global_rec.get(gene)
        if isinstance(g, dict) and g.get("essentiality_score") is not None:
            try:
                return float(g["essentiality_score"])
            except Exception:
                pass

    return 0.0


def compute_features_for_cellline(
    model_id: str,
    lineage: str,
    muts: pd.DataFrame,
    max_variants: int,
    cache: Dict[str, Dict],
    scorer: Optional[Evo2VariantScorer],
    use_cache_only: bool,
    genome: str = "hg38",
) -> CellLineFeatures:
    subset = pick_variants_for_cellline(muts, max_variants=max_variants)
    n_considered = int(len(subset))

    hrr_max = ber_max = checkpoint_max = atr_axis_max = dnapk_max = ddr_broad_max = 0.0
    scored = 0
    gene_raw_max: Dict[str, float] = {}

    for _, r in subset.iterrows():
        chrom_raw = str(r["Chrom"])
        chrom = chrom_raw if chrom_raw.startswith("chr") else f"chr{chrom_raw}"
        pos = int(r["Pos"])
        alt = str(r["Alt"]).upper()
        ref = None if pd.isna(r.get("Ref")) else str(r.get("Ref")).upper()
        gene = str(r["HugoSymbol"]).upper()

        key = f"{genome}:{chrom}:{pos}:{ref}:{alt}"

        out = cache.get(key)
        if out is None:
            if use_cache_only:
                continue
            if scorer is None:
                continue
            # Prefer backend evo endpoints when available (multi-window + exon corroboration)
            if hasattr(scorer, "score_variant") and ref:  # EvoApiVariantScorer
                hit = scorer.score_variant(assembly="GRCh38" if genome in ("hg38","GRCh38") else "GRCh37", chrom=chrom, pos=pos, ref=ref, alt=alt)
                out = {
                    "min_delta": hit.get("min_delta"),
                    "exon_delta": hit.get("exon_delta"),
                    "disruption": float(hit.get("disruption") or 0.0),
                    "provenance": hit.get("provenance"),
                }
                cache[key] = out
                # No REF validation needed; we sent REF explicitly
                scored += 1
                d = float(out.get("disruption") or 0.0)
                gene_raw_max[gene] = max(gene_raw_max.get(gene, 0.0), d)
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
                continue

            hit = scorer.score_snv(chrom=chrom, pos=pos, alt=alt, genome=genome)
            out = {
                "delta_score": float(hit.get("delta_score")),
                "reference": hit.get("reference"),
                "prediction": hit.get("prediction"),
                "confidence": hit.get("classification_confidence"),
            }
            out["disruption"] = delta_to_disruption(out.get("delta_score"))
            cache[key] = out

        # strict REF validation: only accept if provided ref matches service reference
        if ref and out.get("reference") and str(out["reference"]).upper() != ref:
            continue

        scored += 1
        d = float(out.get("disruption") or 0.0)

        gene_raw_max[gene] = max(gene_raw_max.get(gene, 0.0), d)

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
        lineage=str(lineage),
        hrr_max=hrr_max,
        ber_max=ber_max,
        checkpoint_max=checkpoint_max,
        atr_axis_max=atr_axis_max,
        dnapk_max=dnapk_max,
        ddr_broad_max=ddr_broad_max,
        gene_raw_max=gene_raw_max,
        n_variants_scored=scored,
        n_variants_considered=n_considered,
    )


def build_gene_calibrator(train_feats: Dict[str, CellLineFeatures]) -> Dict[str, List[float]]:
    """Build per-gene empirical distributions on TRAIN only.

    Returns: gene -> sorted list of raw disruptions.
    Also includes '__GLOBAL__' fallback distribution.
    """
    by_gene: Dict[str, List[float]] = {}
    global_vals: List[float] = []

    for f in train_feats.values():
        for g, v in (f.gene_raw_max or {}).items():
            by_gene.setdefault(g, []).append(float(v))
            global_vals.append(float(v))

    # Stabilize: ensure 0.0 is present for each gene and globally
    for g in list(by_gene.keys()):
        by_gene[g].append(0.0)
        by_gene[g].sort()

    global_vals.append(0.0)
    global_vals.sort()
    by_gene['__GLOBAL__'] = global_vals
    return by_gene


def percentile(sorted_vals: List[float], x: float) -> float:
    """Empirical percentile in [0,1] using bisect_right."""
    import bisect

    if not sorted_vals:
        return 0.0
    i = bisect.bisect_right(sorted_vals, float(x))
    return i / float(len(sorted_vals))


def calibrated_gene_score(calib: Dict[str, List[float]], gene: str, raw: float) -> float:
    gene = str(gene).upper()
    if gene in calib:
        return percentile(calib[gene], raw)
    return percentile(calib.get('__GLOBAL__', [0.0]), raw)


def score_classes_sp_calibrated(feat: CellLineFeatures, calib: Dict[str, List[float]]) -> Dict[str, float]:
    """Compute SP class scores using calibrated (gene-specific) disruption."""
    gmax = feat.gene_raw_max or {}

    def g(gene: str) -> float:
        return calibrated_gene_score(calib, gene, float(gmax.get(gene, 0.0)))

    parp = max([g(x) for x in (HRR_GENES | BER_GENES)] or [0.0])

    # ATR axis driver set (checkpoint + replication stress regulators)
    atr_driver = set().union(ATR_AXIS_GENES, CHECKPOINT_GENES, {"ATM", "CHEK2", "ARID1A"})
    atr = max([g(x) for x in atr_driver] or [0.0])

    wee1 = max([g(x) for x in CHECKPOINT_GENES] or [0.0])
    dnapk = max([g(x) for x in DNAPK_GENES] or [0.0])

    return {"PARP": parp, "ATR": atr, "WEE1": wee1, "DNA_PK": dnapk}


def score_classes_sp(feat: CellLineFeatures) -> Dict[str, float]:
    parp = max(feat.hrr_max, feat.ber_max)
    atr = max(feat.ddr_broad_max, feat.atr_axis_max)
    wee1 = feat.checkpoint_max
    dnapk = feat.dnapk_max
    return {"PARP": parp, "ATR": atr, "WEE1": wee1, "DNA_PK": dnapk}


def apply_depmap_grounding(scores: Dict[str, float], depmap: Dict, lineage: str) -> Dict[str, float]:
    out = dict(scores)
    for cls, target in CLASS_TARGET_GENE.items():
        if cls in out:
            ess = get_lineage_essentiality(depmap, lineage=lineage, gene=target)
            out[cls] = out[cls] * ess
    return out


def predict_from_scores(scores: Dict[str, float], none_threshold: float) -> str:
    best_cls, best_score = max(scores.items(), key=lambda kv: kv[1])
    if best_score < none_threshold:
        return "NONE"
    return best_cls


def confusion_matrix(y_true: List[str], y_pred: List[str], labels: List[str]) -> List[List[int]]:
    idx = {l: i for i, l in enumerate(labels)}
    cm = [[0 for _ in labels] for __ in labels]
    for t, p in zip(y_true, y_pred):
        cm[idx.get(t, idx["NONE"])][idx.get(p, idx["NONE"])] += 1
    return cm


def macro_f1(y_true: List[str], y_pred: List[str], labels: List[str]) -> float:
    # simple macro-F1
    from collections import defaultdict

    tp = defaultdict(int)
    fp = defaultdict(int)
    fn = defaultdict(int)
    for t, p in zip(y_true, y_pred):
        if t == p:
            tp[t] += 1
        else:
            fp[p] += 1
            fn[t] += 1
    f1s = []
    for l in labels:
        if l == "NONE":
            continue
        precision = tp[l] / max(1, tp[l] + fp[l])
        recall = tp[l] / max(1, tp[l] + fn[l])
        if precision + recall == 0:
            f1 = 0.0
        else:
            f1 = 2 * precision * recall / (precision + recall)
        f1s.append(f1)
    return sum(f1s) / max(1, len(f1s))


def tune_none_threshold(
    mids: List[str],
    labels_by_mid: Dict[str, str],
    score_by_mid: Dict[str, Dict[str, float]],
    *,
    grid: List[float],
    max_parp_fpr: Optional[float],
) -> Dict[str, float]:
    """Tune NONE threshold on training set only (no leakage).

    Objective: maximize macro-F1 subject to optional PARP false-positive rate constraint.
"""
    best = {"none_threshold": 0.0, "macro_f1": -1.0, "parp_fpr": 1.0, "accuracy": 0.0}
    for thr in grid:
        y_true = [labels_by_mid[m] for m in mids]
        y_pred = [predict_from_scores(score_by_mid[m], none_threshold=thr) for m in mids]

        acc = sum(1 for t, p in zip(y_true, y_pred) if t == p) / max(1, len(y_true))
        mf1 = macro_f1(y_true, y_pred, LABELS)

        non_parp_idx = [i for i, t in enumerate(y_true) if t != "PARP"]
        parp_fp = sum(1 for i in non_parp_idx if y_pred[i] == "PARP")
        parp_fpr = parp_fp / max(1, len(non_parp_idx))

        if max_parp_fpr is not None and parp_fpr > max_parp_fpr:
            continue

        if mf1 > best["macro_f1"]:
            best = {"none_threshold": float(thr), "macro_f1": float(mf1), "parp_fpr": float(parp_fpr), "accuracy": float(acc)}

    return best


def _one_hot(y_idx: List[int], n_classes: int) -> np.ndarray:
    Y = np.zeros((len(y_idx), n_classes), dtype=np.float64)
    for i, c in enumerate(y_idx):
        Y[i, int(c)] = 1.0
    return Y


def softmax(z: np.ndarray) -> np.ndarray:
    z = z - np.max(z, axis=1, keepdims=True)
    ez = np.exp(z)
    return ez / np.sum(ez, axis=1, keepdims=True)


def fit_softmax_regression(
    X: np.ndarray,
    y: List[str],
    classes: List[str],
    *,
    lr: float = 0.5,
    reg: float = 1e-3,
    steps: int = 2000,
    seed: int = 1337,
) -> Dict[str, Any]:
    """Train-only multinomial logistic regression (softmax) with L2.

    Returns dict containing W, bias, feature scaling params, and class list.
    """
    rng = np.random.default_rng(seed)

    class_to_idx = {c: i for i, c in enumerate(classes)}
    y_idx = [class_to_idx.get(lbl, class_to_idx["NONE"]) for lbl in y]

    X = X.astype(np.float64)
    mu = X.mean(axis=0)
    sigma = X.std(axis=0)
    sigma[sigma < 1e-8] = 1.0
    Xn = (X - mu) / sigma

    n, d = Xn.shape
    k = len(classes)

    W = 0.01 * rng.standard_normal((k, d))
    b = np.zeros((k,), dtype=np.float64)

    Y = _one_hot(y_idx, k)

    for _ in range(int(steps)):
        logits = Xn @ W.T + b
        P = softmax(logits)
        # grad
        G = (P - Y) / max(1, n)
        dW = G.T @ Xn + reg * W
        db = G.sum(axis=0)
        W -= lr * dW
        b -= lr * db

    return {"classes": classes, "W": W, "b": b, "mu": mu, "sigma": sigma}


def predict_softmax(
    model: Dict[str, Any],
    X: np.ndarray,
) -> np.ndarray:
    X = X.astype(np.float64)
    mu = model["mu"]; sigma = model["sigma"]
    Xn = (X - mu) / sigma
    W = model["W"]; b = model["b"]
    logits = Xn @ W.T + b
    return softmax(logits)


def tune_prob_threshold(
    y_true: List[str],
    prob: np.ndarray,
    classes: List[str],
    *,
    grid: List[float],
    max_parp_fpr: Optional[float],
) -> Dict[str, float]:
    """Tune a probability threshold for predicting non-NONE.

    Rule:
    - compute best non-NONE class probability
    - if best_non_none_prob < thr => NONE
    - else => argmax over non-NONE classes
    """
    idx = {c: i for i, c in enumerate(classes)}
    non_none = [c for c in classes if c != "NONE"]
    non_none_idx = [idx[c] for c in non_none]

    best = {"prob_threshold": 0.0, "macro_f1": -1.0, "parp_fpr": 1.0, "accuracy": 0.0}

    for thr in grid:
        y_pred = []
        for i in range(prob.shape[0]):
            sub = prob[i, non_none_idx]
            j = int(np.argmax(sub))
            best_cls = non_none[j]
            best_p = float(sub[j])
            if best_p < thr:
                y_pred.append("NONE")
            else:
                y_pred.append(best_cls)

        acc = sum(1 for t, p in zip(y_true, y_pred) if t == p) / max(1, len(y_true))
        mf1 = macro_f1(y_true, y_pred, LABELS)

        non_parp_idx = [i for i, t in enumerate(y_true) if t != "PARP"]
        parp_fp = sum(1 for i in non_parp_idx if y_pred[i] == "PARP")
        parp_fpr = parp_fp / max(1, len(non_parp_idx))

        if max_parp_fpr is not None and parp_fpr > max_parp_fpr:
            continue
        if mf1 > best["macro_f1"]:
            best = {"prob_threshold": float(thr), "macro_f1": float(mf1), "parp_fpr": float(parp_fpr), "accuracy": float(acc)}

    return best


def pred_from_prob(prob_row: np.ndarray, classes: List[str], prob_threshold: float) -> str:
    idx = {c: i for i, c in enumerate(classes)}
    non_none = [c for c in classes if c != "NONE"]
    non_none_idx = [idx[c] for c in non_none]
    sub = prob_row[non_none_idx]
    j = int(np.argmax(sub))
    best_cls = non_none[j]
    best_p = float(sub[j])
    return "NONE" if best_p < prob_threshold else best_cls


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n_per_class", type=int, default=25)
    ap.add_argument("--seed", type=int, default=1337)
    ap.add_argument("--max_variants_per_line", type=int, default=12)
    ap.add_argument("--z_sensitive_threshold", type=float, default=-0.8)
    ap.add_argument("--min_margin", type=float, default=0.25)
    ap.add_argument("--test_frac", type=float, default=0.2)
    ap.add_argument("--none_threshold", type=float, default=0.0, help="Fixed NONE threshold (used when --tune_none_threshold is not set)")
    ap.add_argument("--tune_none_threshold", action="store_true", help="Tune NONE threshold on train only (no leakage)")
    ap.add_argument("--max_parp_fpr", type=float, default=None, help="Optional constraint during tuning: PARP FPR <= this value on train")
    ap.add_argument("--use_cache_only", action="store_true", help="Do not call Evo2; only use cached variant scores")
    ap.add_argument("--cache_path", type=str, default="")
    ap.add_argument("--evo_api_base", type=str, default="", help="If set, use local backend /api/evo endpoints for S (multi-window + exon)")
    ap.add_argument("--evo_api_model_id", type=str, default="evo2_1b")
    ap.add_argument("--evo_api_timeout_s", type=float, default=60.0)
    ap.add_argument("--evo_api_exon_flank", type=int, default=4096)
    ap.add_argument("--out_prefix", type=str, default="gdsc2_multimodal_spd")
    ap.add_argument("--flush_cache_every", type=int, default=1, help="Write Evo2 cache to disk every N cell lines (default: 1)")
    args = ap.parse_args()

    random.seed(args.seed)

    root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    data_dir = os.path.join(root, "data")
    results_dir = os.path.join(root, "results")
    safe_mkdir(results_dir)

    gdsc_path = os.path.join(data_dir, "GDSC2_fitted_dose_response_27Oct23.xlsx")
    omics_path = os.path.join(data_dir, "OmicsSomaticMutations.csv")
    depmap_grounding_path = os.path.join(data_dir, "depmap_essentiality_by_context.json")
    model_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "data", "depmap", "Model.csv"))

    for p in (gdsc_path, omics_path, depmap_grounding_path, model_path):
        if not os.path.exists(p):
            raise FileNotFoundError(p)

    model_df = pd.read_csv(model_path, usecols=["ModelID", "COSMICID", "OncotreeLineage"], low_memory=False).dropna(subset=["COSMICID", "ModelID"])
    model_df["COSMIC_ID"] = model_df["COSMICID"].apply(normalize_cosmic_id)
    model_df = model_df.dropna(subset=["COSMIC_ID"])
    model_df["ModelID"] = model_df["ModelID"].astype(str)
    model_df["OncotreeLineage"] = model_df["OncotreeLineage"].astype(str)
    model_df = model_df[["ModelID", "COSMIC_ID", "OncotreeLineage"]].drop_duplicates()

    gdsc = pd.read_excel(gdsc_path, engine="openpyxl", usecols=["COSMIC_ID", "DRUG_NAME", "Z_SCORE", "AUC"])
    gdsc["COSMIC_ID"] = gdsc["COSMIC_ID"].apply(normalize_cosmic_id)
    gdsc = gdsc.dropna(subset=["COSMIC_ID", "DRUG_NAME"])
    gdsc = gdsc[gdsc["DRUG_NAME"].isin(set(DRUG_TO_CLASS.keys()))].copy()
    gdsc["drug_class"] = gdsc["DRUG_NAME"].map(DRUG_TO_CLASS)
    gdsc = gdsc.merge(model_df, on="COSMIC_ID", how="inner")

    # Label each cell line
    labels_by_mid: Dict[str, str] = {}
    lineage_by_mid: Dict[str, str] = {}
    for mid, g in gdsc.groupby("ModelID"):
        mid = str(mid)
        lineage_by_mid[mid] = str(g["OncotreeLineage"].iloc[0])
        z_by_class = g.groupby("drug_class")["Z_SCORE"].mean().to_dict()
        labels_by_mid[mid] = compute_label_from_z(z_by_class, args.z_sensitive_threshold, args.min_margin)

    # Stratified sample
    by_label: Dict[str, List[str]] = {l: [] for l in LABELS}
    for mid, lab in labels_by_mid.items():
        by_label.get(lab, by_label["NONE"]).append(mid)

    chosen: List[str] = []
    for lab in LABELS:
        pool = by_label.get(lab, [])
        if not pool:
            continue
        k = min(len(pool), args.n_per_class)
        chosen.extend(random.sample(pool, k))

    chosen = sorted(set(chosen))

    # Train/test split (STRATIFIED by label; avoids accidental label skew in test)
    by_lab_chosen: Dict[str, List[str]] = {l: [] for l in LABELS}
    for mid in chosen:
        by_lab_chosen[labels_by_mid.get(mid, "NONE")].append(mid)

    test_ids: set = set()
    train_ids: List[str] = []
    for lab in LABELS:
        mids = list(by_lab_chosen.get(lab, []))
        if not mids:
            continue
        random.shuffle(mids)
        n_test_lab = max(1, int(round(len(mids) * float(args.test_frac))))
        n_test_lab = min(n_test_lab, max(1, len(mids) - 1))  # keep at least 1 train if possible
        test_ids.update(mids[:n_test_lab])
        train_ids.extend(mids[n_test_lab:])

    # deterministic ordering for reproducibility
    train_ids = sorted(set(train_ids))
    test_ids = set(sorted(test_ids))

    # Load depmap grounding
    depmap = load_depmap_grounding(depmap_grounding_path)

    # Load cache
    cache: Dict[str, Dict] = {}
    if args.cache_path:
        cache_path = args.cache_path
    else:
        cache_path = os.path.join(results_dir, f"{args.out_prefix}_evo2_cache.json")

    if os.path.exists(cache_path):
        try:
            cache = json.load(open(cache_path))
        except Exception:
            cache = {}

    scorer = None
    if not args.use_cache_only:
        if getattr(args, "evo_api_base", ""):
            scorer = EvoApiVariantScorer(
                api_base=args.evo_api_base,
                model_id=args.evo_api_model_id,
                timeout_s=args.evo_api_timeout_s,
                exon_flank=args.evo_api_exon_flank,
            )
        else:
            scorer = Evo2VariantScorer()

    # Stream Omics mutations for chosen
    want = set(chosen)
    usecols_m = ["ModelID", "Chrom", "Pos", "Ref", "Alt", "VariantType", "HugoSymbol", "VepImpact"]
    muts_chunks = []
    for chunk in pd.read_csv(omics_path, usecols=usecols_m, chunksize=200000):
        chunk["ModelID"] = chunk["ModelID"].astype(str)
        sub = chunk[chunk["ModelID"].isin(want)].copy()
        if len(sub):
            sub["HugoSymbol"] = sub["HugoSymbol"].astype(str).str.upper()
            sub = sub[sub["HugoSymbol"].isin(DDR_BROAD)]
            if len(sub):
                muts_chunks.append(sub)
        if len(muts_chunks) and sum(len(x) for x in muts_chunks) > 400000:
            break

    muts = pd.concat(muts_chunks, ignore_index=True) if muts_chunks else pd.DataFrame(columns=usecols_m)

    feats: Dict[str, CellLineFeatures] = {}
    for i, mid in enumerate(chosen, start=1):
        mm = muts[muts["ModelID"].astype(str) == str(mid)]
        feats[mid] = compute_features_for_cellline(
            model_id=mid,
            lineage=lineage_by_mid.get(mid, "Unknown"),
            muts=mm,
            max_variants=args.max_variants_per_line,
            cache=cache,
            scorer=scorer,
            use_cache_only=bool(args.use_cache_only),
            genome="hg38",
        )

        if not args.use_cache_only:
            print(f"[progress] {i}/{len(chosen)} ModelID={mid} scored={feats[mid].n_variants_scored}/{feats[mid].n_variants_considered} cache_keys={len(cache)}")
        if (i % max(1, int(args.flush_cache_every))) == 0:
            with open(cache_path, "w") as f:
                json.dump(cache, f)

    # Save cache
    with open(cache_path, "w") as f:
        json.dump(cache, f)

    # Evaluate methods
    # Evaluate methods (report train/test; tune on train only if enabled)
    test_list = [mid for mid in chosen if mid in test_ids]
    train_list = list(train_ids)

    def eval_on(mids: List[str], pred_by_mid: Dict[str, str]) -> Dict:
        y_true = [labels_by_mid[mid] for mid in mids]
        y_pred = [pred_by_mid.get(mid, "NONE") for mid in mids]

        acc = sum(1 for t, p in zip(y_true, y_pred) if t == p) / max(1, len(y_true))
        mf1 = macro_f1(y_true, y_pred, LABELS)
        cm = confusion_matrix(y_true, y_pred, LABELS)

        non_parp_idx = [i for i, t in enumerate(y_true) if t != "PARP"]
        parp_fp = sum(1 for i in non_parp_idx if y_pred[i] == "PARP")
        parp_fpr = parp_fp / max(1, len(non_parp_idx))

        return {
            "accuracy": acc,
            "macro_f1": mf1,
            "parp_false_positive_rate": parp_fpr,
            "confusion_matrix": cm,
        }

    preds: Dict[str, Dict[str, str]] = {}

    # Baseline: Always NONE
    preds["Always NONE"] = {mid: "NONE" for mid in chosen}

    # P-only baseline (gene-bucket presence; uses whatever S scores exist)
    def p_only(mid: str) -> str:
        f = feats[mid]
        if f.n_variants_scored == 0:
            return "NONE"
        if f.hrr_max > 0 or f.ber_max > 0:
            return "PARP"
        if f.atr_axis_max > 0 or f.ddr_broad_max > 0:
            return "ATR"
        if f.checkpoint_max > 0:
            return "WEE1"
        if f.dnapk_max > 0:
            return "DNA_PK"
        return "NONE"

    preds["P-only"] = {mid: p_only(mid) for mid in chosen}

    # Build gene calibrator on TRAIN only (SPE doctrine: gene-specific calibration)
    train_feats = {mid: feats[mid] for mid in train_list}
    calib = build_gene_calibrator(train_feats)

    # SP / SPD score dictionaries
    sp_scores: Dict[str, Dict[str, float]] = {}
    spd_scores: Dict[str, Dict[str, float]] = {}

    for i, mid in enumerate(chosen, start=1):
        base = score_classes_sp_calibrated(feats[mid], calib=calib)
        sp_scores[mid] = base
        spd_scores[mid] = apply_depmap_grounding(base, depmap=depmap, lineage=feats[mid].lineage)

    # Default (fixed) thresholds
    preds["SP"] = {mid: predict_from_scores(sp_scores[mid], none_threshold=args.none_threshold) for mid in chosen}
    preds["SPD"] = {mid: predict_from_scores(spd_scores[mid], none_threshold=args.none_threshold) for mid in chosen}

    tuning = {}
    if args.tune_none_threshold:
        grid = [round(x * 0.05, 3) for x in range(0, 41)]  # 0.00..2.00
        tuning["SP"] = tune_none_threshold(
            mids=train_list,
            labels_by_mid=labels_by_mid,
            score_by_mid=sp_scores,
            grid=grid,
            max_parp_fpr=args.max_parp_fpr,
        )

        tuning["SPD"] = tune_none_threshold(
            mids=train_list,
            labels_by_mid=labels_by_mid,
            score_by_mid=spd_scores,
            grid=grid,
            max_parp_fpr=args.max_parp_fpr,
        )

        # apply tuned thresholds
        preds["SP"] = {mid: predict_from_scores(sp_scores[mid], none_threshold=tuning["SP"]["none_threshold"]) for mid in chosen}
        preds["SPD"] = {mid: predict_from_scores(spd_scores[mid], none_threshold=tuning["SPD"]["none_threshold"]) for mid in chosen}

    # Learned combiner (train-only): softmax regression over SP/SPD score vectors
    # Feature sets
    def _feat_sp(mid: str) -> np.ndarray:
        f = feats[mid]
        s4 = sp_scores[mid]
        return np.array([
            float(s4.get("PARP", 0.0)),
            float(s4.get("ATR", 0.0)),
            float(s4.get("WEE1", 0.0)),
            float(s4.get("DNA_PK", 0.0)),
            float(f.n_variants_scored),
        ], dtype=np.float64)

    def _feat_spd(mid: str) -> np.ndarray:
        f = feats[mid]
        s4 = spd_scores[mid]
        ess = [
            get_lineage_essentiality(depmap, lineage=f.lineage, gene="PARP1"),
            get_lineage_essentiality(depmap, lineage=f.lineage, gene="ATR"),
            get_lineage_essentiality(depmap, lineage=f.lineage, gene="WEE1"),
            get_lineage_essentiality(depmap, lineage=f.lineage, gene="PRKDC"),
        ]
        return np.array([
            float(s4.get("PARP", 0.0)),
            float(s4.get("ATR", 0.0)),
            float(s4.get("WEE1", 0.0)),
            float(s4.get("DNA_PK", 0.0)),
            float(f.n_variants_scored),
            float(ess[0]), float(ess[1]), float(ess[2]), float(ess[3]),
        ], dtype=np.float64)

    # Train models
    y_train = [labels_by_mid[m] for m in train_list]
    X_train_sp = np.stack([_feat_sp(m) for m in train_list], axis=0)
    X_train_spd = np.stack([_feat_spd(m) for m in train_list], axis=0)
    lr_sp = fit_softmax_regression(X_train_sp, y_train, LABELS, lr=0.5, reg=1e-3, steps=2000, seed=args.seed)
    lr_spd = fit_softmax_regression(X_train_spd, y_train, LABELS, lr=0.5, reg=1e-3, steps=2000, seed=args.seed)

    # Tune probability threshold on train only (safety constraint supported)
    grid_p = [round(x * 0.05, 3) for x in range(0, 19)]  # 0.00..0.90
    prob_train_sp = predict_softmax(lr_sp, X_train_sp)
    prob_train_spd = predict_softmax(lr_spd, X_train_spd)
    tuning["LR_SP"] = tune_prob_threshold(y_train, prob_train_sp, LABELS, grid=grid_p, max_parp_fpr=args.max_parp_fpr)
    tuning["LR_SPD"] = tune_prob_threshold(y_train, prob_train_spd, LABELS, grid=grid_p, max_parp_fpr=args.max_parp_fpr)

    # Predict on all chosen
    X_all_sp = np.stack([_feat_sp(m) for m in chosen], axis=0)
    X_all_spd = np.stack([_feat_spd(m) for m in chosen], axis=0)
    prob_all_sp = predict_softmax(lr_sp, X_all_sp)
    prob_all_spd = predict_softmax(lr_spd, X_all_spd)
    preds["LR-SP"] = {mid: pred_from_prob(prob_all_sp[i], LABELS, tuning["LR_SP"]["prob_threshold"]) for i, mid in enumerate(chosen)}
    preds["LR-SPD"] = {mid: pred_from_prob(prob_all_spd[i], LABELS, tuning["LR_SPD"]["prob_threshold"]) for i, mid in enumerate(chosen)}

    results = []
    for name, pred in preds.items():
        results.append({
            "name": name,
            "train": eval_on(train_list, pred),
            "test": eval_on(test_list, pred),
        })

    receipt = {
        "n_cell_lines": len(chosen),
        "n_per_class_requested": int(args.n_per_class),
        "seed": int(args.seed),
        "max_variants_per_line": int(args.max_variants_per_line),
        "z_sensitive_threshold": float(args.z_sensitive_threshold),
        "min_margin": float(args.min_margin),
        "split": {"n_train": len(train_list), "n_test": len(test_list), "test_frac": float(args.test_frac)},
        "none_threshold": float(args.none_threshold),
        "tune_none_threshold": bool(args.tune_none_threshold),
        "max_parp_fpr": None if args.max_parp_fpr is None else float(args.max_parp_fpr),
        "tuning": tuning,
        "use_cache_only": bool(args.use_cache_only),
        "cache_path": os.path.relpath(cache_path, results_dir),
        "label_distribution": dict(Counter([labels_by_mid[mid] for mid in chosen])),
        "methods": results,
        "notes": [
            "Preclinical benchmark: labels derived from GDSC2 Z_SCORE per class with ambiguity gating.",
            "S = Evo2 disruption; P = mechanistic pathway aggregation; D = DepMap lineage essentiality penalty.",
            "Use_cache_only is intended for fast smoke runs; full runs should enable Evo2 calls and persist cache.",
            "If tune_none_threshold is enabled, tuning occurs on TRAIN only and metrics are reported separately for TRAIN and TEST.",
        ],
    }

    out_path = os.path.join(results_dir, f"{args.out_prefix}_n{len(chosen)}.json")
    with open(out_path, "w") as f:
        json.dump(receipt, f, indent=2)

    print("Wrote receipt:", out_path)
    for m in receipt["methods"]:
        t = m["test"]
        print(
            m["name"],
            "test_acc=", round(t["accuracy"], 3),
            "test_macro_f1=", round(t["macro_f1"], 3),
            "test_parp_fpr=", round(t["parp_false_positive_rate"], 3),
        )


    return 0


if __name__ == "__main__":
    raise SystemExit(main())
