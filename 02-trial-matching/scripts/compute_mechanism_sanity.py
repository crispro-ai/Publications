#!/usr/bin/env python3
"""Compute receipt-backed 'mechanism sanity' metrics for trial matching.

This is NOT outcome validation.
It answers: "Given our trial MoA vectors, do DDR-tagged trials align more to a DDR-heavy 
patient mechanism vector than non-DDR trials?" (deterministic sanity check).

Zeta Protocol Update: Uses magnitude-weighted similarity instead of pure cosine.

Inputs:
- oncology-coPilot/oncology-backend-minimal/api/resources/trial_moa_vectors.json

Outputs:
- publications/02-trial-matching/receipts/<ts>/mechanism_sanity.json
- publications/02-trial-matching/receipts/latest/mechanism_sanity.json
"""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

import numpy as np


def now_ts() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def calculate_weighted_fit(patient_vector: np.ndarray, trial_vec: np.ndarray) -> float:
    """
    Magnitude-aware similarity (Zeta Protocol Fix - Option 1)
    fit = (patient_vector · trial_vector) / ||trial_vector||
    """
    denom = float(np.linalg.norm(trial_vec))
    if denom == 0.0:
        return 0.0
    return float(np.dot(patient_vector, trial_vec / denom))


def main(argv: Optional[list[str]] = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out_dir", type=str, default=None, help="Receipt directory (default: receipts/<ts>)")
    args = ap.parse_args(argv)

    pub_dir = Path(__file__).resolve().parents[1]
    trial_path = Path(__file__).resolve().parents[3] / "oncology-coPilot" / "oncology-backend-minimal" / "api" / "resources" / "trial_moa_vectors.json"
    if not trial_path.exists():
        print(f"❌ Missing trial MoA vectors: {trial_path}")
        return 2

    trial_moa: Dict[str, Any] = json.loads(trial_path.read_text())

    # Patient vector for sanity check: high DDR profile
    patient_vector = np.array([0.88, 0.12, 0.05, 0.02, 0.0, 0.0, 0.0], dtype=float)

    ddr = []
    non = []
    skipped = 0

    for _, data in trial_moa.items():
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

        if float(np.linalg.norm(tv)) == 0.0:
            skipped += 1
            continue

        fit = calculate_weighted_fit(patient_vector, tv)
        if float(moa.get("ddr", 0.0) or 0.0) > 0.5:
            ddr.append(fit)
        else:
            non.append(fit)

    mean_ddr = float(np.mean(ddr)) if ddr else 0.0
    mean_non = float(np.mean(non)) if non else 0.0

    out_dir = Path(args.out_dir).resolve() if args.out_dir else (pub_dir / "receipts" / now_ts())
    out_dir.mkdir(parents=True, exist_ok=True)

    payload = {
        "run": {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "trial_moa_path": str(trial_path),
            "trial_moa_sha256": sha256_file(trial_path),
            "n_trials": len(trial_moa),
            "n_skipped_zero_vector": skipped,
            "patient_vector_7d": patient_vector.tolist(),
            "ddr_tag_threshold": 0.5,
            "algorithm": "magnitude_weighted_similarity_v1"
        },
        "metrics": {
            "ddr_trials_count": len(ddr),
            "non_ddr_trials_count": len(non),
            "mean_ddr_fit": mean_ddr,
            "mean_non_ddr_fit": mean_non,
            "separation_delta": mean_ddr - mean_non,
        },
    }

    out_json = out_dir / "mechanism_sanity.json"
    out_json.write_text(json.dumps(payload, indent=2))

    latest = pub_dir / "receipts" / "latest"
    latest.mkdir(parents=True, exist_ok=True)
    (latest / "mechanism_sanity.json").write_text(out_json.read_text())

    print(f"✅ Wrote: {out_json}")
    print(f"✅ Updated latest: {latest / 'mechanism_sanity.json'}")
    return 0


if __name__ == "__main__":
    import sys
    raise SystemExit(main(sys.argv[1:]))

