## Abstract

**Background:** A patient with ovarian cancer faces hundreds of open trials but lacks a systematic method to identify which trials match her tumor's molecular vulnerabilities. Current trial navigation relies on eligibility filters (histology, stage) but does not quantify mechanism alignment between tumor profiles and drug mechanisms of action. Phase 2 oncology trials have a 71% failure rate, partly because eligibility filters enroll patients without targetable vulnerabilities alongside those with mechanism-aligned features, diluting trial signal.

**Methods:** We represent patient tumor profiles and trial drugs as 7-dimensional mechanism vectors spanning DNA damage repair (DDR), MAPK, PI3K, VEGF, HER2, immunotherapy, and efflux pathways. Trial drugs (n=59) were manually curated with mechanism of action annotations. Patient vectors were computed from somatic mutations and pathway aggregation. Mechanism fit was calculated using magnitude-weighted similarity to prevent false positives in low-burden patients. We validated (1) mechanism discrimination using a high-DDR reference patient profile and (2) matchability prevalence in a real ovarian cancer cohort (TCGA-OV, n=585).

**Results:** In a DDR-high reference profile, DDR-targeting trials (n=31) achieved mean fit of 0.874 compared to 0.038 for non-DDR trials (n=17), yielding a 23-fold discrimination ratio (Δ=0.836). Applied to 585 ovarian cancer patients (TCGA-OV), the system identified **271 patients (46.3%) as 'precision-eligible'**—possessing at least one mechanism-aligned trial (best_fit >0.5). The remaining **314 patients (53.7%)** lacked strong mechanism alignment, representing patients who would be trial-eligible by traditional criteria but lack targetable molecular features aligned with available drugs. Survival outcomes did not differ between groups (HR=1.122, p=0.288), as expected—TCGA patients were not enrolled via mechanism matching.

**Conclusions:** Mechanism-based trial matching quantifies the "precision-eligible minority" (46.3% in ovarian cancer) who possess targetable vulnerabilities aligned with available trials. This stratification enables counseling when mechanism fit is low, redirecting patients toward standard-of-care or alternative strategies. Prospective validation is required to demonstrate enrollment and outcome benefits.

---

**Claim Guardrails:**
- **Validated**: mechanism discrimination, real-cohort matchability prevalence, magnitude-weighted similarity safety fix
- **Not validated**: enrollment lift, response rates, PFS/OS benefit, causal treatment efficacy
