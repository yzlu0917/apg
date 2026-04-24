# CTS Round20 Hard-Negative Contrastive Summary

Round20 keeps the round7 CTS full panel fixed and changes only one thing relative to round18:

- instead of symmetric pairwise contrastive loss,
- add a triplet-style hard-negative term that compares each same pair against the nearest flip negative in the training fold.

This round asks:

- whether round18 was mainly limited by weak negative construction,
- and whether harder negatives can improve same/flip balance without returning to scalar-margin collapse.

The new baselines are:

- `hardneg_post_contrastive`
- `hardneg_transition_contrastive`

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
- new ingredient:
  - same-pair triplet-style constraint against nearest flip negative

## Main result

Round20 is the first pairwise variant that gives a real positive method result instead of a mere tradeoff.

### Against round18 contrastive

- `post_contrastive`
  - `IG = 0.0657`
  - `SS = 0.4480`
- `hardneg_post_contrastive`
  - `IG = 0.0748`
  - `SS = 0.5500`

- `transition_contrastive`
  - `IG = 0.0648`
  - `SS = 0.4199`
- `hardneg_transition_contrastive`
  - `IG = 0.0147`
  - `SS = 0.4829`

The key difference is:

- `post` improves `SS`, but pays for it with worse `IG`
- `transition` improves both `IG` and `SS` at the same time

This is the first clean sign in the pairwise branch that harder negative construction can move the tradeoff frontier, not just rebalance it.

### Against round10 single-point

- `transition_mlp_prob`
  - `IG = 0.1042`
  - `SS = 0.7576`
- `hardneg_transition_contrastive`
  - `IG = 0.0147`
  - `SS = 0.4829`

So round20 still does not beat the best single-point transition scorer on `SS`, but it is much stronger on invariance and materially better than round18 on both axes.

## Family reading

The family audit makes the improvement more concrete.

### Same-side

`hardneg_transition_contrastive` is now extremely strong across almost every same family:

- `reflexivity_style`
  - `IG = 0.0006`
- `projection_style`
  - `IG = 0.0008`
- `constructor_notation`
  - `IG = 0.0007`
- `other_same_rewrite`
  - `IG = 0.0327`
- `theorem_application_style`
  - `IG = 0.0423`
- `eliminator_style`
  - `IG = 0.0506`

This is a major change from earlier rounds, where only a subset of same families looked clean.

### Flip-side

The flip-side remains split rather than decisive.

`hardneg_transition_contrastive` is stronger on:

- `wrong_composition`
  - `SS = 0.4631`
- `wrong_branch`
  - `SS = 0.7498`
- `goal_mismatch_direct_use`
  - `SS = 0.7465`

`hardneg_post_contrastive` is stronger on:

- `wrong_projection`
  - `SS = 0.7160`
- `wrong_theorem_reference`
  - `SS = 0.4054`
- `ill_typed_or_malformed`
  - `SS = 0.6917`
- `wrong_target_term`
  - `SS = 0.5931`

So round20 does not fully resolve the `post vs transition` split on flips.

## Interpretation

Round20 supports a stronger method reading than round18 or round19:

1. weak negative construction was a real bottleneck
2. harder negatives help much more than global loss reweighting
3. the gain is especially meaningful for `transition`
4. but the pairwise branch still has not fully beaten the best single-point baseline on flip sensitivity

So the right reading is:

- hard negatives are the first genuinely successful pairwise modification
- but the broader `post vs transition` story is still conditional and family-dependent

## Best next move

1. keep round20 as the current best pairwise result
2. stop global weight tuning
3. if continuing this branch, prioritize:
   - goal-conditioned contrastive scoring
   - better flip-family targeting
   - cross-model transfer of the same hard-negative recipe
