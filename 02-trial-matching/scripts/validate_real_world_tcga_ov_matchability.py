#!/usr/bin/env python3
"""TCGA-OV Real Validation: Matchability Prevalence (best_fit > threshold)

This is a *real-cohort* validation of the claim:
  "X% of TCGA-OV patients have at least one mechanism-aligned trial (best_fit > 0.5)"

Important:
- This is NOT an outcomes validation.
- Trial bank is the local MoA library (`trial_moa_vectors.json`).
- Patient vectors are derived from *available cohort biomarkers* (HRD proxy, BRCA somatic, TMB, MSI).

Outputs:
- publications/02-trial-matching/receipts/latest/real_world_tcga_ov_validation.json

Reproduce:
- python3 publications/02-trial-matching/scripts/validate_real_world_tcga_ov_matchability.py
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np


ROOT = Path(__file__).resolve().parents[3]
PUB_DIR = Path(__file__).resolve().parents[1]
RECEIPTS_DIR = PUB_DIR / "receipts" / "latest"

BACKEND_DIR = ROOT / "oncology-coPilot" / "oncology-backend-minimal"
TRIAL_MOA_PATH = BACKEND_DIR / "api" / "resources" / "trial_moa_vectors.json"
TCGA_OV_PATH = BACKEND_DIR / "biomarker_enriched_cohorts" / "data" / "tcga_ov_enriched_v2.json"


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def weighted_fit(patient_vec: np.ndarray, trial_vec: np.ndarray) -> float:
    """Magnitude-weighted similarity v1: (patient·trial)/||trial||, clamped to [0,1]."""
    denom = float(np.linalg.norm(trial_vec))
    if denom == 0.0:
        return 0.0
    score = float(np.dot(patient_vec, trial_vec) / denom)
    return max(0.0, min(1.0, score))


def build_patient_vector(p: Dict[str, Any]) -> np.ndaray:
    """Construct a 7D patient vector from TCGA-OV enriched cohort fields.

    Dimensions: [DDR, MAPK, PI3K, VEGF, HER2, IO, Efflux]

    NOTE: TCGA-OV enriched cohort does not contain somatic mutation lists here, so we use:
    - DDR: HRD proxy bucket + BRCA somatic indicator
    - IO: TMB + MSI status
    All other axes are set to 0.0 for this cohort-level validation.
    """
    vec = np.zeros(7, dtype=float)

    # DDR (index 0)
    hrd_map = {"HRD-High": 0.8, "HRD-Intermediate": 0.4, "HRD-Low": 0.1}
    vec[0] = float(hrd_map.get(p.get("hrd_proxy"), 0.0))
    if p.get("brca_somatic"):
        vec[0] = max(vec[0], 0.95)

    # IO (index 5)
    tmb = p.get("tmb")
    if isinstance(tmb, (int, float)):
        if tmb >= 20:
            vec[5] = 1.0
        elif tmb >= 10:
            vec[5] = 0.5
    if str(p.get("msi_status") or "").upper() == "MSI-H":
        vec[5] = 1.0

    return vec


def main() -> int:
    RECEIPTS_DIR.mkdir(parents=True, exist_ok=True)

    if not TRIAL_MOA_PATH.exists():
        raise SystemExit(f"Missing trial MoA file: {TRIAL_MOA_PATH}")
    if not TCGA_OV_PATH.exists():
        raise SystemExit(f"Missing TCGA-OV cohort file: {TCGA_OV_PATH}")

    trial_moa = json.loads(TRIAL_MOA_PATH.read_text())
    cohort = json.loads(TCGA_OV_PATH.read_text())
    patients = (cohort.get("cohort") or {}).get("patients") or []

    threshold = 0.5

    raw_results: List[Dict[str, Any]] = []
    for p in patients:
        pid = p.get("patient_id")
        vec = build_patient_vector(p)

        best = 0.0
        n_matches = 0

        for nct, tv in trial_moa.items():
            moa = tv.get("moa_vector") or {}
            trial_vec = np.array(
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
            if float(np.linalg.norm(trial_vec)) == 0.0:
                continue

            fit = weighted_fit(vec, trial_vec)
            if fit > best:
                best = fit
            if fit > threshold:
                n_matches += 1

        raw_results.append(
            {
                "patient_id": pid,
                "vector": vec.tolist(),
                "best_fit": round(best, 6),
                "n_matches_gt_threshold": int(n_matches),
                "os_days": (p.get("outcomes") or {}).get("os_days"),
                "os_event": (p.get("outcomes") or {}).get("os_event"),
            }
        )

    n_patients = len(raw_results)
    n_matchable = sum(1 for r in raw_results if r["best_fit"] > threshold)
    pct = (n_matchable / n_patients * 100.0) if n_patients else 0.0

    out = {
        "run": {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "trial_moa_path": str(TRIAL_MOA_PATH),
            "trial_moa_sha256": _sha256(TRIAL_MOA_PATH),
            "tcga_ov_path": str(TCGA_OV_PATH),
            "tcga_ov_sha256": _sha256(TCGA_OV_PATH),
            "n_trials": int(len(trial_moa)),
            "n_patients": int(n_patients),
            "threshold": {"best_fit_gt": threshold},
            "algorithm": "magnitude_weighted_similarity_v1",
            "patient_vector_source": "tcga_ov_enriched_v2 (hrd_proxy/brca_somatic/tmb/msi_status)",
        },
        "metrics": {
            "n_matchable": int(n_matchable),
            "pct_matchable": round(pct, 3),
        },
        "raw_results": raw_results,
        "notes": [
            "This is a real-cohort prevalence computation, not an outcomes validation.",
            "Non-DDR axes are 0.0 here because the cohort JSON lacks full somatic mutation lists.",
        ],
    }

    out_path = RECEIPTS_DIR / "real_world_tcga_ov_validation.json"
    out_path.write_text(json.dumps(out, indent=2))

    print(f"# TCGA-OV matchability")
    print(f"n_patients={n_patients} n_matchable={n_matchable} pct={pct:.2f}%")
    print(f"Wrote: {out_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
