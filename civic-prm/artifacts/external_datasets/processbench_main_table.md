# ProcessBench Main Table

## PB-Trace

| model | family | acc@0.5 | acc@val-thr | auroc | invalid_answer_gap | ece | brier |
|---|---|---:|---:|---:|---:|---:|---:|
| frozen_visible | frozen | 0.7059 | - | 0.7863 | -0.1468 | - | - |
| frozen_masked | frozen | 0.7157 | - | 0.8075 | -0.0961 | - | - |
| frozen_step_only | frozen | 0.7784 | - | 0.8759 | -0.0495 | - | - |
| reranker8_visible | reranker | 0.3490 | 0.6980 | 0.7337 | 0.0003 | 0.5660 | 0.5250 |
| reranker8_masked | reranker | 0.3529 | 0.7000 | 0.7229 | -0.0006 | 0.5525 | 0.5101 |

## PB-Prefix

| model | family | ordinary_accuracy | ordinary_auroc | boundary_drop_mean | invalid_answer_gap |
|---|---|---:|---:|---:|---:|
| frozen_visible | frozen | 0.6229 | 0.6759 | 0.2157 | -0.0081 |
| frozen_masked | frozen | 0.6386 | 0.6813 | 0.2058 | -0.0885 |
| frozen_step_only | frozen | 0.6375 | 0.6918 | 0.2143 | -0.0574 |

## Takeaways

- Best `PB-Trace` model by AUROC: `frozen_step_only` (`0.8759`).
- Best `PB-Prefix` model by AUROC: `frozen_step_only` (`0.6918`) with boundary drop `0.2143`.
- Best reranker by AUROC: `reranker8_visible` (`AUROC 0.7337`), but its default-threshold accuracy (`0.3490`) only becomes reasonable after validation-threshold tuning (`0.6980`).
- Overall `PB-Trace` AUROC order: `frozen_step_only, frozen_masked, frozen_visible, reranker8_visible, reranker8_masked`.
