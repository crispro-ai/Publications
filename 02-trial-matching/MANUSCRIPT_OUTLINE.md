# Manuscript Outline: Mechanism-Based Clinical Trial Matching

## 1. Title
Mechanism-Based Clinical Trial Matching: Validated Discrimination of Pathway-Aligned Trials Using 7D Biomarker Vectors

## 2. Abstract
(See `aacr/AACR_ABSTRACT.md`)

## 3. Introduction
- **The Problem**: Phase 2 clinical trial success rate is 28.9%.
- **The Gap**: Generic eligibility criteria (age, stage, etc.) ignore pathway-level mechanism alignment.
- **The Solution**: A novel 7D pathway-vector approach to rank trials by mechanism fit.

## 4. Methods
### 4.1 Patient 7D Mechanism Vectors
- Pathways: DDR, MAPK, PI3K, VEGF, HER2, IO, Efflux.
- Aggregation: Raw sequence disruption weighted by pathway involvement.
- TP53 → DDR (50% contribution handled separately).

### 4.2 Trial MoA Vectors
- Pre-tagged using Gemini API (47 trials validated).
- Represents drug mechanism of action in the same 7D space.### 4.3 Magnitude-Weighted Mechanism Fit (Zeta Protocol Fix)
- **Algorithm**: `fit = (patient_vector · trial_vector) / ||trial_vector||`
- **Rationale**: Pure cosine similarity is magnitude-invariant, leading to overconfident recommendations for low-burden patients. Weighted similarity ensures that low patient burden results in low mechanism fit, even if the pathway pattern matches.

## 5. Results
### 5.1 Mechanism Discrimination
- Mean DDR Fit (High-DDR Patient): **0.874**
- Mean Non-DDR Fit (High-DDR Patient): **0.038**
- Separation Delta: **0.836** (23× discrimination ratio).

### 5.2 Ranking Accuracy
- Top-3 Recall: **0.917**
- Mean Reciprocal Rank (MRR): **0.875**
- (Validated against pilot SME labels across 4 clinical archetypes).

### 5.3 Supporting Clinical Evidence (TCGA)
- **IO Validation**: TMB/MSI stratify OS in TCGA-UCEC (**p=0.001**, **HR=0.32**).
- **DDR Gap Analysis**: Failure of binary PARP gating in TCGA-OV (**p=0.55**) justifies high-resolution mechanism matching.

### 5.4 Shortlist Comession
- 60-65% reduction in trial volume (50+ trials → 5-12 trials).

## 6. Discussion
- Importance of magnitude-aware similarity for clinical safety.
- Decoupling prognostic biomarkers (TCGA) from predictive matching validation.
- Future work: Prospective clinical outcome validation using trial enrollment data.

## 7. Conclusions
Mechanism-based matching provides a rigorous, auditable, and safe approach to precision oncology trial enrollment.
