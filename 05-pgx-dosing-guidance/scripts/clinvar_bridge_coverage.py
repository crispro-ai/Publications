import json
import time
import urllib.parse
import urllib.request
from collections import Counter

CPIC_PATH = 'publications/05-pgx-dosing-guidance/reports/cpic_concordance_report.json'
CASES_PATH = 'publications/05-pgx-dosing-guidance/data/extraction_all_genes_curated.json'
OUT_JSON = 'publications/05-pgx-dosing-guidance/reports/clinvar_bridge_coverage.json'
OUT_MD = 'publications/05-pgx-dosing-guidance/reports/CLINVAR_BRIDGE_COVERAGE_REPORT.md'


def fetch(url: str, timeout: int = 25) -> tuple[int, str]:
    req = urllib.request.Request(url, headers={
        'User-Agent': 'Mozilla/5.0 (compatible; CrisPRO-PGx-Validation/1.0)',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    })
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.status, resp.read().decode('utf-8', errors='replace')


def count_labels(html: str) -> dict:
    # Mirror the simplistic heuristic used in api/routers/evidence/clinvar.py
    low = html.lower()
    def c(term: str) -> int:
        return low.count(term.lower())
    # Note: 'likely pathogenic' contains 'pathogenic', so count LP first and subtract is messy.
    # We keep counts as raw signals, not ground truth.
    return {
        'pathogenic': c('pathogenic'),
        'likely_pathogenic': c('likely pathogenic'),
        'benign': c('benign'),
        'likely_benign': c('likely benign'),
        'vus': c('uncertain significance'),
        'conflicting': c('conflicting classifications of pathogenicity'),
    }


from typing import Optional

def classify(counts: dict) -> Optional[str]:
    # Conservative label: conflicting if explicit conflicting OR both pathogenic+benign appear.
    if counts.get('conflicting', 0) > 0:
        return 'conflicting'
    has_path = counts.get('pathogenic', 0) > 0 or counts.get('likely_pathogenic', 0) > 0
    has_ben = counts.get('benign', 0) > 0 or counts.get('likely_benign', 0) > 0
    if has_path and has_ben:
        return 'conflicting'
    if has_path:
        return 'pathogenic_signal'
    if has_ben:
        return 'benign_signal'
    if counts.get('vus', 0) > 0:
        return 'vus_signal'
    return None


def build_clinvar_url(gene: str, variant: str) -> str:
    term = f"{gene} {variant}".strip()
    return 'https://www.ncbi.nlm.nih.gov/clinvar/?term=' + urllib.parse.quote(term)


def main():
    cpic = json.load(open(CPIC_PATH))
    cases_doc = json.load(open(CASES_PATH))
    cases = {c['case_id']: c for c in cases_doc['cases']}

    non_cpic = [r for r in cpic['concordance_results'] if r.get('cpic_recommendation') is None]

    rows = []
    for r in non_cpic:
        cid = r['case_id']
        gene = r.get('gene') or (cases.get(cid) or {}).get('gene')
        var = (r.get('variant') or (cases.get(cid) or {}).get('variant') or '').strip()

        url = build_clinvar_url(gene or '', var)
        status = None
        html = ''
        err = None
        try:
            status, html = fetch(url)
        except Exception as e:
            err = str(e)

        counts = count_labels(html) if html else {}
        label = classify(counts) if html else None

        rows.append({
            'case_id': cid,
            'gene': gene,
            'variant': var,
            'url': url,
            'http_status': status,
            'fetched': bool(html) and status == 200,
            'counts': counts,
            'heuristic_label': label,
            'error': err,
        })
        time.sleep(0.25)  # be polite

    fetched = sum(1 for x in rows if x['fetched'])
    labeled = sum(1 for x in rows if x['heuristic_label'] is not None)
    total = len(rows)
    by_label = Counter(x['heuristic_label'] or 'none' for x in rows)

    out = {
        'generated_at': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
        'definition': {
            'metric': 'ClinVar bridge coverage',
            'coverage_meaning': 'Whether the system can retrieve a ClinVar search page for the variant and extract any classification signal using the current heuristic (NOT clinical accuracy).',
            'algorithm_note': 'This uses a simplistic HTML term-count heuristic mirroring api/routers/evidence/clinvar.py; it is evidence retrieval, not expert adjudication.'
        },
        'non_cpic_cases': total,
        'fetched_200': fetched,
        'heuristic_labeled': labeled,
        'coverage_rate_fetched': fetched / total if total else None,
        'coverage_rate_labeled': labeled / total if total else None,
        'label_distribution': dict(by_label),
        'rows': rows,
    }

    with open(OUT_JSON, 'w') as f:
        json.dump(out, f, indent=2)

    with open(OUT_MD, 'w') as f:
        f.write('# ClinVar Bridge Coverage Report\n\n')
        f.write(f"Generated: {out['generated_at']}\n\n")
        f.write('## What this report validates\n\n')
        f.write('- **Coverage (retrieval)**: can we fetch a ClinVar page for each non-CPIC variant?\n')
        f.write('- **Coverage (signal extraction)**: can we extract any classification signal using the current heuristic?\n')
        f.write('- This does **NOT** validate clinical correctness or dosing guidance accuracy for non-CPIC variants.\n\n')
        f.write('## Summary\n\n')
        f.write(f"- Non-CPIC variants: **{total}**\n")
        f.write(f"- ClinVar pages fetched (HTTP 200): **{fetched}/{total}**\n")
        f.write(f"- Heuristic label extracted: **{labeled}/{total}**\n")
        f.write(f"- Label distribution: `{json.dumps(out['label_distribution'])}`\n\n")
        f.write('## Sample rows\n\n')
        for x in rows[:15]:
            f.write(f"- {x['case_id']} {x['gene']} {x['variant']} → fetched={x['fetched']} label={x['heuristic_label']}\n")


if __name__ == '__main__':
    main()
