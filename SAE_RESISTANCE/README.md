# 📚 SAE Resistance Prediction: Publication Materials

**Status:** ✅ **CONSOLIDATED** (December 24, 2025)  
**Target Venue:** bioRxiv (preprint) → Nature Communications / Cell Reports Medicine  
**Location:** `.cursor/MOAT/CLINICAL_TRIALS/publication/SAE_RESISTANCE/`

---

## 📌 THE STORY

### Title (Recommended)
**"Sparse Autoencoder Features from Protein Language Models Predict Platinum Resistance in Ovarian Cancer"**

### Key Finding
TRUE SAE features (AUROC 0.783) outperform gene-level PROXY SAE (AUROC 0.628) for predicting platinum resistance, with all 9 large-effect features mapping coherently to the DNA Damage Repair (DDR) pathway.

### Numbers That Matter
| Metric | TRUE SAE | PROXY SAE | Delta |
|--------|----------|-----------|-------|
| Mean AUROC (5-fold CV) | **0.783 ± 0.100** | 0.628 ± 0.119 | +0.155 |
| DDR_bin p-value | **p=0.0020** | N/A | Significant |
| Feature→Pathway coherence | 9/9 DDR | N/A | 100% |

---

## 📁 Contents

### `/manuscript/`
- `MANUSCRIPT_DRAFT.md` — Full manuscript (Methods, Results, Discussion)
- `references.bib` — BibTeX references

### `/figures/`
- `figure2_roc_curves.png` — TRUE SAE vs PROXY SAE ROC comparison
- `figure3_ddr_bin_distribution.png` — DDR_bin in resistant vs sensitive patients
- `figure4_feature_pathway_mapping.png` — 9 diamond features → DDR pathway mapping

### `/scripts/`
- `head_to_head_proxy_vs_true.py` — Fair head-to-head comparison (5-fold CV)
- `generate_ddr_bin_distribution.py` — Generate Figure 3

### `/data/`
- `sae_feature_mapping.true_sae_diamonds.v1.json` — 9 diamond feature mappings
- `true_sae_diamonds_baseline.v1.json` — Reproducible AUROC baseline

### Root files
- `PUBLICATION_PLAN_PROXY_VS_TRUE_SAE.mdc` — Full publication plan

---

## 🎯 Key Figures

### Figure 2: ROC Comparison
- TRUE SAE (blue) vs PROXY SAE (orange)
- Shows clear separation across all 5 folds

### Figure 3: DDR_bin Distribution
- Resistant patients (orange) have higher DDR_bin scores
- Cohen's d = 0.642, p = 0.0020

### Figure 4: Feature→Pathway Mapping
- All 9 large-effect features map to DDR pathway
- TP53 dominant (28/30 top-activating variants)

---

## 📊 Validation Status

| Component | Status | Artifact |
|-----------|--------|----------|
| TRUE SAE extraction | ✅ Complete | Tier-3 cohort (149 patients) |
| Head-to-head comparison | ✅ Complete | TRUE SAE wins all 5 folds |
| Feature mapping | ✅ Complete | 9/9 features → DDR_bin |
| DDR_bin significance | ✅ Complete | p=0.0020, d=0.642 |
| Figures generated | ✅ Complete | Figures 2, 3, 4 |
| Manuscript draft | ✅ Complete | Ready for review |

---

## 🚀 Next Steps

1. **Internal review** — Alpha + Manager review manuscript
2. **Supplementary materials** — Add detailed methods, extended data
3. **bioRxiv submission** — Target: Q1 2025
4. **Peer review journal** — Target: Nature Communications

---

## 🔗 Related Documents

- `.cursor/MOAT/SAE_INTELLIGENCE/` — SAE system documentation
- `.cursor/MOAT/PREVENTION/` — Prevention framework (uses DDR_bin)
- `.cursor/MOAT/SAE_FAILURE_POSTMORTEM.mdc` — Journey to TRUE SAE

---

*Document Owner: Zo*  
*Last Updated: December 24, 2025*

