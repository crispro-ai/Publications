# Data Extraction Audit for Case Study Generation

**Purpose:** Audit all available methods to extract toxicity data for building reactive vs pretreatment case studies  
**Date:** January 13, 2025  
**Status:** 🔄 **COMPREHENSIVE AUDIT**

---

## 📋 **CASE STUDY DATA REQUIREMENTS**

Based on `caseStudy.mdc`, we need to extract:

### **Core Data Elements:**
1. **PGx Variants:** DPYD, TPMT, UGT1A1, CYP2D6 variants (germline)
2. **Treatment Exposure:** Drug names, dates, doses
3. **Toxicity Outcomes:** Grade 3+ toxicity, hospitalization, specific AE types
4. **Timing:** Testing date vs treatment start date (to stratify reactive vs pretreatment)
5. **Cohort Metadata:** Sample size (N), cancer type, trial phase

### **Target Cohorts (from caseStudy.mdc):**
- **TCGA-COAD** (n=627) - Fluoropyrimidine + DPYD
- **TCGA-READ** (n=177) - Fluoropyrimidine + DPYD
- **TCGA-GBM** (n=617) - Temozolomide + MGMT
- **TCGA-SKCM** (n=470) - Immunotherapy + HLA
- **PREPARE cohort** (n=1,103) - Published DPYD RCT
- **n=442 case study** (source unknown - needs identification)

---

## 🔍 **EXISTING DATA EXTRACTION METHODS**

### **1. PubMed Literature Search** ✅ **IMPLEMENTED**

**Script:** `search_pubmed_pgx.py`  
**Location:** `oncology-coPilot/oncology-backend-minimal/scripts/data_acquisition/pgx/`

**What It Does:**
- Searches PubMed for PGx studies (DPYD, TPMT, UGT1A1)
- Extracts: PMID, title, abstract, authors, publication date, journal
- Queries include: toxicity outcomes, dose adjustments, pre-treatment screening

**Strengths:**
- ✅ Can find published case studies with reactive vs pretreatment comparisons
- ✅ Extracts prevention rates, toxicity reduction percentages
- ✅ Finds corresponding author emails for data requests

**Limitations:**
- ❌ Abstracts may not contain full toxicity tables
- ❌ No direct access to patient-level data
- ❌ May miss unpublished or conference-only data

**Use Case for Case Studies:**
- **Primary Use:** Find published papers with reactive vs pretreatment comparisons (like the n=442 case study)
- **Secondary Use:** Extract aggregate statistics (toxicity rates, ORs) from published tables

**Example Query:**
```python
query = '(pharmacogenomics OR "PGx") AND (DPYD OR dihydropyrimidine dehydrogenase) AND (fluoropyrimidine OR 5-fluorouracil OR capecitabine) AND (toxicity OR adverse OR "dose adjustment")'
```

**Enhancement Needed:**
- Add query for "reactive testing" vs "pretreatment testing" comparisons
- Add query for "terminated trial" + "toxicity" + "DPYD/TPMT"

---

### **2. ClinicalTrials.gov Search** ✅ **IMPLEMENTED**

**Script:** `search_clinicaltrials_pgx.py`  
**Location:** `oncology-coPilot/oncology-backend-minimal/scripts/data_acquisition/pgx/`

**What It Does:**
- Searches ClinicalTrials.gov for PGx trials
- Extracts: NCT ID, title, status, phase, PI contact, outcome measures
- Filters by status (COMPLETED, TERMINATED)

**Strengths:**
- ✅ Can identify terminated trials (potential case studies)
- ✅ Provides PI contact information for data requests
- ✅ Shows outcome measures (may include toxicity endpoints)

**Limitations:**
- ❌ ClinicalTrials.gov doesn't publish results (only protocol)
- ❌ No direct access to patient-level data
- ❌ Termination reasons may not specify PGx variants

**Use Case for Case Studies:**
- **Primary Use:** Identify terminated trials where Safety Gate could have prevented failure
- **Secondary Use:** Find completed trials with PGx outcomes (may have published results)

**Enhancement Needed:**
- Add filter for "TERMINATED" status + "toxicity" reason
- Cross-reference with PubMed to find published results from terminated trials

---

### **3. Prevention Rate Extraction** ✅ **IMPLEMENTED**

**Script:** `extract_prevention_rates_from_pubmed.py`  
**Location:** `oncology-coPilot/oncology-backend-minimal/scripts/data_acquisition/pgx/`

**What It Does:**
- Parses PubMed abstracts to extract:
  - Prevention rates (% prevented)
  - Toxicity reduction (% reduction)
  - Hospitalization reduction (% reduction)
  - Sample sizes (N)
  - Sensitivity/specificity

**Strengths:**
- ✅ Automated extraction from abstracts
- ✅ Handles multiple percentage formats
- ✅ Aggregates by gene (DPYD, TPMT, UGT1A1)

**Limitations:**
- ❌ Only extracts from abstracts (may miss full tables)
- ❌ May miss nuanced data (e.g., reactive vs pretreatment breakdowns)
- ❌ No validation of extracted numbers

**Use Case for Case Studies:**
- **Primary Use:** Extract aggregate statistics from published papers
- **Secondary Use:** Validate prevention rates across multiple studies

**Enhancement Needed:**
- Add extraction for "reactive" vs "pretreatment" group comparisons
- Add extraction for odds ratios (OR) and confidence intervals

---

### **4. Cost Data Extraction** ✅ **IMPLEMENTED**

**Script:** `extract_cost_data_from_trials.py`  
**Location:** `oncology-coPilot/oncology-backend-minimal/scripts/data_acquisition/pgx/`

**What It Does:**
- Identifies trials with cost-effectiveness outcomes
- Extracts cost-related keywords from outcome measures

**Strengths:**
- ✅ Identifies trials measuring cost outcomes
- ✅ Can find completed trials with published cost data

**Limitations:**
- ❌ ClinicalTrials.gov doesn't publish cost results
- ❌ Requires follow-up with PI or published papers

**Use Case for Case Studies:**
- **Secondary Use:** Find trials with cost-effectiveness data (for economic validation)

---

### **5. BioMed-MCP Integration** ✅ **IMPLEMENTED**

**Script:** `biomed_mcp_integration.py`  
**Location:** `oncology-coPilot/oncology-backend-minimal/scripts/data_acquisition/pgx/`

**What It Does:**
- Uses BioMed-MCP agents (PubMedAgent, ClinicalTrialsAgent)
- Provides unified interface for literature and trial searches
- Supports Azure OpenAI and standard OpenAI API

**Strengths:**
- ✅ More sophisticated than direct API calls
- ✅ Can handle complex queries with LLM assistance
- ✅ May extract structured data from full-text papers

**Limitations:**
- ❌ Requires OpenAI API key (cost)
- ❌ May have rate limits
- ❌ Dependent on BioMed-MCP agent quality

**Use Case for Case Studies:**
- **Primary Use:** Complex queries requiring LLM interpretation
- **Secondary Use:** Extract structured data from full-text PDFs (if available)

---

## 🆕 **MISSING DATA EXTRACTION METHODS**

### **6. TCGA Data Extraction** ❌ **NOT IMPLEMENTED**

**What We Need:**
- Extract germline variants (DPYD, TPMT, UGT1A1) from TCGA cohorts
- Extract treatment exposure data (drug names, dates)
- Extract toxicity outcomes (Grade 3+ AEs from clinical data)
- Stratify by testing timing (reactive vs pretreatment)

**Data Sources:**
- **TCGA GDC Portal:** https://portal.gdc.cancer.gov/
- **cBioPortal:** https://www.cbioportal.org/
- **TCGA Firehose:** Legacy data (may have treatment logs)

**Challenges:**
- TCGA primarily has tumor sequencing (somatic), not germline
- Treatment data may be sparse (TCGA focused on genomics, not treatment)
- Toxicity data may not be standardized (different AE reporting formats)

**Implementation Approach:**
```python
# Pseudo-code for TCGA extraction
def extract_tcga_pgx_case_study(cohort="TCGA-COAD"):
    # 1. Get germline variants (if available via dbGaP)
    germline_variants = extract_germline_variants(cohort, genes=["DPYD", "TPMT", "UGT1A1"])
    
    # 2. Get treatment exposure (from clinical files)
    treatment_data = extract_treatment_exposure(cohort, drugs=["5-FU", "capecitabine"])
    
    # 3. Get toxicity outcomes (from clinical files)
    toxicity_data = extract_toxicity_outcomes(cohort, grade_threshold=3)
    
    # 4. Stratify by testing timing (simulate reactive vs pretreatment)
    # Note: TCGA doesn't have testing dates, so we'd need to simulate based on:
    # - Variant discovery method (germline panel vs tumor sequencing)
    # - Treatment start date vs sequencing date
    stratified = stratify_reactive_pretreatment(germline_variants, treatment_data)
    
    return stratified
```

**Status:** 🔴 CRITICAL - Need to determine if TCGA has germline PGx data

**Action Required:**
- **Ask Agent Jr:** Search TCGA documentation for germline PGx variant availability
- **Alternative:** Use TCGA somatic data as proxy (if germline not available)

---

### **7. Web Search for Case Studies** ❌ **NOT IMPLEMENTED**

**What We Need:**
- Find the source of the n=442 case study (Table 3 data)
- Find other published reactive vs pretreatment comparisons
- Find terminated trials with published genotype-toxicity data

**Search Strategy:**
1. **Google Scholar:** "reactive testing" + "pretreatment" + "DPYD" + "toxicity"
2. **PubMed:** "reactive pharmacogenomics" + "pretreatment screening" + "fluoropyrimidine"
3. **ClinicalTrials.gov:** Cross-reference terminated trials with PubMed publications

**Implementation Approach:**
```python
# Pseudo-code for web search
def find_reactive_pretreatment_case_studies():
    queries = [
        '"reactive testing" AND "pretreatment" AND DPYD AND toxicity',
        '"reactive pharmacogenomics" AND "pretreatment screening" AND fluoropyrimidine',
        'terminated AND toxicity AND DPYD AND "genotype"',
        'n=442 AND DPYD AND toxicity AND pretreatment',  # Specific to our case study
    ]
    
    results = []
    for query in queries:
        # Use web search tool (if available)
        web_results = web_search(query)
        # Or use PubMed/Google Scholar APIs
        pubmed_results = search_pubmed(query)
        results.extend(web_results)
    
    return results
```

**Status:** 🟡 **NEEDS WEB SEARCH TOOL** - Can ask another agent to perform web searches

**Action Required:**
- **Ask Agent Jr:** Perform web searches to find:
  1. Source of n=442 case study (Table 3)
  2. Other reactive vs pretreatment comparisons
  3. Terminated trials with published genotype-toxicity data

---

### **8. Full-Text PDF Extraction** ❌ **PARTIALLY IMPLEMENTED**

**What We Need:**
- Extract full tables from published papers (not just abstracts)
- Extract patient-level data (if published in supplements)
- Extract detailed toxicity breakdowns (reactive vs pretreatment groups)

**Current Status:**
- BioMed-MCP may support full-text extraction (if PDFs available)
- No dedicated PDF parsing script

**Implementation Approach:**
```python
# Pseudo-code for PDF extraction
def extract_tables_from_pdf(pmid_or_url):
    # 1. Get PDF (via PubMed Central or publisher)
    pdf_path = download_pdf(pmid_or_url)
    
    # 2. Extract tables (using tabula-py or camelot)
    tables = extract_tables_from_pdf(pdf_path)
    
    # 3. Parse reactive vs pretreatment data
    reactive_pretreatment_data = parse_reactive_pretreatment_table(tables)
    
    return reactive_pretreatment_data
```

**Status:** 🟡 **NEEDS PDF PARSING LIBRARY** - Can use existing tools (tabula-py, camelot)

**Action Required:**
- **Option A:** Use BioMed-MCP if it supports PDF extraction
- **Option B:** Implement PDF table extraction using tabula-py or camelot
- **Option C:** Ask Agent Jr to manually extract tables from identified papers

---

### **9. Direct Data Requests** ❌ **NOT AUTOMATED**

**What We Need:**
- Contact PIs of completed/terminated trials for patient-level data
- Request genotype-toxicity correlation data from published studies

**Current Status:**
- Scripts extract PI contact information from ClinicalTrials.gov
- No automated email template or request system

**Implementation Approach:**
```python
# Pseudo-code for data requests
def request_trial_data(nct_id):
    # 1. Get PI contact from ClinicalTrials.gov
    pi_info = get_pi_contact(nct_id)
    
    # 2. Generate email template
    email_template = generate_data_request_email(
        nct_id=nct_id,
        request_type="genotype-toxicity correlation",
        purpose="case study validation"
    )
    
    # 3. Send email (manual or automated)
    send_email(pi_info['email'], email_template)
    
    return email_template
```

**Status:** 🟡 **MANUAL PROCESS** - Can generate email templates, but sending requires human approval

**Action Required:**
- Generate email templates for data requests
- Prioritize trials with published results (higher likelihood of data sharing)

---

## 📊 **DATA EXTRACTION ROADMAP FOR CASE STUDIES**

### **Phase 1: Identify Case Study Sources** (Week 1)

**Tasks:**
1. ✅ Use `search_pubmed_pgx.py` to find reactive vs pretreatment comparisons
2. ✅ Use `search_clinicaltrials_pgx.py` to find terminated trials
3. 🔄 **ASK AGENT JR:** Web search for n=442 case study source
4. 🔄 **ASK AGENT JR:** Find other reactive vs pretreatment comparisons

**Deliverable:** List of 5-10 candidate case studies with:
- Source (PMID, NCT ID, or web link)
- Cohort size (N)
- Data availability (abstract only, full paper, patient-level)

---

### **Phase 2: Extract Published Data** (Week 2)

**Tasks:**
1. ✅ Use `extract_prevention_rates_from_pubmed.py` to extract aggregate stats
2. 🔄 **NEW:** Extract reactive vs pretreatment breakdowns from abstracts
3. 🔄 **NEW:** Extract full tables from PDFs (if available)
4. 🔄 **NEW:** Cross-reference ClinicalTrials.gov with PubMed publications

**Deliverable:** Extracted data for 3-5 case studies:
- Toxicity rates (reactive vs pretreatment)
- Odds ratios and confidence intervals
- Sample sizes and statistical significance

---

### **Phase 3: TCGA Data Extraction** (Week 3-4)

**Tasks:**
1. 🔄 **ASK AGENT JR:** Verify TCGA germline PGx variant availability
2. 🔄 **NEW:** Extract TCGA-COAD germline variants (DPYD, TPMT, UGT1A1)
3. 🔄 **NEW:** Extract TCGA treatment exposure data
4. 🔄 **NEW:** Extract TCGA toxicity outcomes
5. 🔄 **NEW:** Stratify by reactive vs pretreatment (simulate based on sequencing timing)

**Deliverable:** TCGA case study data:
- TCGA-COAD: Fluoropyrimidine + DPYD (n=627)
- TCGA-GBM: Temozolomide + MGMT (n=617)
- TCGA-SKCM: Immunotherapy + HLA (n=470)

---

### **Phase 4: Data Requests** (Week 5)

**Tasks:**
1. 🔄 **NEW:** Generate email templates for data requests
2. 🔄 **NEW:** Prioritize trials with published results
3. 🔄 **MANUAL:** Send data requests (requires human approval)

**Deliverable:** Data request emails sent to 5-10 PIs

---

## 🎯 **IMMEDIATE ACTION ITEMS**

### **For Agent Jr (Web Search):**

1. **Find n=442 Case Study Source:**
   - Search: "n=442" + "DPYD" + "toxicity" + "pretreatment" + "reactive"
   - Search: "Table 3" + "DPYD" + "Grade 3+ toxicity" + "hospitalization"
   - Search: "reactive testing" + "pretreatment" + "64% toxicity" + "31% toxicity"

2. **Find Other Reactive vs Pretreatment Comparisons:**
   - Search: "reactive pharmacogenomics" + "pretreatment screening" + "toxicity"
   - Search: "post-toxicity testing" + "pre-treatment testing" + "DPYD"
   - Search: "terminated trial" + "DPYD" + "toxicity" + "genotype"

3. **Find Terminated Trials with Published Data:**
   - Cross-reference ClinicalTrials.gov terminated trials with PubMed publications
   - Search: "[NCT Number]" + "terminated" + "toxicity" + "DPYD/TPMT"

### **For This Agent (Implementation):**

1. **Enhance PubMed Search:**
   - Add query for "reactive testing" vs "pretreatment testing"
   - Add query for "terminated trial" + "toxicity" + "PGx"

2. **Enhance Prevention Rate Extraction:**
   - Add extraction for reactive vs pretreatment group comparisons
   - Add extraction for odds ratios (OR) and confidence intervals

3. **Create TCGA Extraction Script:**
   - Check TCGA data availability (germline variants, treatment, toxicity)
   - Implement extraction if data is available

4. **Create PDF Table Extraction Script:**
   - Use tabula-py or camelot to extract tables from PDFs
   - Parse reactive vs pretreatment tables

---

## 📝 **SUMMARY**

### **✅ What We Have:**
- PubMed search (literature)
- ClinicalTrials.gov search (trials)
- Prevention rate extraction (aggregate stats)
- BioMed-MCP integration (advanced queries)

### **🔄 What We Need:**
- **Web search** (to find n=442 case study source) - ASK AGENT JR
- **TCGA data extraction** (germline variants, treatment, toxicity)
- **PDF table extraction** (full tables from papers)
- **Reactive vs pretreatment extraction** (enhance existing scripts)

### **🎯 Priority:**
1. **HIGH:** Find n=442 case study source (web search - Agent Jr)
2. **HIGH:** Extract reactive vs pretreatment data from published papers (enhance scripts)
3. **MEDIUM:** TCGA data extraction (if germline data available)
4. **LOW:** PDF table extraction (if needed for specific papers)

---

## 🔗 **RESOURCES**

- **Existing Scripts:** `oncology-coPilot/oncology-backend-minimal/scripts/data_acquisition/pgx/`
- **Case Study Document:** `publications/05-pgx-dosing-guidance/caseStudy.mdc`
- **Reactive vs Pretreatment Analysis:** `publications/05-pgx-dosing-guidance/reports/REACTIVE_VS_PRETREATMENT_ANALYSIS.md`
- **Data Requirements for Jr:** `publications/05-pgx-dosing-guidance/reports/JR_DATA_REQUIREMENTS.md`

---

**Next Steps:** 
1. Ask Agent Jr to perform web searches (see "IMMEDIATE ACTION ITEMS")
2. Enhance existing scripts to extract reactive vs pretreatment data
3. Verify TCGA germline PGx data availability
