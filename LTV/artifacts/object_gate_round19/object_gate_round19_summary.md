# CTS Round19 Weighted Contrastive Summary

Round19 keeps the round7 CTS full panel fixed and tests a narrower question than round18:

- if round18 still leaves too much semantic sensitivity on the table,
- can this be recovered simply by upweighting the flip term in the contrastive loss?

This round uses the same embedding-style contrastive setup as round18, but with fixed asymmetric weights:

- `same_weight = 1.0`
- `flip_weight = 2.0`
- `flip_weight = 4.0`

The corresponding baselines are:

- `flip2_post_contrastive`
- `flip2_transition_contrastive`
- `flip4_post_contrastive`
- `flip4_transition_contrastive`

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

Simple flip-upweighting does not rescue round18.

### Reference round18

- `post_contrastive`
  - `IG = 0.0657`
  - `SS = 0.4480`
- `transition_contrastive`
  - `IG = 0.0648`
  - `SS = 0.4199`

### Round19 `flip_weight = 2`

- `flip2_post_contrastive`
  - `IG = 0.0642`
  - `SS = 0.4342`
- `flip2_transition_contrastive`
  - `IG = 0.0615`
  - `SS = 0.3938`

### Round19 `flip_weight = 4`

- `flip4_post_contrastive`
  - `IG = 0.0643`
  - `SS = 0.4056`
- `flip4_transition_contrastive`
  - `IG = 0.0660`
  - `SS = 0.4067`

So the pattern is consistent:

1. `flip_weight = 2` gives only tiny `IG` changes and lowers `SS`
2. `flip_weight = 4` lowers `SS` further for `post`
3. `flip_weight = 4` does not improve `transition` over round18 either

## Family reading

The family audit shows the same thing:

- round19 does not create a new flip-family strength that was absent in round18
- it mostly rebalances existing tradeoffs

The clearest surviving `transition` strengths are still:

- `wrong_composition`
- part of `wrong_theorem_reference`
- some targeted-family slices

But the broader flip-side picture still favors `post` in more places overall:

- `wrong_projection`
- `wrong_branch`
- `wrong_target_term`

On same families, the weighted runs remain strong on:

- `projection_style`
- `constructor_notation`

but they do not produce a broad same-side rescue beyond what round18 already had.

In fact, some same slices get worse for `transition` under heavier flip weighting:

- `reflexivity_style`
- `other_same_rewrite`

## Interpretation

Round19 is a clean negative on a narrow method question:

- the current contrastive bottleneck is not fixed by simply multiplying the flip loss

This matters because it rules out a tempting easy explanation:

- round18 was not merely “underweighting flips”

The more likely issue is structural:

- negative construction is still too weak, or
- the score needs more goal/task conditioning, or
- both

## Updated method reading

After round19, the pairwise branch looks like this:

1. scalar pairwise margin was too blunt
2. embedding-style contrastive is a real improvement
3. but naive asymmetric flip-upweighting does not turn it into a clean win

So the next move should not be:

- more scalar weight tuning

It should be closer to:

1. harder negatives
2. goal-conditioned contrastive scoring
3. possibly a structured asymmetric objective, rather than a single global flip multiplier
