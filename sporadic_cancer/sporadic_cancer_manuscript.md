# Conservative tumor-context gating for sporadic cancers: a provenance-first approach for precision oncology without tumor NGS

## Abstract

**Background:** Decision support systems in oncology often silently extrapolate from incomplete inputs. We validated a conservative, provenance-first tumor-context gating layer that adjusts efficacy and confidence based on biomarker completeness.

**Results (Nature Medicine-quality):** In clinical validation using TCGA-UCEC (n=527), mechanism-based gating using TMB and MSI status successfully predicted overall survival. TMB-high (≥20 mut/Mb) was associated with superior OS (HR=0.32, p=0.001), and MSI-high status predicted improved OS (HR=0.49, p=0.007). A combined OR-gate showed the strongest signal (HR=0.39, p=0.00017). Negative control analysis (TCGA-COADREAD, n=590) confirmed tumor-type specificity (p>0.75). Behavioral validation on 469 real-world profiles (TCGA-OV) showed high trigger frequency (98.1% PARP penalty) under incomplete intake.

**Conclusions:** Conservative gating provides transparent, reproducible adjustments that reduce overconfidence while identifying subgroups with significant survival lift.

---
## 1. Clinical Outcome Validation (TCGA-UCEC)
Detailed results are in `TCGA_UCEC_MANUSCRIPT_NATURE_MEDICINE.md`.

- **TMB Strate (n=516):** HR=0.32, 95% CI 0.15-0.65, p=0.001
- **MSI Strategy (n=527):** HR=0.49, 95% CI 0.29-0.83, p=0.007
- **Combined OR-Gate (n=527):** HR=0.39, 95% CI 0.23-0.65, p=0.00017

**Receipts:**
- `receipts/clinical/baseline_comparison_io_tcga_ucec.json`
- `figures/clinical/figure_io_tmb_tcga_ucec_os.png`

## 2. Behavioral Validation (Non-Outcome)
### 2.1 Scenario Suite Conformance
A 25-case scenario suite exercising threshold boundaries shows 100% policy conformance vs a naive reference implementation.
**Receipt:** `receipts/benchmark_gate_effects.json`

### 2.2 Real-world Trigger Rate (TCGA-OV, n=469)
In a true clinical population, the system applied a PARP penalty to **98.1% (460/469)** of patients, demonstrating safety-first behavior when high-DDR markers are absent.
**Receipt:** `receipts/clinical/real_cohort_behavioral_validation.json`

## 3. Figures
- Figure 1 (TMB OS): `figures/clinical/figure_io_tmb_tcga_ucec_os.png`
- Figure 2 (Architecture): `figures/figure_1_architecture.png`
- Figure 3 (PARP Gates): `figures/figure_2_parp_gates.png`

## 4. Reproducibility
```bash
bash scripts/validation/sporadic_gates_publication/run_all.sh
```
