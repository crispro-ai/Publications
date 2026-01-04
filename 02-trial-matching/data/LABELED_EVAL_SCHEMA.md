# Trial Matching — Labeled Evaluation Set (Schema)

This file defines what we need to **prove** ranking claims (Top‑k, MRR, NDCG) for `publications/02-trial-matching`.

## Goal
Evaluate whether mechanism-fit ranking returns **clinically relevant trials** for a patient case, vs a baseline.

## File
- `publications/02-trial-matching/data/labeled_eval_cases.json`

## Schema (JSON)
Top-level:
- `version` (string)
- `created_at` (ISO string)
- `cases` (array)

Each case:
- `case_id` (string)
- `disease` (string)
- `patient_moa_vector_7d` (array[7] of floats; order must match `trial_moa_vectors.json`: `[ddr,mapk,pi3k,vegf,her2,io,efflux]`)
- `ground_truth`:
  - `relevant_trials` (array of NCT IDs; subset of keys in `trial_moa_vectors.json`)
  - `primary_relevant_trial` (optional NCT ID; if present enables strict MRR)
- `notes` (optiontring)
- `provenance`:
  - `labeled_by` (string)
  - `labeling_method` (string; e.g. "SME review", "retrospective enrollment")
  - `blinded` (bool)

## Minimum viable dataset
- **N ≥ 20 cases** with at least 1 relevant trial each
- At least **5 DDR-high**, **5 non‑DDR**, plus mixed cases
- Labels must be human-reviewed (SME) or outcome-derived (enrollment/eligibility)

## Metrics we will compute
- Recall@k (k = 3, 5, 10)
- MRR (requires `primary_relevant_trial` or chooses the first hit in `relevant_trials`)
- NDCG@k (optional; supports multiple relevant trials)
- Coverage: fraction of cases producing any ranking (non-empty output)

