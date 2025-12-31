## Baseline comparison (Tier 3: curated DDR gene list)

Dataset: `/Users/fahadkiani/Desktop/development/crispr-assistant-main/publications/synthetic_lethality/data/data/test_cases_100.json`

Curated DDR gene list (9): ATM, BARD1, BRCA1, BRCA2, BRIP1, CHEK2, PALB2, RAD51C, RAD51D

Rule: if any mutated gene is in curated DDR list → predict PARP (represented as `olaparib`); otherwise no prediction.

### Metrics (bootstrap 95% CI)

- SL-positive cases (n=70)
  - Coverage: 54.3% (42.9–65.7%) (38/70)
  - Drug@1 (All SL+; uncovered counted incorrect): 54.3% (42.9–65.7%)
  - Drug@1 (Covered SL+ only): 100.0% (100.0–100.0%)
- SL-negative cases (n=30)
  - PARP FP rate (rule fires on SL−): 0.0% (0.0–0.0%)

### Notes

- This is a deterministic, knowledge-lite baseline intended to approximate expert curation without sequence/pathway scoring.
- The rule is intentionally conservative: it only fires on a fixed DDR gene list, which limits coverage by design.
- Raw per-case outputs: `/Users/fahadkiani/Desktop/development/crispr-assistant-main/publications/synthetic_lethality/docs/baseline_comparison.json`
