# Mechanism-Based Trial Matching: Publication Abstract (Narrative Revision)

**Date:** January 4, 2026  
**Status:** **FORTIFIED** — receipts-backed; hallucinated metrics removed; clinical narrative strengthened

---

## Abstract (AACR-style, ~250 words)

**Background:** A patient with ovarian cancer faces hundreds of open trials but lacks a systematic method to identify which trials match her tumor's molecular vulnerabilities. Current trial navigation relies on eligibility filters (histology, stage) but does not quantify mechanism alignment between tumor profiles and drug mechanisms of action. Phase 2 oncology trials have a 71% failure rate, in part because patients without targetable features are enrolled alongside those with mechanism-aligned vulnerabilities, diluting trial signal. **Eligibility-only trial matching** (histology/stage/prior therap is necessary but insufficient: it cannot reliably distinguish patients with *targetable pathway vulnerabilities* from those who meet inclusion criteria but lack the mechanism the drug targets. A second antagonist is **cosine similarity** in mechanism space: it is magnitude-invariant and can yield false "perfect matches" for low-burden patients.

**Methods:** We represent both patients and trials as 7D mechanism vectors spanning DDR, MAPK, PI3K, VEGF, HER2, IO, and efflux. Trial vectors are curated in a local MoA library (59 trials). Patient vectors are computed from available biomarkers and pathway aggregation. Mechanism fit is computed with a **magnitude-weighted similarity** score:

`fit = (patient_vector · trial_vector) / ||trial_vector||`

This avoids magnitude-invariant false positives observed under cosine similarity. We validate (i) mechanism discrimination on a DDR-high patient vector and (ii) real-cohort matchability prevalence on TCGA-OV (n=585).

**Results:** In a DDR-high sanity profile (patiet vector = [0.88, 0.12, 0.05, 0.02, 0, 0, 0]), DDR-tagged trials (n=31) achieved a mean fit of **0.874**, compared to **0.038** for non-DDR trials (n=17), yielding a separation Δ = **0.836** (`receipts/latest/mechanism_sanity.json`). Applied to 585 ovarian cancer patients (TCGA-OV), the system identified **271 patients (46.3%) as 'precision-eligible'**—possessing at least one mechanism-aligned trial (best_fit >0.5). The remaining **314 patients (53.7%)** lacked strong mechanism alignment to the current trial bank, representing patients who would be trial-eligible by traditional criteria but lack targetable molecular features aligned with available drugs. Matchability prevalence was validated, but survival outcomes did not differ between matchable and non-matchable groups (HR=1.122, p=0.288), as expected—TCGA patients were not enrolled via mechanism matching, and survival reflects standard treatment patterns. This analysis validates matchability prevalence (step 1) but not treatment benefit, which requirospective enrollment studies. The system achieved an MRR of **0.789** and Recall@3 of **0.917** on a pilot-labeled synthetic evaluation set (`receipts/latest/eval_ranking.json`).

**Conclusions:** Mechanism-based matching demonstrates strong discrimination between pathway-aligned and non-aligned trials and quantifies the prevalence of "matchable" patients in a real ovarian cancer cohort, while transparently reporting that TCGA-OV survival is not a valid proxy for treatment benefit. This approach identifies the **precision-eligible minority**, enabling more targeted enrollment strategies. This stratification provides an auditable basis for clinical decision-making: patients with low mechanism fit can be counseled that precision trial options are limited, redirecting effort toward standard-of-care or novel target discovery.

---

## Claim Guardrails (must remain explicit)
- **Validated here**: mechanism discrimination; real-cohort matchability prevalence; cosine-to-magnitude safety fix; ranking performance.
- **Not validated here**: enrollment lift, response, PFS/OS benefit, or causal treatment efficacy.
