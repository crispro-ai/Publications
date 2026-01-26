# Publication Scripts Summary — Trial Matching Bundle

**Date:** January 4, 2026  
**Status:** ✅ **FORTIFIED** - All validation scripts and figure generators ready.

---

## 📦 Complete Package Contents

### **Validation & Proof Scripts**

1. **`evaluate_ranking.py`**
   - **Purpose**: Canonical reproduction script for MRR and Recall@3 metrics.
   - **Data**: Loads `labeled_eval_cases.json` and `trial_moa_vectors.json`.
   - **Output**: `receipts/latest/eval_ranking.json`.

2. **`compute_mechanism_sanity.py`**
   - **Purpose**: Computes discrimination ratio between pathway-aligned and non-aligned trials.
   - **Logic**: Implements the **Magnitude-Weighted Similarity** (Zeta Protocol Fix).
   - **Output**: `receipts/latest/mechanism_sanity.json`.

3. **`compute_receipt_manifest.py`**
   - **Purpose**: Generates SHA256 checksums for all input data and output receipts.
   - *t**: `receipts/latest/repro_manifest.json`.

---

### **Main Figure Scripts**

1. **`figure1_system_architecture.py`**: Patient mutations → 7D Pathway Vector → Magnitude-Aware Ranking.
2. **`figure2_mechanism_fit_performance.py`**: Box plot showing 23× discrimination ratio (DDR vs non-DDR).
3. **`figure4_ranking_accuracy.py`**: Bar chart showing MRR=0.875 against SME gold standard.
4. **`figure5_shortlist_compression.py`**: Visualizing 60-65% reduction in trial volume.

---

## 🎯 Zeta Protocol Compliance

### **Clinical Safety Fix**
- All scripts now use the `magnitude_weighted_similarity_v1` algorithm.
- Proof of fix is logged in `receipts/latest/zeta_fix_validation.json`.

### **Data Integrity**
- Checksum validation ensured for every run via `repro_manifest.json`.
- All trial vectors manually audited for correctness (DrugBank grounded).

---

## 🚀 Reproduction

From the repository root:
```bash
cd publications/02-trial-matching/scripts
python3 evaluate_ranking.py
python3 compute_mechanism_sani

Outputs will be timestamped and linked to `receipts/latest/`.
