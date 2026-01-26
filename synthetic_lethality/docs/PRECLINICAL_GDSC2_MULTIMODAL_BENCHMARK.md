# Preclinical Multimodal Synthetic Lethality Benchmark (GDSC2 + DepMap + Omics)

**Status**: Deliverable implemented (preclinical RUO)  
**Scope**: Cell-line outcomes (NOT patient outcomes)

---

## What we are delivering (the abstraction)

This benchmark instantiates the core **multimodal mechanistic stack**:

- **S (Sequence disruption)**: allele-resolved variants (`Chrom/Pos/Ref/Alt`) scored with Evo2 (delta log-likelihood)
- **P (Pathway aggregation)**: mechanistic gene-set aggregation into drug-class scores
- **D (Dependency grounding)**: context/lineage essentiality priors (DepMap) used as a safety penalty

**Prediction task** (preclinical):

> For each cell line, predict the best drug class (PARP / ATR / WEE1 / DNA-PK) or NONE.

**Outcome label** (ground truth): derived from **GDSC2 drug sensitivity** (Z_SCORE) under a transparent rule.

---

## Data inputs used

- **Omics (allele-resolved variants)**: `publications/synthetic_lethality/data/OmicsSomaticMutations.csv`
- **Drug response**: `publications/synthetic_lethality/data/GDSC2_fitted_dose_response_27Oct23.xlsx`
- **DepMap model mapping**: `data/depmap/Model.csv` (ModelID ↔ COSMICID + lineage)
- **DepMap grounding artifact**: `publications/synthetic_lethality/data/depmap_essentiality_by_context.json`

---

## 1) Preflight (join + coverage + label distribution)

This proves the join exists and tells us how much real coverage we have.

Run:

```bash
python3 publications/synthetic_lethality/code/preflight_gdsc2_depmap_omics.py \
  --max_lines 1000 \
  --z_sensitive_threshold -0.8 \
  --min_margin 0.25 \
  --out gdsc2_depmap_omics_preflight_m1k.json
```

Output receipt:
- `publications/synthetic_lethality/results/gdsc2_depmap_omics_preflight_m1k.json`

Key outputs:
- label distribution (PARP/ATR/WEE1/DNA_PK/NONE)
- number of cell lines with Omics mutation coverage
- top lineages

---

##  Benchmark runner (S/P/D)

Runner:
- `publications/synthetic_lethality/code/benchmark_gdsc2_multimodal_spd.py`

What it does:
- Builds labels from GDSC2 mean Z_SCORE per class (with ambiguity gating)
- Samples a **balanced** set per class (`--n_per_class`)
- Pulls DDR-relevant variants for those cell lines from Omics
- Scores variants via Evo2 (or cache-only for smoke)
- Computes method outputs:
  - **Always NONE**
  - **P-only**
  - **SP** (Sequence+Pathway)
  - **SPD** (SP + DepMap lineage penalty)

### Smoke run (cache-only)

This is intended to validate formats and end-to-end wiring quickly (not performance).

```bash
python3 publications/synthetic_lethality/code/benchmark_gdsc2_multimodal_spd.py \
  --n_per_class 3 \
  --max_variants_per_line 8 \
  --use_cache_only \
  --cache_path publications/synthetic_lethality/results/gdsc2_multiclass_evo2_preflight_25_evo2_cache.json \
  --out_prefix gdsc2_multimodal_spd_smoke
```

Output receipt example:
- `publications/synthetic_lethality/results/gdsc2_multimodal_spd_smoke_n15.json`

### Full run (Evo2 scoring enabled)

Remove `--use_cache_only` to allow Evo2 scoring calls. Scores are cached to `results/..._evo2_cache.json`.

```bash
python3 publications/synthetic_lethality/code/benchmark_gdsc2_multimodal_spd.py \
  --n_per_class 50 \
  --max_variants_per_line 12 \
  --out_prefix gdsc2_multimodal_spd_v1
```

---

## Notes / current limitations (honest)

- This is **preclinical**: GDSC2 is an in-vitro proxy, not clinical response.
- Performance is currently not optimized; this delivers the benchmark harness + receipts.
- To drive accuracy upward, the next step is to:
  - improve label definition (avoid trivial dominance by a class)
  - tune none-thresholds and class thresholds on train split (no leakage)
  - broaden features beyond max-disruption (e.g., per-gene counts, severity-weighted aggregation)
  - add additional modalities (expression signatures) if available

