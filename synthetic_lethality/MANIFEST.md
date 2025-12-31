## Synthetic Lethality Publication Bundle (single folder)

### Entry points
- **Master doc**: `docs/SYNTHETIC_LETHALITY_PUBLICATION_MASTER.mdc`
- **Primary results table (copy/paste)**: `docs/results_pack.md`
- **Primary receipts (JSON)**: `results/publication_suite_20251230_192215.json`
- **Primary receipts (MD table)**: `docs/publication_suite_20251230_131605.md`
- **Figure (SVG)**: `figures/figure_bar_chart.svg`
- **Error analysis**: `docs/error_analysis.md`
- **Row-level breakdown**: `results/confusion_breakdown.csv`

### Data
- **100-case dataset**: `data/data/test_cases_100.json`
- **DepMap lineage summaries**: `data/depmap_essentiality_by_context.json`
  - Derived from `data/depmap/CRISPRGeneEffect.csv` + `data/depmap/Model.csv` in repo root.

### Repro scripts
- Run suite: `code/run_publication_suite.py`
- Make results pack: `code/make_results_pack.py`
- DepMap lineage processor: `code/generate_depmap_by_lineage.py`
- Dataset generator: `code/create_100_case_dataset.py`
- Dataset validator: `code/validate_test_cases.py`

### Quick reproduce (from repo root)

```bash
cd oncology-coPilot/oncology-backend-minimal/scripts/benchmark_sl
python3 run_publication_suite.py --test-file test_cases_100.json --api-root http://127.0.0.1:8000 --model-id evo2_1b
python3 publication/make_results_pack.py
```
