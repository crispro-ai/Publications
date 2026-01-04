## Synthetic Lethality Publication Bundle (Unified Clinical + Benchmark)

### Primary Manuscripts
- **Clinical Nature Medicine Draft**: `manuscript/TCGA_OV_SYNTHETIC_LETHALITY_NATURE_MEDICINE.md` (Retrospective AUROC=0.70)
- **Technical Master Manuscript**: `manuscript/main/MANUSCRIPT.md` (100-case benchmark focus)

### Entry Points & Docs
- **Results Pack Summary**: `docs/results_pack.md`
- **Error Analysis**: `docs/error_analysis.md`
- **Tables**: `manuscript/tables/tables.md`
- **Supplement**: `manuscript/supplement/supplement.md`

### Clinical Results (TCGA-OV)
- **Primary Clinical Report**: `results/clinical/tcga_ov_clinical_report.json`
- **ROC Curve (Platinum)**: `figures/clinical/roc_platinum_response.png`
- **Survival Curves**: `figures/clinical/km_os.png`, `figures/clinical/km_pfs.png`
- **Waterfall Plot**: `figures/clinical/waterfall_ddr_bin_publication.png`
- **DDR_bin Distribution**: `figures/clinical/ddr_bin_histogram_publication.png`

### Benchmark Results (100-case)
- **Primary Receipts (JSON)**: `results/publication_suite_20251230_192215.json`
- **Benchmark Figure (SVG)**: `figures/figure_bar_chart.svg`
- **DepMap grounding artifact**: `data/depmap_essentiality_by_context.json`

### Repro Scripts
- Run suite: `code/run_publication_suite.py`
- Make results pack: `code/make_results_pack.py`
- Dataset generator: `code/create_100_case_dataset.py`

### Source Code Refinements (Backend)
The refined S/P/E logic with functionalized DepMap grounding and PMID tie-breaking is implemented in:
- `oncology-backend-minimal/api/services/synthetic_lethality/dependency_identifier.py`
- `oncology-backend-minimal/api/services/synthetic_lethality/drug_recommender.py`
