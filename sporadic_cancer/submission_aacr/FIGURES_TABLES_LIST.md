# Figures and Tables (Submission List)

## Figures

- **Figure 1**: `figures/figure_1_architecture.png` — Architecture schematic (Inputs → TumorContext → per-drug gates → provenance-bearing outputs).
- **Figure 2**: `figures/figure_2_parp_gates.png` — PARP gate behavior (germline-negative penalty vs HRD rescue).
- **Figure 3**: `figures/figure_3_confidence_caps.png` — Confidence caps as a function of completeness (L0/L1/L2).
- **Figure 4**: `figures/clinical/figure_io_tmb_tcga_ucec_os.png` — Kaplan–Meier OS stratified by TMB-high (UCEC).
- **Figure 5**: `figures/clinical/figure_io_msi_tcga_ucec_os.png` — Kaplan–Meier OS stratified by MSI-high (UCEC).
- **Figure 6**: `figures/clinical/figure_baseline_comparison_io_tcga_ucec.png` — Combined biomarker comparison (UCEC).
- **Figure 7**: `figures/clinical/figure_baseline_comparison_io_tcga_coadread.png` — Negative control comparison (COADREAD).
- **Figure 8**: `figures/biological_coherence.png` — Biological coherence (TCGA-OV): Spearman correlations among biomarkers and gate triggers.

## Tables

- **Tables (main)**: `TABLES.md` — TumorContext fields, gate definitions, test/scenario summary.
- **Table (Tier 2)**: `results/threshold_sensitivity.csv` — Threshold sensitivity (TCGA-OV): IO boost and PARP rescue/penalty trigger rates under threshold sweeps.
- **Table (Tier 2)**: `results/subgroup_consistency.csv` — Subgroup consistency (TCGA-OV): trigger rates stratified by stage and platinum-status proxy.
- **Table (Tier 2)**: `results/biological_coherence_stats.csv` — Numeric correlation pairs backing Figure 8.

## Supplement

- **Supplement**: `SUPPLEMENT.md` — Claims-vs-code truth table, scenario-suite outputs, and example API payloads.
