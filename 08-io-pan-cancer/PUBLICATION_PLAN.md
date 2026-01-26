# 💀 IO PREDICTION PAN-CANCER VALIDATION: PUBLICATION PLAN

**Date:** January 25, 2026  
**Lead:** Zo  
**Status:** 📋 **PLAN DRAFT - PENDING DATA ACQUISITION**

---

## 📋 PUBLICATION OBJECTIVE

**Title:** *Pan-Cancer Validation of a Two-Pathway Transcriptomic Biomarker for Immune Checkpoint Inhibitor Response Prediction*

**Target Journal:** Nature Medicine (primary), JCO Precision Oncology (secondary)

**Core Claim:** A simple, interpretable 2-pathway signature (TIL infiltration + T-cell exhaustion) predicts anti-PD-1 response across multiple cancer types, enabling precision patient selection.

---

## ⚠️ HONEST ASSESSMENT: CURRENT STATE

### What We HAVE Validated:

| Dataset | Cancer | Treatment | n | Our AUC | Status |
|---------|--------|-----------|---|---------|--------|
| GSE91061 (train) | Melanoma | Nivolumab | 73 | 0.601 (CV) | ✅ Internal |
| GSE91061 (test) | Melanoma | Nivolumab | 32 | 0.806 | ✅ Internal |
| GSE168204 | Melanoma | Anti-PD-1 | 11 | **0.714** | ✅ **External** |

### What We CLAIM But Haven't Proven:

| Claim | Evidence | Gap |
|-------|----------|-----|
| "Works in ovarian" | None | ❌ No ovarian IO cohort tested |
| "Pan-cancer applicability" | 1 cancer (melanoma) | ❌ Need 3-5 cancers |
| "Reduces harm" | Theoretical | ❌ No irAE correlation data |
| "Clinically useful" | Retrospective | ❌ No prospective validation |

---

## 🎯 PUBLICATION REQUIREMENTS

### Minimum Viable Publication (MVP):

| Requirement | Target | Status |
|-------------|--------|--------|
| **Internal validation** | ≥100 patients, ≥1 cancer | ✅ Done (melanoma n=105) |
| **External validation** | ≥50 patients, same cancer | ⚠️ Weak (n=11) |
| **Pan-cancer validation** | ≥3 different cancers | ❌ Not done |
| **Comparison to PD-L1/TMB** | Head-to-head in same cohort | ⚠️ Partial |

### Target Publication (Nature Medicine level):

| Requirement | Target | Status |
|-------------|--------|--------|
| **Pan-cancer discovery** | 3-5 cancers in training | ❌ |
| **Pan-cancer validation** | 3-5 cancers in validation | ❌ |
| **Total n** | ≥500 patients | ❌ |
| **Subgroup analysis** | By cancer type, PD-L1, TMB | ❌ |
| **Comparison to existing** | TMEscore, IMPRES, GEP | ⚠️ |
| **Prospective cohort** | Any size | ❌ |

---

## 📊 DATA ACQUISITION PLAN

### Phase 1: Identify Available Datasets

**Required Search:** GEO datasets with:
- Pre-treatment RNA-seq
- Checkpoint inhibitor treatment (anti-PD-1, anti-PD-L1, anti-CTLA-4)
- Clinical response data (RECIST or equivalent)
- Publicly accessible

### Priority Cancer Types:

| Priority | Cancer | Rationale | IO Response Rate |
|----------|--------|-----------|------------------|
| 1 | **Ovarian** | Core use case (Ayesha) | 4-15% |
| 2 | **NSCLC** | High IO usage, good data | 15-25% |
| 3 | **RCC** | High IO usage | 20-25% |
| 4 | **Bladder** | Atezolizumab approved | 15-20% |
| 5 | **HNSCC** | Pembrolizumab approved | 15-20% |

### Known Candidate Datasets (Need Verification):

| GEO ID | Cancer | Treatment | Claimed n | RNA-seq | Response | Status |
|--------|--------|-----------|-----------|---------|----------|--------|
| GSE206422 | Ovarian | Pembro+Bev+Cyclo | ~50? | Multi-omics | Clinical | ⏳ VERIFY |
| GSE271757 | Ovarian | Pembro+Chemo | ~40? | RNA-seq | Clinical | ⏳ VERIFY |
| GSE227666 | Ovarian | NACT±Pembro | ~50? | RNA-seq | Survival | ⏳ VERIFY |
| GSE179994 | NSCLC | Pembrolizumab | ~36? | RNA-seq | Response | ⏳ VERIFY |
| GSE67501 | RCC | Nivolumab | ~30? | RNA-seq | Response | ⏳ VERIFY |
| GSE176307 | Bladder | Atezolizumab | ~30? | RNA-seq | Response | ⏳ VERIFY |
| GSE135222 | HNSCC | Pembrolizumab | ~30? | RNA-seq | Response | ⏳ VERIFY |

**⚠️ CRITICAL:** These are claimed from web search. MUST VERIFY:
1. Actual sample size with matched response
2. Presence of TIL/Exhaustion genes in expression matrix
3. Response labels accessible (not in supplementary)
4. Pre-treatment samples (not post-treatment)

---

## 📋 DATA VERIFICATION PROTOCOL

### For Each Dataset:

```python
# STEP 1: Download metadata
# Check for: response column, sample count, pre-treatment annotation

# STEP 2: Verify expression data
# Check for: presence of key genes (CD8A, PDCD1, etc.)

# STEP 3: Count usable samples
# Criteria:
#   - Pre-treatment RNA-seq
#   - RECIST response OR survival with clear responder definition
#   - All 21 pathway genes expressed (or ≥80%)

# STEP 4: Create patient-level dataset
# Output: patient_id, cancer_type, treatment, response, til_score, exhaustion_score
```

### Key Genes That MUST Be Present:

**TIL_INFILTRATION (13 genes):**
```
CD8A, CD8B, CD3D, CD3E, CD3G, CD4, CD2, GZMA, GZMB, PRF1, IFNG, TNF, IL2
```

**EXHAUSTION (8 genes):**
```
PDCD1, CTLA4, LAG3, TIGIT, HAVCR2, BTLA, CD96, VSIR
```

**If any dataset is missing >20% of these genes → Document limitation, proceed with available genes**

---

## 🔬 ANALYSIS PLAN

### Primary Analysis:

**Step 1: Apply Trained Model (No Retraining)**

For each external cohort, apply melanoma-trained coefficients:
```
logit = -1.388 + 0.807×TIL_score + 0.633×EXHAUSTION_score
P(response) = sigmoid(logit)
```

Report: AUC with 95% CI (bootstrap, 1000 iterations)

**Step 2: Compare to Existing Biomarkers**

If available in each dataset:
- PD-L1 expression (CD274 gene)
- TMB (if mutation data available)
- TMEscore (if computable)

Report: Head-to-head AUC comparison

**Step 3: Stratified Analysis**

- By cancer type
- By treatment (anti-PD-1 vs anti-PD-L1)
- By TIL status (high vs low)

### Secondary Analyses:

**Step 4: Pan-Cancer Model**

If validated in ≥3 cancers:
- Pool all cohorts
- Train unified model
- Report: Combined AUC, heterogeneity (I² statistic)

**Step 5: Clinical Utility**

- Net reclassification improvement (NRI)
- Decision curve analysis
- Number needed to screen (NNS)

---

## 📋 DELIVERABLES

### Deliverable 1: Data Verification Report

**Deadline:** 3 days from start

| Output | Content |
|--------|---------|
| `data_verification.md` | Verified n, gene coverage, response rates |
| `usable_cohorts.json` | List of cohorts that pass QC |
| `exclusion_reasons.md` | Why any cohorts were excluded |

**Success Criteria:**
- ≥3 cohorts with ≥25 patients each
- ≥2 cancer types beyond melanoma
- Gene coverage ≥80% in all cohorts

**Failure Criteria:**
- <2 usable cohorts → Paper not possible
- All ovarian cohorts fail → Ovarian claim not possible

### Deliverable 2: Validation Results

**Deadline:** 7 days from start

| Output | Content |
|--------|---------|
| `validation_results.json` | AUC, 95% CI, p-value per cohort |
| `forest_plot.png` | Meta-analysis forest plot |
| `roc_curves/` | ROC curve per cohort |
| `performance_table.md` | Summary statistics |

**Success Criteria:**
- ≥2 cohorts with AUC >0.60 and p<0.05
- No cohort with AUC <0.45 (worse than random)
- Pooled AUC >0.60

**Failure Criteria:**
- All cohorts AUC ~0.50 → Model doesn't generalize, paper killed
- Ovarian AUC <0.55 → Cannot claim ovarian applicability

### Deliverable 3: Manuscript Draft

**Deadline:** 14 days from start (if validation passes)

| Output | Content |
|--------|---------|
| `MANUSCRIPT_MULTI_CANCER.md` | Full manuscript draft |
| `figures/` | All figures (ROC, forest, heatmap) |
| `tables/` | All tables |
| `supplementary/` | Additional analyses |

---

## ⚠️ HONEST RISK ASSESSMENT

### High Risk Scenarios:

| Risk | Probability | Mitigation | If Occurs |
|------|-------------|------------|-----------|
| **Ovarian cohorts not available** | 30% | Try GSE206422, GSE271757, GSE227666 | Pivot to other cancers |
| **Ovarian AUC ~0.50** | 40% | — | Remove ovarian from paper |
| **All cohorts AUC ~0.50** | 20% | — | Kill paper, model doesn't generalize |
| **Missing key genes** | 25% | Impute or use available | Document limitation |
| **Insufficient sample size** | 30% | Pool multiple cohorts | Wider CIs, weaker claims |

### Realistic Outcomes:

| Outcome | Probability | Result |
|---------|-------------|--------|
| **Full success** (≥3 cancers, AUC >0.65) | 25% | Nature Medicine target |
| **Partial success** (2 cancers, AUC >0.60) | 35% | JCO Precision Oncology |
| **Ovarian only fails** (others work) | 20% | Paper without ovarian |
| **Melanoma only works** | 15% | Melanoma-specific paper |
| **Complete failure** | 5% | No paper, model abandoned |

---

## 📋 EXECUTION TIMELINE

### Day 1-3: Data Acquisition & Verification

| Day | Task | Owner | Output |
|-----|------|-------|--------|
| 1 | Download all candidate datasets from GEO | Zo | Raw data files |
| 1 | Verify sample counts and metadata | Zo | `data_inventory.md` |
| 2 | Check gene coverage in each dataset | Zo | `gene_coverage.csv` |
| 2 | Extract response labels | Zo / Agent X if scrape needed | `response_labels.csv` |
| 3 | Create unified analysis-ready dataset | Zo | `analysis_cohort.json` |
| 3 | **Decision Gate:** Proceed or abort | Zo | Go/No-go |

### Day 4-7: Validation Analysis

| Day | Task | Owner | Output |
|-----|------|-------|--------|
| 4 | Compute TIL + Exhaustion scores | Zo | Pathway scores |
| 4 | Apply model, compute AUCs | Zo | `validation_results.json` |
| 5 | Bootstrap confidence intervals | Zo | 95% CIs |
| 5 | Head-to-head vs PD-L1 | Zo | Comparison table |
| 6 | Create figures (ROC, forest) | Zo | `figures/` |
| 7 | Stratified analyses | Zo | Subgroup results |
| 7 | **Decision Gate:** Validation pass/fail | Zo | Go/No-go for manuscript |

### Day 8-14: Manuscript (If Validation Passes)

| Day | Task | Owner | Output |
|-----|------|-------|--------|
| 8-9 | Draft Methods + Results | Zo | Sections |
| 10-11 | Draft Introduction + Discussion | Zo | Sections |
| 12 | Create all tables | Zo | Tables |
| 13 | Finalize figures | Zo | Print-ready figures |
| 14 | Complete draft | Zo | `MANUSCRIPT_MULTI_CANCER.md` |

---

## 📋 AGENT X SUPPORT REQUIREMENTS

If data access is blocked or needs scraping:

### Potential Agent X Tasks:

| Scenario | Task | Output Needed |
|----------|------|---------------|
| **Supplementary file extraction** | Extract response labels from Excel/PDF supplements | CSV with patient_id, response |
| **Clinical trial data** | Scrape clinical trial registry for outcome data | Trial results |
| **Publication table extraction** | Extract patient-level data from publication tables | Reconstructed dataset |
| **GEO soft file parsing** | Parse complex GEO soft files | Clean metadata |

### Handoff Protocol:

If I hit a data acquisition roadblock:
1. Document exact dataset and issue
2. Create task specification for Agent X
3. Define expected output format
4. Set deadline
5. Continue with other cohorts while waiting

---

## 💀 GO/NO-GO CRITERIA

### Day 3 Gate: Data Availability

| Criterion | Go | No-Go |
|-----------|----|----|
| Usable cohorts | ≥3 cohorts, ≥100 total patients | <2 cohorts OR <50 total |
| Gene coverage | ≥80% in majority | <50% in all |
| Ovarian data | ≥1 cohort with ≥20 patients | None → proceed without ovarian |

### Day 7 Gate: Validation Results

| Criterion | Go | No-Go |
|-----------|----|----|
| Pan-cancer AUC | ≥2 cohorts AUC >0.60 | All AUC ~0.50 |
| Significance | ≥2 cohorts p <0.05 | All p >0.20 |
| Heterogeneity | I² <75% | I² >90% (too variable) |

### If No-Go:

- Document findings honestly
- Identify why model failed
- Archive analysis
- Move to alternative approach or abandon claim

---

## 📋 IMMEDIATE NEXT STEP

**Action:** Download and verify GSE206422, GSE271757, GSE227666 (ovarian) + GSE179994 (NSCLC)

**Owner:** Zo

**Method:**
1. Use GEOparse to download metadata
2. Check sample annotations for: pre-treatment, IO treatment, response
3. Download expression matrix
4. Verify key genes present
5. Report back with verified numbers

**Start:** NOW

---

**Document Status:** 📋 **PLAN APPROVED - READY FOR EXECUTION**
