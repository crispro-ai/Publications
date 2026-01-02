# Supplement (Sporadic Cancer Strategy)

This supplement provides executable receipts backing the manuscript claims (unit tests, validation scripts, scenario-suite outputs, E2E smoke test outputs, and example API requests/responses).

## Supplement A. Claims vs code truth table

| Claim | Code location | Receipt | Status |
|---|---|---|---|
| PARP germline/HRD gate: germline− & HRD<42 → 0.6x; rescue at HRD≥42; unknown → 0.8x | `oncology-coPilot/oncology-backend-minimal/api/services/efficacy_orchestrator/sporadic_gates.py` | `receipts/pytest_sporadic_gates.txt`, `receipts/validate_sporadic_gates_report.json` | PASS |
| IO boost gate (checkpoint drugs): TMB≥20 → 1.35x; MSI-high → 1.30x; TMB≥10 → 1.25x (mutually exclusive) | `.../sporadic_gates.py` | `receipts/pytest_sporadic_gates.txt`, `receipts/validate_sporadic_gates_report.json` | PASS |
| Confidence caps: L0 cap 0.4; L1 cap 0.6; L2 no cap | `.../sporadic_gates.py` | `receipts/pytest_sporadic_gates.txt`, Fig. 3 | PASS |
| Orchestrator attaches `sporadic_gates_provenance` per drug when context present | `oncology-coPilot/oncology-backend-minimal/api/services/efficacy_orchestrator/orchestrator.py` | `receipts/e2e_efficacy_response.json` | PASS |
| E2E workflow (Quick Intake → efficacy predict) produces provenance-bearing outputs | `api/routers/tumor.py`, `.../orchestrator.py` | `receipts/e2e_tumor_context.json`, `receipts/e2e_efficacy_response.json`, `receipts/e2e_sporadic_workflow.txt` | PASS |
| Trials search supports sporadic filtering metadata (`excluded_count`, biomarker matches) | `api/services/hybrid_trial_search.py` | Code inspection; environment-dependent (AstraDB/Neo4j) | PARTIAL |

## Supplement B. Scenario suite outputs (25 cases)

- Scenario suite file: `data/scenario_suite_25_20251231_080940.json`
- Count: 25 cases
- Gate effects benchmark receipt: `receipts/benchmark_gate_effects.json` (changed efficacy in 13/25 cases; changed confidence in 13/25 cases)

| Case | Label | Germline | Completeness | Inputs (TMB/MSI/HRD) | Eff(in→out) | Conf(in→out) | Gates applied |
|---|---|---|---:|---|---|---|---|
| SC001 | PARP_gate | negative | 0.5 | TMB=-; MSI=-; HRD=- | 0.70→0.56 | 0.80→0.60 | PARP_UNKNOWN_HRD, CONFIDENCE_CAP_L1 |
| SC002 | PARP_gate | negative | 0.5 | TMB=-; MSI=-; HRD=10.0 | 0.70→0.42 | 0.80→0.60 | PARP_HRD_LOW, CONFIDENCE_CAP_L1 |
| SC003 | PARP_gate | negative | 0.5 | TMB=-; MSI=-; HRD=25.0 | 0.70→0.42 | 0.80→0.60 | PARP_HRD_LOW, CONFIDENCE_CAP_L1 |
| SC004 | PARP_gate | negative | 0.5 | TMB=-; MSI=-; HRD=41.0 | 0.70→0.42 | 0.80→0.60 | PARP_HRD_LOW, CONFIDENCE_CAP_L1 |
| SC005 | PARP_gate | negative | 0.5 | TMB=-; MSI=-; HRD=42.0 | 0.70→0.70 | 0.80→0.60 | PARP_HRD_RESCUE, CONFIDENCE_CAP_L1 |
| SC006 | PARP_gate | negative | 0.5 | TMB=-; MSI=-; HRD=58.0 | 0.70→0.70 | 0.80→0.60 | PARP_HRD_RESCUE, CONFIDENCE_CAP_L1 |
| SC007 | PARP_gate | positive | 0.5 | TMB=-; MSI=-; HRD=10.0 | 0.70→0.70 | 0.80→0.60 | PARP_GERMLINE, CONFIDENCE_CAP_L1 |
| SC008 | PARP_gate | unknown | 0.2 | TMB=-; MSI=-; HRD=- | 0.70→0.56 | 0.80→0.40 | PARP_UNKNOWN_GERMLINE, CONFIDENCE_CAP_L0 |
| SC009 | PARP_gate | unknown | 0.9 | TMB=-; MSI=-; HRD=60.0 | 0.70→0.56 | 0.80→0.80 | PARP_UNKNOWN_GERMLINE |
| SC010 | IO_gate | negative | 0.9 | TMB=5.0; MSI=MSS; HRD=- | 0.60→0.60 | 0.70→0.70 | - |
| SC011 | IO_gate | negative | 0.9 | TMB=10.0; MSI=MSS; HRD=- | 0.60→0.60 | 0.70→0.70 | - |
| SC012 | IO_gate | negative | 0.9 | TMB=19.0; MSI=MSS; HRD=- | 0.60→0.60 | 0.70→0.70 | - |
| SC013 | IO_gate | negative | 0.9 | TMB=20.0; MSI=MSS; HRD=- | 0.60→0.81 | 0.70→0.70 | IO_TMB_BOOST |
| SC014 | IO_gate | negative | 0.9 | TMB=25.0; MSI=MSS; HRD=- | 0.60→0.81 | 0.70→0.70 | IO_TMB_BOOST |
| SC015 | IO_gate | negative | 0.9 | TMB=5.0; MSI=MSI-High; HRD=- | 0.60→0.78 | 0.70→0.70 | IO_MSI_BOOST |
| SC016 | IO_gate | negative | 0.9 | TMB=5.0; MSI=MSI-H; HRD=- | 0.60→0.78 | 0.70→0.70 | IO_MSI_BOOST |
| SC017 | IO_gate | negative | 0.9 | TMB=25.0; MSI=MSI-High; HRD=- | 0.60→0.81 | 0.70→0.70 | IO_TMB_BOOST |
| SC018 | IO_gate | negative | 0.9 | TMB=25.0; MSI=MSI-H; HRD=- | 0.60→0.81 | 0.70→0.70 | IO_TMB_BOOST |
| SC019 | IO_gate | negative | 0.9 | TMB=-; MSI=MSI-High; HRD=- | 0.60→0.78 | 0.70→0.70 | IO_MSI_BOOST |
| SC020 | CONF_cap | unknown | 0.1 | TMB=-; MSI=-; HRD=- | 0.75→0.75 | 0.90→0.40 | CONFIDENCE_CAP_L0 |
| SC021 | CONF_cap | unknown | 0.25 | TMB=-; MSI=-; HRD=- | 0.75→0.75 | 0.50→0.40 | CONFIDENCE_CAP_L0 |
| SC022 | CONF_cap | unknown | 0.3 | TMB=-; MSI=-; HRD=- | 0.75→0.75 | 0.90→0.60 | CONFIDENCE_CAP_L1 |
| SC023 | CONF_cap | unknown | 0.5 | TMB=-; MSI=-; HRD=- | 0.75→0.75 | 0.65→0.60 | CONFIDENCE_CAP_L1 |
| SC024 | CONF_cap | unknown | 0.69 | TMB=-; MSI=-; HRD=- | 0.75→0.75 | 0.95→0.60 | CONFIDENCE_CAP_L1 |
| SC025 | CONF_cap | unknown | 0.7 | TMB=-; MSI=-; HRD=- | 0.75→0.75 | 0.95→0.95 | - |

## SupC. Example API payloads and responses

Examples receipt: `receipts/api_examples_20251231_083052.json`

### Endpoint: `/api/tumor/quick_intake`

**Request payload**

```json
{
  "cancer_type": "ovarian_hgs",
  "stage": "IIIC",
  "line": 2,
  "hrd_score": 35
}
```

**Response (truncated)**

```json
{
  "tumor_context": {
    "somatic_mutations": [],
    "copy_number_alterations": [],
    "fusions": [],
    "tmb": 5.2,
    "msi_status": null,
    "hrd_score": 35.0,
    "tmb_metrics": null,
    "msi_metrics": null,
    "hrd_metrics": null,
    "qc": null,
    "ihc": null,
    "signatures": null,
    "level": "L1",
    "priors_used": true,
    "completeness_score": 0.5,
    "tumor_context_source": "Quick Intake",
    "specimen_type": null,
    "report_date": null,
    "panel_name": null,
    "panel_version": null
  },
  "provenance": {
    "no_report_mode": true,
    "disease_priors_used": true,
    "disease_priors_version": "v1.0_bootstrap",
    "priors_refresh_date": "2025-12-31",
    "platinum_proxy_used": false,
    "confidence_version": "v1.0",
    "estimates": {
      "tmb": {
        "value": 5.2,
        "source": "disease_prior"
      },
      "msi_status": {
        "value": null,
        "source": "unknown"
      },
      "hrd_score": {
        "value": 35.0,
        "source": "manual"
      }
    }
  },
  "confidence_cap": 0.6,
  "recommendations": [
    "Level 1 analysis: Partial data provided. Full tumor NGS recommended for complete assessment.",
    "MSI status unknown. MSI testing (IHC/PCR or NGS) recommended for immunotherapy eligibility."
  ]
}
```

### Endpoint: `/api/efficacy/predict`

**Request payload**

```json
{
  "mutations": [
    {
      "gene": "TP53",
      "hgvs_p": "R248W"
    }
  ],
  "germline_status": "negative",
  "tumor_context": {
    "disease": "ovarian_hgs",
    "tmb": 5.0,
    "hrd_score": 30.0,
    "msi_status": "MSS",
    "completeness_score": 0.5
  },
  "disease": "ovarian",
  "options": {
    "include_all_drugs": true
  }
}
```

**Response (truncated)**

```json
{
  "drugs": [
    {
      "name": "adavosertib",
      "moa": "WEE1 inhibitor",
      "efficacy_score": 0.43,
      "confidence": 0.46,
      "evidence_tier": "consider",
      "badges": [
        "PathwayAligned"
      ],
      "evidence_strength": 0.0,
      "citations": [],
      "citations_count": 0,
      "clinvar": {
        "classification": null,
        "review_status": null,
        "prior": 0.0
      },
      "evidence_manifest": {
        "pubmed_query": null,
        "citations": [],
        "clinvar": {
          "classification": null,
          "review_status": null
        }
      },
      "insights": {
        "functionality": 0.0,
        "chromatin": 0.0,
        "essentiality": 0.0,
        "regulatory": 0.0
      },
      "rationale": [
        {
          "type": "sequence",
          "value": 0.1,
          "percentile": 0.1
        },
        {
          "type": "pathway",
          "percentile": 1.0,
          "breakdown": {
            "ras_mapk": 0.0,
            "tp53": 0.1
          }
        },
        {
          "type": "evidence",
          "strength": 0.0
        }
      ],
      "meets_evidence_gate": false,
      "insufficient_signal": false
    },
    {
      "name": "ceralasertib",
      "moa": "ATR inhibitor",
      "efficacy_score": 0.43,
      "confidence": 0.46,
      "evidence_tier": "consider",
      "badges": [
        "PathwayAligned"
      ],
      "evidence_strength": 0.0,
      "citations": [],
      "citations_count": 0,
      "clinvar": {
        "classification": null,
        "review_status": null,
        "prior": 0.0
      },
      "evidence_manifest": {
        "pubmed_query": null,
        "citations": [],
        "clinvar": {
          "classification": null,
          "review_status": null
        }
      },
      "insights": {
        "functionality": 0.0,
        "chromatin": 0.0,
        "essentiality": 0.0,
        "regulatory": 0.0
      },
      "rationale": [
        {
          "type": "sequence",
          "value": 0.1,
          "percentile": 0.1
        },
        {
          "type": "pathway",
          "percentile": 1.0,
          "breakdown": {
            "ras_mapk": 0.0,
            "tp53": 0.1
          }
        },
        {
          "type": "evidence",
          "strength": 0.0
        }
      ],
      "meets_evidence_gate": false,
      "insufficient_signal": false
    },
    {
      "name": "trametinib",
      "moa": "MEK inhibitor",
      "efficacy_score": 0.03,
      "confidence": 0.31,
      "evidence_tier": "consider",
      "badges": [],
      "evidence_strength": 0.0,
      "citations": [],
      "citations_count": 0,
      "clinvar": {
        "classification": null,
        "review_status": null,
        "prior": 0.0
      },
      "evidence_manifest": {
        "pubmed_query": null,
        "citations": [],
        "clinvar": {
          "classification": null,
          "review_status": null
        }
      },
      "insights": {
        "functionality": 0.0,
        "chromatin": 0.0,
        "essentiality": 0.0,
        "regulatory": 0.0
      },
      "rationale": [
        {
          "type": "sequence",
          "value": 0.1,
          "percentile": 0.1
        },
        {
          "type": "pathway",
          "percentile": 0.0,
          "breakdown": {
            "ras_mapk": 0.0,
            "tp53": 0.1
          }
        },
        {
          "type": "evidence",
          "strength": 0.0
        }
      ],
      "meets_evidence_gate": false,
      "insufficient_signal": false
    }
  ],
  "run_signature": "184e4cc9-377e-4225-8b3b-2d7f440504c6",
  "scoring_strategy": {
    "approach": "curated_fallback_missing_alleles",
    "source": "unknown",
    "models_tested": [],
    "windows_tested": [],
    "ablation_mode": "SPE"
  },
  "evidence_tier": "consider",
  "provenance": {
    "run_id": "184e4cc9-377e-4225-8b3b-2d7f440504c6",
    "profile": "baseline",
    "cache": "miss",
    "flags": {
      "fusion_active": false,
      
```

### Endpoint: `/api/efficacy/predict`

**Request payload**

```json
{
  "mutations": [
    {
      "gene": "BRCA1",
      "hgvs_p": "E23V"
    }
  ],
  "germline_status": "negative",
  "tumor_context": {
    "disease": "ovarian_hgs",
    "tmb": 25.0,
    "hrd_score": 30.0,
    "msi_status": "MSS",
    "completeness_score": 0.9
  },
  "disease": "ovarian",
  "options": {
    "include_all_drugs": true
  }
}
```

**Response (truncated)**

```json
{
  "drugs": [
    {
      "name": "olaparib",
      "moa": "PARP inhibitor",
      "efficacy_score": 0.258,
      "confidence": 0.54,
      "evidence_tier": "consider",
      "badges": [
        "PathwayAligned"
      ],
      "evidence_strength": 0.0,
      "citations": [],
      "citations_count": 0,
      "clinvar": {
        "classification": null,
        "review_status": null,
        "prior": 0.0
      },
      "evidence_manifest": {
        "pubmed_query": null,
        "citations": [],
        "clinvar": {
          "classification": null,
          "review_status": null
        }
      },
      "insights": {
        "functionality": 0.0,
        "chromatin": 0.0,
        "essentiality": 0.0,
        "regulatory": 0.0
      },
      "rationale": [
        {
          "type": "sequence",
          "value": 0.1,
          "percentile": 0.1
        },
        {
          "type": "pathway",
          "percentile": 1.0,
          "breakdown": {
            "ras_mapk": 0.0,
            "tp53": 0.0
          }
        },
        {
          "type": "evidence",
          "strength": 0.0
        }
      ],
      "meets_evidence_gate": false,
      "insufficient_signal": false,
      "sporadic_gates_provenance": {
        "germline_status": "negative",
        "level": "L2",
        "gates_applied": [
          "PARP_HRD_LOW",
          "SPORADIC_SUMMARY"
        ],
        "efficacy_delta": -0.172,
        "confidence_delta": 0.0,
        "rationale": [
          {
            "gate": "PARP_HRD_LOW",
            "verdict": "REDUCED",
            "penalty": 0.6,
            "hrd_score": 30.0,
            "reason": "Germline negative, HRD<42 (score=30.0) \u2192 PARP reduced to 0.6x"
          },
          {
            "gate": "SPORADIC_SUMMARY",
            "germline_status": "negative",
            "level": "L2",
            "completeness": 0.9,
            "original_efficacy": 0.43,
            "final_efficacy": 0.258,
            "efficacy_delta": -0.172,
            "original_confidence": 0.54,
            "final_confidence": 0.54,
            "confidence_delta": 0.0,
            "gates_applied": [
              "PARP_HRD_LOW"
            ]
          }
        ]
      }
    },
    {
      "name": "niraparib",
      "moa": "PARP inhibitor",
      "efficacy_score": 0.258,
      "confidence": 0.54,
      "evidence_tier": "consider",
      "badges": [
        "PathwayAligned"
      ],
      "evidence_strength": 0.0,
      "citations": [],
      "citations_count": 0,
      "clinvar": {
        "classification": null,
        "review_status": null,
        "prior": 0.0
      },
      "evidence_manifest": {
        "pubmed_query": null,
        "citations": [],
        "clinvar": {
          "classification": null,
          "review_status": null
        }
      },
      "insights": {
        "functionality": 0.0,
        "chromatin": 0.0,
        "essentiality": 0.0,
        "regulatory": 0.0
      },
      "rationale": [
        {
          "type": "sequence",
          "value": 0.1,
          "percentile": 0.1
        },
        {
          "type": "pathway",
          "percentile": 1.0,
          "breakdown": {
            "ras_mapk": 0.0,
            "tp53": 0.0
          }
        },
        {
          "type": "evidence",
          "strength": 0.0
        }
      ],
      "meets_evidence_gate": false,
      "insufficient_signal": false,
      "sporadic_gates_provenance": {
        "germline_status": "negative",
        "level": "L2",
        "gates_applied": [
          "PARP_HRD_LOW",
          "SPORADIC_SUMMARY"
        ],
        "efficacy_delta": -0.172,
        "confidence_delta": 0.0,
        "rationale": [
          {
            "gate": "PARP_HRD_LOW",
            "verdict": "REDUCED",
            "penalty": 0.6,
            "hrd_score": 30.0,
            "reason": "Germline negative, HRD<42 (score=30.0) \u2192 PARP reduced to 0.6x"
          },
          {
            "gate": "SPORADIC_SUMMARY",
            "germl
```

## Supplement D. Disease priors format and versioning policy

- **Priors file**: `oncology-coPilot/oncology-backend-minimal/api/resources/disease_priors.json`
- **Versioning policy (minimal)**:
  - Add a `priors_version` string and update it on every priors change (semantic or dated).
  - Quick Intake responses should echo `priors_version` and `priors_used` for provenance.
  - Missing priors fields must default to `null` and reduce completeness/confidence (never silently assumed).
  - Each priors update should include a short provenance note (source cohort + DOI/PMID when available).
