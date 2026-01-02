[Date]

Editorial Office
[AACR Journal Name]
American Association for Cancer Research

Re: Submission of manuscript, “Conservative tumor-context gating for sporadic cancers: a provenance-first approach for precision oncology when tumor NGS is unavailable”

Dear Editors,

We are submitting the enclosed manuscript for consideration in an AACR journal.

### Summary of the work
This manuscript describes a conservative, provenance-first tumor-context layer designed for the practical clinical reality that tumor NGS is often not yet available when therapy options are discussed. The system operationalizes a structured TumorContext schema (TMB, MSI status, HRD score, and completeness) and applies deterministic per-drug gates that (i) modulate PARP-class efficacy under germline-negative/HRD contexts, (ii) boost checkpoint inhibitors under high-confidence tumor biomarkers, (iii) cap confidence under incomplete intake (L0/L1) to reduce overconfident outputs. Each adjustment emits structured provenance (`sporadic_gates_provenance`) suitable for audit and UI transparency.

### Why this is appropriate for AACR
AACR journals emphasize rigorous, reproducible translational cancer research. Our contribution is a systems-and-validation paper: we provide executable receipts (unit tests, end-to-end smoke tests, scenario-suite benchmarks, and reproducible figures) demonstrating deterministic behavior and auditability. The work is framed explicitly to avoid over-claiming clinical outcome benefit: this submission establishes operational correctness and transparency as a prerequisite for outcome benchmarking on cohort-appropriate datasets.

### Claims discipline
We do **not** claim clinical outcome improvement in this submission. We claim deterministic, provenance-backed behavior and conservative confidence handling under incomplete intake.

### Data and code availability
All validation receipts, figures, and scenario-suite artifacts required to reproduce the reported results are included in `publications/sporadic_cancer/submission_aacr/`. The production gate logic is located in the main repository under `oncology-coPilot/oncology-backend-minimal/api/services/efficacy_orchestrator/sporadic_gates.py`.

### Conflicts of interest
[To be completed]

Thank you for your consideration.

Sincerely,

[Corresponding Author Name, degrees]
[Institution]
[Email]
