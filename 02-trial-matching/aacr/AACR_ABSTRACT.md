# AACR Abstract (Draft) — Mechanism-Based Trial Matching (Non-Outcome Validation)

## Title
Mechanism-based clinical trial matching using 7D pathway vectors with reproducible, receipt-backed validation

## Authors / Affiliations
[TBD — add names + institutions]

## Background
Trial matching is often driven by keywords and eligibility filters (histology/stage/prior therapy). These criteria are necessary but insufficient: they do not quantify whether a patient’s tumor vulnerabilities align with a trial drug’s mechanism of action (MoA), and can therefore over-enroll mechanistically non-aligned patients, diluting trial signal.

## Methods
Trials are represented with a 7D mechanism-of-action (MoA) vector. For a given patient mechanism vector, we compute **magnitude-weighted similarity** (fit = (patient·trial)/||trial||) to rank trials by mechanism fit, avoiding magnitude-invariant false positives observed under cosine similarity. We validate **non-outcome** properties of the publication bundle:
- **Reproducibility**: stable figures/tables and a cryptographic hash manifest.
- **Mechanism sanity**: DDR-tagged trials align more strongly to a DDR-heavy vector than non‑DDR trials.
- **SME adjudication (optional)**: Recall@k / MRR against blinded SME labels (not enrollment outcomes).

## Results (receipt-backed)
- **Mechanism sanity receipt**: `publications/02-trial-matching/receipts/latest/mechanism_sanity.json`
- **Reproducibility manifest**: `publications/02-trial-matching/receipts/latest/repro_manifest.json`

If SME labels exist, ranking metrics are reported from:
- `publications/02-trial-matching/receipts/latest/eval_ranking.json`

## Conclusions
This work demonstrates a reproducible, audit-ready mechanism-based ranking pipeline for trial matching. Outcome validation (enrollment/benefit) is explicitly out of scope for this bundle and is planned as future work.

## Keywords
Clinical trials; trial matching; mechanism of action; pathway vectors; reproducibility; auditability
