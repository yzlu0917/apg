# CTS Round4 Targeted Expansion Summary

## Scope

Round4 expands weak CTS families instead of doing another generic sweep.

Main additions:

- direct theorem-reference flips for `add_zero / zero_add / mul_zero / zero_mul`
- explicit composition flip for equality symmetry
- explicit wrong-target-term flip for reflexivity
- one extra projection-style same rewrite

This round also fixes a data bug: API-derived `pair_id` values now include a short hash of the variant string, so multiple variants from the same source and prompt mode no longer collide.

## Data Added

- updated auto panel: `36` rows total
  - `15 same`
  - `21 flip`
- round4 novel-only slice: `8` rows
  - `2 same`
  - `6 flip`

Weak-family counts after round4 in the updated auto panel:

- `wrong_theorem_reference = 6`
- `wrong_composition = 3`
- `wrong_target_term = 4`

## High-Level Readout

- full auto panel:
  - `transition_only`: `IG = 0.2000`, `SS = 0.6422`
  - `concat_all`: `IG = 0.1333`, `SS = 0.3338`
- novel-only targeted slice:
  - `transition_only`: `IG = 0.0`, `SS = 0.1667`
  - `concat_all`: `IG = 0.0`, `SS = 0.6667`

Interpretation:

- round4 improves the full-panel flip readout for `transition_only`;
- but the newly added weak-family rows do not uniformly rescue `transition_only` on their own.

## What Improved

- `wrong_theorem_reference` moved from essentially no `transition_only` signal to a readable positive signal on the full auto panel.
- `wrong_target_term` is now strong for `transition_only` on the full auto panel aggregate.
- `wrong_projection`, `ill_typed_or_malformed`, and `goal_mismatch_direct_use` remain compatible with the earlier direction.

## What Is Still Weak

- `wrong_composition` is still not solved.
  - On the updated auto panel, `transition_only` is effectively zero on this family.
  - On the novel-only slice, text is the only baseline with even a small positive signal.
- same-family evidence is still unstable and often confounded by degenerate invariance.
  - low `IG` for `pre_state_only` is still mostly non-responsiveness
  - some low `IG` wins for `concat_all` are not enough to justify a representation switch

## Gate Read

- `Object gate`: still partially supported
- `Audit gate`: still not passed
- current bounded claim:
  - `transition_only` is a stronger flip-sensitive representation on several failure families
  - but it is not yet a uniformly validated object representation across all rewrite and composition families

## Next Priorities

1. Add more structurally distinct `wrong_composition` families instead of repeating equality-symmetry variants.
2. Add harder same rewrites that are not explained by trivial invariance.
3. Keep using the fixed hashed `pair_id` path for any future API-derived CTS rows.
