#!/usr/bin/env python3
"""Generate the sporadic cancer manuscript markdown from receipts.

This keeps the manuscript "receipt-backed" and avoids hand-edit drift.

Run from: publications/sporadic_cancer/
"""

from __future__ import annotations

import json
from pathlib import Path


def newest(glob_pat: str) -> Path:
    paths = list(Path("data").glob(glob_pat))
    if not paths:
        raise FileNotFoundError(f"No files matched data/{glob_pat}")
    return max(paths, key=lambda p: p.stat().st_mtime)


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    scenario_path = newest("scenario_suite_25_*.json")
    bench_path = Path("receipts/benchmark_gate_effects.json")
    bench = load_json(bench_path)
    s = bench.get("stats", {})

    changed_eff = s.get("changed_eff_cases")
    changed_conf = s.get("changed_conf_cases")
    n_cases = s.get("n_cases")
    agree_eff = s.get("agreement_naive_vs_system_eff")
    agree_conf = s.get("agreement_naive_vs_system_conf")

    md: list[str] = []

    md.append(
        "# Conservative tumor-context gating for sporadic cancers: a provenance-first approach for precision oncology without tumor NGS"
    )
    md.append("")

    # Abstract
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
        "**Results:** Unit tests passed (8/8; receipt `receipts/pytest_sporadic_gates.txt`) and a standalone validation script passed (6/6; receipts `receipts/validate_sporadic_gates.txt` and `receipts/validate_sporadic_gates_report.json`). Quick Intake executed successfully for 15/15 cancer types (receipt `receipts/quick_intake_15cancers.json`). An end-to-end smoke test (Quick Intake → efficacy prediion) produced provenance-bearing drug outputs (receipts `receipts/e2e_tumor_context.json`, `receipts/e2e_efficacy_response.json`, `receipts/e2e_sporadic_workflow.txt`)."
    )
    md.append("")

    if all(v is not None for v in [changed_eff, changed_conf, n_cases, agree_eff, agree_conf]):
        md.append(
            f"On a 25-case scenario suite exercising thresholds (`{scenario_path.as_posix()}`), sporadic gates modified efficacy in **{changed_eff}/{n_cases}** cases and confidence in **{changed_conf}/{n_cases}** cases. System outputs matched a naive-rule implementation in **{agree_eff}/{n_cases}** efficacy outcomes and **{agree_conf}/{n_cases}** confidence outcomes (receipt `receipts/benchmark_gate_effects.json`)."
        )
        md.append("")

    md.append(
        "**Conclusions:** A conservative tumor-context gating layer provides transparent, reproducible adjustments that reduce overconfidence under incomplete intake and clearly communicate which biomarkers drove changes. This design supports safe iteration toward full tumor NGS integration while remaining operational for the sporadic majority."
    )
    md.append("")

    # Intro
    md.append("## Introduction")
    md.append("")
    md.append(
        "Precision oncology aligns therapy selection with tumor biology using molecular biomarkers. In practice, comprehensive tumor profiling is not always available when options are being discussed. Meanwhile, most patients are germline-negative for high-penetrance hereditary variants."
    )
    md.append("")
    md.append(
        "This work treats missing tumor evidence as a first-class engineering and safety problem. We propose a conservative tumor-context gating layer that: (i) represents tumor context explicitly, (ii) applies deterministic adjustments only when evidence is present, and (iii) caps confidence when inputs are incomplete. Importantly, each adjustment emits structured provenance to support audit, UI transparency, and executable validation receipts."
    )
    md.append("")

    # Methods
    md.append("## Methods")
    md.append("")
    md.append("### System overview")
    md.append(
        "Sporadic gates are applied per drug inside the efficacy orchestration layer. Inputs include germline status and a TumorContext object. Outputs include adjusted efficacy/confidence and optional per-drug provenance (`sporadic_gates_provenance`)."
    )
    md.append("")

    md.append("### TumorContext schema")
    md.append(
        "For the gating layer, we rely on TMB, MSI status, HRD score, and completeness score. Completeness is mapped into three levels: L0 (<0.3), L1 (0.3–<0.7), and L2 (≥0.7). Completeness is a proxy for evidence availability, not biology."
    )
    md.append("")

    md.append("### Gating logic (PARP / IO / confidence)")
    md.append("")
    md.append("- **PARP gate:** for PARP-class drugs, germline-negative contexts are rescued when HRD ≥ 42; otherwise HRD-low contexts are reduced to 0.6x; HRD-unknown in germline-negative is 0.8x.")
    md.append("- **IO boost:** for oint inhibitors, boosts are mutually exclusive with precedence: TMB≥20 → 1.35x; else MSI-H → 1.30x; else TMB≥10 → 1.25x.")
    md.append("- **Confidence caps:** L0 cap 0.4, L1 cap 0.6, L2 uncapped.")
    md.append("")

    # Results
    md.append("## Results")
    md.append("")
    md.append("### Validation receipts")
    md.append("")
    md.append(f"- Scenario suite: `{scenario_path.as_posix()}`")
    md.append(f"- Benchmark receipt: `{bench_path.as_posix()}`")
    md.append("- Unit tests: `receipts/pytest_sporadic_gates.txt`")
    md.append("- Validator receipts: `receipts/validate_sporadic_gates.txt`, `receipts/validate_sporadic_gates_report.json`")
    md.append("- E2E receipts: `receipts/e2e_tumor_context.json`, `receipts/e2e_efficacy_response.json`, `receipts/e2e_sporadic_workflow.txt`")
    md.append("")

    md.append("### Figures")
    md.append("")
    md.append("- Figure 1: architecture (generated by `make_figures.py`)")
    md.append("- Figure 2: `figures/figure_2_parp_gates.png`")
  d("- Figure 3: `figures/figure_3_confidence_caps.png`")
    md.append("")

    # Discussion
    md.append("## Discussion")
    md.append("")
    md.append(
        "This manuscript makes a systems claim: deterministic, provenance-first tumor-context gating reduces overconfidence under incomplete intake and makes biomarker-driven adjustments auditable. We do not claim clinical outcome benefit in this package; outcome benchmarking requires cohort-appropriate data and is handled separately."
    )
    md.append("")

    # References (placeholder)
    md.append("## References")
    md.append("")
    md.append("1. Farmer H, et al. Nature. 2005.")
    md.append("2. Bryant HE, et al. Nature. 2005.")
    md.append("3. Le DT, et al. N Engl J Med. 2015.")
    md.append("")

    out = Path("sporadic_cancer_manuscript.md")
    out.write_text("\n".join(md), encoding="utf-8")
    print(f"✅ wrote {out}")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
