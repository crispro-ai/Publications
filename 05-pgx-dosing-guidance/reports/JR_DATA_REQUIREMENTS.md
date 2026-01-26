# Data Requirements for Trial Failure Prevention Validation

**Task:** Find terminated clinical trials where Safety Gate could prevent failure  
**Agent:** Jr  
**Deadline:** ASAP  
**Status:** 🔄 **PENDING DATA COLLECTION**

---

## 🎯 **WHAT WE'RE LOOKING FOR**

### **Primary Target: Terminated Oncology Trials with Toxicity**

Find trials that meet **ALL** of these criteria:

1. ✅ **Status = "Terminated"** (early termination)
2. ✅ **Reason = "Adverse events" OR "Safety concerns" OR "Toxicity"**
3. ✅ **Drugs:** Fluoropyrimidines (5-FU, capecitabine) OR Thiopurines (mercaptopurine, azathioprine) OR Irinotecan
4. ✅ **Genetics:** DPYD, TPMT, or UGT1A1 variants implicated (mentioned in termination reason or publication)
5. ✅ **Published data:** Genotype-toxicity correlation available (at minimum: how many patients had toxicity, how many had variants)

---

## 📊 **DATA NEEDED (Priority Order)**

### **TIER 1: Critical (Must Have)**

#### **1. Trial Identifiers**
- **NCT Number** (ClinicalTrials.gov ID)
- **Trial Title**
- **Sponsor**
- **Termination Date**
- **Reason for Termination** (exact text from ClinicalTrials.gov)
- **ClinicalTrials.gov URL**

#### **2. Patient-Level Data (If Available)**
- **Total enrolled:** N = ?
- **Patients with severe toxicity (Grade 3-4):** n = ?
- **Patients with DPYD/TPMT/UGT1A1 variants:** n = ?
- **Overlap:** How many toxic patients had variants? (critical for sensitivity calculation)

**Example Format:**
```json
{
  "nct_id": "NCT01234567",
  "total_enrolled": 30,
  "severe_toxicity_cases": 6,
  "variant_carriers": 8,
  "toxic_cases_with_variant": 5,
  "toxic_cases_without_variant": 1
}
```

#### **3. Publication Data**
- **Publication PMID** (if available)
- **Publication Title**
- **Journal**
- **Genotype-toxicity table or figure** (screenshot or extracted data)
- **Key Finding:** "Trial terminated due to Grade 3-4 toxicity in X/Y patients. DPYD *2A carriers had Y% toxicity rate vs Z% in non-carriers."

---

### **TIER 2: Important (Nice to Have)**

#### **4. Genotype Details**
- **Specific variants detected:** DPYD *2A, *13, TPMT *3A, etc.
- **Variant frequencies:** How many patients per genotype?
- **Testing method:** Sanger, NGS, panel?

#### **5. Toxicity Details**
- **Toxicity type:** Diarrhea, neutropenia, myelosuppression, etc.
- **Severity:** Grade 3 vs Grade 4?
- **Onset:** How many cycles before toxicity appeared?

#### **6. Trial Design Details**
- **Phase:** Phase I, II, III?
- **Disease:** Cancer type
- **Treatment regimen:** Dose, schedule

---

### **TIER 3: Optional (If Available)**

#### **7. Control Groups**
- Did trial have a control arm without genetic testing?
- Were variants tested retrospectively after termination?

#### **8. Follow-Up Publications**
- Any post-hoc analyses showing genotype-toxicity correlation?
- Any case reports from the trial?

---

## 🔍 **SEARCH STRATEGY**

### **STEP 1: ClinicalTrials.gov Search**

**Search Queries:**
1. `terminated AND (5-fluorouracil OR capecitabine) AND (DPYD OR toxicity)`
2. `terminated AND (mercaptopurine OR azathioprine) AND (TPMT OR toxicity)`
3. `terminated AND irinotecan AND (UGT1A1 OR toxicity)`
4. `terminated AND (adverse events) AND oncology AND genetic`

**Filters:**
- Status: `Terminated`
- Study Type: `Interventional`
- Conditions: `Cancer` OR `Oncology`
- Study Results: `Has Results` (if available)

**Expected Output:**
- List of 5-10 candidate NCT numbers
- For each: Download full record, note termination reason

---

### **STEP 2: Publication Search**

**For each candidate NCT:**
1. Search PubMed: `NCT[All Fields] AND ("NCT01234567" OR "terminated" OR "toxicity")`
2. Search Google Scholar: `"[NCT Number]" terminated toxicity`
3. Check trial's "References" section on ClinicalTrials.gov

**What to Extract:**
- Full publication text (PDF if available)
- Genotype-toxicity correlation tables
- Summary statistics: "X of Y patients with DPYD *2A had severe toxicity"

---

### **STEP 3: Data Extraction**

**For each trial with publication data:**

**Extract Table/Figure:**
```
| Genotype | Total N | Toxicity Cases | Toxicity Rate |
|----------|---------|----------------|---------------|
| DPYD *2A | 5       | 4              | 80%           |
| DPYD WT  | 25      | 2              | 8%            |
```

**Calculate Safety Gate Performance:**
- **True Positives:** Toxic cases WITH variant (Safety Gate would flag)
- **False Negatives:** Toxic cases WITHOUT variant (Safety Gate would miss)
- **Sensitivity:** TP / (TP + FN) = X%

---

## 📋 **DELIVERABLE FORMAT**

**Create JSON file:** `terminated_trials_candidates.json`

```json
{
  "trials": [
    {
      "nct_id": "NCT01234567",
      "title": "Phase II Study of Capecitabine in Colorectal Cancer",
      "sponsor": "University Hospital",
      "termination_date": "2018-03-15",
      "termination_reason": "Terminated early due to unacceptable rate of Grade 3-4 diarrhea (6/30 patients, 20%)",
      "ct_gov_url": "https://clinicaltrials.gov/study/NCT01234567",
      
      "drugs": ["capecitabine"],
      "disease": "Colorectal Cancer",
      "phase": "Phase II",
      
      "enrollment": {
        "total": 30,
        "severe_toxicity": 6,
        "terminated_early": true
      },
      
      "genotype_data": {
        "available": true,
        "tested_gene": "DPYD",
        "variants_detected": ["*2A", "*13"],
        "carriers_total": 8,
        "toxic_with_variant": 5,
        "toxic_without_variant": 1,
        "sensitivity_estimate": "5/6 = 83%"
      },
      
      "publication": {
        "pmid": "12345678",
        "title": "Early Termination Due to DPYD Deficiency in Capecitabine Trial",
        "journal": "Journal of Clinical Oncology",
        "year": 2018,
        "url": "https://pubmed.ncbi.nlm.nih.gov/12345678",
        "has_genotype_table": true,
        "extracted_table": "..."
      },
      
      "safety_gate_applicable": true,
      "notes": "Good candidate - DPYD variants clearly implicated, genotype-toxicity correlation published"
    }
  ],
  
  "search_metadata": {
    "search_date": "2025-01-13",
    "searches_performed": [
      "ClinicalTrials.gov: terminated + 5-FU + DPYD",
      "PubMed: NCT01234567",
      "Google Scholar: '[NCT]' terminated toxicity"
    ],
    "total_candidates_found": 5,
    "with_publications": 2,
    "with_genotype_data": 2
  }
}
```

---

## ✅ **SUCCESS CRITERIA**

**Minimum Success:**
- ✅ Find **at least 1 trial** that:
  - Terminated due to toxicity
  - Has published genotype-toxicity correlation
  - Shows Safety Gate would flag ≥70% of toxic cases

**Optimal Success:**
- ✅ Find **2-3 trials** with different drug-variant combinations:
  - One DPYD + fluoropyrimidine trial
  - One TPMT + thiopurine trial (if available)

**Validation Goal:**
After Jr provides data, we'll:
1. Apply Safety Gate algorithm to each trial's patient genotypes
2. Calculate: "Would Safety Gate have flagged the toxic patients?"
3. Calculate: "Could trial have continued if flagged patients were excluded/dose-adjusted?"

**Expected Output Statement:**
> "Trial NCT# was terminated due to Grade 3-4 toxicity in 6/30 patients. Retrospective Safety Gate screening flagged 5/6 cases (83% sensitivity). If screening had been used, trial would have met safety threshold and continued to completion."

---

## 🚨 **POTENTIAL CHALLENGES**

### **Challenge 1: Genotype Data Not Always Published**
- **Solution:** Look for post-hoc analyses, case reports, conference abstracts
- **Fallback:** If no genotype data → Mark as "inapplicable" but keep in list

### **Challenge 2: Trials May Not Test Genetics Until After Termination**
- **Solution:** This is OK! Retrospective genetic testing still validates Safety Gate
- **Value:** Shows "if genetics were tested upfront, could have prevented failure"

### **Challenge 3: Toxicity May Not Be Solely Due to PGx Variants**
- **Solution:** This is expected. Safety Gate won't catch all toxicities
- **Goal:** Show Safety Gate flags MOST toxic cases (≥70% sensitivity is acceptable)

---

## 📝 **NOTES FOR JR**

1. **Focus on oncology trials** - Safety Gate is designed for cancer drugs
2. **Prioritize trials with published data** - Genotype-toxicity correlation is critical
3. **Don't worry about perfect data** - Aggregate statistics (X of Y patients) is sufficient
4. **Include all candidate trials** - Even if data is incomplete, document for future follow-up
5. **Extract exact numbers** - "6/30 patients" is better than "20% had toxicity"

---

## 🔗 **RESOURCES**

**ClinicalTrials.gov:**
- Advanced Search: https://clinicaltrials.gov/ct2/search/advanced
- Search Tips: Status="Terminated", Conditions="Cancer"

**PubMed:**
- Search Format: `(NCT[All Fields] AND "NCT01234567") OR (terminated AND toxicity AND DPYD)`

**CPIC Guidelines:**
- DPYD: https://cpicpgx.org/genes-drugs/
- TPMT: https://cpicpgx.org/genes-drugs/
- (These list known variant-drug interactions that cause toxicity)

---

**Questions?** Contact Zo for clarification on Safety Gate algorithm or validation approach.
