#!/usr/bin/env python3
"""Generate adversarial-audit proof receipts for the trial-matching bundle.

Writes to `publications/02-trial-matching/receipts/latest/`:
- zeta_fix_validation.json (before/after cosine vs magnitude-weighted)
- kras_g12c_edge_case.json (MAPK patient -> MAPK trials)
- io_dimension_validation.json (IO patient -> IO trials)

These receipts are *mechanistic proofs* and do not claim clinical outcome benefit.

Reproduce:
  python3 publications/02-trial-matching/scripts/generate_adversarial_audit_receipts.py
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

import numpy as np


ROOT = Path(__file__).resolve().parents[3]
PUB_DIR = Path(__file__).resolve().parents[1]
RECEIPTS_DIR = PUB_DIR / "receipts" / "latest"

BACKEND_DIR = ROOT / "oncology-coPilot" / "oncology-backend-minimal"
TRIAL_MOA_PATH = BACKEND_DIR / "api" / "resources" / "trial_moa_vectors.json"


def cosine(a: np.ndarray, b: np.ndarray) -> float:
    denom = float(np.linalg.norm(a) * np.linalg.norm(b))
    if denom == 0.0:
        return 0.0
    return float(np.dot(a, b) / denom)


def weighted(a: np.ndarray, b: np.ndarray) -> float:
    denom = float(np.linalg.norm(b))
    if denom == 0.0:
        return 0.0
    return max(0.0, min(1.0, float(np.dot(a, b) / denom)))


def load_trials() -> Dict[str, Any]:
    return json.loads(TRIAL_MOA_PATH.read_text())


def top_trials(patient_vec: np.ndarray, trials: Dict[str, Any], k: int = 10) -> List[Dict[str, Any]]:
    out = []
    for nct, data in trials.items():
        moa = data.get("moa_vector") or {}
        tv = np.array(
            [
                moa.get("ddr", 0.0),
                moa.get("mapk", 0.0),
                moa.get("pi3k", 0.0),
                moa.get("vegf", 0.0),
                moa.get("her2", 0.0),
                moa.get("io", 0.0),
                moa.get("efflux", 0.0),
            ],
            dtype=float,
        )
        if float(np.linalg.norm(tv)) == 0.0:
            continue
        fit = weighted(patient_vec, tv)
        out.append(
            {
                "nct_id": nct,
                "fit": round(fit, 6),
                "primary_moa": (data.get("provenance") or {}).get("primary_moa", ""),
                "moa_vector": moa,
            }
        )

    out.sort(key=lambda x: x["fit"], reverse=True)
    return out[:k]


def main() -> int:
    RECEIPTS_DIR.mkdir(parents=True, exist_ok=True)

    trials = load_trials()

    # Audit 1: Zeta fix
    low = np.array([0.1, 0, 0, 0, 0, 0, 0], dtype=float)
    high = np.array([0.88, 0, 0, 0, 0, 0, 0], dtype=float)
    ddr_trial = np.array([1.0, 0, 0, 0, 0, 0, 0], dtype=float)

    zeta = {
        "run": {"generated_at": datetime.now(timezone.utc).isoformat()},
        "case_low": {
            "patient_vector": low.tolist(),
            "trial_vector": ddr_trial.tolist(),
            "before_cosine": round(cosine(low, ddr_trial), 6),
            "after_weighted": round(weighted(low, ddr_trial), 6),
        },
        "case_high": {
            "patient_vector": high.tolist(),
            "trial_vector": ddr_trial.tolist(),
            "before_cosine": round(cosine(high, ddr_trial), 6),
            "after_weighted": round(weighted(high, ddr_trial), 6),
        },
        "notes": [
            "Cosine is magnitude-invariant: low burden can produce a false perfect match.",
            "Weighted fit clamps to [0,1] and reflects patient burden.",
        ],
    }
    (RECEIPTS_DIR / "zeta_fix_validation.json").write_text(json.dumps(zeta, indent=2))

    # Audit 7: KRAS G12C (MAPK-high prototype)
    kras = np.array([0.0, 0.9, 0.0, 0.0, 0.0, 0.0, 0.0], dtype=float)
    kras_out = {
        "run": {"generated_at": datetime.now(timezone.utc).isoformat()},
        "patient_vector": kras.tolist(),
        "top_10": top_trials(kras, trials, k=10),
        "notes": [
            "This is a synthetic edge-case prototype for discrimination testing.",
        ],
    }
    (RECEIPTS_DIR / "kras_g12c_edge_case.json").write_text(json.dumps(kras_out, indent=2))

    # Audit 8: IO-high prototype
    io = np.array([0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0], dtype=float)
    io_out = {
        "run": {"generated_at": datetime.now(timezone.utc).isoformat()},
        "patient_vector": io.tolist(),
        "top_10": top_trials(io, trials, k=10),
        "notes": [
            "This is a synthetic edge-case prototype for discrimination testing.",
        ],
    }
    (RECEIPTS_DIR / "io_dimension_validation.json").write_text(json.dumps(io_out, indent=2))

    print("Wrote:")
    print("-", RECEIPTS_DIR / "zeta_fix_validation.json")
    print("-", RECEIPTS_DIR / "kras_g12c_edge_case.json")
    print("-", RECEIPTS_DIR / "io_dimension_validation.json")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
