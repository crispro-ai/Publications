# Tables (Synthetic Lethality Publication)

## Table 1. System Performance Summary

| Metric | SP Pipeline (Full) | Rule Baseline (90 genes) | Random |
|---|---|---|---|
| **Drug@1 Accuracy** | **92.9%** [85.7%, 98.6%] | 64.3% [52.9%, 75.7%] | 15.7% [7.1%, 24.3%] |
| **PARP False Positive Rate** | **0.0%** [0.0%, 0.0%] | 33.3% [16.7%, 50.0%] | 50.0% [33.3%, 66.7%] |
| **Ablation (S-only)** | 18.6% | - | - |
| **Ablation (P-only)** | 18.6% | - | - |

## Table 2. Clinical Validation (Retrospective TCGA-OV)

| Endpoint | N | Signal (DDR_bin) | Metric | Status |
|---|---|---|---|---|
| **Platinum Response** | 149 | AUROC = 0.698 | Predictive Value | **PASS** |
| **Overall Survival** | 149 | p = 0.347 | Prognostic Value | TREND |
| **PFS** | 141 | p = 0.556 | Prognostic Value | TREND |

## Table 3. Confidence Resolver (E-component Augmentation)

| Drug Pair (Tie-break example) | Initial Score (SP) | Augmented Score (SPE) | Resolver Logic |
|---|---|---|---|
| Drug A vs Drug B | 0.91 vs 0.91 | 0.98 vs 0.91 | PMID match for Drug A (+0.07 boost) |
| Drug C vs Drug D | 0.85 vs 0.85 | 0.88 vs 0.85 | PMID match for Drug C (+0.03 boost) |

