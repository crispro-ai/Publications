# Agent Jr - Web Search Tasks for Case Study Data

**Purpose:** Specific web search tasks for Agent Jr to find case study data  
**Date:** January 13, 2025  
**Priority:** 🔴 **HIGH - BLOCKING CASE STUDY GENERATION**

---

## 🎯 **PRIMARY TASK: Find n=442 Case Study Source**

We have data from "Table 3" showing:
- **Wild-type:** 415 patients, 30% toxicity, 13% hospitalization
- **Pretreatment:** 16 patients, 31% toxicity, 25% hospitalization
- **Reactive:** 11 patients, 64% toxicity, 64% hospitalization
- **Total:** 442 patients

**We need:**
1. **Source paper:** What paper/publication contains this Table 3?
2. **NCT Number:** Is this from a clinical trial? (If yes, what's the NCT ID?)
3. **Full citation:** Author, journal, year, DOI/PMID

**Search Queries for Agent Jr:**

```
Query 1: "n=442" AND "DPYD" AND "toxicity" AND "pretreatment" AND "reactive"
Query 2: "Table 3" AND "DPYD" AND "Grade 3+ toxicity" AND "hospitalization" AND "442 patients"
Query 3: "reactive testing" AND "pretreatment" AND "64% toxicity" AND "31% toxicity" AND "DPYD"
Query 4: "442 patients" AND "DPYD" AND "fluoropyrimidine" AND "toxicity" AND "pretreatment screening"
Query 5: "reactive pharmacogenomics" AND "pretreatment" AND "64%" AND "31%" AND "hospitalization"
```

**Expected Results:**
- Paper title, authors, journal
- PMID or DOI
- Link to full paper (if open access)
- NCT number (if applicable)

---

## 🔍 **SECONDARY TASK: Find Other Reactive vs Pretreatment Comparisons**

**Goal:** Find additional published studies comparing reactive vs pretreatment PGx testing

**Search Queries:**

```
Query 1: "reactive pharmacogenomics" AND "pretreatment screening" AND "toxicity" AND "DPYD"
Query 2: "post-toxicity testing" AND "pre-treatment testing" AND "DPYD" AND "fluoropyrimidine"
Query 3: "reactive testing" AND "pretreatment" AND "TPMT" AND "thiopurine" AND "toxicity"
Query 4: "reactive testing" AND "pretreatment" AND "UGT1A1" AND "irinotecan" AND "toxicity"
Query 5: "reactive" AND "pretreatment" AND "pharmacogenomics" AND "cancer" AND "toxicity comparison"
```

**What to Extract:**
- Paper title, authors, journal, year
- Cohort size (N)
- Toxicity rates (reactive vs pretreatment)
- Odds ratios and confidence intervals
- Statistical significance (p-values)

---

## 🚨 **TERTIARY TASK: Find Terminated Trials with Published Data**

**Goal:** Find trials that were terminated due to toxicity, with published genotype-toxicity correlation data

**Search Strategy:**

1. **Start with ClinicalTrials.gov terminated trials:**
   - Search: Status="TERMINATED" + Reason="Adverse events" + Intervention="5-FU" OR "capecitabine"
   - Extract NCT numbers

2. **Cross-reference with PubMed:**
   - For each NCT number, search: `"[NCT Number]" AND "terminated" AND "toxicity"`
   - Look for published papers from these trials

3. **Specific Search Queries:**

```
Query 1: "terminated" AND "clinical trial" AND "DPYD" AND "toxicity" AND "genotype"
Query 2: "early termination" AND "adverse events" AND "DPYD" AND "fluoropyrimidine"
Query 3: "trial termination" AND "toxicity" AND "pharmacogenomics" AND "DPYD"
Query 4: "[NCT Number from ClinicalTrials.gov]" AND "terminated" AND "toxicity" AND "publication"
```

**What to Extract:**
- NCT number
- Trial title
- Termination reason (exact text)
- Published paper (if available)
- Genotype-toxicity correlation data (if published)

---

## 📋 **DELIVERABLE FORMAT**

**For Each Found Case Study, Provide:**

```json
{
  "case_study_id": "CS001",
  "source": {
    "type": "published_paper" | "clinical_trial" | "web_source",
    "title": "Paper/Trial Title",
    "authors": ["Author 1", "Author 2"],
    "journal": "Journal Name",
    "year": 2024,
    "pmid": "12345678",
    "doi": "10.xxxx/xxxx",
    "nct_id": "NCT01234567",
    "url": "https://..."
  },
  "cohort": {
    "n_total": 442,
    "n_wild_type": 415,
    "n_pretreatment": 16,
    "n_reactive": 11,
    "cancer_type": "Colorectal Cancer",
    "drug": "Fluoropyrimidine (5-FU/capecitabine)",
    "gene": "DPYD"
  },
  "outcomes": {
    "wild_type": {
      "grade3_toxicity_n": 126,
      "grade3_toxicity_pct": 30.4,
      "hospitalization_n": 53,
      "hospitalization_pct": 12.8
    },
    "pretreatment": {
      "grade3_toxicity_n": 5,
      "grade3_toxicity_pct": 31.3,
      "hospitalization_n": 4,
      "hospitalization_pct": 25.0
    },
    "reactive": {
      "grade3_toxicity_n": 7,
      "grade3_toxicity_pct": 63.6,
      "hospitalization_n": 7,
      "hospitalization_pct": 63.6
    }
  },
  "statistics": {
    "reactive_vs_wt_odds_ratio": 9.59,
    "reactive_vs_wt_ci": "2.70-34.04",
    "reactive_vs_wt_p_value": 0.001,
    "pretreatment_vs_wt_odds_ratio": 2.02,
    "pretreatment_vs_wt_ci": "0.62-6.56",
    "pretreatment_vs_wt_p_value": 0.167
  },
  "data_availability": {
    "abstract_only": false,
    "full_paper_available": true,
    "patient_level_data": false,
    "supplementary_tables": true
  }
}
```

---

## ✅ **SUCCESS CRITERIA**

**Minimum Success:**
- ✅ Find source of n=442 case study (paper citation + link)
- Find 1-2 additional reactive vs pretreatment comparisons

**Optimal Success:**
- ✅ Find source of n=442 case study with full paper access
- ✅ Find 3-5 additional reactive vs pretreatment comparisons
- ✅ Find 1-2 terminated trials with published genotype-toxicity data

---

## 🔗 **RESOURCES**

- **Full Audit Document:** `publications/05-pgx-dosing-guidance/reports/DATA_EXTRACTION_AUDIT.md`
- **Case Study Document:** `publications/05-pgx-dosing-guidance/caseStudy.mdc`
- **Reactive vs Pretreatment Analysis:** `publications/05-pgx-dosing-guidance/reports/REACTIVE_VS_PRETREATMENT_ANALYSIS.md`

---

## 📝 **NOTES FOR AGENT JR**

1. **Focus on oncology/cancer trials** - Safety Gate is for cancer drugs
2. **Prioritize papers with full tables** - We need exact numbers, not just percentages
3. **Check for open access papers** - Easier to extract data from
4. **Look for supplementary materials** - Often contain detailed tables
5. **If you find a paper but can't access it** - Provide citation and we can request access

---

**Status:** 🔴 **PENDING - BLOCKING CASE STUDY GENERATION**  
**Priority:** Find n=442 case study source is CRITICAL for manuscript integration
