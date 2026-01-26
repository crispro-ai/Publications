## Hydrated publication suite (S/P/SP)

- **Run ID**: `20260122_204157`
- **Dataset**: `publications/synthetic_lethality/data/test_cases_100_hydrated_fixed_complete.json`
- **API**: `http://127.0.0.1:8000`
- **Model**: `evo2_1b`

### Summary

| Method | Pos Class@1 | 95% CI | Pos Drug@1 | 95% CI | Neg PARP FP | 95% CI | S modes |
|---|---:|---:|---:|---:|---:|---:|---|
| Ablation S | 18.6% | [10.0%, 28.6%] | 18.6% | [10.0%, 28.6%] | 0.0% | [0.0%, 0.0%] | `{"evo2_adaptive": 100}` |
| Ablation P | 18.6% | [10.0%, 28.6%] | 18.6% | [10.0%, 28.6%] | 0.0% | [0.0%, 0.0%] | `{"evo2_adaptive": 100}` |
| Ablation SP | 82.9% | [72.9%, 91.4%] | 82.9% | [72.9%, 91.4%] | 0.0% | [0.0%, 0.0%] | `{"evo2_adaptive": 100}` |
