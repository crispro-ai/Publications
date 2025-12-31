#!/usr/bin/env python3
"""Tier 3 baseline: curated DDR gene list -> predict PARP class.

Rule:
- If any mutation gene in curated DDR list -> predict PARP (representative drug: 'olaparib')
- Else -> no prediction

Metrics reported (bootstrap 95% CI; Bernoulli bootstrap, B=2000, seed=42):
- Coverage (SL+): % of SL-positive cases where rule fires
- Drug@1 (Covered, SL+): accuracy among covered SL-positive cases
- Drug@1 (All, SL+): accuracy among all SL-positive cases (uncovered counts incorrect)
- PARP FP (SL-): false-positive rate among SL-negative cases (rule fires)

Outputs:
- publications/synthetic_lethality/docs/baseline_comparison.json
- publications/synthetic_lethality/docs/baseline_comparison.md
"""

from __future__ import annotations

import json
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Tuple

DATASET = Path(__file__).resolve().parents[1] / "data" / "data/test_cases_100.json"
OUT_JSON = Path(__file__).resolve().parents[1] / "docs" / "baseline_comparison.json"
OUT_MD = Path(__file__).resolve().parents[1] / "docs" / "baseline_comparison.md"

CURATED_DDR = {
    "BRCA1",
    "BRCA2",
    "ATM",
    "PALB2",
    "CHEK2",
    "RAD51C",
    "RAD51D",
    "BARD1",
    "BRIP1",
}

PARP_DRUGS = {"olaparib", "niraparib", "rucaparib", "talazoparib"}


def _lower_list(xs: List[str]) -> List[str]:
    return [str(x).lower().strip() for x in (xs or []) if str(x).strip()]


def _case_genes(case: Dict[str, Any]) -> List[str]:
    muts = case.get("mutations") or []
    genes: List[str] = []
    for m in muts:
        g = (m.get("gene") or "").upper().strip()
        if g:
            genes.append(g)
    return genes


def _gt_drug_set(case: Dict[str, Any]) -> set:
    gt = (case.get("ground_truth") or {})
    eff = _lower_list(gt.get("effective_drugs") or [])
    return set(eff)


def _is_sl_positive(case: Dict[str, Any]) -> bool:
    return bool(((case.get("ground_truth") or {}).get("synthetic_lethality_detected")))


def _rule_fires(case: Dict[str, Any]) -> bool:
    genes = set(_case_genes(case))
    return bool(genes.intersection(CURATED_DDR))


def _bootstrap_ci(values: List[int], B: int = 2000, seed: int = 42) -> Tuple[float, float]:
    """Bootstrap CI for Bernoulli list of 0/1 values."""
    if not values:
        return (0.0, 0.0)
    rng = random.Random(seed)
    n = len(values)
    stats: List[float] = []
    for _ in range(B):
        s = 0
        for _i in range(n):
            s += values[rng.randrange(0, n)]
        stats.append(s / n)
    stats.sort()
    lo = stats[int(0.025 * B)]
    hi = stats[int(0.975 * B)]
    return (lo, hi)


@dataclass
class Metrics:
    coverage: float
    coverage_ci: Tuple[float, float]

    drug_at1_all: float
    drug_at1_all_ci: Tuple[float, float]

    drug_at1_covered: float
    drug_at1_covered_ci: Tuple[float, float]

    neg_parp_fp: float
    neg_parp_fp_ci: Tuple[float, float]

    n_pos: int
    n_neg: int
    n_covered: int


def compute(cases: List[Dict[str, Any]]) -> Tuple[Metrics, List[Dict[str, Any]]]:
    pos = [c for c in cases if _is_sl_positive(c)]
    neg = [c for c in cases if not _is_sl_positive(c)]

    rows: List[Dict[str, Any]] = []

    fires_pos: List[int] = []
    correct_all: List[int] = []
    correct_covered: List[int] = []

    for c in pos:
        fires = _rule_fires(c)
        fires_pos.append(1 if fires else 0)

        gt = _gt_drug_set(c)
        pred = "olaparib" if fires else None
        is_correct = (pred in gt) if pred else False

        correct_all.append(1 if is_correct else 0)
        if fires:
            correct_covered.append(1 if is_correct else 0)

        rows.append(
            {
                "case_id": c.get("case_id"),
                "is_positive": True,
                "genes": sorted(set(_case_genes(c))),
                "gt_drugs": sorted(gt),
                "rule_fires": fires,
                "prediction": pred,
                "correct": is_correct,
            }
        )

    fires_neg: List[int] = []
    for c in neg:
        fires = _rule_fires(c)
        fires_neg.append(1 if fires else 0)
        rows.append(
            {
                "case_id": c.get("case_id"),
                "is_positive": False,
                "genes": sorted(set(_case_genes(c))),
                "gt_drugs": sorted(_gt_drug_set(c)),
                "rule_fires": fires,
                "prediction": "olaparib" if fires else None,
                "correct": (not fires),
            }
        )

    n_pos = len(pos)
    n_neg = len(neg)
    n_covered = sum(fires_pos)

    coverage = n_covered / n_pos if n_pos else 0.0
    drug_at1_all = sum(correct_all) / n_pos if n_pos else 0.0
    drug_at1_covered = (sum(correct_covered) / len(correct_covered)) if correct_covered else 0.0
    neg_parp_fp = sum(fires_neg) / n_neg if n_neg else 0.0

    metrics = Metrics(
        coverage=coverage,
        coverage_ci=_bootstrap_ci(fires_pos),
        drug_at1_all=drug_at1_all,
        drug_at1_all_ci=_bootstrap_ci(correct_all),
        drug_at1_covered=drug_at1_covered,
        drug_at1_covered_ci=_bootstrap_ci(correct_covered) if correct_covered else (0.0, 0.0),
        neg_parp_fp=neg_parp_fp,
        neg_parp_fp_ci=_bootstrap_ci(fires_neg),
        n_pos=n_pos,
        n_neg=n_neg,
        n_covered=n_covered,
    )

    return metrics, rows


def main() -> int:
    cases = json.loads(DATASET.read_text(encoding="utf-8"))
    metrics, rows = compute(cases)

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)

    out = {
        "method": "rule_curated_ddr_9",
        "curated_ddr_genes": sorted(CURATED_DDR),
        "parp_drugs": sorted(PARP_DRUGS),
        "metrics": {
            "coverage": metrics.coverage,
            "coverage_ci": metrics.coverage_ci,
            "drug_at1_all": metrics.drug_at1_all,
            "drug_at1_all_ci": metrics.drug_at1_all_ci,
            "drug_at1_covered": metrics.drug_at1_covered,
            "drug_at1_covered_ci": metrics.drug_at1_covered_ci,
            "neg_parp_fp": metrics.neg_parp_fp,
            "neg_parp_fp_ci": metrics.neg_parp_fp_ci,
            "n_pos": metrics.n_pos,
            "n_neg": metrics.n_neg,
            "n_covered": metrics.n_covered,
        },
        "cases": rows,
    }

    OUT_JSON.write_text(json.dumps(out, indent=2, sort_keys=True), encoding="utf-8")

    def pct(x: float) -> str:
        return f"{x*100:.1f}%"

    def ci_str(ci: Tuple[float, float]) -> str:
        return f"({ci[0]*100:.1f}–{ci[1]*100:.1f}%)"

    md: List[str] = []
    md.append(
        """## Baseline comparison (Tier 3: curated DDR gene list)

"""
    )
    md.append(f"Dataset: `{DATASET}`\n\n")
    md.append("Curated DDR gene list (9): " + ", ".join(sorted(CURATED_DDR)) + "\n\n")
    md.append(
        "Rule: if any mutated gene is in curated DDR list → predict PARP (represented as `olaparib`); otherwise no prediction.\n\n"
    )

    md.append("""### Metrics (bootstrap 95% CI)

""")
    md.append(f"- SL-positive cases (n={metrics.n_pos})\n")
    md.append(
        f"  - Coverage: {pct(metrics.coverage)} {ci_str(metrics.coverage_ci)} ({metrics.n_covered}/{metrics.n_pos})\n"
    )
    md.append(
        f"  - Drug@1 (All SL+; uncovered counted incorrect): {pct(metrics.drug_at1_all)} {ci_str(metrics.drug_at1_all_ci)}\n"
    )
    md.append(
        f"  - Drug@1 (Covered SL+ only): {pct(metrics.drug_at1_covered)} {ci_str(metrics.drug_at1_covered_ci)}\n"
    )
    md.append(f"- SL-negative cases (n={metrics.n_neg})\n")
    md.append(
        f"  - PARP FP rate (rule fires on SL−): {pct(metrics.neg_parp_fp)} {ci_str(metrics.neg_parp_fp_ci)}\n\n"
    )

    md.append("""### Notes

""")
    md.append(
        "- This is a deterministic, knowledge-lite baseline intended to approximate expert curation without sequence/pathway scoring.\n"
    )
    md.append(
        "- The rule is intentionally conservative: it only fires on a fixed DDR gene list, which limits coverage by design.\n"
    )
    md.append(f"- Raw per-case outputs: `{OUT_JSON}`\n")

    OUT_MD.write_text("".join(md), encoding="utf-8")

    print(f"✅ wrote {OUT_MD}")
    print(f"✅ wrote {OUT_JSON}")
    print(json.dumps(out["metrics"], indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
