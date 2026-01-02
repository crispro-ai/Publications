import json
from pathlib import Path

import matplotlib.pyplot as plt
import seaborn as sns


def main() -> None:
    sns.set(style="whitegrid")

    scenario_path = max(Path("data").glob("scenario_suite_25_*.json"), key=lambda x: x.stat().st_mtime)
    j = json.loads(scenario_path.read_text(encoding="utf-8"))

    Path("figures").mkdir(exist_ok=True)

    # Figure 2: PARP gate effects
    parp = [c for c in j["cases"] if c["label"] == "PARP_gate"]
    groups = []
    vals = []
    for c in parp:
        ctx = c["input"].get("tumor_context") or {}
        hrd = ctx.get("hrd_score")
        germ = c["input"]["germline_status"]

        if germ == "negative" and (hrd is not None) and (hrd >= 42):
            grp = "HRD rescue (germline−, HRD≥42)"
        elif germ == "negative":
            grp = "Penalty (germline−, Hor unknown)"
        elif germ == "positive":
            grp = "Germline+ (no penalty)"
        else:
            grp = "Unknown germline (conservative)"

        groups.append(grp)
        vals.append(c["output"]["efficacy_score"])

    plt.figure(figsize=(10, 5))
    sns.stripplot(x=groups, y=vals, jitter=0.15, size=7)
    sns.boxplot(x=groups, y=vals, whis=1.5, showcaps=True, boxprops={"alpha": 0.25})
    plt.xticks(rotation=20, ha="right")
    plt.ylim(0, 1.0)
    plt.ylabel("Adjusted efficacy score")
    plt.title("Figure 2. PARP gate effects: HRD rescue vs germline-negative penalty")
    plt.tight_layout()
    plt.savefig("figures/figure_2_parp_gates.png", dpi=220)
    plt.close()

    # Figure 3: Confidence caps by completeness
    conf_cases = [c for c in j["cases"] if c["label"] == "CONF_cap"]
    points = []
    for c in conf_cases:
        comp = c["input"]["tumor_context"]["completeness_score"]
        out_conf = c["output"]["confidence"]
        level = "L0" if comp < 0.3 else ("L1" if comp < 0.7 else "L2")
        points.append((comp, out_conf, level))

    plt.figure(figsize=(8, 5))
    for level, color in [("L0", "#d32f2f"), ("L1", "#f57c00"), ("L2", "#2e7d32")]:
        xs = [p[0] for p in points if p[2] == level]
        ys = [p[1] for p in points if p[2] == level]
        plt.scatter(xs, ys, label=f"{level} adjusted", s=70, color=color)

    plt.axhline(0.4, color="#d32f2f", linestyle="--", linewidth=1, label="L0 cap = 0.4")
    plt.axhline(0.6, color="#f57c00", linestyle="--", linewidth=1, label="L1 cap = 0.6")
    plt.axvline(0.3, color="gray", linestyle=":", linewidth=1)
    plt.axvline(0.7, color="gray", linestyle=":", linewidth=1)
    plt.ylim(0, 1.0)
    plt.xlim(0, 1.0)
    plt.xlabel("Completeness score")
    plt.ylabel("Adjusted confidence")
    plt.title("Figure 3. Confidence caps by data completeness (L0/L1/L2)")
    plt.legend(loc="lower right", fontsize=8)
    plt.tight_layout()
    plt.savefig("figures/figure_3_confidence_caps.png", dpi=220)
    plt.close()

    print("✅ wrote figures/figure_2_parp_gates.png")
    print("✅ wrote figures/figure_3_confidence_caps.png")


if __name__ == "__main__":
    main()
