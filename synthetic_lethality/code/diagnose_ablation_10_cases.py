#!/usr/bin/env python3
"""30-minute diagnostic: verify S-only/P-only failure mode on 10 PARP-ground-truth SL-positive cases.

Select:
- 5 BRCA1 cases
- 3 BRCA2 cases
- 2 other DDR cases (ATM, PALB2 preferred)

For each case: report GT drug + predictions under ablation_mode S / P / SP.

Outputs:
- docs/ablation_diagnostic_10_cases.md
"""

import json
import os
import urllib.request
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

API_ROOT = os.getenv("API_ROOT", "http://127.0.0.1:8000")
TEST_FILE = Path(__file__).resolve().parents[1] / "data" / "data/test_cases_100.json"  # publications/synthetic_lethality/data
OUT_MD = Path(__file__).resolve().parents[1] / "docs" / "ablation_diagnostic_10_cases.md"


def _lower_list(xs: List[str]) -> List[str]:
    return [str(x).lower().strip() for x in (xs or []) if str(x).strip()]


def _post_json(url: str, payload: Dict[str, Any], timeout_s: float = 60.0) -> Dict[str, Any]:
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout_s) as r:
        return json.loads(r.read().decode("utf-8"))


def _predict_top_drug(case: Dict[str, Any], ablation_mode: str) -> Optional[str]:
    payload = {
        "model_id": "evo2_1b",
        "mutations": case.get("mutations") or [],
        "disease": case.get("disease", "ovarian_cancer"),
        "options": {
            "adaptive": True,
            "ensemble": False,
            "fast": True,
            "panel_id": "sl_publication",
            "ablation_mode": ablation_mode,
        },
    }
    resp = _post_json(f"{API_ROOT}/api/efficacy/predict", payload)
    drugs = resp.get("drugs") or []
    if not drugs:
        return None

    # Use the same deterministic tie-break as the benchmark suite:
    # sort by (confidence desc, name asc)
    def key(d: Dict[str, Any]) -> Tuple[float, str]:
        return (-float(d.get("confidence", 0.0) or 0.0), str(d.get("name", "")).lower())

    top = sorted(drugs, key=key)[0]
    return (top.get("name") or None)


def _primary_gene(case: Dict[str, Any], preferred: List[str]) -> str:
    muts = case.get("mutations") or []
    genes = [(m.get("gene") or "").upper().strip() for m in muts if (m.get("gene") or "").strip()]
    for p in preferred:
        if p in genes:
            return p
    return genes[0] if genes else ""


def main() -> int:
    cases = json.loads(TEST_FILE.read_text(encoding="utf-8"))

    # Filter to SL-positive where GT includes PARP drugs (olaparib or niraparib).
    pos_parp = []
    for c in cases:
        gt = c.get("ground_truth") or {}
        if not gt.get("synthetic_lethality_detected"):
            continue
        gt_drugs_l = _lower_list(gt.get("effective_drugs") or [])
        if not ("olaparib" in gt_drugs_l or "niraparib" in gt_drugs_l):
            continue
        pos_parp.append(c)

    def pick_by_gene(gene: str, n: int) -> List[Dict[str, Any]]:
        out = []
        for c in pos_parp:
            genes = {(m.get("gene") or "").upper().strip() for m in (c.get("mutations") or [])}
            if gene in genes:
                out.append(c)
            if len(out) >= n:
                break
        return out

    sel: List[Dict[str, Any]] = []
    sel += pick_by_gene("BRCA1", 5)
    sel += [c for c in pick_by_gene("BRCA2", 50) if c not in sel][:3]

    # Prefer 2 other DDR genes (ATM, PALB2), else fall back to next DDR genes.
    other_pref = ["ATM", "PALB2", "RAD51C", "RAD51D", "CDK12", "ARID1A", "MBD4"]
    for g in other_pref:
        if len(sel) >= 10:
            break
        picks = [c for c in pick_by_gene(g, 50) if c not in sel]
        if picks:
            sel.append(picks[0])

    if len(sel) < 10:
        # fallback: fill from remaining pos_parp
        for c in pos_parp:
            if c not in sel:
                sel.append(c)
            if len(sel) >= 10:
                break

    sel = sel[:10]

    rows = []
    s_preds = []
    p_preds = []
    sp_preds = []

    for idx, c in enumerate(sel, 1):
        gt_drugs_l = _lower_list((c.get("ground_truth") or {}).get("effective_drugs") or [])
        # Display all ground-truth drugs (often multiple acceptable PARP inhibitors)
        gt = "/".join(sorted(dict.fromkeys(gt_drugs_l)))

        gene = _primary_gene(c, ["BRCA1", "BRCA2", "ATM", "PALB2", "RAD51C", "RAD51D", "CDK12", "ARID1A", "MBD4"])

        s_top = _predict_top_drug(c, "S")
        p_top = _predict_top_drug(c, "P")
        sp_top = _predict_top_drug(c, "SP")

        s_preds.append((s_top or ""))
        p_preds.append((p_top or ""))
        sp_preds.append((sp_top or ""))

        rows.append({
            "i": idx,
            "case_id": c.get("case_id"),
            "gene": gene,
            "gt": gt,
            "s": (s_top or "(none)"),
            "p": (p_top or "(none)"),
            "sp": (sp_top or "(none)"),
        })

    # Pattern analysis
    def summarize(preds: List[str]) -> Dict[str, Any]:
        c = Counter([p.lower().strip() for p in preds if p and p.strip()])
        if not c:
            return {"kind": "EMPTY", "top": None, "top_frac": 0.0}
        top, n = c.most_common(1)[0]
        kind = "SYSTEMATIC" if (n >= 7) else "MIXED"
        return {"kind": kind, "top": top, "top_frac": n / 10.0, "counts": c}

    s_sum = summarize(s_preds)
    p_sum = summarize(p_preds)
    overlap = sum(1 for i in range(10) if (s_preds[i] or "").lower().strip() == (p_preds[i] or "").lower().strip())

    # Correctness against GT list (not a single selected drug string)
    sp_correct = 0
    for r in rows:
        gt_set = {x.strip() for x in r["gt"].lower().split('/') if x.strip()}
        if r["sp"].lower().strip() in gt_set:
            sp_correct += 1

    md = []
    md.append("## 10-case ablation diagnostic (SL-positive, PARP ground truth)\n\n")
    md.append(f"API: `{API_ROOT}`\n\n")
    md.append(f"Dataset: `{TEST_FILE.as_posix()}`\n\n")

    md.append("| # | Case | Gene | GT Drug | S-only Pred | P-only Pred | SP Pred |\n")
    md.append("|---:|---|---|---|---|---|---|\n")
    for r in rows:
        md.append(f"| {r['i']} | {r['case_id']} | {r['gene']} | {r['gt']} | {r['s']} | {r['p']} | {r['sp']} |\n")

    md.append("\n### Pattern analysis\n\n")
    md.append(f"- **S-only pattern**: {s_sum['kind']} (most common: `{s_sum['top']}`, {s_sum['top_frac']:.0%} of cases)\n")
    md.append(f"- **P-only pattern**: {p_sum['kind']} (most common: `{p_sum['top']}`, {p_sum['top_frac']:.0%} of cases)\n")
    md.append(f"- **S-only vs P-only overlap**: same prediction in **{overlap}/10** cases\n")
    md.append(f"- **SP accuracy vs GT**: correct in **{sp_correct}/10** cases\n")

    md.append("\n### Conclusion\n\n")
    if s_sum["kind"] == "SYSTEMATIC" or p_sum["kind"] == "SYSTEMATIC":
        md.append("Failure mode is **SYSTEMATIC** (consistent wrong top-choice dominates), consistent with a coherent but mis-calibrated ranking under ablation.\n")
    else:
        md.append("Failure mode appears **MIXED/RANDOM** (no single dominant wrong top-choice), suggesting additional debugging is required.\n")

    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUT_MD.write_text("".join(md), encoding="utf-8")
    print(f"✅ wrote {OUT_MD}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
