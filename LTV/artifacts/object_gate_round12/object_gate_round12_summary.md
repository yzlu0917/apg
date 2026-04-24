# Object Gate Round12 Summary

Round12 ports the scorer-conditioned Lean object-gate comparison from DeepSeek-Prover-V2-7B to Goedel-Prover-V2-8B.

This round asks:

- after fixing the data slice and scorer family,
- do we still see the same `post-state vs transition` ordering on a second prover?

## Setup

- model: `Goedel-Prover-V2-8B`
- fixed data: `data/lean/lean_mini_v0_round7.jsonl`
- fixed size:
  - `79` step examples
  - `40` theorems
  - `66` positive
  - `13` negative
- extraction:
  - layers `[-1, -8, -16] -> [35, 28, 20]`
  - hidden size `4096`
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

Round12 shows real cross-model divergence.

The DeepSeek round11 reading does **not** transfer cleanly to Goedel.

### Under `linear_prob`

- `post_linear_prob`
  - `AUROC = 0.9674`
  - `accuracy = 0.8987`
  - `brier = 0.0914`
  - `earliest_fail = 1.0`
- `transition_linear_prob`
  - `AUROC = 0.9883`
  - `accuracy = 0.9241`
  - `brier = 0.0719`
  - `earliest_fail = 1.0`

On Goedel, the old linear-prob reading now favors `transition`, not `post-state`.

### Under `mlp_prob`

- `post_mlp_prob`
  - `AUROC = 0.8869`
  - `accuracy = 0.9494`
  - `brier = 0.0522`
  - `earliest_fail = 0.8462`
- `transition_mlp_prob`
  - `AUROC = 0.9149`
  - `accuracy = 0.9367`
  - `brier = 0.0658`
  - `earliest_fail = 0.9231`

Under the MLP scorer, Goedel still gives a split reading:

- `transition` is better on `AUROC` and `earliest_fail`
- `post-state` is better on `accuracy` and `brier`

### Under `centroid_cosine`

- `post_centroid_cosine`
  - `AUROC = 0.8683`
- `transition_centroid_cosine`
  - `AUROC = 0.7739`

The simple geometry scorer again does not support a unique transition advantage.

## Cross-model comparison

Compared with DeepSeek round11:

- DeepSeek `linear_prob`: `post > transition`
- Goedel `linear_prob`: `transition > post`

This is the most important round12 result.

It means the main object-gate reading is now conditional on **both**:

- scorer choice
- model choice

## Interpretation

Round12 is a positive identification result, not a clean method win.

It supports:

- the current disagreement is not just a scorer artifact inside one model
- model-dependent representation structure matters

It does **not** support:

- a scorer-robust, model-robust claim that `transition` is the better object
- a scorer-robust, model-robust claim that `post-state` is sufficient

## Updated claim boundary

The strongest supported claim after round12 is:

- latent object comparisons are currently scorer-conditional and model-conditional

This is still useful:

- it makes “maybe the model just has not learned this invariant well” a live hypothesis

## Best next move

1. run seed-stability checks for `mlp_prob` on both DeepSeek and Goedel
2. if stable, run the same comparison on one more prover family
3. only after that decide whether the project should pivot to:
   - multi-model diagnosis branch
   - or a narrower object claim
