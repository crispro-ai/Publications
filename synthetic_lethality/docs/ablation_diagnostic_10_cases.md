## 10-case ablation diagnostic (SL-positive, PARP ground truth)

API: `http://127.0.0.1:8000`

Dataset: `/Users/fahadkiani/Desktop/development/crispr-assistant-main/publications/synthetic_lethality/data/data/test_cases_100.json`

| # | Case | Gene | GT Drug | S-only Pred | P-only Pred | SP Pred |
|---:|---|---|---|---|---|---|
| 1 | SL_001 | BRCA1 | niraparib/olaparib | osimertinib | ceralasertib | niraparib |
| 2 | SL_002 | BRCA1 | niraparib/olaparib | osimertinib | ceralasertib | niraparib |
| 3 | SL_014 | BRCA1 | niraparib/olaparib | osimertinib | ceralasertib | niraparib |
| 4 | SL_015 | BRCA1 | niraparib/olaparib | osimertinib | ceralasertib | niraparib |
| 5 | SL_027 | BRCA1 | niraparib/olaparib | osimertinib | ceralasertib | niraparib |
| 6 | SL_003 | BRCA2 | niraparib/olaparib | osimertinib | ceralasertib | niraparib |
| 7 | SL_004 | BRCA2 | niraparib/olaparib | osimertinib | ceralasertib | niraparib |
| 8 | SL_016 | BRCA2 | niraparib/olaparib | osimertinib | ceralasertib | niraparib |
| 9 | SL_008 | ATM | niraparib/olaparib | osimertinib | ceralasertib | niraparib |
| 10 | SL_009 | PALB2 | niraparib/olaparib | osimertinib | ceralasertib | niraparib |

### Pattern analysis

- **S-only pattern**: SYSTEMATIC (most common: `osimertinib`, 100% of cases)
- **P-only pattern**: SYSTEMATIC (most common: `ceralasertib`, 100% of cases)
- **S-only vs P-only overlap**: same prediction in **0/10** cases
- **SP accuracy vs GT**: correct in **10/10** cases

### Conclusion

Failure mode is **SYSTEMATIC** (consistent wrong top-choice dominates), consistent with a coherent but mis-calibrated ranking under ablation.
