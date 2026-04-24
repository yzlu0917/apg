# Object Gate Round13 Summary

Round13 tests the smallest conditional-transition variant on the main DeepSeek Lean object-gate setup.

This round asks:

- if `delta` alone is too weak,
- does a minimal conditional version `f(h^-, delta)` help?

The tested conditional representation is:

- `conditional_transition = concat(h_minus, delta_h)`

This is intentionally minimal:

- no new scorer family
- no new data slice
- no new CTS panel

## Setup

- model: `DeepSeek-Prover-V2-7B`
- fixed data: `data/lean/lean_mini_v0_round7.jsonl`
- fixed features: round7 `boundary_states.pt`
- size:
  - `79` step examples
  - `40` theorems
  - `66` positive
  - `13` negative
- grouped CV:
  - leave-one-theorem-out

Compared representations:

- `post-state`
- `transition`
- `conditional_transition = [h^- ; delta]`

Compared scorers:

- `linear_prob`
- `mlp_prob`
- `centroid_cosine`

## Main result

The naive conditional version does **not** improve the object-gate reading.

It is worse than the best `post-state` and `transition` baselines under every scorer family tested.

### `linear_prob`

- `post_linear_prob`
  - `AUROC = 0.9848`
- `transition_linear_prob`
  - `AUROC = 0.9406`
- `conditional_transition_linear_prob`
  - `AUROC = 0.9487`
  - `accuracy = 0.8101`
  - `brier = 0.1899`

The conditional concat slightly beats bare `transition` on `AUROC`, but its classification quality is much worse, especially on `accuracy` and `brier`.

### `mlp_prob`

- `post_mlp_prob`
  - `AUROC = 0.9499`
  - `accuracy = 0.9747`
  - `brier = 0.0267`
- `transition_mlp_prob`
  - `AUROC = 0.9837`
  - `accuracy = 0.9367`
  - `brier = 0.0567`
- `conditional_transition_mlp_prob`
  - `AUROC = 0.9272`
  - `accuracy = 0.9114`
  - `brier = 0.0897`

Under the MLP scorer, the naive conditional version is clearly worse than both `post-state` and `transition`.

### `centroid_cosine`

- `post_centroid_cosine`
  - `AUROC = 0.9033`
- `transition_centroid_cosine`
  - `AUROC = 0.7716`
- `conditional_transition_centroid_cosine`
  - `AUROC = 0.7319`

The simple geometry readout also does not support this conditional representation.

## Interpretation

Round13 is a useful negative result.

It does **not** say:

- context does not matter

It says something narrower:

- the most naive way of adding context,
  - `concat(h^-, delta)`
  - is not a good object feature on this setup

So the current evidence supports:

- bare `delta` is not the whole story
- but “add context by concatenation” is also not enough

## Updated method reading

If a stronger conditional transition feature exists, it likely needs to be more structured than:

- raw concatenation

More plausible next candidates are:

1. interaction features such as `h^- * delta`
2. bilinear / energy-style scorers over `(h^-, delta)`
3. pairwise or contrastive objectives that directly optimize same/flip behavior

## Best next move

1. do not treat `concat(h^-, delta)` as the right conditional object
2. keep it as a clean negative baseline
3. if continuing this branch, move to structured conditional scorers rather than larger generic MLPs
