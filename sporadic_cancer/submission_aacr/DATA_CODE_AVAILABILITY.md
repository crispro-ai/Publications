# Data and Code Availability

## Data availability

This submission is a **systems and validation** package. The primary artifacts are executable receipts and synthetic scenario suites. All required materials are included in this submission folder:

- **Scenario suite**: `data/scenario_suite_25_*.json`
- **Receipts** (tests, validator outputs, E2E outputs): `receipts/`
- **Figures**: `figures/`
- **Tables/Supplement**: `TABLES.md`, `SUPPLEMENT.md`

No patient-identifying data are included.

## Code availability

- **Gate logic (production)**: `oncology-coPilot/oncology-backend-minimal/api/services/efficacy_orchestrator/sporadic_gates.py`
- **Figure generation (submission)**: `publications/sporadic_cancer/make_figures.py`
- **Manuscript generation (submission)**: `publications/sporadic_cancer/make_manuscript.py`

## Reproducibility

To regenerate figures and the short manuscript summary from the scenario suite:

```bash
cd publications/sporadic_cancer
python3 make_figures.py
python3 make_manuscript.py
```

The AACR submission manuscript is provided as a static artifact:
- `submission_aacr/MANUSCRIPT_DRAFT.md`
