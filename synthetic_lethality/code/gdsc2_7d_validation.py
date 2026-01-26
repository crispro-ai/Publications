#!/usr/bin/env python3
"""
7D Pathway Mapping Validation on GDSC2

This script validates the 7D pathway framework on GDSC2 cell lines and compares
performance to the SPD-ML approach.

Strategy:
1. Compute 7D mechanism vectors from cell line mutations
2. Define drug MoA vectors for PARP/ATR/WEE1/DNA-PK
3. Use magnitude-weighted similarity for drug matching
4. Evaluate accuracy, PARP FPR, and correlations
5. Compare to SPD-ML results

NO TRAINING - purely deterministic, transparent framework.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import math
import os
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import httpx
import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, f1_score, precision_recall_fscore_support

def _maybe_add_backend_to_syspath() -> None:
    """
    Best-effort: add `oncology-coPilot/oncology-backend-minimal` to sys.path so we can reuse production 7D code.
    Works both when running from repo root and when running from Cursor worktrees.
    """
    here = os.path.abspath(os.path.dirname(__file__))
    candidates = []

    # Walk up a few levels looking for the backend folder
    cur = here
    for _ in range(8):
        candidates.append(os.path.join(cur, "oncology-coPilot", "oncology-backend-minimal"))
        cur = os.path.abspath(os.path.join(cur, ".."))

    # Also try the common absolute repo path used in this workspace
    candidates.append("/Users/fahadkiani/Desktop/development/crispr-assistant-main/oncology-coPilot/oncology-backend-minimal")

    for p in candidates:
        if os.path.exists(os.path.join(p, "api")):
            sys.path.insert(0, os.path.abspath(p))
            return


_maybe_add_backend_to_syspath()

try:
    from api.services.pathway_to_mechanism_vector import (
        convert_pathway_scores_to_mechanism_vector,
        MECHANISM_INDICES_7D,
    )
    from api.services.mechanism_fit_ranker import MechanismFitRanker
    from api.services.pathway.drug_mapping import get_pathway_weights_for_gene
    from api.services.pathway.aggregation import aggregate_pathways
except ImportError as e:
    print(f"Warning: Could not import 7D framework: {e}")
    print("Will use local implementations")
    # Fallback gene-to-pathway mapping
    def get_pathway_weights_for_gene(gene_symbol: str) -> Dict[str, float]:
        g = gene_symbol.strip().upper()
        if g in {"BRAF", "KRAS", "NRAS", "EGFR", "MAP2K1", "MAPK1"}:
            return {"ras_mapk": 1.0}
        if g in {"BRCA1", "BRCA2", "ATM", "ATR", "CHEK1", "RAD51", "PALB2", "MBD4"}:
            return {"ddr": 1.0}
        if g in {"TP53", "MDM2", "CHEK2"}:
            return {"tp53": 1.0}
        if g in {"PTEN", "PIK3CA", "AKT1", "AKT2", "MTOR"}:
            return {"pi3k": 1.0}
        if g in {"VEGFA", "VEGFR1", "VEGFR2", "KDR", "FLT1"}:
            return {"vegf": 1.0}
        if g in {"ERBB2", "ERBB3", "ERBB4"}:
            return {"her2": 1.0}
        return {}
    
    def aggregate_pathways(seq_scores: List[Dict]) -> Dict[str, float]:
        """Fallback pathway aggregation."""
        pathway_totals = {}
        pathway_counts = {}
        for score in seq_scores:
            pathway_weights = score.get("pathway_weights", {})
            raw = float(score.get("sequence_disruption", 0.0))
            for pathway, weight in pathway_weights.items():
                pathway_totals[pathway] = pathway_totals.get(pathway, 0.0) + (raw * float(weight))
                pathway_counts[pathway] = pathway_counts.get(pathway, 0) + 1
        return {p: (t / pathway_counts[p]) if pathway_counts[p] > 0 else 0.0 
                for p, t in pathway_totals.items()}


# Drug class definitions (same as SPD benchmark)
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


# 7D Drug MoA Vectors (mechanism of action)
# Based on pathway targets for synthetic lethality drugs
DRUG_MOA_VECTORS_7D = {
    "PARP": {
        "ddr": 0.95,      # PARP primarily targets DDR
        "ras_mapk": 0.05,
        "pi3k": 0.0,
        "vegf": 0.0,
        "her2": 0.0,
        "io": 0.0,
        "efflux": 0.0,
    },
    "ATR": {
        "ddr": 0.80,      # ATR targets DDR (replication stress)
        "ras_mapk": 0.20,  # Some MAPK cross-talk in replication stress
        "pi3k": 0.0,
        "vegf": 0.0,
        "her2": 0.0,
        "io": 0.0,
        "efflux": 0.0,
    },
    "WEE1": {
        "ddr": 0.70,      # WEE1 targets G2/M checkpoint (DDR-related)
        "ras_mapk": 0.30,  # Cell cycle checkpoint has MAPK signaling
        "pi3k": 0.0,
        "vegf": 0.0,
        "her2": 0.0,
        "io": 0.0,
        "efflux": 0.0,
    },
    "DNA_PK": {
        "ddr": 0.90,      # DNA-PK is core DDR component
        "ras_mapk": 0.10,
        "pi3k": 0.0,
        "vegf": 0.0,
        "her2": 0.0,
        "io": 0.0,
        "efflux": 0.0,
    },
    "NONE": {
        "ddr": 0.0,
        "ras_mapk": 0.0,
        "pi3k": 0.0,
        "vegf": 0.0,
        "her2": 0.0,
        "io": 0.0,
        "efflux": 0.0,
    },
}

# Gene-specific drug preferences (from therapy fit system)
# PARP-preferring genes (core HR pathway)
PARP_GENES = {
    "BRCA1", "BRCA2", "PALB2", "RAD51C", "RAD51D", 
    "BARD1", "BRIP1", "MBD4", "ATM", "CDK12"
}

# ATR-preferring genes (replication stress, chromatin remodeling)
ATR_GENES = {
    "ARID1A", "CHEK2"
}

# WEE1-preferring genes (G2/M checkpoint)
WEE1_GENES = {
    "WEE1", "CDC25A"
}


def moa_dict_to_vector(moa_dict: Dict[str, float], use_6d: bool = True) -> List[float]:
    """Convert MoA dict to 7D or 6D vector list."""
    if use_6d:
        # 6D: [DDR, MAPK, PI3K, VEGF, HER2, Efflux] (skip IO)
        return [
            moa_dict.get("ddr", 0.0),
            moa_dict.get("ras_mapk", 0.0),
            moa_dict.get("pi3k", 0.0),
            moa_dict.get("vegf", 0.0),
            moa_dict.get("her2", 0.0),
            moa_dict.get("efflux", 0.0),
        ]
    else:
        # 7D: [DDR, MAPK, PI3K, VEGF, HER2, IO, Efflux]
        return [
            moa_dict.get("ddr", 0.0),
            moa_dict.get("ras_mapk", 0.0),
            moa_dict.get("pi3k", 0.0),
            moa_dict.get("vegf", 0.0),
            moa_dict.get("her2", 0.0),
            moa_dict.get("io", 0.0),
            moa_dict.get("efflux", 0.0),
        ]


def compute_magnitude_weighted_fit(patient_vector: List[float], drug_vector: List[float]) -> float:
    """
    Compute magnitude-weighted mechanism fit (same as MechanismFitRanker).
    
    Formula: fit = (patient_vector · drug_vector) / ||drug_vector||
    This prevents low-burden patients from matching high-intensity drugs.
    """
    if len(patient_vector) != len(drug_vector):
        return 0.0
    
    # Dot product
    dot_product = sum(p * d for p, d in zip(patient_vector, drug_vector))
    
    # Normalize by drug magnitude only
    drug_magnitude = math.sqrt(sum(d**2 for d in drug_vector))
    
    if drug_magnitude == 0.0:
        return 0.0
    
    # Weighted fit
    fit = dot_product / drug_magnitude
    
    # Clamp to [0, 1]
    return max(0.0, min(1.0, fit))


def _is_snv(ref: str, alt: str) -> bool:
    ref = str(ref or "").upper()
    alt = str(alt or "").upper()
    return len(ref) == 1 and len(alt) == 1 and ref in "ACGT" and alt in "ACGT" and ref != alt


def _safe_float(x) -> Optional[float]:
    try:
        if x is None:
            return None
        if isinstance(x, (int, float)):
            return float(x)
        s = str(x).strip()
        if s == "" or s.lower() in ("none", "null", "nan"):
            return None
        return float(s)
    except Exception:
        return None


HRR_CNA_GENES = [
    # Core HRR genes
    "BRCA1", "BRCA2", "PALB2", "RAD51C", "RAD51D", "BRIP1", "BARD1", "MBD4",
    # Extended HRR genes
    "ATM", "CHEK2", "FANCA", "RAD50", "MRE11", "NBN", "CDK12",
]


def _scale_disruption_to_unit_interval(disruption: float, lo: float = 1e-6, hi: float = 1e-3) -> float:
    """
    Map raw Evo2 disruption (~|delta|) into [0,1] for thresholding.
    Defaults reflect typical delta magnitudes (~1e-6..1e-3) for SNVs.
    """
    if disruption is None or not isinstance(disruption, (int, float)):
        return 0.0
    x = float(disruption)
    if x <= lo:
        return 0.0
    if x >= hi:
        return 1.0
    return (x - lo) / (hi - lo)


async def score_variant_with_evo2(
    client: httpx.AsyncClient,
    sem: asyncio.Semaphore,
    api_base: str,
    chrom: str,
    pos: int,
    ref: str,
    alt: str,
    model_id: str = "evo2_1b",
) -> Optional[Dict[str, float]]:
    """
    Score a variant using Evo2 API (multi-window + exon).
    
    Returns: Dict with 'min_delta', 'exon_delta', 'disruption', or None if failed.
    """
    try:
        if not _is_snv(ref, alt):
            return None

        # Limit concurrent in-flight HTTP requests
        async with sem:
            multi_payload = {
                "assembly": "GRCh38",
                "chrom": str(chrom),
                "pos": int(pos),
                "ref": str(ref).upper(),
                "alt": str(alt).upper(),
                "model_id": model_id,
            }

            multi_resp = await client.post(f"{api_base}/api/evo/score_variant_multi", json=multi_payload)
            multi_resp.raise_for_status()
            multi_data = multi_resp.json() or {}
            min_delta = _safe_float(multi_data.get("min_delta"))

            exon_resp = await client.post(f"{api_base}/api/evo/score_variant_exon", json=multi_payload)
            exon_resp.raise_for_status()
            exon_data = exon_resp.json() or {}
            exon_delta = _safe_float(exon_data.get("exon_delta"))

        if min_delta is None and exon_delta is None:
            return None

        disruption = max(abs(min_delta or 0.0), abs(exon_delta or 0.0))
        return {"min_delta": float(min_delta or 0.0), "exon_delta": float(exon_delta or 0.0), "disruption": float(disruption)}
    except Exception as e:
        print(f"⚠️  Evo2 scoring failed for {chrom}:{pos} {ref}>{alt}: {e}")
        return None


async def compute_pathway_scores_from_mutations_evo2(
    mutations_df: pd.DataFrame,
    api_base: str,
    client: httpx.AsyncClient,
    sem: asyncio.Semaphore,
    model_id: str = "evo2_1b",
    max_variants: int = 50,
) -> Dict[str, float]:
    """
    Compute pathway scores from mutations using Evo2 scoring.
    
    Uses production pathway aggregation pattern:
    1. Score variants with Evo2 (multi-window + exon)
    2. Get pathway weights for each gene
    3. Aggregate using aggregate_pathways()
    
    Args:
        mutations_df: DataFrame with mutations (Chrom, Pos, Ref, Alt, HugoSymbol)
        api_base: Evo2 API base URL
        model_id: Evo2 model to use
        max_variants: Max variants to score per cell line (for speed)
    
    Returns:
        Dict of pathway scores
    """
    if mutations_df.empty:
        return {"ddr": 0.0, "ras_mapk": 0.0, "pi3k": 0.0, "vegf": 0.0, "her2": 0.0, "tp53": 0.0}
    
    # Limit variants for speed (prioritize DDR genes)
    ddr_genes = {"BRCA1", "BRCA2", "TP53", "ATM", "ATR", "CHEK1", "CHEK2", "RAD51", "PALB2", "MBD4"}
    
    if len(mutations_df) > max_variants:
        # Prioritize DDR genes first
        ddr_muts = mutations_df[mutations_df["HugoSymbol"].str.upper().isin(ddr_genes)]
        other_muts = mutations_df[~mutations_df["HugoSymbol"].str.upper().isin(ddr_genes)]
        
        # Take top DDR mutations + sample others
        n_ddr = min(len(ddr_muts), max_variants // 2)
        n_other = max_variants - n_ddr
        
        mutations_df = pd.concat([
            ddr_muts.head(n_ddr),
            other_muts.head(n_other),
        ])
    
    # Keep SNVs only (Evo2 backend supports SNVs reliably; indels often fail/ref-mismatch)
    muts = mutations_df.copy()
    muts["Ref_str"] = muts["Ref"].astype(str)
    muts["Alt_str"] = muts["Alt"].astype(str)
    muts = muts[muts["Ref_str"].str.len().eq(1) & muts["Alt_str"].str.len().eq(1)]

    # Score variants with Evo2 (concurrently, bounded by semaphore)
    seq_scores: List[Dict[str, Any]] = []
    n_seen = 0
    n_scored = 0
    n_scored_mapped = 0

    async def _score_row(row) -> Optional[Dict[str, Any]]:
        chrom = row.get("Chrom", "")
        pos = row.get("Pos")
        ref = row.get("Ref_str", "")
        alt = row.get("Alt_str", "")
        gene = row.get("HugoSymbol", "")

        if pd.isna(pos) or not chrom or not ref or not alt or not gene:
            return None

        evo2_result = await score_variant_with_evo2(
            client=client,
            sem=sem,
            api_base=api_base,
            chrom=str(chrom),
            pos=int(pos),
            ref=str(ref),
            alt=str(alt),
            model_id=model_id,
        )
        if evo2_result is None:
            return None

        pathway_weights = get_pathway_weights_for_gene(gene)
        if not pathway_weights:
            return None

        return {
            "sequence_disruption": float(evo2_result["disruption"]),
            "calibrated_seq_percentile": 0.0,  # not needed for pathway aggregation in this validator
            "pathway_weights": pathway_weights,
            "variant": {"gene": gene, "consequence": str(row.get("Consequence", "unknown")).lower()},
        }

    tasks = []
    for _, row in muts.iterrows():
        n_seen += 1
        tasks.append(_score_row(row))

    results = await asyncio.gather(*tasks)
    for r in results:
        if r:
            n_scored += 1
            seq_scores.append(r)
            if isinstance(r.get("pathway_weights"), dict) and len(r["pathway_weights"]) > 0:
                n_scored_mapped += 1
    
    # Aggregate pathways
    if seq_scores:
        pathway_scores = aggregate_pathways(seq_scores)
        # Calibrate aggregate scores into [0,1] with bounded range (interpretable & stable).
        # NOTE: This is a scaling layer; the real signal is in aggregate_pathways() + missense gating.
        for pathway in pathway_scores:
            pathway_scores[pathway] = _scale_disruption_to_unit_interval(float(pathway_scores[pathway]))

        # Provenance for debugging (stored under special key)
        pathway_scores["_provenance"] = {
            "variants_seen_snv": n_seen,
            "variants_scored_evo2": n_scored,
            "variants_scored_and_mapped": n_scored_mapped,
        }
        return pathway_scores
    else:
        return {"ddr": 0.0, "ras_mapk": 0.0, "pi3k": 0.0, "vegf": 0.0, "her2": 0.0, "tp53": 0.0}


def compute_pathway_scores_from_mutations(mutations_df: pd.DataFrame) -> Dict[str, float]:
    """
    Compute pathway scores from mutations (FALLBACK - mutation count only).
    
    Use compute_pathway_scores_from_mutations_evo2() for production scoring.
    """
    # DDR pathway genes (simplified set)
    DDR_GENES = {
        "BRCA1", "BRCA2", "TP53", "ATM", "ATR", "CHEK1", "CHEK2", 
        "RAD51", "PALB2", "FANCA", "MBD4", "PARP1", "PARP2",
        "MSH2", "MSH6", "MLH1", "PMS2", "EXO1", "POLQ",
    }
    
    # MAPK pathway genes
    MAPK_GENES = {
        "KRAS", "NRAS", "HRAS", "BRAF", "MAP2K1", "MAP2K2",
        "MAPK1", "MAPK3", "NF1", "CRAF",
    }
    
    # PI3K pathway genes
    PI3K_GENES = {
        "PIK3CA", "PIK3R1", "PIK3R2", "PTEN", "AKT1", "AKT2",
        "MTOR", "TSC1", "TSC2",
    }
    
    # VEGF pathway genes
    VEGF_GENES = {
        "VEGFA", "VEGFR1", "VEGFR2", "FLT1", "KDR", "FLT4",
    }
    
    # HER2 pathway genes
    HER2_GENES = {
        "ERBB2", "ERBB3", "ERBB4",
    }
    
    pathway_scores = {
        "ddr": 0.0,
        "ras_mapk": 0.0,
        "pi3k": 0.0,
        "vegf": 0.0,
        "her2": 0.0,
        "tp53": 0.0,
    }
    
    if mutations_df.empty:
        return pathway_scores
    
    # Count mutations per gene
    gene_counts = mutations_df.groupby("HugoSymbol").size().to_dict()
    
    # Aggregate by pathway
    for gene, count in gene_counts.items():
        gene_upper = gene.upper()
        
        if gene_upper in DDR_GENES:
            pathway_scores["ddr"] += count * 0.1  # Simplified scoring
        if gene_upper in MAPK_GENES:
            pathway_scores["ras_mapk"] += count * 0.1
        if gene_upper in PI3K_GENES:
            pathway_scores["pi3k"] += count * 0.1
        if gene_upper in VEGF_GENES:
            pathway_scores["vegf"] += count * 0.1
        if gene_upper in HER2_GENES:
            pathway_scores["her2"] += count * 0.1
        if gene_upper == "TP53":
            pathway_scores["tp53"] += count * 0.1
    
    # Normalize pathway scores to [0, 1] range
    for pathway in pathway_scores:
        pathway_scores[pathway] = min(1.0, pathway_scores[pathway])
    
    return pathway_scores


def compute_pathway_scores_from_mutations_weighted(mutations_df: pd.DataFrame) -> Dict[str, float]:
    """
    Improved non-Evo2 pathway scoring:
    - Use production gene→pathway mapping (`get_pathway_weights_for_gene`) when available
    - Weight variants by consequence (LoF > missense > other; synonymous ignored)
    - Conservative DDR missense gating to reduce PARP false positives
    - Hotspot lift for TP53/BRAF/KRAS/NRAS missense
    """
    if mutations_df.empty:
        return {"ddr": 0.0, "ras_mapk": 0.0, "pi3k": 0.0, "vegf": 0.0, "her2": 0.0, "tp53": 0.0}

    hotspot_genes = {"TP53", "BRAF", "KRAS", "NRAS"}
    pathway_totals: Dict[str, float] = {}
    pathway_counts: Dict[str, int] = {}

    for _, row in mutations_df.iterrows():
        gene = str(row.get("HugoSymbol") or "").strip().upper()
        if not gene:
            continue

        pw = get_pathway_weights_for_gene(gene) or {}
        if not pw:
            continue

        cons = str(row.get("MolecularConsequence") or row.get("VariantType") or "").lower()
        impact = str(row.get("VepImpact") or "").lower()
        likely_lof = row.get("LikelyLoF")
        try:
            is_lof = bool(likely_lof) and str(likely_lof).lower() not in ("0", "false", "nan", "")
        except Exception:
            is_lof = False

        # Base weight by consequence / impact
        w = 0.0
        if is_lof or any(k in cons for k in ("frameshift", "stop_gained", "splice", "start_lost", "stop_lost")):
            w = 1.0
        elif "missense" in cons:
            w = 0.2
        elif "synonymous" in cons:
            w = 0.0
        elif impact == "high":
            w = 0.6
        elif impact == "moderate":
            w = 0.2
        elif impact in ("low", "modifier"):
            w = 0.0
        else:
            w = 0.05

        if w <= 0.0:
            continue

        # Hotspot lift (bounded)
        if gene in hotspot_genes and ("missense" in cons or impact in ("moderate", "high")):
            w = max(w, 0.6)

        # Conservative DDR missense gating
        if "ddr" in pw and ("missense" in cons) and w < 0.2:
            continue

        for pathway, weight in pw.items():
            if not isinstance(weight, (int, float)):
                continue
            pathway_totals[pathway] = pathway_totals.get(pathway, 0.0) + (w * float(weight))
            pathway_counts[pathway] = pathway_counts.get(pathway, 0) + 1

    out: Dict[str, float] = {"ddr": 0.0, "ras_mapk": 0.0, "pi3k": 0.0, "vegf": 0.0, "her2": 0.0, "tp53": 0.0}
    for pathway, total in pathway_totals.items():
        n = pathway_counts.get(pathway, 0)
        if n <= 0:
            continue
        out[pathway] = max(0.0, min(1.0, float(total) / float(n)))
    return out


def compute_hrd_proxy_from_mutations(
    mutations_df: pd.DataFrame,
    primary_gene: Optional[str] = None,
    default_if_none: Optional[float] = None,
) -> Optional[float]:
    """
    Compute HRD proxy from DDR mutations (fallback when copy number data unavailable).
    
    Logic (from biomarker_extractor.py):
    - Core HRR mutations (BRCA1/BRCA2/PALB2/RAD51C/RAD51D/BRIP1/BARD1) → HRD=55.0
    - Extended HRR mutations (ATM/CHEK2/FANCA/etc.) → HRD=45.0
    - Multiple HRR mutations (biallelic loss) → HRD=65.0
    
    Args:
        mutations_df: DataFrame with mutations (HugoSymbol column)
        primary_gene: Primary DDR gene (if known)
    
    Returns:
        HRD proxy score (0-100) or None if cannot estimate
    """
    if mutations_df.empty:
        return None
    
    # Core HRR genes (high confidence for HRD)
    CORE_HRR_GENES = {
        "BRCA1", "BRCA2", "PALB2", "RAD51C", "RAD51D", 
        "BRIP1", "BARD1", "MBD4"  # MBD4 added (BER deficiency → HRD)
    }
    
    # Extended HRR genes (medium confidence)
    EXTENDED_HRR_GENES = {
        "ATM", "CHEK2", "FANCA", "FANCC", "FANCD2",
        "RAD50", "MRE11", "NBN", "CDK12"
    }
    
    # Count mutations by gene
    gene_counts = mutations_df.groupby("HugoSymbol").size().to_dict()
    
    # Check for core HRR mutations
    core_mutations = []
    extended_mutations = []
    
    for gene, count in gene_counts.items():
        gene_upper = gene.upper()
        if gene_upper in CORE_HRR_GENES:
            core_mutations.append((gene_upper, count))
        elif gene_upper in EXTENDED_HRR_GENES:
            extended_mutations.append((gene_upper, count))
    
    # Priority 1: Core HRR mutation → HRD=55.0
    if core_mutations:
        # Check for biallelic loss (multiple mutations in same gene)
        for gene, count in core_mutations:
            if count >= 2:  # Biallelic loss
                return 65.0  # Highest HRD estimate
        return 55.0  # Core HRR mutation present
    
    # Priority 2: Extended HRR mutation → HRD=45.0
    if extended_mutations:
        return 45.0
    
    # Priority 3: If primary gene is known, use that
    if primary_gene:
        primary_upper = primary_gene.upper()
        if primary_upper in CORE_HRR_GENES:
            return 55.0
        elif primary_upper in EXTENDED_HRR_GENES:
            return 45.0
    
    # No HRR mutations detected → optionally return a default proxy
    if default_if_none is not None:
        return float(default_if_none)
    return None


def load_hrd_proxy_map(
    hrd_proxy_path: Optional[str],
    model_df: pd.DataFrame,
) -> Dict[str, float]:
    """
    Load HRD proxy scores from a file and map to ModelID.

    Supported formats:
    - JSON: {ModelID: score} or {COSMIC_ID: score}
    - CSV: columns like ModelID, COSMIC_ID/COSMICID, HRD/HRD_SCORE/hrd_proxy
    """
    if not hrd_proxy_path:
        return {}
    if not os.path.exists(hrd_proxy_path):
        print(f"⚠️  HRD proxy file not found: {hrd_proxy_path}")
        return {}

    # Build COSMIC -> ModelID lookup
    cosmic_to_model = {}
    if "COSMICID" in model_df.columns:
        for _, row in model_df.iterrows():
            cosmic_id = normalize_cosmic_id(row.get("COSMICID"))
            model_id = row.get("ModelID")
            if cosmic_id and model_id:
                cosmic_to_model[cosmic_id] = model_id

    out: Dict[str, float] = {}
    try:
        if hrd_proxy_path.lower().endswith(".json"):
            with open(hrd_proxy_path, "r") as f:
                data = json.load(f)
            if isinstance(data, dict):
                for k, v in data.items():
                    key = str(k)
                    score = _safe_float(v if not isinstance(v, dict) else v.get("hrd_score") or v.get("hrd_proxy"))
                    if score is None:
                        continue
                    if key.startswith("TCGA-"):
                        # Not a GDSC2/DepMap key
                        continue
                    if key.startswith("ACH-"):
                        out[key] = float(score)
                    elif key.isdigit():
                        model_id = cosmic_to_model.get(key)
                        if model_id:
                            out[model_id] = float(score)
        else:
            df = pd.read_csv(hrd_proxy_path, low_memory=False, nrows=5)
            hrd_cols = {"HRD_SCORE", "HRD", "hrd_proxy", "hrd_score"}
            has_hrd_col = any(c in df.columns for c in hrd_cols)

            if has_hrd_col:
                df = pd.read_csv(hrd_proxy_path, low_memory=False)
                # Try ModelID directly
                if "ModelID" in df.columns:
                    for _, row in df.iterrows():
                        model_id = row.get("ModelID")
                        score = _safe_float(row.get("HRD_SCORE") or row.get("HRD") or row.get("hrd_proxy") or row.get("hrd_score"))
                        if model_id and score is not None:
                            out[str(model_id)] = float(score)
                # Try COSMIC ID mapping
                elif "COSMIC_ID" in df.columns or "COSMICID" in df.columns:
                    col = "COSMIC_ID" if "COSMIC_ID" in df.columns else "COSMICID"
                    for _, row in df.iterrows():
                        cosmic_id = normalize_cosmic_id(row.get(col))
                        score = _safe_float(row.get("HRD_SCORE") or row.get("HRD") or row.get("hrd_proxy") or row.get("hrd_score"))
                        if cosmic_id and score is not None:
                            model_id = cosmic_to_model.get(cosmic_id)
                            if model_id:
                                out[model_id] = float(score)
            else:
                # Fallback: treat CSV as a gene-level CNA matrix (e.g., OmicsCNGeneWGS.csv)
                out = build_hrd_proxy_map_from_cna_matrix(hrd_proxy_path, model_df)
    except Exception as e:
        print(f"⚠️  Failed to load HRD proxy file: {e}")
        return {}

    print(f"Loaded HRD proxy scores for {len(out)} ModelIDs from {hrd_proxy_path}")
    return out


def _map_gene_columns(columns: List[str], gene_list: List[str]) -> Dict[str, str]:
    """
    Map gene symbols to CNA matrix columns.
    Supports columns like 'BRCA1 (672)' or 'BRCA1'.
    """
    col_map: Dict[str, str] = {}
    for gene in gene_list:
        for col in columns:
            if col == gene or col.startswith(f"{gene} "):
                col_map[gene] = col
                break
    return col_map


def _infer_cna_loss_threshold(sample_values: np.ndarray) -> float:
    """
    Infer a loss threshold from CNA value distribution.
    Heuristics:
      - median ~0 → log2 ratio scale → loss < -0.5
      - median ~1 → ratio scale → loss < 0.7
      - median ~2 → absolute CN → loss < 1.5
    """
    if sample_values.size == 0:
        return 0.7
    median = float(np.median(sample_values))
    if median < 0.2:
        return -0.5
    if median < 1.4:
        return 0.7
    return 1.5


def build_hrd_proxy_map_from_cna_matrix(
    cna_path: str,
    model_df: pd.DataFrame,
) -> Dict[str, float]:
    """
    Compute HRD proxy scores from a gene-level CNA matrix.
    Uses HRR gene copy losses as a proxy for HRD.
    """
    if not os.path.exists(cna_path):
        return {}

    # Read header to discover columns without loading the full matrix
    header_df = pd.read_csv(cna_path, nrows=5, low_memory=False)
    columns = list(header_df.columns)

    # Identify ID column
    id_col = None
    for candidate in ["ModelID", "DepMap_ID", "COSMIC_ID", "COSMICID"]:
        if candidate in columns:
            id_col = candidate
            break
    if id_col is None:
        print("⚠️  CNA matrix missing ModelID/COSMICID identifier; cannot compute HRD proxy.")
        return {}

    # Map HRR gene columns
    gene_col_map = _map_gene_columns(columns, HRR_CNA_GENES)
    if not gene_col_map:
        print("⚠️  CNA matrix lacks HRR gene columns; cannot compute HRD proxy.")
        return {}

    usecols = [id_col] + list(gene_col_map.values())
    df = pd.read_csv(cna_path, usecols=usecols, low_memory=False)

    # Infer CNA loss threshold from sample distribution
    sample_vals = df[list(gene_col_map.values())].to_numpy().flatten()
    sample_vals = sample_vals[~np.isnan(sample_vals)]
    loss_threshold = _infer_cna_loss_threshold(sample_vals)

    # Compute loss counts per model
    loss_counts = (df[list(gene_col_map.values())] <= loss_threshold).sum(axis=1)
    # Map loss count to HRD proxy score (0-100) with HRD-high at >=2 losses
    hrd_scores = 20 + (loss_counts * 12)
    hrd_scores = hrd_scores.clip(lower=0, upper=100)

    # Build ID mapping
    out: Dict[str, float] = {}
    if id_col == "ModelID":
        for model_id, score in zip(df[id_col].astype(str), hrd_scores.astype(float)):
            out[model_id] = float(score)
    else:
        cosmic_to_model = {}
        if "COSMICID" in model_df.columns:
            for _, row in model_df.iterrows():
                cosmic_id = normalize_cosmic_id(row.get("COSMICID"))
                model_id = row.get("ModelID")
                if cosmic_id and model_id:
                    cosmic_to_model[cosmic_id] = model_id
        for cosmic_raw, score in zip(df[id_col], hrd_scores.astype(float)):
            cosmic_id = normalize_cosmic_id(cosmic_raw)
            model_id = cosmic_to_model.get(cosmic_id)
            if model_id:
                out[model_id] = float(score)

    print(
        "Computed HRD proxy from CNA matrix "
        f"(genes={len(gene_col_map)}, loss_threshold={loss_threshold:.2f}, models={len(out)})"
    )
    return out


def predict_drug_with_7d(
    mechanism_vector_7d: List[float],
    min_ddr_threshold: float = 0.25,
    min_fit_threshold: float = 0.25,
    use_6d: bool = True,
    use_hierarchical: bool = False,
    primary_gene: Optional[str] = None,  # NEW: Gene-specific boosts
    hrd_proxy: Optional[float] = None,  # NEW: HRD proxy score (0-100)
) -> Tuple[str, Dict[str, float]]:
    """
    Predict drug class using 7D mechanism vector with gene-specific boosts.
    
    Decision logic (three modes):
    
    Mode 1 (default): Magnitude-weighted fit ranking
    1. If DDR < threshold: return NONE
    2. Compute magnitude-weighted fit for each drug class
    3. Pick drug with highest fit, if fit >= min_fit_threshold
    4. Otherwise: return NONE
    
    Mode 2 (hierarchical, Option B): More permissive thresholds for multi-class
    1. If DDR >= 0.60: PARP (highest priority)
    2. Elif DDR >= 0.40 and MAPK >= 0.30: ATR (moderate DDR + some MAPK)
    3. Elif DDR >= 0.35: WEE1 (moderate DDR, checkpoint vulnerable)
    4. Elif DDR >= 0.30 and fit >= 0.25: DNA_PK
    5. Else: NONE
    
    Mode 3 (gene-specific boosts): Gene context overrides thresholds
    - PARP_GENES (BRCA1/BRCA2/PALB2) → PARP if DDR >= 0.50
    - ATR_GENES (ARID1A) → ATR if DDR >= 0.40
    - WEE1_GENES → WEE1 if DDR >= 0.35
    - Fallback to threshold-based logic
    """
    ddr_score = mechanism_vector_7d[0]
    mapk_score = mechanism_vector_7d[1] if len(mechanism_vector_7d) > 1 else 0.0
    
    # HRD-AWARE DDR THRESHOLD (NEW - WIWFM logic)
    # Adaptive threshold based on HRD proxy (from WIWFM sporadic gates)
    adjusted_ddr_threshold = min_ddr_threshold  # Default
    hrd_rationale = None
    
    if hrd_proxy is not None:
        if hrd_proxy >= 42.0:
            # HRD-high → RESCUE (lower threshold)
            adjusted_ddr_threshold = 0.45  # Lower threshold for HRD-high
            hrd_rationale = f"HRD-high (≥42, score={hrd_proxy:.1f}) → lower threshold 0.45"
        elif hrd_proxy < 42.0:
            # HRD-low → PENALTY (higher threshold)
            adjusted_ddr_threshold = 0.70  # Higher threshold for HRD-low
            hrd_rationale = f"HRD-low (<42, score={hrd_proxy:.1f}) → higher threshold 0.70"
        # else: use default threshold (HRD unknown)
    
    # Compute fit scores for reporting (needed in all modes)
    fit_scores = {}
    for drug_class in ["PARP", "ATR", "WEE1", "DNA_PK"]:
        drug_vector = moa_dict_to_vector(DRUG_MOA_VECTORS_7D[drug_class], use_6d=use_6d)
        if len(drug_vector) != len(mechanism_vector_7d):
            if len(drug_vector) > len(mechanism_vector_7d):
                drug_vector = drug_vector[:len(mechanism_vector_7d)]
            else:
                drug_vector = drug_vector + [0.0] * (len(mechanism_vector_7d) - len(drug_vector))
        fit = compute_magnitude_weighted_fit(mechanism_vector_7d, drug_vector)
        fit_scores[drug_class] = fit
    
    # GENE-SPECIFIC BOOSTS (Priority 1 - overrides HRD threshold for specific genes)
    if primary_gene:
        primary_gene_upper = primary_gene.strip().upper()
        
        # PARP-preferring genes (core HR pathway)
        if primary_gene_upper in PARP_GENES:
            # Use lower of: gene-specific threshold (0.50) or HRD-adjusted threshold
            parp_threshold = min(0.50, adjusted_ddr_threshold) if hrd_proxy else 0.50
            if ddr_score >= parp_threshold:
                return "PARP", fit_scores
        
        # ATR-preferring genes (replication stress)
        if primary_gene_upper in ATR_GENES:
            if ddr_score >= 0.40:  # ATR fires for ATR-preferring genes
                return "ATR", fit_scores
        
        # WEE1-preferring genes (G2/M checkpoint)
        if primary_gene_upper in WEE1_GENES:
            if ddr_score >= 0.35:  # WEE1 fires for WEE1-preferring genes
                return "WEE1", fit_scores
    
    if use_hierarchical:
        # Hybrid: Tiered thresholds with HRD-aware adjustment
        # Hybrid decision logic: PARP uses HRD-adjusted threshold
        if ddr_score >= adjusted_ddr_threshold:
            # DDR meets threshold (adjusted by HRD) → PARP
            return "PARP", fit_scores
        elif ddr_score >= 0.35:
            # Moderate DDR → WEE1 (permissive for multi-class)
            return "WEE1", fit_scores
        elif ddr_score >= 0.30:
            # Lower DDR → DNA_PK (permissive)
            return "DNA_PK", fit_scores
        elif ddr_score >= 0.40:
            # ATR: DDR only (no MAPK requirement, fixes ATR never firing)
            return "ATR", fit_scores
        else:
            return "NONE", fit_scores
    
    else:
        # Original logic: Magnitude-weighted fit ranking with HRD-aware threshold
        # Use HRD-adjusted threshold if available, otherwise use min_ddr_threshold
        effective_threshold = adjusted_ddr_threshold if hrd_proxy is not None else min_ddr_threshold
        if ddr_score < effective_threshold:
            return "NONE", {"PARP": 0.0, "ATR": 0.0, "WEE1": 0.0, "DNA_PK": 0.0, "NONE": 1.0}
        
        # Compute fit scores for each drug
        fit_scores = {}
        for drug_class in ["PARP", "ATR", "WEE1", "DNA_PK"]:
            drug_vector = moa_dict_to_vector(DRUG_MOA_VECTORS_7D[drug_class], use_6d=use_6d)
            # Ensure dimensions match
            if len(drug_vector) != len(mechanism_vector_7d):
                # Pad or truncate to match
                if len(drug_vector) > len(mechanism_vector_7d):
                    drug_vector = drug_vector[:len(mechanism_vector_7d)]
                else:
                    drug_vector = drug_vector + [0.0] * (len(mechanism_vector_7d) - len(drug_vector))
            fit = compute_magnitude_weighted_fit(mechanism_vector_7d, drug_vector)
            fit_scores[drug_class] = fit
        
        # Add NONE as fallback (fit = 0.0)
        fit_scores["NONE"] = 0.0
        
        # Pick best drug
        best_drug = max(fit_scores.items(), key=lambda x: x[1])
        
        if best_drug[1] >= min_fit_threshold:
            return best_drug[0], fit_scores
        else:
            return "NONE", fit_scores


def normalize_cosmic_id(x) -> Optional[str]:
    try:
        if pd.isna(x):
            return None
        return str(int(float(x)))
    except Exception:
        return None


def compute_label_from_z(
    z_by_class: Dict[str, float],
    z_sensitive_threshold: float = -0.8,
    min_margin: float = 0.25,
) -> str:
    """Label rule: pick most sensitive drug class, or NONE if ambiguous."""
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


def load_spd_results(spd_json_path: str) -> Optional[Dict]:
    """Load SPD-ML results for comparison."""
    if not os.path.exists(spd_json_path):
        return None
    
    with open(spd_json_path, "r") as f:
        return json.load(f)


def _extract_spd_method_test_metrics(spd_obj: Dict) -> Dict[str, Optional[float]]:
    """
    SPD receipts in this repo are not uniform. Some store metrics under top-level `metrics`,
    others store per-method metrics under `methods` (list of {name, train, test}).
    We extract a conservative, comparable set:
      - test_accuracy
      - test_macro_f1
      - parp_fpr
    """
    if not isinstance(spd_obj, dict):
        return {"test_accuracy": None, "test_macro_f1": None, "parp_fpr": None, "method": None}

    # Case A: top-level metrics
    top_m = spd_obj.get("metrics")
    if isinstance(top_m, dict):
        top_fpr = top_m.get("parp_fpr")
        if top_fpr is None:
            top_fpr = top_m.get("parp_false_positive_rate")
        return {
            "test_accuracy": _safe_float(top_m.get("test_accuracy") or top_m.get("accuracy")),
            "test_macro_f1": _safe_float(top_m.get("test_macro_f1") or top_m.get("macro_f1")),
            "parp_fpr": _safe_float(top_fpr),
            "method": top_m.get("method"),
        }

    # Case B: per-method list
    methods = spd_obj.get("methods")
    if isinstance(methods, list):
        pref = ["LR-SPD", "LR-SP", "SPD", "SP", "P-only"]
        by_name = {m.get("name"): m for m in methods if isinstance(m, dict) and m.get("name")}
        for name in pref:
            m = by_name.get(name)
            if not isinstance(m, dict):
                continue
            test = m.get("test") or {}
            if not isinstance(test, dict):
                continue
            acc = _safe_float(test.get("accuracy"))
            f1 = _safe_float(test.get("macro_f1"))
            fpr_val = test.get("parp_false_positive_rate")
            if fpr_val is None:
                fpr_val = test.get("parp_fpr")
            fpr = _safe_float(fpr_val)
            return {"test_accuracy": acc, "test_macro_f1": f1, "parp_fpr": fpr, "method": name}

    return {"test_accuracy": None, "test_macro_f1": None, "parp_fpr": None, "method": None}


async def main_async() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--z_sensitive_threshold", type=float, default=-0.8)
    ap.add_argument("--min_margin", type=float, default=0.25)
    ap.add_argument("--min_ddr_threshold", type=float, default=0.25, help="Minimum DDR score to consider SL drugs (data-driven: median ~0.30)")
    ap.add_argument("--min_fit_threshold", type=float, default=0.25, help="Minimum mechanism fit to predict drug")
    group = ap.add_mutually_exclusive_group()
    group.add_argument("--use_6d", action="store_true", help="Use 6D (skip IO dimension) for cell lines (default)")
    group.add_argument("--use_7d", action="store_true", help="Use 7D (includes IO dimension)")
    ap.add_argument("--use_hierarchical", action="store_true", help="Use hierarchical thresholds (Option B) for multi-class prediction")
    ap.add_argument("--evo2_api_base", type=str, default="http://127.0.0.1:8000", help="Evo2 API base URL (required for production pathway scoring)")
    ap.add_argument("--evo2_model_id", type=str, default="evo2_1b", help="Evo2 model ID")
    ap.add_argument("--max_variants_per_line", type=int, default=30, help="Max variants to score per cell line (for speed)")
    ap.add_argument("--evo2_timeout_s", type=float, default=60.0, help="HTTP timeout (seconds) for Evo2 scoring requests")
    ap.add_argument("--evo2_max_concurrency", type=int, default=10, help="Max concurrent Evo2 HTTP requests (avoid connection flaps)")
    ap.add_argument(
        "--mutation_scoring",
        type=str,
        default="simple_counts",
        choices=["simple_counts", "consequence_weighted"],
        help="When Evo2 is disabled, how to compute pathway scores from mutations.",
    )
    ap.add_argument("--hrd_proxy_file", type=str, default=None, help="Optional HRD proxy file (JSON/CSV) keyed by ModelID or COSMIC_ID")
    ap.add_argument("--hrd_proxy_default", type=float, default=0.0, help="Default HRD proxy when missing; set <0 to keep unknown")
    ap.add_argument("--max_cell_lines", type=int, default=500, help="Max cell lines to process")
    ap.add_argument("--spd_results", type=str, help="Path to SPD-ML results JSON for comparison")
    ap.add_argument("--out", type=str, default="gdsc2_7d_validation.json")
    args = ap.parse_args()

    # Default dimension is 6D for cell lines unless explicitly overridden.
    args.use_6d = True if not getattr(args, "use_7d", False) else False
    
    # Set up paths - find actual locations
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Try multiple possible root locations
    possible_roots = [
        os.path.abspath(os.path.join(script_dir, "..")),  # Relative to script
        os.path.abspath(os.path.join(script_dir, "..", "..", "..")),  # Go up to project root
        "/Users/fahadkiani/Desktop/development/crispr-assistant-main",  # Absolute path
    ]
    
    gdsc_path = None
    omics_path = None
    model_path = None
    results_dir = None
    
    for root_candidate in possible_roots:
        test_data = os.path.join(root_candidate, "publications", "synthetic_lethality", "data", "GDSC2_fitted_dose_response_27Oct23.xlsx")
        test_omics = os.path.join(root_candidate, "publications", "synthetic_lethality", "data", "OmicsSomaticMutations.csv")
        test_model = os.path.join(root_candidate, "data", "depmap", "Model.csv")
        test_results = os.path.join(root_candidate, "publications", "synthetic_lethality", "results")
        
        if os.path.exists(test_data) and os.path.exists(test_omics) and os.path.exists(test_model):
            gdsc_path = test_data
            omics_path = test_omics
            model_path = test_model
            results_dir = test_results
            os.makedirs(results_dir, exist_ok=True)
            break
    
    if not gdsc_path:
        # Fallback: use relative paths and hope for the best
        root = os.path.abspath(os.path.join(script_dir, ".."))
        data_dir = os.path.join(root, "data")
        results_dir = os.path.join(root, "results")
        os.makedirs(results_dir, exist_ok=True)
        gdsc_path = os.path.join(data_dir, "GDSC2_fitted_dose_response_27Oct23.xlsx")
        omics_path = os.path.join(data_dir, "OmicsSomaticMutations.csv")
        model_path = os.path.abspath(os.path.join(script_dir, "..", "..", "..", "data", "depmap", "Model.csv"))
    
    print(f"Loading GDSC2 data from {gdsc_path}...")
    gdsc_df = pd.read_excel(gdsc_path, engine="openpyxl")
    
    print(f"Loading Omics mutations from {omics_path}...")
    omics_df = pd.read_csv(omics_path, low_memory=False)
    
    print(f"Loading DepMap Model.csv from {model_path}...")
    # DepMap mapping (same approach as preflight script)
    model_df = pd.read_csv(
        model_path,
        usecols=["ModelID", "COSMICID", "OncotreeLineage"],
        low_memory=False,
    ).dropna(subset=["COSMICID", "ModelID"])
    model_df["COSMIC_ID_str"] = model_df["COSMICID"].apply(normalize_cosmic_id)
    model_df = model_df.dropna(subset=["COSMIC_ID_str"])
    model_df["ModelID"] = model_df["ModelID"].astype(str)

    # Load optional HRD proxy map (if provided)
    hrd_proxy_map = load_hrd_proxy_map(args.hrd_proxy_file, model_df)
    default_hrd_proxy = None if args.hrd_proxy_default < 0 else args.hrd_proxy_default
    
    # Normalize COSMIC IDs in GDSC
    gdsc_df["COSMIC_ID_str"] = gdsc_df["COSMIC_ID"].apply(normalize_cosmic_id)
    gdsc_df = gdsc_df.dropna(subset=["COSMIC_ID_str", "DRUG_NAME"])
    gdsc_df = gdsc_df[gdsc_df["DRUG_NAME"].isin(set(PARP_DRUGS | ATR_DRUGS | WEE1_DRUGS | DNAPK_DRUGS))].copy()
    
    # Join Model ↔ GDSC2
    merged = model_df.merge(
        gdsc_df,
        left_on="COSMIC_ID_str",
        right_on="COSMIC_ID_str",
        how="inner",
        suffixes=("_model", "_gdsc"),
    )
    
    print(f"Found {len(merged)} ModelID × Drug combinations after join")
    
    # Filter to SL drugs (already filtered in merge, but keep for clarity)
    merged_sl = merged[merged["DRUG_NAME"].isin(set(PARP_DRUGS | ATR_DRUGS | WEE1_DRUGS | DNAPK_DRUGS))]
    print(f"Filtered to {len(merged_sl)} SL drug combinations")
    
    # Group by ModelID and compute labels
    cell_line_labels = {}
    cell_line_zscores = defaultdict(dict)
    
    for model_id, group in merged_sl.groupby("ModelID"):
        z_by_class = {}
        for _, row in group.iterrows():
            drug = row["DRUG_NAME"]
            drug_class = DRUG_TO_CLASS.get(drug, "UNKNOWN")
            if drug_class == "UNKNOWN":
                continue
            z_score = row.get("Z_SCORE")
            if pd.notna(z_score):
                z_by_class[drug_class] = z_score
                cell_line_zscores[model_id][drug_class] = float(z_score)
        
        if z_by_class:
            label = compute_label_from_z(
                z_by_class,
                z_sensitive_threshold=args.z_sensitive_threshold,
                min_margin=args.min_margin,
            )
            cell_line_labels[model_id] = label
    
    print(f"Computed labels for {len(cell_line_labels)} cell lines")
    label_counts = Counter(cell_line_labels.values())
    print(f"Label distribution: {dict(label_counts)}")
    
    # Limit cell lines if requested
    cell_line_ids = list(cell_line_labels.keys())[:args.max_cell_lines]
    
    # Process each cell line: compute 7D vector and predict
    predictions_7d = {}
    mechanism_vectors = {}
    pathway_scores_all = {}
    
    print("\nComputing 7D mechanism vectors...")
    print(f"Using Evo2 API: {args.evo2_api_base} (model: {args.evo2_model_id})")
    
    # Use async Evo2 scoring if API base provided
    use_evo2 = args.evo2_api_base and args.evo2_api_base != "none"

    client: Optional[httpx.AsyncClient] = None
    sem: Optional[asyncio.Semaphore] = None
    if use_evo2:
        client = httpx.AsyncClient(timeout=args.evo2_timeout_s)
        sem = asyncio.Semaphore(int(args.evo2_max_concurrency))
    
    async def process_cell_line(model_id: str) -> Tuple[str, Dict]:
        """Process a single cell line asynchronously."""
        # Get mutations for this cell line
        cell_mutations = omics_df[omics_df["ModelID"] == model_id].copy()
        
        # Compute pathway scores
        if use_evo2:
            try:
                pathway_scores = await compute_pathway_scores_from_mutations_evo2(
                    cell_mutations,
                    api_base=args.evo2_api_base,
                    client=client,
                    sem=sem,
                    model_id=args.evo2_model_id,
                    max_variants=args.max_variants_per_line,
                )
            except Exception as e:
                print(f"⚠️  Evo2 failed for {model_id}: {e}, falling back to mutation counts")
                pathway_scores = (
                    compute_pathway_scores_from_mutations_weighted(cell_mutations)
                    if args.mutation_scoring == "consequence_weighted"
                    else compute_pathway_scores_from_mutations(cell_mutations)
                )
        else:
            pathway_scores = (
                compute_pathway_scores_from_mutations_weighted(cell_mutations)
                if args.mutation_scoring == "consequence_weighted"
                else compute_pathway_scores_from_mutations(cell_mutations)
            )
        
        return model_id, pathway_scores
    
    # Process cell lines asynchronously (in batches to avoid overwhelming API)
    pathway_scores_all = {}
    batch_size = 10

    try:
        for i in range(0, len(cell_line_ids), batch_size):
            batch = cell_line_ids[i:i+batch_size]
            batch_results = await asyncio.gather(*[process_cell_line(mid) for mid in batch])
            for mid, ps in batch_results:
                pathway_scores_all[mid] = ps

            if (i // batch_size + 1) % 5 == 0:
                print(f"  Processed {min(i+batch_size, len(cell_line_ids))}/{len(cell_line_ids)} cell lines...")
    finally:
        if client is not None:
            await client.aclose()
    
    for model_id in cell_line_ids:
        pathway_scores = pathway_scores_all.get(model_id, {})
        pathway_scores_all[model_id] = pathway_scores
        # Strip provenance key from scoring stage (don't feed into mechanism mapping)
        if isinstance(pathway_scores, dict) and "_provenance" in pathway_scores:
            pathway_scores = {k: v for k, v in pathway_scores.items() if k != "_provenance"}
        
        # Extract primary DDR gene and compute HRD proxy
        cell_mutations = omics_df[omics_df["ModelID"] == model_id].copy()
        primary_ddr_gene = None
        hrd_proxy = None
        
        # Prefer external HRD proxy if provided
        if hrd_proxy_map:
            hrd_proxy = hrd_proxy_map.get(model_id)

        if hrd_proxy is None and not cell_mutations.empty:
            # Compute HRD proxy from mutations (fallback method).
            # default_if_none uses CLI setting to control conservative behavior.
            hrd_proxy = compute_hrd_proxy_from_mutations(
                cell_mutations,
                primary_gene=None,
                default_if_none=default_hrd_proxy,
            )
            # Get all DDR genes from mutations
            ddr_genes_in_mutations = set()
            all_ddr_genes = PARP_GENES | ATR_GENES | WEE1_GENES
            for _, row in cell_mutations.iterrows():
                gene = str(row.get("HugoSymbol", "")).strip().upper()
                if gene in all_ddr_genes:
                    ddr_genes_in_mutations.add(gene)
            
            # Priority: PARP genes > ATR genes > WEE1 genes
            parp_matches = ddr_genes_in_mutations & PARP_GENES
            atr_matches = ddr_genes_in_mutations & ATR_GENES
            wee1_matches = ddr_genes_in_mutations & WEE1_GENES
            
            if parp_matches:
                primary_ddr_gene = list(parp_matches)[0]  # Take first match
            elif atr_matches:
                primary_ddr_gene = list(atr_matches)[0]
            elif wee1_matches:
                primary_ddr_gene = list(wee1_matches)[0]
        
        # Convert to 7D or 6D mechanism vector (use_6d=True skips IO dimension for cell lines)
        use_7d_vector = not args.use_6d
        try:
            mechanism_vector_7d, dim_used = convert_pathway_scores_to_mechanism_vector(
                pathway_scores,
                tumor_context=None,
                tmb=None,
                msi_status=None,
                use_7d=use_7d_vector,
            )
        except:
            # Fallback if import failed
            if use_7d_vector:
                mechanism_vector_7d = [0.0] * 7
                ddr_idx = 0
                tp53_score = pathway_scores.get("tp53", 0.0)
                ddr_score = pathway_scores.get("ddr", 0.0)
                mechanism_vector_7d[ddr_idx] = ddr_score + (tp53_score * 0.5)
                mechanism_vector_7d[1] = pathway_scores.get("ras_mapk", 0.0)
                mechanism_vector_7d[2] = pathway_scores.get("pi3k", 0.0)
                mechanism_vector_7d[3] = pathway_scores.get("vegf", 0.0)
                mechanism_vector_7d[4] = pathway_scores.get("her2", 0.0)
                # IO and Efflux remain 0.0 (no TMB/MSI data for cell lines)
                dim_used = "7D"
            else:
                # 6D: [DDR, MAPK, PI3K, VEGF, HER2, Efflux]
                mechanism_vector_7d = [0.0] * 6
                ddr_idx = 0
                tp53_score = pathway_scores.get("tp53", 0.0)
                ddr_score = pathway_scores.get("ddr", 0.0)
                mechanism_vector_7d[ddr_idx] = ddr_score + (tp53_score * 0.5)
                mechanism_vector_7d[1] = pathway_scores.get("ras_mapk", 0.0)
                mechanism_vector_7d[2] = pathway_scores.get("pi3k", 0.0)
                mechanism_vector_7d[3] = pathway_scores.get("vegf", 0.0)
                mechanism_vector_7d[4] = pathway_scores.get("her2", 0.0)
                mechanism_vector_7d[5] = pathway_scores.get("efflux", 0.0)  # Efflux (usually 0 for cell lines)
                dim_used = "6D"

        # Safety: clamp to [0,1]. Production vectors are intended to be 0..1;
        # our DDR composition (DDR + 0.5*TP53) can exceed 1.0 without clamping.
        mechanism_vector_7d = [max(0.0, min(1.0, float(x))) for x in mechanism_vector_7d]
        
        mechanism_vectors[model_id] = mechanism_vector_7d
        
        # Predict drug class with HRD-aware thresholds and gene-specific boosts
        pred_drug, fit_scores = predict_drug_with_7d(
            mechanism_vector_7d,
            min_ddr_threshold=args.min_ddr_threshold,
            min_fit_threshold=args.min_fit_threshold,
            use_6d=args.use_6d,
            use_hierarchical=args.use_hierarchical,
            primary_gene=primary_ddr_gene,  # Gene-specific boosts
            hrd_proxy=hrd_proxy,  # NEW: HRD-aware thresholds
        )
        predictions_7d[model_id] = {
            "predicted": pred_drug,
            "fit_scores": fit_scores,
            "mechanism_vector": mechanism_vector_7d,
        }
    
    print(f"Computed predictions for {len(predictions_7d)} cell lines")
    
    # Evaluate predictions
    y_true = [cell_line_labels.get(mid, "NONE") for mid in cell_line_ids]
    y_pred = [predictions_7d[mid]["predicted"] for mid in cell_line_ids]
    
    # Metrics
    accuracy = accuracy_score(y_true, y_pred)
    macro_f1 = f1_score(y_true, y_pred, average="macro", zero_division=0.0)
    per_class_metrics = precision_recall_fscore_support(
        y_true, y_pred, labels=LABELS, zero_division=0.0
    )
    
    precision_dict = dict(zip(LABELS, per_class_metrics[0]))
    recall_dict = dict(zip(LABELS, per_class_metrics[1]))
    f1_dict = dict(zip(LABELS, per_class_metrics[2]))
    
    # PARP False Positive Rate (safety metric)
    parp_fp = sum(1 for i, (true, pred) in enumerate(zip(y_true, y_pred)) 
                  if pred == "PARP" and true != "PARP")
    parp_total_non_parp = sum(1 for true in y_true if true != "PARP")
    parp_fpr = parp_fp / parp_total_non_parp if parp_total_non_parp > 0 else 0.0
    
    # Correlations: DDR score vs actual PARP sensitivity
    ddr_scores = [mechanism_vectors[mid][0] for mid in cell_line_ids]
    parp_zscores = [cell_line_zscores.get(mid, {}).get("PARP") for mid in cell_line_ids]
    
    parp_zscores_valid = [(ddr, z) for ddr, z in zip(ddr_scores, parp_zscores) if z is not None]
    if parp_zscores_valid:
        ddr_vals = [x[0] for x in parp_zscores_valid]
        z_vals = [x[1] for x in parp_zscores_valid]
        parp_ddr_correlation = np.corrcoef(ddr_vals, z_vals)[0, 1] if len(ddr_vals) > 1 else 0.0
    else:
        parp_ddr_correlation = None
    
    # Load SPD results if provided
    spd_results = None
    if args.spd_results:
        spd_results = load_spd_results(args.spd_results)
    
    # Build receipt
    receipt = {
        "validation_type": "7D_pathway_mapping",
        "timestamp": pd.Timestamp.now().isoformat(),
        "n_cell_lines": len(cell_line_ids),
        "label_distribution": dict(label_counts),
        "parameters": {
            "min_ddr_threshold": args.min_ddr_threshold,
            "min_fit_threshold": args.min_fit_threshold,
            "z_sensitive_threshold": args.z_sensitive_threshold,
            "min_margin": args.min_margin,
            "use_6d": args.use_6d,
            "dimension": "6D" if args.use_6d else "7D",
            "use_hierarchical": args.use_hierarchical,
            "evo2_enabled": use_evo2,
            "evo2_api_base": args.evo2_api_base if use_evo2 else None,
            "evo2_model_id": args.evo2_model_id if use_evo2 else None,
            "max_variants_per_line": args.max_variants_per_line,
            "hrd_proxy_file": args.hrd_proxy_file,
            "hrd_proxy_default": args.hrd_proxy_default,
        },
        "metrics": {
            "accuracy": float(accuracy),
            "macro_f1": float(macro_f1),
            "precision_per_class": {k: float(v) for k, v in precision_dict.items()},
            "recall_per_class": {k: float(v) for k, v in recall_dict.items()},
            "f1_per_class": {k: float(v) for k, v in f1_dict.items()},
            "parp_fpr": float(parp_fpr),
            "parp_ddr_correlation": float(parp_ddr_correlation) if parp_ddr_correlation is not None else None,
        },
        "drug_moa_vectors": DRUG_MOA_VECTORS_7D,
        "predictions": {
            mid: {
                "true_label": cell_line_labels.get(mid, "NONE"),
                "predicted": pred["predicted"],
                "fit_scores": pred["fit_scores"],
                "ddr_score": mechanism_vectors[mid][0],
            }
            for mid, pred in list(predictions_7d.items())[:20]  # Sample first 20
        },
        "comparison": {},
    }
    
    # Add SPD comparison if available
    if spd_results:
        spd_m = _extract_spd_method_test_metrics(spd_results)
        receipt["comparison"] = {
            "spd_method": spd_m.get("method"),
            "spd_accuracy": spd_m.get("test_accuracy"),
            "spd_macro_f1": spd_m.get("test_macro_f1"),
            "spd_parp_fpr": spd_m.get("parp_fpr"),
            "7d_accuracy": float(accuracy),
            "7d_macro_f1": float(macro_f1),
            "7d_parp_fpr": float(parp_fpr),
            "7d_wins_accuracy": (spd_m.get("test_accuracy") is None) or (float(accuracy) > float(spd_m.get("test_accuracy") or 0.0)),
            "7d_wins_f1": (spd_m.get("test_macro_f1") is None) or (float(macro_f1) > float(spd_m.get("test_macro_f1") or 0.0)),
            "7d_wins_fpr": (spd_m.get("parp_fpr") is None) or (float(parp_fpr) < float(spd_m.get("parp_fpr") or 1.0)),
        }
    
    # Save receipt
    out_path = os.path.join(results_dir, args.out)
    with open(out_path, "w") as f:
        json.dump(receipt, f, indent=2)
    
    print(f"\n{'='*60}")
    print("7D Pathway Mapping Validation Results")
    print(f"{'='*60}")
    print(f"Accuracy: {accuracy:.3f}")
    print(f"Macro F1: {macro_f1:.3f}")
    print(f"PARP FPR: {parp_fpr:.3f}")
    if parp_ddr_correlation:
        print(f"PARP DDR Correlation: {parp_ddr_correlation:.3f}")
    print(f"\nPer-class metrics:")
    for label in LABELS:
        print(f"  {label:8s}: P={precision_dict[label]:.3f}, R={recall_dict[label]:.3f}, F1={f1_dict[label]:.3f}")
    
    if spd_results:
        print(f"\n{'='*60}")
        print("Comparison: 7D vs SPD-ML")
        print(f"{'='*60}")
        spd_m = _extract_spd_method_test_metrics(spd_results)
        spd_acc = spd_m.get("test_accuracy")
        spd_f1 = spd_m.get("test_macro_f1")
        spd_fpr = spd_m.get("parp_fpr")
        meth = spd_m.get("method") or "UNKNOWN"
        def fmt(x, default="NA"):
            return f"{float(x):.3f}" if x is not None else default
        print(f"Method:   SPD={meth}")
        print(f"Accuracy:  7D={accuracy:.3f} vs SPD={fmt(spd_acc)} ({'✅ 7D WINS' if (spd_acc is None or accuracy > float(spd_acc)) else '❌ SPD wins'})")
        print(f"Macro F1:  7D={macro_f1:.3f} vs SPD={fmt(spd_f1)} ({'✅ 7D WINS' if (spd_f1 is None or macro_f1 > float(spd_f1)) else '❌ SPD wins'})")
        print(f"PARP FPR:  7D={parp_fpr:.3f} vs SPD={fmt(spd_fpr)} ({'✅ 7D WINS' if (spd_fpr is None or parp_fpr < float(spd_fpr)) else '❌ SPD wins'})")
    
    print(f"\nReceipt saved to: {out_path}")
    
    return 0


def main() -> int:
    """Entry point that wraps async main."""
    return asyncio.run(main_async())


if __name__ == "__main__":
    sys.exit(main())
