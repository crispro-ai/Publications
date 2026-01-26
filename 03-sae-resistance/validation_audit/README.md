# Validation Audit Files

This directory contains all validation, audit, and testing files related to SAE resistance prediction.

## Directory Structure

### `brca/`
BRCA validation files including:
- Data leakage findings
- Nested CV validation results
- Diamond feature analysis
- Improvement strategies
- Execution progress

### `ovarian/`
Ovarian cancer validation files including:
- Data leakage findings (0.783 → 0.478)
- Nested CV validation results
- Diamond feature testing (MEAN vs MAX aggregation)
- Ovarian pivot execution plan
- Moment of truth results

### `serial_sae/`
Serial SAE (GSE165897) validation files including:
- GSE165897 manuscript draft with overfitting audit
- Post-treatment pathway score validation

## Key Findings

### BRCA Validation
- **Original AUROC**: 0.844 (invalid due to data leakage)
- **Corrected AUROC**: 0.607 (nested CV, mean aggregation)
- **Status**: Below baseline (Oncotype DX 0.650)

### Ovarian Validation
- **Original AUROC**: 0.783 (invalid due to data leakage)
- **Corrected AUROC**: 0.478 (nested CV with feature selection)
- **Diamond features (MAX)**: 0.555 (weak signal, not publication-worthy)
- **Status**: Worse than random or weak signal

### Serial SAE (GSE165897)
- **Sample size**: n=11 (extremely small)
- **EPV**: 1.33 (high overfitting risk)
- **Validation**: No cross-validation, no bootstrap CIs
- **Status**: Hypothesis-generating, requires external validation

## Lessons Learned

1. **Data leakage is critical**: Feature selection must be inside CV folds
2. **Nested CV is essential**: Standard CV can inflate performance by 20-30 pp
3. **Small sample sizes**: EPV < 2 indicates high overfitting risk
4. **Aggregation matters**: MAX outperforms MEAN for resistance prediction
5. **Proper validation**: Bootstrap CIs, multiple testing correction required

## Files Moved

All files were moved from:
- `.cursor/MOAT/SAE_INTELLIGENCE/BRCA_VALIDATION/`
- `.cursor/MOAT/SAE_INTELLIGENCE/OVARIAN_VALIDATION/`
- `publications/serial-sae/MANUSCRIPT_DRAFT.md`

Date: 2025-01-29
