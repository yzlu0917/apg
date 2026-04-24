# Round32: Calibration-aware hard-negative contrastive

## Goal

Keep the round20 hard-negative pairwise recipe fixed in spirit, but add an explicit calibration term during training so the model is not only separating embeddings, but also learning a more stable positive-vs-negative score margin inside each training fold.

## Method

Implemented [evaluate_cts_calibrated_hardneg_contrastive.py](/cephfs/luyanzhen/apg/LTV/scripts/evaluate_cts_calibrated_hardneg_contrastive.py).

Relative to round20, the new ingredient is:

- keep the same pairwise same loss
- keep the same flip push-apart loss
- keep the same nearest-flip hard-negative term
- add a `class score calibration` loss on the train fold:
  - positive items = all sources + same variants
  - negative items = flip variants
  - score = `neg_dist - pos_dist` to the current class centroids
  - optimize BCE on this score during training

This is intentionally minimal: no new data, no new panel, no parameter sweep.

## Main result

Round32 is **not** a clean replacement for round20. It gives a new tradeoff.

### Overall metrics

Compared to round20:

- `hardneg_post_contrastive`
  - `IG = 0.0748`
  - `SS = 0.5500`
- `calhardneg_post_contrastive`
  - `IG = 0.0857`
  - `SS = 0.5609`

- `hardneg_transition_contrastive`
  - `IG = 0.0147`
  - `SS = 0.4829`
- `calhardneg_transition_contrastive`
  - `IG = 0.0300`
  - `SS = 0.5191`

So the readout is:

- `post`: slightly better flip sensitivity, slightly worse invariance
- `transition`: clearly better flip sensitivity, but no longer as exceptionally clean on same-side invariance as round20

This means round32 does not dominate round20. It moves the frontier in one direction, not both.

## Family reading

The family audit clarifies where the tradeoff comes from.

### Transition same-side

Relative to round20 `hardneg_transition_contrastive`:

- `reflexivity_style`: `0.0006 -> 0.0022`
- `projection_style`: `0.0008 -> 0.0016`
- `other_same_rewrite`: `0.0327 -> 0.1334`
- `eliminator_style`: `0.0506 -> 0.0239`

So the main same-side cost is not global collapse. It is concentrated, especially in `other_same_rewrite`.

### Flip-side

Relative to round20, `transition` improves on several flip families:

- `wrong_projection`: `0.5276 -> 0.5732`
- `wrong_branch`: `0.7498 -> 0.7545`
- `wrong_composition`: `0.4631 -> 0.4693`
- `wrong_target_term`: `0.5017 -> 0.5089`
- `wrong_theorem_reference`: `0.3676 -> 0.4984`

But it is not a universal gain:

- `ill_typed_or_malformed`: `0.3855 -> 0.3794`

So round32 is best understood as:

- a calibration-aware flip booster for `transition`
- with a nontrivial same-side cost concentrated in a few rewrite families

## Interpretation

Round32 supports one real mechanism claim:

- explicit score calibration is not a useless add-on; it changes behavior in a systematic way and can lift `transition` on flip sensitivity.

But it does **not** yet support the stronger claim that calibration-aware training is simply better than round20.

The current boundary is:

- round20 remains the cleanest pairwise result if same-side cleanliness is the priority;
- round32 is a credible alternative if the priority is lifting `transition` flip sensitivity without collapsing invariance.

## Status

- not a clean win
- not a dead end
- best read as a controlled tradeoff branch, not a new default mainline
