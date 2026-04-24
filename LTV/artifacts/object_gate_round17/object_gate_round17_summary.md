# CTS Round17 Pairwise Margin Summary

Round17 switches from single-point local-soundness supervision to a directly pairwise objective on the round7 CTS full panel.

This round asks:

- if the current bottleneck is objective mismatch,
- does directly optimizing same/flip behavior help?

The new baselines are:

- `post_pairwise_margin`
- `transition_pairwise_margin`

Both are trained with a pairwise objective:

- same pairs: minimize score gap
- flip pairs: enforce `source > variant` by a margin

This is a minimal pairwise route, not yet a full contrastive embedding model.

## Setup

- model: `DeepSeek-Prover-V2-7B`
- data: `data/cts/cts_mini_v0_auto_panel_round7_seed.jsonl`
- size:
  - `58` pairs
  - `30 same`
  - `28 flip`
- protocol:
  - leave-one-source-theorem-out
- compared fields:
  - `post-state`
  - `transition`

## Main result

Pairwise supervision changes the tradeoff, but does not produce a clean win.

### Against round10 single-point baselines

Reference single-point results on the same panel:

- `post_mlp_prob`
  - `IG = 0.0720`
  - `SS = 0.7645`
- `transition_mlp_prob`
  - `IG = 0.1042`
  - `SS = 0.7576`

Round17 pairwise results:

- `post_pairwise_margin`
  - `IG = 0.0691`
  - `SS = 0.5990`
- `transition_pairwise_margin`
  - `IG = 0.0518`
  - `SS = 0.1843`

## Interpretation

This is not a failure of the pairwise idea, but it is not the hoped-for clean rescue either.

What it shows is more specific:

1. direct pairwise supervision can improve invariance
2. but the current scalar pairwise margin objective can also collapse semantic sensitivity

This effect is strongest for `transition`:

- `IG` improves a lot
- `SS` collapses sharply

So the current pairwise objective is pushing the model toward “stable scores” without preserving enough flip discrimination.

## Family reading

The family audit shows the same pattern:

- `transition_pairwise_margin` is better on several same families such as:
  - `projection_style`
  - `reflexivity_style`
  - `constructor_notation`
- but it underperforms badly on most important flip families such as:
  - `wrong_projection`
  - `wrong_theorem_reference`
  - `wrong_composition`
  - `wrong_branch`

The main exception is that it still retains some signal on:

- `wrong_target_term`
- part of `ill_typed_or_malformed`

## Updated method reading

Round17 supports a narrower conclusion:

- objective mismatch was real
- but a scalar pairwise-margin scorer is still too weak / too blunt

So the next move should not be:

- more tuning of the same scalar margin loss

It should be something closer to:

1. contrastive embedding objectives
2. asymmetric weighting between same and flip terms
3. goal-conditioned pairwise latent scoring

## Best next move

1. keep round17 as the first real pairwise baseline
2. do not read it as a clean win
3. if continuing, move from scalar pairwise margin to embedding-style contrastive training
