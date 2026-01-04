#!/usr/bin/env python3
"""Write a reproducibility manifest for the publication run.

Goal: prove "same inputs -> same outputs" by hashing:
- key inputs (trial_moa_vectors.json, key scripts)
- generated outputs (figures/*, tables/*)
- receipts/latest/*.json/*.txt

Outputs:
- publications/02-trial-matching/receipts/<ts>/repro_manifest.json
- publications/02-trial-matching/receipts/latest/repro_manifest.json
"""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional


def now_ts() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def list_files(base: Path, globs: List[str]) -> List[Path]:
    out: List[Path] = []
    for g in globs:
        out.extend(base.glob(g))
    return sorted([p for p in out if p.is_file()])


def main(argv: Optional[list[str]] = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out_dir", type=str, default=None, help="Receipt directory (default: receipts/<ts>)")
    args = ap.parse_args(argv)

    pub_dir = Path(__file__).resolve().parents[1]
    trial_path = Path(__file__).resolve().parents[3] / "oncology-coPilot" / "oncology-backend-minimal" / "api" / "resources" / "trial_moa_vectors.json"

    scripts_dir = pub_dir / "scripts"
    figures_dir = pub_dir / "figures"
    tables_dir = pub_dir / "tables"
    latest_dir = pub_dir / "receipts" / "latest"

    inputs = [
        trial_path,
        scripts_dir / "generate_all_figures.py",
        scripts_dir / "generate_tables.py",
        scripts_dir / "evaluate_ranking.py",
        scripts_dir / "compute_mechanism_sanity.py",
    ]

    inputs = [p for p in inputs if p.exists()]

    outputs = []
    outputs.extend(list_files(figures_dir, ["*.png", "*.pdf"]))
    outputs.extend(list_files(tables_dir, ["*.csv", "*.tex"]))
    outputs.extend(list_files(latest_dir, ["*.json", "*.txt", "*.csv"]))

    manifest = {
        "run": {
            "generated_at": datetime.now(timezone.utc).isoformat(),
        },
        "inputs": {str(p): sha256_file(p) for p in inputs},
        "outputs": {str(p.relative_to(pub_dir)): sha256_file(p) for p in outputs if p.exists()},
    }

    out_dir = Path(args.out_dir).resolve() if args.out_dir else (pub_dir / "receipts" / now_ts())
    out_dir.mkdir(parents=True, exist_ok=True)

    out_json = out_dir / "repro_manifest.json"
    out_json.write_text(json.dumps(manifest, indent=2))

    latest_dir.mkdir(parents=True, exist_ok=True)
    (latest_dir / "repro_manifest.json").write_text(out_json.read_text())

    print(f"✅ Wrote: {out_json}")
    print(f"✅ Updated latest: {latest_dir / 'repro_manifest.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
