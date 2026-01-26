# AACR Submission Packet — Mechanism-Based Clinical Trial Matching

## What this is
An AACR-ready, evidence-first submission packet for the `publications/02-trial-matching` bundle. All claims are backed by reproducible JSON receipts.

## Scope (Zeta-Compliant)
- ✅ **Validated Discrimination**: 23× separation ratio between pathway-aligned and non-aligned trials.
- ✅ **Clinical Safety**: Magnitude-weighted similarity prevents low-burden false positives.
- ✅ **Ranking Accuracy**: MRR = 0.875 against pilot SME labels.
- ✅ **Reproducibility**: One-command reproduction script with SHA256 manifest.

## Included documents
- `aacr/AACR_ABSTRACT.md`: Final refactored abstract with validated metrics.
- `aacr/AACR_FIGURES_TABLES.md`: Figure captions and data tables.
- `aacr/AACR_REPRODUCIBILITY.md`: Step-by-step reproduction instructions.

## Canonical Receipts
- `rect/mechanism_sanity.json`: Discrimination metrics (0.874 vs 0.038).
- `receipts/latest/eval_ranking.json`: Ranking accuracy metrics (MRR=0.875).
- `receipts/latest/zeta_fix_validation.json`: Before/after proof of safety fix.
- `receipts/latest/repro_manifest.json`: Checksum manifest for all input vectors.
- `receipts/latest/kras_g12c_edge_case.json`: Evidence of specificity for single-gene patients.
- `receipts/latest/io_dimension_validation.json`: Evidence of independent IO axis matching.

## Final Validation Status
**OVERALL STATUS**: ✅ **FORTIFIED**
**Zeta Compliance**: **FULL** (Transparent reporting of TCGA-OV failure as technical justification).
