# Main Table Draft

## Recommended Main Table Slice

Primary slice:

- `data/generated/craft_core_hard_model_generated_full_hybrid_counterfactual_v2_natural.jsonl`

This is the best current single main slice because it combines:

- tri-domain coverage
- model-generated origin
- audited counterfactual structure
- naturalized surface shift
- deployment relevance

Secondary benchmark:

- `data/generated/craft_core_benchmark_v3_midset_k6_v3_accept_export_ignore_semantic_v2_from_analysis.jsonl`

This is not the main deployment table. It is the cleaner benchmark-v3 audit slice and should be reported as a complementary process-faithfulness benchmark.

## Recommended Columns

- `ordinary_auroc`
- `amcd`
- `ass_total`
- `selection_gain_at4`
- `exploitability_rate`

Optional appendix columns:

- `ece`
- `brier`
- `aurc`

## Main Table Values

| model | ordinary_auroc | amcd | ass_total | selection_gain_at4 | exploitability_rate |
|---|---:|---:|---:|---:|---:|
| reranker8_masked | 0.6795 | 0.8529 | 0.0184 | 0.3824 | 0.0588 |
| masked_bce | 0.5969 | 0.7647 | 0.1041 | 0.2647 | 0.1765 |
| pairwise_visible | 0.5753 | 0.7353 | 0.0848 | 0.2059 | 0.2941 |
| visible_bce | 0.5926 | 0.7059 | 0.0941 | 0.2647 | 0.2353 |
| visible_cond_swap | 0.5640 | 0.7059 | 0.0377 | 0.2059 | 0.2353 |
| reranker8_visible | 0.5398 | 0.5294 | 0.2128 | 0.3235 | 0.1765 |

## Table Reading

- Best deployment model: `reranker8_masked`
- Best low-`ASS_total` frozen-head repair: `visible_cond_swap`
- Strongest visible deployment baseline: `reranker8_visible`, but it is highly answer-sensitive and weak on `AMCD`

## Key Pairwise Comparisons

### reranker8_masked vs reranker8_visible

- ordinary AUROC: `+0.1397` with bootstrap CI `[0.0644, 0.2608]`
- AMCD: `+0.3235` with bootstrap CI `[0.1818, 0.4583]`
- ASS_total: `-0.1944` with bootstrap CI `[-0.2485, -0.1355]`

### reranker8_masked vs visible_cond_swap

- ordinary AUROC: `+0.1155` with bootstrap CI `[0.0419, 0.2102]`
- AMCD: `+0.1470` with bootstrap CI `[0.0454, 0.2500]`
- ASS_total: `-0.0193` with bootstrap CI `[-0.0278, -0.0108]`

### reranker8_masked vs pairwise_visible

- ordinary AUROC: `+0.1042` with bootstrap CI `[0.0164, 0.2093]`
- AMCD: `+0.1176` with bootstrap CI `[0.0000, 0.2222]`
- exploitability rate: `-0.2353` with bootstrap CI `[-0.4000, -0.0834]`

## Suggested Caption

Seed-averaged results on the naturalized full-hybrid generated slice. The strongest current deployment model is the masked `Qwen3-Reranker-8B`, which outperforms the visible reranker and the strongest frozen-head baselines on both `AMCD` and downstream utility while keeping answer-swap sensitivity low.

## Secondary Benchmark-V3 Readout

Use this as a secondary table or boxed comparison, not as the primary main table.

### Reranker8 On Benchmark-V3 Midset

| model | ordinary_auroc | amcd | ass_total | selection_gain_at4 | exploitability_rate |
|---|---:|---:|---:|---:|---:|
| reranker8_masked | 0.5589 | 0.6731 | 0.0438 | 0.3889 | 0.1111 |
| reranker8_visible | 0.5524 | 0.6058 | 0.1344 | 0.3889 | 0.1111 |

### Benchmark-V3 Takeaway

- benchmark-v3 preserves the visible-vs-masked faithfulness gap
- benchmark-v3 does not currently amplify that gap into a utility gap
- benchmark-v3 should therefore be framed as a cleaner process-faithfulness benchmark, not a direct replacement for the deployment-oriented full-hybrid slice
- the same-dataset robustness summary is consistent with this reading: mixed visible-attacker transfer is slightly worse for `reranker8_visible` than for `reranker8_masked`, but both views land on the same attacked-quartet utility, so the main separation remains faithfulness rather than deployment exploitability
- a benchmark-v3-specific reproduction pass is also consistent: the reranker bootstrap keeps the masked `AMCD` edge (`+0.0673`) and low-`ASS_total` edge (`-0.0906`) while leaving utility tied

## External-Source ProcessBench Table

This is a separate mainline for the benchmark pivot. It should not be merged into the synthetic deployment table or forced into quartet metrics.

### PB-Trace

| model | acc@0.5 | acc@val-thr | auroc | invalid_answer_gap |
|---|---:|---:|---:|---:|
| frozen_visible | 0.7059 | - | 0.7863 | -0.1468 |
| frozen_masked | 0.7157 | - | 0.8075 | -0.0961 |
| frozen_step_only | 0.7784 | - | 0.8759 | -0.0495 |
| reranker8_visible | 0.3490 | 0.6980 | 0.7337 | 0.0003 |
| reranker8_masked | 0.3529 | 0.7000 | 0.7229 | -0.0006 |

### PB-Prefix

| model | ordinary_accuracy | ordinary_auroc | boundary_drop_mean | invalid_answer_gap |
|---|---:|---:|---:|---:|
| frozen_visible | 0.6229 | 0.6759 | 0.2157 | -0.0081 |
| frozen_masked | 0.6386 | 0.6813 | 0.2058 | -0.0885 |
| frozen_step_only | 0.6375 | 0.6918 | 0.2143 | -0.0574 |

### External-Source Takeaway

- `ProcessBench` now supports a real external-source benchmark package with `PB-Trace` and `PB-Prefix`.
- The strongest current external-source verifier is `frozen_step_only`, not the reranker.
- `Qwen3-Reranker-8B` is not hopeless on `ProcessBench`: its main failure is threshold calibration, not complete lack of ranking signal. But even with validation-tuned thresholds it still does not beat the best frozen trace baseline on AUROC.
