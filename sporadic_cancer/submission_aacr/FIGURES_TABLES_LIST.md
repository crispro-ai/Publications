# Figures and Tables (Submission List)

## Figures

- **Figure 1**: `figures/figure_1_architecture.png` — Architecture schematic (Inputs → TumorContext → per-drug gates → provenance-bearing outputs).
- **Figure 2**: `figures/figure_2_parp_gates.png` — PARP gate behavior (germline-negative penalty vs HRD rescue).
- **Figure 3**: `figures/figure_3_confidence_caps.png` — Confidence caps as a function of completeness (L0/L1/L2).

## Tables

- **Table 1–3**: `TABLES.md` — TumorContext fields, gate definitions, test/scenario summary.

## Supplement

- **Supplement A–C**: `SUPPLEMENT.md` — Claims-vs-code truth table, scenario-suite outputs, and example API payloat > sporadic_cancer/submission_aacr/SUBMISSION_CHECKLIST.md <<'MD'
# AACR Submission Checklist (Sporadic Cancer)

## Included

- **Manuscript**: `MANUSCRIPT_DRAFT.md`
- **Figures**: `figures/figure_1_architecture.png`, `figure_2_parp_gates.png`, `figure_3_confidence_caps.png`
- **Tables**: `TABLES.md`
- **Supplement**: `SUPPLEMENT.md`
- **Cover letter**: `COVER_LETTER.md`
- **Data/Code availability**: `DATA_CODE_AVAILABILITY.md`
- **Author contributions**: `AUTHOR_CONTRIBUTIONS.md`
- **Competing interests**: `COMPETING_INTERESTS.md`
- **Figure/Table list**: `FIGURES_TABLES_LIST.md`

## To fill before uploading to AACR portal

- **Journal selection**: [Cancer Research / Clinical Cancer Research / Cancer Research Communications]
- **Author list + affiliations**
- **Corresponding author contact**
- **Funding statement**
- **Ethics statement** (if required; this submission uses no patient-identifying data)
- **Preprint status** (if any)

## Claims discipline (important)

This submission is framed as a **systems + validation** paper:
- ✅ Claims: deterministic gate behavior, provenance, conservative confidence under incomplete intake.
- ❌ Avoid claims: improved clinical outcomes, “validated” HRD/PARP benefit, universal IO benefit.
