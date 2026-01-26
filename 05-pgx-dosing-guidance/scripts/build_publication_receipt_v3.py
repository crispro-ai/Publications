import json
import time
from pathlib import Path

BASE = Path('publications/05-pgx-dosing-guidance')
PREP = BASE / 'reports' / 'prepare_outcome_validation.json'
CYP = BASE / 'reports' / 'cyp2c19_clopidogrel_efficacy_validation.json'
OUT = BASE / 'reports' / 'publication_receipt_v3.json'


def main():
    prep = json.loads(PREP.read_text())
    cyp = json.loads(CYP.read_text())

    out = {
        'generated_at': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
        'modules': {
            'prepare': {
                'pmid': prep['source']['pmid'],
                'n_total': prep['cohort']['total_patients'],
                'n_actionable': prep['cohort']['actionable_carriers_total'],
                'n_nonactionable': prep['cohort']['nonactionable_total'],
                'actionability_sensitivity': prep['classification_validation']['sensitivity'],
                'actionability_specificity': prep['classification_validation']['specificity'],
                'carrier_rrr': prep['toxicity_outcomes']['actionable_carriers']['rrr'],
                'carrier_control_rate': prep['toxicity_outcomes']['actionable_carriers']['control']['rate'],
                'carrier_intervention_rate': prep['toxicity_outcomes']['actionable_carriers']['intervention']['rate'],
                'carrier_fisher_two_sided_p': prep['toxicity_outcomes']['actionable_carriers']['fisher_two_sided_p'],
                'note': prep['classification_validation']['interpretation'],
            },
            'cyp2c19': {
                'pmid': cyp['source']['pmid'],
                'endpoint': cyp['endpoint'],
                'em_rate': cyp['counts']['extensive_metabolizer']['rate'],
                'pmim_rate': cyp['counts']['poor_or_intermediate']['rate'],
                'risk_ratio': cyp['effect']['risk_ratio_pmim_vs_em'],
                'fisher_two_sided_p': cyp['effect']['fisher_two_sided_p'],
                'reported_multivariate_hr': cyp['effect']['reported_multivariate_hr'],
                'system_examples': cyp['system_recommendations_examples'],
            }
        }
    }

    OUT.write_text(json.dumps(out, indent=2))


if __name__ == '__main__':
    main()
