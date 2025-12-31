#!/usr/bin/env python3
"""Create a manuscript-ready ablation table from a publication_suite_*.json receipt."""

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List, Tuple
import random


def _bootstrap_ci(successes: List[int], n_boot: int = 2000, seed: int = 42) -> Tuple[float, float]:
    rng = random.Random(seed)
    n = len(successes)
    if n == 0:
        return (0.0, 0.0)
    stats = []
    for _ in range(n_boot):
        s = 0
        for _i in range(n):
            s += successes[rng.randrange(n)]
        stats.append(s / n)
    stats.sort()
    lo = stats[int(0.025 * len(stats))]
    hi = stats[int(0.975 * len(stats))]
    return lo, hi


def _summarize_method(method: Dict[str, Any]) -> Dict[str, Any]:
    rows = method.get("cases") or []

    pos = [r for r in rows if (r.get("eval") or {}).get("is_positive")]
    neg = [r for r in rows if not (r.get("eval") or {}).get("is_positive")]

    pos_drug_success = [1 if (r.get("eval") or {}).get("drug_at1") or (r.get("eval") or {}).get("correct_drug") else 0 for r in pos]
    neg_parp_fp = [1 if (r.get("eval") or {}).get("neg_parp_fp") or (r.get("eval") or {}).get("parp_fp") else 0 for r in neg]

    pos_drug = sum(pos_drug_success) / len(pos_drug_success) if pos_drug_success else 0.0
    neg_fp = sum(neg_parp_fp) / len(neg_parp_fp) if neg_parp_fp else 0.0

    pos_ci = _bootstrap_ci(pos_drug_success)
    neg_ci = _bootstrap_ci(neg_parp_fp)

    return {
        "pos_n": len(pos_drug_success),
        "neg_n": len(neg_parp_fp),
        "pos_drug_at1": pos_drug,
        "pos_drug_at1_ci": pos_ci,
        "neg_parp_fp": neg_fp,
        "neg_parp_fp_ci": neg_ci,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--receipt", required=True)
    ap.add_argument("--out-md", default="docs/ablation_table.md")
    args = ap.parse_args()

    receipt_path = Path(args.receipt)
    report = json.loads(receipt_path.read_text(encoding="utf-8"))

    methods = report.get("methods") or []

    # We report a minimal, reviewer-relevant set.
    want = [
        ("Rule (DDR→PARP)", "baseline"),
        ("Ablation S", "ablation"),
        ("Ablation P", "ablation"),
        ("Model SP", "model"),
    ]

    selected: List[Dict[str, Any]] = []
    for name, _kind in want:
        m = next((x for x in methods if x.get("name") == name), None)
        if m is None:
            continue
        selected.append(m)

    lines: List[str] = []
    lines.append("## Ablation study (S-only vs P-only vs SP)\n")
    lines.append(f"Receipt: `{receipt_path.as_posix()}`\n")
    lines.append("\n")
    lines.append("| Configuration | Pos Drug@1 | Pos Drug@1 (95% CI) | Neg PARP FP | Neg PARP FP (95% CI) | Pos N | Neg N |\n")
    lines.append("|---|---:|---:|---:|---:|---:|---:|\n")

    label_map = {
        "Ablation S": "S-only",
        "Ablation P": "P-only",
        "Model SP": "SP (full)",
        "Rule (DDR→PARP)": "Rule baseline",
    }

    for m in selected:
        s = _summarize_method(m)
        lines.append(
            "| "
            + label_map.get(m.get("name"), m.get("name", ""))
            + f" | {s['pos_drug_at1']:.1%}"
            + f" | ({s['pos_drug_at1_ci'][0]:.1%}, {s['pos_drug_at1_ci'][1]:.1%})"
            + f" | {s['neg_parp_fp']:.1%}"
            + f" | ({s['neg_parp_fp_ci'][0]:.1%}, {s['neg_parp_fp_ci'][1]:.1%})"
            + f" | {s['pos_n']} | {s['neg_n']} |\n"
        )

    out_path = Path(args.out_md)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("".join(lines), encoding="utf-8")
    print(f"✅ wrote {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
