# Round31: Neighborhood scorer branch

## Goal

Stop local rescue and try a genuinely new scorer that targets neighborhood calibration directly, instead of adding another learned head.

## Method

Implemented [scripts/evaluate_cts_knn_local.py](/cephfs/luyanzhen/apg/LTV/scripts/evaluate_cts_knn_local.py) with two local-neighborhood readouts on frozen round7 CTS full-panel features:

- `knn_local_prob` / `knn_local_margin`: Euclidean kNN local density-ratio with RBF kernel
- `knn_local_cosine_prob` / `knn_local_cosine_margin`: top-k cosine local margin

Protocol:
- frozen train features: `artifacts/object_gate_round7/deepseek_prover_v2_7b/boundary_states.pt`
- frozen panel: `data/cts/cts_mini_v0_auto_panel_round7_seed.jsonl`
- scorer only; no new data, no new recipe, no panel changes

## Key result

### 1. Euclidean RBF local density fully degenerates

The initial neighborhood idea did not fail because training splits were empty or feature variance vanished.

Observed diagnostic:
- leave-one-theorem-out train splits still have both classes, e.g. `77` rows with `64 pos / 13 neg`
- `h_plus` and `delta_h` both have normal feature variance
- but CTS test points sit extremely far from both positive and negative neighborhoods after standardization
- resulting top-k Euclidean distances are around `76-128`, so `exp(-d^2)` underflows to `0`
- both positive and negative local densities become `0`, so every pair receives `margin = 0`, `prob = 0.5`

So the RBF branch is a clean negative control for this setting.

### 2. Cosine local margin is non-degenerate, but clearly weaker than the current main line

DeepSeek round31 aggregate:

- `post_knn_local_cosine_prob`: `IG = 0.1747`, `SS = 0.2777`
- `transition_knn_local_cosine_prob`: `IG = 0.1374`, `SS = 0.2264`
- `post_knn_local_cosine_margin`: `IG = 0.2389`, `SS = 0.3270`
- `transition_knn_local_cosine_margin`: `IG = 0.1816`, `SS = 0.2466`

Comparison to prior credible baselines:
- round18 `post_contrastive`: `IG = 0.0657`, `SS = 0.4480`
- round18 `transition_contrastive`: `IG = 0.0648`, `SS = 0.4199`
- round20 `hardneg_transition_contrastive`: `IG = 0.0147`, `SS = 0.4829`

So the cosine neighborhood scorer is not just "not best"; it is materially worse on both same-side invariance and flip sensitivity.

## Readout

This branch produced two useful conclusions:

1. neighborhood calibration is a real issue, but naive local Euclidean density is unusable in this high-dimensional frozen-feature regime;
2. switching to a scale-free cosine neighborhood readout avoids collapse, but still does not match the learned contrastive / hard-negative main line.

## Status

- `RBF local density`: clean negative control
- `cosine local margin`: clean negative baseline
- no second-model rerun is justified from this result

## Current claim boundary

Round31 does **not** reopen the scorer branch as a competitive main path.
It only shows that:
- the earlier context-sensitive failures are not rescued by a simple local-neighborhood scorer;
- the current strong signal still lives in the contrastive / hard-negative family, not in naive nonparametric neighborhood scoring.
