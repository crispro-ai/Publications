# SME Adjudication Protocol (Non-outcome Validation)

This protocol enables **auditable, non-outcome validation** of the trial-matching ranking system.

## Goal
Given a patient mechanism vector, determine whether the ranked trial list contains **SME-judged relevant trials** near the top.

This produces **label-backed ranking receipts** (Recall@k / MRR) without requiring enrollment outcomes.

## Inputs
- Trial MoA vectors: `oncology-coPilot/oncology-backend-minimal/api/resources/trial_moa_vectors.json`
- Labeled cases file: `publications/02-trial-matching/data/labeled_eval_cases.json`

## Blinding
SMEs should NOT see:
- internal tags like “DDR trial” or mechanism fit scores
- any thresholds/targets used in the publication tables

SMEs MAY see:
- trial title + brief mechanism description (human-readable)
- key eligibility constraints if they are part of the inte matching scope (disease/site/line)

## Labeling task (per case)
SME provides:
- `relevant_trials`: NCT IDs that are clinically relevant for the case
- optional `primary_relevant_trial`: the single best/most-relevant NCT ID

## Provenance requirements
Each case MUST include:
- `labeled_by`
- `labeling_method` (e.g., “SME review”)
- `blinded` (true/false)
- a short note on what information the SME had access to

## Receipt generation
Run:
- `python3 publications/02-trial-matching/scripts/evaluate_ranking.py`

This writes:
- `publications/02-trial-matching/receipts/latest/eval_ranking.json`

## What we can claim from this
- Recall@k / MRR on **SME-labeled relevance** for the defined scope.

## What we cannot claim from this
- Enrollment lift
- Outcome benefit
- Screening success rate

