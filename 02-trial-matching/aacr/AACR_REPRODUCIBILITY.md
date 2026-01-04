# AACR Reproducibility Statement (Receipt-Backed)

## Canonical reproduce command
```bash
cd publications/02-trial-matching/scripts
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 generate_all_figures.py --format both --output-dir ../figures --write-receipts --run-eval-if-present
```

## Receipts (stable pointers)
- `publications/02-trial-matching/receipts/latest/mechanism_sanity.json`
- `publications/02-trial-matching/receipts/latest/repro_manifest.json`
- `publications/02-trial-matching/receipts/latest/generate_all_figures_stdout.txt`

## Hash manifest
`repro_manifest.json` records SHA256 hashes of key inputs and outputs for deterministic verification.

## SME adjudication (optional)
- Blinded SME packet: `publications/02-trial-matching/receipts/latest/sme_packet.json`
- SME labels file: `publications/02-trial-matching/data/labeled_eval_cases.json`
- Ranking metrics receipt (only after labels): `publications/02-trial-matching/receipts/latest/eval_ranking.json`
