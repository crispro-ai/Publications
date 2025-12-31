## Benchmark composition (transparency)

Dataset: `publications/synthetic_lethality/data/data/test_cases_100.json`

Totals: N=100 (SL+ N=70, SL- N=30)

### SL-positive gene distribution

| Gene | Count | % |
|---|---:|---:|
| TP53 | 12 | 17.1% |
| CDK12 | 10 | 14.3% |
| BRCA1 | 8 | 11.4% |
| RAD51C | 8 | 11.4% |
| BRCA2 | 7 | 10.0% |
| RAD51D | 7 | 10.0% |
| ARID1A | 6 | 8.6% |
| PALB2 | 5 | 7.1% |
| MBD4 | 4 | 5.7% |
| ATM | 3 | 4.3% |

### SL-negative gene distribution

| Gene | Count | % |
|---|---:|---:|
| KRAS | 15 | 50.0% |
| EGFR | 15 | 50.0% |

### Lineage proxy (disease field) distribution

| Disease | Count | % |
|---|---:|---:|
| breast_cancer | 34 | 34.0% |
| prostate_cancer | 34 | 34.0% |
| ovarian_cancer | 32 | 32.0% |

### Variant consequence distribution

| Consequence | Count | % |
|---|---:|---:|
| missense | 50 | 50.0% |
| unknown | 39 | 39.0% |
| stop_gained | 7 | 7.0% |
| frameshift_variant | 4 | 4.0% |

### SL-positive ground-truth drug distribution

| Drug | Count | % |
|---|---:|---:|
| olaparib | 52 | 42.6% |
| niraparib | 52 | 42.6% |
| ceralasertib | 11 | 9.0% |
| adavosertib | 7 | 5.7% |

