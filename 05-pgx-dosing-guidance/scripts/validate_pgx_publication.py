import json
import time
from collections import Counter

CASE_PATH = 'publications/05-pgx-dosing-guidance/data/extraction_all_genes_curated.json'
CPIC_PATH = 'publications/05-pgx-dosing-guidance/reports/cpic_concordance_report.json'
CLINVAR_PATH = 'publications/05-pgx-dosing-guidance/reports/clinvar_bridge_coverage.json'

OUT_JSON = 'publications/05-pgx-dosing-guidance/reports/publication_receipt_v2.json'
OUT_MD = 'publications/05-pgx-dosing-guidance/reports/PUBLICATION_RECEIPT_V2.md'


def main():
    cases_doc = json.load(open(CASE_PATH))
    cpic = json.load(open(CPIC_PATH))
    clinvar = json.load(open(CLINVAR_PATH))

    cases = cases_doc['cases']

    # Coverage
    total_cases = len(cases)
    by_gene = Counter(c.get('gene') for c in cases)
    by_source = Counter(c.get('source') for c in cases)

    drug_present = [c for c in cases if (c.get('drug') or '').strip()]

    # CPIC
    cpic_matched = [r for r in cpic['concordance_results'] if r.get('cpic_recommendation') is not None]
    non_cpic = [r for r in cpic['concordance_results'] if r.get('cpic_recommendation') is None]
    concordant = [r for r in cpic_matched if r.get('concordant') is True]

    # Clinical evaluable for toxicity = drug present + labeled toxicity
    clinically_evaluable = [c for c in cases if (c.get('drug') or '').strip() and c.get('toxicity_occurred') in (True, False)]
    tox_pos = [c for c in clinically_evaluable if c.get('toxicity_occurred') is True]
    tox_neg = [c for c in clinically_evaluable if c.get('toxicity_occurred') is False]

    tp = sum(1 for c in tox_pos if (c.get('our_prediction') or {}).get('would_have_flagged'))
    fn = len(tox_pos) - tp
    fp = sum(1 for c in tox_neg if (c.get('our_prediction') or {}).get('would_have_flagged'))
    tn = len(tox_neg) - fp

    sensitivity = tp / (tp + fn) if (tp + fn) else None
    specificity = tn / (tn + fp) if (tn + fp) else None

    out = {
        'generated_at': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
        'definitions': {
            'cpic_coverage': 'cases_with_cpic_match / total_cases in this dataset',
            'cpic_concordance': 'concordant recommendations among cases with CPIC match',
            'toxicity_sensitivity': 'flagged among toxicity-positive cases WITH drug + outcome labels',
            'toxicity_specificity': 'requires toxicity-negative cases WITH drug + outcome labels (often unavailable in this dataset)',
            'clinvar_bridge_coverage': 'ability to retrieve ClinVar evidence for non-CPIC variants (NOT dosing accuracy)',
        },
        'cohort': {
            'total_cases': total_cases,
            'by_gene': dict(by_gene),
            'by_source': dict(by_source),
            'drug_present_n': len(drug_present),
        },
        'cpic': {
            'cases_with_cpic_match': len(cpic_matched),
            'cpic_coverage_rate': (len(cpic_matched) / total_cases) if total_cases else None,
            'cpic_concordant_in_matched': len(concordant),
            'cpic_concordance_rate_in_matched': (len(concordant) / len(cpic_matched)) if cpic_matched else None,
        },
        'toxicity_validation': {
            'clinically_evaluable_n': len(clinically_evaluable),
            'toxicity_positive_n': len(tox_pos),
            'toxicity_negative_n': len(tox_neg),
            'tp': tp,
            'fn': fn,
            'tn': tn,
            'fp': fp,
            'sensitivity': sensitivity,
            'specificity': specificity,
            'missed_cases': [c['case_id'] for c in tox_pos if not (c.get('our_prediction') or {}).get('would_have_flagged')],
        },
        'clinvar_bridge': {
            'non_cpic_cases': clinvar.get('non_cpic_cases'),
            'fetched_200': clinvar.get('fetched_200'),
            'heuristic_labeled': clinvar.get('heuristic_labeled'),
            'label_distribution': clinvar.get('label_distribution'),
        }
    }

    json.dump(out, open(OUT_JSON, 'w'), indent=2)

    with open(OUT_MD, 'w') as f:
        f.write('# Publication Receipt (v2)\n\n')
        f.write(f"Generated: {out['generated_at']}\n\n")
        f.write('## Cohort\n')
        f.write(f"- Total cases: {out['cohort']['total_cases']}\n")
        f.write(f"- Drug present: {out['cohort']['drug_present_n']}\n")
        f.write(f"- By gene: {out['cohort']['by_gene']}\n")
        f.write(f"- By source: {out['cohort']['by_source']}\n\n")

        f.write('## CPIC\n')
        f.write(f"- CPIC matched: {out['cpic']['cases_with_cpic_match']}\n")
        f.write(f"- CPIC coverage rate: {out['cpic']['cpic_coverage_rate']:.3f}\n")
        f.write(f"- CPIC concordance in matched: {out['cpic']['cpic_concordance_rate_in_matched']:.3f}\n\n")

        f.write('## Toxicity validation (clinically evaluable subset only)\n')
        tv = out['toxicity_validation']
        f.write(f"- Clinically evaluable N: {tv['clinically_evaluable_n']}\n")
        f.write(f"- Toxicity positives: {tv['toxicity_positive_n']}\n")
        f.write(f"- Toxicity negatives: {tv['toxicity_negative_n']}\n")
        f.write(f"- Sensitivity: {tv['tp']}/{tv['tp']+tv['fn']} = {tv['sensitivity']:.3f}\n")
        if tv["specificity"] is None:
            f.write("- Specificity: N/A (no clinically-labeled toxicity-negative cases in cohort)\n")
        else:
            f.write(f"- Specificity: {tv['tn']}/{tv['tn']+tv['fp']} = {tv['specificity']:.3f}\n")
        f.write(f"- Missed toxicity case_ids: {tv['missed_cases']}\n\n")

        f.write('## ClinVar bridge (coverage)\n')
        cb = out['clinvar_bridge']
        f.write(f"- Non-CPIC cases: {cb['non_cpic_cases']}\n")
        f.write(f"- Fetched 200: {cb['fetched_200']}\n")
        f.write(f"- Heuristic labeled: {cb['heuristic_labeled']}\n")
        f.write(f"- Label distribution: {cb['label_distribution']}\n")


if __name__ == '__main__':
    main()
