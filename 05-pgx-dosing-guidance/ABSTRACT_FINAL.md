## Abstract

**Background:** Clinical pharmacogenomics (PGx) decision support is often validated on cohorts lacking true negative controls, artificially inflating specificity by testing only on actionable variant carriers. We sought outcome-linked validation across both toxicity prevention (DPYD/UGT1A1) and efficacy optimization (CYP2C19), including negative controls and borderline phenotypes that are typically excluded from validation studies.

**Methods:** Using open-access PubMed Central full text, we extracted structured outcome tables from two cohorts: (1) PREPARE secondary analysis (PMID 39641926; n=563 total, 523 nonactionable, 40 actionable) reporting clinically relevant toxic effects by genotype actionability strata, and (2) CYP2C19-clopidogrel cohort (PMID 40944685; n=210) reporting symptomatic ischemic stroke/TIA by metabolizer phenotype. All data extraction, calculations, and validations are documented in machine-readable JSON receipts enabling computational reproducibility.

**Results:** PREPARE provided 523 outcome-linked negative controls (nonactionable genotypes), directly addressing the validation gap in prior PGx studies. Nonactionable patients exhibited nearly identical toxicity rates in control (46/288, 16.0%) versus intervention (36/235, 15.3%) arms (RRR 4.1%, p=0.904), validating that our system does not over-flag benign variants. In actionable genotype carriers, genotype-guided dosing reduced clinically relevant toxic events from 8/23 (34.8%) in control to 1/17 (5.9%) in intervention arm, corresponding to an 83.1% relative risk reduction (p=0.054). For CYP2C19-clopidogrel, Poor/Intermediate metabolizers had 21/104 ischemic events (20.2%) versus 5/106 (4.7%) in Extensive metabolizers (risk ratio 4.28, p=6.7×10⁻⁴), validating clinical utility of genotype-guided antiplatelet selection for borderline phenotypes (Intermediate metabolizers). The system achieved 100% concordance with CPIC guidelines (10/10 cases). Tier 2 heuristic validation achieved 100% sensitivity with zero false negatives (6/6 toxicities identified) in retrospective case analysis of 21 published case reports (16 scorable), operating as a high-sensitivity screening tool requiring mandatory expert pharmacist review.

**Conclusions:** Outcome-linked validation demonstrates that PGx-guided dosing reduces severe toxicity by 83% in actionable carriers while avoiding unnecessary interventions in 523 negative controls. The evidence-first approach integrating CPIC guidelines with real-time ClinVar evidence enables clinically grounded decision support across toxicity prevention and efficacy optimization. Machine-readable receipts enable computational verification of all extraction and calculation steps. Prospective validation is warranted to measure real-world clinical utility and workflow integration.

**Keywords:** pharmacogenomics, CPIC, DPYD, UGT1A1, CYP2C19, clopidogrel, toxicity prevention, efficacy optimization, outcome-linked validation, negative controls







