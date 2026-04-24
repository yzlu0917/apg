# CTS Round6 Manual Stability Check

## Scope

Round6 adds only manually curated rows.

Purpose:

- strengthen `wrong_composition` with non-equality composition families
- revisit `wrong_target_term` on the round6 source base
- check whether the earlier instability was mainly caused by source mix

## Data Added

Lean source base:

- `32` records
- `62` steps
- `13` negative steps

CTS additions:

- manual-only round6 slice: `8` rows
  - `4 same`
  - `4 flip`
- full panel round6: `50` rows
  - `22 same`
  - `28 flip`

Key family counts in the round6 full panel:

- `wrong_composition = 8`
- `wrong_target_term = 6`

## High-Level Readout

Round6 full panel:

- `transition_only`: `IG = 0.3426`, `SS = 0.8057`
- `post_state_only`: `IG = 0.4091`, `SS = 0.5357`
- `concat_all`: `IG = 0.3193`, `SS = 0.5357`

Interpretation:

- transition becomes much stronger on flip sensitivity;
- but same-family invariance gets worse.

## What Improved

`wrong_composition` now looks meaningfully better:

- round5 full panel:
  - `transition_only SS = 0.1667`
- round6 full panel:
  - `transition_only SS = 0.7294`

`wrong_target_term` also recovers on the round6 source base:

- round6 full panel:
  - `transition_only SS ~= 1.0`

This suggests the earlier regression was at least partly source-mix dependent, not a clean failure of the representation.

## What Remains Weak

The core remaining problem is same-family stability.

In round6:

- `transition_only` overall `IG` rises to `0.3426`
- `reflexivity_style` same-family has very poor invariance for `transition_only`
- `other_same_rewrite` also remains unstable

This means the object still behaves more like a strong flip detector than a clean semantic invariant.

## Gate Read

- `Object gate`: stronger on flip families than before
- `Audit gate`: still not passed

Most accurate current claim:

- `transition_only` is now strongly supported as a failure-sensitive representation across several flip families, including `wrong_composition` on the round6 source base;
- but the same-family side is still too unstable to claim a robust object representation.

## Next Priorities

1. Focus on hard same-family rewrites, especially `reflexivity_style` and `other_same_rewrite`.
2. Separate true semantic invariance failure from superficial formatting / tokenization shift.
3. Only after same-family stability improves should the project try to push harder on `Audit gate`.
