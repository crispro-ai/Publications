#!/usr/bin/env python3
"""Mission-agnostic baseline for Target-Lock validation.

Purpose
- Addresses the "stage-aware" critique by quantifying how much performance is driven by
  mission conditioning vs a mission-agnostic score.

Method
- Use staged `../data/real_target_lock_data.csv` (8 missions × 38 genes).
- Construct a per-gene mission-agnostic score = mean Target-Lock across missions.
- For each mission/step, compute AUROC/AUPRC using the agnostic score to predict that step's labels.

Outputs
- ../data/mission_agnostic_baseline.csv

Notes
- This does NOT prove clinical utility; it only tests whether the mission-conditioned scoring changes
  discrimination vs an agnostic baseline on the same curated gene universe.
"""

import json
import os
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score,average_precision_score

SEED = int(os.environ.get("SEED", "42"))
np.random.seed(SEED)

DATA_DIR = Path("publication/data")
OUT_PATH = DATA_DIR / "mission_agnostic_baseline.csv"


def load_rules() -> dict:
    rules_path = Path(
        os.environ.get(
            "METASTASIS_RULES_PATH",
            "oncology-coPilot/oncology-backend-minimal/api/config/metastasis_rules_v1.0.1.json",
        )
    )
    if not rules_path.exists():
        rules_path = Path("oncology-coPilot/oncology-backend-minimal/api/config/metastasis_rules_v1.0.0.json")
    if not rules_path.exists():
        raise FileNotFoundError(f"Missing ruleset: {rules_path}")
    return json.loads(rules_path.read_text())


def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    csv_path = DATA_DIR / "real_target_lock_data.csv"
    if not csv_path.exists():
        raise FileNotFoundError(
            f"Missing dataset: {csv_path}. Run staging first:\n"
            f"  venv/bin/python scripts/metastasis/stage_publication_inputs.py\n"
        )

    rules = load_rules()
    scores = pd.read_csv(csv_path)
    if "mission" not in scores.columns:
        raise ValueError("Expected column `mission` in real_target_lock_data.csv")

    # per-gene mission-agnostic score
    gene_avg = scores.groupby("gene")["target_lock_score"].mean().rename("target_lock_agnostic")

    results = []
    for step, step_data in rules["steps"].items():
        primary = set(step_data.get("primary_genes", []))
        secondary = set(step_data.get("secondary_genes", []))
        relevant = primary | secondary

        step_rows = scores[scores["mission"] == step].copy()
        if len(step_rows) == 0:
            continue

        y_true = step_rows["gene"].apply(lambda g: 1 if g in relevant else 0).to_numpy()
        y_score = step_rows["gene"].map(gene_avg).to_numpy()

        if len(np.unique(y_true)) < 2:
            continue

        auroc = roc_auc_score(y_true, y_score)
        auprc = average_precision_score(y_true, y_score)

        results.append(
            {
                "step": step,
                "n_genes": int(len(step_rows)),
                "n_positive": int(y_true.sum()),
                "auroc_agnostic": float(auroc),
                "auprc_agnostic": float(auprc),
            }
        )

    out = pd.DataFrame(results).sort_values("step")
    out.to_csv(OUT_PATH, index=False)

    print(f"✅ Saved mission-agnostic baseline: {OUT_PATH}")
    if len(out):
        print(f"Mean AUROC (agnostic): {out['auroc_agnostic'].mean():.3f} ± {out['auroc_agnostic'].std():.3f}")
        print(f"Mean AUPRC (agnostic): {out['auprc_agnostic'].mean():.3f} ± {out['auprc_agnostic'].std():.3f}")


if __name__ == "__main__":
    main()
