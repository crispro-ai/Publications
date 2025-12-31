## Supplementary Information

### S1. Benchmark dataset schema
See: `publications/synthetic_lethality/data/data/test_cases_100.json`

Each case has:
- `case_id`
- `disease`
- `mutations`: list of variants
- `ground_truth`:
  - `synthetic_lethality_detected` (boolean)
  - `effective_drugs` (list)
  - `clinical_evidence.pmid` (string PMID when applicable)
  - optional DepMap grounding fields

### S2. DepMap lineage summarization
- Raw sources:
  - `data/depmap/CRISPRGeneEffect.csv`
  - `data/depmap/Model.csv`
- Output used in this bundle:
  - `publications/synthetic_lethality/data/depmap_essentiality_by_context.json`

### S3. Ablation diagnostic (sample-based)
- Supplementary File S3: `publications/synthetic_lethality/docs/ablation_diagnostic_10_cases.md`

### S4. Benchmark composition (transparency)
- `publications/synthetic_lethality/manuscript/tables/benchmark_composition.md`
- `publications/synthetic_lethality/docs/benchmark_composition.json`

### S5. Ablation table
- `publications/synthetic_lethality/manuscript/tables/ablation_table.md`
- Receipt: `publications/synthetic_lethality/results/publication_suite_20251230_192215.json`

### S6. Full receipts
- `publications/synthetic_lethality/results/publication_suite_20251230_192215.json`

### S7. Figure asset
- `publications/synthetic_lethality/figures/figure_bar_chart.svg`
### S8. Baseline comparison (Tier 3)
- `publications/synthetic_lethality/docs/baseline_comparison.md`
- `publications/synthetic_lethality/docs/baseline_comparison.json`
