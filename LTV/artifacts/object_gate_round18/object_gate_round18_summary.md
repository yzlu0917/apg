# CTS Round18 Contrastive Embedding Summary

Round18 keeps the round7 CTS full panel fixed and replaces the scalar pairwise-margin scorer with a minimal embedding-style contrastive objective.

This round asks:

- whether the round17 collapse came from using a scalar pairwise score that was too blunt,
- and whether a small latent embedding objective can preserve more same/flip balance.

The new baselines are:

- `post_contrastive`
- `transition_contrastive`

Both learn a normalized embedding from the underlying feature vector and then score items by:

- distance to the positive item centroid
- versus distance to the negative item centroid

with training losses:

- same pairs: pull source and variant together
- flip pairs: push source and variant apart by a margin

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

Embedding-style contrastive training is clearly better than the round17 scalar pairwise-margin baseline, but it is still not a clean win over the best round10 single-point baseline.

### Against round17 pairwise margin

- `post_pairwise_margin`
  - `IG = 0.0691`
  - `SS = 0.5990`
- `post_contrastive`
  - `IG = 0.0657`
  - `SS = 0.4480`

- `transition_pairwise_margin`
  - `IG = 0.0518`
  - `SS = 0.1843`
- `transition_contrastive`
  - `IG = 0.0648`
  - `SS = 0.4199`

The main gain is on `transition`:

- `IG` stays much better than the round10 single-point baseline
- `SS` recovers sharply relative to round17

### Against round10 single-point baselines

- `post_mlp_prob`
  - `IG = 0.0720`
  - `SS = 0.7645`
- `post_contrastive`
  - `IG = 0.0657`
  - `SS = 0.4480`

- `transition_mlp_prob`
  - `IG = 0.1042`
  - `SS = 0.7576`
- `transition_contrastive`
  - `IG = 0.0648`
  - `SS = 0.4199`

So the contrastive route improves invariance relative to round10, especially for `transition`, but it still gives up a large amount of flip sensitivity.

## Family reading

The family audit shows a more balanced picture than round17, but not a decisive rescue.

### Same-side

`transition_contrastive` is very strong on:

- `reflexivity_style`
  - `IG = 0.0079`
- `projection_style`
  - `IG = 0.0035`
- `constructor_notation`
  - `IG = 0.0019`

It is still not clearly better on the harder same families:

- `other_same_rewrite`
  - `post = 0.1623`
  - `transition = 0.1650`
- `eliminator_style`
  - `post = 0.2948`
  - `transition = 0.2887`
- `theorem_application_style`
  - `post = 0.0815`
  - `transition = 0.0961`

### Flip-side

`transition_contrastive` remains stronger on:

- `wrong_theorem_reference`
  - `SS = 0.3175`
- `wrong_composition`
  - `SS = 0.4582`
- `goal_mismatch_direct_use`
  - `SS = 0.6126`

But `post_contrastive` is stronger on more flip families overall:

- `wrong_projection`
  - `0.5843 > 0.4550`
- `wrong_branch`
  - `0.6534 > 0.6113`
- `ill_typed_or_malformed`
  - `0.5858 > 0.3568`
- `wrong_target_term`
  - `0.4391 > 0.3789`

## Interpretation

Round18 supports a narrower but cleaner conclusion:

1. the pairwise direction is not dead
2. the round17 collapse was partly a scalar-objective problem
3. a minimal contrastive embedding objective gives a noticeably better same/flip balance than scalar pairwise margin
4. but this minimal version still does not beat the best single-point baseline on semantic sensitivity

So the correct reading is not:

- pairwise training already wins

It is:

- pairwise training remains promising
- but the first contrastive implementation is still partial
- and `transition` still does not recover a unique overall advantage under the current minimal contrastive recipe

## Best next move

1. keep round18 as the first credible contrastive baseline
2. stop tuning scalar pairwise margins
3. if continuing this branch, prioritize:
   - asymmetric same/flip weighting
   - harder negative construction
   - goal-conditioned contrastive scoring
