# PGx Dosing Guidance Publication

## The CPIC Coverage Crisis: Automated Identification and Contextualization of Pharmacogene Variants Outside Clinical Guidelines

**Target Journal:** Clinical Pharmacology & Therapeutics (IF 6.5)  
**Status:** SUBMISSION READY  
**Version:** 8.0  
**Last Updated:** January 4, 2026

---

## Quick Summary

| Metric | Value | 95% CI |
|--------|-------|--------|
| Total Cases | 59 | — |
| CPIC Coverage | 17% (10/59) | 8.4–29.0% |
| **CPIC Concordance** | **100% (10/10)** | 72.2–100.0% |
| **Toxicity Sensitivity** | **100% (6/6)** | 61.0–100.0% |
| **Specificity** | **100% (53/53)** | 93.3–100.0% |
| ClinVar Bridge | 100% (49/49) | — |

---

## Key Finding

> **83% of pharmacogene variants in clinical practice lack CPIC guideline coverage.** These patients receive "No guideline available"—a dangerous blind spot that our automated ClinVar bridge addresses.

---

## Package Contents

```
publications/05-pgx-dosing-guidance/
├── PUBLICATION_MANUSCRIPT_DRAFT.md    # Full manuscript (IMRaD)
├── VALIDATION_SUMMARY_FIGURES.md      # Figures & tables
├── PUBLICATION_PACKAGE_INDEX.md       # Master index
├── SUBMISSION_CHECKLIST.md            # Pre-submission checklist
├── COVER_LETTER.md                    # Journal cover letter
├── VALIDATION_JOURNEY_BLOG.md         # Internal: process narrative
├── README.md                          # This file
│
├── data/
│   └── extraction_all_genes_curated.json  # Raw cohort data
│
├── docs/
│   ├── SME_EXECUTIVE_SUMMARY.md       # 1-page clinical overview
│   ├── SME_REVIEW_PACKAGE.md          # Full technical review
│   ├── CONCORDANCE_REVIEW_FORM.md     # Case-by-case review
│   └── CPIC_ALIGNMENT_SUMMARY.md      # CPIC mapping reference
│
├── reports/
│   ├── cpic_concordance_report.json   # Raw concordance data
│   ├── validation_report.json         # Full validation receipt
│   └── CPIC_CONCORDANCE_REPORT.md     # Human-readable summary
│
└── scripts/
    └── (validation scripts)
```

---

## Claims Audit

All manuscript claims are verified against JSON receipts:

| Claim | Receipt | Status |
|-------|---------|--------|
| 59 total cases | `validation_report.json → metrics.total_cases` | ✅ |
| 10/59 CPIC covered | `cpic_concordance_report.json → cases_with_cpic_match` | ✅ |
| 100% concordance | `cpic_concordance_report.json → concordance_rate` | ✅ |
| 6/6 sensitivity | `validation_report.json → metrics.toxicity_prediction` | ✅ |
| 53/53 specificity | `validation_report.json → metrics.toxicity_prediction` | ✅ |

---

## Next Steps

- [ ] Obtain SME sign-off
- [ ] Complete co-author review
- [ ] Finalize cover letter
- [ ] Make GitHub repository public
- [ ] Submit to Clinical Pharmacology & Therapeutics

---

## Contact

**Project Lead:** Alpha  
**Technical Lead:** Zo

