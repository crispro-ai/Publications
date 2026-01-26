#!/usr/bin/env python3
"""
Replace stub chromatin in the 38-gene Target-Lock dataset with REAL Enformer predictions.

What this does
- Loads staged `../data/real_target_lock_data.csv` (8 missions × 38 genes).
- For each gene, queries Ensembl for gene locus and uses TSS as a consistent coordinate.
- Calls the backend Enformer client (ENFORMER_URL must be set) to get accessibility + provenance.
- Writes:
  - `../data/real_target_lock_data.csv` (overwritten) with updated chromatin + recomputed target_lock_score
  - `../data/chromatin_audit_enformer_38genes.csv` with per-gene details and stub-rate

Why TSS?
- The existing publication dataset does not include per-row genomic coordinates.
- TSS-based chromatin is a defensible, explicit approximation for "is the gene locus accessible".

Hard requirement for Option A
- This script FAILS if any Enformer calls fall back to deterministic stubs.

Usage
  venv/bin/python scripts/metastasis/update_target_lock_chromatin_enformer.py
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Dict, Optional, Tuple

import httpx
import pandas as pd

import asyncio


DATA_DIR = Path("publication/data")
IN_CSV = DATA_DIR / "real_target_lock_data.csv"
OUT_CSV = DATA_DIR / "real_target_lock_data.csv"  # overwrite (resubmission mode)
AUDIT_CSV = DATA_DIR / "chromatin_audit_enformer_38genes.csv"
TSS_CACHE_CSV = DATA_DIR / "gene_tss_grch38_38genes.csv"

RULES_PATH_DEFAULT = "oncology-coPilot/oncology-backend-minimal/api/config/metastasis_rules_v1.0.1.json"

WEIGHTS = {"functionality": 0.35, "essentiality": 0.35, "chromatin": 0.15, "regulatory": 0.15}

# Ensembl symbol aliases for common publication gene names
ENSEMBL_SYMBOL_ALIASES = {
    "VEGFR2": "KDR",
    "VEGFR1": "FLT1",
}



async def _ensembl_lookup_gene(gene: str) -> Dict:
    symbol = gene
    url = f"https://rest.ensembl.org/lookup/symbol/homo_sapiens/{symbol}?expand=0"
    headers = {"Content-Type": "application/json"}
    async with httpx.AsyncClient(timeout=httpx.Timeout(30.0, connect=10.0)) as client:
        r = await client.get(url, headers=headers)
        try:
            r.raise_for_status()
            return r.json()
        except httpx.HTTPStatusError:
            # Retry with alias if known (e.g., VEGFR2 -> KDR)
            alias = ENSEMBL_SYMBOL_ALIASES.get(gene.upper())
            if not alias or alias.upper() == gene.upper():
                raise
            url2 = f"https://rest.ensembl.org/lookup/symbol/homo_sapiens/{alias}?expand=0"
            r2 = await client.get(url2, headers=headers)
            r2.raise_for_status()
            js2 = r2.json()
            # Preserve original requested gene name for downstream reporting
            js2["_requested_symbol"] = gene
            js2["_resolved_symbol"] = alias
            return js2


async def _gene_tss(gene: str) -> Tuple[str, int]:
    js = await _ensembl_lookup_gene(gene)
    chrom = str(js.get("seq_region_name"))
    start = int(js.get("start"))
    end = int(js.get("end"))
    strand = int(js.get("strand", 1))
    tss = start if strand == 1 else end
    return chrom, tss


async def _chromatin_for_gene(gene: str, chrom: str, pos: int) -> Dict:
    # For locus accessibility we use reference sequence at TSS; no SNV is applied.
    payload = {
        "chrom": str(chrom),
        "pos": int(pos),
        "ref": "N",
        "alt": "N",
        "context_bp": 32000,
        "use_cache": True,
    }

    enformer_url = os.environ.get("ENFORMER_URL")
    if not enformer_url:
        raise RuntimeError("ENFORMER_URL must be set")

    async with httpx.AsyncClient(timeout=httpx.Timeout(300.0, connect=10.0)) as client:
        r = await client.post(f"{enformer_url}/predict", json=payload)
        r.raise_for_status()
        pred = r.json() or {}

    return {
        "gene": gene,
        "chrom": chrom,
        "pos": pos,
        "accessibility_score": float(pred.get("accessibility_score", 0.0)),
        "provenance": pred.get("provenance") or {},
    }


def _is_stub(prov: Dict) -> bool:
    return (prov or {}).get("method") == "deterministic_fallback"


async def main_async() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not IN_CSV.exists():
        raise FileNotFoundError(f"Missing input dataset: {IN_CSV}. Run staging first.")

    enformer_url = os.environ.get("ENFORMER_URL")
    if not enformer_url:
        raise RuntimeError("ENFORMER_URL must be set to your deployed Modal Enformer endpoint for Option A.")

    df = pd.read_csv(IN_CSV)
    if "mission" not in df.columns or "gene" not in df.columns:
        raise ValueError("Expected columns `gene` and `mission` in real_target_lock_data.csv")

    genes = sorted(df["gene"].unique())
    if len(genes) != 38:
        raise ValueError(f"Expected 38 genes, found {len(genes)}")

    # Load or build a frozen TSS coordinate map to avoid repeated Ensembl calls.
    if TSS_CACHE_CSV.exists():
        tss_df = pd.read_csv(TSS_CACHE_CSV)
        tss_map = {r["gene"]: (str(r["chrom"]), int(r["pos"])) for _, r in tss_df.iterrows()}
    else:
        tss_rows = []
        for g in genes:
            chrom, pos = await _gene_tss(g)
            tss_rows.append({"gene": g, "chrom": chrom, "pos": pos})
        tss_df = pd.DataFrame(tss_rows)
        tss_df.to_csv(TSS_CACHE_CSV, index=False)
        tss_map = {r["gene"]: (str(r["chrom"]), int(r["pos"])) for _, r in tss_df.iterrows()}

    # Fetch chromatin per gene (TSS-based)
    results = []
    for g in genes:
        chrom, pos = tss_map[g]
        results.append(await _chromatin_for_gene(g, chrom=chrom, pos=pos))

    audit = pd.DataFrame(
        [
            {
                "gene": r["gene"],
                "chrom": r["chrom"],
                "pos": r["pos"],
                "accessibility_score": r["accessibility_score"],
                "method": (r["provenance"] or {}).get("method"),
                "model": (r["provenance"] or {}).get("model"),
                "warning": (r["provenance"] or {}).get("warning"),
                "enformer_url": enformer_url,
            }
            for r in results
        ]
    )
    audit.to_csv(AUDIT_CSV, index=False)

    # Fail hard if any stub predictions occurred
    stub_count = int((audit["method"] == "deterministic_fallback").sum())
    if stub_count > 0:
        raise RuntimeError(
            f"Enformer stub fallback detected for {stub_count}/38 genes. "
            f"Fix ENFORMER_URL deployment before resubmission."
        )

    # Apply chromatin score to all missions for each gene
    chromatin_map = {r["gene"]: r["accessibility_score"] for r in results}
    df["chromatin"] = df["gene"].map(chromatin_map).astype(float)

    # Recompute target_lock_score using existing component scores
    df["target_lock_score"] = (
        df["functionality"].astype(float) * WEIGHTS["functionality"]
        + df["essentiality"].astype(float) * WEIGHTS["essentiality"]
        + df["chromatin"].astype(float) * WEIGHTS["chromatin"]
        + df["regulatory"].astype(float) * WEIGHTS["regulatory"]
    ).round(3)

    df.to_csv(OUT_CSV, index=False)

    print(f"✅ Wrote updated dataset (Enformer chromatin): {OUT_CSV}")
    print(f"✅ Wrote chromatin audit: {AUDIT_CSV}")


def main() -> None:
    asyncio.run(main_async())


if __name__ == "__main__":
    main()

