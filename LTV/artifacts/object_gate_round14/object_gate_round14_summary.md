# Object Gate Round14 Summary

Round14 tests a more structured conditional-transition representation on the main DeepSeek Lean object-gate setup.

This round asks:

- if raw concatenation `concat(h^-, delta)` is too weak,
- does a more structured interaction feature help?

The new tested representation is:

- `interaction_transition = concat(delta_h, h_minus * delta_h)`

where `*` is elementwise multiplication.

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
- `interaction_transition = [delta ; h^- * delta]`

Compared scorers:

- `linear_prob`
- `mlp_prob`
- `centroid_cosine`

## Main result

The structured interaction feature is meaningfully better than the round13 raw-concat baseline, but it still does not beat bare `transition`.

## Key comparison

### Under `mlp_prob`

- `transition_mlp_prob`
  - `AUROC = 0.9837`
  - `accuracy = 0.9367`
  - `brier = 0.0567`
  - `earliest_fail = 1.0`
- `conditional_transition_mlp_prob`
  - `AUROC = 0.9272`
  - `accuracy = 0.9114`
  - `brier = 0.0897`
  - `earliest_fail = 0.9231`
- `interaction_transition_mlp_prob`
  - `AUROC = 0.9563`
  - `accuracy = 0.9367`
  - `brier = 0.0652`
  - `earliest_fail = 1.0`

This is the core round14 result:

- `interaction_transition` clearly improves over raw concat
- but it still remains weaker than bare `transition`

### Under `linear_prob`

- `transition_linear_prob`
  - `AUROC = 0.9406`
  - `accuracy = 0.8608`
  - `brier = 0.1265`
- `interaction_transition_linear_prob`
  - `AUROC = 0.9190`
  - `accuracy = 0.8228`
  - `brier = 0.1772`

The interaction feature does not help the linear scorer.

### Under `centroid_cosine`

- `transition_centroid_cosine`
  - `AUROC = 0.7716`
- `interaction_transition_centroid_cosine`
  - `AUROC = 0.7622`

The simple geometry readout also does not benefit.

## Interpretation

Round14 is a partial positive result, but not a win.

It supports:

- structured conditioning is better than naive conditioning

It does not support:

- this specific interaction feature is better than bare `delta`

So the updated method reading is:

- “conditioning matters” is still plausible
- “conditioning by raw concatenation” is a bad implementation
- “conditioning by simple elementwise interaction” is a better implementation than concat
- but it still does not surpass bare transition under the current scorer family

## Best next move

If continuing this branch, the next step should not be more feature concatenation.

The better next candidates are:

1. bilinear / energy-style scorers over `(h^-, delta)`
2. explicit interaction-only features plus learned weighting
3. pairwise / contrastive objectives that directly optimize same/flip behavior
