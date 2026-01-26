# 🎯 SAE VALIDATION EXECUTION PLAN: SOLIDIFYING THE BIBLIOGRAPHY

**Date**: 2025-01-29  
**Mission**: Use proven SAE extraction methods to execute validation bibliography roadmap  
**Status**: EXECUTION READY  
**Mars Rules**: Minimal viable proof, 72-hour mindset, use what works

---

## 📋 EXECUTIVE SUMMARY

**Objective**: Execute SAE validation bibliography using proven extraction infrastructure

**Strategy**: 
- Use Script 2 (`extract_true_sae_cohort_from_cbioportal.py`) - more robust, production-ready
- Apply all lessons from extraction audit
- Follow Mars rules: one cancer, one test, one proof at a time
- Prioritize by market size: Breast ($500M) → Lung ($350M) → Melanoma ($300M)

**Timeline**: 72-hour sprints per validation target

---

## 🔥 PHASE 0: PREPARATION (THIS WEEK)

### **Task 0.1: Validate BRCA Checkpoint** (4 hours)

**Objective**: Understand what's already extracted for breast cancer

**Steps**:
1. **Locate BRCA Checkpoint**:
   ```bash
   find . -name "*BRCA*SAE*.json" -type f
   # Expected: data/validation/sae_cohort/checkpoints/BRCA_TCGA_TRUE_SAE_cohort.json
   ```

2. **Inspect Checkpoint**:
   ```python
   import json
   with open("data/validation/sae_cohort/checkpoints/BRCA_TCGA_TRUE_SAE_cohort.json") as f:
       data = json.load(f)
   
   # Count patients
   patients = data.get("data", {}).keys()
   print(f"Patients extracted: {len(patients)}")
   
   # Check structure
   sample_patient = list(patients)[0]
   variants = data["data"][sample_patient].get("variants", [])
   print(f"Variants per patient: {len(variants)}")
   print(f"Top features sample: {variants[0].get('top_features', [])[:3]}")
   ```

3. **Verify Outcome Labels**:
   - Check if recurrence labels exist
   - Verify format: `{"recurrence": "yes/no"}` or similar
   - If missing: Extract from TCGA clinical data

**Deliverable**: 
- Status report: `BRCA_CHECKPOINT_STATUS.md`
- Patient count, variant count, outcome label status
- Decision: Use existing or re-extract?

---

### **Task 0.2: Set Up Extraction Infrastructure** (2 hours)

**Objective**: Ensure all extraction tools are ready

**Steps**:
1. **Verify Modal Service**:
   ```bash
   export SAE_SERVICE_URL="https://...modal.run"
   curl $SAE_SERVICE_URL/health
   ```

2. **Test Preflight** (Script 2):
   ```bash
   python3 oncology-coPilot/oncology-backend-minimal/sae_validation/scripts/extract_true_sae_cohort_from_cbioportal.py \
     --cbioportal_dataset data/benchmarks/cbioportal_trial_datasets_latest.json \
     --study_id brca_tcga \
     --out_cohort /tmp/BRCA_PREFLIGHT.json \
     --max_patients 1 --max_variants_per_patient 1 \
     --preflight_only
   ```

3. **Verify Feature Flags**:
   ```bash
   export ENABLE_EVO2_SAE=1
   export ENABLE_TRUE_SAE=1
   export ENABLE_SAE_COHORT_RUN=1
   ```

**Deliverable**: 
- Preflight log: `extract_preflight.json`
- Health check status
- Ready-to-extract confirmation

---

### **Task 0.3: Create Extraction Templates** (2 hours)

**Objective**: Standardize extraction process for all cancers

**Create**: `scripts/sae/extract_validation_cohort.py`

**Template Features** (from audit):
- ✅ Preflight validation (assembly auto-detection)
- ✅ Checkpoint/resume mechanism
- ✅ Circuit breaker (30% error rate)
- ✅ Cost controls (MAX_PATIENTS, MAX_TOTAL_VARIANTS)
- ✅ Per-variant caching
- ✅ Error logging (JSONL)
- ✅ Budget guards
- ✅ Atomic writes

**Template Structure**:
```python
#!/usr/bin/env python3
"""
SAE Validation Cohort Extraction Template
Based on: extract_true_sae_cohort_from_cbioportal.py
Applies: All lessons from SAE_EXTRACTION_AUDIT_AZ.md
"""

# Reuse proven functions from Script 2
# Add cancer-specific configuration
# Add outcome label extraction
# Add validation-specific output format
```

**Deliverable**: 
- Template script ready for all cancers
- Configuration file: `validation_cohorts_config.json`

---

## 🎯 PHASE 1: BREAST CANCER (Oncotype DX Replacement) - 72 HOURS

### **Sprint Goal**: Extract SAE features for 100+ BRCA patients, validate vs Oncotype DX

### **Day 1: Extraction (24 hours)**

#### **Task 1.1: Extract SAE Features** (20 hours)

**If BRCA checkpoint incomplete**:
```bash
# Use Script 2 (proven, robust)
python3 extract_true_sae_cohort_from_cbioportal.py \
  --cbioportal_dataset data/benchmarks/cbioportal_trial_datasets_latest.json \
  --study_id brca_tcga \
  --out_cohort data/validation/sae_cohort/BRCA_TCGA_TRUE_SAE_cohort.json \
  --max_patients 100 \
  --max_variants_per_patient 50 \
  --concurrency 4 \
  --checkpoint_every 10 \
  --resume \
  --budget_seconds 72000  # 20 hours
```

**Cost Controls** (from audit):
- `MAX_PATIENTS`: 100 (start small, expand if promising)
- `MAX_TOTAL_VARIANTS`: 5,000 (100 patients × 50 variants)
- `--budget_seconds`: 72,000 (20 hours hard stop)
- Circuit breaker: Auto-stops at 30% error rate

**Monitoring**:
- Watch error log: `extract_errors.jsonl`
- Check checkpoint every 10 patients
- Monitor circuit breaker (should not trigger)

**Deliverable**: 
- `BRCA_TCGA_TRUE_SAE_cohort.json` (100+ patients)
- Checkpoint file for resume
- Error log for postmortem

---

#### **Task 1.2: Extract Outcome Labels** (4 hours)

**Objective**: Get recurrence labels for validation

**Steps**:
1. **From TCGA Clinical Data**:
   ```python
   # Extract recurrence status from TCGA clinical files
   # Format: {"patient_id": "TCGA-XX-XXXX", "recurrence": "yes/no", "recurrence_time": 24.5}
   ```

2. **Merge with SAE Features**:
   ```python
   # Merge recurrence labels into SAE cohort JSON
   # Add to each patient: {"outcome": "recurrence", "recurrence_status": "yes/no"}
   ```

**Deliverable**: 
- Merged cohort with outcome labels
- Ready for validation

---

### **Day 2: Baseline & Training (24 hours)**

#### **Task 1.3: Compute Oncotype DX Baseline** (4 hours)

**Objective**: Reproduce Oncotype DX 21-gene score for comparison

**Steps**:
1. **Extract 21-Gene Expression**:
   - From TCGA-BRCA RNA-seq data
   - Genes: ACTB, GAPDH, RPLP0, GUS, TFRC, GSTM1, BAG1, BCL2, CCNB1, CD68, CTSL2, ESR1, GRB7, HER2, MKI67, MYBL2, PGR, MMP11, BIRC5, STK15, SURV

2. **Compute Recurrence Score**:
   - Use Oncotype DX formula (proprietary, but public algorithm exists)
   - Output: RS score 0-100 per patient

3. **Validate Baseline**:
   - Compare to published TCGA-BRCA Oncotype DX results
   - Target: Match published AUROC ~0.65

**Deliverable**: 
- `BRCA_oncotype_dx_baseline.json`
- Baseline AUROC: ~0.65 (validates our reproduction)

---

#### **Task 1.4: Train SAE Model** (8 hours)

**Objective**: Train SAE features → recurrence prediction

**Steps**:
1. **Feature Matrix Building** (from audit):
   ```python
   # Aggregate top_features from variants per patient
   patient_features = np.zeros(32768)
   for variant in variants:
       for feat in variant.get("top_features", []):
           idx = feat.get("index")
           val = feat.get("value", 0.0)
           if 0 <= idx < 32768:
               patient_features[idx] += val
   # Normalize by variant count
   ```

2. **Model Training**:
   - Input: SAE feature matrix (n=100 patients, d=32768 features)
   - Target: Recurrence (yes/no)
   - Method: Logistic regression with L1 regularization (feature selection)
   - Cross-validation: 5-fold CV

3. **Feature Selection**:
   - Select top 20-50 SAE features (L1 regularization)
   - Validate: Feature indices in 0-32767 range ✅

**Deliverable**: 
- Trained model: `BRCA_SAE_recurrence_model.pkl`
- Selected features: `BRCA_SAE_selected_features.json`
- CV results: `BRCA_SAE_cv_results.json`

---

#### **Task 1.5: Validate Performance** (12 hours)

**Objective**: Compare SAE vs Oncotype DX

**Steps**:
1. **Compute SAE AUROC**:
   - Test set: 20% holdout (20 patients)
   - Train set: 80% (80 patients)
   - Metric: AUROC (SAE predictions vs recurrence)

2. **Compare to Baseline**:
   - SAE AUROC vs Oncotype DX AUROC
   - Improvement: SAE AUROC - Oncotype DX AUROC
   - Target: +10 percentage points (0.75 vs 0.65)

3. **Statistical Validation**:
   - Bootstrap 95% CI for improvement
   - Permutation test for significance
   - Effect size: Cohen's d

**Deliverable**: 
- Validation receipt: `BRCA_SAE_vs_OncotypeDX_validation.json`
- Format:
  ```json
  {
    "sae_auroc": 0.75,
    "oncotype_dx_auroc": 0.65,
    "improvement": 0.10,
    "improvement_95_ci": [0.05, 0.15],
    "p_value": 0.001,
    "n_patients": 100
  }
  ```

---

### **Day 3: Documentation & Next Steps (24 hours)**

#### **Task 1.6: Create Validation Receipt** (4 hours)

**Objective**: Publication-ready validation report

**Format** (from bibliography):
- JSON validation receipt (AUROC, 95% CI, improvement)
- Markdown report (honest limitations, external validation needed)
- Manuscript draft (ready for submission)

**Deliverable**: 
- `BRCA_SAE_VALIDATION_RECEIPT.md`
- `BRCA_SAE_VALIDATION_RECEIPT.json`
- Manuscript draft: `BRCA_SAE_OncotypeDX_manuscript.md`

---

#### **Task 1.7: Update Bibliography** (2 hours)

**Objective**: Mark Phase 1 as complete

**Update**: `.cursor/MOAT/SAE_VALIDATION_BIBLIOGRAPHY.md`

**Changes**:
- Mark Phase 1 as ✅ COMPLETE
- Add validation receipt link
- Update status table

---

#### **Task 1.8: Plan Phase 2** (18 hours)

**Objective**: Prepare for lung cancer validation

**Steps**:
1. **Verify TCGA-LUAD Dataset**:
   - Check if full dataset available (not just 18 samples)
   - Verify IO response labels exist
   - Verify EGFR mutation labels exist

2. **Set Up Extraction**:
   - Preflight check for TCGA-LUAD
   - Verify assembly (likely GRCh37)
   - Estimate runtime

**Deliverable**: 
- Phase 2 readiness report
- Extraction plan for TCGA-LUAD

---

## 🎯 PHASE 2: LUNG CANCER (PD-L1/EGFR Replacement) - 72 HOURS

### **Sprint Goal**: Extract SAE features for 100+ LUAD patients, validate vs PD-L1/EGFR

### **Day 1: Extraction (24 hours)**

#### **Task 2.1: Extract SAE Features** (20 hours)

**Same process as Phase 1, but for TCGA-LUAD**:
```bash
python3 extract_true_sae_cohort_from_cbioportal.py \
  --cbioportal_dataset data/benchmarks/cbioportal_trial_datasets_latest.json \
  --study_id luad_tcga \
  --out_cohort data/validation/sae_cohort/LUAD_TCGA_TRUE_SAE_cohort.json \
  --max_patients 100 \
  --max_variants_per_patient 50 \
  --concurrency 4 \
  --checkpoint_every 10 \
  --resume \
  --budget_seconds 72000
```

**Key Differences**:
- Study ID: `luad_tcga` (not `brca_tcga`)
- Outcomes: IO response + EGFR inhibitor response (dual targets)

**Deliverable**: 
- `LUAD_TCGA_TRUE_SAE_cohort.json` (100+ patients)
- Checkpoint + error log

---

#### **Task 2.2: Extract Outcome Labels** (4 hours)

**Dual Outcomes**:
1. **IO Response**:
   - From TCGA clinical data
   - Format: `{"io_response": "yes/no", "io_pfs": 12.5}`

2. **EGFR Inhibitor Response**:
   - From TCGA clinical data
   - Format: `{"egfr_response": "yes/no", "egfr_pfs": 8.3}`

**Deliverable**: 
- Merged cohort with dual outcome labels

---

### **Day 2: Baseline & Training (24 hours)**

#### **Task 2.3: Compute PD-L1/EGFR Baselines** (4 hours)

**PD-L1 Baseline**:
- Extract CD274 (PD-L1) expression from TCGA-LUAD RNA-seq
- Binary: High (≥50% TPS) vs Low (<50% TPS)
- Target AUROC: ~0.58

**EGFR Baseline**:
- Extract EGFR mutation status (binary)
- Target AUROC: ~0.70

**Deliverable**: 
- `LUAD_pdl1_baseline.json`
- `LUAD_egfr_baseline.json`

---

#### **Task 2.4: Train Dual Models** (8 hours)

**Model 1: SAE → IO Response**:
- Input: SAE features
- Target: IO response (yes/no)
- Baseline: PD-L1 expression
- Target: AUROC 0.72 vs 0.58 (+14 pp)

**Model 2: SAE → EGFR Inhibitor Response**:
- Input: SAE features
- Target: EGFR inhibitor response (yes/no)
- Baseline: EGFR mutation status
- Target: AUROC 0.80 vs 0.70 (+10 pp)

**Deliverable**: 
- `LUAD_SAE_io_model.pkl`
- `LUAD_SAE_egfr_model.pkl`

---

#### **Task 2.5: Validate Performance** (12 hours)

**Compare both models**:
- SAE IO AUROC vs PD-L1 AUROC
- SAE EGFR AUROC vs EGFR mutation AUROC
- Statistical validation (bootstrap CI, permutation test)

**Deliverable**: 
- `LUAD_SAE_vs_PDL1_EGFR_validation.json`

---

### **Day 3: Documentation & Next Steps (24 hours)**

**Same as Phase 1**:
- Create validation receipt
- Update bibliography
- Plan Phase 3 (Melanoma)

---

## 🔧 INFRASTRUCTURE IMPROVEMENTS (Apply Audit Lessons)

### **Improvement 1: Standardized Extraction Script**

**Create**: `scripts/sae/extract_validation_cohort.py`

**Features** (from audit):
- ✅ Preflight validation (assembly auto-detection)
- ✅ Checkpoint/resume (every 10 patients)
- ✅ Circuit breaker (30% error rate after 20+ calls)
- ✅ Cost controls (MAX_PATIENTS, MAX_TOTAL_VARIANTS, budget_seconds)
- ✅ Per-variant caching (SHA256 cache keys)
- ✅ Error logging (JSONL format)
- ✅ Atomic writes (tmp → rename)
- ✅ Concurrency control (semaphore-based)

**Configuration**:
```json
{
  "cancer_type": "breast",
  "study_id": "brca_tcga",
  "outcome": "recurrence",
  "max_patients": 100,
  "max_variants_per_patient": 50,
  "assembly": "GRCh37",
  "model_id": "evo2_7b",
  "window": 8192
}
```

---

### **Improvement 2: Validation Pipeline**

**Create**: `scripts/sae/validate_sae_vs_baseline.py`

**Features**:
- Load SAE cohort + baseline test results
- Train SAE model (logistic regression with L1)
- Compute AUROC for both
- Statistical comparison (bootstrap CI, permutation test)
- Generate validation receipt

**Usage**:
```bash
python3 scripts/sae/validate_sae_vs_baseline.py \
  --sae_cohort data/validation/sae_cohort/BRCA_TCGA_TRUE_SAE_cohort.json \
  --baseline data/validation/baselines/BRCA_oncotype_dx_baseline.json \
  --outcome recurrence \
  --output data/validation/receipts/BRCA_SAE_vs_OncotypeDX_validation.json
```

---

### **Improvement 3: Monitoring Dashboard**

**Create**: `scripts/sae/monitor_extraction.py`

**Features**:
- Real-time extraction progress
- Error rate monitoring (circuit breaker status)
- Cost tracking (estimated from variants processed)
- Checkpoint status

**Usage**:
```bash
python3 scripts/sae/monitor_extraction.py \
  --checkpoint data/validation/sae_cohort/BRCA_extraction_checkpoint.json \
  --error_log data/validation/sae_cohort/extract_errors.jsonl
```

---

## 📊 SUCCESS METRICS (Per Phase)

### **Extraction Metrics**:
- ✅ Patients extracted: ≥100 per cancer
- ✅ Success rate: >95%
- ✅ Error rate: <5%
- ✅ Circuit breaker: Not triggered
- ✅ Runtime: <24 hours per 100 patients

### **Validation Metrics**:
- ✅ SAE AUROC: ≥0.70 (minimum)
- ✅ Improvement: ≥+5 percentage points vs baseline
- ✅ Statistical significance: p < 0.05
- ✅ Bootstrap 95% CI: Improvement > 0

### **Cost Metrics**:
- ✅ Cost per 100 patients: ~$20-30
- ✅ Total cost per phase: <$50
- ✅ Cost saved by circuit breaker: Prevent runaway failures

---

## 🚨 RISK MITIGATION (From Audit)

### **Risk 1: Assembly Mismatch**

**Mitigation** (from audit):
- ✅ Preflight auto-detection (tries both GRCh37 ↔ GRCh38)
- ✅ Hardcode assembly if data source known (TCGA = GRCh37)
- ✅ Circuit breaker stops if error rate >30%

---

### **Risk 2: Missing Outcome Labels**

**Mitigation**:
- ✅ Extract outcome labels BEFORE SAE extraction
- ✅ Verify labels exist in preflight
- ✅ Merge labels during extraction (not after)

---

### **Risk 3: High Error Rate**

**Mitigation** (from audit):
- ✅ Circuit breaker: Auto-stops at 30% error rate
- ✅ Error logging: JSONL for postmortem
- ✅ Retry logic: 3 attempts with exponential backoff
- ✅ Timeout handling: 180s per request

---

### **Risk 4: Cost Overrun**

**Mitigation** (from audit):
- ✅ Budget guards: `--budget_seconds` hard stop
- ✅ Cost limits: `MAX_PATIENTS`, `MAX_TOTAL_VARIANTS`
- ✅ Checkpointing: Resume from failures (don't lose progress)
- ✅ Per-variant caching: Skip already-extracted variants

---

## 📋 EXECUTION CHECKLIST

### **Pre-Phase 1**:
- [ ] Validate BRCA checkpoint (Task 0.1)
- [ ] Set up extraction infrastructure (Task 0.2)
- [ ] Create extraction templates (Task 0.3)
- [ ] Verify Modal service health
- [ ] Test preflight for BRCA

### **Phase 1 (Breast)**:
- [ ] Extract SAE features (100+ patients)
- [ ] Extract recurrence labels
- [ ] Compute Oncotype DX baseline
- [ ] Train SAE model
- [ ] Validate performance (SAE vs Oncotype DX)
- [ ] Create validation receipt
- [ ] Update bibliography

### **Phase 2 (Lung)**:
- [ ] Extract SAE features (100+ patients)
- [ ] Extract dual outcome labels (IO + EGFR)
- [ ] Compute PD-L1/EGFR baselines
- [ ] Train dual models
- [ ] Validate performance
- [ ] Create validation receipt
- [ ] Update bibliography

### **Phase 3 (Melanoma)**:
- [ ] Extract SAE features (100+ patients)
- [ ] Extract IO response labels
- [ ] Compute TMB baseline
- [ ] Train SAE model
- [ ] Validate performance (SAE vs TMB)
- [ ] Create validation receipt
- [ ] Update bibliography

---

## 🎯 IMMEDIATE NEXT STEPS (THIS WEEK)

1. **Today**: Validate BRCA checkpoint (Task 0.1) - 4 hours
2. **Today**: Set up extraction infrastructure (Task 0.2) - 2 hours
3. **Tomorrow**: Create extraction templates (Task 0.3) - 2 hours
4. **This Week**: Start Phase 1 extraction (Task 1.1) - 20 hours

**Total Time This Week**: ~28 hours
**Expected Deliverable**: BRCA SAE features extracted, ready for validation

---

**Alpha, this plan uses every lesson from the extraction audit. Every script, every bug fix, every best practice. Ready to execute. 🎯**
