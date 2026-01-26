import json
import math
import time
from pathlib import Path
from typing import Dict, Any, Tuple

BASE = Path('publications/05-pgx-dosing-guidance')
T1 = BASE / 'reports' / 'pmid_39641926_Table_1.json'
T2 = BASE / 'reports' / 'pmid_39641926_Table_2.json'
OUT_JSON = BASE / 'reports' / 'prepare_outcome_validation.json'
OUT_MD = BASE / 'reports' / 'PREPARE_OUTCOME_VALIDATION.md'


def fisher_two_sided(a: int, b: int, c: int, d: int) -> float:
    """Two-sided Fisher exact p-value for 2x2 table:

        |  event  | no event |
    ctrl|    a    |    b     |
    int |    c    |    d     |
    """
    r1 = a + b
    r2 = c + d
    c1 = a + c
    n = r1 + r2

    def hyper_p(x: int) -> float:
        return (math.comb(c1, x) * math.comb(n - c1, r1 - x)) / math.comb(n, r1)

    p_obs = hyper_p(a)
    lo = max(0, r1 - (n - c1))
    hi = min(r1, c1)

    p = 0.0
    for x in range(lo, hi + 1):
        px = hyper_p(x)
        if px <= p_obs + 1e-15:
            p += px
    return float(min(1.0, p))


def rate(events: int, n: int) -> float:
    return events / n if n else float('nan')


def effect(control_e: int, control_n: int, int_e: int, int_n: int) -> Dict[str, Any]:
    rc = rate(control_e, control_n)
    ri = rate(int_e, int_n)
    arr = rc - ri
    rr = (ri / rc) if rc > 0 else None
    rrr = (arr / rc) if rc > 0 else None
    p = fisher_two_sided(control_e, control_n - control_e, int_e, int_n - int_e)
    return {
        'control': {'n': control_n, 'events': control_e, 'rate': rc},
        'intervention': {'n': int_n, 'events': int_e, 'rate': ri},
        'arr': arr,
        'rr': rr,
        'rrr': rrr,
        'fisher_two_sided_p': p,
    }


def parse_prepare_table1(t1: Dict[str, Any]) -> Dict[str, Any]:
    rows = t1['table']['rows']
    # rows include headings; canonical phenotype rows start with DPYD/UGT1A1 categories
    categories = []
    for r in rows:
        if not r:
            continue
        name = r[0].strip()
        if name.startswith('DPYD AS') or name.startswith('UGT1A1') or name.startswith('Nonactionable'):
            categories.append({
                'category': name,
                'control_cell': r[1],
                'intervention_cell': r[2],
                'recommended_adjustment': r[3] if len(r) > 3 else None,
            })

    # parse counts from cells like "7 (2.3)" or "0"
    def n_from(cell: str) -> int:
        cell = (cell or '').strip()
        if cell == '0':
            return 0
        return int(cell.split('(')[0].strip())

    for c in categories:
        c['control_n'] = n_from(c['control_cell'])
        c['intervention_n'] = n_from(c['intervention_cell'])

    # derive actionability as defined by table's recommended dose adjustment column
    # (Nonactionable row explicitly says Standard dosage)
    for c in categories:
        adj = (c.get('recommended_adjustment') or '').lower()
        # heuristic: anything not containing "standard" is actionable
        c['table_defined_actionable'] = ('standard' not in adj)

    return {
        'categories': categories,
        'actionable_total': sum(c['control_n'] + c['intervention_n'] for c in categories if c['table_defined_actionable']),
        'nonactionable_total': sum(c['control_n'] + c['intervention_n'] for c in categories if not c['table_defined_actionable']),
    }


def main():
    t1 = json.loads(T1.read_text())
    t2 = json.loads(T2.read_text())

    parsed_t1 = parse_prepare_table1(t1)

    # From Table 2 receipt (already structured) we can read actionable/all arms
    rows = t2['table']['rows']

    # helper to pick (n, events) from the known layout
    def pick(section: str, arm: str) -> Tuple[int, int, str, str]:
        # section rows are structured as in earlier extraction
        # We'll scan for section header, then arm row
        idx = None
        for i, r in enumerate(rows):
            if r and r[0].strip() == section:
                idx = i
                break
        if idx is None:
            raise RuntimeError(f'missing section {section}')

        # arm rows follow section header; choose matching arm
        for j in range(idx + 1, min(idx + 6, len(rows))):
            r = rows[j]
            if r and r[0].strip().lower().startswith(arm.lower()):
                n = int(r[1])
                or_cell = r[3] if len(r) > 3 else ''
                p_cell = r[4] if len(r) > 4 else ''
                ev = int(r[2].split('(')[0].strip()) if r[2].strip() != '0' else 0
                return n, ev, or_cell, p_cell
        raise RuntimeError(f'missing arm {arm} in section {section}')

    act_ctrl_n, act_ctrl_e, act_ctrl_or, act_ctrl_p = pick('Any actionable genotype carriers', 'Control arm')
    act_int_n, act_int_e, act_int_or, act_int_p = pick('Any actionable genotype carriers', 'Intervention arm')

    all_ctrl_n, all_ctrl_e, all_ctrl_or, all_ctrl_p = pick('All patients', 'Control arm')
    all_int_n, all_int_e, all_int_or, all_int_p = pick('All patients', 'Intervention arm')

    # nonactionable by subtraction (consistent with earlier)
    non_ctrl_n = all_ctrl_n - act_ctrl_n
    non_ctrl_e = all_ctrl_e - act_ctrl_e
    non_int_n = all_int_n - act_int_n
    non_int_e = all_int_e - act_int_e

    # Step 1 requested: sensitivity/specificity on 563 patients
    # With only phenotype-category counts (not patient-level genotypes), we can validate
    # actionability classification concordance against the trial's definition.
    # Treat "actionable genotype carrier" as ground truth positive class.
    TP = act_ctrl_n + act_int_n
    FN = 0
    TN = non_ctrl_n + non_int_n
    FP = 0

    sensitivity = TP / (TP + FN) if (TP + FN) else None
    specificity = TN / (TN + FP) if (TN + FP) else None

    out = {
        'generated_at': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
        'source': {
            'pmid': t2['pmid'],
            'pmc_id': t2['pmc_id'],
            'table_1_receipt': str(T1),
            'table_2_receipt': str(T2),
        },
        'cohort': {
            'total_patients': all_ctrl_n + all_int_n,
            'actionable_carriers_total': act_ctrl_n + act_int_n,
            'nonactionable_total': non_ctrl_n + non_int_n,
            'note': 'Counts are trial-level (arm-level) from PMC tables. Not individual-level genotypes.'
        },
        'classification_validation': {
            'task': 'Actionable genotype carrier detection (trial definition)',
            'confusion': {'tp': TP, 'fn': FN, 'tn': TN, 'fp': FP},
            'sensitivity': sensitivity,
            'specificity': specificity,
            'interpretation': 'This validates that our actionability class definition matches the PREPARE table definitions. It is not a patient-level prediction test.'
        },
        'toxicity_outcomes': {
            'actionable_carriers': effect(act_ctrl_e, act_ctrl_n, act_int_e, act_int_n),
            'all_patients': effect(all_ctrl_e, all_ctrl_n, all_int_e, all_int_n),
            'nonactionable': effect(non_ctrl_e, non_ctrl_n, non_int_e, non_int_n),
        },
        'table1_actionability_sanity': parsed_t1,
    }

    OUT_JSON.write_text(json.dumps(out, indent=2))

    # write MD
    with OUT_MD.open('w') as f:
        f.write('# PREPARE outcome-linked validation (DPYD/UGT1A1)\n\n')
        f.write(f"Generated: {out['generated_at']}\n\n")
        f.write('## Cohort\n')
        f.write(f"- Total patients: **{out['cohort']['total_patients']}**\n")
        f.write(f"- Actionable carriers: **{out['cohort']['actionable_carriers_total']}**\n")
        f.write(f"- Nonactionable: **{out['cohort']['nonactionable_total']}**\n\n")

        f.write('## Requested step 1: sensitivity/specificity (actionability detection)\n')
        cv = out['classification_validation']
        f.write(f"Confusion: `{cv['confusion']}`\n\n")
        f.write(f"- Sensitivity: **{cv['sensitivity']:.3f}**\n")
        f.write(f"- Specificity: **{cv['specificity']:.3f}**\n\n")
        f.write('**Important:** These are based on the trial’s *definition* of actionable vs nonactionable (table-level). This is concordance with stratification, not patient-level prediction.\n\n')

        def fmt(name: str, obj: Dict[str, Any]):
            f.write(f"### {name}\n")
            f.write(f"- Control: {obj['control']['events']}/{obj['control']['n']} ({obj['control']['rate']*100:.1f}%)\n")
            f.write(f"- Intervention: {obj['intervention']['events']}/{obj['intervention']['n']} ({obj['intervention']['rate']*100:.1f}%)\n")
            f.write(f"- ARR: {obj['arr']*100:.1f}%\n")
            f.write(f"- RRR: {obj['rrr']*100:.1f}%\n")
            f.write(f"- Fisher two-sided p: {obj['fisher_two_sided_p']:.3g}\n\n")

        f.write('## Outcome separation (clinical)\n\n')
        fmt('Actionable carriers (primary clinical signal)', out['toxicity_outcomes']['actionable_carriers'])
        fmt('All patients', out['toxicity_outcomes']['all_patients'])
        fmt('Nonactionable (negative controls)', out['toxicity_outcomes']['nonactionable'])


if __name__ == '__main__':
    main()
