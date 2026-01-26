#!/usr/bin/env python3
"""TCGA-OV Real Validation: Survival Analysis for Matchable vs Non-Matchable

Protocol (Alpha):
- Define matchable as best_fit > 0.5
- Compare OS for matchable vs non-matchable via:
  - Kaplan–Meier + logrank test
  - Cox regression (univariate: group only)

Inputs:
- receipts/latest/real_world_tcga_ov_validation.json (contains per-patient best_fit + OS)

Outputs:
- receipts/latest/real_world_tcga_ov_survival_validation.json
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

import numpy as np
import pandas as pd
from lifelines import CoxPHFitter, KaplanMeierFitter
from lifelines.statistics import logrank_test


PUB_DIR = Path(__file__).resolve().parents[1]
RECEIPTS_DIR = PUB_DIR / "receipts" / "latest"


@dataclass
class GroupSummary:
    n: int
    n_events: int
    median_days: Optional[float]


def _median_from_kmf(kmf: KaplanMeierFitter) -> Optional[float]:
    try:
        m = float(kmf.median_survival_time_)
        if np.isfinite(m):
            return m
    except Exception:
        return None
    return None


def main() -> int:
    in_path = RECEIPTS_DIR / "real_world_tcga_ov_validation.json"
    out_path = RECEIPTS_DIR / "real_world_tcga_ov_survival_validation.json"

    if not in_path.exists():
        raise SystemExit(f"Missing input receipt: {in_path}")

    payload = json.loads(in_path.read_text())
    rows = payload.get("raw_results") or []

    if not rows:
        raise SystemExit("Input receipt contains no raw_results")

    df = pd.DataFrame(rows)

    # Hygiene
    df = df.dropna(subset=["os_days", "os_event", "best_fit"]).copy()
    df["os_days"] = pd.to_numeric(df["os_days"], errors="coerce")
    df["os_event"] = df["os_event"].astype(bool)
    df = df.dropna(subset=["os_days"]).copy()

    # Define groups
    df["matchable"] = (df["best_fit"] > 0.5).astype(int)

    match = df[df["matchable"] == 1]
    non = df[df["matchable"] == 0]

    # KM
    km_m = KaplanMeierFitter()
    km_n = KaplanMeierFitter()

    km_m.fit(match["os_days"], event_observed=match["os_event"], label="matchable")
    km_n.fit(non["os_days"], event_observed=non["os_event"], label="non_matchable")

    # Logrank
    lr = logrank_test(
        match["os_days"],
        non["os_days"],
        event_observed_A=match["os_event"],
        event_observed_B=non["os_event"],
    )

    # Cox (univariate)
    cph = CoxPHFitter()
    cox_df = df[["os_days", "os_event", "matchable"]].copy()
    cox_df = cox_df.rename(columns={"os_days": "T", "os_event": "E"})
    cph.fit(cox_df, duration_col="T", event_col="E")

    hr = float(np.exp(cph.params_["matchable"]))
    p_value = float(cph.summary.loc["matchable", "p"])

    out: Dict[str, Any] = {
        "run": {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "input_receipt": str(in_path),
            "n_total_with_os": int(len(df)),
            "threshold": {"best_fit_gt": 0.5},
        },
        "groups": {
            "matchable": asdict(
                GroupSummary(
                    n=int(len(match)),
                    n_events=int(match["os_event"].sum()),
                    median_days=_median_from_kmf(km_m),
                )
            ),
            "non_matchable": asdict(
                GroupSummary(
                    n=int(len(non)),
                    n_events=int(non["os_event"].sum()),
                    median_days=_median_from_kmf(km_n),
                )
            ),
        },
        "km": {
            "logrank": {
                "test_statistic": float(lr.test_statistic),
                "p_value": float(lr.p_value),
            }
        },
        "cox": {
            "model": "univariate_matchable",
            "hazard_ratio": hr,
            "p_value": p_value,
            "interpretation": {
                "hr_lt_1_better_survival_for_matchable": bool(hr < 1.0)
            },
        },
        "notes": [
            "This tests association with OS, not treatment benefit. TCGA-OV is not a trial enrollment dataset.",
            "Group definition is purely best_fit > 0.5 against the 59-trial MoA bank.",
        ],
    }

    out_path.write_text(json.dumps(out, indent=2))

    print("# TCGA-OV Survival Validation")
    print(f"Input:  {in_path}")
    print(f"Output: {out_path}")
    print(f"n_total_with_os: {out['run']['n_total_with_os']}")
    print(f"matchable: {out['groups']['matchable']['n']} | non_matchable: {out['groups']['non_matchable']['n']}")
    print(f"Logrank p={out['km']['logrank']['p_value']:.6g} (stat={out['km']['logrank']['test_statistic']:.3f})")
    print(f"Cox HR={out['cox']['hazard_ratio']:.3f} p={out['cox']['p_value']:.6g}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
