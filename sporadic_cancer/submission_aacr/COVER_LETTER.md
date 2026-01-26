1/4/2026

Editorial Office
NPJ Digital Medicine
Nature Portfolio

Re: Submission of manuscript, "Scalable precision oncology via conservative biomarker gating: clinical validation in patients without comprehensive tumor sequencing"

Dear Editors,

We are submitting the enclosed manuscript for consideration in NPJ Digital Medicine.

### Summary of the work
This manuscript describes a conservative, provenance-first tumor-context layer designed for the practical clinical reality that tumor NGS is often not yet available when therapy options are discussed. The system operationalizes a structured TumorContext schema (TMB, MSI status, HRD score, and completeness) and applies deterministic per-drug gates that (i) modulate PARP-class efficacy under germline-negative/HRD contexts, (ii) boost checkpoint inhibitors under high-confidence tumor biomarkers, (iii) cap confidence under incomplete intake (L0/L1) to reduce overconfident outputs. Each adjustment emits structured provenance (`sporadic_gates_provenance`) suitable for audit and UI transparency.

We validate the system using real-world clinical cohorts (TCGA-UCEC, TCGA-COADREAD, TCGA-OV) with survival analysis demonstrating that affordable biomarkers (TMB/MSI) can stratify survival in a tumor-type-specific manner. The system demonstrates safety-first behavior under incomplete intake, with conservative confidence caps and transparent uncertainty quantification.

### Why this is appropriate for NPJ Digital Medicine
NPJ Digital Medicine emphasizes digital health innovations that address real-world clinical challenges with rigorous validation and computational reproducibility. Our contribution addresses a critical equity gap in precision oncology: most decision support systems assume complete tumor sequencing (cost: $3,000–$5,000, availability: <10%), creating barriers for resource-constrained settings. We provide executable receipts (unit tests, end-to-end smoke tests, scenario-suite benchmarks, and reproducible figures) demonstrating deterministic behavior, auditability, and full computational reproducibility. The work is framed explicitly to enable equitable deployment across diverse care settings with transparent uncertainty quantification.

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
