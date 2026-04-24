# CTS Round21 Goal-Conditioned Hard-Negative Summary

Round21 keeps the round7 CTS full panel fixed and starts testing the next method hypothesis after round20:

- if hard negatives help, can explicit goal conditioning reduce the remaining flip-family split?

This round adds a minimal form of conditioning:

- use the theorem `header` as a goal signal
- encode its last-token hidden states once per theorem
- concatenate goal features and feature-goal interactions into the hard-negative contrastive encoder

The new baselines are:

- `goalhardneg_post_contrastive`
- `goalhardneg_transition_contrastive`

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
- base recipe:
  - round20 hard-negative contrastive
- added conditioning:
  - header last-token states
  - concatenation plus elementwise interaction

## Main result

This first goal-conditioned version is not a clean improvement over round20.

### Against round20

- `hardneg_post_contrastive`
  - `IG = 0.0748`
  - `SS = 0.5500`
- `goalhardneg_post_contrastive`
  - `IG = 0.0513`
  - `SS = 0.4611`

- `hardneg_transition_contrastive`
  - `IG = 0.0147`
  - `SS = 0.4829`
- `goalhardneg_transition_contrastive`
  - `IG = 0.0085`
  - `SS = 0.3979`

So the pattern is:

1. conditioning improves invariance further
2. but it also reduces semantic sensitivity
3. the result is more conservative, not more decisive

## Family reading

The family audit shows the same story.

### Same-side

`goalhardneg_transition_contrastive` is extremely stable on same families:

- `reflexivity_style`
  - `IG = 0.0015`
- `projection_style`
  - `IG = 0.0010`
- `constructor_notation`
  - `IG = 0.0004`
- `other_same_rewrite`
  - `IG = 0.0285`
- `eliminator_style`
  - `IG = 0.0186`

This is even cleaner than round20 on several same slices.

### Flip-side

But the flip-side does not improve in a matching way.

`goalhardneg_transition_contrastive` is stronger only on a few slices such as:

- `wrong_theorem_reference`
- part of `api_targeted_family`

And it is weaker than round20 or still weaker than `post` on many important flip slices:

- `wrong_composition`
- `wrong_branch`
- `wrong_target_term`
- `goal_mismatch_direct_use`
- `ill_typed_or_malformed`

So the conditioning is acting more like a stabilizer than a stronger semantic discriminator.

## Interpretation

Round21 is best read as a partial / diagnostic result, not as the new best method.

It shows:

1. minimal header-based goal conditioning is usable
2. it can make the scorer more invariant
3. but this first version does not resolve the flip-family bottleneck

So the right reading is not:

- goal conditioning already fixes the post/transition split

It is:

- naive goal conditioning can over-regularize the scorer
- and a better conditioned design likely needs more targeted structure than “header concat + interaction”

## Best next move

1. keep round20 as the current best pairwise result
2. keep round21 as a useful conditioning diagnostic
3. if continuing the conditioning branch, prefer:
   - flip-family-targeted hard negatives
   - more selective goal conditioning
   - cross-model transfer of the stronger round20 recipe before further conditioning sweep
