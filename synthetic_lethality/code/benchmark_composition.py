#!/usr/bin/env python3
"""Benchmark transparency: summarize gene/lineage/drug/consequence distributions for test_cases_*.json."""

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List


def _safe_list(x):
    return x if isinstance(x, list) else ([] if x is None else [x])


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--test-file", required=True)
    ap.add_argument("--out-json", default="docs/benchmark_composition.json")
    ap.add_argument("--out-md", default="docs/benchmark_composition.md")
    args = ap.parse_args()

    cases = json.loads(Path(args.test_file).read_text(encoding="utf-8"))

    pos = [c for c in cases if (c.get("ground_truth") or {}).get("synthetic_lethality_detected")]
    neg = [c for c in cases if not (c.get("ground_truth") or {}).get("synthetic_lethality_detected")]

    def summarize(subset: List[Dict[str, Any]]) -> Dict[str, Any]:
        genes = []
        lineages = []
        consequences = []
        gt_drugs = []
        for c in subset:
            disease = (c.get("disease") or "unknown").strip().lower()
            # Use disease as a lineage proxy in this curated dataset.
            lineages.append(disease)

            muts = c.get("mutations") or []
            for m in muts:
                g = (m.get("gene") or "").strip().upper()
                if g:
                    genes.append(g)
                cons = (m.get("consequence") or "").strip().lower()
                if cons:
                    consequences.append(cons)

            gt = c.get("ground_truth") or {}
            for d in _safe_list(gt.get("effective_drugs")):
                if isinstance(d, str) and d.strip():
                    gt_drugs.append(d.strip().lower())

        return {
            "n_cases": len(subset),
            "gene_counts": Counter(genes),
            "lineage_counts": Counter(lineages),
            "consequence_counts": Counter(consequences),
            "gt_drug_counts": Counter(gt_drugs),
        }

    pos_s = summarize(pos)
    neg_s = summarize(neg)

    out = {
        "dataset": str(args.test_file),
        "n_total": len(cases),
        "positive": {
            "n": pos_s["n_cases"],
            "genes": pos_s["gene_counts"].most_common(),
            "lineages": pos_s["lineage_counts"].most_common(),
            "consequences": pos_s["consequence_counts"].most_common(),
            "gt_drugs": pos_s["gt_drug_counts"].most_common(),
        },
        "negative": {
            "n": neg_s["n_cases"],
            "genes": neg_s["gene_counts"].most_common(),
            "lineages": neg_s["lineage_counts"].most_common(),
            "consequences": neg_s["consequence_counts"].most_common(),
            "gt_drugs": neg_s["gt_drug_counts"].most_common(),
        },
    }

    out_json = Path(args.out_json)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(out, indent=2), encoding="utf-8")

    def md_table(title: str, items: List[List[Any]], total: int, header1: str) -> List[str]:
        lines = [f"### {title}\n", "\n", f"| {header1} | Count | % |\n", "|---|---:|---:|\n"]
        for k, c in items[:25]:
            pct = (c / total) if total else 0.0
            lines.append(f"| {k} | {c} | {pct:.1%} |\n")
        lines.append("\n")
        return lines

    md: List[str] = []
    md.append("## Benchmark composition (transparency)\n\n")
    md.append(f"Dataset: `{args.test_file}`\n\n")
    md.append(f"Totals: N={len(cases)} (SL+ N={len(pos)}, SL- N={len(neg)})\n\n")

    md += md_table("SL-positive gene distribution", out["positive"]["genes"], len(pos), "Gene")
    md += md_table("SL-negative gene distribution", out["negative"]["genes"], len(neg), "Gene")
    md += md_table("Lineage proxy (disease field) distribution", Counter([c.get("disease","unknown").strip().lower() for c in cases]).most_common(), len(cases), "Disease")
    md += md_table("Variant consequence distribution", Counter([ (m.get("consequence") or "").strip().lower() for c in cases for m in (c.get("mutations") or []) if (m.get("consequence") or "").strip() ]).most_common(), max(1, sum(len(c.get("mutations") or []) for c in cases)), "Consequence")
    md += md_table("SL-positive ground-truth drug distribution", out["positive"]["gt_drugs"], max(1, sum(c for _, c in out["positive"]["gt_drugs"])), "Drug")

    out_md = Path(args.out_md)
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_md.write_text("".join(md), encoding="utf-8")

    print(f"✅ wrote {out_json}")
    print(f"✅ wrote {out_md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
