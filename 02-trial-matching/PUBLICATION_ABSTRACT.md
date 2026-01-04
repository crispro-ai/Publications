# Mechanism-Based Trial Matching — Publication Abstract (Receipt-Backed, Non-Outcome)

**Last updated:** 2026-01-04  
**Scope:** **Non-outcome validation** (reproducibility + mechanism sanity; optional SME adjudication)  

---

## Abstract (AACR-style, ~250 words)

**Background:** Clinical trial matching is often performed using keyword search, broad eligibility filters, or single biomarkers. These approaches can miss mechanistically aligned studies and are difficult to audit when inputs are incomplete.

**Methods:** We represent trials with a 7-dimensional mechanism-of-action (MoA) vector over pathway axes: DNA damage repair (DDR), MAPK, PI3K, VEGF, HER2, immuno-oncology (IO), and efflux. Given a patient mechanism vector, we compute cosine similarity to rank trials by mechanism fit. This publication bundle validates **non-outcome** properties only: (i) reproducibility (same inputs → same outputs, verified via cryptographic hashes) and (ii) mechanism signal sanity (DDR-tagged trials should score higher than non-DDR trials against a DDR-heavy patient vector). Ranking accuracy against blinded subject matter expert (SME) labels is supported as an **optional** evaluation step when SME labels are present; enrollment/outcome validation is explicitly out of scope.

**Results (receipt-backed):** Using the current MoA vector corpus (`oncology-coPilot/oncology-backend-minimal/api/resources/trial_moa_vectors.json`, SHA256 recorded in receipts), the mechanism sanity check compared DDR-tagged trials (n=31) vs non-DDR trials (n=17) under a fixed DDR-heavy patient vector. Mean mechanism fit was **0.983** for DDR-tagged trials and **0.043** for non-DDR trials, with separation Δ = **0.940** (`receipts/latest/mechanism_sanity.json`). A reproducibility manifest records hashes of key inputs, scripts, and generated artifacts (`receipts/latest/repro_manifest.json`).

**Conclusions:** Mechanism-based ranking with explicit provenance enables reproducible, auditable trial shortlisting behavior under a pathway-vector representation. Outcome validation (enrollment/benefit) requires separate clinical datasets and is planned as future work; this bundle provides a receipt-backed foundation for safe iteration.

---

## Receipts referenced by this abstract

- Mechanism sanity: `publications/02-trial-matching/receipts/latest/mechanism_sanity.json`
- Repro manifest: `publications/02-trial-matching/receipts/latest/repro_manifest.json`
- SME packet (blinded Top-N trial IDs per case): `publications/02-trial-matching/receipts/latest/sme_packet.json`
- SME ranking metrics (only after SME labels exist): `publications/02-trial-matching/receipts/latest/eval_ranking.json`
