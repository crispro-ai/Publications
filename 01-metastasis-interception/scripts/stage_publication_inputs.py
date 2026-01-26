#!/usr/bin/env python3
"""
Stage canonical publication inputs into the repo-level `publication/` directory.

Why:
- The repo contains a full submission bundle under `publications/01-metastasis-interception/.../publication/`.
- The one-command reproduction pipeline writes to `publication/` at repo root.
- Several validation scripts previously created synthetic data if inputs were missing, which is unacceptable for resubmission.

This script makes the reproduction pipeline deterministic and fail-loud:
- Copies the canonical CSV/JSON inputs from the publication bundle into `../data/`.
- Validates the presence and basic shape of key datasets (e.g., 8×38=304 Target-Lock rows).

Usage:
  venv/bin/python scripts/metastasis/stage_publication_inputs.py

Optional env vars:
  PUBLICATION_BUNDLE_DIR: override the source bundle directory.
"""

from __future__ import annotations

import os
import shutil
from dataclasses import dataclass
from pathlib import Path

import pandas as pd


@dataclass(frozen=True)
class StageSpec:
    src_bundle_dir: Path
    dst_root_dir: Path


REQUIRED_FILES = [
    "data/real_target_lock_data.csv",
    "data/real_guide_validation_dataset.csv",
]

OPTIONAL_FILES = [
    "data/real_target_lock_data.json",
    "data/real_guide_validation_dataset.json",
]


def _default_bundle_dir() -> Path:
    return Path("publications/01-metastasis-interception/figures/publication")


def _get_spec() -> StageSpec:
    src = Path(os.environ.get("PUBLICATION_BUNDLE_DIR", str(_default_bundle_dir())))
    dst = Path("publication")
    return StageSpec(src_bundle_dir=src, dst_root_dir=dst)


def _require_exists(p: Path) -> None:
    if not p.exists():
        raise FileNotFoundError(f"Required path not found: {p}")


def _copy_file(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)


def _validate_real_target_lock(csv_path: Path) -> None:
    df = pd.read_csv(csv_path)
    required_cols = {
        "gene",
        "mission",
        "functionality",
        "essentiality",
        "chromatin",
        "regulatory",
        "target_lock_score",
        "is_primary",
        "is_secondary",
    }
    missing = sorted(list(required_cols - set(df.columns)))
    if missing:
        raise ValueError(f"{csv_path} missing required columns: {missing}")

    n_missions = df["mission"].nunique()
    n_genes = df["gene"].nunique()
    n_rows = len(df)

    # Expected for the publication bundle used in the manuscript: 8 missions × 38 genes = 304 rows
    if n_missions != 8:
        raise ValueError(f"Expected 8 missions in {csv_path}, got {n_missions}")
    if n_genes != 38:
        raise ValueError(f"Expected 38 unique genes in {csv_path}, got {n_genes}")
    if n_rows != 304:
        raise ValueError(f"Expected 304 rows in {csv_path}, got {n_rows}")



def _validate_real_guide_dataset(csv_path: Path) -> None:
    df = pd.read_csv(csv_path)
    if len(df) != 20:
        raise ValueError(f"Expected 20 guide rows in {csv_path}, got {len(df)}")
    required = {"sequence", "mission_step", "target_gene"}
    missing = sorted(list(required - set(df.columns)))
    if missing:
        raise ValueError(f"{csv_path} missing required guide columns: {missing}")
def main() -> None:
    spec = _get_spec()
    print("=" * 80)
    print("📦 Staging publication inputs → repo root `publication/`")
    print("=" * 80)
    print(f"Source bundle: {spec.src_bundle_dir}")
    print(f"Dest root:     {spec.dst_root_dir}")

    _require_exists(spec.src_bundle_dir)

    # Ensure destination exists
    (spec.dst_root_dir / "data").mkdir(parents=True, exist_ok=True)

    # Copy required inputs
    for rel in REQUIRED_FILES:
        src = spec.src_bundle_dir / rel
        dst = spec.dst_root_dir / rel
        _require_exists(src)
        _copy_file(src, dst)
        print(f"✅ {rel}")

    # Copy optional inputs if present (do not fail on missing legacy JSON files)
    for rel in OPTIONAL_FILES:
        src = spec.src_bundle_dir / rel
        dst = spec.dst_root_dir / rel
        if src.exists():
            _copy_file(src, dst)
            print(f"✅ {rel} (optional)")
        else:
            print(f"ℹ️  {rel} not present in bundle (optional)")

    # Validate key dataset(s)
    _validate_real_target_lock(spec.dst_root_dir / "data/real_target_lock_data.csv")
    print("✅ Validated `real_target_lock_data.csv` shape (8×38=304)")

    print("\n✅ Staging complete.")


if __name__ == "__main__":
    main()

