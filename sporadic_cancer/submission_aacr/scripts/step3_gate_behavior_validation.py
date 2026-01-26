#!/usr/bin/env python3
"""
STEP 3 (A→Z): Gate Behavior Validation (Tier 2)

Inputs:
- results/tcga_ov_complete_analysis_table.csv  (built from real local sources)

Outputs:
- results/threshold_sensitivity.csv
- results/subgroup_consistency.csv
- figures/biological_coherence.png
- results/biological_coherence_stats.csv

Scope:
- Threshold sensitivity: sweep TMB and HRD thresholds and report gate trigger rates.
- Subgroup consistency: compare trigger rates across stage and platinum status strata.
- Biological coherence: correlations among biomarkers and between biomarkers and triggers.

No fabricated data; if a field is missing, the script records NA and proceeds.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Any, Tuple, Optional

import numpy as np
import pandas as pd


ROOT = Path("/Users/fahadkiani/Desktop/development/crispr-assistant-main/publications/sporadic_cancer/submission_aacr")
INPUT_TABLE = ROOT / "results" / "tcga_ov_complete_analysis_table.csv"
OUT_RESULTS = ROOT / "results"
OUT_FIGS = ROOT / "figures"
OUT_RESULTS.mkdir(parents=True, exist_ok=True)
OUT_FIGS.mkdir(parents=True, exist_ok=True)


def _is_msi_high(x: Any) -> bool:
    if x is None or (isinstance(x, float) and np.isnan(x)):
        return False
    s = str(x).strip().lower()
    return s in {"msi-h", "msih", "msi_high", "msi-high"}


def _stage_group(stage: Any) -> str:
    if stage is None or (isinstance(stage, float) and np.isnan(stage)):
        return "UNKNOWN"
    s = str(stage).strip().upper()
    # TCGA OV has IIIC/IV etc; group to III vs IV vs other
    if s.startswith("III"):
        return "STAGE_III"
    if s.startswith("IV"):
        return "STAGE_IV"
    return "OTHER"


def _platinum_group(x: Any) -> str:
    if x is None or (isinstance(x, float) and np.isnan(x)):
        return "UNKNOWN"
    s = str(x).strip().lower()
    if s in {"sensitive", "resistant", "tooearly", "missing"}:
        return s.upper()
    return "OTHER"


def compute_gate_triggers(
    df: pd.DataFrame,
    tmb_threshold: float,
    hrd_threshold: float,
    assume_germline_negative: bool,
) -> pd.DataFrame:
    """
    Returns df with boolean trigger columns added:
    - io_boost: TMB >= tmb_threshold OR MSI-H
    - parp_rescue: HRD >= hrd_threshold (only meaningful if germline-negative; for unknown germline, reported separately)
    - parp_penalty: (HRD is known and < hrd_threshold) OR HRD missing
    """
    out = df.copy()
    out["tmb_val"] = pd.to_numeric(out.get("tmb_final"), errors="coerce")
    out["hrd_val"] = pd.to_numeric(out.get("hrd_final"), errors="coerce")
    out["msi_high"] = out.get("msi_status").apply(_is_msi_high) if "msi_status" in out.columns else False

    out["io_boost"] = (out["tmb_val"] >= float(tmb_threshold)) | out["msi_high"]

    # Germline status is not available (it is 'unknown' for nearly all); we explicitly choose a mode
    # for reporting expected behavior under the paper's gate definition.
    out["germline_mode"] = "ASSUME_NEGATIVE" if assume_germline_negative else "UNKNOWN"

    # PARP rescue/penalty are defined relative to HRD threshold; germline modifies multiplier in code,
    # but in this paper's Tier-2 behavior validation we focus on trigger behavior.
    out["parp_rescue"] = out["hrd_val"] >= float(hrd_threshold)
    out["parp_penalty"] = out["hrd_val"].isna() | (out["hrd_val"] < float(hrd_threshold))

    return out


def rate(x: pd.Series) -> float:
    denom = float(x.notna().sum())
    if denom == 0:
        return float("nan")
    return float((x == True).sum()) / denom  # noqa: E712


def run_threshold_sensitivity(df: pd.DataFrame) -> pd.DataFrame:
    rows = []

    # TMB sweep (IO)
    for thr in [10, 15, 20, 25]:
        d = compute_gate_triggers(df, tmb_threshold=thr, hrd_threshold=42, assume_germline_negative=True)
        rows.append(
            {
                "sweep": "TMB",
                "threshold": thr,
                "io_boost_rate": rate(d["io_boost"]),
                "parp_rescue_rate": np.nan,
                "parp_penalty_rate": np.nan,
                "n": len(d),
                "notes": "IO boost = (TMB >= threshold) OR MSI-H; HRD fixed at 42",
                "literature_range": "FDA pan-cancer: 10; KEYNOTE-158: 10; Samstein 2019 often uses 20",
                "our_choice_flag": "YES" if thr == 20 else "NO",
            }
        )

    # HRD sweep (PARP)
    for thr in [30, 35, 40, 42, 45, 50]:
        d = compute_gate_triggers(df, tmb_threshold=20, hrd_threshold=thr, assume_germline_negative=True)
        rows.append(
            {
                "sweep": "HRD",
                "threshold": thr,
                "io_boost_rate": np.nan,
                "parp_rescue_rate": rate(d["parp_rescue"]),
                "parp_penalty_rate": rate(d["parp_penalty"]),
                "n": len(d),
                "notes": "PARP rescue/penalty defined relative to HRD threshold; TMB fixed at 20",
                "literature_range": "Myriad: 42; other assays vary (30–50)",
                "our_choice_flag": "YES" if thr == 42 else "NO",
            }
        )

    out = pd.DataFrame(rows)
    out.to_csv(OUT_RESULTS / "threshold_sensitivity.csv", index=False)
    return out


def run_subgroup_consistency(df: pd.DataFrame) -> pd.DataFrame:
    base = compute_gate_triggers(df, tmb_threshold=20, hrd_threshold=42, assume_germline_negative=True)
    base["stage_group"] = base.get("tumor_stage_2009").apply(_stage_group) if "tumor_stage_2009" in base.columns else "UNKNOWN"
    base["platinum_group"] = base.get("platinum_status").apply(_platinum_group) if "platinum_status" in base.columns else "UNKNOWN"

    rows = []
    for (group_name, group_col) in [("STAGE_GROUP", "stage_group"), ("PLATINUM_GROUP", "platinum_group")]:
        for g, sub in base.groupby(group_col):
            rows.append(
                {
                    "grouping": group_name,
                    "subgroup": g,
                    "n": len(sub),
                    "io_boost_rate": rate(sub["io_boost"]),
                    "parp_rescue_rate": rate(sub["parp_rescue"]),
                    "parp_penalty_rate": rate(sub["parp_penalty"]),
                }
            )

    out = pd.DataFrame(rows).sort_values(["grouping", "subgroup"])
    out.to_csv(OUT_RESULTS / "subgroup_consistency.csv", index=False)
    return out


def spearman(a: pd.Series, b: pd.Series) -> float:
    x = pd.to_numeric(a, errors="coerce")
    y = pd.to_numeric(b, errors="coerce")
    m = x.notna() & y.notna()
    if m.sum() < 3:
        return float("nan")
    return float(pd.Series(x[m]).corr(pd.Series(y[m]), method="spearman"))


def run_biological_coherence(df: pd.DataFrame) -> Tuple[pd.DataFrame, Path]:
    base = compute_gate_triggers(df, tmb_threshold=20, hrd_threshold=42, assume_germline_negative=True)

    # Biomarkers
    base["tmb_val"] = pd.to_numeric(base.get("tmb_final"), errors="coerce")
    base["hrd_val"] = pd.to_numeric(base.get("hrd_final"), errors="coerce")
    base["msi_high"] = base.get("msi_status").apply(_is_msi_high) if "msi_status" in base.columns else False
    base["brca_somatic_flag"] = base.get("brca_somatic").notna() & (base.get("brca_somatic").astype(str).str.strip() != "") if "brca_somatic" in base.columns else False
    base["brca_any_flag"] = base.get("has_brca_mutation").fillna(False) | base["brca_somatic_flag"]

    # Correlation matrix across numeric/boolean (booleans cast to 0/1)
    mat = pd.DataFrame(
        {
            "tmb": base["tmb_val"],
            "hrd": base["hrd_val"],
            "msi_high": base["msi_high"].astype(int),
            "brca_any": base["brca_any_flag"].astype(int),
            "io_boost": base["io_boost"].astype(int),
            "parp_rescue": base["parp_rescue"].astype(int),
            "parp_penalty": base["parp_penalty"].astype(int),
        }
    )

    corr = mat.corr(method="spearman")
    stats = []
    for i in corr.columns:
        for j in corr.columns:
            if i == j:
                continue
            stats.append({"var1": i, "var2": j, "spearman_rho": float(corr.loc[i, j])})
    stats_df = pd.DataFrame(stats)
    stats_df.to_csv(OUT_RESULTS / "biological_coherence_stats.csv", index=False)

    # Plot heatmap
    fig_path = OUT_FIGS / "biological_coherence.png"
    try:
        import matplotlib.pyplot as plt
        import seaborn as sns

        plt.figure(figsize=(10, 8))
        sns.heatmap(corr, annot=True, fmt=".2f", cmap="vlag", vmin=-1, vmax=1)
        plt.title("Biological Coherence: Spearman correlations (TCGA-OV)")
        plt.tight_layout()
        plt.savefig(fig_path, dpi=200)
        plt.close()
    except Exception as e:
        # Don't fail the pipeline if plotting stack isn't available
        print(f"WARN: failed to render heatmap: {e}")

    return corr, fig_path


def main() -> None:
    if not INPUT_TABLE.exists():
        raise FileNotFoundError(f"Missing input table: {INPUT_TABLE}")
    df = pd.read_csv(INPUT_TABLE)

    print("=" * 80)
    print("STEP 3: GATE BEHAVIOR VALIDATION (TIER 2)")
    print("=" * 80)
    print(f"Loaded cohort rows: {len(df)} from {INPUT_TABLE}")

    ts = run_threshold_sensitivity(df)
    print(f"Wrote threshold sensitivity: {OUT_RESULTS / 'threshold_sensitivity.csv'} ({len(ts)} rows)")

    sg = run_subgroup_consistency(df)
    print(f"Wrote subgroup consistency: {OUT_RESULTS / 'subgroup_consistency.csv'} ({len(sg)} rows)")

    corr, fig_path = run_biological_coherence(df)
    print(f"Wrote biological coherence stats: {OUT_RESULTS / 'biological_coherence_stats.csv'}")
    if fig_path.exists():
        print(f"Wrote biological coherence figure: {fig_path}")
    else:
        print(f"Biological coherence figure not generated (plotting unavailable). Expected path: {fig_path}")

    print("DONE")


if __name__ == "__main__":
    main()
