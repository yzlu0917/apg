# Object Gate Round11 Summary

Round11 re-runs the main Lean object-gate comparison under the scorer lessons from round9/10.

This round asks:

- does scorer choice only affect same-side CTS audit?
- or does it also change the main `post-state` vs `transition` object-gate comparison?

## Setup

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

Compared scorers:

- `linear_prob`
- `mlp_prob`
- `centroid_cosine`

## Main result

Scorer choice materially changes the main object-gate reading, not just CTS same-side audit.

### Under `linear_prob`

- `post_linear_prob`
  - `AUROC = 0.9848`
  - `accuracy = 0.9114`
  - `brier = 0.0809`
  - `earliest_fail = 1.0`
- `transition_linear_prob`
  - `AUROC = 0.9406`
  - `accuracy = 0.8608`
  - `brier = 0.1265`
  - `earliest_fail = 0.9231`

Under the old linear-prob reading, `post-state` is clearly better.

### Under `mlp_prob`

- `post_mlp_prob`
  - `AUROC = 0.9499`
  - `accuracy = 0.9747`
  - `brier = 0.0267`
  - `earliest_fail = 0.9231`
- `transition_mlp_prob`
  - `AUROC = 0.9837`
  - `accuracy = 0.9367`
  - `brier = 0.0567`
  - `earliest_fail = 1.0`

Under the MLP reading, `transition` regains the ranking advantage on `AUROC` and `earliest_fail`, but `post-state` still has better calibrated-probability behavior on `accuracy` and `brier`.

### Under `centroid_cosine`

- `post_centroid_cosine`
  - `AUROC = 0.9033`
- `transition_centroid_cosine`
  - `AUROC = 0.7716`

The simple geometry scorer does not support a unique transition advantage.

## Interpretation

Round11 changes the object-gate reading in a precise way:

1. scorer choice is a first-order confounder for the main Lean object-gate comparison, not just for CTS same-side audit.
2. there is still no scorer-robust claim that `transition` dominates `post-state`.
3. there is also no longer a scorer-robust claim that `post-state` dominates `transition`.

So the current most accurate object-level reading is:

- `transition vs post-state` remains scorer-conditional
- the comparison is genuinely open again under better scorers

## Claim boundary update

Round11 does **not** justify:

- “transition is clearly the better object”
- “post-state is clearly enough; transition adds nothing”

The supported claim is narrower:

- latent-state-based object signals are real
- but the `post-state` vs `transition` comparison is not yet scorer-stable

## Best next move

1. run seed-stability checks for `mlp_prob`
2. then run the same scorer-conditioned object-gate comparison on at least one additional prover
3. only after that, rewrite the object claim table
