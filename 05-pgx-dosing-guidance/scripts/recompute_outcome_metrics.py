#!/usr/bin/env python3
"""
Recompute outcome-linked metrics from receipt raw tables (publication reproducibility)

This script does NOT fetch new data. It recomputes the key clinical effect sizes
directly from the `raw_table_data` embedded in the receipts:
- PREPARE: RRR (actionable), negative control RRR (nonactionable)
- CYP2C19: Risk Ratio (PM/IM vs EM)

It produces a machine-readable verification receipt that can be cited as
computational reproducibility for publication.

Research Use Only - Not for Clinical Decision Making
"""

import json
import math
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Tuple


ROOT = Path(__file__).resolve().parents[1]  # publications/05-pgx-dosing-guidance
REPORTS = ROOT / "reports"


def _load(path: Path) -> Dict[str, Any]:
    with open(path) as f:
        return json.load(f)


def _rrr(control_rate: float, intervention_rate: float) -> float:
    if control_rate <= 0:
        return float("nan")
    return (control_rate - intervention_rate) / control_rate


def _risk_ratio(a_rate: float, b_rate: float) -> float:
    if b_rate <= 0:
        return float("inf")
    return a_rate / b_rate


def recompute_prepare(prepare: Dict[str, Any]) -> Dict[str, Any]:
    t2 = prepare["raw_table_data"]["Table_2_clinically_relevant_toxic_effects"]

    ca = t2["control_arm"]["actionable_carriers"]
    ia = t2["intervention_arm"]["actionable_carriers"]
    cn = t2["control_arm"]["nonactionable"]
    inn = t2["intervention_arm"]["nonactionable"]

    # Compute rates from counts to avoid rounding artifacts in receipt-provided `rate` fields
    ca_rate = ca["toxic_events"] / ca["total"]
    ia_rate = ia["toxic_events"] / ia["total"]
    cn_rate = cn["toxic_events"] / cn["total"]
    inn_rate = inn["toxic_events"] / inn["total"]

    actionable_rrr = _rrr(ca_rate, ia_rate)
    nonactionable_rrr = _rrr(cn_rate, inn_rate)

    return {
        "actionable": {
            "control_rate": ca_rate,
            "intervention_rate": ia_rate,
            "rrr": actionable_rrr,
            "counts": {
                "control": {"toxic_events": ca["toxic_events"], "total": ca["total"]},
                "intervention": {"toxic_events": ia["toxic_events"], "total": ia["total"]},
            },
        },
        "nonactionable_negative_controls": {
            "control_rate": cn_rate,
            "intervention_rate": inn_rate,
            "rrr": nonactionable_rrr,
            "counts": {
                "control": {"toxic_events": cn["toxic_events"], "total": cn["total"]},
                "intervention": {"toxic_events": inn["toxic_events"], "total": inn["total"]},
            },
        },
    }


def recompute_cyp2c19(cyp: Dict[str, Any]) -> Dict[str, Any]:
    t4 = cyp["raw_table_data"]["Table_4_clopidogrel_subset_by_phenotype"]
    em = t4["extensive_metabolizer"]
    pm_im = t4["poor_intermediate_metabolizer"]

    # Compute rates from counts to avoid rounding artifacts in receipt-provided `rate` fields
    em_rate = em["events"] / em["total"]
    pm_im_rate = pm_im["events"] / pm_im["total"]
    rr = _risk_ratio(pm_im_rate, em_rate)

    return {
        "pm_im_vs_em": rr,
        "rates": {"pm_im": pm_im_rate, "em": em_rate},
        "counts": {
            "pm_im": {"events": pm_im["events"], "total": pm_im["total"]},
            "em": {"events": em["events"], "total": em["total"]},
        },
    }


def within_tol(a: float, b: float, tol: float = 1e-3) -> bool:
    try:
        return abs(a - b) <= tol
    except Exception:
        return False


def main() -> int:
    prepare_path = REPORTS / "prepare_outcome_validation.json"
    cyp_path = REPORTS / "cyp2c19_clopidogrel_efficacy_validation.json"

    prepare = _load(prepare_path)
    cyp = _load(cyp_path)

    recomputed_prepare = recompute_prepare(prepare)
    recomputed_cyp = recompute_cyp2c19(cyp)

    # Compare to stored metrics (receipt-backed)
    stored_prepare = prepare["calculated_metrics"]
    stored_cyp = cyp["calculated_metrics"]

    comparisons = {
        "prepare_actionable_rrr_match": within_tol(
            recomputed_prepare["actionable"]["rrr"],
            float(stored_prepare["actionable_carriers"]["relative_risk_reduction"]),
        ),
        "prepare_nonactionable_rrr_match": within_tol(
            recomputed_prepare["nonactionable_negative_controls"]["rrr"],
            float(stored_prepare["nonactionable_negative_controls"]["relative_risk_reduction"]),
        ),
        "cyp2c19_rr_match": within_tol(
            recomputed_cyp["pm_im_vs_em"],
            float(stored_cyp["risk_ratio"]["pm_im_vs_em"]),
            tol=1e-2,
        ),
    }

    out = {
        "receipt_type": "recompute_outcome_metrics_verification",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "inputs": {
            "prepare_receipt": str(prepare_path),
            "cyp2c19_receipt": str(cyp_path),
        },
        "recomputed": {
            "prepare": recomputed_prepare,
            "cyp2c19": recomputed_cyp,
        },
        "stored_receipt_metrics": {
            "prepare": {
                "actionable_rrr": stored_prepare["actionable_carriers"]["relative_risk_reduction"],
                "nonactionable_rrr": stored_prepare["nonactionable_negative_controls"]["relative_risk_reduction"],
            },
            "cyp2c19": {
                "pm_im_vs_em_risk_ratio": stored_cyp["risk_ratio"]["pm_im_vs_em"],
            },
        },
        "comparisons": comparisons,
        "overall_verified": all(comparisons.values()),
        "notes": {
            "scope": "Recomputes only effect sizes from receipt raw tables; does not fetch PMC XML.",
            "interpretation": "If all comparisons match, manuscript effect sizes are computationally reproducible from embedded tables.",
        },
    }

    out_path = REPORTS / f"recompute_outcome_metrics_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
    with open(out_path, "w") as f:
        json.dump(out, f, indent=2)

    print(f"Wrote verification receipt: {out_path}")
    print(f"overall_verified={out['overall_verified']}")
    return 0 if out["overall_verified"] else 2


if __name__ == "__main__":
    raise SystemExit(main())


