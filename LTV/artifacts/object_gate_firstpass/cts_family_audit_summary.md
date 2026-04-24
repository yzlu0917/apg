# CTS Family Audit Summary

## Scope

This note summarizes the family-sliced audit derived from:

- `cts_mini_panel_eval_v2.json` + `cts_mini_v0_panel_annotated.jsonl`
- `cts_auto_panel_eval.json` + `cts_mini_v0_auto_panel_annotated.jsonl`

The goal is not to declare `Audit gate` passed. The goal is to identify where the current object signal for `transition_only` is supported, where it is weak, and what to expand next.

## Overall

- curated panel (`20` pairs):
  - `transition_only`: `IG = 0.2000`, `SS = 0.6003`
  - `concat_all`: `IG = 0.0`, `SS = 0.5`
- auto panel (`28` pairs):
  - `transition_only`: `IG = 0.0769`, `SS = 0.4418`
  - `concat_all`: `IG = 0.3893`, `SS = 0.4667`

Readout:

- `transition_only` remains the best-balanced single representation.
- `concat_all` can look good on aggregate but is not stable enough to treat as the main representation.
- `pre_state_only` often gets low `IG` by being nearly non-responsive.

## Families That Currently Support `transition_only`

Supported same-family evidence:

- `projection_style`
- `eliminator_style`
- `reflexivity_style`

Supported flip-family evidence:

- `wrong_branch`
- `ill_typed_or_malformed`
- `goal_mismatch_direct_use`

These are the slices where `transition_only` most consistently combines low invariance gap with usable semantic sensitivity.

## Families That Currently Do Not Support a Global Claim

Weak or unstable flip families:

- `wrong_theorem_reference`
- `wrong_composition`
- `wrong_target_term`

Weak or mixed same-family evidence:

- parts of `constructor_notation`

Interpretation:

- the current object signal is not uniform across semantic failure modes;
- the theorem-reference and target-term flips are the main places where the claim can still break.

## What This Means for the Gates

- `Object gate`: partially supported, but only as a bounded object-identification claim.
- `Audit gate`: not passed yet.
- `Conversion gate`: too early.
- `Scale gate`: blocked until weak families are expanded and re-audited.

## Next Expansion Priorities

1. Add more `wrong_theorem_reference`, `wrong_composition`, and `wrong_target_term` flips.
2. Add harder same-family rewrites for `constructor_notation` and beyond theorem-application-style rewrites.
3. Re-run family audit after the weak slices have at least a minimally readable sample size.
