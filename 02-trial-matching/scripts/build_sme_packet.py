#!/usr/bin/env python3
"""Build a blinded SME adjudication packet (Top-N NCT IDs per case).

Writes:
- publications/02-trial-matching/receipts/latest/sme_packet.json

This packet intentionally omits scores to support blinding.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np


def cosine(a: np.ndarray, b: np.ndarray) -> float:
    da = float(np.linalg.norm(a))
    db = float(np.linalg.norm(b))
    if da == 0.0 or db == 0.0:
        return 0.0
    return float(np.dot(a / da, b / db))


def rank_trials(patient_vec: List[float], trial_moa: Dict[str, Any]) -> List[str]:
    pv = np.array(patient_vec, dtype=float)
    scored = []
    for nct_id, data in trial_moa.items():
        moa = (data or {}).get("moa_vector") or {}
        tv = np.array([
            float(moa.get("ddr", 0.0) or 0.0),
            float(moa.get("mapk", 0.0) or 0.0),
            float(moa.get("pi3k", 0.0) or 0.0),
            float(moa.get("vegf", 0.0) or 0.0),
            float(moa.get("her2", 0.0) or 0.0),
            float(moa.get("io", 0.0) or 0.0),
            float(moa.get("efflux", 0.0) or 0.0),
        ], dtype=float)
        scored.append((nct_id, cosine(pv, tv)))

    scored.sort(key=lambda x: x[1], reverse=True)
    return [x[0] for x in scored]


def main(argv: Optional[list[str]] = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--top_n", type=int, default=15)
    args = ap.parse_args(argv)

    pub_dir = Path(__file__).resolve().parents[1]
    eval_path = pub_dir / "data" / "labeled_eval_cases.json"
    trial_path = Path(__file__).resolve().parents[3] / "oncology-coPilot" / "oncology-backend-minimal" / "api" / "resources" / "trial_moa_vectors.json"

    if not eval_path.exists():
        print(f"❌ Missing labeled ev set: {eval_path}")
        return 2
    if not trial_path.exists():
        print(f"❌ Missing trial MoA vectors: {trial_path}")
        return 2

    ev = json.loads(eval_path.read_text())
    cases = ev.get("cases") or []
    if not cases:
        print("❌ labeled_eval_cases.json has no cases")
        return 2

    trial_moa = json.loads(trial_path.read_text())

    packet = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "top_n": int(args.top_n),
        "trial_moa_path": str(trial_path),
        "cases": [],
    }

    for c in cases:
        ranked = rank_trials(c["patient_moa_vector_7d"], trial_moa)[: int(args.top_n)]
        packet["cases"].append(
            {
                "case_id": c.get("case_id"),
                "disease": c.get("disease"),
                "ranked_nct_ids": ranked,
                "instructions": "SME: mark relevant NCT IDs; paste into ground_truth.relevant_trials in labeled_eval_cases.json",
            }
        )

    latest = pub_dir / "receipts" / "latest"
    latest.mkdir(parents=True, exist_ok=True)
    out_path = latest / "sme_packet.json"
    out_path.write_text(json.dumps(packet, indent=2))

    print(f"✅ Wrote SME packet: {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
