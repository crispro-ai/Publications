#!/bin/bash
# Resubmission-safe reproduction script
# - Stages canonical submission-bundle inputs into repo root `publication/`
# - Runs the same validation suite as `scripts/reproduce_all.sh`
# - Avoids any possibility of silently generating synthetic datasets
#
# Usage:
#   ./scripts/reproduce_all_resubmission.sh
#
set -e

echo "================================================================================"
echo "METASTASIS INTERCEPTION - RESUBMISSION-SAFE REPRODUCTION"
echo "================================================================================"
echo ""

START_TIME=$(date +%s)

echo "Step 1/6: Environment Setup..."
if [ ! -d "venv" ]; then
  echo "  Creating virtual environment..."
  python3 -m venv venv
fi
echo "  Installing dependencies..."
venv/bin/pip install -q --upgrade pip
venv/bin/pip install -q -r requirements.txt
echo ""

echo "Step 2/6: Configuration..."
export PYTHONPATH=$(pwd)
export SEED=42
export EVO_FORCE_MODEL=evo2_1b
export EVO_USE_DELTA_ONLY=1
echo ""

echo "Step 3/6: Stage canonical publication inputs..."
venv/bin/python stage_publication_inputs.py
echo ""

echo "Step 3.5/6: Update chromatin with Enformer (Option A)..."
venv/bin/python update_target_lock_chromatin_enformer.py
echo ""

echo "Step 4/6: Validation Metrics (Day 1)..."
venv/bin/python compute_per_step_validation.py
venv/bin/python compute_specificity_matrix.py
venv/bin/python compute_precision_at_k.py
venv/bin/python compute_ablation_study.py
venv/bin/python compute_confounder_analysis.py
echo ""

echo "Step 5/6: Enhanced Validation (Day 2)..."
venv/bin/python generate_calibration_curves.py
venv/bin/python compute_effect_sizes.py
venv/bin/python generate_table_s2.py
echo ""

echo "Step 6/7: Hold-Out Validation (28 train / 10 test)..."
venv/bin/python compute_holdout_validation.py
echo ""

echo "Step 7/8: Additional Validations (Optional - may require external data/services)..."
echo "  Note: TCGA and Prospective validations require external data/APIs"
echo "  These can be run separately if data/services are available:"
echo "    - TCGA: venv/bin/python compute_tcga_external_validation.py"
echo "    - Prospective: venv/bin/python compute_prospective_validation_direct_evo2.py (requires EVO2_API_BASE)"
echo ""

echo "Step 8/8: Verification..."
EXPECTED_FILES=(
  "../figures/figure2a_per_step_roc.png"
  "../figures/figure2b_specificity_matrix.png"
  "../figures/figure2c_precision_at_k.png"
  "../figures/figure2d_ablation.png"
  "../figures/figure_s1_confounders.png"
  "../figures/figure_s2_calibration_curves.png"
  "../figures/figure_s3_effect_sizes.png"
  "../data/per_step_validation_metrics.csv"
  "../data/specificity_enrichment.csv"
  "../data/precision_at_k.csv"
  "../data/ablation_study.csv"
  "../data/chromatin_audit_enformer_38genes.csv"
  "../data/confounder_analysis.csv"
  "../data/effect_sizes.csv"
  "../data/holdout_validation_metrics.csv"
  "../data/holdout_train_test_split.json"
  "../tables/table_s2_validation_metrics.csv"
)

OPTIONAL_FILES=(
  "../data/tcga_external_validation_metrics.csv"
  "../data/prospective_validation_target_lock_scores.csv"
  "../data/prospective_validation_with_negatives_scores.csv"
)

MISSING=0
for file in "${EXPECTED_FILES[@]}"; do
  if [ -f "$file" ]; then
    echo "  ✅ OK: $file"
  else
    echo "  ❌ MISSING: $file"
    MISSING=$((MISSING + 1))
  fi
done

echo ""
echo "Optional files (require external data/services):"
OPTIONAL_MISSING=0
for file in "${OPTIONAL_FILES[@]}"; do
  if [ -f "$file" ]; then
    echo "  ✅ OK: $file"
  else
    echo "  ⚠️  OPTIONAL (not found): $file"
    OPTIONAL_MISSING=$((OPTIONAL_MISSING + 1))
  fi
done

END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))
MINUTES=$((DURATION / 60))
SECONDS=$((DURATION % 60))

echo ""
echo "================================================================================"
echo "DONE"
echo "================================================================================"
echo "Time elapsed: ${MINUTES}m ${SECONDS}s"
if [ $MISSING -ne 0 ]; then
  echo "❌ ERROR: $MISSING required output file(s) missing"
  exit 1
fi
if [ $OPTIONAL_MISSING -gt 0 ]; then
  echo "⚠️  NOTE: $OPTIONAL_MISSING optional file(s) not found (TCGA/Prospective validations require external data/APIs)"
fi
echo "✅ All required files generated."

