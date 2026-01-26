# Trial Matching Publication: Submission Readiness Audit

**Date:** January 4, 2026  
**Status:** ✅ **SUBMISSION READY** (with minor fixes applied)

---

## ✅ **AUDIT RESULTS**

### **1. Abstract Consistency** ✅
- **PUBLICATION_ABSTRACT.md**: All metrics match receipts
  - DDR fit: **0.874** ✅ (receipt: 0.874)
  - Non-DDR fit: **0.038** ✅ (receipt: 0.038)
  - Separation: **0.836** ✅ (receipt: 0.836)
  - Matchable %: **46.3%** ✅ (receipt: 46.3%)
  - Cox HR: **1.122, p=0.288** ✅ (receipt: 1.122, p=0.288)
  - Logrank p: **0.288** ✅ (receipt: 0.288)
  - Algorithm: **magnitude-weighted similarity** ✅ (correctly stated)

- **AACR_ABSTRACT.md**: ✅ **FIXED** - Updated to mention "magnitude-weighted similarity" instead of "cosine similarity"

- **MANUSCRIPT_OUTLINE.md**: All metrics match receipts ✅

### **2. Receipt Validation** ✅
All critical receipts present and validated:

| Receipt | Status | Key Metrics |
|---------|--------|---------json` | ✅ | DDR: 0.874, Non-DDR: 0.038, Separation: 0.836 |
| `real_world_tcga_ov_validation.json` | ✅ | Matchable: 46.3% (n=585) |
| `real_world_tcga_ov_survival_validation.json` | ✅ | Cox HR=1.122, p=0.288; Logrank p=0.288 |
| `eval_ranking.json` | ✅ | MRR: 0.875, Recall@3: 0.917 |
| `zeta_fix_validation.json` | ✅ | Validates magnitude-weighted fix |
| `io_dimension_validation.json` | ✅ | IO dimension validation |
| `kras_g12c_edge_case.json` | ✅ | KRAS G12C edge case |
| `repro_manifest.json` | ✅ | Reproducibility manifest |

### **3. Algorithm Consistency** ✅
- **Magnitude-weighted similarity** correctly implemented in:
  - `api/services/mechanism_fit_ranker.py` (production code)
  - `scripts/compute_mechanism_sanity.py` (validation script)
- **Algorithm provenance** tracked in receipts (`algorithm: "magnitude_weighted_similarity_v1"`)

### **4. Narrative Consistency** ✅
- **Antagonists explicitly named**:
  1. Eligibility-only matching (ignores mechanism alignment)
  2. Cosine similriance (false positives for low-burden patients)
- **Solution clearly stated**: Magnitude-weighted similarity with 7D mechanism vectors
- **Validation scope transparent**: Mechanism discrimination + matchability prevalence (NOT outcome benefit)

### **5. Claim Guardrails** ✅
- **Explicitly stated** in PUBLICATION_ABSTRACT.md:
  - ✅ Validated: mechanism discrimination; real-cohort matchability prevalence; cosine-to-magnitude safety fix
  - ✅ NOT validated: enrollment lift, response, PFS/OS benefit, or causal treatment efficacy

### **6. File Structure** ✅
- **Scripts**: 15 Python scripts present
- **Data**: 2 JSON data files present
- **Receipts**: 9 receipts in `receipts/latest/`
- **Abstracts**: Both PUBLICATION_ABSTRACT.md and AACR_ABSTRACT.md present and consistent

### **7. Reproducibility** ✅
- **Repro manifest**: `repro_manifest.json` present with SHA256 hashes
- **Fixed seeds**: All scripts use deterministic seeds where applicable
- **Input data**: All input files documented and accessible
� **FIXES APPLIED**

1. ✅ **AACR_ABSTRACT.md**: Updated line 13 to mention "magnitude-weighted similarity" instead of "cosine similarity"

---

## 📋 **SUBMISSION CHECKLIST**

- [x] All metrics match receipts
- [x] Algorithm correctly stated (magnitude-weighted similarity)
- [x] Antagonists explicitly named
- [x] Validation scope transparent
- [x] Claim guardrails explicit
- [x] All receipts present and validated
- [x] Reproducibility manifest present
- [x] Narrative consistent across all documents

---

## ✅ **VERDICT: SUBMISSION READY**

All critical components validated. The publication bundle is ready for submission with:
- ✅ Receipt-backed metrics
- ✅ Transparent limitations
- ✅ Reproducible validation
- ✅ Consistent narrative

**No blocking issues identified.**
