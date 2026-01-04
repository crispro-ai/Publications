# Supplement (Synthetic Lethality Publication)

## Supplement A. Lineage-aware DepMap Grounding

The system functionalizes DepMap lineage data as a safety net. Below is the mapping used for lineage-specific scoring.

| Disease Context | DepMap Lineage | Example Gene Dependency (Median Effect) |
|---|---|---|
| Ovarian | Ovary/Fallopian Tube | PARP1 (-0.71), ATR (-1.09), WEE1 (-2.81) |
| Breast | Breast | BRCA1 (-0.42), BRCA2 (-0.49) |
| Pancreatic | Pancreas | KRAS (-0.85) |

## Supplement B. E-component (Evidence) Augmentation

The literature component (E) is used as an augmentation layer to break ties and provide clinical grounding.

- **Fast Mode (deterministic)**: `fast=True` (literature disabled, SP-only mechanistic floor).
- **Augmented Mode**: `fast=False` (PMID-based resolver enabled, SPE performance).

## Supplement C. Receipts and Reproducibility

1.  **Benchmark Receipt**: `results/publication_suite_20251230_192215.json`
2.  **Clinical Report (TCGA-OV)**: `oncology-backend-minimal/scripts/validation/out/ddr_bin_tcga_ov/report.json`
3.  **DepMap grounding artifact**: `data/depmap_essentiality_by_context.json`
