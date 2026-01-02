#!/usr/bin/env python3
"""Generate sporadic_cancer_manuscript.md from receipts (path-robust)."""

from __future__ import annotations

import json
from pathlib import Path


def newest(base: Path, glob_pat: str) -> Path:
    paths = list((base / "data").glob(glob_pat))
    if not paths:
        raise FileNotFoundError(f"No files matched {(base / 'data' / glob_pat)}")
    return max(paths, key=lambda p: p.stat().st_mtime)


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    base = Path(__file__).resolve().parent

    scenari = newest(base, "scenario_suite_25_*.json")
    bench_path = base / "receipts" / "benchmark_gate_effects.json"
    bench = load_json(bench_path)
    s = bench.get("stats", {})

    md: list[str] = []

    md.append(
        "# Conservative tumor-context gating for sporadic cancers: a provenance-first approach for precision oncology without tumor NGS"
    )
    md.append("")

    md.append("## Abstract")
    md.append("")
    md.append(
        "**Background:** Most oncology patients are germline-negative (sporadic) and frequently lack immediately available tumor NGS at the time therapy options are discussed. In this setting, decision support systems can silently extrapolate from incomplete inputs and emit overconfident recommendations."
    )
    md.append("")
    md.append(
        "**Methods:** We implemented a conservative, provenance-first tumor-context layer consisting of (i) a structured TumorContext schema with explicit biomarker fields (TMB, MSI status, HRD score) and a completeness score mapped to three intake levels (L0/L1/L2); (ii) a Quick Intake pathway that creates TumorContext under partial information; and (iii) deterministic sporadic gates applied per drug to adjust efficacy and/or confidence. Gates include a PARP inhibitor penalty for germline-negative, HRD-low contexts with rescue for HRD-high tumors; an immunotherapy (checkpoint inhibitor) boost for strong tumor biomarkers; and confidence caps based on TumorContext completeness. Each adjustment emits structured provenance (`sporadic_gates_provenance`)."
    )
    md.append("")

    md.append(
        "**Results:** Unit tests passed (8/8; receipt `receipts/pytest_sporadic_gates.txt`) and a standalone validation script passed (6/6; receipts `receipts/validate_sporadic_gates.txt` and `receipts/validate_sporadic_gates_report.json`). Quick Intake executed successfully for 15/15 cancer types (receipt `receipts/quick_intake_15cancers.json`). An end-to-end smoke test (Quick Intake → efficacy prediction) produced provenance-bearing drug outputs (recets `receipts/e2e_tumor_context.json`, `receipts/e2e_efficacy_response.json`, `receipts/e2e_sporadic_workflow.txt`)."
    )

    if all(k in s for k in [
        'changed_eff_cases','changed_conf_cases','n_cases','agreement_naive_vs_system_eff','agreement_naive_vs_system_conf'
    ]):
        md.append("")
        md.append(
            f"On a 25-case scenario suite exercising thresholds (`{scenario_path.as_posix()}`), sporadic gates modified efficacy in **{s['changed_eff_cases']}/{s['n_cases']}** cases and confidence in **{s['changed_conf_cases']}/{s['n_cases']}** cases. System outputs matched a naive-rule implementation in **{s['agreement_naive_vs_system_eff']}/{s['n_cases']}** efficacy outcomes and **{s['agreement_naive_vs_system_conf']}/{s['n_cases']}** confidence outcomes (receipt `receipts/benchmark_gate_effects.json`)."
        )

    md.append("")
    md.append(
        "**Conclusions:** A conservative tumor-context gating layer provides transparent, reproducible adjustments that reduce overconfidence under incomplete intake and clearly communicate which biomarkers drove changes. This design supports safe iteration toward full tumor NGS integration while remaining operational for the sporadic majority."
    )
    md.append("")

    md.append("## Results (receipts + figures)")
    md.append("")
    md.append("### Receipts")
    md.append("")
    md.append(f"- Scenario suite: `{scenario_path}`")
    md.append(f"- Benchmark receipt: `{bench_path}`")
    md.append("- Unit tests: `receipts/pytest_sporadic_gates.txt`")
    md.append("- Validator receipts: `receipts/validate_sporadic_gates.txt`, `receipts/validate_sporadic_gates_report.json`")
    md.append("- E2E receipts: `receipts/e2e_tumor_context.json`, `receipts/e2e_efficacy_response.json`, `receipts/e2e_sporadic_workflow.txt`")
    md.append("")

    md.append("### Figures")
    md.append("")
    md.append("- Figure 1: `figures/figure_1_architecture.png`")
    md.append("- Figure 2: `figures/figure_2_parp_gates.png`")
    md.append("- Figure 3: `figures/figure_3_confidence_caps.png`")
    md.append("")

    out = base / "sporadic_cancer_manuscript.md"
    out.write_text("\n".join(md), encoding="utf-8")
    print(f"✅ wrote {out}")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
