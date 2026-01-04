#!/usr/bin/env python3
"""Evaluate trial ranking against a labeled evaluation set.

This is the missing piece needed to *prove* ranking claims (Top‑k/MRR/etc.)
for publications/02-trial-matching.

Inputs:
- Labeled cases: publications/02-trial-matching/data/labeled_eval_cases.json
- Trial MoA vectors: oncology-coPilot/oncology-backend-minimal/api/resources/trial_moa_vectors.json

Outputs (receipts):
- publications/02-trial-matching/receipts/<ts>/eval_ranking.json
- publications/02-trial-matching/receipts/latest/eval_ranking.json

Claim hygiene:
- If the labeled set is missing, this script exits non-zero.
- Metrics are only as valid as the labels' provenance.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np


def now_ts() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")


def cosine(a: np.ndarray, b: np.ndarray) -> float:
    da = float(np.linalg.norm(a))
    db = float(np.linalg.norm(b))
    if da == 0.0 or db == 0.0:
        return 0.0
    return float(np.dot(a / da, b / db))


def rank_trials(patient_vec: List[float], trial_moa: Dict[str, Any]) -> List[Tuple[str, float]]:
    pv = np.array(patient_vec, dtype=float)
    scored: List[Tuple[str, float]] = []
    for nct_id, data in trial_moa.items():
        moa_dict = (data or {}).get("moa_vector") or {}
        # 7D order matches trial_moa_vectors.json keys: ddr,mapk,pi3k,vegf,her2,io,efflux
        tv = np.array([
            float(moa_dict.get("ddr", 0.0) or 0.0),
            float(moa_dict.get("mapk", 0.0) or 0.0),
            float(moa_dict.get("pi3k", 0.0) or 0.0),
            float(moa_dict.get("vegf", 0.0) or 0.0),
            float(moa_dict.get("her2", 0.0) or 0.0),
            float(moa_dict.get("io", 0.0) or 0.0),
            float(moa_dict.get("efflux", 0.0) or 0.0),
        ], dtype=float)
        scored.append((nct_id, cosine(pv, tv)))
    scored.sort(key=lambda x: x[1], reverse=True)
    return scored


def recall_at_k(ranked_ids: List[str], relevant: set[str], k: int) -> float:
    if not relevant:
        return 0.0
    topk = set(ranked_ids[:k])
    return float(len(topk & relevant)) / float(len(relevant))


def mrr(ranked_ids: List[str], primary: Optional[str], relevant: set[str]) -> float:
    # If a single "primary" is provided, use it. Otherwise, use first relevant hit.
    targets: List[str] = [primary] if primary else []
    if not targets:
        targets = list(relevant)
    if not targets:
        return 0.0

    for i, rid in enumerate(ranked_ids, start=1):
        if rid in targets:
            return 1.0 / float(i)
    return 0.0


def main(argv: Optional[list[str]] = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--eval", type=str, default="../data/labeled_eval_cases.json", help="Labeled eval cases JSON")
    ap.add_argument("--trial_moa", type=str, default=None, help="Override path to trial_moa_vectors.json")
    ap.add_argument("--out_dir", type=str, default=None, help="Receipt output directory (default: receipts/<ts>)")
    args = ap.parse_args(argv)

    pub_dir = Path(__file__).resolve().parents[1]
    eval_path = (Path(args.eval) if args.eval else pub_dir / "data" / "labeled_eval_cases.json").resolve()

    if not eval_path.exists():
        print(f"❌ Missing labeled eval set: {eval_path}")
        print("   Create it using data/LABELED_EVAL_SCHEMA.md and re-run.")
        return 2

    if args.trial_moa:
        trial_path = Path(args.trial_moa).resolve()
    else:
        trial_path = Path(__file__).resolve().parents[3] / "oncology-coPilot" / "oncology-backend-minimal" / "api" / "resources" / "trial_moa_vectors.json"

    if not trial_path.exists():
        print(f"❌ Missing trial MoA vectors: {trial_path}")
        return 2

    ev = json.loads(eval_path.read_text())
    cases = (ev.get("cases") or [])
    trial_moa = json.loads(trial_path.read_text())

    if not cases:
        print("❌ Labeled eval set has no cases")
        return 2

    # Gate: require SME labels (non-empty relevant_trials) for every case
    for c in cases:
        cid = str(c.get("case_id") or "")
        gt = c.get("ground_truth") or {}
        rel_list = gt.get("relevant_trials") or []
        if not rel_list:
            print(f"❌ Case {cid}: ground_truth.relevant_trials is empty (SME labels required)")
            return 2

    # Compute metrics per case
    per_case = []
    r3s = []
    r5s = []
    r10s = []
    mrrs = []

    for c in cases:
        cid = str(c.get("case_id") or "")
        vec = c.get("patient_moa_vector_7d")
        gt = c.get("ground_truth") or {}
        rel = set(gt.get("relevant_trials") or [])
        primary = gt.get("primary_relevant_trial")

        if not (isinstance(vec, list) and len(vec) == 7):
            print(f"❌ Case {cid}: patient_moa_vector_7d must be length-7 list")
            return 2

        ranked = rank_trials(vec, trial_moa)
        ranked_ids = [x[0] for x in ranked]

        r3 = recall_at_k(ranked_ids, rel, 3)
        r5 = recall_at_k(ranked_ids, rel, 5)
        r10 = recall_at_k(ranked_ids, rel, 10)
        rr = mrr(ranked_ids, primary=primary, relevant=rel)

        per_case.append({
            "case_id": cid,
        "n_relevant": len(rel),
            "recall_at_3": r3,
            "recall_at_5": r5,
            "recall_at_10": r10,
            "mrr": rr,
            "top_10": ranked[:10],
        })

        r3s.append(r3)
        r5s.append(r5)
        r10s.append(r10)
        mrrs.append(rr)

    out_ts = now_ts()
    out_dir = Path(args.out_dir).resolve() if args.out_dir else (pub_dir / "receipts" / out_ts)
    out_dir.mkdir(parents=True, exist_ok=True)

    summary = {
        "run": {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "eval_path": str(eval_path),
            "trial_moa_path": str(trial_path),
            "n_cases": len(per_case),
            "n_trials": len(trial_moa),
        },
        "recall_at_3": float(np.mean(r3s)),
        "recall_at_5": float(np.mean(r5s)),
        "recall_at_10": float(np.mean(r10s)),
        "mrr": float(np.mean(mrrs)),
        "per_case": per_case,
    }

    out_json = out_dir / "eval_ranking.json"
    out_json.write_text(json.dumps(summary, indent=2))

    # refresh latest
    latest = pub_dir / "receipts" / "latest"
    latest.mkdir(parents=True, exist_ok=True)
    (latest / "eval_ranking.json").write_text(out_json.read_text())

    print(f"✅ Wrote receipts: {out_json}")
    print(f"✅ Updated latest: {latest / 'eval_ranking.json'}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
