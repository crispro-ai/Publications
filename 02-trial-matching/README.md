# Trial Matching (Publication Bundle)

This bundle validates **non-outcome** properties of mechanism-based trial matching:
- **Reproducibility**: same inputs → same rankings/figures/tables + a hash manifest.
- **Mechanism sanity**: DDR-tagged trials align more strongly to a DDR-heavy mechanism vector than non‑DDR trials.
- **SME adjudication (optional)**: ranking quality against blinded SME labels (Recall@k / MRR), explicitly **not** enrollment outcomes.

## Quick start

```bash
cd publications/02-trial-matching/scripts
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Canonical reproduce (figures + tables + receipts)
python3 generate_all_figures.py --format both --output-dir ../figures --write-receipts --run-eval-if-present
```

## Inputs

- Trial MoA vectors: `oncology-coPilot/oncology-backend-minimal/api/resources/trial_moa_vectors.json`

## Receipts (stable pointers)

- `receipts/latest/mechanism_sanity.json`
- `receipts/latest/repro_manifest.json`
- `receipts/latest/generate_all_figures_stdout.txt`
- `receipts/latest/sme_packet.json` (blinded packet for SMEs)
- `receipts/latest/eval_ranking.json` (only after SME labels exist)

## SME evaluation

1) Generate a blinded packet (Top‑N trial IDs per case):

```bash
cd publications/02-trial-matching/scripts
python3 build_sme_packet.py --top_n 15
```

2) SME fills labels in:
- `data/labeled_eval_cases.json` (add `ground_truth.relevant_trials` per case)

3) Re-run the canonical reproduce command (above). If labels exist, it writes:
- `receipts/latest/eval_ranking.json`

See:
- `SME_ADJUDICATION_PROTOCOL.md`
- `data/LABELED_EVAL_SCHEMA.md`

## Notes on claim hygiene

This bundle does **not** validate:
- enrollment lift / clinical outcomes
- Top‑k / MRR claims without SME labels
