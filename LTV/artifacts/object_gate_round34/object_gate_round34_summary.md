# Round34: Minimal TC-TEM first pass

## Goal

Instantiate the new general mainline frozen in round33:

- not another scorer swap,
- but a minimal **Task-Conditioned Transition Energy Model (TC-TEM)**.

## Method

Implemented [evaluate_cts_tctem.py](/cephfs/luyanzhen/apg/LTV/scripts/evaluate_cts_tctem.py).

This first-pass TC-TEM does three things in one model:

- input = concatenated `(h^-, h^+, Δh)`
- explicit theorem-header conditioning via tiled goal vector interaction
- unified objective with:
  - local correctness BCE on items
  - same-pair consistency
  - flip-pair margin separation
  - hard-negative triplet-style term
  - calibration regularization

Important difference from rounds 20/32:

- it no longer compares separate `post` vs `transition` heads
- it learns one conditioned compatibility score over the full transition object

## Protocol note

A 300-epoch version and then an 80-epoch version were both too expensive for a minimal first pass in this leave-one-theorem-out setup.
The reported round34 result therefore uses `epochs = 20`, which is also aligned with the proposal's original `10–20` epoch head-training range.

## Main result

Round34 produces a real first-pass signal, but not a clean win.

Overall:

- `tctem_energy`
  - `IG = 0.0578`
  - `SS = 0.5108`

Comparison:

- round20 `hardneg_transition_contrastive`
  - `IG = 0.0147`
  - `SS = 0.4829`
- round32 `calhardneg_transition_contrastive`
  - `IG = 0.0300`
  - `SS = 0.5191`
- round34 `tctem_energy`
  - `IG = 0.0578`
  - `SS = 0.5108`

So the first-pass reading is:

- better `SS` than round20
- slightly worse `SS` than round32
- clearly worse `IG` than both round20 and round32

This means the new general formulation is not empty, but the first implementation is not yet the new default mainline either.

## Family reading

### Same-side

TC-TEM is very clean on some families:

- `reflexivity_style = 0.0`
- `projection_style = 0.0`
- `constructor_notation ~= 0.0`
- `theorem_application_style ~= 0.0005`

But it is clearly unstable on others:

- `other_same_rewrite = 0.1660`
- `eliminator_style = 0.3680`

So the first-pass same-side weakness is concentrated, not global.

### Flip-side

TC-TEM is strong on several flip families:

- `wrong_projection = 0.6680`
- `wrong_theorem_reference = 0.5657`
- `wrong_composition = 0.4978`
- `wrong_branch ~= 1.0`
- `transitivity_fabrication ~= 0.9902`

But it is weak on others:

- `wrong_target_term = 0.3205`
- `ill_typed_or_malformed = 0.0003`
- `transitivity_order_swap = 0.0`

So this first-pass TC-TEM still has a split flip profile.

## Additional diagnostic

The score distribution is already showing saturation pressure:

- across `116` source/variant scores,
- `95` are `> 0.999`,
- `11` are `< 1e-3`

So this first-pass implementation likely over-compresses confidence, which helps explain why some families are extremely clean while others collapse into brittle all-or-nothing behavior.

## Interpretation

Round34 supports a limited but important claim:

- moving to a single task-conditioned transition object is viable;
- the new mainline is not vacuous;
- but the first implementation is still too saturated to count as a clean replacement for round20.

The best current reading is:

- round33 was the right conceptual shift;
- round34 is a credible first executable instance;
- but this first TC-TEM should be treated as a **promising first-pass branch**, not yet as the project's best method result.
