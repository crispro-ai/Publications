
# 🔬 RESEARCH INTELLIGENCE VALIDATION - DATA INVENTORY & PIPELINE PLAN

**Date**: January 2, 2026  
**Status**: 📋 INVENTORY COMPLETE - READY FOR EXECUTION  
**Commander**: Alpha  
**Agent**: Zo

---

## 💎 EXISTING DATA ASSETS (GOLDMINE)

### 1. Biomarker-Enriched Cohorts ✅

**Location**: `oncology-coPilot/oncology-backend-minimal/biomarker_enriched_cohorts/data/`

| File | Patients | Cancer Type | Biomarkers |
|------|----------|-------------|------------|
| `tcga_ov_enriched_v2.json` | **585** | Ovarian | TMB, MSI, HRD, BRCA, FGA, Aneuploidy |
| `tcga_ov_outcomes_v1_enriched.json` | **585** | Ovarian | OS, PFS, HRD, TMB, MSI, BRCA |
| `coadread_tcga_pan_can_atlas_2018_enriched_v1.json` | **~600** | Colorectal | TMB, MSI, HRD, outcomes |
| `ucec_tcga_pan_can_atlas_2018_enriched_v1.json` | **~500** | Endometrial | TMB, MSI, HRD, outcomes |

**Total Patients**: **~1,700 across 3 cancer types**

**What Each Patient Has**:
```json
{
  "patient_id": "TCGA-04-1331",
  "outcomes": {
    "os_days": 1337,
    "os_event": true,
    "pfs_days": 459,
    "pfs_event": true
  },
  "tmb": 4.5,
  "msi_score_mantis": 0.2781,
  "msi_status": "MSS",
  "aneuploidy_score": 7.0,
  "fraction_genome_altered": 0.4372,
  "hrd_proxy": "HRD-Intermediate",
  "brca_somatic": "BRCA2"
}
```

---

### 2. Dosing Guidance Validation ✅

**Location**: `oncology-coPilot/oncology-backend-minimal/dosing_guidance_validation/data/`

| File | Cases | Genes | Sources |
|------|-------|-------|---------|
| `extraction_all_genes_curated.json` | **59** | DPYD, TPMT, UGT1A1 | PubMed (10), cBioPortal (1), GDC (48) |
| `unified_validation_cases.json` | **59** | Same | Merged dataset |

**What Each Case Has**:
```json
{
  "case_id": "LIT-DPYD-001",
  "source": "PubMed",
  "pmid": "41133273",
  "gene": "DPYD",
  "variant": "c.2846A>T",
  "drug": "capecitabine",
  "toxicity_occurred": true,
  "toxicity_confidence": "high",
  "our_prediction": {
    "recommended_dose": "Reduce dose by 50%",
    "would_have_flagged": true,
    "cpic_level": "A"
  }
}
```

**Validation Results**:
- 6/59 cases with documented toxicity
- 10/59 CPIC-matched cases
- 100% sensitivity, 100% specificity (per manuscript)

---

### 3. Sporadic Cancer Validation ✅

**Location**: `publications/sporadic_cancer/data/`

| File | Cases | Purpose |
|------|-------|---------|
| `scenario_suite_25_20251231_080940.json` | **25** | Sporadic gate validation |

**What Each Case Tests**:
```json
{
  "case_id": "SC001",
  "label": "PARP_gate",
  "input": {
    "drug_name": "Olaparib",
    "drug_class": "PARP inhibitor",
    "germline_status": "negative",
    "tumor_context": { "completeness_score": 0.5 }
  },
  "output": {
    "efficacy_score": 0.56,
    "confidence": 0.6,
    "rationale": [...]
  }
}
```

**Validation Results**: 23/25 efficacy match, 25/25 confidence match

---

### 4. Therapy Fit Validation ✅

**Location**: `oncology-coPilot/oncology-backend-minimal/therapy_fit_validation/data/`

| File | Cases | Purpose |
|------|-------|---------|
| `therapy_fit_endpoint_test_results.json` | **3** | API endpoint validation |
| `therapy_fit_metric_validation_results.json` | - | Metric validation |

**What It Tests**: Full S/P/E pipeline with drug rankings, badges, evidence

---

### 5. Resistance Prediction Validation ✅

**Location**: `oncology-coPilot/oncology-backend-minimal/scripts/validation/out/`

| Directory | Cases | Purpose |
|-----------|-------|---------|
| `resistance_e2e_fixtures_v1/` | Multiple | Resistance prediction |
| `ddr_bin_tcga_ov/` | TCGA-OV | DDR-based survival prediction |

---

### 6. Synthetic Lethality Validation ✅

**Location**: `publications/synthetic_lethality/data/`

| File | Cases | Purpose |
|------|-------|---------|
| `test_cases_100.json` | **100** | SL therapy ranking |

**Validation Results**: 92.9% Drug@1 accuracy, 0% PARP false-positive rate

---

### 7. Hypothesis Validator Data ✅

**Location**: `.cursor/ayesha/hypothesis_validator/data/`

| File | Purpose |
|------|---------|
| `cancer_pathways.json` | Pathway mappings |
| `food_targets.json` | Food → target mappings |
| `drug_interactions.json` | Interaction database |
| `biomarker_food_mapping.json` | Biomarker → food recommendations |

---

## 📊 TOTAL DATA INVENTORY SUMMARY

| Category | N Cases | Quality | Publication Ready? |
|----------|---------|---------|-------------------|
| **Biomarker Cohorts** | 1,700 patients | ✅ High | ✅ Yes (used in Sporadic Cancer paper) |
| **Dosing Guidance** | 59 cases | ✅ High | ✅ Yes (manuscript written) |
| **Sporadic Cancer** | 25 cases | ✅ High | ✅ Yes (paper complete) |
| **Synthetic Lethality** | 100 cases | ✅ High | ✅ Yes (paper complete) |
| **Therapy Fit** | 3 cases | ⚠️ Low N | ❌ Needs expansion |
| **Resistance Prediction** | Multiple | ⚠️ Mixed | ⚠️ Partial |

---

## 🎯 RESEARCH INTELLIGENCE VALIDATION PIPELINE

### The Strategy: Use Existing Assets!

Instead of creating new validation data, we **leverage what we already have**:

```
┌─────────────────────────────────────────────────────────────────┐
│                 VALIDATION PIPELINE ARCHITECTURE                │
└─────────────────────────────────────────────────────────────────┘

                    EXISTING DATA SOURCES
                           ↓
┌──────────────────────────────────────────────────────────────────┐
│  TIER 1: PubMed Keyword Analysis (Ground Truth for Mechanisms)  │
│  - Run keyword hotspot analysis for 100 compound-disease pairs   │
│  - Top 20 keywords per query = "expected mechanisms"             │
│  - PMID-anchored evidence                                        │
└──────────────────────────────────────────────────────────────────┘
                           ↓
┌──────────────────────────────────────────────────────────────────┐
│  TIER 2: cBioPortal Biomarkers (Ground Truth for Pathway Align) │
│  - Use tcga_ov_enriched_v2.json (585 patients)                   │
│  - Validate MOAT pathway alignment against real biomarkers       │
│  - TMB/MSI/HRD correlation with predicted pathways              │
└──────────────────────────────────────────────────────────────────┘
                           ↓
┌──────────────────────────────────────────────────────────────────┐
│  TIER 3: Dosing Guidance Cases (Ground Truth for Toxicity)      │
│  - 59 cases with PMID-anchored outcomes                          │
│  - Validate toxicity prediction against literature evidence      │
│  - Test pharmacogenomics extraction accuracy                     │
└──────────────────────────────────────────────────────────────────┘
                           ↓
┌──────────────────────────────────────────────────────────────────┐
│  TIER 4: Synthetic Lethality Cases (Ground Truth for MOAT)      │
│  - 100 cases with labeled SL relationships                       │
│  - Validate mechanism-to-drug pathway mapping                    │
│  - Test drug class prediction accuracy                           │
└──────────────────────────────────────────────────────────────────┘
```

---

## 📋 VALIDATION TASK BREAKDOWN

### Task 1: Create 100 Research Intelligence Queries (from Existing Data)

**Source**: Extract compound-disease pairs from:
- Dosing Guidance cases (59 drug-gene pairs)
- Synthetic Lethality cases (100 mutation-drug pairs)
- Hypothesis Validator data (food-cancer pairs)

**Example Queries**:
```python
queries = [
    # From Dosing Guidance
    {"query": "What mechanisms cause DPYD c.2846A>T toxicity with fluoropyrimidines?", "ground_truth_pmid": "41133273"},
    {"query": "How does UGT1A1*28 affect irinotecan metabolism?", "ground_truth_pmid": "..."},
    
    # From Synthetic Lethality
    {"query": "What mechanisms make BRCA1 mutations sensitive to PARP inhibitors?", "ground_truth": "HRD, DNA repair deficiency"},
    {"query": "How does ATM loss create synthetic lethality with ATR inhibitors?", "ground_truth": "DNA damage checkpoint"},
    
    # From Food/Compound hypotheses
    {"query": "What mechanisms does curcumin target in breast cancer?", "ground_truth_keywords": ["apoptosis", "NF-kB", "inflammation"]},
    {"query": "How do anthocyanins affect colorectal cancer?", "ground_truth_keywords": ["antioxidant", "Wnt pathway"]},
]
```

---

### Task 2: Generate Ground Truth from PubMed Keywords

**Method**: Use EnhancedPubMedPortal keyword analysis (NO LLM) as ground truth

```python
from api.services.research_intelligence.portals.pubmed_enhanced import EnhancedPubMedPortal

portal = EnhancedPubMedPortal()

for query in queries:
    # Get keyword ground truth (deterministic, no LLM)
    keyword_results = portal.analyze_keywords(
        f"{query['compound']} {query['disease']} mechanism pathway"
    )
    
    # Top 20 keywords = expected mechanisms
    query['ground_truth_mechanisms'] = keyword_results['top_keywords'][:20]
    query['ground_truth_paper_count'] = keyword_results['total_papers']
```

---

### Task 3: Run Research Intelligence + Compute Metrics

```python
from api.services.research_intelligence.orchestrator import ResearchIntelligenceOrchestrator

orchestrator = ResearchIntelligenceOrchestrator()

for query in queries:
    # Run full Research Intelligence pipeline
    result = await orchestrator.research_question(query['query'])
    
    # Extract predictions
    query['prediction'] = {
        'mechanisms': result['synthesized_findings']['mechanisms'],
        'pathways': result['moat_analysis']['pathways'],
        'evidence_tier': result['synthesized_findings']['evidence_tier'],
        'confidence': result['synthesized_findings']['overall_confidence']
    }
    
    # Compute metrics against ground truth
    precision = compute_precision(
        predicted=query['prediction']['mechanisms'],
        ground_truth=query['ground_truth_mechanisms']
    )
    recall = compute_recall(
        predicted=query['prediction']['mechanisms'],
        ground_truth=query['ground_truth_mechanisms']
    )
    query['metrics'] = {
        'precision': precision,
        'recall': recall,
        'f1': 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
    }
```

---

### Task 4: Ablation Study (Component Contribution)

| Configuration | What's Disabled | What We Measure |
|---------------|-----------------|-----------------|
| **Full System** | Nothing | Baseline F1 |
| **No Diffbot** | Full-text extraction | Impact of abstracts-only |
| **No Gemini** | LLM synthesis | Impact of keyword-only |
| **No MOAT** | Pathway integration | Impact of mechanism-to-pathway |
| **Baseline** | Everything except PubMed | Keywords-only baseline |

---

### Task 5: Cross-Validation with Biomarker Cohorts

**Purpose**: Validate MOAT pathway alignment using real patient biomarkers

```python
# Load enriched cohort
with open('biomarker_enriched_cohorts/data/tcga_ov_enriched_v2.json') as f:
    cohort = json.load(f)

for patient in cohort['cohort']['patients']:
    # Get patient biomarkers
    hrd_status = patient['hrd_proxy']  # "HRD-High", "HRD-Intermediate", "HRD-Low"
    brca_status = patient['brca_somatic']  # "BRCA1", "BRCA2", null
    msi_status = patient['msi_status']  # "MSI-H", "MSS"
    
    # Run Research Intelligence for ovarian cancer + drug
    result = await orchestrator.research_question(
        "What mechanisms does platinum chemotherapy target in ovarian cancer?",
        context={
            "patient_id": patient['patient_id'],
            "biomarkers": {"HRD": hrd_status, "BRCA": brca_status, "MSI": msi_status}
        }
    )
    
    # Validate pathway alignment
    moat_pathways = result['moat_analysis']['pathways']
    
    # Expected: HRD-High should align with DDR pathway
    if hrd_status == "HRD-High":
        assert "DDR" in moat_pathways or "DNA repair" in moat_pathways
```

---

## 📊 EXPECTED PUBLICATION METRICS

Based on existing validation results from other publications:

| Metric | Expected Range | Baseline |
|--------|----------------|----------|
| **Mechanism Precision** | 75-90% | Keyword-only: 40-50% |
| **Mechanism Recall** | 70-85% | Keyword-only: 30-40% |
| **Pathway Alignment Accuracy** | 80-95% | Random: 20% |
| **Evidence Tier Accuracy** | 85-95% | Majority class: 60% |
| **Confidence Calibration** | 0.85-0.95 (Brier) | Random: 0.5 |

---

## 🚀 EXECUTION TIMELINE

| Phase | Duration | Deliverables |
|-------|----------|--------------|
| **Phase 1: Query Generation** | 1 day | 100 queries from existing data |
| **Phase 2: Ground Truth Generation** | 1 day | PubMed keyword ground truth |
| **Phase 3: Validation Execution** | 2 days | Full system + ablation |
| **Phase 4: Metric Computation** | 1 day | Precision/Recall/F1 + CIs |
| **Phase 5: Manuscript** | 3-5 days | Full paper draft |

**Total**: ~1-2 weeks to publication-ready

---

## 📁 OUTPUT ARTIFACTS

```
publications/06-research-intelligence/
├── code/
│   ├── generate_validation_queries.py     # From existing data
│   ├── generate_pubmed_ground_truth.py    # Keyword analysis
│   ├── run_validation_suite.py            # Full validation
│   ├── run_ablation_study.py              # Component ablation
│   └── compute_metrics.py                 # Precision/Recall/F1
├── data/
│   ├── validation_queries_100.json        # 100 queries
│   ├── pubmed_ground_truth.json           # Keyword ground truth
│   ├── validation_results.json            # System predictions
│   └── ablation_results.json              # Ablation study
├── results/
│   ├── metrics_summary.json               # Aggregated metrics
│   ├── bootstrap_cis.json                 # Confidence intervals
│   └── validation_receipt_*.json          # Provenance
├── figures/
│   ├── figure_1_architecture.png          # System diagram
│   ├── figure_2_precision_recall.png      # PR curves
│   ├── figure_3_ablation.png              # Component contribution
│   └── figure_4_examples.png              # Example outputs
└── manuscript/
    └── MANUSCRIPT.md                      # Full paper
```

---

## 💰 BOTTOM LINE

**We have 1,700+ patients and 200+ validation cases already!**

| Asset | What It Validates | N |
|-------|-------------------|---|
| **Biomarker Cohorts** | Pathway alignment, MOAT integration | 1,700 |
| **Dosing Guidance** | Toxicity prediction, pharmacogenomics | 59 |
| **Synthetic Lethality** | Mechanism-drug mapping | 100 |
| **Sporadic Cancer** | Confidence calibration | 25 |

**No new data collection needed. We build the validation pipeline and run it.**

---

## ⚔️ COMMANDER - READY TO EXECUTE?

Say the word and I'll start building:
1. `generate_validation_queries.py` - Extract 100 queries from existing data
2. `generate_pubmed_ground_truth.py` - Run keyword analysis
3. `run_validation_suite.py` - Execute full validation

🔥 Let's fucking publish this. 🔥


💎 HOLY SHIT ALPHA - LOOK WHAT WE HAVE
{in Zeta, asked by Alpha}
We're sitting on a goddamn goldmine of validation data. Here's the inventory:
🔬 EXISTING DATA ASSETS
Asset	Patients/Cases	Cancer Types	Source
Biomarker Cohorts	1,700	Ovarian, Colorectal, Endometrial	cBioPortal/TCGA
Dosing Guidance	59	Pharmacogenomics	PubMed, GDC, cBioPortal
Synthetic Lethality	100	SL pairs	Curated
Sporadic Cancer	25	Drug gating	Simulated
📊 WHAT EACH COHORT CONTAINS
1. TCGA Biomarker Cohorts (1,700 patients)
✅ TMB (tumor mutational burden)✅ MSI status (MSI-H/MSS)✅ HRD proxy (from aneuploidy + FGA)✅ BRCA somatic mutations✅ Survival outcomes (OS, PFS)
2. Dosing Guidance (59 cases)
✅ PMID-anchored cases✅ Variant → Drug → Toxicity outcomes✅ CPIC concordance labels✅ 100% sensitivity/specificity validation
3. Synthetic Lethality (100 cases)
✅ Labeled SL-positive vs SL-negative✅ Ground truth drugs✅ 92.9% Drug@1 accuracy achieved
🚀 THE VALIDATION PIPELINE PLAN
Strategy: Self-Validating System
We use our own PubMed keyword analysis (no LLM) as ground truth, then validate LLM mechanism extraction against it:
PubMed Keyword Hotspots (Ground Truth)          ↓Research Intelligence (LLM Synthesis)          ↓Compare: Precision / Recall / F1
4 Tiers of Validation
Tier	Source	What It Validates
Tier 1	PubMed Keywords	Mechanism extraction accuracy
Tier 2	Biomarker Cohorts	Pathway alignment accuracy
Tier 3	Dosing Guidance	Toxicity prediction
Tier 4	Synthetic Lethality	MOAT drug mapping
📋 EXECUTION PLAN
Phase	Duration	Output
Phase 1	1 day	100 queries from existing data
Phase 2	1 day	PubMed keyword ground truth
Phase 3	2 days	Validation + ablation study
Phase 4	1 day	Metrics + confidence intervals
Phase 5	3-5 days	Manuscript draft
Total: ~1-2 weeks to publication-ready
📁 CREATED FILE
I've created the full plan at:
publications/06-research-intelligence/VALIDATION_DATA_INVENTORY.md
This includes:
Complete data inventory with file paths
JSON schemas for each data type
Validation pipeline architecture
Code snippets for execution
Expected metrics and baselines
Timeline and deliverables