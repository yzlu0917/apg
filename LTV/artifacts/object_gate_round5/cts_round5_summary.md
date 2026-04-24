# CTS Round5 Composition Expansion Summary

## Scope

Round5 adds a minimal set of composition-oriented Lean source theorems and uses them to expand the `wrong_composition` family beyond the original equality-symmetry template.

Added Lean source records:

- `lean_imp_trans_pos`
- `lean_imp_trans_bad_comp`
- `lean_eq_trans_pos`
- `lean_eq_trans_bad_comp`

Added curated CTS rows:

- `3 same`
- `3 wrong_composition`

## Main Readout

- round5 full panel:
  - `transition_only`: `IG = 0.1178`, `SS = 0.4897`
  - `concat_all`: `IG = 0.0556`, `SS = 0.3750`
- round5 manual-only composition slice:
  - `transition_only`: `IG = 0.0`, `SS = 0.3333`
  - `post_state_only`: `IG = 0.6667`, `SS = 0.3333`
  - `concat_all`: `IG = 0.3333`, `SS = 0.3333`

Interpretation:

- round5 does improve `wrong_composition` from near-zero to a readable positive signal;
- but `transition_only` is not uniquely winning on the new composition rows.

## Family-Level Update

`wrong_composition` on the full panel:

- round4:
  - `transition_only ~= 0`
  - `text_only = 0.0183`
- round5:
  - `transition_only = 0.1667`
  - `post_state_only = 0.1667`
  - `text_only = 0.1522`

This is progress, but not a clean win.

## Important Instability

Round5 also shows that family conclusions are still not fully stable under source expansion:

- `wrong_theorem_reference` improves further
- `wrong_composition` improves modestly
- `wrong_target_term` swings back toward `text_only`, while `transition_only` loses the strong advantage seen in round4

That means the current object evidence is still sensitive to the exact source mix and training slice.

## Current Gate Read

- `Object gate`: still partially supported
- `Audit gate`: still not passed

Most accurate current claim:

- `transition_only` remains a strong flip-sensitive candidate overall;
- but family-level support is not yet stable enough to declare a robust object representation.

## Next Priorities

1. Add more structurally distinct `wrong_composition` families, especially non-equality chains.
2. Revisit `wrong_target_term` with the round5 source base, since that family regressed.
3. Keep separating “same-family invariance” from degenerate non-responsiveness.
