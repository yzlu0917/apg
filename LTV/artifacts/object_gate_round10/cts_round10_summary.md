# CTS Round10 Summary

Round10 extends the round9 scoring audit from the fixed reflexivity control to the broader round7 full panel.

This round asks:

- was round9 only a fixed-panel rescue?
- or does the scorer effect persist on a larger same-family panel?

## Setup

- data: `cts_mini_v0_auto_panel_round7_seed.jsonl`
- size: `58` pairs
  - `30 same`
  - `28 flip`
- fixed model and feature source:
  - `DeepSeek-Prover-V2-7B`
  - round7 `boundary_states.pt`

Compared scorers:

- `linear_prob`
- `linear_logit_z`
- `mlp_prob`
- `centroid_cosine`

on both:

- `post-state`
- `transition`

## Main result

For `transition` on the broader full panel:

- `transition_linear_prob`
  - `IG = 0.4007`
  - `SS = 0.7852`
- `transition_linear_logit_z`
  - `IG = 0.3633`
  - `SS = 1.5262`
- `transition_mlp_prob`
  - `IG = 0.1042`
  - `SS = 0.7576`
- `transition_centroid_cosine`
  - `IG = 0.1204`
  - `SS = 0.2224`

This means round9 was not just a fixed-control artifact:

- scorer choice still materially changes the broader same-side reading.

## Family-level reading

### `projection_style`

- round7 `transition_only`: `IG = 0.0467`
- round10 `transition_mlp_prob`: `IG = 0.000009`

This family remains easy and stable.

### `reflexivity_style`

- round7 `transition_only`: `IG = 0.9982`
- round10 `transition_mlp_prob`: `IG = 0.0096`

This is the biggest round10 update:

- the earlier hard-negative reading for `reflexivity_style` does not survive the broader scorer audit.

### `other_same_rewrite`

- round7 `transition_only`: `IG = 0.3439`
- round10 `transition_mlp_prob`: `IG = 0.3138`
- round10 `transition_centroid_cosine`: `IG = 0.0799`

This family improves under better scorers, but not uniformly.

### `eliminator_style`

- round7 `transition_only`: `IG = 0.0010`
- round10 `transition_mlp_prob`: `IG = 0.4915`
- round10 `transition_centroid_cosine`: `IG = 0.0854`

This family is scorer-fragile in the opposite direction:

- the MLP rescue is not universal.

## Important caveat

Round10 does not show that `transition` is now clearly better than `post-state`.

In fact:

- `post_mlp_prob`
  - `IG = 0.0720`
  - `SS = 0.7645`
- `transition_mlp_prob`
  - `IG = 0.1042`
  - `SS = 0.7576`

So the round10 lesson is not:

- “transition wins once the scorer is fixed”

The stronger lesson is:

- scorer choice was a first-order confounder in the previous object/audit reading
- after fixing the scorer, the transition-vs-post-state comparison becomes open again

## Updated interpretation

Round10 changes the project state in two ways:

1. `reflexivity_style` can no longer be treated as a clean hard-negative branch.
2. The main unresolved comparison is now:
   - `transition` vs `post-state`
   under better scorers, on broader panels.

## Best next move

1. Re-run the main object-gate comparison with:
   - `post_mlp_prob`
   - `transition_mlp_prob`
   - one geometry scorer
2. Update the claim table from:
   - “reflexivity hard negative”
   to
   - “same-side conclusion is scorer-conditional”
3. Only then decide whether `transition` still has a unique object-level advantage.
