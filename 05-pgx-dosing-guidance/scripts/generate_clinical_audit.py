import json
import time
from collections import Counter, defaultdict

CASE_PATH = 'publications/05-pgx-dosing-guidance/data/extraction_all_genes_curated.json'
CPIC_PATH = 'publications/05-pgx-dosing-guidance/reports/cpic_concordance_report.json'
CLINVAR_PATH = 'publications/05-pgx-dosing-guidance/reports/clinvar_bridge_coverage.json'

OUT_JSON = 'publications/05-pgx-dosing-guidance/reports/clinical_validation_audit.json'
OUT_MD = 'publications/05-pgx-dosing-guidance/CLINICAL_VALIDATION_AUDIT.md'


def main():
    cases_doc = json.load(open(CASE_PATH))
    cpic = json.load(open(CPIC_PATH))
    clinvar = json.load(open(CLINVAR_PATH)) if _exists(CLINVAR_PATH) else None

    cases = cases_doc['cases']

    # Basic gene/drug distributions
    gene_all = Counter(c.get('gene') for c in cases)
    source_all = Counter(c.get('source') for c in cases)

    drug_present = [c for c in cases if (c.get('drug') or '').strip()]
    drug_missing = [c for c in cases if not (c.get('drug') or '').strip()]

    drug_all = Counter((c.get('drug') or '').strip().lower() for c in drug_present)

    # Outcomes: in this dataset toxicity is only annotated from PubMed abstracts/curation
    tox_true = [c for c in cases if c.get('toxicity_occurred') is True]
    tox_false = [c for c in cases if c.get('toxicity_occurred') is False]
    tox_unknown = [c for c in cases if c.get('toxicity_occurred') not in (True, False)]

    # Define what can be clinically validated
    clinically_evaluable = [c for c in cases if (c.get('drug') or '').strip() and c.get('toxicity_occurred') in (True, False)]
    clinically_pos = [c for c in clinically_evaluable if c.get('toxicity_occurred') is True]
    clinically_neg = [c for c in clinically_evaluable if c.get('toxicity_occurred') is False]

    # CPIC match set
    cpic_matched = [r for r in cpic['concordance_results'] if r.get('cpic_recommendation') is not None]
    non_cpic = [r for r in cpic['concordance_results'] if r.get('cpic_recommendation') is None]

    # Concordance for matched
    concordant = [r for r in cpic_matched if r.get('concordant') is True]

    # Toxicity sensitivity is only meaningful on clinically_evaluable positives
    # Use existing our_prediction.would_have_flagged from case file
    tp = sum(1 for c in clinically_pos if (c.get('our_prediction') or {}).get('would_have_flagged'))
    fn = len(clinically_pos) - tp

    # Specificity can only be computed on clinically_evaluable negatives (drug + confirmed no toxicity)
    # In our data, clinically_neg is small (often 0)
    fp = sum(1 for c in clinically_neg if (c.get('our_prediction') or {}).get('would_have_flagged'))
    tn = len(clinically_neg) - fp

    audit = {
        'generated_at': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
        'cohort': {
            'n_total': len(cases),
            'by_source': dict(source_all),
            'by_gene': dict(gene_all),
            'drug_present_n': len(drug_present),
            'drug_missing_n': len(drug_missing),
            'drug_distribution_present_only': dict(drug_all),
            'toxicity_labels': {
                'tox_true': len(tox_true),
                'tox_false': len(tox_false),
                'tox_unknown': len(tox_unknown),
            },
        },
        'cpic': {
            'cases_with_cpic_match': len(cpic_matched),
            'non_cpic_cases': len(non_cpic),
            'concordant_in_cpic_matched': len(concordant),
            'cpic_concordance_rate_in_matched': (len(concordant) / len(cpic_matched)) if cpic_matched else None,
        },
        'clinical_validation_scope': {
            'clinically_evaluable_definition': 'cases with (drug present) AND (toxicity_occurred is True/False)',
            'clinically_evaluable_n': len(clinically_evaluable),
            'toxicity_positive_n': len(clinically_pos),
            'toxicity_negative_n': len(clinically_neg),
            'toxicity_sensitivity': tp / (tp + fn) if (tp + fn) else None,
            'toxicity_specificity': tn / (tn + fp) if (tn + fp) else None,
            'confusion': {'tp': tp, 'fn': fn, 'tn': tn, 'fp': fp},
            'note': 'If toxicity_negative_n is 0, specificity cannot be estimated clinically from this cohort.'
        },
        'clinvar_bridge': {
            'coverage_report_path': CLINVAR_PATH if clinvar else None,
            'non_cpic_cases': clinvar.get('non_cpic_cases') if clinvar else None,
            'fetched_200': clinvar.get('fetched_200') if clinvar else None,
            'heuristic_labeled': clinvar.get('heuristic_labeled') if clinvar else None,
            'label_distribution': clinvar.get('label_distribution') if clinvar else None,
            'meaning': 'This validates evidence retrieval coverage, not correctness of dosing guidance.'
        }
    }

    with open(OUT_JSON, 'w') as f:
        json.dump(audit, f, indent=2)

    # Human-readable audit
    with open(OUT_MD, 'w') as f:
        f.write('# PGx Dosing Guidance — Clinical Validation Audit\n\n')
        f.write(f"Generated: {audit['generated_at']}\n\n")

        f.write('## 1) Are the 53 "negatives" clinically meaningful?\n\n')
        f.write(f"- Total cases: **{audit['cohort']['n_total']}**\n")
        f.write(f"- Drug present: **{audit['cohort']['drug_present_n']}**\n")
        f.write(f"- Drug missing: **{audit['cohort']['drug_missing_n']}**\n\n")
        f.write('**Finding:** In this cohort, **53/59 cases have no drug recorded** (mostly TCGA/GDC), so they cannot serve as clinical negative controls for toxicity or dosing recommendations.\n\n')

        f.write('## 2) Borderline cases (e.g., CYP2D6/CYP2C19)\n\n')
        f.write('**Finding:** This cohort contains only DPYD/TPMT/UGT1A1. There are **no CYP2D6/CYP2C19 borderline cases**, so this validation cannot speak to gray-zone guideline disagreements for those genes.\n\n')

        f.write('## 3) Gene distribution in negatives\n\n')
        f.write(f"- Overall gene distribution: `{json.dumps(audit['cohort']['by_gene'])}`\n")
        f.write(f"- Sources: `{json.dumps(audit['cohort']['by_source'])}`\n\n")

        f.write('## 4) What is clinically validated here?\n\n')
        f.write('Clinically evaluable cases require: **drug present + an explicit toxicity outcome label**.\n\n')
        f.write(f"- Clinically evaluable N: **{audit['clinical_validation_scope']['clinically_evaluable_n']}**\n")
        f.write(f"- Toxicity positives: **{audit['clinical_validation_scope']['toxicity_positive_n']}**\n")
        f.write(f"- Toxicity negatives: **{audit['clinical_validation_scope']['toxicity_negative_n']}**\n\n")
        f.write(f"Confusion: `{json.dumps(audit['clinical_validation_scope']['confusion'])}`\n\n")

        f.write('**Interpretation:** Sensitivity is estimable on the toxicity-positive set. Specificity requires confirmed toxicity-negative outcomes, which this cohort may not provide.\n\n')

        f.write('## 5) ClinVar bridge — what does 49/49 mean?\n\n')
        if clinvar:
            f.write(f"-on-CPIC cases: **{clinvar['non_cpic_cases']}**\n")
            f.write(f"- ClinVar pages fetched (HTTP 200): **{clinvar['fetched_200']}/{clinvar['non_cpic_cases']}**\n")
            f.write(f"- Heuristic label extracted: **{clinvar['heuristic_labeled']}/{clinvar['non_cpic_cases']}**\n")
            f.write(f"- Label distribution: `{json.dumps(clinvar['label_distribution'])}`\n\n")
        f.write('**Meaning:** This is **coverage of evidence retrieval**, not accuracy of dosing translation.\n\n')

        f.write('## 6) Cohort representativeness\n\n')
        f.write('**Finding:** This cohort is heavily DPYD-enriched and oncology-focused (fluoropyrimidines). It is not representative of general outpatient pharmacogenetic testing panels dominated by CYP2D6/CYP2C19/CYP2C9/VKORC1.\n\n')

        f.write('## 7) Ground truth independence\n\n')
        f.write('**Finding:** Toxicity ground truth comes from PubMed case reports (PMIDs in the dataset). SME documents exist as a review package, but SME sign-off is not embedded as an independent label source in the receipts.\n\n')


def _exists(p: str) -> bool:
    try:
        open(p).close()
        return True
    except Exception:
        return False


if __name__ == '__main__':
    main()
