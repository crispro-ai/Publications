# 🎯 RESEARCH INTELLIGENCE - PRODUCT-FOCUSED EXECUTION PLAN

**Date**: January 2025  
**Commander**: Alpha  
**Agent**: Zo  
**Status**: 🎯 **VALIDATION & PROOF PLAN - BUILDING ON EXISTING SYSTEM**

---

## ✅ WHAT EXISTS (From `RESEARCH_INTELLIGENCE_STATUS.md`)

**Backend**: ✅ **100% COMPLETE - PRODUCTION READY**
- Research Intelligence Orchestrator working
- All 15 MOAT deliverables implemented
- API endpoint: `POST /api/research/intelligence`
- Gemini Deep Research active
- All portals (PubMed, GDC, PDS) integrated
- Frontend: 100% complete, 97% test pass rate

**What We're NOT Building**: The Research Intelligence system (already exists)

**What We ARE Building**: 
- ✅ Validation pipeline (prove it works)
- ✅ Metrics & baselines (prove it's better)
- ✅ Integration enhancements (trial matching)
- ✅ Publication package (document results)

---

## 🧠 THE ABSTRACTION (What We're Proving)

**"Research Intelligence extracts mechanisms from literature better than keyword search, and this improves downstream MOAT systems."**

**The Money**: Oncologist asks "Why is CA-125 rising?" → Gets evidence-backed mechanisms, pathways, trials, nutrition in 60 seconds vs 2 hours of manual research.

---

## 📋 SPRINT BREAKDOWN (Product-Focused)

### **SPRINT 1: Frontend Testing** (22 hours)

**What User Sees**: Frontend won't crash when displaying results

**What We Build**:
- Unit tests for 10 new components
- Integration tests for component wiring
- **Deliverable**: 10 test files, 80%+ coverage

**How We Know It Works**: All tests pass, no crashes in staging

**Value**: Can deploy to production without breaking

---

### **SPRINT 2: Backend Verification** (8 hours)

**What User Sees**: System actually processes queries end-to-end

**What We Build**:
- Test Research Intelligence orchestrator with 10 real queries (system exists, we're verifying)
- Verify all portals connect (PubMed, GDC, PDS) - already integrated per STATUS doc
- Verify MOAT integration returns pathways - already implemented per STATUS doc
- **Deliverable**: Test report confirming what works (validation, not building)

**How We Know It Works**: 10/10 queries return results, all portals respond, MOAT returns pathways

**Value**: Confirm system works as documented before validation pipeline

---

### **SPRINT 3: Backend Merge** (4 hours)

**What User Sees**: Surrogate Validator available in main branch

**What We Build**:
- Copy ebi worktree files to main
- Verify Surrogate Validator tests pass
- **Deliverable**: All backend code in one place

**How We Know It Works**: Tests pass, code compiles

**Value**: Can use Surrogate Validator for validation pipeline

---

### **SPRINT 4: Generate 100 Validation Queries** (8 hours)

**What User Sees**: Nothing (internal validation)

**What We Build**:
- Extract 100 compound-disease pairs from existing data:
  - 40 from Dosing Guidance (drug-gene pairs)
  - 40 from Synthetic Lethality (mutation-drug pairs)
  - 20 from Hypothesis Validator (food-cancer pairs)
- **Deliverable**: `validation_queries_100.json` with queries + source data

**How We Know It Works**: File has 100 queries, each has source (PMID/case_id), can trace back to original data

**Value**: Have validation dataset ready (no new data collection)

**Code**:
```python
# publications/06-research-intelligence/code/generate_validation_queries.py
# Extract from:
# - dosing_guidance_validation/data/unified_validation_cases.json (59 cases)
# - publications/synthetic_lethality/data/test_cases_100.json (100 cases)
# - .cursor/ayesha/hypothesis_validator/data/food_targets.json (food-cancer pairs)
```

---

### **SPRINT 5: Generate PubMed Ground Truth** (8 hours)

**What User Sees**: Nothing (internal validation)

**What We Build**:
- Run keyword hotspot analysis for each of 100 queries
- Extract top 20 keywords per query (deterministic, no LLM)
- **Deliverable**: `pubmed_ground_truth.json` with keywords = "expected mechanisms"

**How We Know It Works**: Each query has 20 keywords, keywords are from PubMed abstracts, reproducible

**Value**: Have ground truth to compare against (proves LLM > keywords)

**Code**:
```python
# publications/06-research-intelligence/code/generate_pubmed_ground_truth.py
# Use: api.services.research_intelligence.portals.pubmed_enhanced.EnhancedPubMedPortal
# Method: analyze_keywords() - deterministic keyword extraction
# Output: {query_id: {top_keywords: [...], paper_count: N}}
```

---

### **SPRINT 6: Run Research Intelligence on 100 Queries** (12 hours)

**What User Sees**: Nothing (internal validation)

**What We Build**:
- Run Research Intelligence orchestrator on all 100 queries
- Extract predictions: mechanisms, pathways, evidence_tier, confidence
- **Deliverable**: `validation_results.json` with predictions for all queries

**How We Know It Works**: All 100 queries return results, predictions have mechanisms/pathways

**Value**: Have system predictions to compare against ground truth

**Code**:
```python
# publications/06-research-intelligence/code/run_validation_suite.py
# For each query:
#   result = await orchestrator.research_question(query['query'])
#   Extract: mechanisms, pathways, evidence_tier, confidence
# Save: validation_results.json
```

---

### **SPRINT 7: Compute Metrics** (8 hours)

**What User Sees**: Nothing (internal validation)

**What We Build**:
- Compare predictions vs ground truth (keywords)
- Compute: Precision, Recall, F1 for mechanisms
- Compute: Pathway alignment accuracy
- Compute: Evidence tier accuracy
- **Deliverable**: `metrics_summary.json` with all metrics

**How We Know It Works**: Metrics computed, can see if RI > baseline

**Value**: Can prove system works (or doesn't)

**Code**:
```python
# publications/06-research-intelligence/code/compute_metrics.py
# For each query:
#   precision = overlap(predicted_mechanisms, ground_truth_keywords) / len(predicted)
#   recall = overlap(predicted_mechanisms, ground_truth_keywords) / len(ground_truth)
#   f1 = 2 * precision * recall / (precision + recall)
# Aggregate: mean precision, recall, f1 across 100 queries
```

---

### **SPRINT 8: Run Baselines** (8 hours)

**What User Sees**: Nothing (internal validation)

**What We Build**:
- Run PubMed abstract-only search (no LLM) on 100 queries
- Run ChatGPT-4 direct query on 100 queries
- Run keyword matching baseline on 100 queries
- Compute same metrics for baselines
- **Deliverable**: `baseline_results.json` with baseline metrics

**How We Know It Works**: Baselines return results, metrics computed

**Value**: Can compare RI vs baselines (proves RI is better)

**Code**:
```python
# publications/06-research-intelligence/code/run_baselines.py
# Baseline 1: PubMed abstract-only (no LLM synthesis)
# Baseline 2: ChatGPT-4 direct query (no multi-portal)
# Baseline 3: Keyword matching (simple string matching)
# Compute same metrics for each baseline
```

---

### **SPRINT 9: Ablation Study** (8 hours)

**What User Sees**: Nothing (internal validation)

**What We Build**:
- Run RI without Diffbot (abstracts only)
- Run RI without Gemini (keyword only)
- Run RI without MOAT (no pathway integration)
- Compute metrics for each configuration
- **Deliverable**: `ablation_results.json` showing component contribution

**How We Know It Works**: Each configuration returns results, metrics show which components matter

**Value**: Can prove which components add value (or don't)

**Code**:
```python
# publications/06-research-intelligence/code/run_ablation_study.py
# Configuration 1: Full system (baseline)
# Configuration 2: No Diffbot (disable full-text extraction)
# Configuration 3: No Gemini (disable LLM synthesis)
# Configuration 4: No MOAT (disable pathway integration)
# Run 100 queries through each, compute metrics
```

---

### **SPRINT 10: Biomarker Cohort Validation** (8 hours)

**What User Sees**: Nothing (internal validation)

**What We Build**:
- Load `tcga_ov_enriched_v2.json` (585 patients)
- For each patient: Run RI query with patient biomarkers
- Validate: HRD-High patients → DDR pathway predicted
- Validate: MSI-H patients → IO pathway predicted
- **Deliverable**: `biomarker_validation_results.json` with pathway alignment accuracy

**How We Know It Works**: Pathway predictions match biomarker status (HRD-High → DDR)

**Value**: Can prove MOAT pathway alignment matches real patient data

**Code**:
```python
# publications/06-research-intelligence/code/validate_biomarker_cohorts.py
# Load: biomarker_enriched_cohorts/data/tcga_ov_enriched_v2.json
# For each patient:
#   query = "What mechanisms does platinum target in ovarian cancer?"
#   context = {"biomarkers": {"HRD": patient['hrd_proxy'], "MSI": patient['msi_status']}}
#   result = await orchestrator.research_question(query, context)
#   Validate: if HRD-High, then "DDR" in result['moat_analysis']['pathways']
# Compute: % of patients where pathway prediction matches biomarker
```

---

### **SPRINT 11: Trial Matching Integration** (12 hours)

**What User Sees**: Better trial recommendations with mechanism-fit ranking

**What We Build**:
- Use Research Intelligence to extract MoA vectors for 200+ trials
- Compare: Manual tagging (47 trials) vs RI extraction (200+ trials)
- Validate: Does RI-extracted MoA improve mechanism fit scores?
- **Deliverable**: Enhanced trial matching with RI-extracted MoA vectors

**How We Know It Works**: 
- RI extracts MoA for 200+ trials (vs 47 manual)
- Mechanism fit scores correlate with manual tagging
- Trial ranking improves (Recall@3, MRR)

**Value**: Can match more trials (200+ vs 47), better mechanism alignment

**Code**:
```python
# publications/06-research-intelligence/code/integrate_trial_matching.py
# For each trial:
#   query = f"What mechanisms does {trial_drug} target in {disease}?"
#   result = await orchestrator.research_question(query)
#   Extract: 7D mechanism vector from result['moat_analysis']['sae_features']
# Compare: RI-extracted vector vs manual tagging (for 47 trials)
# Validate: Mechanism fit correlation
```

---

### **SPRINT 12: Generate Publication Package** (8 hours)

**What User Sees**: Publication-ready manuscript

**What We Build**:
- Generate figures: Precision/Recall curves, ablation study, examples
- Generate tables: Metrics summary, baseline comparison, ablation results
- Write manuscript: Methods, Results, Discussion
- **Deliverable**: `MANUSCRIPT.md` with all figures/tables

**How We Know It Works**: Manuscript has all required sections, figures/tables match results

**Value**: Can submit paper to journal

**Code**:
```python
# publications/06-research-intelligence/code/generate_publication_package.py
# Generate:
#   - figure_1_architecture.png (system diagram)
#   - figure_2_precision_recall.png (PR curves)
#   - figure_3_ablation.png (component contribution)
#   - table_1_metrics_summary.csv (all metrics)
#   - table_2_baseline_comparison.csv (RI vs baselines)
#   - MANUSCRIPT.md (full paper)
```

---

### **SPRINT 13: Staging Deployment** (8 hours)

**What User Sees**: System available in staging for testing

**What We Build**:
- Deploy frontend to staging
- Deploy backend to staging
- Set up monitoring (error tracking, performance)
- Run smoke tests (10 queries)
- **Deliverable**: Staging environment live

**How We Know It Works**: 
- Staging accessible
- 10/10 smoke tests pass
- No crashes
- Response time < 60 seconds

**Value**: Can test with real users before production

---

### **SPRINT 14: Production Deployment** (8 hours)

**What User Sees**: System available in production

**What We Build**:
- Deploy to production
- Monitor usage patterns
- Collect feedback
- **Deliverable**: Production system live

**How We Know It Works**: 
- Production accessible
- Users can submit queries
- System handles load
- No critical bugs

**Value**: Real users can use system

---

## 📊 SPRINT SUMMARY

| Sprint | Hours | What User Sees | Deliverable | How We Know It Works |
|--------|-------|----------------|-------------|----------------------|
| **1. Frontend Testing** | 22 | Frontend won't crash | 10 test files | All tests pass |
| **2. Backend Verification** | 8 | System processes queries | Test report | 10/10 queries work |
| **3. Backend Merge** | 4 | Surrogate Validator available | Code merged | Tests pass |
| **4. Generate Queries** | 8 | Nothing (internal) | 100 queries JSON | File has 100 queries |
| **5. Ground Truth** | 8 | Nothing (internal) | Keywords JSON | 20 keywords per query |
| **6. Run RI** | 12 | Nothing (internal) | Predictions JSON | All queries return results |
| **7. Compute Metrics** | 8 | Nothing (internal) | Metrics JSON | Precision/Recall/F1 computed |
| **8. Run Baselines** | 8 | Nothing (internal) | Baseline metrics | Baselines return results |
| **9. Ablation Study** | 8 | Nothing (internal) | Ablation results | Component contribution shown |
| **10. Biomarker Validation** | 8 | Nothing (internal) | Pathway alignment | HRD-High → DDR matches |
| **11. Trial Matching** | 12 | Better trial recommendations | 200+ trials with MoA | Mechanism fit improves |
| **12. Publication Package** | 8 | Publication-ready paper | Manuscript + figures | Paper complete |
| **13. Staging** | 8 | System in staging | Staging live | Smoke tests pass |
| **14. Production** | 8 | System in production | Production live | Users can use it |

**Total**: 120 hours (6-8 weeks)

---

## 🎯 THE MONEY (What Each Sprint Delivers)

### **Sprints 1-3: Foundation** (34 hours)
**Value**: System works, won't crash, all code in one place

### **Sprints 4-9: Validation** (60 hours)
**Value**: Can prove system works (or doesn't), can publish results

### **Sprint 10: Biomarker Validation** (8 hours)
**Value**: Can prove MOAT pathways match real patient data

### **Sprint 11: Trial Matching** (12 hours)
**Value**: Can match 200+ trials (vs 47 manual), better mechanism alignment

### **Sprint 12: Publication** (8 hours)
**Value**: Can submit paper to journal

### **Sprints 13-14: Deployment** (16 hours)
**Value**: Real users can use system

---

## 💰 BOTTOM LINE

**What We're Building**: Research Intelligence system that extracts mechanisms from literature

**What We're Proving**: 
1. RI extracts mechanisms better than keywords (Sprints 4-9)
2. RI pathways match real patient biomarkers (Sprint 10)
3. RI improves trial matching (Sprint 11)

**What User Gets**:
- Query → Evidence-backed mechanisms in 60 seconds
- Better trial recommendations (200+ vs 47)
- Publication-ready validation results

**Total Effort**: 120 hours (6-8 weeks)

**No Padding. Just Build. Validate. Deploy. 🔥⚔️**

