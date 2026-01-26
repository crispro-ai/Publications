# ClinVar Bridge Coverage Report

Generated: 2026-01-04T09:13:18Z

## What this report validates

- **Coverage (retrieval)**: can we fetch a ClinVar page for each non-CPIC variant?
- **Coverage (signal extraction)**: can we extract any classification signal using the current heuristic?
- This does **NOT** validate clinical correctness or dosing guidance accuracy for non-CPIC variants.

## Summary

- Non-CPIC variants: **49**
- ClinVar pages fetched (HTTP 200): **49/49**
- Heuristic label extracted: **49/49**
- Label distribution: `{"conflicting": 49}`

## Sample rows

- CBIO-coad_cptac_gdc-11CO036 DPYD A348T → fetched=True label=conflicting
- GDC-TCGA-COAD-001 DPYD chr6:g.18139713G>T → fetched=True label=conflicting
- GDC-TCGA-COAD-002 DPYD chr6:g.18130698delA → fetched=True label=conflicting
- GDC-TCGA-COAD-003 DPYD chr6:g.18149023G>A → fetched=True label=conflicting
- GDC-TCGA-COAD-004 DPYD chr6:g.18130729C>T → fetched=True label=conflicting
- GDC-TCGA-COAD-005 DPYD chr6:g.18133864G>A → fetched=True label=conflicting
- GDC-TCGA-COAD-006 DPYD chr6:g.18143662delA → fetched=True label=conflicting
- GDC-TCGA-COAD-007 DPYD chr6:g.18143717C>A → fetched=True label=conflicting
- GDC-TCGA-COAD-008 DPYD chr6:g.18130763G>A → fetched=True label=conflicting
- GDC-TCGA-COAD-009 DPYD chr1:g.97679174G>A → fetched=True label=conflicting
- GDC-TCGA-COAD-010 DPYD chr1:g.97828158C>A → fetched=True label=conflicting
- GDC-TCGA-COAD-011 DPYD chr1:g.97573967C>A → fetched=True label=conflicting
- GDC-TCGA-COAD-012 DPYD chr1:g.97721603A>G → fetched=True label=conflicting
- GDC-TCGA-COAD-013 DPYD chr1:g.97079145G>T → fetched=True label=conflicting
- GDC-TCGA-COAD-014 DPYD chr1:g.97306282G>A → fetched=True label=conflicting
