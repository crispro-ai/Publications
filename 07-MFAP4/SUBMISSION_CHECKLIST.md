# Submission Checklist

## ✅ Included Files

- [x] `MANUSCRIPT_DRAFT.md` - Complete manuscript
- [x] `COVER_LETTER.md` - Submission cover letter
- [x] `DATA_CODE_AVAILABILITY.md` - Data and code availability
- [x] `AUTHOR_CONTRIBUTIONS.md` - CRediT taxonomy
- [x] `COMPETING_INTERESTS.md` - Conflicts of interest
- [x] `FIGURES_TABLES_LIST.md` - Figure and table inventory
- [x] `TABLES.md` - All tables
- [x] `SUPPLEMENT.md` - Supplementary materials

---

## 📝 Fill Before Portal Upload

### Author Information
- [ ] Author list (first name, middle initial, last name)
- [ ] Author affiliations (institution, department, city, country)
- [ ] Corresponding author (name, email, phone, address)
- [ ] Running title (max 50 characters)
- [ ] Keywords (5-10 keywords)

### Funding and Ethics
- [ ] Funding sources (grant numbers, agencies)
- [ ] Ethics statement (IRB approval, informed consent)
- [ ] Data use agreements (if applicable)

### Journal Selection
- [ ] Target journal selected (Clinical Cancer Research OR NPJ Precision Oncology)
- [ ] Journal-specific formatting checked (author guidelines)
- [ ] Word count verified (abstract <250 words, main text limits)

### Figures and Tables
- [ ] All figures generated and validated
- [ ] Figure legends complete
- [ ] Tables formatted correctly
- [ ] Supplementary materials prepared

### References
- [ ] All references formatted correctly (journal-specific style)
- [ ] PubMed IDs verified
- [ ] In-text citations match reference list
- [ ] Reference count within journal limits

---

## ✅ Claims Discipline

### Validated Claims (From Receipts)
- [x] MFAP4 AUROC = 0.763 (external validation, GSE63885)
- [x] EMT composite score CV-AUROC = 0.715 ± 0.179 (5-fold CV)
- [x] Cohort characteristics (n=101, 34 resistant, 67 sensitive)
- [x] Individual gene performance (MFAP4, SNAI1, EFEMP1, VIM, CDH1)
- [x] Bootstrap confidence intervals (n=5000 iterations)

### Not Claimed (Requires Additional Validation)
- [ ] Clinical outcome benefit (prospective validation needed)
- [ ] Treatment selection guidance (clinical trial validation needed)
- [ ] Platform translation (RNA-seq/ctDNA validation needed)
- [ ] Multi-cohort validation (additional cohorts needed)

---

## 🔍 Pre-Submission Review

### Reproducibility Check
- [ ] Run `gse63885_bootstrap_ci.py` - verify results match manuscript
- [ ] Run `generate_gse63885_figures.py` - verify figures match manuscript
- [ ] Check receipt file: `emt_platinum_auroc_results.json`
- [ ] Verify all metrics are exact (no rounding discrepancies)

### Manuscript Quality
- [ ] Abstract <250 words
- [ ] Introduction sets up problem clearly
- [ ] Methods section complete and reproducible
- [ ] Results match receipts exactly
- [ ] Discussion addresses limitations
- [ ] Conclusions are supported by data

### Data and Code Availability
- [ ] Data artifacts accessible (GSE63885 public, in-repo artifacts)
- [ ] Code scripts accessible and documented
- [ ] Reproduce commands tested and working
- [ ] Provenance tracking complete

---

## 📤 Portal Upload Checklist

### Required Files
- [ ] Manuscript (formatted per journal guidelines)
- [ ] Cover letter
- [ ] Figures (high-resolution, publication-ready)
- [ ] Tables (formatted correctly)
- [ ] Supplementary materials (if applicable)

### Author Information
- [ ] All authors listed with affiliations
- [ ] Corresponding author designated
- [ ] Author contributions completed
- [ ] Competing interests disclosed

### Additional Materials
- [ ] Data availability statement
- [ ] Code availability statement
- [ ] Ethics approval (if required)
- [ ] Funding acknowledgments

---

## 🎯 Final Validation

Before clicking "Submit":

1. **Receipts Match**: All reported numbers match `emt_platinum_auroc_results.json`
2. **Reproducibility**: Scripts run successfully and regenerate results
3. **Claims Discipline**: Only validated claims are made
4. **Journal Compliance**: Formatting matches journal guidelines
5. **Author Approval**: All authors have reviewed and approved

---

**Status**: ✅ Draft complete, ready for author review  
**Last Updated**: January 28, 2025  
**Next Step**: Author review and finalization
